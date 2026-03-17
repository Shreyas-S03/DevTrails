from __future__ import annotations

import os
from dataclasses import dataclass

from dotenv import load_dotenv


@dataclass(frozen=True)
class OrchestratorSettings:
    supabase_url: str
    supabase_service_role_key: str
    weather_intensity_threshold_mm: float = 15.0
    pollution_intensity_threshold_aqi: float = 200.0
    strike_intensity_threshold: float = 0.6
    fraud_speed_threshold_kmph: float = 15.0
    manual_review_risk_threshold: float = 0.95


DISRUPTION_TYPE_MAP = {
    "heavy_rain": "EXTREME_WEATHER",
    "extreme_weather": "EXTREME_WEATHER",
    "severe_pollution": "SEVERE_POLLUTION",
    "pollution": "SEVERE_POLLUTION",
    "local_strike": "LOCAL_STRIKE",
    "strike": "LOCAL_STRIKE",
    "EXTREME_WEATHER": "EXTREME_WEATHER",
    "SEVERE_POLLUTION": "SEVERE_POLLUTION",
    "LOCAL_STRIKE": "LOCAL_STRIKE",
}


def load_settings() -> OrchestratorSettings:
    # Load environment variables from .env (if present) for local development.
    load_dotenv(override=False)

    supabase_url = os.getenv("SUPABASE_URL", "").strip()
    supabase_service_role_key = (
        os.getenv("SUPABASE_SECRET_KEY", "").strip()
        or os.getenv("SUPABASE_SERVICE_ROLE_KEY", "").strip()
    )
    return OrchestratorSettings(
        supabase_url=supabase_url,
        supabase_service_role_key=supabase_service_role_key,
    )
