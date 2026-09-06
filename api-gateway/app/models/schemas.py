"""
app/models/schemas.py

CHANGELOG (second review round):
- Added max_length bounds to all free-text fields (route_id, segment_id,
  segment_type, time_of_day_bin). Not exploitable today since unrecognized
  values just map to NaN, but an unbounded string on a public endpoint is
  cheap insurance against oversized payloads regardless.
- Added max_length on TripEtaRequest.segments. Without this, a single
  request with e.g. 50,000 segments forces 50,000 sequential model
  predictions server-side — a DoS vector that completely bypasses the
  per-request rate limiter (which counts requests, not segments). Capped
  at 60, generously above any realistic route (the project doc's own
  routes/GTFS design implies a handful to a few dozen stops per route).
"""

from pydantic import BaseModel, Field
from typing import Optional, List

MAX_TRIP_SEGMENTS = 60
MAX_ID_LENGTH = 64
MAX_TIME_BIN_LENGTH = 16  # e.g. "09:00-09:15"


class SegmentFeatures(BaseModel):
    route_id: str = Field(..., max_length=MAX_ID_LENGTH, json_schema_extra={"example": "R1"})
    segment_id: str = Field(..., max_length=MAX_ID_LENGTH, json_schema_extra={"example": "R1_S1"})
    segment_type: str = Field(..., max_length=MAX_ID_LENGTH, json_schema_extra={"example": "market"})
    time_of_day_bin: str = Field(
        ..., max_length=MAX_TIME_BIN_LENGTH, json_schema_extra={"example": "09:00-09:15"}
    )
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    is_weekend: int = Field(..., ge=0, le=1)
    is_holiday: int = Field(..., ge=0, le=1)
    hour_of_day: float = Field(..., ge=0, le=24)
    distance_km: float = Field(..., gt=0, le=200)  # 200km is a generous upper bound for one segment
    current_speed: Optional[float] = Field(None, ge=0, le=200, description="km/h; null if GPS ping missing")
    previous_segment_speed: Optional[float] = Field(None, ge=0, le=200, description="km/h; null if unavailable")
    weather_severity: int = Field(0, ge=0, le=1)


class EtaPredictionRequest(BaseModel):
    segment: SegmentFeatures


class EtaPredictionResponse(BaseModel):
    route_id: str
    segment_id: str
    predicted_travel_time_seconds: float
    predicted_travel_time_minutes: float
    model_version: str


class TripEtaRequest(BaseModel):
    segments: List[SegmentFeatures] = Field(..., min_length=1, max_length=MAX_TRIP_SEGMENTS)


class SegmentEtaBreakdown(BaseModel):
    segment_id: str
    predicted_travel_time_seconds: float


class TripEtaResponse(BaseModel):
    route_id: str
    total_predicted_seconds: float
    total_predicted_minutes: float
    breakdown: List[SegmentEtaBreakdown]
    model_version: str


class HealthResponse(BaseModel):
    status: str  # "ok" | "degraded" | "model_not_loaded"
    model_loaded: bool
    model_version: str
    self_test_ok: Optional[bool]
    self_test_detail: str