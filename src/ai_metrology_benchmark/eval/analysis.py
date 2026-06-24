"""Aggregated metrics and analysis across benchmark runs."""

from __future__ import annotations

from typing import Any
from collections import defaultdict

import numpy as np

from ..types import StageResult


def stage_summary(results: list[StageResult]) -> dict[str, Any]:
    """Compute per-stage summary statistics."""
    if not results:
        return {"count": 0}

    success = [r for r in results if r.status == "SUCCESS"]
    failed = [r for r in results if r.status == "FAILED"]
    skipped = [r for r in results if r.status == "SKIPPED"]
    errors = [r for r in results if r.status == "ERROR"]

    summary: dict[str, Any] = {
        "count": len(results),
        "success": len(success),
        "failed": len(failed),
        "skipped": len(skipped),
        "errors": len(errors),
        "success_rate": round(len(success) / max(len(results), 1), 3),
    }

    if success:
        rei_c_vals = [r.rei_c for r in success if r.rei_c is not None]
        if rei_c_vals:
            summary["rei_c_mean"] = round(np.mean(rei_c_vals), 2)
            summary["rei_c_median"] = round(np.median(rei_c_vals), 2)

        silent = [r for r in success if r.is_silent_failure]
        summary["silent_failures"] = len(silent)
        summary["silent_failure_rate"] = round(len(silent) / max(len(success), 1), 3)

    return summary


def model_comparison(results_by_model: dict[str, list[StageResult]]) -> dict[str, Any]:
    """Cross-model comparison table."""
    comparison = {}
    for model_name, results in results_by_model.items():
        comparison[model_name] = stage_summary(results)
    return comparison


def by_info_level(results: list[StageResult]) -> dict[str, Any]:
    """Break down results by L1/L2/L3 information level."""
    grouped: dict[str, list[StageResult]] = defaultdict(list)
    for r in results:
        level = r.info_level or "unknown"
        grouped[level].append(r)

    return {
        level: stage_summary(group)
        for level, group in sorted(grouped.items())
    }


def by_metric_type(results: list[StageResult], paper_registry: dict) -> dict[str, Any]:
    """Break down results by metric type."""
    grouped: dict[str, list[StageResult]] = defaultdict(list)
    for r in results:
        paper = paper_registry.get(r.paper_id)
        mt = paper.metric_type if paper else "unknown"
        grouped[mt].append(r)

    return {
        mt: stage_summary(group)
        for mt, group in sorted(grouped.items())
    }


def by_paper(results: list[StageResult]) -> dict[str, Any]:
    """Break down results by methodology paper."""
    grouped: dict[str, list[StageResult]] = defaultdict(list)
    for r in results:
        grouped[r.paper_id].append(r)

    return {
        paper_id: stage_summary(group)
        for paper_id, group in sorted(grouped.items())
    }


def chain_analysis(results_by_stage: dict[int, list[StageResult]]) -> dict[str, Any]:
    """Error propagation analysis across stages.

    Args:
        results_by_stage: {stage_number: [StageResult, ...]}.

    Returns:
        Dict with per-stage success rates and cumulative degradation.
    """
    analysis = {}
    for stage_num in sorted(results_by_stage):
        summary = stage_summary(results_by_stage[stage_num])
        analysis[f"stage_{stage_num}"] = summary

    # Cumulative degradation
    rates = [analysis[s]["success_rate"] for s in sorted(analysis)]
    if rates:
        analysis["cumulative"] = np.prod(rates) if rates else 0
        analysis["max_degradation"] = max(rates) - min(rates) if len(rates) > 1 else 0

    return analysis


def print_summary_table(results: list[StageResult], paper_registry: dict | None = None):
    """Print a human-readable summary table."""
    print(f"\n{'='*70}")
    print(f"RESULTS SUMMARY: {len(results)} tasks")
    print(f"{'='*70}")

    # By level
    print("\nBy Information Level:")
    print(f"  {'Level':<8} {'Success':<10} {'Rate':<10} {'REI-c':<10} {'Silent':<10}")
    print(f"  {'-'*48}")
    for level, summary in by_info_level(results).items():
        rei = f"{summary.get('rei_c_mean', '-'):.2f}" if 'rei_c_mean' in summary else '-'
        silent = f"{summary.get('silent_failure_rate', 0):.1%}"
        print(f"  {level:<8} {summary['success']:<10} "
              f"{summary['success_rate']:<10.1%} {rei:<10} {silent:<10}")

    # By metric
    if paper_registry:
        print("\nBy Metric Type:")
        print(f"  {'Metric':<30} {'Success':<10} {'Rate':<10}")
        print(f"  {'-'*50}")
        for mt, summary in by_metric_type(results, paper_registry).items():
            print(f"  {mt:<30} {summary['success']:<10} "
                  f"{summary['success_rate']:<10.1%}")

    print(f"\n{'='*70}")
