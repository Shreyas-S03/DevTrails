from __future__ import annotations

from datetime import datetime, timedelta, timezone
from typing import Any

from .config import DISRUPTION_TYPE_MAP, OrchestratorSettings


def normalize_disruption_type(raw_type: str) -> str | None:
    return DISRUPTION_TYPE_MAP.get(raw_type.strip().lower()) or DISRUPTION_TYPE_MAP.get(raw_type)


def current_utc_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def monday_week_start_iso(today: datetime | None = None) -> str:
    now = today or datetime.now(timezone.utc)
    monday = (now - timedelta(days=now.weekday())).date()
    return monday.isoformat()


def derive_zone_risk_index(zone: str) -> int:
    # Stable deterministic mapping to [1, 10] without external lookup tables.
    checksum = sum((idx + 1) * ord(ch) for idx, ch in enumerate(zone))
    return (checksum % 10) + 1


def derive_seasonal_risk_index(now: datetime | None = None) -> float:
    month = (now or datetime.now(timezone.utc)).month
    monsoon_months = {6, 7, 8, 9}
    pollution_months = {11, 12, 1, 2}

    monsoon_score = 1.0 if month in monsoon_months else 0.25
    pollution_score = 1.0 if month in pollution_months else 0.35
    seasonal = (0.6 * monsoon_score) + (0.4 * pollution_score)
    return round(min(max(seasonal, 0.0), 1.0), 4)


def disruption_threshold_met(
    disruption_type: str,
    intensity_value: float,
    settings: OrchestratorSettings,
) -> bool:
    if disruption_type == "EXTREME_WEATHER":
        return intensity_value > settings.weather_intensity_threshold_mm
    if disruption_type == "SEVERE_POLLUTION":
        return intensity_value > settings.pollution_intensity_threshold_aqi
    if disruption_type == "LOCAL_STRIKE":
        return intensity_value > settings.strike_intensity_threshold
    return False


def build_hgbr_feature_vector(
    rider_db_data: dict[str, Any],
    disruption: dict[str, Any],
) -> list[float]:
    disruption_type = disruption.get("normalized_type", "")
    intensity_value = float(disruption.get("intensity_value", 0.0))
    zone = str(disruption.get("zone", "")).strip()

    zone_risk_index = derive_zone_risk_index(zone if zone else "UNKNOWN_ZONE")
    zone_baseline_risk = round(zone_risk_index / 10.0, 4)
    rider_experience_months = float(
        rider_db_data.get("profile", {}).get("experience_months", 12.0)
    )

    historical_rain_mm = 25.0
    aqi_index = 90.0
    strike_intensity_index = 8.0

    if disruption_type == "EXTREME_WEATHER":
        historical_rain_mm = intensity_value
    elif disruption_type == "SEVERE_POLLUTION":
        aqi_index = intensity_value
    elif disruption_type == "LOCAL_STRIKE":
        strike_intensity_index = intensity_value * 100.0 if intensity_value <= 1.0 else intensity_value

    strike_intensity_index = min(max(strike_intensity_index, 0.0), 100.0)
    seasonal_risk_index = derive_seasonal_risk_index()

    return [
        float(historical_rain_mm),
        float(zone_risk_index),
        float(max(rider_experience_months, 1.0)),
        float(aqi_index),
        float(strike_intensity_index),
        float(seasonal_risk_index),
        float(zone_baseline_risk),
    ]


def map_api_claim_status_to_db_status(claim_status: str) -> str:
    if claim_status == "APPROVED":
        return "APPROVED"
    if claim_status == "MANUAL_REVIEW":
        return "PENDING"
    return "REJECTED"
