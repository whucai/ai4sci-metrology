#!/usr/bin/env python3
"""R008: COMPONENT reproduction of Deng & Zeng (2023) edge-removal disruption.

Deng & Zeng (2023) "Enhancing the robustness of the disruption metric against noise"
Scientometrics, 2023. DOI: 10.1007/s11192-023-04644-2

COMPONENT task: Evaluates whether agent correctly decomposes the method into
components (hot-spot identification, edge removal, CD5 recomputation) and
implements each correctly. Gold is computed from SciSciNet, not APS data.

Usage:
    python scripts/r008_deng2023_reproduction.py
    python scripts/r008_deng2023_reproduction.py --mock
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

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r008"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GOLD_PATH = OUTPUT_DIR / "gold_values.json"


def build_prompt() -> str:
    return textwrap.dedent("""\
    Reproduce the edge-removal disruption robustness method from:

      Deng & Zeng (2023) "Enhancing the robustness of the disruption metric against noise"
      Scientometrics, 2023. DOI: 10.1007/s11192-023-04644-2

    ## METHOD SUMMARY

    The paper proposes a modified disruption index that removes edges to "hot-spot
    papers" (highly cited references) from the citation network, then recomputes CD5.
    The goal: show that removing highly-cited-reference edges makes the disruption
    metric better at distinguishing innovative from developmental papers.

    ## TASK

    Implement the edge-removal disruption method using SciSciNet data. The method
    has these components:

    ### Component 1: Baseline CD5 Computation
    - For a sample of focal papers, compute CD5 = (ni - nj) / (ni + nj + nk)
    - ni = # papers citing focal but NONE of focal's references
    - nj = # papers citing both focal AND at least one reference
    - nk = # papers citing references but NOT focal
    - Use paper_citations.parquet for the citation graph

    ### Component 2: Hot-Spot Paper Identification
    - Among all reference papers cited by the focal papers, identify the top 3%
      most cited papers (by in-degree in the citation graph)
    - These are the "hot-spot papers"

    ### Component 3: Edge Removal
    - For each focal paper, identify which of its references are hot-spot papers
    - When computing nj (citers that also cite references), ignore edges from
      citers to hot-spot references
    - Recompute ni and nj with the pruned edge set

    ### Component 4: Comparison
    - Compare CD5 before vs after edge removal
    - Report: mean CD5 change, rank correlation before/after, % papers with
      significant rank change, number of hot-spot papers identified

    ## MANDATORY CONSTRAINTS

    ### C1: DATA SOURCE
    Use SciSciNet:
      from src.sciscigpt_local.sciscinet_connector import load_papers_sample, load_table
      papers = load_papers_sample(n_shards=3)
      pc = load_table("paper_citations")

    ### C2: SAMPLE
    - Filter papers to: year >= 1945, disruption_score not null, citation_count > 0, reference_count > 0
    - Sample 500 papers using np.random.seed(42) and np.random.choice
    - Use these 500 as focal papers

    ### C3: CITATION COUNTS
    - Compute in-degree from paper_citations using groupby("cited_paper_id").size()
    - Hot-spot threshold: top 3% most cited among all references (sorted citation counts)

    ### C4: CD5 FORMULA
    - CD5 = (ni - nj) / (ni + nj + nk)
    - ni = citers with NO overlap with focal's references
    - nj = citers with at least one reference overlap with focal's references
    - nk = papers citing focal's references but not citing focal

    ### C5: REQUIRED OUTPUT SECTIONS

    print("\\n=== DATA_LOAD ===")
    # N papers loaded, N valid, N focal sampled

    print("\\n=== CITATION_GRAPH ===")
    # N edges in paper_citations, N unique cited papers, in-degree range

    print("\\n=== HOTSPOT ===")
    # N unique references, threshold, N hotspot papers

    print("\\n=== CD5_BASELINE ===")
    # Mean, std of baseline CD5 across focal papers

    print("\\n=== CD5_EDGE_REMOVAL ===")
    # Mean, std of new CD5, mean delta, N papers with CD5 change

    print("\\n=== COMPARISON ===")
    # Rank correlation, % significant rank change

    print("\\n=== DIFF_TABLE ===")
    # | Metric | Value |
    # | n_focal | 500 |
    # | baseline_cd5_mean | ... |
    # | new_cd5_mean | ... |
    # | cd5_delta_mean | ... |
    # | rank_correlation | ... |
    # | pct_rank_change | ... |
    # | n_papers_changed | ... |
    # | n_hotspot_papers | ... |

    ### C6: KEY REQUIREMENTS
    - Use defaultdict(set) for refs, citers, citer_refs dicts
    - Use set operations (&, |, -) for ni/nj/nk computation
    - Hot-spot removal: effective_refs = citer_refs - hotspot_ids
    - Print progress every 100 papers
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


