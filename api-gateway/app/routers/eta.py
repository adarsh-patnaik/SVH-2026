"""
app/routers/eta.py

CHANGELOG (second review round):
- Exceptions are no longer stringified straight into the HTTP response body.
  `logger.exception(...)` logs the full traceback server-side; the client
  gets a generic, non-leaking message. Today's failure modes are benign
  (bad category, NaN), but raw exception text in a public response is a
  bad habit that eventually leaks a file path, internal config value, or
  stack detail once the code changes.
"""

import logging

from fastapi import APIRouter, HTTPException, Request

from app.models.schemas import (
    EtaPredictionRequest,
    EtaPredictionResponse,
    TripEtaRequest,
    TripEtaResponse,
    SegmentEtaBreakdown,
    HealthResponse,
)
from app.services.eta_service import eta_service, EtaModelNotLoadedError
from app.rate_limit import limiter

logger = logging.getLogger("gatisync-eta-api")
router = APIRouter()

GENERIC_PREDICTION_ERROR = (
    "Prediction failed due to invalid or unsupported input. "
    "Check that all required fields are present and within expected ranges."
)


@router.get("/health", response_model=HealthResponse)
def health():
    if not eta_service.is_loaded:
        return HealthResponse(
            status="model_not_loaded",
            model_loaded=False,
            model_version="unloaded",
            self_test_ok=None,
            self_test_detail="Model has not been loaded.",
        )

    self_test = eta_service.last_self_test_status
    status = "ok" if self_test["ok"] else "degraded"

    return HealthResponse(
        status=status,
        model_loaded=True,
        model_version=eta_service.model_version,
        self_test_ok=self_test["ok"],
        self_test_detail=self_test["detail"],
    )


@router.post("/predict-eta", response_model=EtaPredictionResponse)
@limiter.limit("20/minute")
def predict_eta(request: Request, body: EtaPredictionRequest):
    try:
        seconds = eta_service.predict_segment_seconds(body.segment.model_dump())
    except EtaModelNotLoadedError:
        raise HTTPException(status_code=503, detail="ETA model is not loaded yet.")
    except Exception:
        logger.exception(
            f"Prediction failed for route_id={body.segment.route_id!r} "
            f"segment_id={body.segment.segment_id!r}"
        )
        raise HTTPException(status_code=400, detail=GENERIC_PREDICTION_ERROR)

    return EtaPredictionResponse(
        route_id=body.segment.route_id,
        segment_id=body.segment.segment_id,
        predicted_travel_time_seconds=seconds,
        predicted_travel_time_minutes=round(seconds / 60, 2),
        model_version=eta_service.model_version,
    )


@router.post("/predict-eta/trip", response_model=TripEtaResponse)
@limiter.limit("20/minute")
def predict_trip_eta(request: Request, body: TripEtaRequest):
    # Empty-list case is now also caught by schemas.py's min_length=1, but
    # kept here too as a defensive belt-and-suspenders check.
    if not body.segments:
        raise HTTPException(status_code=400, detail="At least one segment is required.")

    try:
        segment_dicts = [s.model_dump() for s in body.segments]
        seconds_list = eta_service.predict_trip_seconds(segment_dicts)
    except EtaModelNotLoadedError:
        raise HTTPException(status_code=503, detail="ETA model is not loaded yet.")
    except Exception:
        logger.exception(
            f"Trip prediction failed for route_id={body.segments[0].route_id!r}, "
            f"{len(body.segments)} segment(s)"
        )
        raise HTTPException(status_code=400, detail=GENERIC_PREDICTION_ERROR)

    breakdown = [
        SegmentEtaBreakdown(segment_id=seg.segment_id, predicted_travel_time_seconds=secs)
        for seg, secs in zip(body.segments, seconds_list)
    ]
    total = sum(seconds_list)

    return TripEtaResponse(
        route_id=body.segments[0].route_id,
        total_predicted_seconds=round(total, 1),
        total_predicted_minutes=round(total / 60, 2),
        breakdown=breakdown,
        model_version=eta_service.model_version,
    )