from __future__ import annotations

import numpy as np
import pandas as pd

from .utils import clip_risk


def generate_dummy_training_data(
    records: int = 500,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    v0 dataset for quick bootstrap with 3 baseline features.
    """
    if records <= 0:
        raise ValueError("records must be > 0")

    rng = np.random.default_rng(random_state)
    historical_rain_mm = rng.gamma(shape=2.0, scale=22.0, size=records)
    zone_risk_index = rng.integers(low=1, high=11, size=records)
    rider_experience_months = rng.integers(low=1, high=85, size=records)

    rain_norm = np.clip(historical_rain_mm / 220.0, 0.0, 1.0)
    zone_norm = (zone_risk_index - 1.0) / 9.0
    experience_norm = np.clip(rider_experience_months / 72.0, 0.0, 1.0)
    noise = rng.normal(loc=0.0, scale=0.04, size=records)

    raw_risk = (
        0.18
        + (0.42 * rain_norm)
        + (0.36 * zone_norm)
        - (0.22 * experience_norm)
        + noise
    )
    risk_score = clip_risk(raw_risk)

    return pd.DataFrame(
        {
            "historical_rain_mm": historical_rain_mm,
            "zone_risk_index": zone_risk_index,
            "rider_experience_months": rider_experience_months,
            "risk_score": risk_score,
        }
    )


def generate_dummy_training_data_v1(
    records: int = 500,
    random_state: int = 42,
) -> pd.DataFrame:
    """
    v1 synthetic dataset with better realism:
    - AQI and strike features
    - zone-level effects
    - seasonality
    - rare disruption outliers
    """
    if records <= 0:
        raise ValueError("records must be > 0")

    rng = np.random.default_rng(random_state)

    week_of_year = rng.integers(low=1, high=53, size=records)
    zone_id = rng.integers(low=1, high=16, size=records)
    rider_experience_months = rng.integers(low=1, high=97, size=records)

    zone_baseline_map = np.linspace(0.1, 0.95, 15)
    zone_baseline_risk = zone_baseline_map[zone_id - 1]
    zone_risk_index = np.clip(
        np.rint((zone_baseline_risk * 8.5) + rng.normal(loc=1.0, scale=0.9, size=records)),
        1,
        10,
    ).astype(int)

    monsoon_component = (np.sin(((week_of_year - 24) / 52.0) * 2 * np.pi) + 1.0) / 2.0
    pollution_component = (np.sin(((week_of_year - 2) / 52.0) * 2 * np.pi) + 1.0) / 2.0
    seasonal_risk_index = np.clip(
        (0.65 * monsoon_component) + (0.35 * pollution_component), 0.0, 1.0
    )

    historical_rain_mm = (
        rng.gamma(shape=2.2, scale=24.0, size=records)
        + (seasonal_risk_index * rng.uniform(40, 95, size=records))
    )
    aqi_index = (
        55
        + (pollution_component * 165)
        + (zone_baseline_risk * 30)
        + rng.normal(0, 10, size=records)
    )
    strike_intensity_index = np.clip(
        (rng.beta(a=1.6, b=5.0, size=records) * 85) + (zone_baseline_risk * 12), 0, 100
    )

    extreme_weather_shock = (rng.random(records) < 0.06).astype(int)
    pollution_shock = (rng.random(records) < 0.05).astype(int)
    strike_shock = (rng.random(records) < 0.04).astype(int)

    historical_rain_mm += extreme_weather_shock * rng.uniform(90, 170, size=records)
    aqi_index += pollution_shock * rng.uniform(90, 170, size=records)
    strike_intensity_index = np.clip(
        strike_intensity_index + strike_shock * rng.uniform(20, 60, size=records),
        0,
        100,
    )

    rain_norm = np.clip(historical_rain_mm / 320.0, 0.0, 1.0)
    zone_norm = (zone_risk_index - 1.0) / 9.0
    experience_norm = np.clip(rider_experience_months / 96.0, 0.0, 1.0)
    aqi_norm = np.clip((aqi_index - 40.0) / 300.0, 0.0, 1.0)
    strike_norm = np.clip(strike_intensity_index / 100.0, 0.0, 1.0)
    zone_base_norm = np.clip(zone_baseline_risk, 0.0, 1.0)
    noise = rng.normal(loc=0.0, scale=0.03, size=records)

    raw_risk = (
        0.11
        + (0.21 * rain_norm)
        + (0.14 * zone_norm)
        - (0.14 * experience_norm)
        + (0.19 * aqi_norm)
        + (0.15 * strike_norm)
        + (0.09 * seasonal_risk_index)
        + (0.09 * zone_base_norm)
        + (0.08 * extreme_weather_shock)
        + (0.07 * pollution_shock)
        + (0.06 * strike_shock)
        + noise
    )
    risk_score = clip_risk(raw_risk)

    return pd.DataFrame(
        {
            "historical_rain_mm": historical_rain_mm,
            "zone_risk_index": zone_risk_index,
            "rider_experience_months": rider_experience_months,
            "aqi_index": np.clip(aqi_index, 20, 500),
            "strike_intensity_index": strike_intensity_index,
            "seasonal_risk_index": seasonal_risk_index,
            "zone_baseline_risk": zone_baseline_risk,
            "week_of_year": week_of_year,
            "zone_id": zone_id,
            "risk_score": risk_score,
        }
    )
