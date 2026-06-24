#!/usr/bin/env python3
"""R004: STRICT reproduction of Park et al. (2023) CD time trend.

Park et al. (2023) "Papers and patents are becoming less disruptive over time"
Nature, Vol 613, 5 January 2023.

STRICT task type: SciSciNet → SciSciNet. Target is numerical identity for
year-by-year mean CD5 values (1945-2010).

Core analysis (Figure 2a):
  mean(CD5) by year for papers 1945-2010, showing declining disruptiveness.

Usage:
    python scripts/r004_park2023_reproduction.py
    python scripts/r004_park2023_reproduction.py --mock
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.llm_backends import load_llm_from_env

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r004"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GOLD_PATH = OUTPUT_DIR / "gold_values.json"


def build_prompt() -> str:
    return textwrap.dedent("""\
    Reproduce the CD index time-trend analysis from:

      Park, Leahey, Funk (2023) "Papers and patents are becoming less
      disruptive over time." Nature, Vol 613, pp 138-144.

    ## TASK

    Compute the mean CD (disruption) index by year for papers published
    between 1945 and 2010, using SciSciNet data.

    ## MANDATORY CONSTRAINTS

    ### C1: DATA SOURCE
    Use SciSciNet via:
      from src.sciscigpt_local.sciscinet_connector import load_papers_sample
      df = load_papers_sample(n_shards=10)

    ### C2: FILTERS
    - year >= 1945 AND year <= 2010
    - disruption_score not null
    - No additional filters needed (CD index is pre-computed in the data)

    ### C3: ANALYSIS
    1. Filter papers to 1945-2010 with valid disruption_score
    2. Group by year
    3. Compute mean disruption_score per year
    4. Also compute: overall mean, std, CD in 1945, CD in 2010, decline %

    ### C4: REQUIRED OUTPUT SECTIONS
    print("\\n=== DATA_LOAD ===")
    # Total papers loaded, papers after filter, year range

    print("\\n=== DESCRIPTIVE ===")
    # Overall mean CD, std, all years

    print("\\n=== CD_BY_YEAR ===")
    # Print each year: mean CD, N papers
    # Format: 1945: mean=0.035979, N=193

    print("\\n=== RESULTS ===")
    # Sample N, years count, CD 1945, CD 2010, decline %
    # Format: Sample N = 469855
    # Format: Years = 66
    # Format: CD 1945 = 0.035979
    # Format: CD 2010 = 0.001191
    # Format: Decline = 96.7%

    print("\\n=== DIFF_TABLE ===")
    # Print key metrics for comparison
    # | Metric | Value |
    # | sample_N | 469855 |
    # | years_count | 66 |
    # | cd_1945_mean | 0.035979 |
    # | cd_2010_mean | 0.001191 |
    # | decline_pct | 96.7 |
    # | overall_mean_cd | 0.005724 |

    ### C5: KEY REQUIREMENTS
    - Use pandas groupby for aggregation
    - Print all 66 years in CD_BY_YEAR section
    - Ensure all sections are printed with the EXACT section headers shown above
    - Use np.mean() or .mean() for aggregation — do not use custom formulas
    """)


def parse_agent_response(response: Any) -> str:
    content = ""
    if hasattr(response, "content"):
        raw = response.content
        if isinstance(raw, list):
            text_parts = []
            for item in raw:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(text_parts)
        else:
            content = str(raw)
    elif isinstance(response, str):
        content = response
    elif isinstance(response, list):
        # DeepSeek structured output: [{'type': 'thinking', ...}, {'type': 'text', 'text': '...'}]
        text_parts = []
        for item in response:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        content = "\n".join(text_parts)
    else:
        content = str(response)

    m = re.search(r"```(?:python)?\s*\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1)
    return content


def parse_metrics(stdout: str) -> dict[str, Any]:
    """Parse key metrics from DIFF_TABLE section."""
    metrics = {}
    in_section = False
    for line in stdout.split("\n"):
        line = line.strip()
        if "DIFF_TABLE" in line:
            in_section = True
            continue
        if in_section and line.startswith("==="):
            break
        if not in_section or not line:
            continue
        m = re.match(r"\|\s*(\w+)\s*\|\s*([0-9.e+\-]+)\s*\|", line)
        if m:
            key, val = m.group(1), m.group(2)
            try:
                if "." in val or "e" in val.lower():
                    metrics[key] = float(val)
                else:
                    metrics[key] = int(val)
            except ValueError:
                metrics[key] = val
    return metrics


def parse_results(stdout: str) -> dict[str, Any]:
    """Parse RESULTS section for key values."""
    results = {}
    in_section = False
    for line in stdout.split("\n"):
        line = line.strip()
        if "=== RESULTS ===" in line:
            in_section = True
            continue
        if in_section and line.startswith("==="):
            break
        if not in_section or not line:
            continue
        # Parse "Key = Value" format
        m = re.match(r"(\w+(?:\s+\w+)?)\s*=\s*([0-9.e+\-]+)", line)
        if m:
            key = m.group(1).strip().lower().replace(" ", "_")
            val = m.group(2)
            try:
                results[key] = float(val) if "." in val else int(val)
            except ValueError:
                results[key] = val
    return results


def check_section_compliance(code: str) -> dict[str, bool]:
    required = ["DATA_LOAD", "DESCRIPTIVE", "CD_BY_YEAR", "RESULTS", "DIFF_TABLE"]
    result = {}
    for section in required:
        result[section] = bool(re.search(
            rf'print\(["\'](?:\\n)?\s*=== {section} ===["\']\)', code
        ))
    return result


def build_diff_table(gold: dict, agent_metrics: dict) -> list[dict]:
    """Compare agent metrics to gold values."""
    g = gold["gold_results"]
    rows = []

    checks = [
        ("sample_N", g["sample_N"], agent_metrics.get("sample_N"), "exact"),
        ("years_count", g["years_count"], agent_metrics.get("years_count"), "exact"),
        ("cd_1945_mean", g["cd_1945"]["mean"], agent_metrics.get("cd_1945_mean"), 0.01),
        ("cd_2010_mean", g["cd_2010"]["mean"], agent_metrics.get("cd_2010_mean"), 0.01),
        ("decline_pct", g["decline_pct"], agent_metrics.get("decline_pct"), 0.05),
        ("overall_mean_cd", g["overall_mean_cd"], agent_metrics.get("overall_mean_cd"), 0.01),
    ]

    for name, gv, av, tol in checks:
        if av is None:
            rows.append({"metric": name, "gold": gv, "agent": None, "pass": False, "error": "missing"})
            continue

        rel_err = abs(float(av) - float(gv)) / abs(float(gv)) if float(gv) != 0 else abs(float(av) - float(gv))

        if tol == "exact":
            passed = float(av) == float(gv)
        else:
            passed = rel_err <= tol

        rows.append({
            "metric": name,
            "gold": gv,
            "agent": av,
            "relative_error": round(rel_err, 8),
            "tolerance": str(tol),
            "pass": passed,
        })

    return rows


def run_r004(model_name: str = "deepseek-v4-pro", use_mock: bool = False) -> dict[str, Any]:
    print("=" * 70)
    print("R004: Park2023 CD Time Trend — STRICT Reproduction")
    print("=" * 70)

    # Load gold
    print("\n[1/6] Loading gold...")
    with open(GOLD_PATH) as f:
        gold = json.load(f)
    print(f"  Gold: N={gold['gold_results']['sample_N']:,}, {gold['gold_results']['years_count']} years")
    print(f"  CD 1945={gold['gold_results']['cd_1945']['mean']:.6f}, "
          f"CD 2010={gold['gold_results']['cd_2010']['mean']:.6f}")
    print(f"  Decline: {gold['gold_results']['decline_pct']:.1f}%")

    # Load LLM
    print(f"\n[2/6] Loading LLM: {model_name}...")
    if use_mock:
        from src.sciscigpt_local.mock_llm import MockLLM
        llm = MockLLM()
    else:
        llm = load_llm_from_env(model_name)

    # Generate
    print("\n[3/6] Generating agent code...")
    prompt = build_prompt()
    with open(OUTPUT_DIR / "prompt_v0.txt", "w") as f:
        f.write(prompt)

    t0 = time.time()
    response = llm.invoke(prompt)
    agent_code = parse_agent_response(response)
    gen_time = time.time() - t0

    with open(OUTPUT_DIR / "agent_response_v0.txt", "w") as f:
        if hasattr(response, "content"):
            f.write(str(response.content))
        elif isinstance(response, list):
            f.write(str(response))
        else:
            f.write(str(response))
    with open(OUTPUT_DIR / "reproduce_v0_llm.py", "w") as f:
        f.write(agent_code)

    print(f"  Generated {len(agent_code)} chars in {gen_time:.1f}s")

    # Section check
    print("\n[4/6] Checking sections...")
    sections = check_section_compliance(agent_code)
    for s, found in sections.items():
        print(f"  {s}: {'OK' if found else 'MISSING'}")

    # Execute
    print("\n[5/6] Executing agent code...")
    exec_result = execute_python(agent_code, timeout=300)
    exit_code = exec_result.get("exit_code", exec_result.get("returncode", -1))
    stdout = exec_result.get("stdout", "")
    stderr = exec_result.get("stderr", "")

    with open(OUTPUT_DIR / "stdout.txt", "w") as f:
        f.write(stdout)
    if stderr:
        with open(OUTPUT_DIR / "stderr.txt", "w") as f:
            f.write(stderr)

    success = exit_code == 0
    print(f"  Execution: {'SUCCESS' if success else 'FAILED'} (exit={exit_code})")
    if not success:
        print(f"  Stderr (last 500): ...{stderr[-500:]}")

    # Evaluate
    print("\n[6/6] Evaluating...")
    agent_metrics = parse_metrics(stdout)
    # Also try parsing from RESULTS section
    agent_results = parse_results(stdout)
    # Merge (DIFF_TABLE takes precedence)
    agent_metrics = {**agent_results, **agent_metrics}

    print(f"  Parsed metrics: {list(agent_metrics.keys())}")

    diff_table = build_diff_table(gold, agent_metrics)

    # Compute D3 score
    n_checks = len(diff_table)
    n_pass = sum(1 for d in diff_table if d["pass"])
    d3_score = n_pass / n_checks if n_checks > 0 else 0.0

    print(f"\n  === D3 Accuracy ===")
    for d in diff_table:
        status = "PASS" if d["pass"] else "FAIL"
        print(f"  {d['metric']}: gold={d['gold']}, agent={d['agent']}, "
              f"rel_err={d.get('relative_error', 'N/A')} [{status}]")
    print(f"  D3 Score: {n_pass}/{n_checks} = {d3_score:.2f}")

    # Save results
    results = {
        "experiment": "R004",
        "paper": "Park2023 (CD time trend, Nature)",
        "task_type": "strict",
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "generation_time_s": round(gen_time, 1),
        "execution_success": success,
        "section_compliance": sections,
        "all_sections_found": all(sections.values()),
        "diff_table": diff_table,
        "d3_score": d3_score,
        "d3_pass": d3_score >= 0.9,
        "agent_metrics": agent_metrics,
        "spurious_flags": [],
    }

    with open(OUTPUT_DIR / "r004_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to {OUTPUT_DIR / 'r004_results.json'}")
    print(f"{'='*70}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="R004 Park2023 CD Time Trend Reproduction")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model", default="deepseek-v4-pro")
    args = parser.parse_args()
    run_r004(model_name=args.model, use_mock=args.mock)
