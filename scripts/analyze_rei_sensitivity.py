#!/usr/bin/env python3
"""REI-c sensitivity analysis: vary correctness tolerance and penalty weight."""

import json
import sys
import numpy as np
from pathlib import Path


def compute_rei_c(rei, gt, computed, correctness_weight=10.0, eps=0.001):
    """REI-c = REI + correctness_ratio * correctness_weight."""
    if computed is None:
        return rei, 1.0, False
    denom = max(abs(gt), eps)
    correctness_ratio = min(abs(computed - gt) / denom, 10.0)
    rei_c = rei + correctness_ratio * correctness_weight
    is_silent = rei <= 0.5 and correctness_ratio > 0.1
    return rei_c, correctness_ratio, is_silent


def flag_silent(rei, cratio, rei_threshold=0.5, correctness_threshold=0.1):
    return rei <= rei_threshold and cratio > correctness_threshold


def analyze_sensitivity(json_path: str):
    with open(json_path) as f:
        data = json.load(f)

    results = data["results"]

    # Extract all (rei, gt, computed) tuples
    items = []
    for level in ["L1", "L2", "L3"]:
        if level not in results:
            continue
        for r in results[level]:
            if r["status"] == "SUCCESS" and r.get("computed_primary") is not None:
                items.append({
                    "level": level,
                    "rei": r["rei"],
                    "gt": r.get("ground_truth_primary", 0),
                    "computed": r["computed_primary"],
                })

    print("=" * 70)
    print("REI-c SENSITIVITY ANALYSIS")
    print("=" * 70)

    # 1. Sensitivity to correctness_weight
    print("\n## 1. REI-c vs Correctness Weight\n")
    weights = [1, 5, 10, 20, 50, 100]
    print(f"{'Weight':<10}", end="")
    for level in ["L1", "L2", "L3"]:
        print(f"{level + ' mean':>12} {'median':>8}", end="  ")
    print()
    print("-" * 70)

    for w in weights:
        print(f"{w:<10}", end="")
        for level in ["L1", "L2", "L3"]:
            level_items = [i for i in items if i["level"] == level]
            rei_c_vals = [compute_rei_c(i["rei"], i["gt"], i["computed"], w)[0] for i in level_items]
            if rei_c_vals:
                print(f"{np.mean(rei_c_vals):>12.2f} {np.median(rei_c_vals):>8.2f}", end="  ")
            else:
                print(f"{'N/A':>12} {'N/A':>8}", end="  ")
        print()

    # 2. Sensitivity to silent-failure correctness_threshold
    print("\n## 2. Silent Failure Rate vs Correctness Threshold\n")
    thresholds = [0.01, 0.05, 0.10, 0.20, 0.50, 1.0]
    print(f"{'Threshold':<12}", end="")
    for level in ["L1", "L2", "L3"]:
        print(f"{level + ' silent%':>14}", end="  ")
    print()
    print("-" * 60)

    for thresh in thresholds:
        print(f"{thresh:<12}", end="")
        for level in ["L1", "L2", "L3"]:
            level_items = [i for i in items if i["level"] == level]
            silent_count = 0
            for i in level_items:
                _, cratio, _ = compute_rei_c(i["rei"], i["gt"], i["computed"])
                if flag_silent(i["rei"], cratio, correctness_threshold=thresh):
                    silent_count += 1
            pct = silent_count / len(level_items) * 100 if level_items else 0
            print(f"{pct:>12.1f}%", end="  ")
        print()

    # 3. Paired Wilcoxon test: L1 vs L2, L2 vs L3
    print("\n## 3. Level Separation (bootstrap)\n")
    rng = np.random.default_rng(42)
    for l1, l2 in [("L1", "L2"), ("L2", "L3"), ("L1", "L3")]:
        ri1 = np.array([compute_rei_c(i["rei"], i["gt"], i["computed"])[0] for i in items if i["level"] == l1])
        ri2 = np.array([compute_rei_c(i["rei"], i["gt"], i["computed"])[0] for i in items if i["level"] == l2])
        if len(ri1) == 0 or len(ri2) == 0:
            continue
        diff = np.mean(ri2) - np.mean(ri1)
        # Bootstrap CI for difference
        diffs = []
        for _ in range(10000):
            s1 = rng.choice(ri1, size=len(ri1), replace=True)
            s2 = rng.choice(ri2, size=len(ri2), replace=True)
            diffs.append(np.mean(s2) - np.mean(s1))
        lo, hi = np.percentile(diffs, 2.5), np.percentile(diffs, 97.5)
        sig = "***" if lo > 0 else ("**" if np.percentile(diffs, 5) > 0 else ("*" if np.percentile(diffs, 10) > 0 else "ns"))
        print(f"  {l1} vs {l2}: ΔREI-c = {diff:.2f}, 95% CI = [{lo:.2f}, {hi:.2f}] {sig}")

    # 4. Stability across correctness_weight
    print("\n## 4. Level Ranking Stability across Weights\n")
    for w in weights:
        means = {}
        for level in ["L1", "L2", "L3"]:
            level_items = [i for i in items if i["level"] == level]
            vals = [compute_rei_c(i["rei"], i["gt"], i["computed"], w)[0] for i in level_items]
            if vals:
                means[level] = np.mean(vals)
        ranking = sorted(means.items(), key=lambda x: x[1])
        order = " < ".join(f"{l}({v:.1f})" for l, v in ranking)
        print(f"  w={w:>4d}: {order}")


if __name__ == "__main__":
    path = sys.argv[1] if len(sys.argv) > 1 else "refine-logs/stratified_benchmark_50_v2.json"
    analyze_sensitivity(path)
