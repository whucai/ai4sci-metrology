"""Metric templates for multi-metric reproduction benchmark.

Each metric type has:
  - A code-generation prompt template
  - A ground truth computation function
  - An output parser

Supported metrics:
  - disruption: D-index from citation subgraph
  - citation_count_prediction: predict citation count from paper metadata
  - team_size_effect: small vs large team disruption difference
"""

from __future__ import annotations

import re
from typing import Any

import numpy as np
import pandas as pd


# ── Prompt templates ──

DISRUPTION_PROMPT = """Write Python code to compute the Disruption Index D for paper {paper_id}.

Data files:
- refs CSV at '{refs_path}': columns reference_id — papers cited BY paper {paper_id}
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

CRITICAL: The cites CSV contains all citation edges FROM papers that cite paper {paper_id}.
Every unique citing_paper_id in this file is a paper that cites paper {paper_id}.
For each citing paper, the CSV lists ALL papers it cites (not just paper {paper_id}).

Formula: D = (n_i - n_j) / (n_i + n_j)
- n_i = citing papers that cite paper {paper_id} but NOT its references
- n_j = citing papers that cite BOTH paper {paper_id} AND at least one of its references

Algorithm:
1. Read refs CSV → set R (paper {paper_id}'s references)
2. Read cites CSV → group by citing_paper_id, collect each citer's cited papers
3. For each citing paper, check if its cited papers overlap with R
4. n_i = citing papers with NO overlap with R
5. n_j = citing papers WITH overlap with R
6. D = (n_i - n_j) / (n_i + n_j)

Use pandas. Print: D_INDEX = <value>, n_i = <value>, n_j = <value>
Output ONLY Python code."""


CITATION_PREDICTION_PROMPT = """Write Python code to predict citation count for a focal paper.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
- The focal paper has paper_id = {paper_id}

Task:
1. Load the papers CSV
2. Find papers from the SAME YEAR as the focal paper
3. Compute the mean and median citation_count for same-year papers
4. Print: CITATION_COUNT_PREDICTED = <mean_value>, MEDIAN = <median_value>, SAME_YEAR_COUNT = <count>

This is a simple baseline: predict a paper's citation count as the average of its cohort.

Use pandas. Output ONLY Python code."""


TEAM_SIZE_PROMPT = """Write Python code to test whether small teams produce more disruptive science.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count

Task:
1. Load the papers CSV
2. Split into small teams (author_count <= 3) and large teams (author_count > 3)
3. Compute mean disruption_score for each group
4. Print: SMALL_MEAN = <value>, LARGE_MEAN = <value>, DIFFERENCE = <small_mean - large_mean>, N_SMALL = <count>, N_LARGE = <count>

Use pandas. Output ONLY Python code."""


METRIC_CONFIGS: dict[str, dict[str, Any]] = {
    "disruption": {
        "label": "Disruption Index (D)",
        "prompt": DISRUPTION_PROMPT,
        "output_patterns": {
            "D_index": [
                r"D_INDEX\s*[=:]\s*([-+]?\d*\.?\d+)",
                r"(?:Disruption\s*)?D(?:isruption)?\s*(?:Index)?\s*(?:\(D\))?\s*[=:]\s*([-+]?\d*\.?\d+)",
            ],
            "n_i": [r"n_i\s*[=:]\s*(\d+)"],
            "n_j": [r"n_j\s*[=:]\s*(\d+)"],
        },
        "requires_tables": ["paper_citations"],
    },
    "citation_count_prediction": {
        "label": "Citation Count Prediction",
        "prompt": CITATION_PREDICTION_PROMPT,
        "output_patterns": {
            "citation_count": r"CITATION_COUNT_PREDICTED\s*=\s*([-+]?\d*\.?\d+)",
            "median": r"MEDIAN\s*=\s*([-+]?\d*\.?\d+)",
            "same_year_count": r"SAME_YEAR_COUNT\s*=\s*(\d+)",
        },
        "requires_tables": ["papers"],
    },
    "team_size_effect": {
        "label": "Team Size Effect (Wu et al. 2019)",
        "prompt": TEAM_SIZE_PROMPT,
        "output_patterns": {
            "small_mean": r"SMALL_MEAN\s*=\s*([-+]?\d*\.?\d+)",
            "large_mean": r"LARGE_MEAN\s*=\s*([-+]?\d*\.?\d+)",
            "difference": r"DIFFERENCE\s*=\s*([-+]?\d*\.?\d+)",
            "n_small": r"N_SMALL\s*=\s*(\d+)",
            "n_large": r"N_LARGE\s*=\s*(\d+)",
        },
        "requires_tables": ["papers"],
    },
}


