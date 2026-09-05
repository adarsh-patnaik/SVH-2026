"""
simulate_data.py

Generates synthetic "historical" bus GPS/segment travel-time data that mimics
real Indian traffic patterns (rush-hour slowdowns, rain impact, weekend
differences, market-area congestion). This stands in for real Tier-2 city
data, which does not exist publicly (see project research doc, section 9).

Calibration notes (loosely grounded in the BMTC/Delhi OTD research + the
Vanajakshi et al. IIT Madras paper on heterogeneous Indian traffic):
  - Free-flow speed on an open segment: ~28-35 km/h
  - Market / congested segments: ~8-15 km/h during peak, ~15-20 km/h off-peak
  - Morning peak: 08:00-10:30, Evening peak: 17:30-20:30
  - Rain (weather_severity=1) adds a 20-40% time penalty
  - Weekends have ~15% less congestion than weekdays

Output: data/simulated_trips.csv
"""

import numpy as np
import pandas as pd
from datetime import datetime, timedelta

np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. Define your route topology (replace with real OSM-derived segments
#    for your target city, e.g. Jalandhar). Each segment is the stretch of
#    road between two consecutive stops on a route.
# ---------------------------------------------------------------------------
ROUTES = {
    "R1": {  # e.g. a route running through a market + highway stretch
        "segments": [
            {"segment_id": "R1_S1", "distance_km": 1.2, "type": "market"},
            {"segment_id": "R1_S2", "distance_km": 2.5, "type": "residential"},
            {"segment_id": "R1_S3", "distance_km": 3.8, "type": "highway"},
            {"segment_id": "R1_S4", "distance_km": 1.0, "type": "market"},
            {"segment_id": "R1_S5", "distance_km": 2.0, "type": "residential"},
        ],
    },
    "R2": {
        "segments": [
            {"segment_id": "R2_S1", "distance_km": 2.0, "type": "residential"},
            {"segment_id": "R2_S2", "distance_km": 1.5, "type": "market"},
            {"segment_id": "R2_S3", "distance_km": 4.2, "type": "highway"},
        ],
    },
}

SEGMENT_BASE_SPEED_KMH = {
    "market": 14,
    "residential": 22,
    "highway": 32,
}

SEGMENT_SPEED_VARIANCE = {
    "market": 5,
    "residential": 6,
    "highway": 7,
}

PEAK_WINDOWS = [(8, 10.5), (17.5, 20.5)]  # morning, evening (24h float hours)


def time_of_day_bin(hour_float):
    """Bucket the hour into 15-min bins, e.g. '08:00-08:15'."""
    total_minutes = int(hour_float * 60)
    bin_start = (total_minutes // 15) * 15
    h, m = divmod(bin_start, 60)
    h_end, m_end = divmod(bin_start + 15, 60)
    return f"{h:02d}:{m:02d}-{h_end:02d}:{m_end:02d}"


def is_peak(hour_float):
    return any(start <= hour_float <= end for start, end in PEAK_WINDOWS)


def simulate_segment_speed(seg_type, hour_float, is_weekend, weather_severity):
    base = SEGMENT_BASE_SPEED_KMH[seg_type]
    variance = SEGMENT_SPEED_VARIANCE[seg_type]

    speed = base

    if is_peak(hour_float):
        # Peak hours hit congested segment types hardest
        penalty = {"market": 0.45, "residential": 0.30, "highway": 0.35}[seg_type]
        speed *= (1 - penalty)

    if is_weekend:
        speed *= 1.15  # less congestion on weekends

    if weather_severity == 1:
        speed *= np.random.uniform(0.6, 0.8)  # rain penalty 20-40%

    speed += np.random.normal(0, variance * 0.3)
    return max(speed, 4.0)  # floor speed to avoid divide-by-zero / negative


def generate_trips(n_days=90, trips_per_route_per_day=40):
    rows = []
    start_date = datetime(2026, 3, 1)

    for day_offset in range(n_days):
        current_date = start_date + timedelta(days=day_offset)
        day_of_week = current_date.weekday()  # 0=Mon ... 6=Sun
        is_weekend = day_of_week >= 5
        is_holiday = 0
        # sprinkle in a few random holidays
        if np.random.rand() < 0.02:
            is_holiday = 1

        # ~20% chance of rain that day (monsoon-ish clustering could be added)
        day_weather = 1 if np.random.rand() < 0.20 else 0

        for route_id, route in ROUTES.items():
            for trip_num in range(trips_per_route_per_day):
                # spread trips across a 16-hour service day (6am - 10pm)
                start_hour = np.random.uniform(6, 22)
                current_hour = start_hour
                prev_speed = None

                for seg in route["segments"]:
                    seg_type = seg["type"]
                    distance_km = seg["distance_km"]

                    speed_kmh = simulate_segment_speed(
                        seg_type, current_hour, is_weekend or is_holiday, day_weather
                    )
                    travel_time_hours = distance_km / speed_kmh
                    travel_time_seconds = travel_time_hours * 3600

                    rows.append({
                        "date": current_date.strftime("%Y-%m-%d"),
                        "route_id": route_id,
                        "segment_id": seg["segment_id"],
                        "segment_type": seg_type,
                        "distance_km": distance_km,
                        "day_of_week": day_of_week,
                        "is_weekend": int(is_weekend),
                        "is_holiday": is_holiday,
                        "hour_of_day": round(current_hour, 2),
                        "time_of_day_bin": time_of_day_bin(current_hour),
                        "weather_severity": day_weather,
                        "current_speed": round(speed_kmh, 2),
                        "previous_segment_speed": round(prev_speed, 2) if prev_speed else round(speed_kmh, 2),
                        "travel_time_seconds": round(travel_time_seconds, 1),
                    })

                    prev_speed = speed_kmh
                    current_hour += travel_time_hours  # advance clock along the trip

    return pd.DataFrame(rows)


if __name__ == "__main__":
    df = generate_trips(n_days=90, trips_per_route_per_day=40)
    df.to_csv("data/simulated_trips.csv", index=False)
    print(f"Generated {len(df):,} segment-trip records across {df['route_id'].nunique()} routes")
    print(f"Date range: {df['date'].min()} to {df['date'].max()}")
    print(df.head())
