#!/usr/bin/env python3
"""L3 Scoring Fix Ablation Analysis.

Computes the marginal effect of each scoring fix by applying different
combinations of the three changes to the same raw predictions (via stored
per-conclusion diagnostic fields).

Produces the ablation table:
  Setting              DirPartial  GradedSupport  Rebalanced  L3_Dir  L3_CSS  L3_Overall
  Original             ×           ×              ×           ...
  + Direction partial  ✓           ×              ×           ...
  + Graded support     ✓           ✓              ×           ...
  Full revised         ✓           ✓              ✓           ...

Usage:
  python scripts/ablate_l3_scoring.py refine-logs/l3_exact_rerun_20260624/sciscibench_task2_concurrent_*.json
"""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any


def avg(vals: list[float]) -> float:
    return sum(vals) / len(vals) if vals else 0.0


def compute_ablation(results: list[dict]) -> dict[str, Any]:
    """Compute 4 scoring variants on the same predictions."""

    # ── Scoring functions for each variant ──

    def original_binary_direction(detail: dict) -> float:
        """Old: match=1.0, no match=0.0 — no partial credit."""
        return 1.0 if detail["match"] else 0.0

    def calibrated_direction(cd: dict) -> float:
        """New: use the calibration matrix score from conclusion_details."""
        return cd.get("direction_score", 0.0)

    def original_binary_css_per_claim(cd: dict) -> float:
        """Old: strong/moderate → 1.0, weak/none → 0.0."""
        ss = cd.get("support_strength", "weak")
        return 1.0 if ss in ("strong", "moderate") else 0.0

    def graded_css_per_claim(cd: dict) -> float:
        """New: strong=1.0, moderate=0.6, weak=0.3."""
        return cd.get("support_strength_score", 0.0)

    records = []

    for r in results:
        if r.get("level") != "L3" or r.get("status") != "success":
            continue

        cd_list = r.get("conclusion_details", [])
        if not cd_list:
            # Fallback: reconstruct from direction_detail
            details = r.get("direction_detail", {}).get("details", [])
            cd_list = [
                {"gold_direction": d.get("gold_direction", "unknown"),
                 "pred_direction": d.get("pred_directions", ["unknown"])[0] if d.get("pred_directions") else "unknown",
                 "direction_score": 1.0 if d.get("match") else 0.0,
                 "support_strength": "moderate",
                 "support_strength_score": 0.6}
                for d in details
            ]
            if not cd_list:
                continue

        n = len(cd_list)

        # ── Variant 1: Original (binary dir, binary CSS, old weights) ──
        dir1 = sum(original_binary_direction(
            {"match": cd.get("direction_score", 0) >= 0.75}
        ) for cd in cd_list) / n
        css1 = sum(original_binary_css_per_claim(cd) for cd in cd_list) / n
        overall1 = (0.20 * dir1 + 0.15 * r.get("significance_match", 0)
                    + 0.25 * css1 + 0.10 * (1.0 - r.get("hallucinated_claim_rate", 0))
                    + 0.30 * r.get("uncertainty_recognition", 0))

        # Apply generic penalty if present
        specificity = r.get("claim_support_detail", {}).get("l3_specificity", 0)
        orig_penalty = r.get("claim_support_detail", {}).get("generic_claim_penalty", False)
        if orig_penalty or specificity < 0.05:
            overall1 *= 0.65

        # ── Variant 2: + Direction partial (calibrated dir, binary CSS, old weights) ──
        dir2 = sum(calibrated_direction(cd) for cd in cd_list) / n
        overall2 = (0.20 * dir2 + 0.15 * r.get("significance_match", 0)
                    + 0.25 * css1 + 0.10 * (1.0 - r.get("hallucinated_claim_rate", 0))
                    + 0.30 * r.get("uncertainty_recognition", 0))
        if orig_penalty or specificity < 0.05:
            overall2 *= 0.65

        # ── Variant 3: + Graded support (calibrated dir, graded CSS, old weights) ──
        css3 = sum(graded_css_per_claim(cd) for cd in cd_list) / n
        overall3 = (0.20 * dir2 + 0.15 * r.get("significance_match", 0)
                    + 0.25 * css3 + 0.10 * (1.0 - r.get("hallucinated_claim_rate", 0))
                    + 0.30 * r.get("uncertainty_recognition", 0))
        if orig_penalty or specificity < 0.05:
            overall3 *= 0.65

        # ── Variant 4: Full revised (calibrated dir, graded CSS, rebalanced weights) ──
        overall4 = r.get("overall_score", 0.0)

        # Compute direction commit stats
        committed = sum(1 for cd in cd_list if cd.get("pred_direction", "unknown") not in ("unknown",))
        commit_rate = committed / n if n > 0 else 0.0
        committed_correct = sum(
            1 for cd in cd_list
            if cd.get("pred_direction", "unknown") not in ("unknown",)
            and cd.get("direction_score", 0) >= 0.75
        )
        dir_correct_when_committed = committed_correct / max(committed, 1)

        # Support strength distribution
        ss_dist = {"strong": 0, "moderate": 0, "weak": 0}
        for cd in cd_list:
            ss = cd.get("support_strength", "weak")
            ss_dist[ss] = ss_dist.get(ss, 0) + 1

        records.append({
            "paper_id": r.get("paper_id", ""),
            "dir_original": dir1,
            "dir_calibrated": dir2,
            "css_binary": css1,
            "css_graded": css3,
            "overall_v1_original": overall1,
            "overall_v2_dir_partial": overall2,
            "overall_v3_graded_support": overall3,
            "overall_v4_full_revised": overall4,
            "direction_commit_rate": commit_rate,
            "direction_correct_when_committed": dir_correct_when_committed,
            "support_strength_distribution": ss_dist,
        })

    return records