def check_section_compliance(code: str) -> dict[str, bool]:
    required = ["DATA_LOAD", "CITATION_GRAPH", "HOTSPOT", "CD5_BASELINE",
                "CD5_EDGE_REMOVAL", "COMPARISON", "DIFF_TABLE"]
    return {s: bool(re.search(rf'print\(["\'](?:\\n)?\s*=== {s}', code)) for s in required}


def evaluate_components(agent_code: str, agent_metrics: dict) -> dict:
    """Evaluate whether agent correctly implemented each component."""
    results = {}

    # Component 1: ni/nj/nk formula
    has_ni = bool(re.search(r'ni\s*=', agent_code))
    has_nj = bool(re.search(r'nj\s*=', agent_code))
    has_nk = bool(re.search(r'nk\s*=', agent_code))
    has_formula = bool(re.search(r'\(\s*ni\s*-\s*nj\s*\)\s*/\s*\(\s*ni\s*\+\s*nj\s*\+\s*nk\s*\)', agent_code))
    has_set_ops = bool(re.search(r'&\s+\w+|\.intersection|citer_refs.*refs', agent_code))
    results["c1_baseline_cd5"] = has_ni and has_nj and has_formula and has_set_ops

    # Component 2: Hot-spot identification
    has_groupby = bool(re.search(r'groupby.*cited_paper_id.*size', agent_code))
    has_sort = bool(re.search(r'sort|np\.sort|sorted.*citation', agent_code))
    has_threshold = bool(re.search(r'threshold|percentile|top.*3|0\.0?3|int\(.*0\.97', agent_code))
    results["c2_hotspot_id"] = has_groupby and (has_sort or has_threshold)

    # Component 3: Edge removal
    has_effective = bool(re.search(r'effective|remove.*hot|prune|exclude.*hot', agent_code))
    has_recompute = bool(re.search(r'new.*ni|new.*nj|new.*cd5|recompute|after.*removal', agent_code))
    results["c3_edge_removal"] = has_effective and has_recompute

    # Component 4: Comparison
    has_rank_corr = bool(re.search(r'rank.*corr|spearman|argsort.*argsort|corrcoef.*rank', agent_code))
    has_pct = bool(re.search(r'percent|pct|proportion.*changed|changed.*percent', agent_code))
    results["c4_comparison"] = has_rank_corr or has_pct

    results["all_components_present"] = all(results.values())
    return results


