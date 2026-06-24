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
    # NEW: Network-normalized impact (Ke et al. 2023, PNAS)
    "network_normalized_impact": {
        "label": "Network-Normalized Impact (Ke et al. 2023)",
        "prompt": """Write Python code to compute a network-normalized impact measure for a focal paper.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count, title
- citations CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

Method (from Ke et al. 2023, PNAS):
The normalized impact compares a focal paper's citations against papers cited alongside it.
1. Find all papers that cite the focal paper (paper_id={paper_id})
2. For each citing paper, find ALL other papers it cites (co-cited with focal paper)
3. Compute the MEAN citation_count of those co-cited papers
4. Normalized impact = focal_paper_citation_count / mean_co_cited_citation_count
5. If mean_co_cited is 0, set impact to focal_citation_count

Print: NETWORK_IMPACT = <value>, FOCAL_CITATIONS = <count>, CO_CITED_MEAN = <value>, CO_CITED_COUNT = <count>

Use pandas. Output ONLY Python code.
""",
        "output_patterns": {
            "network_impact": r"NETWORK_IMPACT\s*=\s*([-+]?\d*\.?\d+)",
            "focal_citations": r"FOCAL_CITATIONS\s*=\s*(\d+)",
            "co_cited_mean": r"CO_CITED_MEAN\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers", "paper_citations"],
    },
    # NEW: Disruption temporal trend (Park et al. 2023, Nature)
    "disruption_temporal": {
        "label": "Disruption Temporal Trend (Park et al. 2023)",
        "prompt": """Write Python code to test whether science is becoming less disruptive over time.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
- citations CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

Task: Reproduce Park et al. (2023, Nature) finding:
1. Load papers data
2. Group papers by decade (floor(year/10)*10)
3. Compute MEAN disruption_score for each decade
4. Compute a simple linear trend: Pearson correlation between decade and mean disruption
5. Print results

Print: EARLIEST_DECADE = <year>, EARLIEST_MEAN_D = <value>, LATEST_DECADE = <year>, LATEST_MEAN_D = <value>, TREND_CORRELATION = <value>, N_DECADES = <count>

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "earliest_decade": r"EARLIEST_DECADE\s*=\s*(\d+)",
            "earliest_mean_d": r"EARLIEST_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
            "latest_decade": r"LATEST_DECADE\s*=\s*(\d+)",
            "latest_mean_d": r"LATEST_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
            "trend_correlation": r"TREND_CORRELATION\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers"],
    },
    # NEW: Citation inflation bias (Petersen et al. 2023, arXiv)
    "citation_inflation": {
        "label": "Citation Inflation Bias (Petersen et al. 2023)",
        "prompt": """Write Python code to test whether the disruption index is biased by citation inflation.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count,
  reference_count
- citations CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

Method (from Petersen et al. 2023):
The disruption index is biased by citation inflation — papers with longer reference lists produce
lower D-index values because more references → more overlap → lower D.
1. Load papers data
2. Exclude papers with reference_count < 1
3. Bin papers by reference_count deciles (use pd.qcut with 10 bins, duplicates='drop')
4. Compute MEAN disruption_score for each decile
5. Compute Pearson correlation between reference_count and disruption_score
   Use numpy.corrcoef(x, y)[0, 1]
6. Print results

Print: CORRELATION = <value>, LOWEST_REF_BIN_MEAN_D = <value>, HIGHEST_REF_BIN_MEAN_D = <value>, N_PAPERS = <count>

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "correlation": r"CORRELATION\s*=\s*([-+]?\d*\.?\d+)",
            "lowest_ref_mean_d": r"LOWEST_REF_BIN_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
            "highest_ref_mean_d": r"HIGHEST_REF_BIN_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers"],
    },
    # NEW: Frontier author impact (Sam Arts et al. 2025, Research Policy)
    "frontier_author_impact": {
        "label": "Frontier Author Impact (Arts et al. 2025)",
        "prompt": """Write Python code to test whether "frontier" papers have higher impact.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
{patent_section}
Method (from Arts et al. 2025, Research Policy):
Frontier papers are recent highly-cited papers that shift the knowledge frontier.
1. Load papers data
2. Find the most recent year in the data. Identify papers from the most recent 5 years.
3. Compute the 90th percentile of citation_count among these recent papers — this is the threshold.
4. Define "frontier" papers: ALL papers (any year) with citation_count >= threshold
5. Define "non-frontier" papers: ALL remaining papers (any year) with citation_count < threshold
6. Compute mean citation_count and mean disruption_score for frontier vs non-frontier papers
{patent_steps}
Print: FRONTIER_MEAN_CITATIONS = <value>, NON_FRONTIER_MEAN_CITATIONS = <value>, FRONTIER_MEAN_D = <value>, NON_FRONTIER_MEAN_D = <value>, N_FRONTIER = <count>, N_NON_FRONTIER = <count>{patent_output}

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "frontier_mean_cit": r"FRONTIER_MEAN_CITATIONS\s*=\s*([-+]?\d*\.?\d+)",
            "non_frontier_mean_cit": r"NON_FRONTIER_MEAN_CITATIONS\s*=\s*([-+]?\d*\.?\d+)",
            "frontier_mean_d": r"FRONTIER_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
            "non_frontier_mean_d": r"NON_FRONTIER_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers"],
    },
    # ── New metric (2026-06-06): Sleeping Beauty coefficient B ──
    "sleeping_beauty": {
        "label": "Sleeping Beauty Coefficient B (Ke et al. 2015)",
        "prompt": """Write Python code to compute the Sleeping Beauty coefficient B for a given paper.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
- citations CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

Method (from Ke et al. 2015, PNAS):
The beauty coefficient B measures delayed recognition — how much a paper's citation trajectory
lags behind a linear growth reference line.

1. Find the focal paper (paper_id={paper_id}) and get its publication year y0
2. Find ALL papers that cite the focal paper using the citations CSV
3. Join with papers CSV to get each citing paper's publication year
4. Compute c_t = count of citations received in year t (t = citing_year - y0, the age)
5. Find t_m = age at which maximum yearly citations c_tm occurs
6. If t_m == 0: B = 0 (no delayed recognition)
7. Reference line: L_t = c_0 + (c_tm - c_0) * t / t_m   for t in [0, t_m]
8. B = sum over t=0 to t_m of (L_t - c_t) / max(1, c_t)
9. Also compute awakening time t_a = argmax over t of distance from (t, c_t) to line L_t

Print: FOCAL_YEAR = <y0>, PEAK_AGE = <tm>, PEAK_CITATIONS = <ctm>, B_COEFFICIENT = <B>, AWAKENING_AGE = <ta>

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "focal_year": r"FOCAL_YEAR\s*=\s*(\d+)",
            "peak_age": r"PEAK_AGE\s*=\s*(\d+)",
            "peak_citations": r"PEAK_CITATIONS\s*=\s*(\d+)",
            "B_coefficient": r"B_COEFFICIENT\s*=\s*([-+]?\d*\.?\d+)",
            "awakening_age": r"AWAKENING_AGE\s*=\s*(\d+)",
        },
        "requires_tables": ["papers", "paper_citations"],
    },
    # ── New metric (2026-06-06): Career Ranking Mobility D ──
    "career_mobility": {
        "label": "Career Ranking Mobility D (Sun et al. 2023)",
        "prompt": """Write Python code to compute the ranking mobility coefficient D for scientific papers.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count

Method (from Sun et al. 2023, PNAS, adapted for paper-level analysis):
The mobility coefficient D measures how much paper impact rankings change between time periods.

1. Load papers data
2. Compute base_year = {paper_id} % 30 + 1990
3. Filter to papers in year range [base_year, base_year+10]
4. Split into early period [base_year, base_year+5) and late period [base_year+5, base_year+10)
5. Rank papers in each period into 10 deciles by citation_count
   Use: pd.qcut(df["citation_count"].rank(method="first"), 10, labels=False)
6. Build 10x10 transition matrix P where P[i][j] = fraction of papers in early decile j
   whose citation_count falls into late decile i (use late period decile thresholds)
   Late thresholds = [late["citation_count"].quantile(k/10) for k in 1..9]
7. Random walk model: P_model(i|j) ∝ D^|i-j|, normalize each column to sum to 1
8. Find optimal D in [0.01, 0.99] by minimizing Frobenius norm ||P_data - P_model(D)||
9. Compute Top stability: average diagonal probability for top 2 deciles (indices 8,9)
10. Compute Gini coefficient of citation distribution in early period

Print: OPTIMAL_D = <D>, TOP_STABILITY = <stability>, GINI_COEFFICIENT = <gini>, N_PAPERS = <n>

Use numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "optimal_D": r"OPTIMAL_D\s*=\s*([-+]?\d*\.?\d+)",
            "top_stability": r"TOP_STABILITY\s*=\s*([-+]?\d*\.?\d+)",
            "gini_coefficient": r"GINI_COEFFICIENT\s*=\s*([-+]?\d*\.?\d+)",
            "n_papers": r"N_PAPERS\s*=\s*(\d+)",
        },
        "requires_tables": ["papers"],
    },
    # ── New metric (2026-06-06): Novelty-Conventionality ──
    "novelty_conventionality": {
        "label": "Novelty-Conventionality Analysis (Uzzi et al. 2013)",
        "prompt": """Write Python code to analyze the relationship between novelty, conventionality, and scientific impact.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score,
  author_count, novelty_score, conventionality_score

Method (from Uzzi et al. 2013, Science):
Novelty measures atypical combinations of prior knowledge. Conventionality measures how
typical/embedded the combinations are within existing knowledge structures.

1. Load papers data
2. Drop rows where novelty_score or conventionality_score is NaN
3. Compute Pearson correlation between novelty_score and citation_count
4. Compute Pearson correlation between conventionality_score and citation_count
5. Compute Pearson correlation between novelty_score and disruption_score
6. Split papers into "high novelty" (top 25%) and "low novelty" (bottom 75%)
7. Compare mean citation_count between high and low novelty groups

Print: NOVELTY_CIT_CORR = <r>, CONV_CIT_CORR = <r>, NOVELTY_DISRUPTION_CORR = <r>, HIGH_NOVELTY_MEAN_CIT = <value>, LOW_NOVELTY_MEAN_CIT = <value>

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "novelty_cit_corr": r"NOVELTY_CIT_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "conv_cit_corr": r"CONV_CIT_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "novelty_disruption_corr": r"NOVELTY_DISRUPTION_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "high_novelty_mean": r"HIGH_NOVELTY_MEAN_CIT\s*=\s*([-+]?\d*\.?\d+)",
            "low_novelty_mean": r"LOW_NOVELTY_MEAN_CIT\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers"],
    },
    # ── New metric (2026-06-06): Interdisciplinarity ──
    "interdisciplinarity": {
        "label": "Interdisciplinarity Index (various)",
        "prompt": """Write Python code to measure interdisciplinarity and its relationship to impact.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score,
  author_count
- paper_fields CSV at '{paper_fields_path}': columns paper_id, field_id

Method:
Interdisciplinarity measures the diversity of fields a paper spans.

1. Load papers and paper_fields data
2. For each paper, count the number of distinct fields (field_id)
3. Merge field counts back to papers data
4. Compute Pearson correlation between n_fields and citation_count
5. Compute Pearson correlation between n_fields and disruption_score
6. Split papers: "multidisciplinary" (n_fields >= 3) vs "specialized" (n_fields == 1)
7. Compare mean disruption_score between groups

Print: N_FIELDS_CIT_CORR = <r>, N_FIELDS_DISRUPTION_CORR = <r>, MULTI_MEAN_D = <value>, SPECIALIZED_MEAN_D = <value>, N_MULTI = <count>, N_SPECIALIZED = <count>

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "n_fields_cit_corr": r"N_FIELDS_CIT_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "n_fields_disruption_corr": r"N_FIELDS_DISRUPTION_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "multi_mean_d": r"MULTI_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
            "specialized_mean_d": r"SPECIALIZED_MEAN_D\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers", "paper_fields"],
    },
    # ── New metric (2026-06-06): Altmetrics ──
    "altmetrics": {
        "label": "Altmetrics Analysis (Twitter/X attention)",
        "prompt": """Write Python code to analyze the relationship between social media attention and citations.

Data:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score,
  author_count
- paper_twitter CSV at '{paper_twitter_path}': columns paper_id, tweet_id

Method:
Altmetrics measure scholarly impact through social media and other non-traditional channels.

1. Load papers and paper_twitter data
2. Count tweets per paper (group by paper_id, count tweet_id)
3. Merge tweet counts back to papers data (0 for papers with no tweets)
4. Compute Pearson correlation between tweet_count and citation_count
5. Compute Pearson correlation between tweet_count and disruption_score
6. Split papers: "tweeted" (tweet_count > 0) vs "untweeted" (tweet_count == 0)
7. Compare mean citation_count between tweeted and untweeted papers

Print: TWEET_CIT_CORR = <r>, TWEET_DISRUPTION_CORR = <r>, TWEETED_MEAN_CIT = <value>, UNTWEETED_MEAN_CIT = <value>, N_TWEETED = <count>, N_UNTWEETED = <count>

Use pandas and numpy. Output ONLY Python code.
""",
        "output_patterns": {
            "tweet_cit_corr": r"TWEET_CIT_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "tweet_disruption_corr": r"TWEET_DISRUPTION_CORR\s*=\s*([-+]?\d*\.?\d+)",
            "tweeted_mean_cit": r"TWEETED_MEAN_CIT\s*=\s*([-+]?\d*\.?\d+)",
            "untweeted_mean_cit": r"UNTWEETED_MEAN_CIT\s*=\s*([-+]?\d*\.?\d+)",
        },
        "requires_tables": ["papers", "paper_twitter"],
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

    elif metric_type == "network_normalized_impact":
        row = papers[papers["paper_id"] == paper_id]
        if len(row) == 0:
            return {}
        focal_cit = int(row["citation_count"].values[0])
        citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
        if len(citers) == 0:
            return {}
        co_cited = pc[pc["citing_paper_id"].isin(citers)]["cited_paper_id"].unique()
        co_cited = co_cited[co_cited != paper_id]
        if len(co_cited) == 0:
            return {"network_impact": float(focal_cit), "focal_citations": focal_cit,
                    "co_cited_mean": 0.0}
        co_rows = papers[papers["paper_id"].isin(co_cited)]
        mean_co = float(co_rows["citation_count"].mean()) if len(co_rows) > 0 else 0.0
        impact = focal_cit / mean_co if mean_co > 0 else float(focal_cit)
        return {
            "network_impact": round(impact, 4),
            "focal_citations": focal_cit,
            "co_cited_mean": round(mean_co, 2),
        }

    elif metric_type == "disruption_temporal":
        df = papers.dropna(subset=["year", "disruption_score"]).copy()
        df["decade"] = (df["year"] // 10) * 10
        decades = df.groupby("decade")["disruption_score"].mean()
        if len(decades) < 2:
            return {}
        earliest = decades.index.min()
        latest = decades.index.max()
        try:
            from scipy.stats import pearsonr
            r, _ = pearsonr(decades.index.values.astype(float), decades.values)
        except ImportError:
            r = np.corrcoef(decades.index.values.astype(float), decades.values)[0, 1]
        return {
            "earliest_decade": int(earliest),
            "earliest_mean_d": round(float(decades[earliest]), 6),
            "latest_decade": int(latest),
            "latest_mean_d": round(float(decades[latest]), 6),
            "trend_correlation": round(float(r), 6),
        }

    elif metric_type == "citation_inflation":
        df = papers.dropna(subset=["reference_count", "disruption_score"]).copy()
        df = df[df["reference_count"] >= 1]
        if len(df) < 10:
            return {}
        try:
            df["ref_decile"] = pd.qcut(df["reference_count"], 10, labels=False,
                                       duplicates="drop")
        except ValueError:
            return {}
        decile_means = df.groupby("ref_decile")["disruption_score"].mean()
        try:
            from scipy.stats import pearsonr
            r, _ = pearsonr(df["reference_count"].values.astype(float),
                           df["disruption_score"].values.astype(float))
        except ImportError:
            r = np.corrcoef(df["reference_count"], df["disruption_score"])[0, 1]
        return {
            "correlation": round(float(r), 6),
            "lowest_ref_mean_d": round(float(decile_means.iloc[0]), 6),
            "highest_ref_mean_d": round(float(decile_means.iloc[-1]), 6),
        }

    elif metric_type == "frontier_author_impact":
        df = papers.dropna(subset=["year", "citation_count", "disruption_score"]).copy()
        recent_year = int(df["year"].max()) - 5
        recent = df[df["year"] >= recent_year]
        if len(recent) < 10:
            return {}
        threshold = recent["citation_count"].quantile(0.90)
        frontier = df[df["citation_count"] >= threshold]
        non_frontier = df[df["citation_count"] < threshold]
        return {
            "frontier_mean_cit": round(float(frontier["citation_count"].mean()), 2),
            "non_frontier_mean_cit": round(float(non_frontier["citation_count"].mean()), 2),
            "frontier_mean_d": round(float(frontier["disruption_score"].mean()), 6),
            "non_frontier_mean_d": round(float(non_frontier["disruption_score"].mean()), 6),
        }

    elif metric_type == "sleeping_beauty":
        focal = papers[papers["paper_id"] == paper_id]
        if len(focal) == 0:
            return {}
        y0 = int(focal["year"].values[0])

        citing = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
        if len(citing) == 0:
            return {"focal_year": y0, "peak_age": 0, "peak_citations": 0,
                    "B_coefficient": 0.0, "awakening_age": 0}

        citing_papers = papers[papers["paper_id"].isin(citing)].copy()
        if len(citing_papers) == 0:
            return {"focal_year": y0, "peak_age": 0, "peak_citations": 0,
                    "B_coefficient": 0.0, "awakening_age": 0}

        citing_papers["age"] = citing_papers["year"].values - y0
        citing_papers = citing_papers[citing_papers["age"] >= 0]
        if len(citing_papers) == 0:
            return {"focal_year": y0, "peak_age": 0, "peak_citations": 0,
                    "B_coefficient": 0.0, "awakening_age": 0}

        age_counts = citing_papers.groupby("age").size()
        max_age = int(age_counts.index.max())
        c_t = np.zeros(max_age + 1)
        for age, count in age_counts.items():
            c_t[int(age)] = count

        t_m = int(np.argmax(c_t))
        c_tm = float(c_t[t_m])
        c_0 = float(c_t[0])

        if t_m == 0:
            return {"focal_year": y0, "peak_age": 0, "peak_citations": c_tm,
                    "B_coefficient": 0.0, "awakening_age": 0}

        t_vals = np.arange(t_m + 1, dtype=float)
        L_t = c_0 + (c_tm - c_0) * t_vals / t_m

        B = float(np.sum((L_t - c_t[:t_m + 1]) / np.maximum(1, c_t[:t_m + 1])))

        # Awakening time: max perpendicular distance to reference line
        v_norm_sq = float(t_m)**2 + (c_tm - c_0)**2
        if v_norm_sq > 0:
            distances = np.array([
                abs(t_m * (c_t[i] - c_0) - i * (c_tm - c_0)) / np.sqrt(v_norm_sq)
                for i in range(t_m + 1)
            ])
            t_a = int(np.argmax(distances))
        else:
            t_a = 0

        return {
            "focal_year": y0,
            "peak_age": t_m,
            "peak_citations": c_tm,
            "B_coefficient": round(B, 4),
            "awakening_age": t_a,
        }

    elif metric_type == "career_mobility":
        base_year = 1990 + (paper_id % 30)
        window = papers[
            (papers["year"] >= base_year) & (papers["year"] < base_year + 10)
        ].copy()
        if len(window) < 50:
            return {}

        early = window[window["year"] < base_year + 5].copy()
        late = window[window["year"] >= base_year + 5].copy()
        if len(early) < 20 or len(late) < 20:
            return {}

        early["decile"] = pd.qcut(
            early["citation_count"].rank(method="first"), 10, labels=False
        )
        late["decile"] = pd.qcut(
            late["citation_count"].rank(method="first"), 10, labels=False
        )

        late_thresholds = [
            float(late["citation_count"].quantile(k / 10)) for k in range(1, 10)
        ]

        trans = np.zeros((10, 10))
        for j in range(10):
            early_j = early[early["decile"] == j]
            n_j = len(early_j)
            if n_j == 0:
                continue
            cit = early_j["citation_count"].values
            for i in range(10):
                if i == 0:
                    count = (cit < late_thresholds[0]).sum()
                elif i == 9:
                    count = (cit >= late_thresholds[8]).sum()
                else:
                    count = ((cit >= late_thresholds[i - 1]) &
                             (cit < late_thresholds[i])).sum()
                trans[i, j] = count / n_j

        best_d, best_err = 0.5, float("inf")
        for d in np.linspace(0.01, 0.99, 99):
            model = np.zeros((10, 10))
            for j in range(10):
                col = np.array([d ** abs(i - j) for i in range(10)], dtype=float)
                col_sum = col.sum()
                if col_sum > 0:
                    model[:, j] = col / col_sum
            err = np.linalg.norm(trans - model, "fro")
            if err < best_err:
                best_err = err
                best_d = d

        cit_sorted = np.sort(early["citation_count"].values.astype(float))
        n = len(cit_sorted)
        if n > 0 and cit_sorted.sum() > 0:
            gini = float(
                (2 * np.sum(np.arange(1, n + 1) * cit_sorted) -
                 (n + 1) * cit_sorted.sum()) / (n * cit_sorted.sum())
            )
        else:
            gini = 0.0

        top_stability = float((trans[8, 8] + trans[9, 9]) / 2.0)

        return {
            "optimal_D": round(best_d, 4),
            "top_stability": round(top_stability, 4),
            "gini_coefficient": round(gini, 4),
            "n_papers": len(window),
        }

    elif metric_type == "novelty_conventionality":
        df = papers.dropna(
            subset=["novelty_score", "conventionality_score",
                    "citation_count", "disruption_score"]
        ).copy()
        if len(df) < 50:
            return {}
        r_nov_cit = float(np.corrcoef(df["novelty_score"], df["citation_count"])[0, 1])
        r_conv_cit = float(np.corrcoef(df["conventionality_score"], df["citation_count"])[0, 1])
        r_nov_d = float(np.corrcoef(df["novelty_score"], df["disruption_score"])[0, 1])
        threshold = df["novelty_score"].quantile(0.75)
        high = df[df["novelty_score"] >= threshold]
        low = df[df["novelty_score"] < threshold]
        return {
            "novelty_cit_corr": round(r_nov_cit, 6),
            "conv_cit_corr": round(r_conv_cit, 6),
            "novelty_disruption_corr": round(r_nov_d, 6),
            "high_novelty_mean": round(float(high["citation_count"].mean()), 2),
            "low_novelty_mean": round(float(low["citation_count"].mean()), 2),
        }

    elif metric_type == "interdisciplinarity":
        # Load paper_fields lazily
        try:
            from src.sciscigpt_local.sciscinet_connector import load_table
            pf = load_table("paper_fields")
        except Exception:
            return {}

        # Count fields per paper
        field_counts = pf.groupby("paper_id")["field_id"].nunique()
        df = papers[["paper_id", "citation_count", "disruption_score"]].copy()
        df["n_fields"] = df["paper_id"].map(field_counts).fillna(0).astype(int)
        df = df.dropna()

        if len(df) < 50:
            return {}

        r_fields_cit = float(np.corrcoef(df["n_fields"], df["citation_count"])[0, 1])
        r_fields_d = float(np.corrcoef(df["n_fields"], df["disruption_score"])[0, 1])
        multi = df[df["n_fields"] >= 3]
        specialized = df[df["n_fields"] == 1]
        return {
            "n_fields_cit_corr": round(r_fields_cit, 6),
            "n_fields_disruption_corr": round(r_fields_d, 6),
            "multi_mean_d": round(float(multi["disruption_score"].mean()), 6) if len(multi) > 0 else 0.0,
            "specialized_mean_d": round(float(specialized["disruption_score"].mean()), 6) if len(specialized) > 0 else 0.0,
        }

    elif metric_type == "altmetrics":
        try:
            from src.sciscigpt_local.sciscinet_connector import load_table
            pt = load_table("paper_twitter")
        except Exception:
            return {}

        tweet_counts = pt.groupby("paper_id").size()
        df = papers[["paper_id", "citation_count", "disruption_score"]].copy()
        df["tweet_count"] = df["paper_id"].map(tweet_counts).fillna(0).astype(int)
        df = df.dropna()

        if len(df) < 50:
            return {}

        r_tweet_cit = float(np.corrcoef(df["tweet_count"], df["citation_count"])[0, 1])
        r_tweet_d = float(np.corrcoef(df["tweet_count"], df["disruption_score"])[0, 1])
        tweeted = df[df["tweet_count"] > 0]
        untweeted = df[df["tweet_count"] == 0]
        return {
            "tweet_cit_corr": round(r_tweet_cit, 6),
            "tweet_disruption_corr": round(r_tweet_d, 6),
            "tweeted_mean_cit": round(float(tweeted["citation_count"].mean()), 2) if len(tweeted) > 0 else 0.0,
            "untweeted_mean_cit": round(float(untweeted["citation_count"].mean()), 2) if len(untweeted) > 0 else 0.0,
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
        "network_normalized_impact": "network_impact",
        "disruption_temporal": "trend_correlation",
        "citation_inflation": "correlation",
        "frontier_author_impact": "frontier_mean_cit",
        "sleeping_beauty": "B_coefficient",
        "career_mobility": "optimal_D",
        "novelty_conventionality": "novelty_cit_corr",
        "interdisciplinarity": "n_fields_cit_corr",
        "altmetrics": "tweet_cit_corr",
    }
    return primary.get(metric_type, "D_index")


def get_required_tables(metric_type: str) -> list[str]:
    """Get which SciSciNet tables are needed for a metric type."""
    config = METRIC_CONFIGS.get(metric_type, {})
    return config.get("requires_tables", ["paper_citations"])
