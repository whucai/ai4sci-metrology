#!/usr/bin/env python3
"""Statistical Test Suite + Visualization for Reproducibility Metrology.

Completes L2 statistical equivalence framework:
  - Bootstrap confidence intervals for D-index and REI
  - Bayesian equivalence testing (ROPE)
  - Automated visualization: REI distribution, error breakdown, D-index comparison
"""

import sys, os, json, time
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import numpy as np
import pandas as pd

# Visualization imports — optional, gracefully handle if matplotlib missing
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    HAS_MPL = True
except ImportError:
    HAS_MPL = False


def bootstrap_ci(values: np.ndarray, n_bootstrap: int = 10000, alpha: float = 0.05) -> dict:
    """Compute bootstrap confidence interval for a statistic.

    Args:
        values: Observed sample values.
        n_bootstrap: Number of bootstrap resamples.
        alpha: Significance level (0.05 → 95% CI).

    Returns:
        {"mean": float, "ci_lower": float, "ci_upper": float, "std": float}
    """
    values = np.asarray(values, dtype=float)
    n = len(values)
    bootstrap_means = np.zeros(n_bootstrap)
    rng = np.random.RandomState(42)
    for i in range(n_bootstrap):
        idx = rng.randint(0, n, size=n)
        bootstrap_means[i] = np.mean(values[idx])
    lower = np.percentile(bootstrap_means, 100 * alpha / 2)
    upper = np.percentile(bootstrap_means, 100 * (1 - alpha / 2))
    return {
        "mean": float(np.mean(values)),
        "ci_lower": float(lower),
        "ci_upper": float(upper),
        "std": float(np.std(values, ddof=1)),
        "n": n,
        "alpha": alpha,
    }


def tost_equivalence(
    sample_a: np.ndarray | float,
    sample_b: np.ndarray | float,
    margin: float,
    n_bootstrap: int = 10000,
) -> dict:
    """Two One-Sided Tests for equivalence using bootstrap.

    Tests whether sample_a and sample_b differ by less than `margin`.

    Args:
        sample_a: Observed values (or single scalar).
        sample_b: Ground truth / reference values (or single scalar).
        margin: Equivalence margin (±margin).
        n_bootstrap: Bootstrap resamples.

    Returns:
        {"equivalent": bool, "p_upper": float, "p_lower": float, "diff_mean": float, "diff_ci": [lower, upper]}
    """
    a = np.asarray([sample_a]).flatten() if np.isscalar(sample_a) else np.asarray(sample_a)
    b = np.asarray([sample_b]).flatten() if np.isscalar(sample_b) else np.asarray(sample_b)

    # Bootstrap the difference in means
    n_a = len(a)
    diff_dist = np.zeros(n_bootstrap)
    rng = np.random.RandomState(42)
    for i in range(n_bootstrap):
        idx_a = rng.randint(0, n_a, size=n_a)
        if len(b) == 1:
            diff_dist[i] = np.mean(a[idx_a]) - b[0]
        else:
            n_b = len(b)
            idx_b = rng.randint(0, n_b, size=n_b)
            diff_dist[i] = np.mean(a[idx_a]) - np.mean(b[idx_b])

    diff_mean = np.mean(a) - np.mean(b)
    # Proportion of bootstrap diffs beyond ±margin
    p_upper = np.mean(diff_dist >= margin)
    p_lower = np.mean(diff_dist <= -margin)
    equivalent = (p_upper < 0.05) and (p_lower < 0.05)

    ci_lower = np.percentile(diff_dist, 2.5)
    ci_upper = np.percentile(diff_dist, 97.5)

    return {
        "equivalent": equivalent,
        "p_upper": round(float(p_upper), 4),
        "p_lower": round(float(p_lower), 4),
        "diff_mean": round(float(diff_mean), 6),
        "diff_ci": [round(float(ci_lower), 6), round(float(ci_upper), 6)],
        "margin": margin,
    }


