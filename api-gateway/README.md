# GatiSync ETA Inference API

This is the "API/ML Service (FastAPI)" box from the architecture diagram —
it wraps the trained LightGBM model from `ml-engine/` in an HTTP API that
the Go ingestion worker, commuter PWA, and SMS bot can all call.

## Folder structure (fits into your existing `api-gateway/`)

```
api-gateway/
├── app/
│   ├── main.py                    # FastAPI entrypoint — loads model on startup
│   ├── routers/
│   │   └── eta.py                 # /predict-eta, /predict-eta/trip, /health
│   ├── services/
│   │   └── eta_service.py         # loads LightGBM model, does the actual inference
│   ├── models/
│   │   └── schemas.py             # request/response Pydantic schemas
│   └── ml_models/                 # <- put trained model files here (see below)
│       ├── eta_lightgbm.txt
│       └── categorical_maps.json
├── tests/
│   └── test_eta_api.py
└── requirements.txt
```

## Setup

1. **Copy the trained model files** from `ml-engine/model/` into
   `api-gateway/app/ml_models/`:

   ```bash
   # from the gatisync/ root
   cp ml-engine/model/eta_lightgbm.txt api-gateway/app/ml_models/
   cp ml-engine/model/categorical_maps.json api-gateway/app/ml_models/
   ```

   Do this every time you retrain — this service reads its own local copy,
   not `ml-engine/` directly, so it can be containerized and deployed
   independently.

2. **Install dependencies:**

   ```bash
   cd api-gateway
   pip install -r requirements.txt
   ```

3. **Run the API:**

   ```bash
   uvicorn app.main:app --reload --port 8000
   ```

4. **Check it's alive:**

   ```bash
   curl http://localhost:8000/health
   ```

   You should see `"model_loaded": true`. If it says `false`, the model
   files aren't in `app/ml_models/` — go back to step 1.

5. **Try a prediction** (or just open http://localhost:8000/docs for the
   interactive Swagger UI):

   ```bash
   curl -X POST http://localhost:8000/predict-eta \
     -H "Content-Type: application/json" \
     -d '{
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
         "weather_severity": 0
       }
     }'
   ```

   Expected response shape:

   ```json
   {
     "route_id": "R1",
     "segment_id": "R1_S1",
     "predicted_travel_time_seconds": 62.7,
     "predicted_travel_time_minutes": 1.05,
     "model_version": "lightgbm-v1"
   }
   ```

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Load-balancer/uptime check — confirms the model is loaded |
| `POST` | `/predict-eta` | ETA for one upcoming segment |
| `POST` | `/predict-eta/trip` | Sums ETA across multiple upcoming segments (a full stop-to-stop journey) |

`/predict-eta/trip` is what the commuter PWA will actually call most —
"how long until the bus reaches MY stop" is usually several segments away,
not just the next one.

## Notes on design choices

- **Model loads once at startup**, not per-request (see `main.py`'s
  `lifespan` handler). LightGBM booster loading has real I/O overhead —
  doing it per-request would blow your 1.5s end-to-end latency target.
- **`current_speed` / `previous_segment_speed` are optional** in the
  request schema. Real driver-app GPS pings drop packets (your own
  simulator models this with ~3% missing data) — the API needs to accept
  `null` here rather than reject the request, exactly like the training
  data does.
- **Unseen category warning**: if a request comes in with a `route_id` or
  `segment_id` the model never saw during training (e.g. you added a new
  route to the city but haven't retrained), the service logs a warning
  instead of silently mis-predicting. Watch your logs for these after
  adding new routes.
- **CORS is wide open (`allow_origins=["*"]`)** for local development.
  Before any real deployment, restrict this to your actual PWA's domain in
  `main.py`.

## Testing

```bash
pip install pytest
pytest tests/
```

The tests accept either `200` or `503` for prediction endpoints, since CI
environments won't have the model file present — that's intentional so
tests don't require committing model binaries to git. Once you run these
locally with the model files in place, you should see real `200` responses
with populated ETA values.

## Next step: hook this into the Go ingestion worker / Redis flow

Per the architecture diagram, the actual runtime flow is:

```
Redis (live bus state) --> this FastAPI service --> Redis (predicted ETA) --> WebSocket to PWA
```

Right now this service only answers on-demand HTTP requests. The next
piece is a small background loop (in `services/` here, or as a Go
component) that:
1. Reads each active bus's current segment + speed from Redis
2. Calls `eta_service.predict_segment_seconds()` internally (already
   importable — no need to go through HTTP for this internal loop)
2. Writes the predicted ETA back to Redis
3. The existing WebSocket layer pushes that to the commuter PWA on the
   next tick

This is also where live drift-detection (comparing actual bus position vs.
last prediction, to catch incidents early) would plug in.
