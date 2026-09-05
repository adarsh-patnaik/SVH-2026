"""
simulate_data.py

Generates synthetic "historical" bus GPS/segment travel-time data calibrated
to realistic Indian Tier-2/3 city traffic dynamics.

Replaces the toy deterministic formula with rich real-world dynamics:
  - 6 routes with 6-10 segments each across diverse urban topologies
  - 8 distinct segment types: market, residential, highway, school_zone,
    flyover, narrow_lane, commercial_hub, signalized_corridor
  - Non-deterministic events:
      * Random incidents (~2% of segments encounter breakdowns, minor accidents,
        waterlogging chokes causing 2.0x-4.5x traversal delays)
      * Discrete traffic signal delays and bus-stop dwell jitter
      * Driver behavior variance (aggressive, cautious, average)
      * Sensor/telemetry noise on current_speed and previous_segment_speed
        (simulating noisy GPS checkpoints rather than ground truth)
      * Telemetry packet loss: ~3% missing/NaN readings
  - Full calendar year (365 days):
      * Monsoon season (June-September) with rain clustering & waterlogging penalties
      * Festival season spikes (Diwali/Dussehra in Oct/Nov, Holi in March)
      * Winter morning fog delays (Dec-Jan early morning highway/flyover slowdowns)
      * School dropoff/dismissal congestion windows vs school holidays

Outputs:
  data/simulated_trips.csv
"""

import os
import numpy as np
import pandas as pd
from datetime import datetime, timedelta

# Fix seed for reproducible baseline generation
np.random.seed(42)

