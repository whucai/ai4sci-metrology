#!/usr/bin/env python3
"""Analyze stratified benchmark results with failure taxonomy, REI stats, per-journal breakdown."""

import json
import sys
import numpy as np
from collections import Counter, defaultdict
from pathlib import Path


def bootstrap_ci(values, n_bootstrap=10000, ci=95):
    """Bootstrap confidence interval for mean."""
    if len(values) < 2:
        return np.nan, np.nan
    arr = np.array(values)
    means = []
    rng = np.random.default_rng(42)
    for _ in range(n_bootstrap):
        sample = rng.choice(arr, size=len(arr), replace=True)
        means.append(np.mean(sample))
    lo = (100 - ci) / 2
    hi = 100 - lo
    return np.percentile(means, lo), np.percentile(means, hi)


def analyze_results(json_path: str):
    with open(json_path) as f:
        data = json.load(f)

    results = data["results"]
    config = data.get("config", {})

    print("=" * 70)
    print("STRATIFIED BENCHMARK ANALYSIS")
    print(f"  File: {json_path}")
    print(f"  Papers: {config.get('n_papers', '?')}, Seed: {config.get('seed', '?')}")
    print("=" * 70)

    # Per-level summary
    print("\n## 1. Per-Level Summary\n")
    print(f"{'Level':<8} {'Success':<10} {'Correct':<10} {'SilentFail':<12} {'REI-c mean':<12} {'REI-c CI95':<20}")
    print("-" * 70)

    level_stats = {}
    for level in ["L1", "L2", "L3"]:
        if level not in results:
            continue
        items = results[level]
        n = len(items)
        success = sum(1 for r in items if r["status"] == "SUCCESS")
        correct = sum(1 for r in items if r.get("failure_category") == "correct")
        silent = sum(1 for r in items if r.get("is_silent_failure"))
        rei_c_vals = [r["rei_c"] for r in items]
        mean_rei = np.mean(rei_c_vals) if rei_c_vals else 0
        lo, hi = bootstrap_ci(rei_c_vals)
        level_stats[level] = {
            "n": n, "success": success, "correct": correct,
            "silent": silent, "mean_rei_c": mean_rei, "ci": (lo, hi),
            "items": items
        }
        print(f"{level:<8} {success}/{n:<7} {correct}/{n:<7} {silent}/{n:<9} {mean_rei:<12.2f} ({lo:.2f}, {hi:.2f})")

    # Failure taxonomy per level
    print("\n## 2. Failure Taxonomy\n")
    for level in ["L1", "L2", "L3"]:
        if level not in level_stats:
            continue
        items = level_stats[level]["items"]
        cats = Counter(r.get("failure_category", "unknown") for r in items)
        n = len(items)
        print(f"\n### {level} (n={n})")
        for cat, count in cats.most_common():
            pct = count / n * 100
            bar = "█" * int(pct / 2)
            print(f"  {cat:<25s}: {count:>3d} ({pct:5.1f}%) {bar}")

    # REI-c distribution by failure category
    print("\n## 3. REI-c by Failure Category\n")
    for level in ["L2", "L3"]:
        if level not in level_stats:
            continue
        items = level_stats[level]["items"]
        by_cat = defaultdict(list)
        for r in items:
            by_cat[r.get("failure_category", "unknown")].append(r["rei_c"])
        print(f"\n### {level}")
        for cat, vals in sorted(by_cat.items(), key=lambda x: -np.mean(x[1])):
            print(f"  {cat:<25s}: mean={np.mean(vals):.2f}, median={np.median(vals):.2f}, n={len(vals)}")

    # Per-metric-type breakdown
    print("\n## 4. Per-Metric-Type Breakdown\n")
    all_items = []
    for level in ["L1", "L2", "L3"]:
        if level in level_stats:
            for r in level_stats[level]["items"]:
                r["_level"] = level
                all_items.append(r)

    metric_types = set(r["metric_type"] for r in all_items)
    for mt in sorted(metric_types):
        mt_items = [r for r in all_items if r["metric_type"] == mt]
        by_level = defaultdict(list)
        for r in mt_items:
            by_level[r["_level"]].append(r)
        print(f"\n### {mt} (n={len(mt_items)} total)")
        for level in ["L1", "L2", "L3"]:
            if level not in by_level:
                continue
            li = by_level[level]
            correct = sum(1 for r in li if r.get("failure_category") == "correct")
            success = sum(1 for r in li if r["status"] == "SUCCESS")
            rei_c = np.mean([r["rei_c"] for r in li])
            print(f"  {level}: {correct}/{len(li)} correct, {success}/{len(li)} success, REI-c={rei_c:.2f}")

    # Per-journal breakdown
    print("\n## 5. Per-Journal Breakdown (top 15)\n")
    journal_items = defaultdict(list)
    for r in all_items:
        journal_items[r.get("paper_journal", "<NA>")].append(r)
    top_journals = sorted(journal_items.items(), key=lambda x: -len(x[1]))[:15]
    for journal, items in top_journals:
        by_level = defaultdict(list)
        for r in items:
            by_level[r["_level"]].append(r)
        l1_correct = sum(1 for r in by_level.get("L1", []) if r.get("failure_category") == "correct")
        l2_correct = sum(1 for r in by_level.get("L2", []) if r.get("failure_category") == "correct")
        l3_correct = sum(1 for r in by_level.get("L3", []) if r.get("failure_category") == "correct")
        n = len(items) // 3  # each paper in 3 levels
        print(f"  {journal[:50]:<50s}: n={n:>2d}, L1_correct={l1_correct}/{n}, L2_correct={l2_correct}/{n}, L3_correct={l3_correct}/{n}")

    # Cross-level success matrix
    print("\n## 6. Cross-Level Success Matrix\n")
    paper_ids = set()
    for level in ["L1", "L2", "L3"]:
        if level in level_stats:
            for r in level_stats[level]["items"]:
                paper_ids.add(r["paper_id"])

    paper_results = {}
    for pid in paper_ids:
        paper_results[pid] = {}
        for level in ["L1", "L2", "L3"]:
            if level in level_stats:
                for r in level_stats[level]["items"]:
                    if r["paper_id"] == pid:
                        paper_results[pid][level] = r["failure_category"]

    l1_correct = sum(1 for p in paper_results.values() if p.get("L1") == "correct")
    l2_correct = sum(1 for p in paper_results.values() if p.get("L2") == "correct")
    l3_correct = sum(1 for p in paper_results.values() if p.get("L3") == "correct")
    all_correct = sum(1 for p in paper_results.values()
                      if all(p.get(l) == "correct" for l in ["L1", "L2", "L3"]))
    none_correct = sum(1 for p in paper_results.values()
                       if all(p.get(l) != "correct" for l in ["L1", "L2", "L3"]))

    n_papers = len(paper_results)
    print(f"  Total papers: {n_papers}")
    print(f"  L1 correct: {l1_correct}/{n_papers} ({l1_correct/n_papers*100:.1f}%)")
    print(f"  L2 correct: {l2_correct}/{n_papers} ({l2_correct/n_papers*100:.1f}%)")
    print(f"  L3 correct: {l3_correct}/{n_papers} ({l3_correct/n_papers*100:.1f}%)")
    print(f"  ALL levels correct: {all_correct}/{n_papers}")
    print(f"  NO levels correct: {none_correct}/{n_papers}")

    # Key findings summary
    print("\n## 7. Key Findings\n")
    l1 = level_stats.get("L1", {})
    l2 = level_stats.get("L2", {})
    l3 = level_stats.get("L3", {})

    findings = []
    # Difficulty gradient
    if l1 and l2 and l3:
        gradient = f"REI-c: L1={l1['mean_rei_c']:.2f} < L2={l2['mean_rei_c']:.2f} < L3={l3['mean_rei_c']:.2f}"
        findings.append(f"Difficulty gradient: {gradient}")

    # Silent failure rate
    for level_name, stats in [("L1", l1), ("L2", l2), ("L3", l3)]:
        if stats:
            sf_rate = stats["silent"] / stats["n"] * 100
            findings.append(f"{level_name} silent failure rate: {sf_rate:.1f}% ({stats['silent']}/{stats['n']})")

    # Correct rate comparison
    if l1 and l2:
        delta = l1["correct"]/l1["n"]*100 - l2["correct"]/l2["n"]*100
        findings.append(f"L1→L2 correct-rate drop: {delta:.0f}pp")

    for f in findings:
        print(f"  - {f}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "refine-logs/stratified_benchmark_50_v2.json"
    analyze_results(path)
