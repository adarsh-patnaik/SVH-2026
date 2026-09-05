# GatiSync — ETA Prediction ML Engine

Ultra-low-bandwidth, high-accuracy bus segment travel time and ETA prediction system designed for Tier-2/3 Indian cities. Built for the Smart India Hackathon.

---

## 1. System Architecture & Workflow

The ML engine trains and serves a LightGBM regressor predicting `travel_time_seconds` across urban bus corridors using real-time and historical context:

```
[Driver Android App] (MQTT + Protobuf)
       │
       ▼
[Go Ingestion Worker] ──► [PostgreSQL / PostGIS + Redis]
                                   │
                                   ▼
                       [Python ML Engine (LightGBM)]
                                   │
                                   ▼
                       [FastAPI Gateway] ──► [Commuter Next.js PWA / SMS Fallback]
```

### Core Components (`gatisync/ml-engine/`)

- `src/simulator/simulate_data.py` — Generates 365 days of synthetic historical bus segment travel times across 6 distinct Indian urban transit routes (8 segment types), incorporating stochastic traffic events, signal delays, passenger dwells, driver variance, GPS sensor jitter, packet drops, and seasonal calendars (monsoon, festivals, winter fog).
- `src/tune_hyperparams.py` — Bayesian hyperparameter optimization using **Optuna** with expanding-window temporal cross-validation (zero temporal leakage). Outputs optimal configuration to `model/best_params.json`.
- `src/train_model.py` — Trains the LightGBM model with strict temporal train/val/test date splits and validation early stopping. Saves model artifact to `model/eta_lightgbm.txt` and category maps to `model/categorical_maps.json`.
- `src/evaluate.py` — Generates comprehensive evaluation diagnostics on the held-out temporal test set (unseen future month), including slice-based breakdowns by segment type, time of day, incident status, and multi-segment journey ETA error, saving visual diagnostic plots to `reports/evaluation_plots.png`.
- `src/predict_eta.py` — Production-ready inference function for `api-gateway` with strict categorical encoding consistency and graceful fallback for dropped telemetry packets (`None`/`NaN` speeds).

---

## 2. Quickstart & Execution

```bash
cd gatisync/ml-engine

# 1. Install dependencies
pip install -r requirements.txt

# 2. Generate full-year realistic synthetic dataset (164,250 records across 6 routes)
python src/simulator/simulate_data.py

# 3. (Optional) Run Optuna hyperparameter tuning across temporal cross-validation folds
python src/tune_hyperparams.py --n-trials 20

# 4. Train LightGBM model on temporal split (with early stopping & test evaluation)
python src/train_model.py

# 5. Run comprehensive test evaluation and generate diagnostic plots
python src/evaluate.py

# 6. Test single-segment inference (including dropped telemetry edge cases)
python src/predict_eta.py
```

---

## 3. Evaluation & Defensible Benchmarks

### The 3.7-Second MAE Post-Mortem: Why the Previous Result Was Invalid

An earlier prototype of this pipeline reported an MAE of **3.7 seconds** and MAPE of **0.71%**. In a real-world review or hackathon judging panel, this number is an immediate red flag indicating synthetic curve-fitting and data leakage:

1. **Inverted Deterministic Formula**: The original toy simulator computed `travel_time_seconds = (distance_km / speed_kmh) * 3600` and assigned `current_speed = speed_kmh`. LightGBM's decision trees trivially solved the inverse arithmetic relation $t = d/v$ to machine precision.
2. **Random Split Data Leakage**: A standard random 80/20 train/test split distributed trips from the exact same hour, route, and weather conditions across both training and test sets. The model memorized specific daily conditions rather than learning true generalization.

### Honest Methodology: Strict Temporal Holdout

To reflect real-world deployment where the model predicts future transit conditions from past telemetry:

