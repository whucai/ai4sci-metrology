#!/usr/bin/env python3
"""
Download & Merge: Inventor Disambiguation + Paper-Patent Links + Journal Rankings

Produces 3 output tables:
  1. inventor_patent_paper.parquet  — inventor → patent → paper chain
  2. paper_journal_rank.parquet     — paper → journal → SJR rank
  3. inventor_patent_paper_journal.parquet — full chain

Data sources:
  - PatentsView g_persistent_inventor.tsv.zip (~850 MB, already downloaded)
  - SciSciNet (papers, patents, paper_patents) — already in data/sciscinet/
  - SCImago Journal Rank all.csv (~76 MB, already downloaded)
"""

import pandas as pd
import numpy as np
import glob
import os
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data"

# ---- Config ----
PATENTSVIEW_ZIP = DATA_DIR / "patentsview" / "g_persistent_inventor.tsv.zip"
SCISCINET_DIR = DATA_DIR / "sciscinet"
SJR_CSV = DATA_DIR / "sjr" / "scimagojr_all.csv"
OUTPUT_DIR = DATA_DIR / "merged"

# Top comprehensive journals (by ISSN and name patterns)
COMPREHENSIVE_JOURNALS = {
    "0028-0836",  # Nature
    "1476-4687",  # Nature (electronic)
    "0036-8075",  # Science
    "1095-9203",  # Science (electronic)
    "0027-8424",  # PNAS
    "1091-6490",  # PNAS (electronic)
    "2041-1723",  # Nature Communications
    "2375-2548",  # Science Advances
    "2050-084X",  # eLife
    "1549-1676",  # PLoS Medicine
    "1553-734X",  # PLoS Computational Biology
    "1553-7358",  # PLoS Biology
    "1932-6203",  # PLoS ONE
}

COMPREHENSIVE_NAME_PATTERNS = [
    "nature", "science", "pnas", "proceedings of the national academy",
    "plos one", "plos biology", "plos medicine", "elife",
    "nature communications", "science advances",
]


def timer(label: str):
    def decorator(func):
        def wrapper(*args, **kwargs):
            t0 = time.time()
            result = func(*args, **kwargs)
            elapsed = time.time() - t0
            print(f"  [{label}] done in {elapsed:.1f}s")
            return result
        return wrapper
    return decorator


# ============================================================
# Step 1: Load PatentsView inventor data
# ============================================================
@timer("Load PatentsView inventors")
def load_patentsview_inventors():
    """Load the latest disambiguation column from PatentsView."""
    print("Loading PatentsView persistent inventor data...")
    cols = ["patent_id", "inventor_sequence", "disamb_inventor_id_20241231"]
    dtypes = {
        "patent_id": str,
        "inventor_sequence": "Int64",
        "disamb_inventor_id_20241231": str,
    }
    df = pd.read_csv(
        PATENTSVIEW_ZIP,
        compression="zip",
        sep="\t",
        usecols=cols,
        dtype=dtypes,
        na_values=["", " "],
        low_memory=False,
    )
    # Clean patent_id (strip quotes from TSV)
    df["patent_id"] = df["patent_id"].str.strip('"')
    df["disamb_inventor_id_20241231"] = df["disamb_inventor_id_20241231"].str.strip('"')
    # Drop rows where inventor is not disambiguated
    df = df.dropna(subset=["disamb_inventor_id_20241231"])
    df = df.rename(columns={
        "disamb_inventor_id_20241231": "inventor_id",
        "inventor_sequence": "inventor_seq",
    })
    print(f"  Loaded {len(df):,} disambiguated inventor mentions")
    print(f"  Unique inventors: {df.inventor_id.nunique():,}")
    print(f"  Unique patents: {df.patent_id.nunique():,}")
    return df


# ============================================================
# Step 2: Load SciSciNet paper-patent links
# ============================================================
@timer("Load SciSciNet paper-patent links")
def load_sciscinet_paper_patents():
    """Load paper-patent links from SciSciNet."""
    print("Loading SciSciNet paper-patent links...")
    df = pd.read_parquet(SCISCINET_DIR / "paper_patents.parquet")
    # Strip "US-" prefix from patent_id for matching with PatentsView
    df["patent_id_raw"] = df["patent_id"].str.replace(r"^US-", "", regex=True)
    print(f"  Loaded {len(df):,} paper-patent links")
    print(f"  Unique papers: {df.paper_id.nunique():,}")
    print(f"  Unique patents: {df.patent_id_raw.nunique():,}")
    return df


