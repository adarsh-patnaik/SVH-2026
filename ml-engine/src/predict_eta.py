"""
predict_eta.py

Inference utility to load the trained LightGBM model and predict ETA
for a single upcoming segment. This logic is called by api-gateway
for live commuter ETA calculations.

Supports:
  - Valid categorical mapping aligned with training dictionary
  - Graceful handling of missing sensor telemetry (None / NaN for current_speed
    or previous_segment_speed when packet drops occur)
"""

import os
import json
import numpy as np
import pandas as pd
import lightgbm as lgb
from typing import Optional

MODEL_FILE = "model/eta_lightgbm.txt"
ENCODERS_FILE = "model/categorical_maps.json"

_model = None
_cat_maps = None


def get_model():
    global _model, _cat_maps
    if _model is None:
        if not os.path.exists(MODEL_FILE):
            raise FileNotFoundError(f"Model file not found at {MODEL_FILE}. Run train_model.py first.")
        _model = lgb.Booster(model_file=MODEL_FILE)

        if os.path.exists(ENCODERS_FILE):
            with open(ENCODERS_FILE, "r") as f:
                _cat_maps = json.load(f)
        else:
            _cat_maps = {}
    return _model, _cat_maps


def predict_segment_time(
    route_id: str,
    segment_id: str,
    segment_type: str,
    time_of_day_bin: str,
    day_of_week: int,
    is_weekend: int,
    is_holiday: int,
    hour_of_day: float,
    distance_km: float,
    current_speed: Optional[float] = None,
    previous_segment_speed: Optional[float] = None,
    weather_severity: int = 0,
) -> float:
    """
    Returns predicted travel time in seconds for one bus segment.
    Handles missing sensor telemetry (None / NaN) gracefully.
    """
    model, cat_maps = get_model()

    curr_spd = float(current_speed) if (current_speed is not None and not np.isnan(current_speed)) else np.nan
    prev_spd = float(previous_segment_speed) if (previous_segment_speed is not None and not np.isnan(previous_segment_speed)) else np.nan

    row = pd.DataFrame([{
        "route_id": route_id,
        "segment_id": segment_id,
        "segment_type": segment_type,
        "time_of_day_bin": time_of_day_bin,
        "day_of_week": int(day_of_week),
        "is_weekend": int(is_weekend),
        "is_holiday": int(is_holiday),
        "hour_of_day": float(hour_of_day),
        "distance_km": float(distance_km),
        "current_speed": curr_spd,
        "previous_segment_speed": prev_spd,
        "weather_severity": int(weather_severity),
    }])

    # Apply category mappings if available to ensure integer code consistency
    for col in ["route_id", "segment_id", "segment_type", "time_of_day_bin"]:
        if col in cat_maps and cat_maps[col]:
            categories = list(cat_maps[col].values())
            row[col] = pd.Categorical(row[col], categories=categories)
        else:
            row[col] = row[col].astype("category")

    predicted_seconds = model.predict(row)[0]
    return round(float(predicted_seconds), 1)


if __name__ == "__main__":
    print("Running inference smoke tests with predict_segment_time()...\n")

    # Example 1: Morning peak in a market corridor (heavy congestion expected)
    t1 = predict_segment_time(
        route_id="R1",
        segment_id="R1_S1",
        segment_type="market",
        time_of_day_bin="09:00-09:15",
        day_of_week=1,
        is_weekend=0,
        is_holiday=0,
        hour_of_day=9.25,
        distance_km=0.9,
        current_speed=12.0,
        previous_segment_speed=14.0,
        weather_severity=0,
    )
    print(f"1. R1_S1 (Market, Morning Peak, 0.9km):  {t1:.1f}s ({t1/60:.2f} min)")

    # Example 2: Highway stretch on Outer Ring Road (fast free-flow)
    t2 = predict_segment_time(
        route_id="R3",
        segment_id="R3_S1",
        segment_type="highway",
        time_of_day_bin="11:30-11:45",
        day_of_week=2,
        is_weekend=0,
        is_holiday=0,
        hour_of_day=11.6,
        distance_km=4.2,
        current_speed=38.0,
        previous_segment_speed=36.5,
        weather_severity=0,
    )
    print(f"2. R3_S1 (Highway, Off-Peak, 4.2km):    {t2:.1f}s ({t2/60:.2f} min)")

    # Example 3: Dropped telemetry packet (current_speed is None / dropped)
    t3 = predict_segment_time(
        route_id="R2",
        segment_id="R2_S6",
        segment_type="school_zone",
        time_of_day_bin="14:00-14:15",
        day_of_week=3,
        is_weekend=0,
        is_holiday=0,
        hour_of_day=14.1,
        distance_km=1.3,
        current_speed=None,  # Telemetry packet dropped!
        previous_segment_speed=16.5,
        weather_severity=1,  # Rain
    )
    print(f"3. R2_S6 (School Zone, Rain, Dropped GPS Speed): {t3:.1f}s ({t3/60:.2f} min)")