- **Full-Year Calendar**: 365 days (2025-01-01 to 2025-12-31), 164,250 segment traversals across 6 routes.
- **Strict Temporal Split**:
  - **Training Set**: First 309 days (Jan 1 – Nov 5, 2025) — 139,050 rows
  - **Validation Set**: Preceding 28 days (Nov 6 – Dec 3, 2025) — 12,600 rows (used for early stopping & Optuna CV)
  - **Held-Out Test Set**: Final 28 days (Dec 4 – Dec 31, 2025) — 12,600 rows (**100% unseen future dates**)
- **Stochastic Environment**:
  - Unannounced incidents (~2% probability of breakdowns, accidents, waterlogging causing 2.0x–4.5x traversal delays).
  - GPS noise and measurement jitter ($\mathcal{N}(0, 2.2\text{ km/h})$) between entry-point checkpoint speed and actual traversal.
  - Signal phase delays and bus stop passenger boarding dwell times.
  - Telemetry packet loss (~3% missing `NaN` speeds).

### Results on Held-Out Test Set (Unseen Future Month)

| Metric | Held-Out Test Result | Interpretation / Real-World Context |
|---|---|---|
| **Segment MAE (seconds)** | **47.3 s** | Average error under 48 seconds per segment |
| **Segment MAE (minutes)** | **0.79 min** | Well within the project doc spec (< 3.0 min) |
| **Segment Median Absolute Error** | **25.6 s** (0.43 min) | Typical segment predicted within half a minute |
| **Segment MAPE** | **9.82%** | High commercial viability for dynamic ETAs |
| **Segment RMSE** | **97.2 s** | Elevated by the 2% unannounced incident tail |
| **P90 Error** | **88.0 s** (1.47 min) | 90% of all segment predictions within 1.5 min |
| **P95 Error** | **140.5 s** (2.34 min) | Captures severe peak congestion |
| **Full Journey MAE (~35-45 min trip)** | **3.76 min** (**5.93% MAPE**) | Correlated segment errors partially cancel out |

---

## 4. Performance Breakdown & Error Analysis

The diagnostic suite in `src/evaluate.py` isolates where the model performs reliably versus where traffic variance is highest:

### Error by Segment Type

| Segment Type | Test Samples | Mean Travel Time | MAE (sec) | MAE (min) | MAPE (%) | P90 Error |
|---|---|---|---|---|---|---|
| **commercial_hub** | 1,680 | 572.7 s (9.5m) | **69.4 s** | 1.16 min | 10.92% | 148.9 s |
| **market** | 1,680 | 454.7 s (7.6m) | **62.7 s** | 1.05 min | 12.92% | 129.3 s |
| **narrow_lane** | 1,400 | 369.2 s (6.2m) | **55.5 s** | 0.93 min | 13.73% | 104.5 s |
| **signalized_corridor** | 1,680 | 398.6 s (6.6m) | **46.8 s** | 0.78 min | 10.68% | 75.6 s |
| **school_zone** | 840 | 398.2 s (6.6m) | **46.3 s** | 0.77 min | 9.98% | 90.3 s |
| **residential** | 1,960 | 420.0 s (7.0m) | **38.7 s** | 0.64 min | 7.91% | 62.7 s |
| **highway** | 1,680 | 437.4 s (7.3m) | **33.0 s** | 0.55 min | 6.39% | 51.3 s |
| **flyover** | 1,680 | 299.7 s (5.0m) | **28.5 s** | 0.48 min | 7.09% | 35.7 s |

**Key Insights:**
- `market`, `narrow_lane`, and `commercial_hub` segments exhibit the highest error (55–70s MAE). This accurately reflects real Indian urban conditions where informal roadside parking, pedestrian friction, and hand-cart bottlenecks introduce non-linear variance that cannot be predicted by checkpoint speeds alone.
- `flyover` and `highway` segments are most predictable (28–33s MAE, ~6-7% MAPE), benefiting from uninterrupted flow.

### Normal Operations vs. Unannounced Incidents

- **Normal Operations (98.0% of trips)**:
  - MAE: **36.7 seconds** (0.61 min) | MAPE: **8.84%** | P90: **79.8 seconds**