# ---------------------------------------------------------------------------
# 1. Route Topologies for Tier-2 Indian City
# ---------------------------------------------------------------------------
ROUTES = {
    "R1": {  # Central Bus Station <-> Industrial Suburb (16.3 km)
        "description": "Central Bus Station to Phase-II Industrial Estate",
        "segments": [
            {"segment_id": "R1_S1", "distance_km": 0.9, "type": "market"},
            {"segment_id": "R1_S2", "distance_km": 1.4, "type": "signalized_corridor"},
            {"segment_id": "R1_S3", "distance_km": 2.6, "type": "flyover"},
            {"segment_id": "R1_S4", "distance_km": 1.1, "type": "narrow_lane"},
            {"segment_id": "R1_S5", "distance_km": 2.2, "type": "residential"},
            {"segment_id": "R1_S6", "distance_km": 3.8, "type": "highway"},
            {"segment_id": "R1_S7", "distance_km": 1.8, "type": "school_zone"},
            {"segment_id": "R1_S8", "distance_km": 2.5, "type": "commercial_hub"},
        ],
    },
    "R2": {  # Railway Station <-> University Campus (11.9 km)
        "description": "Railway Station to Central University",
        "segments": [
            {"segment_id": "R2_S1", "distance_km": 0.8, "type": "market"},
            {"segment_id": "R2_S2", "distance_km": 1.0, "type": "narrow_lane"},
            {"segment_id": "R2_S3", "distance_km": 2.1, "type": "signalized_corridor"},
            {"segment_id": "R2_S4", "distance_km": 3.2, "type": "flyover"},
            {"segment_id": "R2_S5", "distance_km": 1.9, "type": "residential"},
            {"segment_id": "R2_S6", "distance_km": 1.3, "type": "school_zone"},
            {"segment_id": "R2_S7", "distance_km": 1.6, "type": "residential"},
        ],
    },
    "R3": {  # Ring Road Circular (25.0 km)
        "description": "Outer Ring Road Circular Expressway",
        "segments": [
            {"segment_id": "R3_S1", "distance_km": 4.2, "type": "highway"},
            {"segment_id": "R3_S2", "distance_km": 1.5, "type": "commercial_hub"},
            {"segment_id": "R3_S3", "distance_km": 3.6, "type": "flyover"},
            {"segment_id": "R3_S4", "distance_km": 1.2, "type": "market"},
            {"segment_id": "R3_S5", "distance_km": 2.8, "type": "residential"},
            {"segment_id": "R3_S6", "distance_km": 4.5, "type": "highway"},
            {"segment_id": "R3_S7", "distance_km": 1.7, "type": "signalized_corridor"},
            {"segment_id": "R3_S8", "distance_km": 2.4, "type": "flyover"},
            {"segment_id": "R3_S9", "distance_km": 3.1, "type": "highway"},
        ],
    },
    "R4": {  # Old City Heritage Shuttle (6.3 km)
        "description": "Old City Walled Heritage Shuttle",
        "segments": [
            {"segment_id": "R4_S1", "distance_km": 0.8, "type": "narrow_lane"},
            {"segment_id": "R4_S2", "distance_km": 1.1, "type": "market"},
            {"segment_id": "R4_S3", "distance_km": 0.9, "type": "market"},
            {"segment_id": "R4_S4", "distance_km": 0.7, "type": "narrow_lane"},
            {"segment_id": "R4_S5", "distance_km": 1.3, "type": "signalized_corridor"},
            {"segment_id": "R4_S6", "distance_km": 1.5, "type": "commercial_hub"},
        ],
    },
    "R5": {  # Airport & Outskirts Express (19.8 km)
        "description": "Interstate Terminal to Airport Outer Corridor",
        "segments": [
            {"segment_id": "R5_S1", "distance_km": 1.6, "type": "commercial_hub"},
            {"segment_id": "R5_S2", "distance_km": 4.0, "type": "flyover"},
            {"segment_id": "R5_S3", "distance_km": 4.5, "type": "highway"},
            {"segment_id": "R5_S4", "distance_km": 2.2, "type": "signalized_corridor"},
            {"segment_id": "R5_S5", "distance_km": 3.5, "type": "highway"},
            {"segment_id": "R5_S6", "distance_km": 2.8, "type": "residential"},
            {"segment_id": "R5_S7", "distance_km": 1.2, "type": "commercial_hub"},
        ],
    },
    "R6": {  # District Hospital & Suburban Connector (14.1 km)
        "description": "District Civil Hospital to Suburban Sports Complex",
        "segments": [
            {"segment_id": "R6_S1", "distance_km": 1.2, "type": "signalized_corridor"},
            {"segment_id": "R6_S2", "distance_km": 1.5, "type": "school_zone"},
            {"segment_id": "R6_S3", "distance_km": 2.3, "type": "residential"},
            {"segment_id": "R6_S4", "distance_km": 2.9, "type": "flyover"},
            {"segment_id": "R6_S5", "distance_km": 1.4, "type": "market"},
            {"segment_id": "R6_S6", "distance_km": 1.0, "type": "narrow_lane"},
            {"segment_id": "R6_S7", "distance_km": 2.0, "type": "residential"},
            {"segment_id": "R6_S8", "distance_km": 1.8, "type": "commercial_hub"},
        ],
    },
}

# ---------------------------------------------------------------------------
# 2. Segment Physical Calibration Parameters
# ---------------------------------------------------------------------------
SEGMENT_BASE_SPEED_KMH = {
    "market": 13.5,
    "narrow_lane": 11.0,
    "commercial_hub": 16.5,
    "school_zone": 18.0,
    "signalized_corridor": 21.0,
    "residential": 23.0,
    "highway": 36.0,
    "flyover": 42.0,
}

SEGMENT_SPEED_VARIANCE = {
    "market": 4.5,
    "narrow_lane": 3.5,
    "commercial_hub": 4.0,
    "school_zone": 4.0,
    "signalized_corridor": 4.5,
    "residential": 5.0,
    "highway": 6.5,
    "flyover": 5.0,
}

# Standard Indian urban peak traffic windows (hours in 24h float)
GENERAL_PEAK_WINDOWS = [(8.0, 10.5), (17.5, 20.5)]
SCHOOL_PEAK_WINDOWS = [(7.5, 8.75), (13.5, 15.25)]
MARKET_PEAK_WINDOWS = [(17.0, 21.5)]