# ============================================================
# Step 3: Load SciSciNet patents
# ============================================================
@timer("Load SciSciNet patents")
def load_sciscinet_patents():
    """Load patent metadata from SciSciNet shards."""
    print("Loading SciSciNet patent metadata...")
    patent_files = sorted(glob.glob(str(SCISCINET_DIR / "patents" / "shard_*.parquet")))
    dfs = []
    for f in patent_files:
        df = pd.read_parquet(f, columns=["patent_id", "title", "year", "date"])
        df["patent_id_raw"] = df["patent_id"].str.replace(r"^US-", "", regex=True)
        dfs.append(df)
    result = pd.concat(dfs, ignore_index=True)
    print(f"  Loaded {len(result):,} patents from {len(patent_files)} shards")
    return result


# ============================================================
# Step 4: Load SciSciNet papers
# ============================================================
@timer("Load SciSciNet papers")
def load_sciscinet_papers():
    """Load paper metadata from SciSciNet shards."""
    print("Loading SciSciNet paper metadata...")
    paper_files = sorted(glob.glob(str(SCISCINET_DIR / "papers" / "shard_*.parquet")))
    paper_cols = [
        "paper_id", "doi", "doc_type", "year", "date", "author_count",
        "journal_id", "journal_name", "journal_issn",
        "citation_count", "disruption_score", "novelty_score",
        "title",
    ]
    dfs = []
    for f in paper_files:
        df = pd.read_parquet(f, columns=paper_cols)
        dfs.append(df)
    result = pd.concat(dfs, ignore_index=True)
    print(f"  Loaded {len(result):,} papers from {len(paper_files)} shards")
    print(f"  Unique journal_issn: {result.journal_issn.nunique():,}")
    print(f"  Year range: {result.year.min()} - {result.year.max()}")
    return result


# ============================================================
# Step 5: Load and prepare SJR journal rankings
# ============================================================
@timer("Load SJR journal rankings")
def load_sjr():
    """Load SCImago Journal Rank data."""
    print("Loading SJR journal rankings...")
    df = pd.read_csv(SJR_CSV)
    # Standardize ISSN
    df["Issn"] = df["Issn"].astype(str).str.strip().str.replace("-", "")
    df = df.rename(columns={
        "Title": "sjr_journal_name",
        "field": "asjc_field_id",
        "SJR": "sjr",
        "h-index": "h_index",
        "avg_citations": "avg_citations_2y",
        "Issn": "issn",
        "Sourceid": "scopus_source_id",
    })
    # Mark comprehensive journals
    df["is_comprehensive"] = df["issn"].isin(COMPREHENSIVE_JOURNALS)
    # Add SJR quartile per field per year
    df["sjr_quartile"] = df.groupby(["asjc_field_id", "year"])["sjr"].transform(
        lambda x: pd.qcut(x.rank(method="first"), 4, labels=["Q4", "Q3", "Q2", "Q1"], duplicates="drop")
    )
    print(f"  Loaded {len(df):,} journal-year records")
    print(f"  Unique ISSNs: {df.issn.nunique():,}")
    print(f"  Year range: {df.year.min()} - {df.year.max()}")
    return df


