"""
predict_eta.py

Minimal example of loading the trained LightGBM model and predicting ETA
for a single upcoming segment. This is the logic your api-gateway/app/
services/ layer will wrap in a FastAPI endpoint.
"""

import lightgbm as lgb
import pandas as pd

model = lgb.Booster(model_file="model/eta_lightgbm.txt")


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
    current_speed: float,
    previous_segment_speed: float,
    weather_severity: int,
) -> float:
    """Returns predicted travel time in seconds for one segment."""
    row = pd.DataFrame([{
        "route_id": route_id,
        "segment_id": segment_id,
        "segment_type": segment_type,
        "time_of_day_bin": time_of_day_bin,
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "hour_of_day": hour_of_day,
        "distance_km": distance_km,
        "current_speed": current_speed,
        "previous_segment_speed": previous_segment_speed,
        "weather_severity": weather_severity,
    }])

    # Cast categoricals the same way training did so LightGBM reads them correctly
    for col in ["route_id", "segment_id", "segment_type", "time_of_day_bin"]:
        row[col] = row[col].astype("category")

    predicted_seconds = model.predict(row)[0]
    return round(predicted_seconds, 1)


if __name__ == "__main__":
    # Example: a bus currently in a market segment on route R1 at 9:15 AM
    eta_seconds = predict_segment_time(
        route_id="R1",
        segment_id="R1_S1",
        segment_type="market",
        time_of_day_bin="09:00-09:15",
        day_of_week=1,
        is_weekend=0,
        is_holiday=0,
        hour_of_day=9.25,
        distance_km=1.2,
        current_speed=13.5,
        previous_segment_speed=15.0,
        weather_severity=0,
    )
    print(f"Predicted travel time: {eta_seconds:.0f}s ({eta_seconds/60:.1f} min)")
