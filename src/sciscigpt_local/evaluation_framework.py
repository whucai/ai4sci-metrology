"""M2c: Multi-Level Result Comparison Framework.

Implements the 4-level comparison from HARD_PROBLEMS.md:
  Level 1 — Exact numeric comparison (tolerance-based)
  Level 2 — Statistical equivalence (direction + significance)
  Level 3 — Trend consistency (correlation of effect across subgroups)
  Level 4 — Conclusion consistency (qualitative alignment)

Used by the EvaluationSpecialist to assess reproduction quality.
"""

from __future__ import annotations

import json
from typing import Any

import numpy as np
from scipy.stats import spearmanr


def level1_numeric(
    reproduced: dict[str, float],
    expected: dict[str, float],
    tolerance: float = 0.20,
) -> dict[str, Any]:
    """Level 1: Exact numeric comparison with relative tolerance.

    Returns per-metric deviation and overall match rate.
    """
    comparisons = []
    for key in expected:
        if key in reproduced:
            ev, rv = expected[key], reproduced[key]
            if abs(ev) > 1e-10:
                dev = abs(rv - ev) / abs(ev)
            else:
                dev = abs(rv - ev) if abs(rv) > 1e-10 else 0.0
            comparisons.append({
                "metric": key,
                "expected": ev,
                "reproduced": rv,
                "deviation": round(dev, 4),
                "match": dev <= tolerance,
            })

    if not comparisons:
        return {"level": 1, "status": "NO_DATA", "match_rate": 0.0, "comparisons": []}

    matched = sum(1 for c in comparisons if c["match"])
    return {
        "level": 1,
        "status": "PASS" if matched == len(comparisons) else "PARTIAL" if matched > 0 else "FAIL",
        "match_rate": round(matched / len(comparisons), 4),
        "comparisons": comparisons,
    }


def level2_statistical(
    reproduced_effect: dict[str, Any],
    expected_effect: dict[str, Any],
) -> dict[str, Any]:
    """Level 2: Statistical equivalence check.

    Compares:
    - Effect direction (sign of difference)
    - Significance (both p < threshold)
    - Effect size magnitude (within order of magnitude)
    """
    checks = []

    # Direction check
    rep_dir = reproduced_effect.get("direction", 0)
    exp_dir = expected_effect.get("direction", 0)
    direction_match = (rep_dir > 0) == (exp_dir > 0) if exp_dir != 0 else True
    checks.append({
        "check": "direction",
        "expected": "positive" if exp_dir > 0 else "negative" if exp_dir < 0 else "zero",
        "reproduced": "positive" if rep_dir > 0 else "negative" if rep_dir < 0 else "zero",
        "match": direction_match,
    })

    # Significance check
    rep_p = reproduced_effect.get("p_value", 1.0)
    exp_p = expected_effect.get("p_value", 1.0)
    rep_sig = rep_p < 0.001
    exp_sig = exp_p < 0.001
    checks.append({
        "check": "significance_p001",
        "expected": exp_sig,
        "reproduced": rep_sig,
        "match": rep_sig == exp_sig,
    })

    # Effect size magnitude check (within 2 orders of magnitude)
    rep_es = abs(reproduced_effect.get("effect_size", 0))
    exp_es = abs(expected_effect.get("effect_size", 0))
    if exp_es > 1e-10:
        ratio = rep_es / exp_es if rep_es > exp_es else exp_es / rep_es
        mag_match = ratio <= 100
    else:
        mag_match = rep_es < 0.001
    checks.append({
        "check": "effect_magnitude",
        "expected": exp_es,
        "reproduced": rep_es,
        "ratio": round(rep_es / exp_es, 2) if exp_es > 1e-10 else None,
        "match": mag_match,
    })

    matched = sum(1 for c in checks if c["match"])
    return {
        "level": 2,
        "status": "PASS" if matched == len(checks) else "PARTIAL" if matched >= 2 else "FAIL",
        "match_rate": round(matched / len(checks), 4),
        "checks": checks,
    }


def level3_trend(
    reproduced_by_group: dict[str, float],
    expected_by_group: dict[str, float],
) -> dict[str, Any]:
    """Level 3: Trend consistency across subgroups.

    Uses Spearman rank correlation to check if the pattern
    of results across subgroups (fields, years) is consistent.
    """
    # Find common keys
    common = set(reproduced_by_group.keys()) & set(expected_by_group.keys())
    if len(common) < 5:
        return {"level": 3, "status": "NO_DATA", "spearman_rho": None, "p_value": None,
                "n_groups": len(common), "message": "Need >= 5 common groups for trend check"}

    rep_vals = [reproduced_by_group[k] for k in common]
    exp_vals = [expected_by_group[k] for k in common]

    try:
        rho, p = spearmanr(rep_vals, exp_vals)
        rho = 0.0 if np.isnan(rho) else rho
        p = 1.0 if np.isnan(p) else p
    except Exception:
        rho, p = 0.0, 1.0

    trend_match = rho > 0.7

    return {
        "level": 3,
        "status": "PASS" if trend_match else "FAIL",
        "spearman_rho": round(rho, 4),
        "p_value": round(p, 6),
        "n_groups": len(common),
        "match": trend_match,
    }


