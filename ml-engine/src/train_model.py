"""
train_model.py

Trains a LightGBM regressor to predict `travel_time_seconds` for a bus
segment, using the features called out in the project doc (section 11):
route_id, segment_id, time_of_day_bin, day_of_week, is_holiday,
current_speed, previous_segment_speed, weather_severity.

Usage:
    python simulate_data.py        # generates data/simulated_trips.csv
    python train_model.py          # trains + evaluates + saves model
"""

import pandas as pd
import numpy as np
import lightgbm as lgb
from sklearn.model_selection import train_test_split
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error
import joblib
import json

DATA_PATH = "data/simulated_trips.csv"
MODEL_OUT = "model/eta_lightgbm.txt"
ENCODERS_OUT = "model/categorical_maps.json"


def load_and_prepare(path):
    df = pd.read_csv(path)

    # --- Feature engineering ---
    # Categorical columns: LightGBM handles these natively as category dtype,
    # but we also save a label map so the FastAPI inference service can
    # validate incoming route/segment IDs at request time.
    categorical_cols = ["route_id", "segment_id", "segment_type", "time_of_day_bin"]
    cat_maps = {}
    for col in categorical_cols:
        df[col] = df[col].astype("category")
        cat_maps[col] = dict(enumerate(df[col].cat.categories))

    feature_cols = [
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
    target_col = "travel_time_seconds"

    X = df[feature_cols]
    y = df[target_col]

    return X, y, categorical_cols, cat_maps


def train(X, y, categorical_cols):
    X_train, X_test, y_train, y_test = train_test_split(
        X, y, test_size=0.2, random_state=42
    )

    train_set = lgb.Dataset(X_train, label=y_train, categorical_feature=categorical_cols)
    val_set = lgb.Dataset(X_test, label=y_test, categorical_feature=categorical_cols, reference=train_set)

    params = {
        "objective": "regression",
        "metric": "mae",
        "boosting_type": "gbdt",
        "num_leaves": 31,
        "learning_rate": 0.05,
        "feature_fraction": 0.85,
        "bagging_fraction": 0.85,
        "bagging_freq": 5,
        "min_data_in_leaf": 30,
        "verbose": -1,
    }

    model = lgb.train(
        params,
        train_set,
        num_boost_round=500,
        valid_sets=[train_set, val_set],
        valid_names=["train", "val"],
        callbacks=[lgb.early_stopping(stopping_rounds=30), lgb.log_evaluation(period=50)],
    )

    preds = model.predict(X_test, num_iteration=model.best_iteration)
    mae = mean_absolute_error(y_test, preds)
    mape = mean_absolute_percentage_error(y_test, preds) * 100

    print("\n--- Evaluation on held-out test set ---")
    print(f"MAE:  {mae:.1f} seconds  ({mae/60:.2f} minutes)")
    print(f"MAPE: {mape:.2f}%")

    # Project target from doc section 19: < 3 min MAE for a ~30 min journey
    print(f"Target (doc spec): < 180s (3 min) MAE  -> {'PASS' if mae < 180 else 'NEEDS TUNING'}")

    print("\n--- Top feature importances ---")
    importance = pd.Series(
        model.feature_importance(importance_type="gain"), index=X.columns
    ).sort_values(ascending=False)
    print(importance.head(10))

    return model, mae, mape


if __name__ == "__main__":
    X, y, categorical_cols, cat_maps = load_and_prepare(DATA_PATH)
    model, mae, mape = train(X, y, categorical_cols)

    model.save_model(MODEL_OUT)
    with open(ENCODERS_OUT, "w") as f:
        json.dump(cat_maps, f, indent=2, default=str)

    print(f"\nModel saved to {MODEL_OUT}")
    print(f"Category maps saved to {ENCODERS_OUT}")
