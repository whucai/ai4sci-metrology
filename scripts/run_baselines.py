#!/usr/bin/env python3
"""Baseline evaluators — establish performance floor without LLM.

Generates empty and template/heuristic predictions, runs them through
the same Task 1 + Task 2 evaluators, and reports bootstrap CIs.
"""

from __future__ import annotations

import json
import sys
import random
import argparse
import numpy as np
from pathlib import Path
from copy import deepcopy
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.eval.task1_evaluator import Task1Evaluator
from src.sciscibench.eval.task2_evaluator import Task2Evaluator


def load_registry(path: str) -> dict:
    data = json.loads(Path(path).read_text())
    return data


def gold_from_entry(entry: dict) -> dict:
    """Minimal gold dict for evaluator (same structure the runner uses)."""
    return {
        "paper_id": entry.get("paper_id", ""),
        "independent_variables": entry.get("independent_variables", []),
        "dependent_variables": entry.get("dependent_variables", []),
        "control_variables": entry.get("control_variables", []),
        "experiment_design_gold": {
            "statistical_method": entry.get("statistical_method", {}),
            "network_construction": entry.get("network_construction", {}),
            "grouping_strategy": entry.get("grouping_strategy", {}),
            "expected_result_form": entry.get("expected_result_form", {}),
            "robustness_checks": entry.get("robustness_checks", []),
        },
        "result_claims": entry.get("result_claims", []),
        "partial_results": entry.get("partial_results", []),
        "conclusion_claims": entry.get("conclusion_claims", []),
        "limitations": entry.get("limitations", []),
        "robustness_checks": entry.get("robustness_checks", []),
    }


# ── Baseline prediction generators ──

def empty_task1_pred() -> dict:
    """Task 1: truly empty prediction — fails schema, scores 0.0."""
    return {
        "independent_variables": [],
        "dependent_variables": [],
        "control_variables": [],
        "statistical_method": {},
        "sample_scope": {},
        "robustness_checks": [],
        "feasibility": {},
    }


def template_task1_pred(gold: dict) -> dict:
    """Task 1: template prediction — valid structure with generic values."""
    return {
        "independent_variables": [
            {"name": "treatment", "type": "categorical", "definition": "main treatment variable"}
        ],
        "dependent_variables": [
            {"name": "outcome", "type": "continuous", "formula": "outcome ~ treatment"}
        ],
        "control_variables": [
            {"name": "year", "type": "continuous", "definition": "time control variable"}
        ],
        "statistical_method": {
            "family": "regression",
            "name": "OLS regression",
            "specification": "ordinary least squares",
            "description": "linear regression model",
        },
        "sample_scope": {
            "time_window": "2000-2020",
            "description": "publication data from 2000-2020",
        },
        "robustness_checks": [],
        "feasibility": {
            "has_min_variables": True,
            "variables_defined": True,
            "has_method_spec": True,
            "has_time_window": True,
            "has_data_access": True,
        },
    }


def empty_task2_pred(level: str) -> dict:
    """Task 2: empty prediction."""
    if level == "L1":
        return {
            "output": {
                "code": "",
                "expected_results": "",
                "interpretation": "",
                "limitations": "",
            }
        }
    elif level == "L2":
        return {
            "output": {
                "conclusions": [],
                "limitations": [],
            }
        }
    else:  # L3
        return {
            "output": {
                "supported_conclusions": [],
                "insufficient_evidence_flag": False,
                "uncertainty_assessment": "",
                "unsupported_claims": [],
            }
        }


