"""
tune_hyperparams.py

Hyperparameter optimization for the LightGBM ETA model using Optuna and
strict temporal expanding-window cross-validation.

To prevent temporal data leakage:
  - The final 28 days of the 365-day dataset are held out entirely as the test set.
  - Hyperparameter tuning is executed strictly on the preceding development dates.
  - 3-fold expanding temporal validation is used:
      * Fold 1: Train days 1-180, Validate days 181-235
      * Fold 2: Train days 1-235, Validate days 236-285
      * Fold 3: Train days 1-285, Validate days 286-337

Outputs:
  model/best_params.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import lightgbm as lgb
import optuna
from sklearn.metrics import mean_absolute_error

optuna.logging.set_verbosity(optuna.logging.WARNING)

DATA_PATH = "data/simulated_trips.csv"
OUTPUT_PARAMS_PATH = "model/best_params.json"


def load_dataset(path: str):
    if not os.path.exists(path):
        alt_path = os.path.join(os.path.dirname(path), "simulated", "simulated_trips.csv")
        if os.path.exists(alt_path):
            path = alt_path
        else:
            raise FileNotFoundError(f"Dataset not found at {path} or {alt_path}")

    df = pd.read_csv(path)
    df["date"] = pd.to_datetime(df["date"])
    df = df.sort_values(["date", "hour_of_day"]).reset_index(drop=True)

    categorical_cols = ["route_id", "segment_id", "segment_type", "time_of_day_bin"]
    for col in categorical_cols:
        df[col] = df[col].astype("category")

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

    return df, feature_cols, target_col, categorical_cols


def get_temporal_folds(df: pd.DataFrame, test_days: int = 28):
    """
    Splits development set into 3 expanding temporal folds.
    """
    unique_dates = sorted(df["date"].unique())
    dev_dates = unique_dates[:-test_days]  # Hold out final test days

    n_dev = len(dev_dates)
    # Define expanding cutoff points
    fold1_train_end = dev_dates[int(n_dev * 0.55)]
    fold1_val_end = dev_dates[int(n_dev * 0.70)]

    fold2_train_end = fold1_val_end
    fold2_val_end = dev_dates[int(n_dev * 0.85)]

    fold3_train_end = fold2_val_end
    fold3_val_end = dev_dates[-1]

    folds = [
        (dev_dates[0], fold1_train_end, fold1_train_end, fold1_val_end),
        (dev_dates[0], fold2_train_end, fold2_train_end, fold2_val_end),
        (dev_dates[0], fold3_train_end, fold3_train_end, fold3_val_end),
    ]
    return folds


def objective(trial, df, feature_cols, target_col, categorical_cols, folds):
    # Optuna search space
    params = {
        "objective": "regression",
        "metric": "mae",
        "boosting_type": "gbdt",
        "verbosity": -1,
        "n_jobs": -1,
        "learning_rate": trial.suggest_float("learning_rate", 0.02, 0.12, log=True),
        "num_leaves": trial.suggest_int("num_leaves", 20, 100),
        "max_depth": trial.suggest_int("max_depth", 4, 10),
        "min_child_samples": trial.suggest_int("min_child_samples", 20, 80),
        "subsample": trial.suggest_float("subsample", 0.65, 0.95),
        "subsample_freq": trial.suggest_int("subsample_freq", 1, 5),
        "colsample_bytree": trial.suggest_float("colsample_bytree", 0.65, 0.95),
        "reg_alpha": trial.suggest_float("reg_alpha", 1e-3, 5.0, log=True),
        "reg_lambda": trial.suggest_float("reg_lambda", 1e-3, 5.0, log=True),
    }

    fold_maes = []

    for fold_idx, (tr_start, tr_end, val_start, val_end) in enumerate(folds):
        train_mask = (df["date"] >= tr_start) & (df["date"] <= tr_end)
        val_mask = (df["date"] > val_start) & (df["date"] <= val_end)

        X_tr, y_tr = df.loc[train_mask, feature_cols], df.loc[train_mask, target_col]
        X_val, y_val = df.loc[val_mask, feature_cols], df.loc[val_mask, target_col]

        train_data = lgb.Dataset(X_tr, label=y_tr, categorical_feature=categorical_cols)
        val_data = lgb.Dataset(X_val, label=y_val, categorical_feature=categorical_cols, reference=train_data)

        model = lgb.train(
            params,
            train_data,
            num_boost_round=300,
            valid_sets=[val_data],
            callbacks=[lgb.early_stopping(stopping_rounds=25, verbose=False)],
        )

        preds = model.predict(X_val, num_iteration=model.best_iteration)
        mae = mean_absolute_error(y_val, preds)
        fold_maes.append(mae)

    return float(np.mean(fold_maes))


def run_tuning(n_trials: int = 25):
    print("Loading dataset for hyperparameter optimization...")
    df, feature_cols, target_col, categorical_cols = load_dataset(DATA_PATH)

    folds = get_temporal_folds(df, test_days=28)
    print(f"Constructed {len(folds)} expanding temporal cross-validation folds on dev set.")

    sampler = optuna.samplers.TPESampler(seed=42)
    study = optuna.create_study(direction="minimize", sampler=sampler)

    print(f"Starting Optuna search ({n_trials} trials)...")
    study.optimize(
        lambda trial: objective(trial, df, feature_cols, target_col, categorical_cols, folds),
        n_trials=n_trials,
        show_progress_bar=True,
    )

    best_trial = study.best_trial
    print("\n--- Hyperparameter Optimization Complete ---")
    print(f"Best Temporal CV MAE: {best_trial.value:.2f} seconds ({best_trial.value/60:.2f} minutes)")
    print("Optimal Parameters:")
    for k, v in best_trial.params.items():
        print(f"  {k}: {v}")

    # Build final parameter dictionary
    best_params = {
        "objective": "regression",
        "metric": "mae",
        "boosting_type": "gbdt",
        "verbosity": -1,
        "n_jobs": -1,
        **best_trial.params,
    }

    os.makedirs(os.path.dirname(OUTPUT_PARAMS_PATH), exist_ok=True)
    with open(OUTPUT_PARAMS_PATH, "w") as f:
        json.dump(best_params, f, indent=2)

    print(f"\nSaved optimal parameters to {OUTPUT_PARAMS_PATH}")
    return best_params


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Tune LightGBM ETA model hyperparameters.")
    parser.add_argument("--n-trials", type=int, default=25, help="Number of Optuna trials")
    args = parser.parse_args()

    run_tuning(n_trials=args.n_trials)
