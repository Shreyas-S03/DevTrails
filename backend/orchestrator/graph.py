from __future__ import annotations

from langgraph.graph import END, StateGraph

from .config import OrchestratorSettings
from .nodes import (
    make_evaluate_parametric_node,
    make_execute_decision_node,
    make_fetch_db_context_node,
    make_fraud_check_node,
    make_risk_evaluator_node,
)
from .repository import SupabaseRepository
from .state import ClaimState


def build_claim_graph(
    repository: SupabaseRepository,
    settings: OrchestratorSettings,
):
    graph = StateGraph(ClaimState)

    graph.add_node("fetch_db_context", make_fetch_db_context_node(repository))
    graph.add_node("evaluate_parametric", make_evaluate_parametric_node(settings))
    graph.add_node("fraud_check_llm", make_fraud_check_node(settings))
    graph.add_node("risk_evaluator", make_risk_evaluator_node())
    graph.add_node("execute_decision", make_execute_decision_node(repository, settings))

    graph.set_entry_point("fetch_db_context")
    graph.add_edge("fetch_db_context", "evaluate_parametric")
    graph.add_edge("evaluate_parametric", "fraud_check_llm")
    graph.add_edge("fraud_check_llm", "risk_evaluator")
    graph.add_edge("risk_evaluator", "execute_decision")
    graph.add_edge("execute_decision", END)

    return graph.compile()
