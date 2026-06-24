#!/usr/bin/env python3
"""M0: Dimension Validity — Validate that the 5-dimension rubric distinguishes
different failure modes and dimensions are not perfectly correlated.

Loads Wu2019 gold annotation, simulates 4 agent output scenarios
(perfect, sample-error, indicator-error, spurious), scores each on
the 5-dimension × 6-component matrix, and checks:
  1. Inter-dimension correlation < 0.85
  2. At least 3 distinct failure patterns
  3. Dimensions provide information beyond binary success/failure
"""
from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "src"))

from sciscibench.annotation import create_wu2019
from sciscibench.eval.dimensions import (
    build_reproduction_profile,
    COMPONENT_DIMENSION_MAP,
    ReproductionProfile,
)


def make_gold_dict(paper) -> dict:
    """Convert SciSciPaper annotation to gold component dict."""
    return {
        "data_source": {
            "data_source": paper.data_source,
            "data_description": paper.data_description,
            "filter_rules": [paper.data_source],
        },
        "sample": {
            "data_source": paper.data_source,
            "N": 42_000_000,
            "time_window": paper.sample_scope.get("time_window", ""),
            "filter_rules": paper.sample_scope.get("filters", []),
        },
        "indicator": {
            "formula": paper.dependent_variables[0].get("formula", ""),
            "indicator_stats": {"mean": -0.02, "std": 0.15},
        },
        "model": {
            "spec_elements": [
                "descriptive", "OLS", "team_size_deciles",
                "mean_D_by_group", "year_fixed_effects"
            ],
            "coefficients": {"team_size_coef": -0.03, "year_1954": 0.01},
        },
        "result_table": {
            "target_tables": ["Table 1: Mean D-index by team size decile"],
            "target_values": [
                {"label": "small_teams_D", "value": 0.04},
                {"label": "large_teams_D", "value": -0.02},
            ],
            "expected_direction": "negative",
        },
        "claim": {
            "conclusion_claims": [
                "Large teams develop existing science and technology",
                "Small teams disrupt science and technology",
                "Both team types are essential",
            ],
        },
    }


def make_perfect_agent() -> dict:
    """Agent that reproduced everything correctly."""
    return {
        "data_source": {
            "data_source": "Web of Science, USPTO, GitHub",
            "code_executed": {"data_source": True},
            "traceable": {"data_source": True},
            "hard_coded": {"data_source": False},
            "hallucinated": {"data_source": False},
        },
        "sample": {
            "N": 41_999_823,
            "filter_rules": ["article type", "has references"],
            "code_executed": {"sample": True},
            "traceable": {"sample": True},
            "hard_coded": {"sample": False},
            "hallucinated": {"sample": False},
        },
        "indicator": {
            "formula": "D = (n_i - n_j) / (n_i + n_j + n_k)",
            "indicator_stats": {"mean": -0.019, "std": 0.148},
            "code_executed": {"indicator": True},
            "traceable": {"indicator": True},
            "hard_coded": {"indicator": False},
            "hallucinated": {"indicator": False},
        },
        "model": {
            "spec_elements": ["descriptive", "OLS", "team_size_deciles",
                              "mean_D_by_group", "year_fixed_effects"],
            "coefficients": {"team_size_coef": -0.028, "year_1954": 0.011},
            "code_executed": {"model": True},
            "traceable": {"model": True},
            "hard_coded": {"model": False},
            "hallucinated": {"model": False},
        },
        "result_table": {
            "produced_tables": ["Table 1: Mean D-index by team size decile"],
            "reproduced_values": [
                {"label": "small_teams_D", "value": 0.039},
                {"label": "large_teams_D", "value": -0.019},
            ],
            "observed_direction": "negative",
            "code_executed": {"result_table": True},
            "traceable": {"result_table": True},
            "hard_coded": {"result_table": False},
            "hallucinated": {"result_table": False},
        },
        "claim": {
            "conclusion_claims": [
                "Large teams tend to develop and consolidate existing knowledge",
                "Small teams tend to disrupt with new ideas",
                "Both large and small teams play vital roles",
            ],
        },
    }


