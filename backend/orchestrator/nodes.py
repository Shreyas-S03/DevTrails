from __future__ import annotations

from typing import Any, Callable
from uuid import uuid4

import numpy as np

from backend.ml.risk_model import predict_hgbr_risk

from .config import OrchestratorSettings
from .repository import SupabaseRepository
from .state import ClaimState
from .utils import (
    build_hgbr_feature_vector,
    current_utc_iso,
    disruption_threshold_met,
    map_api_claim_status_to_db_status,
    monday_week_start_iso,
)


def evaluate_parametric_rules(
    rider: dict[str, Any],
    disruption: dict[str, Any],
    settings: OrchestratorSettings,
) -> bool:
    profile = rider.get("profile", {})
    rider_zone = profile.get("primary_zone")
    rider_status = rider.get("real_time_state", {}).get("status", "")

    disruption_zone = disruption.get("zone")
    disruption_type = disruption.get("normalized_type", "")
    intensity_value = float(disruption.get("intensity_value", 0.0))

    return bool(
        disruption_threshold_met(disruption_type, intensity_value, settings)
        and (disruption_zone == rider_zone)
        and (rider_status == "ONLINE")
    )


def check_fraud_telemetry(rider_fraud_data: dict[str, Any], settings: OrchestratorSettings) -> bool:
    if bool(rider_fraud_data.get("is_mock_location_enabled", False)):
        return True
    speed = float(rider_fraud_data.get("current_speed_kmph", 0.0))
    return speed > settings.fraud_speed_threshold_kmph


def _build_decision(
    claim_status: str,
    payout_amount: float,
    reason: str,
) -> dict[str, Any]:
    return {
        "claim_status": claim_status,
        "payout_amount": round(float(max(payout_amount, 0.0)), 2),
        "reason": reason,
    }


def make_fetch_db_context_node(
    repository: SupabaseRepository,
) -> Callable[[ClaimState], ClaimState]:
    def fetch_db_context(state: ClaimState) -> ClaimState:
        if state.get("final_decision"):
            return state

        rider = repository.fetch_rider_by_id(state["rider_id"])
        if rider is None:
            state["final_decision"] = _build_decision(
                claim_status="DENIED",
                payout_amount=0.0,
                reason="Rider not found",
            )
            return state

        policy_active = bool(rider.get("insurance_profile", {}).get("policy_active", False))
        if not policy_active:
            state["rider_db_data"] = rider
            state["final_decision"] = _build_decision(
                claim_status="DENIED",
                payout_amount=0.0,
                reason="Policy inactive",
            )
            return state

        state["rider_db_data"] = rider
        return state

    return fetch_db_context


def make_evaluate_parametric_node(
    settings: OrchestratorSettings,
) -> Callable[[ClaimState], ClaimState]:
    def evaluate_parametric(state: ClaimState) -> ClaimState:
        if state.get("final_decision"):
            return state

        rider = state.get("rider_db_data", {})
        disruption = state.get("disruption", {})
        state["is_parametric_valid"] = evaluate_parametric_rules(
            rider=rider,
            disruption=disruption,
            settings=settings,
        )
        return state

    return evaluate_parametric


def make_fraud_check_node(
    settings: OrchestratorSettings,
) -> Callable[[ClaimState], ClaimState]:
    def fraud_check_llm(state: ClaimState) -> ClaimState:
        if state.get("final_decision"):
            return state

        fraud_telemetry = state.get("rider_db_data", {}).get("fraud_telemetry", {})
        state["is_fraud"] = check_fraud_telemetry(fraud_telemetry, settings=settings)
        return state

    return fraud_check_llm


def make_risk_evaluator_node() -> Callable[[ClaimState], ClaimState]:
    def risk_evaluator(state: ClaimState) -> ClaimState:
        if state.get("final_decision"):
            return state

        rider = state.get("rider_db_data", {})
        disruption = state.get("disruption", {})
        if not rider:
            state["hgbr_event_risk"] = 0.0
            return state

        features = build_hgbr_feature_vector(rider_db_data=rider, disruption=disruption)
        risk_scores = predict_hgbr_risk(np.asarray([features], dtype=float))
        state["hgbr_event_risk"] = float(risk_scores[0])
        return state

    return risk_evaluator


def make_execute_decision_node(
    repository: SupabaseRepository,
    settings: OrchestratorSettings,
) -> Callable[[ClaimState], ClaimState]:
    def execute_decision(state: ClaimState) -> ClaimState:
        if state.get("final_decision"):
            return state

        rider = state.get("rider_db_data", {})
        disruption = state.get("disruption", {})

        incentive_at_risk = float(
            rider.get("daily_performance", {}).get("incentive_at_risk", 0.0)
        )
        payout_amount = 0.0

        if not state.get("is_parametric_valid", False):
            decision = _build_decision("DENIED", payout_amount, "Parametric criteria not met")
        elif state.get("is_fraud", False):
            decision = _build_decision("FRAUD_FLAGGED", payout_amount, "Fraud Flagged")
        elif float(state.get("hgbr_event_risk", 0.0)) > settings.manual_review_risk_threshold:
            decision = _build_decision("MANUAL_REVIEW", payout_amount, "Manual Review")
        else:
            payout_amount = max(incentive_at_risk, 0.0)
            decision = _build_decision("APPROVED", payout_amount, "Approved by parametric rules")

        claim_id = f"CLM_{uuid4().hex[:12].upper()}"
        db_status = map_api_claim_status_to_db_status(decision["claim_status"])
        review_timestamp = current_utc_iso() if db_status in {"APPROVED", "REJECTED"} else None

        # DB schema requires amount > 0. Use requested amount floor for non-payout paths.
        claim_amount = max(incentive_at_risk, 0.01)

        claim_row = {
            "claim_id": claim_id,
            "rider_id": state["rider_id"],
            "amount": claim_amount,
            "status": db_status,
            "coverage_week_start": monday_week_start_iso(),
            "disruption_type": disruption.get("normalized_type"),
            "decision_reason": decision["reason"],
            "reviewed_at": review_timestamp,
            "paid_at": None,
            "evidence_snapshot": {
                "disruption": disruption,
                "is_parametric_valid": state.get("is_parametric_valid", False),
                "is_fraud": state.get("is_fraud", False),
                "hgbr_event_risk": round(float(state.get("hgbr_event_risk", 0.0)), 6),
            },
        }

        try:
            repository.insert_claim_decision(claim_row)
        except Exception as exc:
            message = str(exc)
            if "claims_one_per_week_per_disruption" in message:
                decision = _build_decision("DENIED", 0.0, "Duplicate weekly claim")
            else:
                decision = _build_decision("DENIED", 0.0, "Claim persistence failed")

        state["final_decision"] = decision
        return state

    return execute_decision
