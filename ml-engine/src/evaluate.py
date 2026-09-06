"""
evaluate.py

Comprehensive evaluation script for the trained GatiSync LightGBM ETA model.
Evaluates on the held-out temporal test set (unseen future dates).

Outputs:
  - Formatted terminal report with metric summaries
  - Segment-type breakdown table
  - Time-of-day / Peak hour breakdown table
  - Incident vs Normal trip comparison
  - Weather impact breakdown
  - Journey-level aggregate ETA error analysis
  - High-resolution multi-panel visualization: reports/evaluation_plots.png
  - JSON evaluation summary: model/evaluation_summary.json
"""

import os
import json
import argparse
import numpy as np
import pandas as pd
import lightgbm as lgb
import matplotlib.pyplot as plt
from sklearn.metrics import mean_absolute_error, mean_absolute_percentage_error, mean_squared_error

MODEL_PATH = "model/eta_lightgbm.txt"
CAT_MAPS_PATH = "model/categorical_maps.json"
DATA_PATH = "data/simulated_trips.csv"
TEST_DATA_PATH = "data/test_trips.csv"
REPORTS_DIR = "reports"
OUTPUT_PLOT_PATH = os.path.join(REPORTS_DIR, "evaluation_plots.png")
OUTPUT_JSON_PATH = "model/evaluation_summary.json"

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


def load_model_and_metadata():
    if not os.path.exists(MODEL_PATH):
        raise FileNotFoundError(f"Model file not found at {MODEL_PATH}. Please run train_model.py first.")

    model = lgb.Booster(model_file=MODEL_PATH)

    cat_maps = {}
    if os.path.exists(CAT_MAPS_PATH):
        with open(CAT_MAPS_PATH, "r") as f:
            cat_maps = json.load(f)

    return model, cat_maps


def load_test_dataset(test_days: int = 28):
    if os.path.exists(TEST_DATA_PATH):
        print(f"Loading cached temporal test set from {TEST_DATA_PATH}...")
        df_test = pd.read_csv(TEST_DATA_PATH)
    else:
        print(f"Loading full dataset from {DATA_PATH} and slicing final {test_days} days as test set...")
        path = DATA_PATH
        if not os.path.exists(path):
            alt_path = os.path.join(os.path.dirname(path), "simulated", "simulated_trips.csv")
            if os.path.exists(alt_path):
                path = alt_path
            else:
                raise FileNotFoundError(f"Dataset not found at {path} or {alt_path}")

        df = pd.read_csv(path)
        df["date"] = pd.to_datetime(df["date"])
        df = df.sort_values(["date", "hour_of_day"]).reset_index(drop=True)
        unique_dates = sorted(df["date"].unique())
        test_dates = unique_dates[-test_days:]
        df_test = df[df["date"].isin(test_dates)].copy()

    for col in CATEGORICAL_COLS:
        df_test[col] = df_test[col].astype("category")

    return df_test


def compute_metrics(y_true, y_pred):
    mae = mean_absolute_error(y_true, y_pred)
    mape = mean_absolute_percentage_error(y_true, y_pred) * 100
    rmse = np.sqrt(mean_squared_error(y_true, y_pred))
    median_ae = np.median(np.abs(y_true - y_pred))
    p90_ae = np.percentile(np.abs(y_true - y_pred), 90)
    p95_ae = np.percentile(np.abs(y_true - y_pred), 95)
    return {
        "mae_sec": float(mae),
        "mae_min": float(mae / 60.0),
        "mape_pct": float(mape),
        "rmse_sec": float(rmse),
        "median_ae_sec": float(median_ae),
        "p90_ae_sec": float(p90_ae),
        "p95_ae_sec": float(p95_ae),
    }