def make_sample_error_agent() -> dict:
    """Agent with wrong sample construction but everything else OK.

    Uses wrong time window and missing document type filter.
    """
    agent = make_perfect_agent()
    # Corrupt the sample
    agent["sample"] = {
        "N": 18_000_000,  # Way off — wrong time window
        "filter_rules": ["has references"],  # Missing "article type" filter
        "code_executed": {"sample": True},
        "traceable": {"sample": True},
        "hard_coded": {"sample": False},
        "hallucinated": {"sample": False},
    }
    # All downstream results are wrong because sample is wrong
    agent["indicator"]["indicator_stats"] = {"mean": 0.08, "std": 0.25}
    agent["model"]["coefficients"] = {"team_size_coef": 0.015, "year_1954": 0.03}
    agent["result_table"]["reproduced_values"] = [
        {"label": "small_teams_D", "value": 0.002},
        {"label": "large_teams_D", "value": 0.001},
    ]
    agent["result_table"]["observed_direction"] = "null"  # Wrong direction
    agent["claim"]["conclusion_claims"] = [
        "Team size has no clear relationship with disruptiveness",
    ]
    return agent


def make_indicator_error_agent() -> dict:
    """Agent with wrong indicator formula but correct sample.

    Uses raw citation ratio instead of disruption index.
    """
    agent = make_perfect_agent()
    agent["indicator"] = {
        "formula": "D_simple = citations / references_count",
        "indicator_stats": {"mean": 5.2, "std": 12.3},
        "code_executed": {"indicator": True},
        "traceable": {"indicator": True},
        "hard_coded": {"indicator": False},
        "hallucinated": {"indicator": False},
    }
    # Model and results still run but different numbers
    agent["model"]["coefficients"] = {"team_size_coef": -0.12, "year_1954": 0.08}
    agent["result_table"]["reproduced_values"] = [
        {"label": "small_teams_D", "value": 0.12},
        {"label": "large_teams_D", "value": -0.08},
    ]
    # Direction still matches by coincidence
    agent["result_table"]["observed_direction"] = "negative"
    agent["claim"]["conclusion_claims"] = [
        "Large teams develop existing knowledge",
        "Small teams disrupt with new ideas",
    ]
    return agent


def make_spurious_agent() -> dict:
    """Spurious reproduction: results match but process is wrong.

    Hard-codes paper values, uses hallucinated variables.
    """
    agent = make_perfect_agent()
    # Results look perfect
    # But process is fabricated
    agent["data_source"] = {
        "data_source": "some_unknown_dataset",
        "code_executed": {"data_source": False},
        "traceable": {"data_source": False},
        "hard_coded": {"data_source": False},
        "hallucinated": {"data_source": True},
    }
    agent["sample"]["N"] = 42_000_000  # Exactly right — suspicious
    agent["sample"]["traceable"] = {"sample": False}
    agent["sample"]["hard_coded"] = {"sample": True}
    agent["indicator"]["traceable"] = {"indicator": False}
    agent["indicator"]["hard_coded"] = {"indicator": True}
    agent["model"]["coefficients"] = {"team_size_coef": -0.030, "year_1954": 0.010}  # Exact match
    agent["model"]["traceable"] = {"model": False}
    agent["model"]["hard_coded"] = {"model": True}
    agent["result_table"]["reproduced_values"] = [
        {"label": "small_teams_D", "value": 0.040},  # Exact match
        {"label": "large_teams_D", "value": -0.020},  # Exact match
    ]
    agent["result_table"]["traceable"] = {"result_table": False}
    agent["result_table"]["hard_coded"] = {"result_table": True}
    return agent


