"""
tests/test_eta_api.py

CHANGELOG (post-review fixes):
- Tests now REQUIRE the model to be present and assert on actual predicted
  values within a plausible range — not just "status code was 200 or 503".
- Added a dedicated test for the categorical encoding fix: predicts the
  same segment features twice using two different dict-construction orders
  and asserts the results are IDENTICAL.
- Added a test for an unseen category (a route_id that never existed in
  training) to confirm it's handled gracefully rather than crashing.
- FIXED: `client` is now a pytest fixture that opens TestClient as a
  context manager (`with TestClient(app) as c:`). Without this, FastAPI's
  `lifespan` startup handler — which calls eta_service.load() — never runs,
  and every test fails with "Model is not loaded" even though the real
  server works fine. This was caught when running the suite for real.

Run with:
    python -m pytest tests/ -v
"""

import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.services.eta_service import eta_service


@pytest.fixture(scope="module")
def client():
    # Context-manager form is REQUIRED for lifespan (startup/shutdown)
    # events to fire on this FastAPI app.
    with TestClient(app) as c:
        yield c


BASE_SEGMENT = {
    "route_id": None,
    "segment_id": None,
    "segment_type": None,
    "time_of_day_bin": None,
    "day_of_week": 1,
    "is_weekend": 0,
    "is_holiday": 0,
    "hour_of_day": 9.25,
    "distance_km": 1.2,
    "current_speed": 13.5,
    "previous_segment_speed": 15.0,
    "weather_severity": 0,
}


def _known_good_segment():
    """Builds a segment using real category values from the loaded model.
    Must be called AFTER the client fixture has run at least once (so the
    lifespan startup has fired and eta_service is loaded)."""
    assert eta_service.is_loaded, (
        "Model is not loaded — copy eta_lightgbm.txt and categorical_maps.json "
        "into app/ml_models/ before running tests."
    )
    seg = dict(BASE_SEGMENT)
    seg["route_id"] = eta_service._category_lists["route_id"][0]
    seg["segment_id"] = eta_service._category_lists["segment_id"][0]
    seg["segment_type"] = eta_service._category_lists["segment_type"][0]
    seg["time_of_day_bin"] = eta_service._category_lists["time_of_day_bin"][0]
    return seg


def test_health_reports_real_self_test_result(client):
    response = client.get("/health")
    assert response.status_code == 200
    body = response.json()
    assert body["model_loaded"] is True
    assert body["status"] == "ok", f"Health self-test failed: {body.get('self_test_detail')}"
    assert body["self_test_ok"] is True
    assert len(body["model_version"]) == 12  # sha256 hash prefix


def test_predict_eta_returns_plausible_value(client):
    payload = {"segment": _known_good_segment()}
    response = client.post("/predict-eta", json=payload)
    assert response.status_code == 200, response.text

    body = response.json()
    seconds = body["predicted_travel_time_seconds"]

    assert seconds > 0, "Predicted time must be positive"
    assert seconds < 3600, "Predicted time for one segment should not exceed an hour"
    assert body["predicted_travel_time_minutes"] == round(seconds / 60, 2)


def test_prediction_is_stable_regardless_of_dict_key_order(client):
    """Guards against the categorical-encoding bug specifically."""
    seg_a = _known_good_segment()
    seg_b = {k: seg_a[k] for k in reversed(list(seg_a.keys()))}

    resp_a = client.post("/predict-eta", json={"segment": seg_a})
    resp_b = client.post("/predict-eta", json={"segment": seg_b})

    assert resp_a.status_code == 200
    assert resp_b.status_code == 200
    assert (
        resp_a.json()["predicted_travel_time_seconds"]
        == resp_b.json()["predicted_travel_time_seconds"]
    ), "Prediction should be identical regardless of input dict ordering"


def test_unseen_category_does_not_crash(client):
    """A route_id that never existed during training should be handled
    gracefully (encoded as missing/NaN category), not crash the request."""
    seg = _known_good_segment()
    seg["route_id"] = "ROUTE_THAT_DOES_NOT_EXIST_IN_TRAINING"

    response = client.post("/predict-eta", json={"segment": seg})
    assert response.status_code == 200, (
        "An unseen category should still produce a response, not a crash"
    )


def test_missing_speed_sensor_data_is_allowed(client):
    seg = _known_good_segment()
    seg["current_speed"] = None
    seg["previous_segment_speed"] = None

    response = client.post("/predict-eta", json={"segment": seg})
    assert response.status_code == 200
    assert response.json()["predicted_travel_time_seconds"] > 0


def test_trip_eta_sums_segments_correctly(client):
    seg1 = _known_good_segment()
    seg2 = _known_good_segment()
    seg2["distance_km"] = 2.5

    response = client.post("/predict-eta/trip", json={"segments": [seg1, seg2]})
    assert response.status_code == 200

    body = response.json()
    assert len(body["breakdown"]) == 2
    expected_total = sum(s["predicted_travel_time_seconds"] for s in body["breakdown"])
    assert body["total_predicted_seconds"] == round(expected_total, 1)


def test_trip_segment_cap_rejected(client):
    """More than MAX_TRIP_SEGMENTS (60) segments in one request should be
    rejected by Pydantic validation (422), not accepted and processed —
    this is the fix for the unbounded-batch-size DoS vector."""
    seg = _known_good_segment()
    too_many_segments = [seg] * 61

    response = client.post("/predict-eta/trip", json={"segments": too_many_segments})
    assert response.status_code == 422, (
        f"Expected 422 for 61 segments (cap is 60), got {response.status_code}"
    )


def test_oversized_string_field_rejected(client):
    """A route_id far longer than any real route ID should be rejected by
    schema validation, not silently accepted."""
    seg = _known_good_segment()
    seg["route_id"] = "R" * 500  # way beyond MAX_ID_LENGTH (64)

    response = client.post("/predict-eta", json={"segment": seg})
    assert response.status_code == 422, (
        f"Expected 422 for oversized route_id, got {response.status_code}"
    )


def test_error_response_does_not_leak_raw_exception_text(client):
    """When prediction fails, the client-facing error should be a generic
    message — not a raw Python exception string that could leak internal
    details (file paths, config values, stack info) as the code evolves."""
    seg = _known_good_segment()
    seg["distance_km"] = -5  # violates gt=0 constraint -> caught by Pydantic (422)
    # This particular case is caught by schema validation before it ever
    # reaches the try/except in the router, so it correctly returns 422
    # with Pydantic's own (safe, generic) validation error format — not a
    # raw exception string. That's still the desired behavior.
    response = client.post("/predict-eta", json={"segment": seg})
    assert response.status_code == 422
    assert "Traceback" not in response.text
    assert ".py" not in response.text  # no file paths leaking into the response


def test_rate_limit_blocks_excessive_requests(client):
    """Fires 25 requests rapidly — the 21st onward should hit the 20/minute
    rate limit and return 429."""
    seg = _known_good_segment()
    payload = {"segment": seg}

    statuses = [client.post("/predict-eta", json=payload).status_code for _ in range(25)]

    assert 429 in statuses, (
        "Expected at least one 429 (rate limited) response among 25 rapid "
        "requests, but rate limiting did not trigger."
    )