# GatiSync — ETA Model Training

## Why simulated data?

Real historical GPS/segment-travel-time data for Tier-2/3 Indian cities is not
publicly available (see project research doc, section 9). The judged-viable
approach is: calibrate simulation parameters against *real* patterns from
Bengaluru/Delhi, generate synthetic history for your target city's routes,
and train on that. This is exactly what "Phase 3" of the roadmap describes.

## Real datasets to pull for calibration / demo credibility

| Dataset | Use it for | Link |
|---|---|---|
| BMTC GPS traces (Bengaluru, ~2000 buses, 1 day) | Sanity-check realistic speed distributions by road type | https://github.com/HSShashank/CNI-22 |
| BMTC GTFS static | Real route/stop topology if you want a Bengaluru demo instead of a fictional city | https://baselight.app/u/kaggle/dataset/anikets95_bmtc_gtfs_dataset |
| Delhi Open Transit Data | Static GTFS is open immediately; GTFS-RT needs a free API key requested on the portal | https://otd.delhi.gov.in/documentation |
| OpenStreetMap (your target city, e.g. Jalandhar) | Real road network + segment geometry to replace the placeholder `ROUTES` dict | https://export.hotosm.org or `osmnx` Python package |

**Recommended path for the hackathon demo:** download OSM data for your
target city, define 2–3 real routes with real stops, then plug those
route/segment IDs and real distances into `simulate_data.py`'s `ROUTES`
dict. That gets you a system that's demoably tied to a real place, even
though the historical numbers are simulated.

## Files

- `simulate_data.py` — generates `data/simulated_trips.csv`, a synthetic
  history calibrated to Indian traffic patterns (rush hour, market
  congestion, rain, weekends).
- `train_model.py` — trains a LightGBM regressor on that data, evaluates
  MAE/MAPE against the doc's target (<3 min error), saves the model.
- `predict_eta.py` — example of loading the saved model for single-segment
  inference — this is what `api-gateway` will call.

## Run it

```bash
cd ml-engine
pip install -r requirements.txt

python simulate_data.py     # writes data/simulated_trips.csv
python train_model.py       # trains, evaluates, saves model/eta_lightgbm.txt
python predict_eta.py       # example single prediction
```

## Swapping in real routes

Edit the `ROUTES` dict at the top of `simulate_data.py`:

```python
ROUTES = {
    "R1": {
        "segments": [
            {"segment_id": "R1_S1", "distance_km": 1.2, "type": "market"},
            # ... pull real distances from OSM routing between your real stops
        ],
    },
}
```

Classify each real segment as `market` / `residential` / `highway` based on
what's actually along that stretch (or refine further — e.g. add a
`school_zone` type if relevant) — this categorical drives the base speed
assumption and is the single highest-leverage feature for MAE.

## Next steps once this trains cleanly

1. Wire `predict_eta.py`'s function into a FastAPI route in `api-gateway/app/services/`.
2. Retrain periodically as real driver-app GPS pings accumulate — replace
   `simulated_trips.csv` with real aggregated segment times once you have
   even a few days of live data; LightGBM retrains in seconds so this can
   run as a nightly cron job.
3. Add `weather_severity` from a real weather API (e.g. OpenWeatherMap) once
   you're past the MVP stage — the doc lists this under "Advanced" scope.