# ============================================================
# Step 6: Merge — inventor → patent → paper → journal rank
# ============================================================
@timer("Merge: inventor → patent → paper")
def merge_inventor_patent_paper(inventors, paper_patents, patents, papers):
    """Join inventor data with paper-patent links."""
    print("Merging inventor → patent → paper...")

    # Step 6a: Merge paper_patents with papers to get journal info
    # Drop patent_id to avoid conflict; we use patent_id_raw for matching
    pp_papers = paper_patents.drop(columns=["patent_id"]).merge(
        papers[["paper_id", "journal_name", "journal_issn", "year", "doi",
                "citation_count", "disruption_score", "novelty_score", "title"]],
        on="paper_id", how="inner", suffixes=("", "_paper")
    )

    # Step 6b: Merge with patents to get patent metadata
    pp_papers_pat = pp_papers.merge(
        patents[["patent_id_raw", "title", "date"]],
        on="patent_id_raw", how="inner", suffixes=("", "_patent")
    )
    pp_papers_pat = pp_papers_pat.rename(columns={
        "title": "paper_title",
        "title_patent": "patent_title",
        "date": "patent_date",
        "year": "paper_year",
    })

    # Step 6c: Merge with inventor data
    full = pp_papers_pat.merge(
        inventors[["patent_id", "inventor_id", "inventor_seq"]],
        left_on="patent_id_raw", right_on="patent_id", how="inner"
    )

    # Select and order columns
    cols = [
        "inventor_id", "patent_id", "patent_id_raw", "inventor_seq",
        "paper_id", "paper_title", "patent_title",
        "paper_year", "patent_date",
        "doi", "journal_name", "journal_issn",
        "citation_count", "disruption_score", "novelty_score",
    ]
    result = full[[c for c in cols if c in full.columns]]
    print(f"  Merged: {len(result):,} inventor-patent-paper links")
    print(f"  Unique inventors: {result.inventor_id.nunique():,}")
    return result


@timer("Merge: paper → journal rank")
def merge_paper_journal_rank(papers, sjr):
    """Join paper journal info with SJR rankings."""
    print("Merging paper → journal rank...")

    # Get unique journal_issn from papers (normalize: remove hyphens, strip)
    papers_clean = papers[["journal_issn", "journal_name"]].dropna(subset=["journal_issn"]).drop_duplicates().copy()
    papers_clean["issn_norm"] = papers_clean["journal_issn"].str.strip().str.replace("-", "")

    # Use most recent SJR year for each journal
    sjr_latest = sjr.sort_values("year").groupby("issn").last().reset_index()
    sjr_latest = sjr_latest[["issn", "sjr", "h_index", "sjr_journal_name",
                             "asjc_field_id", "is_comprehensive", "sjr_quartile"]]

    # Match by normalized ISSN
    merged = papers_clean.merge(sjr_latest, left_on="issn_norm", right_on="issn", how="left")
    n_matched = merged.sjr.notna().sum()
    print(f"  ISSN-matched: {n_matched:,} / {len(merged):,} journals")

    # Fallback: match by exact journal name (lowercase, stripped)
    unmatched = merged[merged.sjr.isna()]
    if len(unmatched) > 0:
        print(f"  Trying name-based fallback for {len(unmatched):,} unmatched...")
        # Build lookup: lowercase name → best SJR record
        sjr_name_lookup = {}
        for _, row in sjr.iterrows():
            key = str(row["sjr_journal_name"]).lower().strip()
            if key and key not in sjr_name_lookup:
                sjr_name_lookup[key] = row["issn"]

        # Fast vectorized lookup
        unmatched_names = unmatched["journal_name"].str.lower().str.strip()
        matched_issns = unmatched_names.map(sjr_name_lookup)

        # For matched ones, fill in SJR data
        mask = matched_issns.notna()
        n_name_matched = mask.sum()
        print(f"  Name-matched: {n_name_matched:,} additional journals")

        if n_name_matched > 0:
            # Build a lookup from issn → sjr data
            sjr_data_lookup = sjr_latest.set_index("issn")
            for idx in unmatched[mask].index:
                issn = matched_issns[idx]
                if issn in sjr_data_lookup.index:
                    for col in sjr_latest.columns:
                        if col != "issn":
                            merged.loc[idx, col] = sjr_data_lookup.loc[issn, col]

    total_matched = merged.sjr.notna().sum()
    print(f"  Total matched: {total_matched:,} / {len(merged):,}")

    # Also mark comprehensive journals by name pattern
    name_lower = merged["journal_name"].str.lower().str.strip()
    for pattern in COMPREHENSIVE_NAME_PATTERNS:
        merged.loc[name_lower.str.contains(pattern, na=False), "is_comprehensive"] = True

    result = merged.rename(columns={
        "sjr": "journal_sjr",
        "h_index": "journal_h_index",
        "sjr_journal_name": "sjr_matched_name",
        "is_comprehensive": "is_comprehensive_journal",
        "sjr_quartile": "journal_quartile",
    })
    print(f"  Final: {len(result):,} paper-journal-rank mappings")
    return result


