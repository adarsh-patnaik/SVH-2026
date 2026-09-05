"""
tests/test_eta_api.py

Basic smoke tests. Requires the model files to be present at
app/ml_models/ for the prediction tests to pass — the health check will
still work even without them.

Run with:
    pytest tests/
"""

from fastapi.testclient import TestClient
from app.main import app

client = TestClient(app)


def test_health_endpoint_responds():
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert "status" in body
    assert "model_loaded" in body


def test_predict_eta_single_segment():
    payload = {
        "segment": {
            "route_id": "R1",
            "segment_id": "R1_S1",
            "segment_type": "market",
            "time_of_day_bin": "09:00-09:15",
            "day_of_week": 1,
            "is_weekend": 0,
            "is_holiday": 0,
            "hour_of_day": 9.25,
            "distance_km": 1.2,
            "current_speed": 13.5,
            "previous_segment_speed": 15.0,
            "weather_severity": 0,
        }
    }
    response = client.post("/predict-eta", json=payload)
    # 503 is acceptable in CI environments without the model file present;
    # 200 is the real pass condition once the model is copied in.
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        body = response.json()
        assert body["predicted_travel_time_seconds"] > 0
        assert body["segment_id"] == "R1_S1"


def test_predict_eta_missing_speed_is_allowed():
    """Sensor pings can drop — current_speed/previous_segment_speed must be optional."""
    payload = {
        "segment": {
            "route_id": "R1",
            "segment_id": "R1_S1",
            "segment_type": "market",
            "time_of_day_bin": "09:00-09:15",
            "day_of_week": 1,
            "is_weekend": 0,
            "is_holiday": 0,
            "hour_of_day": 9.25,
            "distance_km": 1.2,
            "current_speed": None,
            "previous_segment_speed": None,
            "weather_severity": 0,
        }
    }
    response = client.post("/predict-eta", json=payload)
    assert response.status_code in (200, 503)


def test_trip_eta_sums_segments():
    payload = {
        "segments": [
            {
                "route_id": "R1", "segment_id": "R1_S1", "segment_type": "market",
                "time_of_day_bin": "09:00-09:15", "day_of_week": 1, "is_weekend": 0,
                "is_holiday": 0, "hour_of_day": 9.25, "distance_km": 1.2,
                "current_speed": 13.5, "previous_segment_speed": 15.0, "weather_severity": 0,
            },
            {
                "route_id": "R1", "segment_id": "R1_S2", "segment_type": "residential",
                "time_of_day_bin": "09:15-09:30", "day_of_week": 1, "is_weekend": 0,
                "is_holiday": 0, "hour_of_day": 9.4, "distance_km": 2.5,
                "current_speed": 20.0, "previous_segment_speed": 13.5, "weather_severity": 0,
            },
        ]
    }
    response = client.post("/predict-eta/trip", json=payload)
    assert response.status_code in (200, 503)
    if response.status_code == 200:
        body = response.json()
        assert len(body["breakdown"]) == 2
        assert body["total_predicted_seconds"] == sum(
            s["predicted_travel_time_seconds"] for s in body["breakdown"]
        )