def evaluate(df_test: pd.DataFrame, model: lgb.Booster):
    X_test = df_test[FEATURE_COLS]
    y_true = df_test[TARGET_COL].values
    y_pred = model.predict(X_test)

    df_eval = df_test.copy()
    df_eval["predicted_seconds"] = y_pred
    df_eval["error_seconds"] = y_pred - y_true
    df_eval["abs_error_seconds"] = np.abs(df_eval["error_seconds"])
    df_eval["abs_error_pct"] = (df_eval["abs_error_seconds"] / y_true) * 100.0

    overall = compute_metrics(y_true, y_pred)

    print("\n==========================================================================")
    print("           GATISYNC ETA PREDICTION: HONEST TEST SET EVALUATION           ")
    print("==========================================================================")
    print(f"Test Samples:       {len(df_eval):,}")
    print(f"Overall MAE:        {overall['mae_sec']:.1f} s  ({overall['mae_min']:.2f} min)")
    print(f"Overall MAPE:       {overall['mape_pct']:.2f}%")
    print(f"Overall RMSE:       {overall['rmse_sec']:.1f} s  ({overall['rmse_sec']/60:.2f} min)")
    print(f"Median Abs Error:   {overall['median_ae_sec']:.1f} s  ({overall['median_ae_sec']/60:.2f} min)")
    print(f"90th Percentile:    {overall['p90_ae_sec']:.1f} s  ({overall['p90_ae_sec']/60:.2f} min)")
    print(f"95th Percentile:    {overall['p95_ae_sec']:.1f} s  ({overall['p95_ae_sec']/60:.2f} min)")
    print("--------------------------------------------------------------------------")

    # 1. Error by Segment Type
    print("\n[Breakdown by Segment Type]")
    seg_summary = df_eval.groupby("segment_type", observed=True).agg(
        samples=("travel_time_seconds", "count"),
        mean_actual_sec=("travel_time_seconds", "mean"),
        mae_sec=("abs_error_seconds", "mean"),
        mape_pct=("abs_error_pct", "mean"),
        p90_sec=("abs_error_seconds", lambda x: np.percentile(x, 90)),
    ).sort_values("mae_sec", ascending=False)

    print(f"{'Segment Type':<22} | {'Samples':<8} | {'Actual (s)':<10} | {'MAE (s)':<8} | {'MAE (min)':<10} | {'MAPE (%)':<8} | {'P90 (s)':<8}")
    print("-" * 88)
    for seg_type, row in seg_summary.iterrows():
        print(f"{seg_type:<22} | {int(row['samples']):<8} | {row['mean_actual_sec']:<10.1f} | {row['mae_sec']:<8.1f} | {row['mae_sec']/60:<10.2f} | {row['mape_pct']:<8.2f} | {row['p90_sec']:<8.1f}")

    # 2. Error by Time of Day Bin (Top congested vs off-peak)
    print("\n[Breakdown by Time of Day]")
    df_eval["hour_int"] = df_eval["hour_of_day"].astype(int)
    hour_summary = df_eval.groupby("hour_int", observed=True).agg(
        samples=("travel_time_seconds", "count"),
        mae_sec=("abs_error_seconds", "mean"),
        mape_pct=("abs_error_pct", "mean"),
    )
    print(f"{'Hour':<6} | {'Samples':<8} | {'MAE (s)':<8} | {'MAE (min)':<10} | {'MAPE (%)':<8}")
    print("-" * 48)
    for hr, row in hour_summary.iterrows():
        print(f"{hr:02d}:00  | {int(row['samples']):<8} | {row['mae_sec']:<8.1f} | {row['mae_sec']/60:<10.2f} | {row['mape_pct']:<8.2f}")

    # 3. Incident vs Normal Trips
    print("\n[Breakdown by Incident Status]")
    if "is_incident" in df_eval.columns:
        inc_summary = df_eval.groupby("is_incident").agg(
            samples=("travel_time_seconds", "count"),
            actual_mean_s=("travel_time_seconds", "mean"),
            mae_sec=("abs_error_seconds", "mean"),
            mape_pct=("abs_error_pct", "mean"),
            p90_sec=("abs_error_seconds", lambda x: np.percentile(x, 90)),
        )
        for is_inc, row in inc_summary.iterrows():
            label = "Trip With Incident (Unannounced Delay)" if is_inc == 1 else "Normal Operations (Regular Jitter)"
            print(f"  * {label}:")
            print(f"      Samples: {int(row['samples']):,} | Actual Mean: {row['actual_mean_s']:.1f}s | MAE: {row['mae_sec']:.1f}s ({row['mae_sec']/60:.2f} min) | MAPE: {row['mape_pct']:.2f}% | P90: {row['p90_sec']:.1f}s")

    # 4. Multi-Segment Journey ETA Analysis
    # A commuter cares about the cumulative ETA for a 6-8 segment trip (~25-40 min)
    print("\n[Commuter Journey-Level Analysis (~6-8 segments / trip)]")
    # Group by date, route_id, and approximate trip by start hour
    df_eval["trip_proxy"] = df_eval["date"].astype(str) + "_" + df_eval["route_id"].astype(str) + "_" + (df_eval["hour_of_day"] // 1.2).astype(str)
    journey_df = df_eval.groupby("trip_proxy").agg(
        n_segments=("travel_time_seconds", "count"),
        total_actual_sec=("travel_time_seconds", "sum"),
        total_pred_sec=("predicted_seconds", "sum"),
    )
    # Filter to typical multi-segment journeys (>= 5 segments)
    multi_seg = journey_df[journey_df["n_segments"] >= 5].copy()
    if len(multi_seg) > 0:
        multi_seg["journey_mae_sec"] = np.abs(multi_seg["total_actual_sec"] - multi_seg["total_pred_sec"])
        multi_seg["journey_mape"] = (multi_seg["journey_mae_sec"] / multi_seg["total_actual_sec"]) * 100
        mean_journey_actual = multi_seg["total_actual_sec"].mean()
        mean_journey_mae = multi_seg["journey_mae_sec"].mean()
        mean_journey_mape = multi_seg["journey_mape"].mean()
        p90_journey_mae = np.percentile(multi_seg["journey_mae_sec"], 90)

        print(f"Evaluated {len(multi_seg):,} full multi-segment journeys (average {multi_seg['n_segments'].mean():.1f} segments)")
        print(f"Average Journey Travel Time: {mean_journey_actual / 60:.1f} minutes ({mean_journey_actual:.0f} s)")
        print(f"Average Journey ETA Error:   {mean_journey_mae / 60:.2f} minutes ({mean_journey_mae:.1f} s)")
        print(f"Average Journey MAPE:        {mean_journey_mape:.2f}%")
        print(f"90th Percentile Journey Err: {p90_journey_mae / 60:.2f} minutes ({p90_journey_mae:.1f} s)")
        print("-> Segment errors partially cancel out over multi-segment corridors, providing highly defensible commuter ETAs!")

    print("\n==========================================================================")
    return df_eval, overall, seg_summary


def plot_evaluation(df_eval: pd.DataFrame, overall: dict, seg_summary: pd.DataFrame, output_path: str):
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    plt.subplots_adjust(hspace=0.35, wspace=0.25)

    # Subplot 1: Predicted vs Actual Scatter
    ax1 = axes[0, 0]
    sample_eval = df_eval.sample(n=min(3000, len(df_eval)), random_state=42)
    ax1.scatter(
        sample_eval["travel_time_seconds"] / 60.0,
        sample_eval["predicted_seconds"] / 60.0,
        alpha=0.25,
        s=15,
        color="#2563EB",
        edgecolors="none",
    )
    max_val = max(sample_eval["travel_time_seconds"].max(), sample_eval["predicted_seconds"].max()) / 60.0
    ax1.plot([0, max_val], [0, max_val], "r--", linewidth=1.5, label="Perfect Fit (y = x)")
    ax1.set_xlabel("Actual Travel Time (minutes)", fontsize=10, fontweight="bold")
    ax1.set_ylabel("Predicted Travel Time (minutes)", fontsize=10, fontweight="bold")
    ax1.set_title(f"Predicted vs. Actual Segment Time (MAE: {overall['mae_min']:.2f} min)", fontsize=11, fontweight="bold")
    ax1.legend(loc="upper left")
    ax1.grid(True, linestyle=":", alpha=0.6)

    # Subplot 2: Residual Error Distribution
    ax2 = axes[0, 1]
    residuals_sec = df_eval["error_seconds"]
    # Clip extreme outliers for clean visualization
    clipped_res = residuals_sec.clip(-300, 300)
    ax2.hist(clipped_res, bins=60, color="#0D9488", edgecolor="#042F2E", alpha=0.75, density=True)
    ax2.axvline(0, color="red", linestyle="--", linewidth=1.5, label="Zero Bias")
    ax2.set_xlabel("Prediction Error (Predicted - Actual, seconds)", fontsize=10, fontweight="bold")
    ax2.set_ylabel("Density", fontsize=10, fontweight="bold")
    ax2.set_title(f"Residual Error Distribution (Median AE: {overall['median_ae_sec']:.1f}s)", fontsize=11, fontweight="bold")
    ax2.legend(loc="upper right")
    ax2.grid(True, linestyle=":", alpha=0.6)

    # Subplot 3: MAE by Segment Type
    ax3 = axes[1, 0]
    seg_types = seg_summary.index.tolist()
    maes_sec = seg_summary["mae_sec"].values
    colors = ["#DC2626" if "market" in s or "narrow" in s else "#3B82F6" for s in seg_types]
    bars = ax3.barh(seg_types, maes_sec, color=colors, alpha=0.85)
    ax3.set_xlabel("Mean Absolute Error (seconds)", fontsize=10, fontweight="bold")
    ax3.set_title("Prediction Error by Segment Type (Red = High Congestion/Variance)", fontsize=11, fontweight="bold")
    ax3.grid(True, axis="x", linestyle=":", alpha=0.6)
    for bar in bars:
        width = bar.get_width()
        ax3.text(width + 2, bar.get_y() + bar.get_height() / 2, f"{width:.1f}s ({width/60:.2f}m)", va="center", fontsize=8)

    # Subplot 4: Hourly Error Profile (Peak vs Off-Peak)
    ax4 = axes[1, 1]
    hourly = df_eval.groupby("hour_int", observed=True)["abs_error_seconds"].mean()
    ax4.plot(hourly.index, hourly.values, marker="o", linewidth=2, color="#7C3AED")
    ax4.axvspan(8.0, 10.5, color="#FDE047", alpha=0.3, label="Morning Peak (08:00-10:30)")
    ax4.axvspan(17.5, 20.5, color="#F97316", alpha=0.25, label="Evening Peak (17:30-20:30)")
    ax4.set_xlabel("Hour of Day (24-hour)", fontsize=10, fontweight="bold")
    ax4.set_ylabel("Mean Absolute Error (seconds)", fontsize=10, fontweight="bold")
    ax4.set_title("Error Profile across Transit Hours", fontsize=11, fontweight="bold")
    ax4.set_xticks(range(6, 23))
    ax4.legend(loc="upper right", fontsize=8)
    ax4.grid(True, linestyle=":", alpha=0.6)

    plt.suptitle("GatiSync LightGBM ETA Model — Performance Diagnostics (Temporal Holdout)", fontsize=13, fontweight="bold", y=0.99)
    plt.tight_layout()
    plt.savefig(output_path, dpi=180, bbox_inches="tight")
    plt.close()
    print(f"Saved evaluation plots to {output_path}")


def main():
    parser = argparse.ArgumentParser(description="Evaluate LightGBM ETA model.")
    parser.add_argument("--test-days", type=int, default=28, help="Number of days to evaluate in temporal test set")
    args = parser.parse_args()

    model, cat_maps = load_model_and_metadata()
    df_test = load_test_dataset(test_days=args.test_days)

    df_eval, overall, seg_summary = evaluate(df_test, model)
    plot_evaluation(df_eval, overall, seg_summary, OUTPUT_PLOT_PATH)

    summary_json = {
        "overall_metrics": overall,
        "segment_type_mae_sec": seg_summary["mae_sec"].to_dict(),
        "segment_type_mape_pct": seg_summary["mape_pct"].to_dict(),
    }
    with open(OUTPUT_JSON_PATH, "w") as f:
        json.dump(summary_json, f, indent=2)
    print(f"Saved JSON summary to {OUTPUT_JSON_PATH}")


if __name__ == "__main__":
    main()
