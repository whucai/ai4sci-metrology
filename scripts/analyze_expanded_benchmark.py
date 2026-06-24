#!/usr/bin/env python3
"""Analyze expanded benchmark results: original 13 vs auto 97, error taxonomy per metric.

Usage:
    python scripts/analyze_expanded_benchmark.py refine-logs/benchmark_YYYYMMDD_HHMMSS.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from collections import Counter, defaultdict
from typing import Any


# ── Paper classification ──
ORIGINAL_13 = {
    "ms_dynamic_network", "nber_w18958", "arxiv_2306_01949",
    "arxiv_2308_02383", "nature_2023_disruption", "pnas_network_impact",
    "rp_2021_ccby", "rp_2025_sam_arts",
    "acs_disruption_weighted", "scientometrics_robust_disruption",
    "arxiv_disruption_framework",
    "pnas_sleeping_beauty", "pnas_ranking_mobility",
}


def load_results(path: str) -> list[dict]:
    """Load Stage 2 results from benchmark JSON."""
    data = json.loads(Path(path).read_text())
    return data.get("stage2_results", [])


def classify_error(result: dict) -> str:
    """Classify result into error categories using a layered rule set."""
    status = result.get("status", "UNKNOWN")
    error_types = result.get("error_types", []) or []
    is_silent = result.get("is_silent_failure", False)
    fix_count = result.get("fix_count", 0)

    # Layer 1: Did it run at all?
    if status == "SKIPPED":
        return "data_missing"

    if status in ("ERROR",):
        return "parse_fail"

    # Layer 2: Did it succeed?
    if status == "FAILED":
        if "syntax" in error_types:
            return "parse_fail"
        if "import" in error_types:
            return "import_error"
        return "runtime_error"

    # Layer 3: It succeeded — but is it correct?
    if status == "SUCCESS":
        if is_silent:
            return "silent_failure"
        if fix_count > 0:
            return "fixed_then_ok"
        return "perfect"

    return "unknown"


def is_auto_paper(methodology_paper: str) -> bool:
    return methodology_paper.startswith("auto_")


def metric_family(mt: str) -> str:
    """Group metric types into families."""
    families = {
        "disruption": "disruption",
        "disruption_temporal": "disruption_temporal",
        "team_size_effect": "team_size_effect",
        "citation_inflation": "citation_inflation",
        "citation_count_prediction": "citation_count_prediction",
        "network_normalized_impact": "network_normalized_impact",
        "frontier_author_impact": "frontier_author_impact",
        "sleeping_beauty": "sleeping_beauty",
        "career_mobility": "career_mobility",
        "novelty_conventionality": "novelty_conventionality",
        "interdisciplinarity": "interdisciplinarity",
        "altmetrics": "altmetrics",
    }
    return families.get(mt, mt)


def data_dependency(mt: str) -> str:
    """Whether the metric needs per-paper citation data or just the papers table."""
    needs_citations = {
        "disruption", "sleeping_beauty", "network_normalized_impact",
        "disruption_temporal", "citation_inflation", "citation_count_prediction",
    }
    return "requires_citations" if mt in needs_citations else "papers_only"


def build_table(results: list[dict]) -> str:
    """Build the main comparison table."""
    # Group by metric type
    groups: dict[str, list[dict]] = defaultdict(list)
    for r in results:
        mt = r.get("metric_type", "unknown")
        groups[mt].append(r)

    lines = []
    sep = "-" * 100
    header = f"{'Group':<32s} {'Tasks':>6s} {'%Success':>9s} {'%Perfect':>8s} {'Parse':>6s} {'DataMiss':>8s} {'Formula':>7s} {'Silent':>6s} {'Import':>6s} {'REI-c':>7s}"
    lines.append(sep)
    lines.append(header)
    lines.append(sep)

    def row(label, tasks):
        n = len(tasks)
        if n == 0:
            return
        cats = Counter(classify_error(t) for t in tasks)
        success = cats.get("perfect", 0) + cats.get("fixed_then_ok", 0)
        pct = lambda c: f"{100 * c / n:.1f}%"
        rei_vals = [t.get("rei_c", 100) for t in tasks if t.get("status") == "SUCCESS" and t.get("rei_c") is not None]
        rei_mean = f"{sum(rei_vals)/len(rei_vals):.1f}" if rei_vals else "N/A"

        lines.append(
            f"{label:<32s} {n:>6d} {pct(success):>9s} "
            f"{pct(cats['perfect']):>8s} "
            f"{cats['parse_fail']:>5d} {cats['data_missing']:>7d} "
            f"{cats['runtime_error']+cats['silent_failure']:>6d} "
            f"{cats['silent_failure']:>5d} "
            f"{cats['import_error']:>5d} "
            f"{rei_mean:>7s}"
        )
        lines.append(f"  └─ {', '.join(f'{k}={v}' for k,v in cats.most_common(6))}")

    # ── Section A: Original 13 vs Auto 97 ──
    lines.append("\n### A: Original 13 vs Auto-Collected 97\n")
    original = [r for r in results if r.get("methodology_paper") in ORIGINAL_13]
    auto = [r for r in results if is_auto_paper(r.get("methodology_paper", ""))]

    row("ORIGINAL (13 hand-curated)", original)
    row("AUTO (97 arXiv collected)", auto)
    row("ALL (110 papers)", results)

    # ── Section B: Per metric type ──
    lines.append(f"\n### B: Per Metric Type\n")
    for mt in sorted(groups.keys()):
        row(f"  {mt}", groups[mt])

    # ── Section C: Data dependency ──
    lines.append(f"\n### C: Data Dependency\n")
    papers_only = [r for r in results if data_dependency(r.get("metric_type", "")) == "papers_only"]
    needs_cit = [r for r in results if data_dependency(r.get("metric_type", "")) == "requires_citations"]
    row("PAPERS-ONLY", papers_only)
    row("REQUIRES CITATIONS", needs_cit)

    # ── Section D: Info Level breakdown ──
    lines.append(f"\n### D: By Information Level\n")
    for lvl in ["L1", "L2", "L3"]:
        subset = [r for r in results if r.get("level") == lvl]
        if subset:
            row(f"  {lvl}", subset)

    # ── Section E: Top failures ──
    lines.append(f"\n### E: Worst-Performing Papers (by metric type)\n")
    paper_stats = defaultdict(list)
    for r in results:
        pid = r.get("methodology_paper", "?")
        paper_stats[pid].append(r)

    worst = []
    for pid, tasks in paper_stats.items():
        n = len(tasks)
        s = sum(1 for t in tasks if t.get("status") == "SUCCESS")
        mt = tasks[0].get("metric_type", "?")
        worst.append((pid, mt, n, s, 100 * s / n if n else 0))
    worst.sort(key=lambda x: x[4])  # sort by success rate

    lines.append(f"  {'Paper ID':<30s} {'Metric':<28s} {'Tasks':>5s} {'OK':>5s} {'Rate':>7s}")
    for pid, mt, n, s, rate in worst[:15]:
        lines.append(f"  {pid:<30s} {mt:<28s} {n:>5d} {s:>5d} {rate:>6.1f}%")

    # ── Section F: Silent Failure Analysis ──
    lines.append(f"\n### F: Silent Failure Rate by Metric Type\n")
    for mt in sorted(groups.keys()):
        tasks = groups[mt]
        successful = [t for t in tasks if t.get("status") == "SUCCESS"]
        silent = [t for t in successful if t.get("is_silent_failure")]
        if successful:
            lines.append(f"  {mt:<30s}: {len(silent)}/{len(successful)} silent ({100*len(silent)/len(successful):.1f}%)")

    lines.append(sep)
    return "\n".join(lines)


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/analyze_expanded_benchmark.py <benchmark.json>")
        sys.exit(1)

    path = sys.argv[1]
    if not Path(path).exists():
        print(f"File not found: {path}")
        sys.exit(1)

    results = load_results(path)
    print(f"Loaded {len(results)} Stage 2 results from {path}")

    # Quick stats
    status = Counter(r.get("status") for r in results)
    print(f"Status: {dict(status)}")

    metric_counts = Counter(r.get("metric_type") for r in results)
    print(f"Metric types: {len(metric_counts)}")
    for mt, c in metric_counts.most_common():
        print(f"  {mt}: {c}")

    print()
    print(build_table(results))


if __name__ == "__main__":
    main()
