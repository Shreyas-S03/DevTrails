from __future__ import annotations

import os

# Keeps joblib quiet in constrained/sandboxed environments.
os.environ.setdefault("LOKY_MAX_CPU_COUNT", "1")

FEATURE_COLUMNS_V0 = (
    "historical_rain_mm",
    "zone_risk_index",
    "rider_experience_months",
)

FEATURE_COLUMNS_V1 = (
    "historical_rain_mm",
    "zone_risk_index",
    "rider_experience_months",
    "aqi_index",
    "strike_intensity_index",
    "seasonal_risk_index",
    "zone_baseline_risk",
)

TARGET_COLUMN = "risk_score"

MONOTONIC_CONSTRAINTS_V1 = {
    "historical_rain_mm": 1,
    "zone_risk_index": 1,
    "rider_experience_months": -1,
    "aqi_index": 1,
    "strike_intensity_index": 1,
    "seasonal_risk_index": 1,
    "zone_baseline_risk": 1,
}

RISK_SCORE_MIN = 0.1
RISK_SCORE_MAX = 1.0
WEEKLY_PREMIUM_MIN = 15.0
WEEKLY_PREMIUM_MAX = 40.0
