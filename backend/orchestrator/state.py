from __future__ import annotations

from typing import Any
from typing_extensions import TypedDict


class ClaimState(TypedDict):
    rider_id: str
    disruption: dict[str, Any]
    rider_db_data: dict[str, Any]
    is_parametric_valid: bool
    is_fraud: bool
    hgbr_event_risk: float
    final_decision: dict[str, Any]
