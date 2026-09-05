"""
train_model.py

Trains a LightGBM regressor to predict bus segment `travel_time_seconds`
using strict temporal train/validation/test splitting to eliminate data leakage.

Methodology:
  - Dataset is sorted chronologically by date and time of day.
  - Test Set: Final 28 days held out completely (~1 month unseen future data).
  - Validation Set: Preceding 28 days used for early stopping & hyperparameter verification.
  - Train Set: All preceding days (~10 months historical data).
  - Uses hyperparameters from `model/best_params.json` (produced by tune_hyperparams.py)
    or well-regularized defaults.
  - Natively handles missing values (NaNs from dropped telemetry packets).

Usage:
  python src/train_model.py
  python src/train_model.py --tune --n-trials 25
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import lightgbm as lgb
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error

DATA_PATH = "data/simulated_trips.csv"
MODEL_OUT = "model/eta_lightgbm.txt"
ENCODERS_OUT = "model/categorical_maps.json"
PARAMS_IN = "model/best_params.json"
METADATA_OUT = "model/train_metadata.json"
TEST_DATA_OUT = "data/test_trips.csv"

FEATURE_COLS = [
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
CATEGORICAL_COLS = ["route_id", "segment_id", "segment_type", "time_of_day_bin"]
TARGET_COL = "travel_time_seconds"


def load_and_split_data(path: str, test_days: int = 28, val_days: int = 28):
    """
    Loads dataset, enforces categorical types, saves category maps,
    and performs a strict temporal split by date.
    """
    if not os.path.exists(path):
        alt_path = os.path.join(os.path.dirname(path), "simulated", "simulated_trips.csv")
        if os.path.exists(alt_path):
            path = alt_path
        else:
            raise FileNotFoundError(f"Dataset not found at {path} or {alt_path}")

    print(f"Loading dataset from {path}...")
    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "hour_of_day"]).reset_index(drop=True)

    # Encode categoricals and record category mapping
    cat_maps = {}
    for col in CATEGORICAL_COLS:
        df[col] = df[col].astype("category")
        cat_maps[col] = {int(i): str(cat) for i, cat in enumerate(df[col].cat.categories)}

    # Temporal split by unique dates
    unique_dates = sorted(df["date"].unique())
    total_days = len(unique_dates)

    if total_days < (test_days + val_days + 14):
        raise ValueError(f"Dataset has {total_days} days, insufficient for temporal split ({test_days} test + {val_days} val).")

    test_dates = unique_dates[-test_days:]
    val_dates = unique_dates[-(test_days + val_days): -test_days]
    train_dates = unique_dates[: -(test_days + val_days)]

    train_df = df[df["date"].isin(train_dates)].copy()
    val_df = df[df["date"].isin(val_dates)].copy()
    test_df = df[df["date"].isin(test_dates)].copy()

    print("\n--- Temporal Dataset Partitioning ---")
    print(f"Train Set:      {len(train_df):,} rows | {train_df['date'].min().strftime('%Y-%m-%d')} to {train_df['date'].max().strftime('%Y-%m-%d')} ({len(train_dates)} days)")
    print(f"Validation Set: {len(val_df):,} rows | {val_df['date'].min().strftime('%Y-%m-%d')} to {val_df['date'].max().strftime('%Y-%m-%d')} ({len(val_dates)} days)")
    print(f"Test Set:       {len(test_df):,} rows | {test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')} ({len(test_dates)} days)")

    # Save test set for independent evaluation script
    os.makedirs(os.path.dirname(TEST_DATA_OUT), exist_ok=True)
    test_df.to_csv(TEST_DATA_OUT, index=False)

    return train_df, val_df, test_df, cat_maps


def get_model_params(params_path: str) -> dict:
    """
    Loads Optuna-tuned parameters if available, otherwise returns well-calibrated defaults.
    """
    if os.path.exists(params_path):
        print(f"Loading tuned hyperparameters from {params_path}...")
        with open(params_path, "r") as f:
            params = json.load(f)
    else:
        print("Tuned params not found. Using calibrated default parameters.")
        params = {
            "objective": "regression",
            "metric": "mae",
            "boosting_type": "gbdt",
            "learning_rate": 0.05,
            "num_leaves": 45,
            "max_depth": 7,
            "min_child_samples": 40,
            "subsample": 0.85,
            "subsample_freq": 2,
            "colsample_bytree": 0.85,
            "reg_alpha": 0.1,
            "reg_lambda": 0.5,
            "verbosity": -1,
            "n_jobs": -1,
        }
    return params


def train(train_df: pd.DataFrame, val_df: pd.DataFrame, test_df: pd.DataFrame, params: dict):
    """
    Trains the LightGBM model with early stopping on temporal validation set
    and evaluates generalization on the held-out temporal test set.
    """
    X_train, y_train = train_df[FEATURE_COLS], train_df[TARGET_COL]
    X_val, y_val = val_df[FEATURE_COLS], val_df[TARGET_COL]
    X_test, y_test = test_df[FEATURE_COLS], test_df[TARGET_COL]

    train_data = lgb.Dataset(X_train, label=y_train, categorical_feature=CATEGORICAL_COLS)
    val_data = lgb.Dataset(X_val, label=y_val, categorical_feature=CATEGORICAL_COLS, reference=train_data)

    print("\nTraining LightGBM regressor with early stopping...")
    model = lgb.train(
        params,
        train_data,
        num_boost_round=600,
        valid_sets=[train_data, val_data],
        valid_names=["train", "val"],
        callbacks=[
            lgb.early_stopping(stopping_rounds=35, verbose=True),
            lgb.log_evaluation(period=50),
        ],
    )

    # Predictions on unseen temporal test set
    preds = model.predict(X_test, num_iteration=model.best_iteration)
    mae = mean_absolute_error(y_test, preds)
    mape = mean_absolute_percentage_error(y_test, preds) * 100
    rmse = np.sqrt(np.mean((y_test.values - preds) ** 2))
    median_ae = np.median(np.abs(y_test.values - preds))

    print("\n==================================================")
    print("      HONEST EVALUATION ON HELD-OUT TEST SET       ")
    print("==================================================")
    print(f"Temporal Window:     {test_df['date'].min().strftime('%Y-%m-%d')} to {test_df['date'].max().strftime('%Y-%m-%d')}")
    print(f"Total Test Samples:  {len(y_test):,}")
    print(f"MAE (seconds):       {mae:.2f} s")
    print(f"MAE (minutes):       {mae / 60.0:.2f} min")
    print(f"Median Absolute Err: {median_ae:.2f} s ({median_ae / 60.0:.2f} min)")
    print(f"RMSE (seconds):      {rmse:.2f} s ({rmse / 60.0:.2f} min)")
    print(f"MAPE:                {mape:.2f}%")
    print("--------------------------------------------------")
    print(f"Doc Specification Target: < 180s (3.0 min) segment/journey error")
    print(f"Target Assessment:        {'PASS - WELL WITHIN TARGET' if mae < 180 else 'EXCEEDS TARGET'}")
    print("==================================================\n")

    # Feature importances
    print("--- Top Feature Importances (Gain) ---")
    importance = pd.Series(
        model.feature_importance(importance_type="gain"), index=FEATURE_COLS
    ).sort_values(ascending=False)
    for feat, imp in importance.items():
        print(f"  {feat:<24}: {imp:,.1f}")

    metrics = {
        "mae_seconds": float(mae),
        "mae_minutes": float(mae / 60.0),
        "median_ae_seconds": float(median_ae),
        "rmse_seconds": float(rmse),
        "mape_percent": float(mape),
        "best_iteration": int(model.best_iteration),
        "num_test_samples": int(len(y_test)),
        "test_date_start": test_df["date"].min().strftime("%Y-%m-%d"),
        "test_date_end": test_df["date"].max().strftime("%Y-%m-%d"),
    }
    return model, metrics


def main(tune: bool = False, n_trials: int = 25):
    if tune:
        from tune_hyperparams import run_tuning
        print("Running Optuna hyperparameter optimization before training...")
        run_tuning(n_trials=n_trials)

    train_df, val_df, test_df, cat_maps = load_and_split_data(DATA_PATH)
    params = get_model_params(PARAMS_IN)

    model, metrics = train(train_df, val_df, test_df, params)

    os.makedirs(os.path.dirname(MODEL_OUT), exist_ok=True)
    model.save_model(MODEL_OUT)
    print(f"\nModel saved to {MODEL_OUT}")

    with open(ENCODERS_OUT, "w") as f:
        json.dump(cat_maps, f, indent=2)
    print(f"Category maps saved to {ENCODERS_OUT}")

    metadata = {
        "metrics": metrics,
        "parameters": params,
        "features": FEATURE_COLS,
        "categoricals": CATEGORICAL_COLS,
    }
    with open(METADATA_OUT, "w") as f:
        json.dump(metadata, f, indent=2)
    print(f"Training metadata saved to {METADATA_OUT}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Train LightGBM ETA prediction model.")
    parser.add_argument("--tune", action="store_true", help="Run Optuna hyperparameter tuning first")
    parser.add_argument("--n-trials", type=int, default=25, help="Number of Optuna trials if --tune is set")
    args = parser.parse_args()

    main(tune=args.tune, n_trials=args.n_trials)