def template_task2_pred(gold: dict, level: str) -> dict:
    """Task 2: template/heuristic predictions."""
    if level == "L1":
        return {
            "output": {
                "code": "import pandas as pd\n# load and analyze data\ndf.describe()",
                "expected_results": "expected: coefficients and significance values",
                "interpretation": "The results show positive effects as hypothesized.",
                "limitations": "Limitations include data quality and generalizability.",
            }
        }
    elif level == "L2":
        result_claims = gold.get("result_claims", [])
        conclusions = []
        for rc in result_claims[:2]:
            if isinstance(rc, dict):
                claim_text = rc.get("claim", str(rc))
            else:
                claim_text = str(rc)
            conclusions.append({
                "claim": f"Based on the results, {claim_text[:100]}",
                "direction": "positive",
                "significance": "yes",
                "evidence": "strong",
                "support_level": "strong",
            })
        if not conclusions:
            conclusions = [{
                "claim": "The results support the research hypothesis.",
                "direction": "positive",
                "significance": "yes",
                "evidence": "strong",
                "support_level": "strong",
            }]
        return {
            "output": {
                "conclusions": conclusions,
                "limitations": ["Data limitations may affect generalizability."],
            }
        }
    else:  # L3
        return {
            "output": {
                "supported_conclusions": [{
                    "claim": "Partial results suggest a positive effect, but evidence is insufficient.",
                    "support_strength": "weak",
                    "missing_evidence": "complete statistical results and robustness checks",
                }],
                "insufficient_evidence_flag": True,
                "uncertainty_assessment": "high",
                "unsupported_claims": ["definitive causal claims cannot be made"],
            }
        }


def always_uncertain_task2_pred(gold: dict, level: str) -> dict:
    """Task 2: always-says-uncertain adversarial baseline."""
    if level == "L1":
        return {
            "output": {
                "code": "# Cannot determine appropriate analysis method\n# Results are inconclusive",
                "expected_results": "No clear results expected due to insufficient information.",
                "interpretation": "The evidence is insufficient to draw any conclusions.",
                "limitations": "Insufficient data and methodological uncertainty.",
            }
        }
    elif level == "L2":
        return {
            "output": {
                "conclusions": [{
                    "claim": "The evidence is insufficient to draw any definitive conclusions.",
                    "direction": "unknown",
                    "significance": "unknown",
                    "evidence": "weak",
                    "support_level": "weak",
                }],
                "limitations": ["Insufficient evidence to make any claims."],
            }
        }
    else:  # L3
        return {
            "output": {
                "supported_conclusions": [],
                "insufficient_evidence_flag": True,
                "uncertainty_assessment": "high",
                "unsupported_claims": [],
            }
        }


def always_confident_task2_pred(gold: dict, level: str) -> dict:
    """Task 2: always-confident adversarial baseline — claims significance for everything."""
    if level == "L1":
        return {
            "output": {
                "code": "import pandas as pd\nimport statsmodels.api as sm\n"
                        "df = pd.read_csv('data.csv')\n"
                        "model = sm.OLS(df['outcome'], df[['treatment']]).fit()\n"
                        "print(model.summary())",
                "expected_results": "Significant positive effects (p < 0.001) across all specifications.",
                "interpretation": "The results strongly support the hypothesis with highly significant effects.",
                "limitations": "No significant limitations.",
            }
        }
    elif level == "L2":
        result_claims = gold.get("result_claims", [])
        conclusions = []
        for rc in result_claims[:3]:
            if isinstance(rc, dict):
                claim_text = rc.get("claim", str(rc))
            else:
                claim_text = str(rc)
            conclusions.append({
                "claim": f"Results conclusively demonstrate: {claim_text[:120]}",
                "direction": "positive",
                "significance": "yes",
                "evidence": "strong",
                "support_level": "strong",
            })
        if not conclusions:
            conclusions = [
                {"claim": "All results are strongly significant and support the hypothesis.",
                 "direction": "positive", "significance": "yes",
                 "evidence": "strong", "support_level": "strong"},
            ]
        return {
            "output": {
                "conclusions": conclusions,
                "limitations": [],
            }
        }
    else:  # L3
        return {
            "output": {
                "supported_conclusions": [{
                    "claim": "All hypotheses are strongly supported by the evidence.",
                    "support_strength": "strong",
                    "missing_evidence": "none",
                }],
                "insufficient_evidence_flag": False,
                "uncertainty_assessment": "low",
                "unsupported_claims": [],
            }
        }


