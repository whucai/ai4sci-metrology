#!/usr/bin/env python3
"""M1: SciSciGPT Baseline — Real LLM + Sandbox Executor.

Tests the adapted SciSciGPT agent graph with:
  1. Real sandbox execution (subprocess Python)
  2. Real LLM (API or local)
  3. A simple data analysis task

Usage:
  python scripts/test_m1_baseline.py
  python scripts/test_m1_baseline.py --task simple     # Quick test
  python scripts/test_m1_baseline.py --task full        # Full agent workflow
  ANTHROPIC_API_KEY=sk-xxx python scripts/test_m1_baseline.py
"""

from __future__ import annotations

import sys
import json
import argparse
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

# --- Test dataset ---
TEST_CSV = """name,age,height,weight
Alice,25,165,58
Bob,30,180,75
Charlie,22,172,68
Diana,28,160,55
Eve,35,168,62
Frank,40,175,80
Grace,27,158,52
Henry,33,185,90
Iris,29,163,57
Jack,31,178,73
"""


def test_sandbox_direct():
    """Test 1: Direct sandbox execution (no LLM needed)."""
    from src.sciscigpt_local.sandbox import execute_python

    code = """
import pandas as pd
import numpy as np
from pathlib import Path

df = pd.read_csv(Path(__file__).parent / 'data.csv')
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print()
print("Summary statistics:")
print(df.describe())
print()
print("Mean age:", df['age'].mean())
    """.strip()

    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "data.csv"
        data_path.write_text(TEST_CSV)

        # Write script that references the correct path
        script = f"""
import pandas as pd
import numpy as np

df = pd.read_csv('{data_path}')
print("Shape:", df.shape)
print("Columns:", list(df.columns))
print()
print(df.describe())
    """
        result = execute_python(script, timeout=10, workdir=tmpdir)
        success = result["exit_code"] == 0
        print(f"  exit_code: {result['exit_code']}")
        print(f"  elapsed: {result['elapsed']}s")
        print(f"  stdout: {result['stdout'][:300]}")
        if result["stderr"]:
            print(f"  stderr: {result['stderr'][:200]}")
        return success


def test_llm_available():
    """Test 2: Check if a real LLM is available."""
    import os
    if os.environ.get("ANTHROPIC_API_KEY"):
        print("  Anthropic API key found")
        return True
    if os.environ.get("OPENAI_API_KEY"):
        base = os.environ.get("OPENAI_BASE_URL", "")
        model = os.environ.get("LLM_MODEL", "")
        if base:
            print(f"  OpenAI-compatible API: {base} (model: {model})")
        else:
            print("  OpenAI API key found")
        return True
    print("  No API keys — using MockLLM")
    return False


def test_agent_with_task():
    """Test 3: Full agent graph with sandbox tools and LLM."""
    import os
    os.environ.setdefault("ANTHROPIC_BASE_URL", "https://api.deepseek.com/anthropic")

    from src.sciscigpt_local.llm_backends import load_llm_from_env
    from src.sciscigpt_local.graph_adapter import define_sciscigpt_graph
    from src.sciscigpt_local.mock_llm import MockLLM
    from src.sciscigpt_local.sandbox import execute_python, execute_r, execute_julia

    from typing import Type
    from pydantic import BaseModel, Field
    from langchain.tools import BaseTool
    from langchain_core.messages import HumanMessage

    # --- Real sandbox tools ---
    class CodeInput(BaseModel):
        code: str = Field(..., description="Code to execute in the sandbox.")
        state: dict | None = Field(default=None, description="Agent state (ignored).")

    class PythonJupyterTool(BaseTool):
        name: str = "python_jupyter"
        description: str = "Execute Python code in a sandbox. Use for data analysis, statistics, visualization."
        args_schema: Type[BaseModel] = CodeInput

        def _run(self, code: str, state: dict | None = None) -> str:
            result = execute_python(code, timeout=60)
            return json.dumps(result)

    class RJupyterTool(BaseTool):
        name: str = "r_jupyter"
        description: str = "Execute R code in a sandbox. Use for statistical analysis."
        args_schema: Type[BaseModel] = CodeInput

        def _run(self, code: str, state: dict | None = None) -> str:
            result = execute_r(code, timeout=60)
            return json.dumps(result)

    analytics_tools = [PythonJupyterTool(), RJupyterTool()]
    database_tools = []  # Stub — no local DB yet
    literature_tools = []

    # --- LLM ---
    try:
        llm = load_llm_from_env()
    except Exception as e:
        print(f"  LLM load failed: {e}, using MockLLM")
        llm = MockLLM()

    llm_type = type(llm).__name__
    print(f"  LLM: {llm_type}")

    def load_llm(metadata=None):
        return llm

    graph = define_sciscigpt_graph(
        load_llm,
        db_tools=database_tools,
        analytics_tools=analytics_tools,
        lit_tools=literature_tools,
    )

    with tempfile.TemporaryDirectory() as tmpdir:
        data_path = Path(tmpdir) / "data.csv"
        data_path.write_text(TEST_CSV)

        query = f"Load the dataset at {data_path}, compute summary statistics (mean, std, min, max) for all numeric columns, and report the results."

        initial_state = {
            "messages": [HumanMessage(content=query)],
            "metadata": {"user_id": "test_m1"},
            "current": "",
            "next": "",
        }

        print(f"  Query: {query}")
        print(f"  Running graph...")
        print()

        try:
            events = list(graph.stream(initial_state, {"recursion_limit": 30}))
        except Exception as e:
            print(f"  Graph error: {e}")
            import traceback
            traceback.print_exc()
            return False

        node_order = [list(e.keys())[0] for e in events]
        print(f"  Nodes: {' → '.join(node_order)}")
        print(f"  Total events: {len(events)}")

        # Check for sandbox execution in toolset
        toolset_visited = "node_toolset" in node_order
        evaluation_visited = "node_evaluation_specialist" in node_order
        print(f"  Toolset visited: {toolset_visited}")
        print(f"  Evaluation visited: {evaluation_visited}")

        return len(events) > 0


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--task", choices=["direct", "api", "agent", "all"], default="all")
    args = parser.parse_args()

    print("=" * 60)
    print("M1 Baseline: Real LLM + Sandbox")
    print("=" * 60)
    print()

    results = {}

    if args.task in ("direct", "all"):
        print("--- Test 1: Direct sandbox execution ---")
        results["sandbox"] = test_sandbox_direct()
        print()

    if args.task in ("api", "all"):
        print("--- Test 2: LLM availability ---")
        results["llm_available"] = test_llm_available()
        print()

    if args.task in ("agent", "all"):
        print("--- Test 3: Agent + sandbox + LLM ---")
        results["agent"] = test_agent_with_task()
        print()

    passed = sum(1 for v in results.values() if v)
    total = len(results)
    print("=" * 60)
    print(f"Result: {passed}/{total} tests passed")
    print(f"Results: {results}")

    return 0 if passed == total else 1


if __name__ == "__main__":
    sys.exit(main())