def get_prompt(metric_type: str, **kwargs: Any) -> str:
    """Get the code-generation prompt for a metric type.

    Args:
        metric_type: One of 'disruption', 'citation_count_prediction', 'team_size_effect'.
        **kwargs: Template variables (refs_path, cites_path, papers_path, paper_id).

    Returns:
        Formatted prompt string.
    """
    config = METRIC_CONFIGS.get(metric_type)
    if config is None:
        raise ValueError(f"Unknown metric type: {metric_type}. "
                         f"Choose from: {list(METRIC_CONFIGS.keys())}")
    return config["prompt"].format(**kwargs)


def parse_metric_output(stdout: str, metric_type: str) -> dict[str, float]:
    """Parse metric values from sandbox stdout.

    Args:
        stdout: Captured stdout from sandbox execution.
        metric_type: Which metric type to parse.

    Returns:
        Dict of {metric_name: float_value} for all matched patterns.
    """
    config = METRIC_CONFIGS.get(metric_type)
    if config is None:
        return {}

    result = {}
    for key, pats in config["output_patterns"].items():
        if isinstance(pats, str):
            pats = [pats]
        for pat in pats:
            m = re.search(pat, stdout, re.IGNORECASE)
            if m:
                try:
                    result[key] = float(m.group(1))
                except ValueError:
                    pass
                break  # first match wins
    return result


def compute_ground_truth(
    metric_type: str,
    paper_id: int,
    papers: pd.DataFrame,
    pc: pd.DataFrame,
) -> dict[str, float]:
    """Compute ground truth for comparison.

    Args:
        metric_type: Which metric to compute ground truth for.
        paper_id: Focal paper ID.
        papers: SciSciNet papers DataFrame.
        pc: SciSciNet paper_citations DataFrame.

    Returns:
        Dict of {metric_name: ground_truth_value}.
    """
    if metric_type == "disruption":
        refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
        citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
        if len(refs) == 0 or len(citers) == 0:
            return {}
        ref_set = set(refs)
        n_i, n_j = 0, 0
        for cid in citers:
            citer_refs = set(pc[pc["citing_paper_id"] == cid]["cited_paper_id"].values)
            if citer_refs & ref_set:
                n_j += 1
            else:
                n_i += 1
        denom = n_i + n_j
        D = (n_i - n_j) / denom if denom > 0 else 0.0
        return {"D_index": round(D, 6), "n_i": n_i, "n_j": n_j}

    elif metric_type == "citation_count_prediction":
        row = papers[papers["paper_id"] == paper_id]
        if len(row) == 0:
            return {}
        year = row["year"].values[0]
        same_year = papers[papers["year"] == year]
        if len(same_year) == 0:
            return {}
        return {
            "citation_count": round(float(same_year["citation_count"].mean()), 2),
            "median": round(float(same_year["citation_count"].median()), 2),
            "same_year_count": len(same_year),
        }

    elif metric_type == "team_size_effect":
        if "author_count" not in papers.columns:
            return {}
        small = papers[papers["author_count"] <= 3]["disruption_score"]
        large = papers[papers["author_count"] > 3]["disruption_score"]
        small_mean = float(small.mean()) if len(small) > 0 else 0.0
        large_mean = float(large.mean()) if len(large) > 0 else 0.0
        return {
            "small_mean": round(small_mean, 6),
            "large_mean": round(large_mean, 6),
            "difference": round(small_mean - large_mean, 6),
            "n_small": len(small),
            "n_large": len(large),
        }

    return {}


def get_primary_metric(metric_type: str) -> str:
    """Get the primary metric name for a given metric type.

    This is the key used for correctness comparison.
    """
    primary = {
        "disruption": "D_index",
        "citation_count_prediction": "citation_count",
        "team_size_effect": "difference",
    }
    return primary.get(metric_type, "D_index")


def get_required_tables(metric_type: str) -> list[str]:
    """Get which SciSciNet tables are needed for a metric type."""
    config = METRIC_CONFIGS.get(metric_type, {})
    return config.get("requires_tables", ["paper_citations"])