def bayesian_rope(
    sample_a: np.ndarray | float,
    sample_b: np.ndarray | float,
    rope_radius: float = 0.01,
    n_mcmc: int = 20000,
) -> dict:
    """Bayesian Region of Practical Equivalence (ROPE) test.

    Uses a simple analytical normal-normal model: assume observed means are
    normally distributed, compute posterior of the difference, measure proportion
    of posterior falling within [-rope_radius, rope_radius].

    Args:
        sample_a, sample_b: Observed values.
        rope_radius: ROPE half-width.
        n_mcmc: Number of posterior samples.

    Returns:
        {"in_rope": float, "ci_lower": float, "ci_upper": float}
    """
    a = np.asarray([sample_a]).flatten() if np.isscalar(sample_a) else np.asarray(sample_a)
    b = np.asarray([sample_b]).flatten() if np.isscalar(sample_b) else np.asarray(sample_b)

    # Simple bootstrap posterior approximation
    diff_dist = np.zeros(n_mcmc)
    rng = np.random.RandomState(42)
    for i in range(n_mcmc):
        idx_a = rng.randint(0, len(a), size=len(a))
        a_mean = np.mean(a[idx_a])
        if len(b) == 1:
            diff_dist[i] = a_mean - b[0]
        else:
            idx_b = rng.randint(0, len(b), size=len(b))
            diff_dist[i] = a_mean - np.mean(b[idx_b])

    in_rope = np.mean(np.abs(diff_dist) < rope_radius)
    ci_lower = np.percentile(diff_dist, 2.5)
    ci_upper = np.percentile(diff_dist, 97.5)

    return {
        "in_rope": round(float(in_rope), 4),
        "ci_lower": round(float(ci_lower), 6),
        "ci_upper": round(float(ci_upper), 6),
        "rope_radius": rope_radius,
        "verdict": "equivalent" if in_rope > 0.95 else ("undecided" if in_rope > 0.05 else "not_equivalent"),
    }


def plot_rei_distribution(results: list[dict], output_path: str) -> str | None:
    """Plot REI distribution across papers."""
    if not HAS_MPL:
        return None

    rei_values = [r.get("REI", 0) for r in results]
    statuses = [r.get("status", "UNKNOWN") for r in results]
    colors = ["#2ecc71" if s == "SUCCESS" else "#e74c3c" if s == "FAILED" else "#f39c12" for s in statuses]

    fig, axes = plt.subplots(1, 2, figsize=(12, 5))

    # Histogram
    ax = axes[0]
    bins = np.arange(0, max(rei_values) + 2, 1) if rei_values else [0, 1]
    ax.hist(rei_values, bins=bins, color="#3498db", edgecolor="white", alpha=0.8)
    ax.axvline(np.mean(rei_values), color="#e74c3c", linestyle="--", label=f"Mean={np.mean(rei_values):.1f}")
    ax.set_xlabel("REI")
    ax.set_ylabel("Count")
    ax.set_title("REI Distribution Across Papers")
    ax.legend()

    # Scatter
    ax = axes[1]
    x = list(range(len(results)))
    ax.bar(x, rei_values, color=colors, alpha=0.8)
    ax.set_xlabel("Paper Index")
    ax.set_ylabel("REI")
    ax.set_title("REI by Paper")
    ax.axhline(y=np.mean(rei_values), color="#e74c3c", linestyle="--", alpha=0.5)

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def plot_error_breakdown(results: list[dict], output_path: str) -> str | None:
    """Plot error type distribution across all papers."""
    if not HAS_MPL:
        return None

    error_counts = {}
    for r in results:
        for e in r.get("error_types", []):
            error_counts[e] = error_counts.get(e, 0) + 1

    if not error_counts:
        return None

    fig, ax = plt.subplots(figsize=(8, 5))
    labels = list(error_counts.keys())
    values = list(error_counts.values())
    colors = plt.cm.RdYlGn_r([v / max(values) for v in values])

    ax.barh(labels, values, color=colors, alpha=0.8)
    ax.set_xlabel("Occurrences")
    ax.set_title("Error Type Distribution Across Reproductions")

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def plot_d_comparison(computed_d: list[float], gt_d: list[float], output_path: str) -> str | None:
    """Plot computed vs ground truth D-index."""
    if not HAS_MPL:
        return None

    computed = np.asarray(computed_d)
    ground = np.asarray(gt_d)

    fig, ax = plt.subplots(figsize=(6, 6))
    ax.scatter(ground, computed, alpha=0.6, s=40, c="#3498db")
    ax.plot([min(ground), max(ground)], [min(ground), max(ground)],
            "r--", linewidth=1, label="Perfect match")

    # R^2
    ss_res = np.sum((computed - ground) ** 2)
    ss_tot = np.sum((ground - np.mean(ground)) ** 2)
    r2 = 1 - ss_res / ss_tot if ss_tot > 0 else 0

    ax.set_xlabel("Ground Truth D-index")
    ax.set_ylabel("Computed D-index")
    ax.set_title(f"D-index Comparison (R²={r2:.3f})")
    ax.legend()

    plt.tight_layout()
    plt.savefig(output_path, dpi=150, bbox_inches="tight")
    plt.close()
    return output_path


