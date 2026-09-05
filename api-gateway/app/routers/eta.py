"""
app/routers/eta.py

Endpoints:
    POST /predict-eta        -> single segment ETA
    POST /predict-eta/trip   -> sum of ETAs across multiple upcoming segments
    GET  /health             -> model load status (for load balancer / uptime checks)
"""

from fastapi import APIRouter, HTTPException

from app.models.schemas import (
    EtaPredictionRequest,
    EtaPredictionResponse,
    TripEtaRequest,
    TripEtaResponse,
    SegmentEtaBreakdown,
    HealthResponse,
)
from app.services.eta_service import eta_service, EtaModelNotLoadedError, MODEL_VERSION

router = APIRouter()


@router.get("/health", response_model=HealthResponse)
def health():
    return HealthResponse(
        status="ok" if eta_service.is_loaded else "model_not_loaded",
        model_loaded=eta_service.is_loaded,
        model_version=MODEL_VERSION,
    )


@router.post("/predict-eta", response_model=EtaPredictionResponse)
def predict_eta(request: EtaPredictionRequest):
    try:
        seconds = eta_service.predict_segment_seconds(request.segment.model_dump())
    except EtaModelNotLoadedError:
        raise HTTPException(status_code=503, detail="ETA model is not loaded yet.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    return EtaPredictionResponse(
        route_id=request.segment.route_id,
        segment_id=request.segment.segment_id,
        predicted_travel_time_seconds=seconds,
        predicted_travel_time_minutes=round(seconds / 60, 2),
        model_version=MODEL_VERSION,
    )


@router.post("/predict-eta/trip", response_model=TripEtaResponse)
def predict_trip_eta(request: TripEtaRequest):
    if not request.segments:
        raise HTTPException(status_code=400, detail="At least one segment is required.")

    try:
        segment_dicts = [s.model_dump() for s in request.segments]
        seconds_list = eta_service.predict_trip_seconds(segment_dicts)
    except EtaModelNotLoadedError:
        raise HTTPException(status_code=503, detail="ETA model is not loaded yet.")
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Prediction failed: {e}")

    breakdown = [
        SegmentEtaBreakdown(segment_id=seg.segment_id, predicted_travel_time_seconds=secs)
        for seg, secs in zip(request.segments, seconds_list)
    ]
    total = sum(seconds_list)

    return TripEtaResponse(
        route_id=request.segments[0].route_id,
        total_predicted_seconds=round(total, 1),
        total_predicted_minutes=round(total / 60, 2),
        breakdown=breakdown,
        model_version=MODEL_VERSION,
    )