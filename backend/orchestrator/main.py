from __future__ import annotations

from typing import Any

from fastapi import FastAPI, HTTPException

from .config import load_settings
from .graph import build_claim_graph
from .repository import SupabaseRepository
from .schemas import ClaimDecision, ClaimRequest
from .state import ClaimState
from .utils import normalize_disruption_type

app = FastAPI(
    title="AI Parametric Insurance Orchestrator",
    version="0.1.0",
)

_compiled_graph = None


@app.on_event("startup")
def startup_event() -> None:
    global _compiled_graph
    settings = load_settings()
    repository = SupabaseRepository(settings=settings)
    _compiled_graph = build_claim_graph(repository=repository, settings=settings)


def _build_initial_state(payload: ClaimRequest) -> ClaimState:
    normalized_type = normalize_disruption_type(payload.disruption.type)
    disruption_dict: dict[str, Any] = {
        "type": payload.disruption.type,
        "intensity_value": float(payload.disruption.intensity_value),
        "zone": payload.disruption.zone,
        "normalized_type": normalized_type,
    }

    initial_decision: dict[str, Any] = {}
    if normalized_type is None:
        initial_decision = {
            "claim_status": "DENIED",
            "payout_amount": 0.0,
            "reason": "Unsupported disruption type",
        }

    return ClaimState(
        rider_id=payload.rider_id,
        disruption=disruption_dict,
        rider_db_data={},
        is_parametric_valid=False,
        is_fraud=False,
        hgbr_event_risk=0.0,
        final_decision=initial_decision,
    )


@app.post("/evaluate_claim", response_model=ClaimDecision)
def evaluate_claim(payload: ClaimRequest) -> ClaimDecision:
    if _compiled_graph is None:
        raise HTTPException(status_code=500, detail="Orchestrator graph is not initialized.")

    initial_state = _build_initial_state(payload)
    final_state = _compiled_graph.invoke(initial_state)
    final_decision = final_state.get("final_decision", {})

    if not final_decision:
        raise HTTPException(status_code=500, detail="Claim evaluation did not produce a final decision.")
    return ClaimDecision(**final_decision)
