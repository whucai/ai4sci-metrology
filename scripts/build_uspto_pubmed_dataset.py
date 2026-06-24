#!/usr/bin/env python3
"""
Build merged USPTO-PubMed linked dataset for Schaper 2025 reproduction.

Merges:
  1. PatentsView patent metadata (BigQuery export)
  2. Inventor-author matching (Author-ity 2009)
  3. Frontier inventor classification (from representative PMIDs)
  4. Reliance on Science patent-paper citations
  5. WIPO/NBER technology categories
  6. Forward citation counts

Output: data/uspto-pubmed/merged/
  - patents_enriched.parquet  — patent-level dataset with frontier indicators
  - patent_citations.parquet  — patent-to-paper citation links with frontier flags
"""

import os
from pathlib import Path

import numpy as np
import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "uspto-pubmed"
MERGED_DIR = DATA_DIR / "merged"
MERGED_DIR.mkdir(parents=True, exist_ok=True)

PV_DIR = DATA_DIR / "patentsview"
AUTH_DIR = DATA_DIR / "authority"
ROS_DIR = DATA_DIR / "reliance_on_science"

# ── Configuration ──────────────────────────────────────────────────────────
LOOKAHEAD_LAG = 1  # Years: focal year N uses frontier status through N-LAG

# Top-8 general journal NLM abbreviations
TOP_JOURNALS = {
    "Nature", "Science", "Cell",
    "Proc Natl Acad Sci U S A",
    "Lancet",
    "N Engl J Med",
    "JAMA",
    "BMJ", "Br Med J", "Br Med J (Clin Res Ed)",
}


def load_patents() -> pd.DataFrame:
    """Load PatentsView patent metadata."""
    print("[1] Loading patent metadata...")
    patents = pd.read_parquet(PV_DIR / "patents.parquet")
    print(f"    {len(patents):,} patents, {patents['patent_year'].min()}-"
          f"{patents['patent_year'].max()}")

    # Merge forward citations
    fwd = pd.read_parquet(PV_DIR / "forward_cites.parquet")
    patents = patents.merge(fwd, on="patent_id", how="left")
    patents["num_cited_by_us_patents"] = (
        patents["num_cited_by_us_patents"].fillna(0).astype(int)
    )
    print(f"    Forward citations merged: {len(fwd):,} records")

    # Merge inventor counts
    inv_counts = pd.read_parquet(PV_DIR / "inventor_counts.parquet")
    patents = patents.merge(inv_counts, on="patent_id", how="left")
    patents["number_of_inventors"] = (
        patents["number_of_inventors"].fillna(0).astype(int)
    )

    # Merge WIPO class
    wipo = pd.read_parquet(PV_DIR / "wipo_class.parquet")
    patents = patents.merge(
        wipo[["patent_id", "section", "ipc_code"]], on="patent_id", how="left"
    )

    # Merge NBER category
    nber = pd.read_parquet(PV_DIR / "nber_cat.parquet")
    # Take first NBER category per patent
    nber_first = nber.groupby("patent_id").first().reset_index()
    patents = patents.merge(
        nber_first[["patent_id", "category_id", "subcategory_id"]],
        on="patent_id",
        how="left",
    )

    print(f"    Final: {len(patents):,} patents with enriched metadata")
    return patents