def run_statistical_suite(results_json_paths: list[str], output_dir: str | None = None) -> dict:
    """Run full statistical analysis on a set of reproduction results.

    Args:
        results_json_paths: Paths to reproduction result JSON files.
        output_dir: Where to save plots and stats.

    Returns:
        Dict with comprehensive statistics.
    """
    output_dir = output_dir or str(Path(__file__).resolve().parent.parent / "refine-logs")
    os.makedirs(output_dir, exist_ok=True)

    all_results = []
    for path in results_json_paths:
        try:
            with open(path) as f:
                data = json.load(f)
            if isinstance(data, dict) and "status" in data:
                all_results.append(data)
        except Exception:
            continue

    if not all_results:
        return {"error": "No results loaded"}

    # REI statistics
    rei_values = [r.get("REI", 0) for r in all_results]
    rei_stats = bootstrap_ci(np.array(rei_values))

    # Status breakdown
    status_counts = {}
    for r in all_results:
        s = r.get("status", "UNKNOWN")
        status_counts[s] = status_counts.get(s, 0) + 1

    # D-index comparisons
    computed_d = []
    gt_d = []
    for r in all_results:
        cd = r.get("computed_D") or r.get("parsed_metrics", {}).get("D_index")
        gd = r.get("ground_truth_D") or r.get("subgraph_D") or r.get("precomputed_D")
        if cd is not None and gd is not None:
            computed_d.append(float(cd))
            gt_d.append(float(gd))

    d_abs_diff = [abs(ct - gd) for ct, gd in zip(computed_d, gt_d)] if computed_d else []

    # Generate plots
    plot_rei_distribution(all_results, os.path.join(output_dir, "rei_distribution.png"))
    plot_error_breakdown(all_results, os.path.join(output_dir, "error_breakdown.png"))
    if computed_d:
        plot_d_comparison(computed_d, gt_d, os.path.join(output_dir, "d_comparison.png"))
        # TOST + Bayesian on D-index deviations
        tost = tost_equivalence(np.array(d_abs_diff), 0.0, margin=0.05)
        rope = bayesian_rope(np.array(d_abs_diff), 0.0, rope_radius=0.01)
    else:
        tost, rope = {}, {}

    stats = {
        "n_papers": len(all_results),
        "rei_stats": rei_stats,
        "status_breakdown": status_counts,
        "d_index_comparison": {
            "n_pairs": len(computed_d),
            "mean_abs_diff": round(float(np.mean(d_abs_diff)), 6) if d_abs_diff else None,
            "max_abs_diff": round(float(np.max(d_abs_diff)), 6) if d_abs_diff else None,
            "tost_equivalence": tost,
            "bayesian_rope": rope,
        },
    }

    json_path = os.path.join(output_dir, "statistical_suite_results.json")
    with open(json_path, "w") as f:
        json.dump(stats, f, indent=2, default=str)

    return stats


if __name__ == "__main__":
    import glob
    json_dir = Path(__file__).resolve().parent.parent / "refine-logs"
    result_files = glob.glob(str(json_dir / "*.json"))
    stats = run_statistical_suite(result_files)
    print(json.dumps(stats, indent=2, default=str))