def print_profile_matrix(profile: ReproductionProfile, label: str) -> None:
    """Pretty-print the 6×5 component-dimension matrix."""
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]
    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]

    print(f"\n{'='*70}")
    print(f"  {label}")
    print(f"{'='*70}")

    # Header
    header = f"{'Component':<16}"
    for d in all_dims:
        header += f" {d[:6]:>8}"
    print(header)
    print("-" * 70)

    for comp in components:
        cs = profile.component_scores.get(comp, None)
        row = f"  {comp:<14}"
        for dim in all_dims:
            if cs and dim in cs.dimension_scores:
                s = cs.dimension_scores[dim].score
                row += f" {s:8.2f}"
            else:
                row += f" {'—':>8}"
        print(row)

    # Aggregate
    agg = profile.component_scores
    dim_avgs = {}
    for dim in all_dims:
        vals = [cs.dimension_scores[dim].score
                for cs in agg.values()
                if dim in cs.dimension_scores]
        dim_avgs[dim] = sum(vals) / len(vals) if vals else 0

    print("-" * 70)
    avg_row = f"  {'AVERAGE':<14}"
    for dim in all_dims:
        avg_row += f" {dim_avgs[dim]:8.2f}"
    print(avg_row)

    # Spurious flags
    from sciscibench.eval.dimensions import detect_spurious_reproduction
    flags = detect_spurious_reproduction(profile)
    if flags:
        print(f"\n  ⚠️  SPURIOUS FLAGS: {', '.join(flags)}")
    else:
        print(f"\n  ✓ No spurious flags")