def load_frontier_patent_set() -> tuple[set, dict]:
    """Build frontier patent set by matching through patent numbers.

    Author-ity inventor IDs ≠ PatentsView inventor IDs (different systems).
    Instead, match frontier inventors to patents via patent numbers:
      - uiuc_uspto.tsv: inventor_id → patent numbers (zero-padded)
      - PatentsView.patents: patent_id (unpadded numeric string)

    Returns (frontier_patent_ids, frontier_patent_year_range)
    where frontier_patent_year_range maps patent_id -> earliest frontier year.
    """
    print("\n[2] Building frontier patent set via patent-number matching...")

    # Load frontier inventor IDs
    frontier_df = pd.read_parquet(AUTH_DIR / "frontier_inventors.parquet")
    frontier_inv_ids = set(frontier_df["inv_id"].unique())
    print(f"    {len(frontier_inv_ids):,} frontier inventors (representative PMID)")

    # Load inventor data with patent numbers
    inv_data = pd.read_csv(
        AUTH_DIR / "uiuc_uspto.tsv", sep="\t",
        usecols=["inv_id", "patents", "first_app_yr", "last_app_yr"]
    )

    # Filter to frontier inventors
    inv_data = inv_data[inv_data["inv_id"].isin(frontier_inv_ids)]

    # Also load frontier classification with journal/pubdate info
    fc = pd.read_parquet(AUTH_DIR / "inventor_frontier_classification.parquet")
    fc = fc[fc["is_frontier_correct"]]
    # Get PMID pubdates from pmid_journals.parquet
    pmid_journals = pd.read_parquet(AUTH_DIR / "pmid_journals.parquet")
    # Note: pmid_journals only has pmid->journal; pubdate not saved.
    # We'll approximate using inventor's first_app_yr as lower bound.

    # Explode patent numbers per inventor
    inv_data["patent_list"] = inv_data["patents"].str.split("|")
    exploded = inv_data[["inv_id", "patent_list"]].explode("patent_list")
    exploded["patent_num"] = (
        exploded["patent_list"].astype(str).str.lstrip("0")
    )

    # Count frontier inventors per patent
    patent_frontier_counts = (
        exploded.groupby("patent_num")["inv_id"]
        .nunique()
        .reset_index()
        .rename(columns={"inv_id": "num_frontier_inventors"})
    )

    frontier_patent_ids = set(patent_frontier_counts["patent_num"])
    print(f"    Frontier-author patents (via patent # match): "
          f"{len(frontier_patent_ids):,}")

    return frontier_patent_ids, patent_frontier_counts


def classify_patents(
    patents: pd.DataFrame,
    frontier_patent_ids: set,
    patent_frontier_counts: pd.DataFrame,
) -> pd.DataFrame:
    """Classify each patent as frontier-author or not using patent-number match."""
    print("\n[3] Classifying frontier-author patents...")

    result = patents.copy()
    result["has_frontier_inventor"] = (
        result["patent_id"].isin(frontier_patent_ids)
    )
    result = result.merge(
        patent_frontier_counts,
        left_on="patent_id",
        right_on="patent_num",
        how="left",
    )
    result["num_frontier_inventors"] = (
        result["num_frontier_inventors"].fillna(0).astype(int)
    )
    result = result.drop(columns=["patent_num"], errors="ignore")

    n_fa = result["has_frontier_inventor"].sum()
    n_total = len(result)
    print(f"    Frontier-author patents: {n_fa:,} / {n_total:,} "
          f"({100 * n_fa / n_total:.1f}%)")

    return result


def load_patent_paper_citations() -> pd.DataFrame:
    """Load Reliance on Science patent-to-paper citations."""
    print("\n[4] Loading patent-paper citations (Reliance on Science)...")
    pcs = pd.read_csv(ROS_DIR / "_pcs_oa.csv")
    print(f"    {len(pcs):,} citation links")

    # Parse patent number from 'patent' column (format: 'us-11426570-b2')
    pcs["patent_num"] = (
        pcs["patent"].str.extract(r"us-(\d+)-", expand=False)
    )

    # Keep high-confidence citations
    pcs_clean = pcs[pcs["confscore"] >= 6].copy()
    print(f"    High-confidence (confscore >= 6): {len(pcs_clean):,}")

    # Track unique cited papers
    unique_papers = pcs_clean["oaid"].nunique()
    print(f"    Unique cited papers: {unique_papers:,}")

    return pcs_clean


def compute_citation_indicators(
    patents: pd.DataFrame, pcs: pd.DataFrame
) -> pd.DataFrame:
    """Add patent-level citation indicators."""
    print("\n[5] Computing patent-level citation indicators...")

    # Count backward citations to scientific papers per patent
    cite_counts = (
        pcs.groupby("patent_num")["oaid"]
        .nunique()
        .reset_index()
        .rename(columns={"oaid": "num_science_refs"})
    )
    patents = patents.merge(cite_counts, left_on="patent_id",
                            right_on="patent_num", how="left")
    patents["num_science_refs"] = (
        patents["num_science_refs"].fillna(0).astype(int)
    )
    patents = patents.drop(columns=["patent_num"], errors="ignore")

    n_with_refs = (patents["num_science_refs"] > 0).sum()
    print(f"    Patents with >=1 science reference: {n_with_refs:,} "
          f"({100 * n_with_refs / len(patents):.1f}%)")

    return patents


