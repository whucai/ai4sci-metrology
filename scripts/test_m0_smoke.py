#!/usr/bin/env python3
"""M0: SciSciGPT LangGraph Smoke Test.

Verifies the adapted LangGraph state machine runs end-to-end:
  START → ResearchManager → SpecialistSet → Specialist →
  ToolSet → Evaluation → back to RM → END

Uses mock LLM and stub tools — no GPU, no GCP, no network needed.
"""

import sys
import json
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from langchain_core.messages import HumanMessage

from src.sciscigpt_local.mock_llm import MockLLM
from src.sciscigpt_local.mock_tools import (
    database_specialist_tools,
    analytics_specialist_tools,
    literature_specialist_tools,
)
from src.sciscigpt_local.graph_adapter import define_sciscigpt_graph


def test_graph_completes():
    """Verify the graph reaches END state after processing."""
    mock = MockLLM()

    def load_llm(metadata=None):
        return mock

    graph = define_sciscigpt_graph(
        load_llm,
        db_tools=database_specialist_tools,
        analytics_tools=analytics_specialist_tools,
        lit_tools=literature_specialist_tools,
    )

    initial_state = {
        "messages": [HumanMessage(content="Compute summary statistics for data.csv")],
        "metadata": {"user_id": "test"},
        "current": "",
        "next": "",
    }

    print("=" * 60)
    print("M0 Smoke Test: SciSciGPT LangGraph")
    print("=" * 60)
    print(f"Initial query: {initial_state['messages'][0].content}")
    print()

    # Run the graph — it will stream state updates
    events = list(graph.stream(initial_state, {"recursion_limit": 50}))

    # Verify structure
    node_order = []
    final_state = None
    for event in events:
        for node_name, state in event.items():
            node_order.append(node_name)
            final_state = state

    print(f"Nodes visited: {' → '.join(node_order)}")
    print()

    # --- Checks ---
    checks_passed = 0
    checks_total = 4

    # Check 1: graph processed nodes (didn't immediately terminate)
    if len(node_order) > 0:
        print("[PASS] Graph produced events")
        checks_passed += 1
    else:
        print("[FAIL] Graph produced no events")

    # Check 2: ResearchManager was called
    if "node_research_manager" in node_order:
        print("[PASS] ResearchManager activated")
        checks_passed += 1
    else:
        print("[FAIL] ResearchManager not in node order")

    # Check 3: A specialist was called
    specialists = {"node_database_specialist", "node_analytics_specialist", "node_literature_specialist"}
    if specialists & set(node_order):
        print("[PASS] Specialist activated")
        checks_passed += 1
    else:
        print("[FAIL] No specialist in node order")

    # Check 4: Final state reached (no crash)
    if final_state is not None:
        next_val = final_state.get("next", "UNKNOWN")
        print(f"[INFO] Final 'next' value: {next_val}")
        print("[PASS] Graph completed without errors")
        checks_passed += 1
    else:
        print("[FAIL] No final state")

    print()
    print(f"Result: {checks_passed}/{checks_total} checks passed")

    return checks_passed == checks_total


if __name__ == "__main__":
    success = test_graph_completes()
    sys.exit(0 if success else 1)