@timer("Merge: full chain")
def merge_full_chain(ipp, journal_rank):
    """Merge inventor-patent-paper with journal rankings."""
    print("Merging full chain...")
    result = ipp.merge(
        journal_rank[["journal_issn", "journal_sjr", "journal_h_index",
                      "is_comprehensive_journal", "journal_quartile", "asjc_field_id"]],
        on="journal_issn", how="left"
    )
    print(f"  Full chain: {len(result):,} rows")
    print(f"  With journal rank: {result.journal_sjr.notna().sum():,}")
    print(f"  Comprehensive journals: {result.is_comprehensive_journal.sum():,}")
    return result


# ============================================================
# Step 7: Inventor summary statistics
# ============================================================
@timer("Build inventor summary")
def build_inventor_summary(ipp):
    """Build per-inventor summary statistics."""
    print("Building inventor summary...")
    summary = ipp.groupby("inventor_id").agg(
        num_patents=("patent_id", "nunique"),
        num_papers=("paper_id", "nunique"),
        avg_disruption=("disruption_score", "mean"),
        avg_novelty=("novelty_score", "mean"),
        total_citations=("citation_count", "sum"),
    ).reset_index()
    print(f"  {len(summary):,} inventor summaries")
    return summary


# ============================================================
# Main
# ============================================================
def main():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    t0 = time.time()

    print("=" * 60)
    print("SciSci Metrology: Data Merge Pipeline")
    print("=" * 60)

    # Load all data
    inventors = load_patentsview_inventors()
    paper_patents = load_sciscinet_paper_patents()
    patents = load_sciscinet_patents()
    papers = load_sciscinet_papers()
    sjr = load_sjr()

    # Merge
    ipp = merge_inventor_patent_paper(inventors, paper_patents, patents, papers)
    journal_rank = merge_paper_journal_rank(papers, sjr)
    full_chain = merge_full_chain(ipp, journal_rank)
    inventor_summary = build_inventor_summary(ipp)

    # Save outputs
    print("\n" + "=" * 60)
    print("Saving output files...")

    @timer("Save inventor_patent_paper.parquet")
    def save_ipp():
        ipp.to_parquet(OUTPUT_DIR / "inventor_patent_paper.parquet", index=False)
        return len(ipp)
    n_ipp = save_ipp()

    @timer("Save paper_journal_rank.parquet")
    def save_pjr():
        journal_rank.to_parquet(OUTPUT_DIR / "paper_journal_rank.parquet", index=False)
        return len(journal_rank)
    n_pjr = save_pjr()

    @timer("Save inventor_patent_paper_journal.parquet")
    def save_full():
        full_chain.to_parquet(OUTPUT_DIR / "inventor_patent_paper_journal.parquet", index=False)
        return len(full_chain)
    n_full = save_full()

    @timer("Save inventor_summary.parquet")
    def save_summary():
        inventor_summary.to_parquet(OUTPUT_DIR / "inventor_summary.parquet", index=False)
        return len(inventor_summary)
    n_sum = save_summary()

    # Report
    elapsed = time.time() - t0
    print("\n" + "=" * 60)
    print("MERGE COMPLETE")
    print("=" * 60)
    print(f"Total time: {elapsed/60:.1f} min")
    print(f"\nOutput files in {OUTPUT_DIR}:")
    print(f"  1. inventor_patent_paper.parquet          {n_ipp:>12,} rows")
    print(f"  2. paper_journal_rank.parquet             {n_pjr:>12,} rows")
    print(f"  3. inventor_patent_paper_journal.parquet  {n_full:>12,} rows")
    print(f"  4. inventor_summary.parquet               {n_sum:>12,} rows")
    print(f"\nSizes on disk:")
    for f in sorted(OUTPUT_DIR.glob("*.parquet")):
        size_mb = os.path.getsize(f) / (1024 * 1024)
        print(f"  {f.name:45s} {size_mb:8.1f} MB")


if __name__ == "__main__":
    main()
