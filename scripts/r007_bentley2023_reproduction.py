#!/usr/bin/env python3
"""R007: STRICT reproduction of Bentley et al. (2023) weighted disruption.

Bentley et al. (2023) "Is disruption decreasing, or is it accelerating?"
Advances in Complex Systems, 2023. DOI: 10.1142/S0219525923500066

STRICT task type: SciSciNet → SciSciNet. Target is numerical identity for
citation-weighted CD5 values 1945-2010.

Key formula: mCD5(t) = Σ(cit_i * CD5_i) / Σ(cit_i) per year

Usage:
    python scripts/r007_bentley2023_reproduction.py
    python scripts/r007_bentley2023_reproduction.py --mock
"""

from __future__ import annotations

import json, re, sys, textwrap, time
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.llm_backends import load_llm_from_env

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r007"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GOLD_PATH = OUTPUT_DIR / "gold_values.json"


def build_prompt() -> str:
    return textwrap.dedent("""\
    Reproduce the citation-weighted disruption analysis from:

      Bentley, Valverde, Borycz, Vidiella, Horne, Duran-Nebreda, O'Brien (2023)
      "Is disruption decreasing, or is it accelerating?"
      Advances in Complex Systems, 2023. DOI: 10.1142/S0219525923500066

    ## TASK

    Compute both the original (unweighted) and citation-weighted CD5 disruption
    index by year for papers 1945-2010, using SciSciNet data. The paper argues
    that the reported CD5 decline (Park2023) is an artifact of exponential growth
    and that a citation-weighted measure shows different trends.

    ## MANDATORY CONSTRAINTS

    ### C1: DATA SOURCE
    Use SciSciNet via:
      from src.sciscigpt_local.sciscinet_connector import load_papers_sample
      df = load_papers_sample(n_shards=10)

    ### C2: FILTERS
    - year >= 1945 AND year <= 2010
    - disruption_score not null
    - citation_count not null and > 0

    ### C3: ANALYSIS
    1. Filter papers to 1945-2010 with valid disruption_score and citation_count
    2. Group by year
    3. Compute UNWEIGHTED mean CD per year: mean(disruption_score)
    4. Compute WEIGHTED mean CD per year: sum(citation_count * disruption_score) / sum(citation_count)
    5. Also compute: overall means for both, decline %, change 2000-2010 for weighted

    ### C4: REQUIRED OUTPUT SECTIONS
    print("\\n=== DATA_LOAD ===")
    # Total loaded, after filter, year range

    print("\\n=== DESCRIPTIVE ===")
    # Overall unweighted mean CD, overall weighted mean CD
    # Post-1970 weighted mean, change 2000-2010

    print("\\n=== CD_BY_YEAR ===")
    # Print each year: unweighted mean CD, weighted mean CD, N, total citations
    # Format: 1945: uw=0.035979, w=0.076989, N=193, cites=13566

    print("\\n=== RESULTS ===")
    # Key results
    # Format: Sample N = 469855
    # Format: Years = 66
    # Format: UW CD 1945 = 0.035979
    # Format: UW CD 2010 = 0.001191
    # Format: W CD 1945 = 0.076989
    # Format: W CD 2010 = -0.000930
    # Format: UW decline = 96.7%
    # Format: W decline = 101.2%

    print("\\n=== DIFF_TABLE ===")
    # Print all key metrics for comparison
    # | Metric | Value |
    # | sample_N | 469855 |
    # | uw_cd_1945 | 0.035979 |
    # | uw_cd_2010 | 0.001191 |
    # | w_cd_1945 | 0.076989 |
    # | w_cd_2010 | -0.000930 |
    # | uw_decline_pct | 96.7 |
    # | w_decline_pct | 101.2 |
    # | overall_w_cd | 0.014379 |
    # | post1970_w_cd | 0.010449 |
    # | change_2000_2010 | -0.003413 |

    ### C5: KEY REQUIREMENTS
    - Use pandas groupby for aggregation
    - Use citation_count column for weighting (NOT reference_count)
    - Weighted formula: sum(citation_count * disruption_score) / sum(citation_count)
    - Do NOT use custom formulas — use np.average() with weights or manual sum/sum
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
                metrics[key] = float(val) if "." in val or "e" in val.lower() else int(val)
            except ValueError:
                metrics[key] = val
    return metrics


def parse_results(stdout: str) -> dict[str, Any]:
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
    return {
        s: bool(re.search(rf'print\(["\'](?:\\n)?\s*=== {s} ===["\']\)', code))
        for s in required
    }


def build_diff_table(gold: dict, agent_metrics: dict) -> list[dict]:
    g = gold["gold_results"]
    checks = [
        ("sample_N", g["sample_N"], agent_metrics.get("sample_N"), "exact"),
        ("uw_cd_1945", g["unweighted"]["cd_1945_mean"], agent_metrics.get("uw_cd_1945"), 0.01),
        ("uw_cd_2010", g["unweighted"]["cd_2010_mean"], agent_metrics.get("uw_cd_2010"), 0.01),
        ("w_cd_1945", g["weighted"]["cd_1945_mean"], agent_metrics.get("w_cd_1945"), 0.01),
        ("w_cd_2010", g["weighted"]["cd_2010_mean"], agent_metrics.get("w_cd_2010"), 0.01),
        ("uw_decline_pct", g["unweighted"]["decline_pct"], agent_metrics.get("uw_decline_pct"), 0.05),
        ("w_decline_pct", g["weighted"]["decline_pct"], agent_metrics.get("w_decline_pct"), 0.05),
        ("overall_w_cd", g["weighted"]["overall_mean"], agent_metrics.get("overall_w_cd"), 0.01),
        ("post1970_w_cd", g["weighted"]["post_1970_mean"], agent_metrics.get("post1970_w_cd"), 0.01),
    ]

    rows = []
    for name, gv, av, tol in checks:
        if av is None:
            rows.append({"metric": name, "gold": gv, "agent": None, "pass": False, "error": "missing"})
            continue
        rel_err = abs(float(av) - float(gv)) / abs(float(gv)) if abs(float(gv)) > 1e-10 else abs(float(av) - float(gv))
        if tol == "exact":
            passed = float(av) == float(gv)
        else:
            passed = rel_err <= tol
        rows.append({
            "metric": name, "gold": gv, "agent": av,
            "relative_error": round(rel_err, 8), "tolerance": str(tol), "pass": passed,
        })
    return rows


def run_r007(model_name: str = "deepseek-v4-pro", use_mock: bool = False) -> dict[str, Any]:
    print("=" * 70)
    print("R007: Bentley2023 Weighted CD — STRICT Reproduction")
    print("=" * 70)

    print("\n[1/6] Loading gold...")
    with open(GOLD_PATH) as f:
        gold = json.load(f)
    g = gold["gold_results"]
    print(f"  Gold N={g['sample_N']:,}, {g['years_count']} years")
    print(f"  UW: CD1945={g['unweighted']['cd_1945_mean']:.6f}, CD2010={g['unweighted']['cd_2010_mean']:.6f}")
    print(f"  W:  CD1945={g['weighted']['cd_1945_mean']:.6f}, CD2010={g['weighted']['cd_2010_mean']:.6f}")

    print(f"\n[2/6] Loading LLM: {model_name}...")
    if use_mock:
        from src.sciscigpt_local.mock_llm import MockLLM
        llm = MockLLM()
    else:
        llm = load_llm_from_env(model_name)

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
            raw = response.content
            f.write(str(raw))
        elif isinstance(response, list):
            f.write(str(response))
        else:
            f.write(str(response))
    with open(OUTPUT_DIR / "reproduce_v0_llm.py", "w") as f:
        f.write(agent_code)

    print(f"  Generated {len(agent_code)} chars in {gen_time:.1f}s")

    print("\n[4/6] Checking sections...")
    sections = check_section_compliance(agent_code)
    for s, found in sections.items():
        print(f"  {s}: {'OK' if found else 'MISSING'}")

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
        print(f"  Stderr (last 300): ...{stderr[-300:]}")

    print("\n[6/6] Evaluating...")
    agent_metrics = parse_metrics(stdout)
    agent_results = parse_results(stdout)
    agent_metrics = {**agent_results, **agent_metrics}

    diff_table = build_diff_table(gold, agent_metrics)
    n_checks = len(diff_table)
    n_pass = sum(1 for d in diff_table if d["pass"])
    d3_score = n_pass / n_checks if n_checks > 0 else 0.0

    print(f"\n  === D3 Accuracy ===")
    for d in diff_table:
        status = "PASS" if d["pass"] else "FAIL"
        print(f"  {d['metric']}: gold={d['gold']}, agent={d['agent']}, "
              f"rel_err={d.get('relative_error', 'N/A')} [{status}]")
    print(f"  D3 Score: {n_pass}/{n_checks} = {d3_score:.2f}")

    results = {
        "experiment": "R007",
        "paper": "Bentley2023 (Weighted CD, Advances in Complex Systems)",
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

    with open(OUTPUT_DIR / "r007_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to {OUTPUT_DIR / 'r007_results.json'}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="R007 Bentley2023 Weighted CD Reproduction")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model", default="deepseek-v4-pro")
    args = parser.parse_args()
    run_r007(model_name=args.model, use_mock=args.mock)
