#!/usr/bin/env python3
"""Multi-paper, multi-metric benchmark: measure REI/REI-c across papers from SciSciNet.

Supports --metric-type:
  - disruption: D-index from citation subgraph
  - citation_count_prediction: predict citation count from same-year cohort
  - team_size_effect: small vs large team disruption difference
"""

import sys, os, re, json, tempfile, time, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "4096")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS, compute_rei_c
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import (
    get_prompt, parse_metric_output, compute_ground_truth,
    get_primary_metric, get_required_tables, METRIC_CONFIGS,
)

BENCHMARK_SIZE = 25
MAX_FIXES = 3


def _extract_code(text: str) -> str:
    """Extract Python code from LLM response."""
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    code = text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?\s*```$", "", code)
    return code


def generate_code(llm, metric_type: str, **prompt_kwargs) -> str:
    """Generate reproduction code for a given metric type."""
    prompt = get_prompt(metric_type, **prompt_kwargs)
    response = llm.invoke([{"role": "user", "content": prompt}])
    return _extract_code(str(response.content))


def fix_code(llm, code: str, error: str, metric_type: str, attempt: int) -> str:
    """Fix broken code with metric-aware strategies."""
    metric_label = METRIC_CONFIGS[metric_type]["label"]
    primary = get_primary_metric(metric_type)

    strategies = [
        f"Fix import errors. Use only pandas and numpy.",
        f"Check column names match the CSV files exactly.",
        f"Simplify the {metric_label} computation.",
        f"Rewrite minimal script. MUST print {primary} = <value> with the exact variable names.",
    ]
    idx = min(attempt, len(strategies) - 1)
    prompt = f"""Fix this {metric_label} computation code. {strategies[idx]}

Error: {error[:500]}

Code:
```python
{code[:1200]}
```

Output ONLY the fixed Python code."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    return _extract_code(str(response.content))


def reproduce_one_paper(
    llm, paper_id: int, pc: pd.DataFrame, papers: pd.DataFrame,
    metric_type: str = "disruption", max_fixes: int = 3,
    data_paths: dict | None = None,
) -> dict:
    """Run full reproduction pipeline for a single paper and metric.

    Args:
        data_paths: Pre-written CSV paths for non-disruption metrics
                    (avoids rewriting per paper). Keys: 'papers_path'.
    """
    data_paths = data_paths or {}
    try:
        # Compute ground truth for this metric
        gt = compute_ground_truth(metric_type, paper_id, papers, pc)
        primary_key = get_primary_metric(metric_type)

        if metric_type == "disruption":
            refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
            citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
            if len(refs) == 0 or len(citers) == 0:
                return {"status": "SKIPPED", "reason": "no refs or citers", "metric_type": metric_type}

            refs_path = tempfile.mktemp(suffix="_refs.csv")
            cites_path = tempfile.mktemp(suffix="_cites.csv")
            pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
            citer_cites = pc[pc["citing_paper_id"].isin(citers)][
                ["citing_paper_id", "cited_paper_id"]
            ].head(5000)
            citer_cites.to_csv(cites_path, index=False)

            code = generate_code(llm, metric_type, refs_path=refs_path, cites_path=cites_path, paper_id=paper_id)
            gt_value = gt.get(primary_key, 0.0)

        elif metric_type in ("citation_count_prediction", "team_size_effect"):
            papers_path = data_paths.get("papers_path")
            if papers_path is None:
                return {"status": "ERROR", "reason": "missing papers_path"}

            code = generate_code(llm, metric_type, papers_path=papers_path, paper_id=paper_id)
            gt_value = gt.get(primary_key, 0.0)
        else:
            return {"status": "ERROR", "reason": f"unknown metric: {metric_type}"}

        # Execute with self-correction
        error_types = []
        fix_count = 0

        for attempt in range(max_fixes + 1):
            result = execute_python(code, timeout=60)
            stderr = result.get("stderr", "")
            stdout = result.get("stdout", "")
            has_traceback = "Traceback (most recent call last)" in stderr
            is_error = result["exit_code"] != 0 or has_traceback

            if not is_error:
                parsed = parse_metric_output(result["stdout"], metric_type)
                if primary_key in parsed and gt:
                    weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                    rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0
                    computed_val = parsed[primary_key]
                    rei_c, c_ratio, silent = compute_rei_c(rei, gt_value, computed_val)
                    return {
                        "status": "SUCCESS",
                        "paper_id": int(paper_id),
                        "metric_type": metric_type,
                        "ground_truth": {k: v for k, v in gt.items()},
                        "computed": {k: v for k, v in parsed.items()},
                        "computed_primary": computed_val,
                        "ground_truth_primary": gt_value,
                        "REI": rei,
                        "REI_c": rei_c,
                        "correctness_ratio": c_ratio,
                        "is_silent_failure": silent,
                        "error_types": error_types,
                        "fix_count": fix_count,
                    }

            error_text = stderr or result.get("stdout", "")
            error_cat = classify_error(error_text)
            error_types.append(error_cat)
            fix_count += 1

            if attempt < max_fixes:
                code = fix_code(llm, code, error_text, metric_type, attempt)

        weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
        rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0
        return {
            "status": "FAILED",
            "paper_id": int(paper_id),
            "metric_type": metric_type,
            "ground_truth": {k: v for k, v in gt.items()} if gt else {},
            "computed_primary": None,
            "ground_truth_primary": gt_value if gt else None,
            "REI": rei,
            "REI_c": rei,
            "correctness_ratio": None,
            "is_silent_failure": False,
            "error_types": error_types,
            "fix_count": fix_count,
        }
    except Exception as e:
        return {"status": "ERROR", "paper_id": int(paper_id), "metric_type": metric_type, "error": str(e)[:200]}


def sample_papers(papers: pd.DataFrame, pc: pd.DataFrame, n: int, metric_type: str = "disruption") -> list[int]:
    """Sample papers with diverse characteristics."""
    if metric_type == "disruption":
        pc_pids = set(pc["citing_paper_id"].unique()) & set(pc["cited_paper_id"].unique())
        candidates = papers[papers["paper_id"].isin(pc_pids)].copy()
    else:
        candidates = papers.copy()

    if "disruption_score" in candidates.columns:
        valid = candidates.dropna(subset=["disruption_score"])
    else:
        valid = candidates

    if len(valid) < n:
        return list(valid["paper_id"].values)

    if "disruption_score" in valid.columns:
        try:
            valid["d_tercile"] = pd.qcut(valid["disruption_score"], q=3, labels=["low", "mid", "high"])
        except ValueError:
            valid["d_tercile"] = "mid"
        sampled = []
        for tercile in ["low", "mid", "high"]:
            pool = valid[valid["d_tercile"] == tercile]
            k = min(n // 3, len(pool))
            if k > 0:
                sampled.extend(pool.sample(k, random_state=42)["paper_id"].values)
        while len(sampled) < n:
            remaining = valid[~valid["paper_id"].isin(sampled)]
            if len(remaining) == 0:
                break
            sampled.append(remaining.sample(1, random_state=42)["paper_id"].values[0])
        return sampled[:n]

    return list(valid.sample(n, random_state=42)["paper_id"].values)


def main():
    parser = argparse.ArgumentParser(description="Multi-paper, multi-metric benchmark")
    parser.add_argument("--metric-type", default="disruption",
                        choices=list(METRIC_CONFIGS.keys()),
                        help="Which metric to reproduce")
    parser.add_argument("--benchmark-size", type=int, default=BENCHMARK_SIZE,
                        help="Number of papers to test")
    parser.add_argument("--max-fixes", type=int, default=MAX_FIXES,
                        help="Max self-correction attempts")
    parser.add_argument("--output", default=None,
                        help="Output JSON path (default: refine-logs/benchmark_{metric_type}.json)")
    args = parser.parse_args()

    metric_type = args.metric_type
    n_papers = args.benchmark_size
    max_fixes = args.max_fixes

    metric_label = METRIC_CONFIGS[metric_type]["label"]

    print("=" * 70)
    print(f"MULTI-PAPER BENCHMARK — {metric_label}")
    print(f"  Papers: {n_papers}, Max fixes: {max_fixes}")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    print("Loading SciSciNet...", flush=True)
    papers = load_table("papers")
    tables = {"papers": papers}
    for tbl in get_required_tables(metric_type):
        if tbl != "papers":
            tables[tbl] = load_table(tbl)
    pc = tables.get("paper_citations", pd.DataFrame())
    print(f"  Papers: {len(papers):,}", end="")
    if len(pc) > 0:
        print(f", Citations: {len(pc):,}")
    else:
        print()

    # Pre-write data files for non-disruption metrics
    data_paths = {}
    if metric_type in ("citation_count_prediction", "team_size_effect"):
        papers_path = tempfile.mktemp(suffix="_papers.csv")
        cols = ["paper_id", "year", "citation_count", "disruption_score"]
        if "author_count" in papers.columns:
            cols.append("author_count")
        papers[cols].to_csv(papers_path, index=False)
        data_paths["papers_path"] = papers_path
        print(f"  Papers CSV: {papers_path} ({len(papers):,} rows)")

    print(f"\nSampling {n_papers} papers...", flush=True)
    paper_ids = sample_papers(papers, pc, n_papers, metric_type)
    print(f"  Selected {len(paper_ids)} papers\n")

    results = []
    start_time = time.time()

    for i, pid in enumerate(paper_ids):
        elapsed = time.time() - start_time
        eta = (elapsed / (i + 1)) * (len(paper_ids) - i - 1) if i > 0 else 0

        print(f"  [{i+1}/{len(paper_ids)}] Paper {pid}...", end=" ", flush=True)
        r = reproduce_one_paper(llm, pid, pc, papers, metric_type, max_fixes, data_paths)
        results.append(r)

        status_icon = {"SUCCESS": "✓", "FAILED": "✗", "SKIPPED": "→", "ERROR": "!"}.get(r.get("status", ""), "?")
        print(f"{status_icon} {r['status']}", end="")
        if "REI" in r:
            print(f" REI={r['REI']}", end="")
        if r.get("is_silent_failure"):
            print(f" ⚠️SILENT", end="")
        if "error" in r:
            print(f" ({r['error'][:60]})", end="")
        print(f"  [ETA: {eta:.0f}s]", flush=True)

    total_time = time.time() - start_time

    # Summary
    print("\n" + "=" * 70)
    print(f"BENCHMARK RESULTS — {metric_label}")
    print("=" * 70)

    ok = [r for r in results if r["status"] == "SUCCESS"]
    failed = [r for r in results if r["status"] == "FAILED"]
    skipped = [r for r in results if r["status"] == "SKIPPED"]

    rei_vals = [r["REI"] for r in ok + failed if "REI" in r]
    rei_c_vals = [r["REI_c"] for r in ok + failed if "REI_c" in r]

    # Metric-specific deviation stats
    primary_key = get_primary_metric(metric_type)
    deviations = []
    for r in ok:
        cv = r.get("computed_primary")
        gv = r.get("ground_truth_primary")
        if cv is not None and gv is not None and gv != 0:
            deviations.append(abs(cv - gv))

    print(f"\n  Papers attempted: {len(results)}")
    print(f"  SUCCESS: {len(ok)} ({100*len(ok)/len(results):.0f}%)")
    print(f"  FAILED: {len(failed)}")
    print(f"  SKIPPED: {len(skipped)}")
    print(f"  Total time: {total_time:.0f}s ({total_time/len(results):.1f}s/paper)")

    if rei_vals:
        print(f"\n  REI: mean={np.mean(rei_vals):.2f}, median={np.median(rei_vals):.1f}, "
              f"min={np.min(rei_vals):.1f}, max={np.max(rei_vals):.1f}")

    if rei_c_vals:
        print(f"  REI-c: mean={np.mean(rei_c_vals):.2f}, median={np.median(rei_c_vals):.1f}, "
              f"min={np.min(rei_c_vals):.1f}, max={np.max(rei_c_vals):.1f}")

    silent = [r for r in ok if r.get("is_silent_failure")]
    if silent:
        print(f"\n  ⚠️  SILENT FAILURES: {len(silent)}/{len(ok)} successful papers have WRONG {primary_key}")
        print(f"     (code ran without errors, but metric is numerically incorrect)")

    if deviations:
        print(f"\n  {primary_key} mean abs dev: {np.mean(deviations):.6f}")
        print(f"  {primary_key} max abs dev: {np.max(deviations):.6f}")
        exact = sum(1 for d in deviations if d < 1e-10)
        print(f"  Exact match: {exact}/{len(deviations)}")

    from collections import Counter
    all_errors = []
    for r in ok + failed:
        all_errors.extend(r.get("error_types", []))
    if all_errors:
        print(f"\n  Error type distribution: {dict(Counter(all_errors))}")

    # Save results
    out_name = args.output or f"benchmark_{metric_type}.json"
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / out_name
    summary = {
        "config": {"metric_type": metric_type, "n_papers": n_papers, "max_fixes": max_fixes},
        "summary": {
            "n_total": len(results), "n_success": len(ok), "n_failed": len(failed),
            "n_skipped": len(skipped), "time_s": round(total_time, 1),
        },
        "rei_stats": {
            "mean": round(float(np.mean(rei_vals)), 2) if rei_vals else None,
            "median": round(float(np.median(rei_vals)), 2) if rei_vals else None,
            "mean_rei_c": round(float(np.mean(rei_c_vals)), 2) if rei_c_vals else None,
        } if rei_vals else {},
        "silent_failures": len(silent),
        f"{primary_key}_mean_abs_dev": round(float(np.mean(deviations)), 6) if deviations else None,
        "results": results,
    }
    out_path.write_text(json.dumps(summary, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return 0 if len(ok) > 0 else 1


if __name__ == "__main__":
    sys.exit(main())