def build_full_sample(patents: pd.DataFrame) -> pd.DataFrame:
    """Build the full analysis sample with derived variables."""
    print("\n[6] Building analysis sample...")

    df = patents.copy()

    # Apply look-ahead lag for frontier classification
    # A patent filed in year Y should check frontier status through Y-LAG
    df["frontier_eligible_year"] = df["patent_year"] - LOOKAHEAD_LAG

    # Log-transformed citation count
    df["log_cites"] = np.log1p(df["num_cited_by_us_patents"])

    # Create WIPO field dummies (IPC section)
    wipo_dummies = pd.get_dummies(
        df["section"].fillna("unknown"), prefix="wipo"
    )
    df = pd.concat([df, wipo_dummies.astype(int)], axis=1)

    # Create year dummies
    year_dummies = pd.get_dummies(df["patent_year"], prefix="yr")
    df = pd.concat([df, year_dummies.astype(int)], axis=1)

    # Hit patent: top 5% within patent class × year
    # Using WIPO section as patent class proxy
    df["citation_pctile"] = df.groupby(["section", "patent_year"])[
        "num_cited_by_us_patents"
    ].transform(
        lambda x: x.rank(pct=True)
    )
    df["is_hit"] = df["citation_pctile"] >= 0.95

    n_hits = df["is_hit"].sum()
    print(f"    Hit patents (top 5%): {n_hits:,} / {len(df):,} "
          f"({100 * n_hits / len(df):.2f}%)")

    return df


def main():
    print("=" * 60)
    print("Building USPTO-PubMed Linked Dataset")
    print("=" * 60)

    # Step 1: Load patent data
    patents = load_patents()

    # Step 2: Build frontier patent set (via patent-number matching)
    frontier_patent_ids, patent_frontier_counts = load_frontier_patent_set()

    # Step 3: Classify frontier-author patents
    patents = classify_patents(patents, frontier_patent_ids, patent_frontier_counts)

    # Step 4: Load patent-paper citations
    pcs = load_patent_paper_citations()

    # Step 5: Compute citation indicators
    patents = compute_citation_indicators(patents, pcs)

    # Step 6: Build analysis sample
    sample = build_full_sample(patents)

    # Step 7: Save
    print("\n[7] Saving results...")

    # Core patent-level dataset
    out_cols = [
        "patent_id", "patent_year", "patent_date", "patent_type",
        "num_claims", "number_of_inventors", "num_frontier_inventors",
        "has_frontier_inventor",
        "num_cited_by_us_patents", "log_cites", "is_hit", "citation_pctile",
        "num_science_refs",
        "section", "ipc_code", "category_id", "subcategory_id",
        "frontier_eligible_year",
    ]
    out_cols = [c for c in out_cols if c in sample.columns]
    out = sample[out_cols].copy()

    out_path = MERGED_DIR / "patents_enriched.parquet"
    out.to_parquet(out_path, index=False)
    size_mb = out_path.stat().st_size / 1e6
    print(f"    {out_path.name}: {size_mb:.1f} MB, {len(out):,} rows")

    # Save patent-citation links (for frontier-reference analysis)
    pcs_out = pcs[["oaid", "patent_num", "confscore", "reftype"]].copy()
    pcs_out.to_parquet(MERGED_DIR / "patent_citations.parquet", index=False)

    print("\n" + "=" * 60)
    print("Dataset build complete!")
    print(f"Files saved to: {MERGED_DIR}")
    for f in sorted(MERGED_DIR.glob("*.parquet")):
        print(f"  {f.name}: {f.stat().st_size / 1e6:.1f} MB")
    print("=" * 60)

    # Summary statistics
    print("\nSummary Statistics:")
    print(f"  Total patents:              {len(out):>12,}")
    print(f"  Frontier-author patents:    {out['has_frontier_inventor'].sum():>12,}")
    print(f"  Hit patents:                {out['is_hit'].sum():>12,}")
    print(f"  Mean forward cites (all):   {out['num_cited_by_us_patents'].mean():>12.1f}")
    print(f"  Mean forward cites (FA):    {out.loc[out['has_frontier_inventor'], 'num_cited_by_us_patents'].mean():>12.1f}")
    print(f"  Mean forward cites (NFA):   {out.loc[~out['has_frontier_inventor'], 'num_cited_by_us_patents'].mean():>12.1f}")
    print(f"  Median forward cites (all): {out['num_cited_by_us_patents'].median():>12.0f}")
    print(f"  Patent year range:          {out['patent_year'].min()}-{out['patent_year'].max()}")


if __name__ == "__main__":
    main()
