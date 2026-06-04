"""SciSciNet local data connector.

Loads SciSciNet parquet files (from HuggingFace: cssi/SciSciGPT-SciSciNet)
and provides efficient local query functions for SciSci analysis.

SciSciNet tables (19 total):
  - papers (22 shards): paper_id, doi, year, author_count, citation_count,
    disruption_score, novelty_score, conventionality_score, title, abstract, ...
  - paper_citations: citing_paper_id → cited_paper_id (78M rows)
  - authors: author_id, author_name, author_gender (8.1M rows)
  - paper_author_affiliations: paper_id → author_id
  - paper_fields: paper_id → field_id
  - fields: field_id, field_name, field_level
  - institutions: institution details
  - patents, twitter, nct, newsfeed, nih, nsf + paper_* link tables

Dependencies: pyarrow, pandas, huggingface_hub
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Optional

import pandas as pd
import pyarrow.parquet as pq
from huggingface_hub import hf_hub_download

# Cache directory for downloaded parquet files
# Default: project-local data/sciscinet/, fallback to ~/.cache/sciscinet/
_PROJECT_DATA = Path(__file__).resolve().parent.parent.parent / "data" / "sciscinet"
_DEFAULT_CACHE = _PROJECT_DATA if _PROJECT_DATA.exists() else Path.home() / ".cache/sciscinet"
CACHE_DIR = Path(os.environ.get("SCISCINET_CACHE", str(_DEFAULT_CACHE)))
REPO_ID = "cssi/SciSciGPT-SciSciNet"

# Track what's been downloaded
_loaded: dict[str, pd.DataFrame] = {}


def _download(table_name: str) -> Path:
    """Download a SciSciNet parquet file and return local path."""
    CACHE_DIR.mkdir(parents=True, exist_ok=True)
    return Path(hf_hub_download(
        repo_id=REPO_ID,
        filename=table_name + ".parquet",
        repo_type="dataset",
        cache_dir=str(CACHE_DIR),
    ))


def load_table(table_name: str, force: bool = False) -> pd.DataFrame:
    """Load a SciSciNet table as a pandas DataFrame.

    Args:
        table_name: One of: papers (loads first shard), paper_citations,
                    authors, fields, paper_fields, paper_author_affiliations, ...
        force: If True, re-download even if already loaded.

    Returns:
        pandas DataFrame
    """
    if table_name in _loaded and not force:
        return _loaded[table_name]

    if table_name == "papers":
        # Load first shard
        path = _download("papers/shard_00")
    else:
        path = _download(table_name)

    table = pq.read_table(path)
    df = table.to_pandas()
    _loaded[table_name] = df
    return df


def load_papers_sample(n_shards: int = 1) -> pd.DataFrame:
    """Load a sample of papers from SciSciNet.

    Each shard has ~110K papers. Total: 22 shards ≈ 2.4M papers.

    Args:
        n_shards: Number of paper shards to load (1 = ~110K papers).
    """
    dfs = []
    for i in range(min(n_shards, 22)):
        shard_name = f"papers/shard_{i:02d}"
        path = _download(shard_name)
        table = pq.read_table(path)
        dfs.append(table.to_pandas())

    df = pd.concat(dfs, ignore_index=True)
    _loaded["papers"] = df
    return df


def get_disruption_by_team_size(papers: pd.DataFrame) -> dict:
    """Reproduce Wu et al. (2019) finding: compare disruption index by team size.

    Uses SciSciNet's pre-computed disruption_score and author_count columns.

    Returns:
        dict with:
          - small_team_mean: mean D-index for 1-3 authors
          - large_team_mean: mean D-index for 4+ authors
          - small_team_std, large_team_std
          - small_team_count, large_team_count
          - mannwhitney_p: p-value from Mann-Whitney U test
    """
    from scipy.stats import mannwhitneyu

    df = papers.dropna(subset=["disruption_score", "author_count"]).copy()

    small = df[df["author_count"] <= 3]["disruption_score"]
    large = df[df["author_count"] >= 4]["disruption_score"]

    if len(small) == 0 or len(large) == 0:
        return {"error": "Insufficient data for comparison"}

    # Mann-Whitney U test
    try:
        stat, p_value = mannwhitneyu(small, large, alternative="two-sided")
    except Exception:
        stat, p_value = 0.0, 1.0

    return {
        "small_team_mean": round(small.mean(), 5),
        "large_team_mean": round(large.mean(), 5),
        "small_team_std": round(small.std(), 5),
        "large_team_std": round(large.std(), 5),
        "small_team_count": len(small),
        "large_team_count": len(large),
        "difference": round(small.mean() - large.mean(), 5),
        "mannwhitney_u_stat": round(stat, 2),
        "mannwhitney_p": p_value,
        "significant": p_value < 0.001,
    }


def get_citation_network_stats(paper_citations: pd.DataFrame) -> dict:
    """Compute basic citation network statistics.

    Args:
        paper_citations: The paper_citations table (citing_paper_id → cited_paper_id).

    Returns:
        dict with in_degree distribution, out_degree distribution, basic stats.
    """
    in_deg = paper_citations.groupby("cited_paper_id").size()
    out_deg = paper_citations.groupby("citing_paper_id").size()

    return {
        "total_citations": len(paper_citations),
        "unique_cited": len(in_deg),
        "unique_citing": len(out_deg),
        "mean_in_degree": round(in_deg.mean(), 2),
        "mean_out_degree": round(out_deg.mean(), 2),
        "median_in_degree": round(in_deg.median(), 1),
        "max_in_degree": int(in_deg.max()),
    }


def get_field_distribution(paper_fields: pd.DataFrame, fields: pd.DataFrame) -> pd.DataFrame:
    """Compute paper distribution across fields.

    Args:
        paper_fields: paper_id → field_id mapping.
        fields: field_id → field_name lookup.

    Returns:
        DataFrame with field_name, paper_count sorted by count desc.
    """
    merged = paper_fields.merge(fields, on="field_id")
    dist = merged.groupby("field_name").size().sort_values(ascending=False)
    return dist.reset_index(name="paper_count")


def download_all_tables() -> dict[str, pd.DataFrame]:
    """Download all SciSciNet tables (excluding full papers).

    Returns a dict of table_name → DataFrame.
    """
    tables = {}
    names = [
        "authors", "fields", "institutions",
        "paper_citations", "paper_fields",
        "paper_author_affiliations",
        "patents", "twitter", "nct", "nih", "nsf", "newsfeed",
        "nct", "newsfeed", "nih", "nsf",
        "paper_nct", "paper_newsfeed", "paper_nih", "paper_nsf",
        "paper_patents", "paper_twitter",
    ]
    for name in names:
        try:
            tables[name] = load_table(name)
            print(f"  Loaded {name}: {len(tables[name])} rows")
        except Exception as e:
            print(f"  Skipped {name}: {e}")

    return tables


def citation_cascade(
    paper_id: int,
    pc: pd.DataFrame,
    depth: int = 2,
    max_per_level: int = 30,
) -> dict:
    """Multi-hop citation cascade analysis using local SciSciNet data.

    Traverses the citation graph forward from a focal paper through
    its citers, then the citers of those citers, etc.

    Args:
        paper_id: Focal paper ID.
        pc: Paper-citations DataFrame (citing_paper_id, cited_paper_id).
        depth: Number of forward-citation levels to traverse.
        max_per_level: Max citers to collect per source paper.

    Returns:
        dict with focal, levels [{depth, count, paper_ids}], cascade stats.
    """
    result: dict = {
        "focal_paper_id": int(paper_id),
        "depth": depth,
        "levels": [],
    }

    current_ids = {int(paper_id)}
    for level in range(1, depth + 1):
        level_papers: list[int] = []
        next_ids: set[int] = set()

        for pid in list(current_ids)[:5]:
            citers = pc[pc["cited_paper_id"] == pid]["citing_paper_id"].values
            for cid in citers[:max_per_level]:
                cid_int = int(cid)
                level_papers.append(cid_int)
                next_ids.add(cid_int)

        result["levels"].append({
            "depth": level,
            "count": len(level_papers),
            "paper_ids": level_papers[:100],
        })
        current_ids = next_ids
        if not current_ids:
            break

    total = sum(lvl["count"] for lvl in result["levels"])
    result["total_cascade_size"] = total
    result["mean_per_level"] = round(total / depth, 1) if depth > 0 and total > 0 else 0.0
    return result


def field_year_distribution(
    field_id: int,
    paper_fields: pd.DataFrame,
    papers: pd.DataFrame,
    year_range: tuple = (1950, 2020),
) -> dict:
    """Get citation and disruption statistics for a field over time.

    Joins paper_fields with papers metadata to produce field×year stats
    useful for trend analysis and field normalization.

    Args:
        field_id: SciSciNet field ID.
        paper_fields: paper_fields DataFrame.
        papers: papers DataFrame with disruption_score, citation_count columns.
        year_range: (min_year, max_year) tuple.

    Returns:
        dict with field_name, years [{year, n_papers, mean_D, mean_citations}].
    """
    pf = paper_fields[paper_fields["field_id"] == field_id].copy()
    pf = pf.merge(papers[["paper_id", "year", "disruption_score", "citation_count"]],
                  on="paper_id", how="inner")
    pf = pf.dropna(subset=["disruption_score"])

    min_yr, max_yr = year_range
    pf = pf[(pf["year"] >= min_yr) & (pf["year"] <= max_yr)]

    years_data = []
    for yr in sorted(pf["year"].dropna().astype(int).unique()):
        yr_data = pf[pf["year"] == yr]
        years_data.append({
            "year": int(yr),
            "n_papers": len(yr_data),
            "mean_D": round(float(yr_data["disruption_score"].mean()), 6),
            "median_D": round(float(yr_data["disruption_score"].median()), 6),
            "mean_citations": round(float(yr_data["citation_count"].mean()), 2),
        })

    return {
        "field_id": field_id,
        "n_total": len(pf),
        "n_years": len(years_data),
        "years": years_data,
    }


def cem_match(
    treatment_ids: list[int],
    control_pool: pd.DataFrame,
    papers: pd.DataFrame,
    on: list[str] = ("year", "citation_count"),
    bins: dict | None = None,
    k: int = 1,
) -> dict:
    """Coarsened Exact Matching — match treatment papers to controls on coarsened covariates.

    Typical use: match a set of "disrupted" papers to "non-disrupted" controls
    on year and citation count strata, so that D-index comparisons control for
    field-level confounds.

    Args:
        treatment_ids: Paper IDs of the treatment group.
        control_pool: DataFrame with at least paper_id + columns in `on`.
        papers: Full papers table (must have paper_id + columns in `on`).
        on: Columns to match on (default: year, citation_count).
        bins: Dict mapping column → number of bins (default: year=10, citation_count=5).
        k: Number of matched controls per treatment (default 1).

    Returns:
        dict with matched_pairs, balance_table, n_treatment, n_matched.
    """
    if bins is None:
        bins = {"year": 10, "citation_count": 5}

    # Build treatment dataframe
    treatment = papers[papers["paper_id"].isin(treatment_ids)].copy()
    if len(treatment) == 0:
        return {"matched_pairs": [], "balance_table": {}, "n_treatment": 0, "n_matched": 0}

    # Build control dataframe
    control_ids = set(control_pool["paper_id"].values) - set(treatment_ids)
    control = papers[papers["paper_id"].isin(control_ids)].copy()

    # Coarsen matching variables
    for col in on:
        if col not in treatment.columns or col not in control.columns:
            continue
        n_bins = bins.get(col, 5)
        col_min = min(treatment[col].min(), control[col].min())
        col_max = max(treatment[col].max(), control[col].max())

        if col_min == col_max:
            # All same value — skip binning
            treatment[f"{col}_stratum"] = 0
            control[f"{col}_stratum"] = 0
        else:
            treatment[f"{col}_stratum"] = pd.cut(
                treatment[col], bins=n_bins, labels=False,
            )
            control[f"{col}_stratum"] = pd.cut(
                control[col], bins=n_bins, labels=False,
            )

    # Build strata key
    stratum_cols = [f"{c}_stratum" for c in on if f"{c}_stratum" in treatment.columns]
    if not stratum_cols:
        return {"matched_pairs": [], "balance_table": {}, "n_treatment": len(treatment), "n_matched": 0}

    treatment["_stratum"] = treatment[stratum_cols].astype(str).agg("-".join, axis=1)
    control["_stratum"] = control[stratum_cols].astype(str).agg("-".join, axis=1)

    # Match: for each treatment, find k controls in the same stratum
    matched_pairs = []
    control_used = set()

    for _, t_row in treatment.iterrows():
        stratum = t_row["_stratum"]
        candidates = control[
            (control["_stratum"] == stratum) & (~control["paper_id"].isin(control_used))
        ]
        if len(candidates) == 0:
            candidates = control[
                (control["_stratum"] == stratum)
            ]
        n_matched = min(k, len(candidates))
        if n_matched > 0:
            chosen = candidates.sample(n_matched, random_state=42)
            for _, c_row in chosen.iterrows():
                matched_pairs.append({
                    "treatment_id": int(t_row["paper_id"]),
                    "control_id": int(c_row["paper_id"]),
                    "stratum": stratum,
                })
                control_used.add(int(c_row["paper_id"]))

    # Balance table: compare treatment vs matched controls on `on` variables
    matched_control_ids = [p["control_id"] for p in matched_pairs]
    matched_controls = papers[papers["paper_id"].isin(matched_control_ids)]

    balance = {}
    for col in on:
        if col in treatment.columns and col in matched_controls.columns:
            balance[col] = {
                "treatment_mean": round(float(treatment[col].mean()), 4),
                "control_mean": round(float(matched_controls[col].mean()), 4),
                "treatment_std": round(float(treatment[col].std()), 4),
                "control_std": round(float(matched_controls[col].std()), 4),
            }

    return {
        "matched_pairs": matched_pairs,
        "balance_table": balance,
        "n_treatment": len(treatment),
        "n_matched": len({p["treatment_id"] for p in matched_pairs}),
        "n_unique_controls": len(matched_control_ids),
    }