- **Trips with Incident (2.0% of trips: breakdowns, waterlogging, accidents)**:
  - Actual Mean Travel Time: **988.3 seconds** (~16.5 min vs normal ~6.8 min)
  - MAE: **552.1 seconds** (9.20 min) | MAPE: **56.61%**
  - *Explanation*: When a bus encounters an unannounced accident or mechanical breakdown mid-segment, an ETA model predicting from entry-checkpoint telemetry naturally cannot anticipate the delay until subsequent telemetry pings register the stall. This explains the long right-hand tail in RMSE and P95.

### Time-of-Day Traffic Profile

- **Morning Peak (08:00 – 10:00)**: MAE rises to **60.8 – 62.4 s** (commuter & school congestion).
- **Midday Off-Peak (12:00 – 16:00)**: MAE drops to **37.1 – 40.8 s** (stable steady-state flow).
- **Evening Peak (17:00 – 20:00)**: MAE peaks at **58.1 – 66.1 s** (market + return commute friction).
- **Late Evening (21:00 – 22:00)**: MAE drops to **26.1 – 38.8 s**.

---

## 5. Visual Diagnostics

The evaluation pipeline automatically outputs high-resolution diagnostic plots to `reports/evaluation_plots.png`:
1. **Predicted vs. Actual Scatter**: Aligned with $y = x$ line, showing tight correlation with expected widening during high-congestion periods.
2. **Residual Error Distribution**: Centered tightly at 0 seconds with near-zero systematic bias (Median Absolute Error: 25.6s).
3. **MAE by Segment Type**: Visual bar chart highlighting high-friction corridors (red) versus arterial highways.
4. **Error Profile Across Transit Hours**: Line plot demonstrating the morning and evening rush-hour error spikes.

---

## 6. Route Network Topology

The simulator models 6 representative Tier-2 Indian city transit corridors:

1. **Route R1 (Central Station ↔ Industrial Area)**: 8 segments, 16.3 km (`market`, `signalized_corridor`, `flyover`, `narrow_lane`, `residential`, `highway`, `school_zone`, `commercial_hub`).
2. **Route R2 (Railway Station ↔ University)**: 7 segments, 11.9 km (`market`, `narrow_lane`, `signalized_corridor`, `flyover`, `residential`, `school_zone`, `residential`).
3. **Route R3 (Outer Ring Road Circular)**: 9 segments, 25.0 km (`highway`, `commercial_hub`, `flyover`, `market`, `residential`, `highway`, `signalized_corridor`, `flyover`, `highway`).
4. **Route R4 (Old City Heritage Shuttle)**: 6 segments, 6.3 km (`narrow_lane`, `market`, `market`, `narrow_lane`, `signalized_corridor`, `commercial_hub`).
5. **Route R5 (Airport Outer Express)**: 7 segments, 19.8 km (`commercial_hub`, `flyover`, `highway`, `signalized_corridor`, `highway`, `residential`, `commercial_hub`).
6. **Route R6 (District Hospital & Suburb Connector)**: 8 segments, 14.1 km (`signalized_corridor`, `school_zone`, `residential`, `flyover`, `market`, `narrow_lane`, `residential`, `commercial_hub`).

To plug in real-world OpenStreetMap (OSM) geometry for a specific target city (e.g., Jalandhar, Indore, Mysore), edit `ROUTES` in `src/simulator/simulate_data.py`.

---

## 7. Known Limitations & Roadmap

1. **Synthetic Training Foundation**: While the speed distributions and congestion penalties are calibrated against empirical Indian traffic literature (Vanajakshi et al., IIT Madras; Bengaluru BMTC CNI-22 GPS traces; Delhi OTD), true local telemetry must replace synthetic data once the driver app is deployed live in the target city.
2. **Dynamic Incident Re-estimation**: The current LightGBM model predicts segment time at the start of traversal. In the live production system, when the Go ingestion worker detects a bus remaining on a segment longer than $1.5 \times$ the predicted ETA, a real-time incident delay penalty is added dynamically.
3. **Continuous Retraining**: Because LightGBM trains in under 10 seconds on a standard CPU, `train_model.py` is configured to run as a nightly cron job on accumulated PostGIS segment logs.