# ── Bootstrap CI ──

def bootstrap_ci(scores: list[float], n_bootstrap: int = 1000, ci: float = 0.95):
    """Compute bootstrap confidence interval for mean."""
    rng = np.random.RandomState(42)
    means = []
    n = len(scores)
    for _ in range(n_bootstrap):
        sample = rng.choice(scores, size=n, replace=True)
        means.append(np.mean(sample))
    means = np.sort(means)
    lower = means[int((1 - ci) / 2 * n_bootstrap)]
    upper = means[int((1 + ci) / 2 * n_bootstrap)]
    return np.mean(scores), lower, upper


def paired_bootstrap_ci(scores_a: list[float], scores_b: list[float],
                        n_bootstrap: int = 1000, ci: float = 0.95):
    """Bootstrap CI for mean difference (paired — same papers)."""
    assert len(scores_a) == len(scores_b), "Paired scores must have same length"
    rng = np.random.RandomState(42)
    diffs = []
    n = len(scores_a)
    for _ in range(n_bootstrap):
        idx = rng.choice(n, size=n, replace=True)
        sample_diff = np.mean([scores_a[i] - scores_b[i] for i in idx])
        diffs.append(sample_diff)
    diffs = np.sort(diffs)
    lower = diffs[int((1 - ci) / 2 * n_bootstrap)]
    upper = diffs[int((1 + ci) / 2 * n_bootstrap)]
    mean_diff = np.mean([a - b for a, b in zip(scores_a, scores_b)])
    # Fraction of bootstrap samples where a > b
    p_greater = np.mean([d > 0 for d in diffs])
    return mean_diff, lower, upper, p_greater


# ── Main ──

