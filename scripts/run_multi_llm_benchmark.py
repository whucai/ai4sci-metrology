#!/usr/bin/env python3
"""Multi-LLM Benchmark: compare REI/REI-c across available LLM backends.

Runs the same paper subset through each available LLM and compares:
  - REI / REI-c distributions
  - Silent failure rates
  - Success rates
  - D-index accuracy

Usage:
    python scripts/run_multi_llm_benchmark.py
    python scripts/run_multi_llm_benchmark.py --benchmark-size 10 --metric-type disruption
"""

import sys, os, json, time, argparse
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "4096")

from src.sciscigpt_local.llm_backends import get_available_llm_configs, load_llm_from_config
from src.sciscigpt_local.sciscinet_connector import load_table
from scripts.run_benchmark import reproduce_one_paper, sample_papers


def compare_llm_results(all_results: dict) -> dict:
    """Cross-LLM comparison statistics."""
    comparison = {"per_llm": {}, "cross_llm": {}}

    for llm_name, data in all_results.items():
        results = data["results"]
        ok = [r for r in results if r["status"] == "SUCCESS"]
        failed = [r for r in results if r["status"] == "FAILED"]

        rei_vals = [r["REI"] for r in ok + failed]
        rei_c_vals = [r.get("REI_c", r["REI"]) for r in ok + failed]

        silent = [r for r in ok if r.get("is_silent_failure")]

        comparison["per_llm"][llm_name] = {
            "provider": data["config"]["provider"],
            "model": data["config"]["model"],
            "n_total": len(results),
            "n_success": len(ok),
            "n_failed": len(failed),
            "n_silent_failures": len(silent),
            "success_rate": round(len(ok) / len(results), 3) if results else 0,
            "silent_failure_rate": round(len(silent) / len(ok), 3) if ok else 0,
            "rei_mean": round(float(np.mean(rei_vals)), 2) if rei_vals else None,
            "rei_median": round(float(np.median(rei_vals)), 2) if rei_vals else None,
            "rei_c_mean": round(float(np.mean(rei_c_vals)), 2) if rei_c_vals else None,
        }

    # Cross-LLM: papers succeeded by all LLMs
    if len(all_results) >= 2:
        llm_names = list(all_results.keys())
        common_ok = set(
            r["paper_id"] for r in all_results[llm_names[0]]["results"]
            if r["status"] == "SUCCESS"
        )
        for name in llm_names[1:]:
            common_ok &= set(
                r["paper_id"] for r in all_results[name]["results"]
                if r["status"] == "SUCCESS"
            )
        comparison["cross_llm"]["papers_succeeded_by_all"] = len(common_ok)

        # Papers failed by all
        common_fail = set(
            r["paper_id"] for r in all_results[llm_names[0]]["results"]
            if r["status"] == "FAILED"
        )
        for name in llm_names[1:]:
            common_fail &= set(
                r["paper_id"] for r in all_results[name]["results"]
                if r["status"] == "FAILED"
            )
        comparison["cross_llm"]["papers_failed_by_all"] = len(common_fail)

        # Pairwise REI correlation
        if len(llm_names) >= 2:
            a_name, b_name = llm_names[0], llm_names[1]
            a_rei = {r["paper_id"]: r["REI"] for r in all_results[a_name]["results"]}
            b_rei = {r["paper_id"]: r["REI"] for r in all_results[b_name]["results"]}
            common_pids = set(a_rei.keys()) & set(b_rei.keys())
            if len(common_pids) >= 5:
                a_vals = [a_rei[pid] for pid in common_pids]
                b_vals = [b_rei[pid] for pid in common_pids]
                corr = np.corrcoef(a_vals, b_vals)[0, 1]
                comparison["cross_llm"][f"REI_correlation_{a_name}_vs_{b_name}"] = round(float(corr), 4)

    return comparison


