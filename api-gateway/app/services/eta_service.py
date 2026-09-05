"""
app/services/eta_service.py

Loads the trained LightGBM model ONCE at startup (not per-request — LightGBM
model loading has real overhead, and this API needs to answer in well under
the 1.5s end-to-end latency target from the project doc, section 19).

Model artifacts are expected at:
    app/ml_models/eta_lightgbm.txt
    app/ml_models/categorical_maps.json

These are copies of what ml-engine/src/train_model.py produces in
ml-engine/model/. Copy them here after every retrain (see README for the
exact command) — this service does not read from ml-engine/ directly so that
api-gateway can be deployed/scaled as its own container independent of the
ml-engine training environment.
"""

import json
import logging
from pathlib import Path
from typing import Optional, List

import lightgbm as lgb
import pandas as pd

logger = logging.getLogger("eta_service")

MODEL_DIR = Path(__file__).resolve().parent.parent / "ml_models"
MODEL_PATH = MODEL_DIR / "eta_lightgbm.txt"
CATEGORICAL_MAPS_PATH = MODEL_DIR / "categorical_maps.json"
MODEL_VERSION = "lightgbm-v1"  # bump this manually whenever you copy in a retrained model

CATEGORICAL_COLS = ["route_id", "segment_id", "segment_type", "time_of_day_bin"]

FEATURE_ORDER = [
    "route_id",
    "segment_id",
    "segment_type",
    "time_of_day_bin",
    "day_of_week",
    "is_weekend",
    "is_holiday",
    "hour_of_day",
    "distance_km",
    "current_speed",
    "previous_segment_speed",
    "weather_severity",
]


class EtaModelNotLoadedError(RuntimeError):
    pass


class EtaService:
    """Wraps the LightGBM booster + categorical encoding so callers just pass
    plain dicts/Pydantic models and get seconds back."""

    def __init__(self):
        self._model: Optional[lgb.Booster] = None
        self._categorical_maps: dict = {}
        self._known_categories: dict = {}

    def load(self):
        if not MODEL_PATH.exists():
            raise FileNotFoundError(
                f"Model file not found at {MODEL_PATH}. "
                f"Copy it from ml-engine/model/eta_lightgbm.txt first."
            )
        self._model = lgb.Booster(model_file=str(MODEL_PATH))

        if CATEGORICAL_MAPS_PATH.exists():
            with open(CATEGORICAL_MAPS_PATH) as f:
                self._categorical_maps = json.load(f)
            # Build reverse-lookup sets so we can warn on unseen categories
            # (e.g. a route_id that didn't exist during training) instead of
            # LightGBM silently mis-encoding it.
            self._known_categories = {
                col: set(v.values()) for col, v in self._categorical_maps.items()
            }
        else:
            logger.warning(
                "categorical_maps.json not found — skipping unseen-category validation."
            )

        logger.info(f"ETA model loaded from {MODEL_PATH} (version={MODEL_VERSION})")

    @property
    def is_loaded(self) -> bool:
        return self._model is not None

    def _validate_categoricals(self, row: dict):
        for col in CATEGORICAL_COLS:
            known = self._known_categories.get(col)
            if known and row.get(col) not in known:
                logger.warning(
                    f"'{row.get(col)}' was not seen during training for column '{col}'. "
                    f"Prediction may be unreliable until the model is retrained on this route/segment."
                )

    def _build_dataframe(self, segment: dict) -> pd.DataFrame:
        row = {col: segment.get(col) for col in FEATURE_ORDER}
        df = pd.DataFrame([row])
        for col in CATEGORICAL_COLS:
            df[col] = df[col].astype("category")
        return df

    def predict_segment_seconds(self, segment: dict) -> float:
        if not self.is_loaded:
            raise EtaModelNotLoadedError("ETA model has not been loaded yet.")

        self._validate_categoricals(segment)
        df = self._build_dataframe(segment)
        prediction = self._model.predict(df)[0]
        return round(float(prediction), 1)

    def predict_trip_seconds(self, segments: List[dict]) -> List[float]:
        """Predict each segment independently and return the list — used for
        summing a full multi-segment trip ETA."""
        return [self.predict_segment_seconds(seg) for seg in segments]


# Singleton instance shared across the FastAPI app lifetime
eta_service = EtaService()