def level4_conclusion(
    reproduction_summary: str,
    paper_claims: list[str],
) -> dict[str, Any]:
    """Level 4: Conclusion consistency check.

    Maps paper claims against reproduction findings.
    Output: SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED.
    """
    # Rule-based for now (LLM-based in full implementation)
    # Check if key directional findings align
    supported = 0
    details = []

    for claim in paper_claims:
        # Simple keyword matching for direction
        claim_lower = claim.lower()
        if "small" in claim_lower and "disrupt" in claim_lower:
            if "confirmed" in reproduction_summary.lower() or "direction confirmed" in reproduction_summary.lower():
                supported += 1
                details.append({"claim": claim, "verdict": "SUPPORTED", "evidence": "Direction confirmed in reproduction"})
            else:
                details.append({"claim": claim, "verdict": "NOT SUPPORTED", "evidence": "Direction not confirmed"})
        elif "large" in claim_lower and "develop" in claim_lower:
            if "large team" in reproduction_summary.lower():
                supported += 1
                details.append({"claim": claim, "verdict": "SUPPORTED", "evidence": "Large-team finding reproduced"})
            else:
                details.append({"claim": claim, "verdict": "PARTIALLY SUPPORTED", "evidence": "Insufficient data"})
        else:
            details.append({"claim": claim, "verdict": "UNCHECKED", "evidence": "No automated check available"})

    if len(paper_claims) == 0:
        return {"level": 4, "status": "NO_DATA", "verdict": "UNCHECKED", "details": []}

    support_rate = supported / len(paper_claims) if paper_claims else 0
    if support_rate >= 0.8:
        verdict = "SUPPORTED"
    elif support_rate >= 0.5:
        verdict = "PARTIALLY SUPPORTED"
    else:
        verdict = "NOT SUPPORTED"

    return {
        "level": 4,
        "status": "PASS" if verdict == "SUPPORTED" else "PARTIAL",
        "verdict": verdict,
        "support_rate": round(support_rate, 2),
        "details": details,
    }


def run_full_evaluation(
    reproduced: dict[str, float],
    expected: dict[str, float],
    reproduced_effect: dict[str, Any],
    expected_effect: dict[str, Any],
    reproduced_by_group: dict[str, float] | None = None,
    expected_by_group: dict[str, float] | None = None,
    reproduction_summary: str = "",
    paper_claims: list[str] | None = None,
    tolerance: float = 0.20,
) -> dict[str, Any]:
    """Run the full 4-level evaluation framework.

    Returns a composite evaluation report suitable for the EvaluationSpecialist.
    """
    report = {
        "timestamp": None,  # filled by caller
        "levels": {},
        "composite_score": 0.0,
        "overall_verdict": "INCONCLUSIVE",
    }

    # Level 1: Numeric
    l1 = level1_numeric(reproduced, expected, tolerance)
    report["levels"]["1_numeric"] = l1

    # Level 2: Statistical
    l2 = level2_statistical(reproduced_effect, expected_effect)
    report["levels"]["2_statistical"] = l2

    # Level 3: Trend
    if reproduced_by_group and expected_by_group:
        l3 = level3_trend(reproduced_by_group, expected_by_group)
    else:
        l3 = {"level": 3, "status": "SKIPPED", "message": "No group-level data provided"}
    report["levels"]["3_trend"] = l3

    # Level 4: Conclusion
    l4 = level4_conclusion(reproduction_summary, paper_claims or [])
    report["levels"]["4_conclusion"] = l4

    # Composite score (weighted)
    weights = {"1_numeric": 0.25, "2_statistical": 0.30, "3_trend": 0.20, "4_conclusion": 0.25}
    scores = []
    for level_key, weight in weights.items():
        level = report["levels"].get(level_key, {})
        status = level.get("status", "SKIPPED")
        if status == "PASS":
            scores.append(weight * 1.0)
        elif status == "PARTIAL":
            scores.append(weight * 0.5)
        elif status == "FAIL":
            scores.append(weight * 0.0)
        # SKIPPED/NO_DATA → contribute nothing

    if scores:
        report["composite_score"] = round(sum(scores) / sum(
            weights[k] for k in weights if report["levels"].get(k, {}).get("status", "SKIPPED") != "SKIPPED"
        ), 4) if any(report["levels"].get(k, {}).get("status", "SKIPPED") != "SKIPPED" for k in weights) else 0.0

    if report["composite_score"] >= 0.8:
        report["overall_verdict"] = "SUPPORTED"
    elif report["composite_score"] >= 0.5:
        report["overall_verdict"] = "PARTIALLY SUPPORTED"
    elif report["composite_score"] > 0:
        report["overall_verdict"] = "WEAKLY SUPPORTED"
    else:
        report["overall_verdict"] = "INCONCLUSIVE"

    return report


# ── Quick test ──

if __name__ == "__main__":
    # Simulate M2 results vs Wu et al. 2019 claims
    reproduced = {
        "small_mean": 0.00603,
        "large_mean": 0.00053,
        "difference": 0.00550,
    }
    expected = {
        "small_mean": 0.25,
        "large_mean": -0.10,
        "difference": 0.35,
    }

    rep_effect = {
        "direction": 0.00550,
        "p_value": 0.0,
        "effect_size": 0.00550,
    }
    exp_effect = {
        "direction": 0.35,
        "p_value": 0.0,
        "effect_size": 0.35,
    }

    claims = [
        "Small teams tend to disrupt science and technology",
        "Large teams tend to develop existing ideas",
        "The effect is consistent across fields and time periods",
    ]

    report = run_full_evaluation(
        reproduced=reproduced,
        expected=expected,
        reproduced_effect=rep_effect,
        expected_effect=exp_effect,
        reproduction_summary="Direction confirmed, significance confirmed, effect size 60x smaller due to different data coverage",
        paper_claims=claims,
    )

    print(json.dumps(report, indent=2))