def time_of_day_bin(hour_float: float) -> str:
    """Bucket the hour into 15-min bins, e.g. '08:00-08:15'."""
    total_minutes = int(hour_float * 60)
    bin_start = (total_minutes // 15) * 15
    h, m = divmod(bin_start, 60)
    h_end, m_end = divmod(bin_start + 15, 60)
    return f"{h:02d}:{m:02d}-{h_end:02d}:{m_end:02d}"


def is_in_windows(hour_float: float, windows) -> bool:
    return any(start <= hour_float <= end for start, end in windows)


def get_calendar_attributes(dt: datetime):
    """
    Computes seasonal and holiday markers for Indian calendar:
    - Monsoon season: June 15 to Sept 15 (high rain probability, waterlogging)
    - Festival season: Diwali / Dussehra window (Oct 18 to Nov 8), Holi (March 14)
    - Winter fog: Dec 15 to Jan 25 early mornings
    - Standard gazetted holidays
    """
    month = dt.month
    day = dt.day
    day_of_week = dt.weekday()
    is_weekend = int(day_of_week >= 5)

    is_monsoon = 1 if (month in (7, 8) or (month == 6 and day >= 15) or (month == 9 and day <= 15)) else 0
    is_festival = 1 if (month == 10 and day >= 18) or (month == 11 and day <= 8) or (month == 3 and 12 <= day <= 16) else 0
    is_winter_fog = 1 if (month == 12 and day >= 15) or (month == 1 and day <= 25) else 0

    # Fixed gazetted holidays + festival days
    fixed_holidays = [
        (1, 26),  # Republic Day
        (3, 14),  # Holi
        (8, 15),  # Independence Day
        (10, 2),  # Gandhi Jayanti
        (10, 24), # Dussehra
        (11, 1),  # Diwali
        (12, 25), # Christmas
    ]
    is_holiday = 1 if (month, day) in fixed_holidays or is_weekend else 0

    # Weather simulation: monsoon has ~55% rain chance; other months ~8% chance
    rain_prob = 0.55 if is_monsoon else 0.08
    weather_severity = 1 if np.random.rand() < rain_prob else 0

    return {
        "day_of_week": day_of_week,
        "is_weekend": is_weekend,
        "is_holiday": is_holiday,
        "is_monsoon": is_monsoon,
        "is_festival": is_festival,
        "is_winter_fog": is_winter_fog,
        "weather_severity": weather_severity,
    }


def simulate_segment_traversal(
    seg_type: str,
    distance_km: float,
    hour_float: float,
    cal: dict,
    driver_factor: float,
    prev_speed: float,
):
    """
    Simulates physical traversal of a segment including:
    - Base road speed with congestion slowdowns
    - Weather / seasonal penalties
    - Signal delays & passenger boarding dwell times
    - Random non-deterministic incidents (breakdown, accident) on ~2% of trips
    - Sensor jitter on observed speed features
    """
    base_speed = SEGMENT_BASE_SPEED_KMH[seg_type]
    variance = SEGMENT_SPEED_VARIANCE[seg_type]

    speed = base_speed

    # 1. Peak hour congestion penalties
    if is_in_windows(hour_float, GENERAL_PEAK_WINDOWS):
        penalty_map = {
            "market": 0.40,
            "narrow_lane": 0.35,
            "commercial_hub": 0.35,
            "school_zone": 0.25,
            "signalized_corridor": 0.30,
            "residential": 0.20,
            "highway": 0.15,
            "flyover": 0.12,
        }
        speed *= (1.0 - penalty_map.get(seg_type, 0.20))

    # School zone specific dropoff/pickup windows
    if seg_type == "school_zone" and not cal["is_holiday"]:
        if is_in_windows(hour_float, SCHOOL_PEAK_WINDOWS):
            speed *= 0.55  # 45% additional slowdown during school rush

    # Market / Commercial evening rush
    if seg_type in ("market", "commercial_hub"):
        if is_in_windows(hour_float, MARKET_PEAK_WINDOWS):
            speed *= 0.70  # heavy pedestrian and shopper friction

    # Festival season traffic surges in commercial/market areas
    if cal["is_festival"] and seg_type in ("market", "commercial_hub", "narrow_lane"):
        speed *= 0.80

    # Winter morning fog reduction on expressways / flyovers
    if cal["is_winter_fog"] and hour_float <= 8.5 and seg_type in ("highway", "flyover"):
        speed *= 0.75

    # Weekend effect: higher near markets, lighter elsewhere
    if cal["is_weekend"]:
        if seg_type in ("market", "commercial_hub"):
            speed *= 0.88  # busy markets on weekends
        else:
            speed *= 1.12  # lighter commuter traffic

    # Weather penalty
    if cal["weather_severity"] == 1:
        rain_speed_penalty = np.random.uniform(0.65, 0.82)
        speed *= rain_speed_penalty
        if seg_type in ("market", "narrow_lane") and cal["is_monsoon"]:
            # Waterlogging vulnerability
            speed *= np.random.uniform(0.70, 0.88)

    # Driver factor variation (aggressive: >1.0, cautious: <1.0)
    speed *= driver_factor

    # Natural stochastic traffic fluctuation
    speed += np.random.normal(0, variance * 0.35)
    traversal_speed = max(speed, 5.0)

    # 2. Add discrete signal delays and bus-stop dwell times
    # In reality, travel time is not just distance/speed; it includes stopped time
    dwell_delay_sec = 0.0
    if seg_type == "signalized_corridor":
        # 1-3 traffic lights along the corridor, average red phase wait
        num_signals = np.random.choice([1, 2, 3], p=[0.3, 0.5, 0.2])
        dwell_delay_sec += sum(np.random.uniform(10, 55) for _ in range(num_signals))
    elif seg_type in ("market", "commercial_hub", "residential"):
        # Passenger boarding/alighting dwell at intermediate stops
        dwell_delay_sec += np.random.uniform(15, 45)
    elif seg_type == "school_zone" and is_in_windows(hour_float, SCHOOL_PEAK_WINDOWS):
        dwell_delay_sec += np.random.uniform(25, 60)

    # 3. Non-deterministic incident simulation (~2% probability)
    # Breakdown, minor accident, road repair bottleneck, VIP movement
    is_incident = np.random.rand() < 0.02
    incident_delay_sec = 0.0
    if is_incident:
        slowdown_multiplier = np.random.uniform(2.0, 4.5)
        incident_delay_sec = (distance_km / traversal_speed * 3600) * (slowdown_multiplier - 1.0)
        # Cap excessive synthetic delays to realistic range (2 to 10 minutes extra)
        incident_delay_sec = min(incident_delay_sec, 600.0)

    # Compute ground truth travel time in seconds
    cruise_time_seconds = (distance_km / traversal_speed) * 3600
    travel_time_seconds = cruise_time_seconds + dwell_delay_sec + incident_delay_sec

    # 4. Generate observed sensor speeds with realistic GPS noise & jitter
    # Real sensors measure speed at the segment entry gate or rolling 30s average,
    # which has sensor noise and does NOT equal distance / travel_time_seconds
    sensor_noise = np.random.normal(0, 2.2)  # +/- ~2.2 km/h GPS noise
    observed_current_speed = max(traversal_speed + sensor_noise, 3.0)

    if prev_speed is not None:
        observed_prev_speed = max(prev_speed + np.random.normal(0, 2.0), 3.0)
    else:
        observed_prev_speed = observed_current_speed

    # 5. Simulate real-world packet drops / missing telemetry (~3% of rows)
    if np.random.rand() < 0.03:
        observed_current_speed = np.nan
    if np.random.rand() < 0.03:
        observed_prev_speed = np.nan

    return {
        "traversal_speed": traversal_speed,
        "travel_time_seconds": round(travel_time_seconds, 1),
        "current_speed": round(observed_current_speed, 2) if not np.isnan(observed_current_speed) else np.nan,
        "previous_segment_speed": round(observed_prev_speed, 2) if not np.isnan(observed_prev_speed) else np.nan,
        "is_incident": int(is_incident),
    }


def generate_trips(n_days: int = 365, trips_per_route_per_day: int = 10):
    """
    Generates full-year synthetic historical bus segment travel times across all routes.
    """
    rows = []
    start_date = datetime(2025, 1, 1)

    print(f"Generating synthetic data for {n_days} days across {len(ROUTES)} routes...")

    for day_offset in range(n_days):
        current_date = start_date + timedelta(days=day_offset)
        cal = get_calendar_attributes(current_date)
        date_str = current_date.strftime("%Y-%m-%d")

        for route_id, route in ROUTES.items():
            for trip_idx in range(trips_per_route_per_day):
                # Spread trips across 16-hour transit window: 06:00 to 22:00
                start_hour = np.random.uniform(6.0, 21.5)
                current_hour = start_hour

                # Driver behavior variation profile for this trip (aggressive, cautious, average)
                driver_factor = np.clip(np.random.normal(1.0, 0.07), 0.85, 1.18)
                prev_speed = None

                for seg in route["segments"]:
                    seg_id = seg["segment_id"]
                    seg_type = seg["type"]
                    distance_km = seg["distance_km"]

                    sim_result = simulate_segment_traversal(
                        seg_type=seg_type,
                        distance_km=distance_km,
                        hour_float=current_hour,
                        cal=cal,
                        driver_factor=driver_factor,
                        prev_speed=prev_speed,
                    )

                    travel_time_hours = sim_result["travel_time_seconds"] / 3600.0

                    rows.append({
                        "date": date_str,
                        "route_id": route_id,
                        "segment_id": seg_id,
                        "segment_type": seg_type,
                        "distance_km": distance_km,
                        "day_of_week": cal["day_of_week"],
                        "is_weekend": cal["is_weekend"],
                        "is_holiday": cal["is_holiday"],
                        "hour_of_day": round(current_hour, 2),
                        "time_of_day_bin": time_of_day_bin(current_hour),
                        "weather_severity": cal["weather_severity"],
                        "current_speed": sim_result["current_speed"],
                        "previous_segment_speed": sim_result["previous_segment_speed"],
                        "travel_time_seconds": sim_result["travel_time_seconds"],
                        "is_incident": sim_result["is_incident"],
                    })

                    prev_speed = sim_result["traversal_speed"]
                    current_hour = min(current_hour + travel_time_hours, 23.95)

    df = pd.DataFrame(rows)
    return df


if __name__ == "__main__":
    out_dir = "data"
    os.makedirs(out_dir, exist_ok=True)
    os.makedirs(os.path.join(out_dir, "simulated"), exist_ok=True)

    df = generate_trips(n_days=365, trips_per_route_per_day=10)

    # Save to standard primary path and mirrored path
    primary_path = os.path.join(out_dir, "simulated_trips.csv")
    mirror_path = os.path.join(out_dir, "simulated", "simulated_trips.csv")

    df.to_csv(primary_path, index=False)
    df.to_csv(mirror_path, index=False)

    print(f"\nSuccessfully generated {len(df):,} segment records.")
    print(f"Date range: {df['date'].min()} to {df['date'].max()} ({df['date'].nunique()} days)")
    print(f"Routes: {df['route_id'].nunique()} ({list(ROUTES.keys())})")
    print(f"Segment types: {df['segment_type'].nunique()} ({df['segment_type'].unique().tolist()})")
    print(f"Incident trips: {df['is_incident'].sum():,} ({df['is_incident'].mean()*100:.2f}%)")
    print(f"Missing current_speed: {df['current_speed'].isna().sum():,} ({df['current_speed'].isna().mean()*100:.2f}%)")
    print(f"Missing previous_segment_speed: {df['previous_segment_speed'].isna().sum():,} ({df['previous_segment_speed'].isna().mean()*100:.2f}%)")
    print(f"Mean segment travel time: {df['travel_time_seconds'].mean():.1f}s ({df['travel_time_seconds'].mean()/60:.2f} min)")
    print(f"P50 travel time: {df['travel_time_seconds'].median():.1f}s, P90: {df['travel_time_seconds'].quantile(0.9):.1f}s")
    print(f"Saved dataset to {primary_path} and {mirror_path}")
