#!/usr/bin/env python3
"""
Identify frontier scientists using representative PMIDs from Author-ity 2009.

Extracts PMIDs from au_id (format: {pmid}_{version}) in authorlink_uspto.tsv,
queries PubMed API for journal names, and classifies inventors as frontier
scientists if their representative paper is in a top-8 journal.

Output: data/uspto-pubmed/authority/frontier_inventors.parquet
"""

import time
import urllib.request
import urllib.parse
import json
import xml.etree.ElementTree as ET
from pathlib import Path

import pandas as pd

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "uspto-pubmed" / "authority"

# ── Configuration ──────────────────────────────────────────────────────────
TOP_JOURNALS = {
    "Nature",
    "Science",
    "Cell",
    "Proceedings of the National Academy of Sciences",
    "Proceedings of the National Academy of Sciences of the United States of America",
    "PNAS",
    "The Lancet",
    "Lancet",
    "New England Journal of Medicine",
    "The New England Journal of Medicine",
    "JAMA",
    "BMJ",
    "British Medical Journal",
}

# Normalized journal names for matching
TOP_JOURNAL_PATTERNS = [
    "nature",
    "science",
    "cell",
    "proc natl acad sci",
    "p natl acad sci",
    "lancet",
    "n engl j med",
    "new engl j med",
    "jama",
    "bmj",
    "br med j",
    "brit med j",
]

BATCH_SIZE = 200
NCBI_DELAY = 0.35  # ~3 req/sec without API key


def extract_pmids(authorlink_path: Path) -> pd.DataFrame:
    """Extract PMIDs from au_id field and build inventor->PMID mapping."""
    df = pd.read_csv(authorlink_path, sep="\t")

    # Parse au_id: {pmid}_{version}
    parts = df["au_id"].str.rsplit("_", n=1, expand=True)
    df["pmid"] = parts[0]
    df["cluster_version"] = parts[1]

    # Keep unique inventor->PMID pairs (highest prob per inventor)
    df = df.sort_values("prob", ascending=False)
    df = df.drop_duplicates(subset=["inv_id", "pmid"], keep="first")

    print(f"Loaded {len(df):,} inventor-PMID matches")
    print(f"  Unique inventors: {df['inv_id'].nunique():,}")
    print(f"  Unique PMIDs: {df['pmid'].nunique():,}")
    return df


def fetch_pubmed_batch(pmids: list[str]) -> dict:
    """Fetch metadata for a batch of PMIDs from PubMed E-utilities (esummary)."""
    pmids_str = ",".join(str(p) for p in pmids)
    url = (
        "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?"
        f"db=pubmed&id={pmids_str}&retmode=json"
    )
    try:
        req = urllib.request.Request(url)
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read())
    except Exception as e:
        print(f"  Error fetching batch (first PMID={pmids[0]}): {e}")
        return {}


def parse_pubmed_result(data: dict) -> pd.DataFrame:
    """Parse esummary JSON response into DataFrame with journal info."""
    results = data.get("result", {})
    rows = []
    for pmid, info in results.items():
        if pmid == "uids":
            continue
        rows.append(
            {
                "pmid": pmid,
                "journal": info.get("source", ""),
                "pubdate": info.get("pubdate", ""),
                "title": info.get("title", ""),
                "elocationid": info.get("elocationid", ""),
            }
        )
    return pd.DataFrame(rows)


def classify_frontier(journal: str) -> bool:
    """Check if journal name matches a top-8 general journal."""
    j_lower = journal.lower().strip()
    for pattern in TOP_JOURNAL_PATTERNS:
        if pattern in j_lower:
            # Avoid matching "Science" in journal names like "Psychological Science"
            if pattern == "science" and j_lower != "science":
                continue
            return True
    return False


def main():
    authorlink_path = DATA_DIR / "authorlink_uspto.tsv"
    if not authorlink_path.exists():
        print(f"ERROR: {authorlink_path} not found")
        return

    # ── Step 1: Extract PMIDs ───────────────────────────────────────────
    print("\n[1/3] Extracting PMIDs from Author-ity crosswalk...")
    links = extract_pmids(authorlink_path)

    # ── Step 2: Batch query PubMed ──────────────────────────────────────
    print("\n[2/3] Querying PubMed for journal information...")
    unique_pmids = sorted(links["pmid"].unique(), key=lambda x: int(x) if x.isdigit() else 0)
    n_batches = (len(unique_pmids) + BATCH_SIZE - 1) // BATCH_SIZE

    pmid_journals = {}
    for i in range(0, len(unique_pmids), BATCH_SIZE):
        batch = unique_pmids[i : i + BATCH_SIZE]
        batch_num = i // BATCH_SIZE + 1

        data = fetch_pubmed_batch(batch)
        if data:
            for pmid, info in data.get("result", {}).items():
                if pmid != "uids":
                    pmid_journals[pmid] = info.get("source", "")

        if batch_num % 100 == 0 or batch_num == 1:
            pct = 100 * batch_num / n_batches
            print(f"  Batch {batch_num}/{n_batches} ({pct:.1f}%) — "
                  f"{len(pmid_journals):,} journals retrieved")

        time.sleep(NCBI_DELAY)

    print(f"  Retrieved {len(pmid_journals):,} journal names for "
          f"{len(unique_pmids):,} unique PMIDs")

    # ── Step 3: Classify frontier inventors ─────────────────────────────
    print("\n[3/3] Classifying frontier inventors...")
    links["journal"] = links["pmid"].map(pmid_journals)
    links["is_frontier"] = links["journal"].apply(
        lambda j: classify_frontier(str(j)) if pd.notna(j) and j else False
    )

    frontier_inventors = links[links["is_frontier"]].copy()
    frontier_set = set(frontier_inventors["inv_id"].unique())

    n_frontier = links[links["is_frontier"]]["inv_id"].nunique()
    n_total = links["inv_id"].nunique()

    print(f"\n  Frontier inventors: {n_frontier:,} / {n_total:,} "
          f"({100 * n_frontier / n_total:.1f}%)")

    # Show top journals among frontier inventors
    frontier_journals = frontier_inventors["journal"].value_counts()
    print("\n  Top representative journals:")
    for j, c in frontier_journals.head(15).items():
        print(f"    {j}: {c:,}")

    # ── Save results ────────────────────────────────────────────────────
    # Save frontier inventor set
    frontier_df = pd.DataFrame({"inv_id": sorted(frontier_set)})
    frontier_df.to_parquet(DATA_DIR / "frontier_inventors.parquet", index=False)

    # Save full PMID-journal mapping for reference
    pmid_df = pd.DataFrame(
        [{"pmid": k, "journal": v} for k, v in pmid_journals.items()]
    )
    pmid_df.to_parquet(DATA_DIR / "pmid_journals.parquet", index=False)

    # Save link-level classification
    links[["inv_id", "au_id", "pmid", "journal", "is_frontier", "prob"]].to_parquet(
        DATA_DIR / "inventor_frontier_classification.parquet", index=False
    )

    print(f"\nResults saved to: {DATA_DIR}")
    for f in sorted(DATA_DIR.glob("frontier*.parquet")) + sorted(
        DATA_DIR.glob("pmid_journals*.parquet")
    ):
        print(f"  {f.name}")


if __name__ == "__main__":
    main()