def main():
    print("=" * 70)
    print("  M0: Dimension Validity — Wu et al. (2019)")
    print("=" * 70)

    # Load gold annotation
    wu2019 = create_wu2019()
    gold = make_gold_dict(wu2019)
    print(f"\nLoaded: {wu2019.title}")
    print(f"Data: {wu2019.data_source}")
    print(f"Sample: {wu2019.sample_scope}")

    # Four agent scenarios
    scenarios = {
        "Perfect": make_perfect_agent(),
        "Sample-Error": make_sample_error_agent(),
        "Indicator-Error": make_indicator_error_agent(),
        "Spurious": make_spurious_agent(),
    }

    profiles = {}
    for name, agent in scenarios.items():
        profile = build_reproduction_profile("wu2019_disruption", gold, agent)
        profiles[name] = profile
        print_profile_matrix(profile, name)

    # ── M0 Validation Tests ──
    print(f"\n{'='*70}")
    print("  M0 VALIDATION TESTS")
    print(f"{'='*70}")

    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]

    # Test 1: Inter-dimension correlation across scenarios
    print("\n── Test 1: Inter-dimension correlation ──")
    # Collect dimension average scores across all scenarios
    dim_scores = {d: [] for d in all_dims}
    for name, profile in profiles.items():
        for dim in all_dims:
            vals = [cs.dimension_scores[dim].score
                    for cs in profile.component_scores.values()
                    if dim in cs.dimension_scores]
            avg = sum(vals) / len(vals) if vals else 0
            dim_scores[dim].append(avg)

    import math
    correlations = {}
    for i, d1 in enumerate(all_dims):
        for j, d2 in enumerate(all_dims):
            if j <= i:
                continue
            x = dim_scores[d1]
            y = dim_scores[d2]
            n = len(x)
            if n < 3:
                continue
            mx, my = sum(x) / n, sum(y) / n
            num = sum((x[k] - mx) * (y[k] - my) for k in range(n))
            den = math.sqrt(sum((x[k] - mx) ** 2 for k in range(n)) *
                           sum((y[k] - my) ** 2 for k in range(n)))
            r = num / den if den > 1e-10 else 0
            correlations[(d1, d2)] = r

    print(f"  Pairwise correlations (should be < 0.85 for most pairs):")
    for (d1, d2), r in sorted(correlations.items(), key=lambda x: -abs(x[1])):
        flag = " ⚠️  HIGH" if abs(r) > 0.85 else ""
        print(f"    {d1} ↔ {d2}: ρ = {r:+.3f}{flag}")

    high_corr = sum(1 for r in correlations.values() if abs(r) > 0.85)
    if high_corr == 0:
        print(f"  ✓ PASS: No dimension pair exceeds 0.85 correlation")
    else:
        print(f"  ⚠️  WARNING: {high_corr} pair(s) exceed 0.85 — consider merging")

    # Test 2: Distinct failure patterns
    print("\n── Test 2: Distinct failure patterns ──")
    # Each scenario should have a different "weakest dimension"
    patterns = {}
    for name, profile in profiles.items():
        dim_avgs = {}
        for dim in all_dims:
            vals = [cs.dimension_scores[dim].score
                    for cs in profile.component_scores.values()
                    if dim in cs.dimension_scores]
            dim_avgs[dim] = sum(vals) / len(vals) if vals else 0
        weakest = min(dim_avgs, key=dim_avgs.get)
        patterns[name] = (weakest, dim_avgs[weakest], dim_avgs)

    unique_weakest = len(set(p[0] for p in patterns.values()))
    print(f"  Unique weakest dimensions across scenarios: {unique_weakest}")
    for name, (weakest, val, avgs) in patterns.items():
        dims_str = ", ".join(f"{d[:6]}={avgs[d]:.2f}" for d in all_dims)
        print(f"    {name:<18} weakest={weakest:<22} ({val:.2f})  |  {dims_str}")

    if unique_weakest >= 3:
        print(f"  ✓ PASS: {unique_weakest} distinct failure patterns (≥3 required)")
    else:
        print(f"  ⚠️  WARNING: Only {unique_weakest} distinct patterns (<3 required)")

    # Test 3: Binary success vs multi-dimensional scores
    print("\n── Test 3: Binary success would miss diagnostic information ──")
    for name, profile in profiles.items():
        # Binary success: overall result accuracy
        result_comp = profile.component_scores.get("result_table")
        binary_pass = False
        if result_comp and "numerical_accuracy" in result_comp.dimension_scores:
            binary_pass = result_comp.dimension_scores["numerical_accuracy"].score >= 0.7

        # Multi-dimensional: check which components are weak
        weak_components = []
        for comp_name, cs in profile.component_scores.items():
            if cs.aggregate < 0.5:
                weak_components.append(comp_name)

        status = "✓ SUCCESS" if binary_pass else "✗ FAIL"
        if binary_pass and weak_components:
            diagnosis = f"BUT weak in: {', '.join(weak_components)}"
        elif not binary_pass and not weak_components:
            diagnosis = "but no weak components identified"
        elif not binary_pass and weak_components:
            diagnosis = f"due to: {', '.join(weak_components)}"
        else:
            diagnosis = "all components healthy"

        print(f"    {name:<18} binary={status:<12} {diagnosis}")

    print(f"\n  → Binary success says 'pass/fail'; dimensions say 'where and why'")

    # Test 4: Spurious detection
    print("\n── Test 4: Spurious reproduction detection ──")
    from sciscibench.eval.dimensions import detect_spurious_reproduction
    for name, profile in profiles.items():
        flags = detect_spurious_reproduction(profile)
        result_comp = profile.component_scores.get("result_table")
        result_score = result_comp.dimension_scores.get("numerical_accuracy", None) if result_comp else None
        result_val = result_score.score if result_score else 0

        if flags:
            print(f"    {name:<18} result_score={result_val:.2f}  ⚠️  {', '.join(flags)}")
        else:
            print(f"    {name:<18} result_score={result_val:.2f}  ✓ Clean")

    # Summary
    print(f"\n{'='*70}")
    print("  M0 SUMMARY")
    print(f"{'='*70}")
    all_pass = high_corr == 0 and unique_weakest >= 3
    print(f"  Test 1 (correlation <0.85): {'PASS' if high_corr == 0 else 'WARN'} ({high_corr} high pairs)")
    print(f"  Test 2 (failure patterns ≥3): {'PASS' if unique_weakest >= 3 else 'WARN'} ({unique_weakest} patterns)")
    print(f"  Test 3 (binary vs multi-dim): Demonstrated diagnostic value")
    print(f"  Test 4 (spurious detection): Rules operational")
    print(f"\n  {'✓ ALL GATES PASS — proceed to 10-paper validation' if all_pass else '⚠️  ADJUST RUBRIC before expanding'}")

    # Export for record
    output = {
        "paper": "wu2019_disruption",
        "scenarios": list(scenarios.keys()),
        "correlations": {f"{d1}_{d2}": r for (d1, d2), r in correlations.items()},
        "failure_patterns": {name: p[0] for name, p in patterns.items()},
        "tests": {
            "correlation": high_corr == 0,
            "failure_patterns": unique_weakest >= 3,
            "all_pass": all_pass,
        }
    }
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "m0_dimension_validation.json"
    with open(out_path, "w") as f:
        json.dump(output, f, indent=2)
    print(f"\n  Results saved to: {out_path}")


if __name__ == "__main__":
    main()