def main():
    if len(sys.argv) < 2:
        print("Usage: python scripts/ablate_l3_scoring.py <results.json>")
        sys.exit(1)

    path = Path(sys.argv[1])
    data = json.loads(path.read_text())

    records = compute_ablation(data)
    print(f"Analyzed {len(records)} L3 papers\n")

    # ── Ablation Table ──
    def a(key):
        return avg([r[key] for r in records])

    print("=== L3 Scoring Fix Ablation Table ===")
    print(f"{'Setting':<25s} {'DirPart':>6s} {'GradSup':>6s} {'Rebal':>6s}  "
          f"{'L3_Dir':>8s} {'L3_CSS':>8s} {'L3_Overall':>10s}")
    print("-" * 80)

    for label, dp, gs, rb, dk, ck, ok in [
        ("Original", "×", "×", "×", "dir_original", "css_binary", "overall_v1_original"),
        ("+ Direction partial", "✓", "×", "×", "dir_calibrated", "css_binary", "overall_v2_dir_partial"),
        ("+ Graded support", "✓", "✓", "×", "dir_calibrated", "css_graded", "overall_v3_graded_support"),
        ("Full revised", "✓", "✓", "✓", "dir_calibrated", "css_graded", "overall_v4_full_revised"),
    ]:
        print(f"{label:<25s} {dp:>6s} {gs:>6s} {rb:>6s}  "
              f"{a(dk):8.4f} {a(ck):8.4f} {a(ok):10.4f}")

    # ── Direction commit analysis ──
    print(f"\n=== Direction Commit Analysis ===")
    commit_rates = [r["direction_commit_rate"] for r in records]
    print(f"Direction commit rate: {avg(commit_rates):.4f} "
          f"(papers with commit>0: {sum(1 for c in commit_rates if c > 0)}/{len(commit_rates)})")
    correct_when_committed = [r["direction_correct_when_committed"] for r in records if r["direction_commit_rate"] > 0]
    if correct_when_committed:
        print(f"Direction correct when committed: {avg(correct_when_committed):.4f} (n={len(correct_when_committed)})")

    # ── Support strength distribution ──
    print(f"\n=== Support Strength Distribution ===")
    total_ss = {"strong": 0, "moderate": 0, "weak": 0}
    for r in records:
        for k, v in r["support_strength_distribution"].items():
            total_ss[k] = total_ss.get(k, 0) + v
    total = sum(total_ss.values())
    for k in ["strong", "moderate", "weak"]:
        print(f"  {k}: {total_ss[k]}/{total} ({100*total_ss[k]/max(total,1):.1f}%)")

    # ── Save output ──
    out_path = path.with_suffix("").with_name(path.stem + "_ablation.json")
    out_path.write_text(json.dumps(records, indent=2, ensure_ascii=False))
    print(f"\nPer-paper ablation data saved to: {out_path}")


if __name__ == "__main__":
    main()