def run_r008(model_name: str = "deepseek-v4-pro", use_mock: bool = False) -> dict[str, Any]:
    print("=" * 70)
    print("R008: Deng2023 Edge-Removal Disruption — COMPONENT Reproduction")
    print("=" * 70)

    print("\n[1/6] Loading gold...")
    with open(GOLD_PATH) as f:
        gold = json.load(f)
    gs = gold["summary"]
    print(f"  Gold: N={gs['n_focal']}, CD5 mean={gs['baseline_cd5_mean']:.6f}, "
          f"delta={gs['cd5_delta_mean']:.6f}, rank_corr={gs['rank_correlation']:.4f}")

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
        raw = response.content if hasattr(response, "content") else str(response)
        f.write(str(raw))
    with open(OUTPUT_DIR / "reproduce_v0_llm.py", "w") as f:
        f.write(agent_code)

    print(f"  Generated {len(agent_code)} chars in {gen_time:.1f}s")

    print("\n[4/6] Checking sections...")
    sections = check_section_compliance(agent_code)
    for s, found in sections.items():
        print(f"  {s}: {'OK' if found else 'MISSING'}")

    print("\n[5/6] Executing agent code...")
    exec_result = execute_python(agent_code, timeout=600)
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

    print("\n[6/6] Evaluating...")
    agent_metrics = parse_metrics(stdout)
    comp_eval = evaluate_components(agent_code, agent_metrics)

    # D1: structural fidelity (section compliance)
    d1_score = sum(sections.values()) / max(len(sections), 1)

    # D2: executability
    d2_score = 1.0 if success else 0.0

    # D3: numerical accuracy — compare agent metrics to gold
    d3_checks = []
    key_metrics = [
        ("n_focal", gs["n_focal"], agent_metrics.get("n_focal"), "exact"),
        ("baseline_cd5_mean", gs["baseline_cd5_mean"], agent_metrics.get("baseline_cd5_mean"), 0.05),
        ("new_cd5_mean", gs["new_cd5_mean"], agent_metrics.get("new_cd5_mean"), 0.05),
        ("cd5_delta_mean", gs["cd5_delta_mean"], agent_metrics.get("cd5_delta_mean"), 0.1),
        ("rank_correlation", gs["rank_correlation"], agent_metrics.get("rank_correlation"), 0.05),
        ("n_papers_changed", gs["n_papers_with_cd5_change"], agent_metrics.get("n_papers_changed"), 0.2),
        ("n_hotspot_papers", gs["n_hotspot_papers_total"], agent_metrics.get("n_hotspot_papers"), 0.3),
    ]

    for name, gv, av, tol in key_metrics:
        if av is None:
            d3_checks.append({"metric": name, "gold": gv, "agent": None, "pass": False})
            continue
        if tol == "exact":
            passed = int(av) == int(gv)
        else:
            rel_err = abs(float(av) - float(gv)) / max(abs(float(gv)), 1e-10)
            passed = rel_err <= tol
        d3_checks.append({
            "metric": name, "gold": gv, "agent": av,
            "relative_error": round(abs(float(av) - float(gv)) / max(abs(float(gv)), 1e-10), 6),
            "pass": passed,
        })

    n_pass = sum(1 for d in d3_checks if d["pass"])
    d3_score = n_pass / len(d3_checks) if d3_checks else 0.0

    # D4: claim consistency — edge removal should increase CD5 (positive delta)
    agent_delta = agent_metrics.get("cd5_delta_mean")
    if agent_delta is not None:
        if float(agent_delta) > 0:
            d4_score = 1.0
        elif float(agent_delta) > -0.01:
            d4_score = 0.8  # near zero, possibly correct but need investigation
        else:
            d4_score = 0.5  # wrong direction
    else:
        d4_score = 0.5

    # D5: auditability
    has_seed = bool(re.search(r'np\.random\.seed|random\.seed', agent_code))
    has_sections = all(sections.values())
    d5_score = (0.5 if has_seed else 0.0) + (0.5 if has_sections else 0.0)

    overall = round(
        d1_score * 0.15 + d2_score * 0.15 + d3_score * 0.30 +
        d4_score * 0.15 + d5_score * 0.10 +
        (1.0 if comp_eval.get("all_components_present") else 0.0) * 0.15,
        3,
    )

    print(f"\n  === Component Evaluation ===")
    for cname, cpass in comp_eval.items():
        if cname != "all_components_present":
            print(f"  {cname}: {'PASS' if cpass else 'FAIL'}")

    print(f"\n  === D3 Accuracy ===")
    for d in d3_checks:
        status = "PASS" if d["pass"] else "FAIL"
        print(f"  {d['metric']}: gold={d['gold']}, agent={d['agent']} [{status}]")

    print(f"\n  === Overall Scores ===")
    print(f"  D1 (sections): {d1_score:.2f}")
    print(f"  D2 (execution): {d2_score:.2f}")
    print(f"  D3 (accuracy): {d3_score:.2f} ({n_pass}/{len(d3_checks)} checks)")
    print(f"  D4 (claim): {d4_score:.2f}")
    print(f"  D5 (auditability): {d5_score:.2f}")
    print(f"  Components: all_present={comp_eval.get('all_components_present', False)}")
    print(f"  Overall: {overall:.3f}")

    results = {
        "experiment": "R008",
        "paper": "Deng2023 (Edge-Removal Disruption, Scientometrics)",
        "task_type": "component",
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "generation_time_s": round(gen_time, 1),
        "execution_success": success,
        "section_compliance": sections,
        "all_sections_found": all(sections.values()),
        "component_evaluation": comp_eval,
        "d1_score": d1_score, "d2_score": d2_score, "d3_score": d3_score,
        "d4_score": d4_score, "d5_score": d5_score,
        "overall_score": overall,
        "d3_checks": d3_checks,
        "d3_pass": d3_score >= 0.7,
        "agent_metrics": agent_metrics,
    }

    with open(OUTPUT_DIR / "r008_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to {OUTPUT_DIR / 'r008_results.json'}")
    print("=" * 70)
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="R008 Deng2023 Edge-Removal Reproduction")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model", default="deepseek-v4-pro")
    args = parser.parse_args()
    run_r008(model_name=args.model, use_mock=args.mock)
