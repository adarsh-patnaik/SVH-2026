"""
app/models/schemas.py
"""

from pydantic import BaseModel, Field
from typing import Optional, List


class SegmentFeatures(BaseModel):
    route_id: str = Field(..., example="R1")
    segment_id: str = Field(..., example="R1_S1")
    segment_type: str = Field(..., example="market")
    time_of_day_bin: str = Field(..., example="09:00-09:15")
    day_of_week: int = Field(..., ge=0, le=6, description="0=Monday ... 6=Sunday")
    is_weekend: int = Field(..., ge=0, le=1)
    is_holiday: int = Field(..., ge=0, le=1)
    hour_of_day: float = Field(..., ge=0, le=24)
    distance_km: float = Field(..., gt=0)
    current_speed: Optional[float] = Field(None, description="km/h; null if GPS ping missing")
    previous_segment_speed: Optional[float] = Field(None, description="km/h; null if unavailable")
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
    segments: List[SegmentFeatures]


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