def main():
    parser = argparse.ArgumentParser(description="Multi-LLM benchmark comparison")
    parser.add_argument("--benchmark-size", type=int, default=15,
                        help="Papers per LLM")
    parser.add_argument("--metric-type", default="disruption",
                        choices=["disruption", "citation_count_prediction", "team_size_effect"])
    parser.add_argument("--max-fixes", type=int, default=3)
    args = parser.parse_args()

    print("=" * 70)
    print("MULTI-LLM BENCHMARK")
    print("=" * 70)

    # Discover available LLMs
    configs = get_available_llm_configs()
    if not configs:
        print("ERROR: No LLM backends configured.")
        print("Set OPENAI_API_KEY and/or ANTHROPIC_AUTH_TOKEN environment variables.")
        return 1

    print(f"\nAvailable backends ({len(configs)}):")
    for c in configs:
        print(f"  - {c.name} ({c.provider}): {c.model}")

    # Load shared data
    print("\nLoading SciSciNet...", flush=True)
    papers = load_table("papers")
    pc = load_table("paper_citations")
    print(f"  Papers: {len(papers):,}, Citations: {len(pc):,}")

    # Sample papers once — same papers for all LLMs
    paper_ids = sample_papers(papers, pc, args.benchmark_size, args.metric_type)
    print(f"\nTest set: {len(paper_ids)} papers (same for all LLMs)\n")

    all_results = {}
    total_start = time.time()

    for config in configs:
        print("=" * 70)
        print(f"Benchmarking: {config.name} ({config.model})")
        print("=" * 70)

        try:
            llm = load_llm_from_config(config)
            print(f"  LLM loaded: {type(llm).__name__}")
        except Exception as e:
            print(f"  SKIP: Failed to load {config.name}: {e}")
            continue

        results = []
        llm_start = time.time()

        for i, pid in enumerate(paper_ids):
            elapsed = time.time() - llm_start
            eta = (elapsed / (i + 1)) * (len(paper_ids) - i - 1) if i > 0 else 0

            print(f"  [{i+1}/{len(paper_ids)}] Paper {pid}...", end=" ", flush=True)
            r = reproduce_one_paper(llm, pid, pc, papers, args.metric_type, args.max_fixes)
            results.append(r)

            icon = {"SUCCESS": "✓", "FAILED": "✗", "SKIPPED": "→"}.get(r["status"], "?")
            print(f"{icon} REI={r.get('REI','?')}" +
                  (" ⚠️" if r.get("is_silent_failure") else "") +
                  f" [ETA: {eta:.0f}s]", flush=True)

        llm_time = time.time() - llm_start
        ok = [r for r in results if r["status"] == "SUCCESS"]
        silent = [r for r in ok if r.get("is_silent_failure")]

        print(f"\n  {config.name} summary:")
        print(f"    Success: {len(ok)}/{len(results)}, Silent failures: {len(silent)}, Time: {llm_time:.0f}s")

        all_results[config.name] = {
            "config": {
                "name": config.name,
                "provider": config.provider,
                "model": config.model,
            },
            "results": results,
            "summary": {
                "n_success": len(ok),
                "n_total": len(results),
                "n_silent_failures": len(silent),
                "time_s": round(llm_time, 1),
            },
        }

    total_time = time.time() - total_start

    # Cross-LLM comparison
    print("\n" + "=" * 70)
    print("CROSS-LLM COMPARISON")
    print("=" * 70)

    comparison = compare_llm_results(all_results)

    # Print comparison table
    print(f"\n{'LLM':<20} {'Success':>8} {'Rate':>8} {'REI':>6} {'REI-c':>6} {'Silent':>8}")
    print("-" * 60)
    for name, stats in comparison["per_llm"].items():
        print(f"{name:<20} {stats['n_success']:>3}/{stats['n_total']:<4} "
              f"{stats['success_rate']:>6.0%} {stats['rei_mean']:>6.1f} "
              f"{stats['rei_c_mean']:>6.1f} {stats['silent_failure_rate']:>6.0%}")

    if comparison["cross_llm"]:
        cs = comparison["cross_llm"]
        print(f"\n  Papers succeeded by all: {cs.get('papers_succeeded_by_all', 'N/A')}")
        print(f"  Papers failed by all: {cs.get('papers_failed_by_all', 'N/A')}")
        for k, v in cs.items():
            if k.startswith("REI_correlation"):
                print(f"  {k}: {v}")

    # Save results
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "multi_llm_comparison.json"
    output = {
        "config": {
            "benchmark_size": args.benchmark_size,
            "metric_type": args.metric_type,
            "max_fixes": args.max_fixes,
        },
        "comparison": comparison,
        "all_results": all_results,
        "total_time_s": round(total_time, 1),
    }
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