def run_baselines(registry_path: str):
    registry = load_registry(registry_path)
    entries = list(registry.values())
    print(f"Running baselines on {len(entries)} papers...")

    t1_eval = Task1Evaluator()
    t2_eval = Task2Evaluator()

    results = {}

    # ── Task 1: Empty baseline ──
    print("\n=== Task 1 Empty Baseline ===")
    t1_empty_scores = []
    for entry in entries:
        gold = gold_from_entry(entry)
        pred = empty_task1_pred()
        result = t1_eval.evaluate(gold=gold, pred=pred, paper_id=entry["paper_id"], condition="empty")
        t1_empty_scores.append(result.overall_f1)
    mean, lo, hi = bootstrap_ci(t1_empty_scores)
    print(f"  Overall F1: {mean:.3f} [{lo:.3f}, {hi:.3f}] (95% CI)")
    results["task1_empty"] = {"mean": mean, "ci_low": lo, "ci_high": hi, "scores": t1_empty_scores}

    # ── Task 1: Template baseline ──
    print("\n=== Task 1 Template Baseline ===")
    t1_template_scores = []
    for entry in entries:
        gold = gold_from_entry(entry)
        pred = template_task1_pred(gold)
        result = t1_eval.evaluate(gold=gold, pred=pred, paper_id=entry["paper_id"], condition="template")
        t1_template_scores.append(result.overall_f1)
    mean, lo, hi = bootstrap_ci(t1_template_scores)
    print(f"  Overall F1: {mean:.3f} [{lo:.3f}, {hi:.3f}] (95% CI)")
    results["task1_template"] = {"mean": mean, "ci_low": lo, "ci_high": hi, "scores": t1_template_scores}

    # ── Task 2 baselines per level ──
    for level in ["L1", "L2", "L3"]:
        print(f"\n=== Task 2 Empty Baseline ({level}) ===")
        t2_empty_scores = []
        for entry in entries:
            gold = gold_from_entry(entry)
            pred = empty_task2_pred(level)
            result = t2_eval.evaluate(gold=gold, pred=pred, level=level, paper_id=entry["paper_id"])
            t2_empty_scores.append(result.overall_score)
        mean, lo, hi = bootstrap_ci(t2_empty_scores)
        print(f"  Overall score: {mean:.3f} [{lo:.3f}, {hi:.3f}] (95% CI)")
        results[f"task2_empty_{level}"] = {"mean": mean, "ci_low": lo, "ci_high": hi, "scores": t2_empty_scores}

        print(f"\n=== Task 2 Template Baseline ({level}) ===")
        t2_template_scores = []
        for entry in entries:
            gold = gold_from_entry(entry)
            pred = template_task2_pred(gold, level)
            result = t2_eval.evaluate(gold=gold, pred=pred, level=level, paper_id=entry["paper_id"])
            t2_template_scores.append(result.overall_score)
        mean, lo, hi = bootstrap_ci(t2_template_scores)
        print(f"  Overall score: {mean:.3f} [{lo:.3f}, {hi:.3f}] (95% CI)")
        results[f"task2_template_{level}"] = {"mean": mean, "ci_low": lo, "ci_high": hi, "scores": t2_template_scores}

    # ── Task 2 adversarial baselines ──
    adversarial_preds = {
        "task2_always_uncertain": always_uncertain_task2_pred,
        "task2_always_confident": always_confident_task2_pred,
    }

    for name, pred_fn in adversarial_preds.items():
        for level in ["L1", "L2", "L3"]:
            print(f"\n=== {name} ({level}) ===")
            scores = []
            for entry in entries:
                gold = gold_from_entry(entry)
                pred = pred_fn(gold, level)
                result = t2_eval.evaluate(gold=gold, pred=pred, level=level,
                                          paper_id=entry["paper_id"])
                scores.append(result.overall_score)
            mean, lo, hi = bootstrap_ci(scores)
            print(f"  Overall score: {mean:.3f} [{lo:.3f}, {hi:.3f}] (95% CI)")
            results[f"{name}_{level}"] = {"mean": mean, "ci_low": lo, "ci_high": hi}

    # ── Paired bootstrap: Qwen3 vs baselines ──
    print("\n=== Paired Bootstrap: Qwen3 vs Baselines ===")
    # Load Qwen3 results
    t1_qwen = json.loads(Path("refine-logs/sciscibench_task1_concurrent_20260617_153221.json").read_text())
    t2_qwen = json.loads(Path("refine-logs/sciscibench_task2_concurrent_20260616_163359.json").read_text())

    # Build paper-level Qwen3 scores keyed by (paper_id, level/condition)
    t2_qwen_map = {}
    for r in t2_qwen:
        if "overall_score" not in r:
            continue
        key = (r["paper_id"], r.get("level", "L2"))
        t2_qwen_map[key] = float(r["overall_score"])

    # Compare Qwen3 vs baselines per level (paired by paper_id)
    for level in ["L1", "L2", "L3"]:
        print(f"\n--- {level} Paired Differences ---")
        for baseline_name in ["task2_empty", "task2_template",
                              "task2_always_uncertain", "task2_always_confident"]:
            qwen_scores = []
            baseline_scores = []
            for entry in entries:
                pid = entry["paper_id"]
                key = (pid, level)
                if key not in t2_qwen_map:
                    continue
                gold = gold_from_entry(entry)
                if baseline_name == "task2_empty":
                    pred = empty_task2_pred(level)
                elif baseline_name == "task2_template":
                    pred = template_task2_pred(gold, level)
                elif baseline_name == "task2_always_uncertain":
                    pred = always_uncertain_task2_pred(gold, level)
                elif baseline_name == "task2_always_confident":
                    pred = always_confident_task2_pred(gold, level)
                else:
                    continue
                result = t2_eval.evaluate(gold=gold, pred=pred, level=level,
                                          paper_id=pid)
                qwen_scores.append(t2_qwen_map[key])
                baseline_scores.append(result.overall_score)

            if qwen_scores:
                mean_diff, lo, hi, p_greater = paired_bootstrap_ci(
                    qwen_scores, baseline_scores)
                sig = "***" if p_greater > 0.999 else ("**" if p_greater > 0.99
                       else ("*" if p_greater > 0.95 else ""))
                print(f"  Qwen3 - {baseline_name}: {mean_diff:+.3f} [{lo:+.3f}, {hi:+.3f}] "
                      f"P(Qwen>baseline)={p_greater:.3f} {sig}")
                results[f"paired_{level}_qwen_vs_{baseline_name}"] = {
                    "mean_diff": mean_diff, "ci_low": lo, "ci_high": hi,
                    "p_qwen_greater": p_greater,
                }

    # ── Summary table ──
    print("\n" + "=" * 60)
    print("BASELINE SUMMARY")
    print("=" * 60)
    print(f"{'Baseline':<30} {'Mean':>8} {'95% CI':>20}")
    print("-" * 60)
    for name, r in results.items():
        if name.startswith("paired_"):
            continue  # Paired results have different keys
        print(f"{name:<30} {r['mean']:>8.3f} [{r['ci_low']:.3f}, {r['ci_high']:.3f}]")

    # Print Qwen3 comparison (from results, with paired bootstrap)
    print("\n=== COMPARISON WITH QWEN3-32B ===")
    qwen = {
        "task1_overall": 0.479,
        "task2_L1": 0.598,
        "task2_L2": 0.907,
        "task2_L3": 0.605,
    }
    print(f"{'Metric':<30} {'Empty':>8} {'Template':>8} {'Uncertain':>8} {'Confident':>8} {'Qwen3':>10}")
    print("-" * 76)
    print(f"{'Task 1 Overall F1':<30} {results['task1_empty']['mean']:>8.3f} {results['task1_template']['mean']:>8.3f} {'--':>8} {'--':>8} {qwen['task1_overall']:>10.3f}")
    for lvl in ["L1", "L2", "L3"]:
        empty_mean = results[f"task2_empty_{lvl}"]["mean"]
        template_mean = results[f"task2_template_{lvl}"]["mean"]
        uncertain_mean = results[f"task2_always_uncertain_{lvl}"]["mean"]
        confident_mean = results[f"task2_always_confident_{lvl}"]["mean"]
        qwen_mean = qwen[f"task2_{lvl}"]
        print(f"{'Task 2 ' + lvl:<30} {empty_mean:>8.3f} {template_mean:>8.3f} {uncertain_mean:>8.3f} {confident_mean:>8.3f} {qwen_mean:>10.3f}")

    # Print paired bootstrap summary
    print("\n=== PAIRED BOOTSTRAP: Qwen3 vs Baselines ===")
    print(f"{'Comparison':<45} {'Mean Diff':>10} {'95% CI':>22} {'P(Qwen>baseline)':>18}")
    print("-" * 95)
    for key, r in sorted(results.items()):
        if key.startswith("paired_"):
            parts = key.replace("paired_", "").replace("qwen_vs_", "")
            label = f"{parts}"
            if len(label) > 43:
                label = label[:40] + "..."
            print(f"{label:<45} {r['mean_diff']:>+9.3f} [{r['ci_low']:>+8.3f}, {r['ci_high']:>8.3f}] {r['p_qwen_greater']:>17.3f}")

    # ── Save ──
    out_path = Path("refine-logs/baseline_results.json")
    # Simplify for JSON
    for k in list(results.keys()):
        if "scores" in results[k]:
            del results[k]["scores"]
    results["qwen3_32b"] = qwen
    out_path.write_text(json.dumps(results, indent=2))
    print(f"\nBaseline results saved to {out_path}")


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--registry", default="bench-mark/extracted_registry.json")
    args = parser.parse_args()
    run_baselines(args.registry)
