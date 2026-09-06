# GatiSync ETA Inference API

FastAPI service wrapping the trained LightGBM ETA model from `ml-engine/` —
the "API/ML Service" box in the architecture diagram. Called by the
commuter PWA (and eventually the Go ingestion worker / Redis flow) to get
predicted bus segment travel times.

**Status: hardened and fully tested — 10/10 tests passing.**

## Folder structure

```
api-gateway/
├── app/
│   ├── main.py                    # FastAPI entrypoint, CORS, rate limiter, startup model load
│   ├── rate_limit.py               # shared slowapi Limiter instance
│   ├── routers/
│   │   └── eta.py                 # /predict-eta, /predict-eta/trip, /health
│   ├── services/
│   │   └── eta_service.py         # loads LightGBM model, explicit categorical encoding, self-test
│   ├── models/
│   │   └── schemas.py             # request/response schemas with length/range bounds
│   └── ml_models/                 # trained model files go here (see Setup)
│       ├── eta_lightgbm.txt
│       └── categorical_maps.json
├── tests/
│   └── test_eta_api.py            # 10 tests, all asserting real values — not just status codes
└── requirements.txt
```

## Setup

1. **Copy the trained model files** from `ml-engine/model/`:

   ```bash
   cp ml-engine/model/eta_lightgbm.txt api-gateway/app/ml_models/
   cp ml-engine/model/categorical_maps.json api-gateway/app/ml_models/
   ```

   Do this after every retrain — `api-gateway` reads its own local copy
   so it can be containerized/deployed independently of `ml-engine`.
   `model_version` in every response is a SHA-256 hash of the actual
   loaded model file, so a mismatched or stale copy is always visible,
   never silent.

2. **Install dependencies:**

   ```bash
   cd api-gateway
   pip install -r requirements.txt --user
   ```

   Dependencies use bounded ranges (`>=X,<X+1`), not exact pins — exact
   pins broke on Python 3.14 because `pydantic-core`'s older patch
   versions have no prebuilt wheel for it and fail to compile from source.
   Bounded ranges let pip pick a compatible patch release while still
   protecting against a surprise major-version bump later.

3. **Run the API:**

   ```bash
   python -m uvicorn app.main:app --port 8000
   ```

   (Use `python -m uvicorn ...` rather than bare `uvicorn ...` if your
   `pip install --user` Scripts folder isn't on PATH. `--reload` can be
   flaky on very new Python versions on Windows — omit it if you hit
   reloader subprocess errors.)

4. **Check it's alive:**

   ```bash
   curl http://localhost:8000/health
   ```

   Expect:
   ```json
   {"status":"ok","model_loaded":true,"model_version":"<12-char hash>","self_test_ok":true,"self_test_detail":"OK — sample prediction: ...s"}
   ```

   `self_test_ok: true` means the API didn't just load the model file —
   it ran a real prediction against a known category and confirmed the
   output is a sane number. If this is ever `false`, the model loaded but
   something in the categorical encoding or feature pipeline is broken —
   don't demo until this says `true`.

## Endpoints

| Method | Path | Purpose |
|---|---|---|
| `GET` | `/health` | Runs a real self-test prediction, not just an is-loaded check |
| `POST` | `/predict-eta` | ETA for one upcoming segment |
| `POST` | `/predict-eta/trip` | Sums ETA across up to 60 segments (a full stop-to-stop journey) |

## Testing

```bash
pip install pytest --user
python -m pytest tests/ -v
```

**10 tests, all passing:**
- Health self-test reports a real prediction, not just `is_loaded`
- Single-segment prediction returns a plausible value (not zero/negative/absurd)
- Prediction is stable regardless of input dict key ordering (encoding-stability guard)
- Unseen category (never seen during training) doesn't crash the request
- Missing GPS sensor data (`current_speed`/`previous_segment_speed: null`) is handled — coerced to `NaN`, not rejected
- Trip ETA correctly sums per-segment predictions
- More than 60 segments in one trip request is rejected (422) — DoS-via-batch-size guard
- An oversized string field is rejected (422)
- Error responses never leak raw exception text, file paths, or tracebacks
- Rate limiting actually triggers a `429` after 20 requests/minute

The `client` fixture uses `with TestClient(app) as c:` — this is required
for FastAPI's `lifespan` startup handler (which loads the model) to
actually run during tests. Without it, every test fails with "model not
loaded" even though the real server works fine — this bit us once already,
worth remembering if tests mysteriously start failing again after an
unrelated change.

## Security hardening (two review rounds)

| Issue | Fix |
|---|---|
| Categorical encoding could theoretically drift from training-time codes | Explicit `pd.Categorical(..., categories=<training list>)` built from `categorical_maps.json`, not left to library defaults |
| `/health` reported "loaded" even if predictions were silently broken | Runs a real self-test prediction at startup and on every `/health` call |
| Model/category-map files could drift out of sync after a manual copy | `model_version` is a content hash of the actual loaded file — mismatches are visible, not silent |
| Tests only checked HTTP status codes | Tests assert real predicted values, encoding stability, and content of error responses |
| Wide-open CORS (`*`) with no enforcement | Refuses to start under `ENVIRONMENT=production/staging` unless `ALLOWED_ORIGINS` is explicitly set |
| No cap on `/predict-eta/trip` batch size | Capped at 60 segments — closes a DoS vector that bypassed the per-request rate limiter |
| Raw exception text returned to clients | Full details logged server-side (`logger.exception`); client gets a generic message |
| Unbounded string fields | `max_length` added to all ID/type fields |
| Unbounded dependency versions | Bounded to `>=X,<X+1` ranges |
| No rate limiting | `slowapi`, 20 req/min per IP, matching the original project doc's security spec |
| Missing GPS sensor data (`null` speed fields) crashed with a 400 | Explicit `pd.to_numeric(..., errors="coerce")` turns `None` into proper `NaN`, which LightGBM handles as intended |

## Known limitations (being upfront about scope)

- `/health`'s self-test validates ONE known-good sample — it confirms the
  pipeline works at all, not that every route/segment predicts well.
  Model quality is what `ml-engine`'s MAPE/MAE evaluation is for.
- Rate limiting is in-memory per-process. Fine for a single-instance demo;
  would need a Redis backend if this ever runs as multiple replicas behind
  a load balancer.
- `ALLOWED_ORIGINS` still defaults to `*` when `ENVIRONMENT` is unset or
  `development` — this is intentional for local dev, but the app will
  now refuse to start with a wildcard under `production`/`staging`.
- A `Pandas4Warning` appears in test output about categorical construction
  behavior changing in a future pandas version (unseen categories will
  raise instead of silently becoming NaN). Not a current bug — just worth
  knowing before an unrelated `pip install --upgrade` down the line.

## Next step: wire this into the Go ingestion worker / Redis flow

Per the architecture diagram, the target runtime flow is:

```
Redis (live bus state) --> this FastAPI service --> Redis (predicted ETA) --> WebSocket to PWA
```

Currently this service only answers on-demand HTTP requests. The next
piece is a background loop that reads each active bus's current segment
from Redis, calls `eta_service.predict_segment_seconds()` internally,
writes the ETA back to Redis, and lets the existing WebSocket layer push
it to the commuter PWA. This is also where live drift-detection (comparing
actual bus position vs. last prediction, to catch incidents early) plugs in.