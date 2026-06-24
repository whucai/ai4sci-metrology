#!/usr/bin/env python3
"""
Download USPTO PatentsView patent data for Research Policy paper reproduction.

NOTE: The PatentsView API v1 (api.patentsview.org) has been DEPRECATED as of 2025.
Data has migrated to the USPTO Open Data Portal (data.uspto.gov) which requires
API key authentication.

This script supports TWO download methods:
  1. --source huggingface : Download from HuggingFace datasets (works, no auth needed)
  2. --source api         : PatentsView API v1 (DEPRECATED — will likely fail)

Target papers:
  1. Arts et al. (2021) RP: NLP on patent text — needs patent title, abstract
  2. Schaper et al. (2025) RP: Frontier scientists — needs inventor names, patent citations

HuggingFace sources used:
  - kaustav16/patent_abstract_uspto  : 9.36M patent abstracts (2.7 GB)
  - mhurhangee/us_patent_claim1      : 4.47M Claim 1 texts (split by year)
  - 0zo/google_patentsview_claims_2016 : 150K with dates + CPC (2016 only)

Usage:
    # Download abstracts from HuggingFace (recommended)
    python scripts/download_patentsview.py --source huggingface --sample-size 100000 --years 2015,2016,2017,2018,2019

    # Health check
    python scripts/download_patentsview.py --health-check

Data saved to: data/patentsview/
  - patent_abstracts.parquet  : patent_id, patent_abstract (9.36M rows)
  - claims_YYYY.parquet       : patent_id, claim_text (per year)
  - patents_full.parquet      : Merged dataset (patent_id + abstract + claim + date + cpc)
  - patents_sample_50k.parquet: 50K sample for quick testing
  - patents_sample_100k.parquet: 100K sample

Requirements:
    pip install requests pandas pyarrow tqdm huggingface_hub
"""

import os
import sys
import json
import time
import argparse
from pathlib import Path
from typing import Optional

import requests
import pandas as pd
from tqdm import tqdm

# ---------- Configuration ----------

PATENTSVIEW_API = "https://api.patentsview.org"
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "data" / "patentsview"

# Fields available in PatentsView (documented at patentsview.org/apis)
PATENT_FIELDS = [
    "patent_id",
    "patent_title",
    "patent_abstract",
    "patent_date",
    "patent_num_claims",
    "patent_type",
    "patent_num_cited_by_us_patents",
    "patent_num_combined_citations",
    "app_date",
    "patent_processing_time",
    "wipo_kind",
    "inventor_first_name",
    "inventor_last_name",
    "assignee_organization",
    "cpc_subgroup_id",
]

INVENTOR_FIELDS = [
    "inventor_id",
    "inventor_name_first",
    "inventor_name_last",
    "patent_id",
]

# ---------- API Client ----------

class PatentsViewClient:
    """Client for the PatentsView REST API.

    The PatentsView API uses a JSON query language. Key endpoints:
      - /patents/query     — patent metadata
      - /inventors/query   — inventor disambiguation data
      - /cpc_subsections/query — CPC classification

    API docs: https://patentsview.org/apis/purpose
    """

    def __init__(self, base_url: str = PATENTSVIEW_API, rate_limit_delay: float = 0.5):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({
            "User-Agent": "ai4sci-metrology-research/1.0 (mailto:research@example.com)",
            "Accept": "application/json",
        })
        self.rate_limit_delay = rate_limit_delay

    def _query(self, endpoint: str, q: dict, f: list[str],
               page: int = 1, per_page: int = 1000,
               sort: Optional[list] = None) -> dict:
        """Execute a PatentsView query.

        Args:
            endpoint: e.g. "patents", "inventors"
            q: query filter dict, e.g. {"_gte": {"patent_date": "2000-01-01"}}
            f: list of field names to return
            page: page number (1-indexed)
            per_page: results per page (max 10000)
            sort: optional sort, e.g. [{"patent_date": "desc"}]
        """
        body = {"q": q, "f": f, "o": {"page": page, "per_page": per_page}}
        if sort:
            body["o"]["sort"] = sort

        url = f"{self.base_url}/{endpoint}/query"
        resp = self.session.post(url, json=body, timeout=60)
        resp.raise_for_status()
        data = resp.json()

        if "error" in data:
            raise RuntimeError(f"API error: {data['error']}")

        time.sleep(self.rate_limit_delay)
        return data

    def query_patents(self, q: dict, f: list[str], page: int = 1,
                      per_page: int = 1000) -> dict:
        return self._query("patents", q, f, page, per_page)

    def query_inventors(self, q: dict, f: list[str], page: int = 1,
                        per_page: int = 1000) -> dict:
        return self._query("inventors", q, f, page, per_page)

    def get_total_count(self, endpoint: str, q: dict) -> int:
        """Get total number of matching records."""
        result = self._query(endpoint, q, ["patent_id"], page=1, per_page=1)
        return result.get("total_patent_count", 0)


# ---------- Download Functions ----------

def download_patents_by_year_range(client: PatentsViewClient,
                                   year_start: int, year_end: int,
                                   max_patents: Optional[int] = None) -> pd.DataFrame:
    """Download patent metadata for a given year range.

    Uses the PatentsView date-range query. For each year, downloads in pages
    of up to 10,000 patents per request.
    """
    all_records = []

    q = {
        "_and": [
            {"_gte": {"patent_date": f"{year_start}-01-01"}},
            {"_lte": {"patent_date": f"{year_end}-12-31"}},
        ]
    }

    total = client.get_total_count("patents", q)
    n_to_fetch = min(total, max_patents) if max_patents else total
    per_page = 1000  # safer than max 10k
    n_pages = (n_to_fetch + per_page - 1) // per_page

    print(f"  Total patents in range: {total:,}")
    print(f"  Fetching: {n_to_fetch:,} ({n_pages} pages)")

    for page in tqdm(range(1, n_pages + 1), desc="  Downloading patents"):
        try:
            result = client.query_patents(q, PATENT_FIELDS, page=page, per_page=per_page)
            patents = result.get("patents", [])
            if not patents:
                break
            all_records.extend(patents)
        except Exception as e:
            print(f"  [WARN] Page {page} failed: {e}")
            time.sleep(2)  # back off and retry once
            try:
                result = client.query_patents(q, PATENT_FIELDS, page=page, per_page=per_page)
                patents = result.get("patents", [])
                all_records.extend(patents)
            except Exception as e2:
                print(f"  [ERROR] Page {page} retry also failed: {e2}")
                break

    df = pd.DataFrame(all_records)
    print(f"  Downloaded {len(df):,} patent records")
    return df


def download_citations_for_patents(client: PatentsViewClient,
                                    patent_ids: list[str]) -> pd.DataFrame:
    """Download citation edges for a list of patent IDs.

    PatentsView stores citations within the patent record itself as nested
    arrays. We query each patent to extract its citations.

    A more efficient approach: use the bulk download citation table.
    """
    all_citations = []
    per_page = 500  # smaller because of nested data

    for i in tqdm(range(0, len(patent_ids), per_page), desc="  Downloading citations"):
        batch = patent_ids[i:i + per_page]
        # Query with citation fields
        q = {"patent_id": batch}
        f = ["patent_id", "citpat_cited_patent_id", "citpat_citing_patent_id",
             "citpat_num_times_cited"]
        try:
            result = client._query("patents", q, f, page=1, per_page=per_page)
            for patent in result.get("patents", []):
                pid = patent.get("patent_id")
                for cit in patent.get("patent_citations", []):
                    all_citations.append({
                        "citing_patent_id": pid,
                        "cited_patent_id": cit.get("cited_patent_id"),
                        "num_times_cited": cit.get("num_times_cited_by_us_patents"),
                    })
        except Exception as e:
            print(f"  [WARN] Citation batch failed at index {i}: {e}")

    df = pd.DataFrame(all_citations)
    print(f"  Downloaded {len(df):,} citation edges")
    return df


def download_inventors_for_patents(client: PatentsViewClient,
                                    patent_ids: list[str]) -> pd.DataFrame:
    """Download disambiguated inventor data for a list of patent IDs."""
    all_inventors = []
    per_page = 1000

    for i in tqdm(range(0, len(patent_ids), per_page), desc="  Downloading inventors"):
        batch = patent_ids[i:i + per_page]
        q = {"patent_id": batch}
        try:
            result = client._query("inventors", q, INVENTOR_FIELDS,
                                   page=1, per_page=per_page)
            for inv in result.get("inventors", []):
                all_inventors.append({
                    "inventor_id": inv.get("inventor_id"),
                    "inventor_name_first": inv.get("inventor_name_first"),
                    "inventor_name_last": inv.get("inventor_name_last"),
                    "patent_id": inv.get("patent_id"),
                })
        except Exception as e:
            print(f"  [WARN] Inventor batch failed at index {i}: {e}")

    df = pd.DataFrame(all_inventors)
    print(f"  Downloaded {len(df):,} inventor records")
    return df


def check_api_health() -> dict:
    """Quick check if the PatentsView API is responsive."""
    try:
        resp = requests.get("https://api.patentsview.org/", timeout=10)
        return {"endpoint": "api.patentsview.org", "status": resp.status_code, "ok": resp.ok}
    except Exception as e:
        return {"endpoint": "api.patentsview.org", "status": "error", "error": str(e)}


# ---------- Alternative: Bulk Download ----------

BULK_DOWNLOAD_GUIDE = """
================================================================================
ALTERNATIVE: PatentsView Bulk Data Download
================================================================================

If the API is slow or deprecated, use the bulk download approach:

1. Visit: https://patentsview.org/download/
2. Download these TSV files (gzip compressed):
   - patent.tsv.zip       — patent metadata (id, title, abstract, date, num_claims)
   - uspatentcitation.tsv.zip — citation edges (patent_id, citation_id)
   - inventor.tsv.zip     — disambiguated inventor data
   - patent_claim.tsv.zip — claim text (if available)

3. Process locally:

   import pandas as pd
   patents = pd.read_csv('patent.tsv', sep='\\t', low_memory=False)
   # Filter to your date range
   patents_2000_2010 = patents[
       (patents['patent_date'] >= '2000-01-01') &
       (patents['patent_date'] <= '2010-12-31')
   ]
   patents_2000_2010.to_parquet('data/patentsview/patents.parquet')

   citations = pd.read_csv('uspatentcitation.tsv', sep='\\t')
   # Join with patent filter
   citations_filtered = citations[
       citations['patent_id'].isin(patents_2000_2010['patent_id'])
   ]
   citations_filtered.to_parquet('data/patentsview/citations.parquet')

ALTERNATIVE DATA SOURCES:
  - Kaggle: https://www.kaggle.com/datasets — search "USPTO patents"
  - HuggingFace: https://huggingface.co/datasets — search "patent"
  - Google Patents Public Data (BigQuery): bigquery-public-data.patents
  - Zenodo: https://zenodo.org/ — search "USPTO patent dataset"
  - USPTO Open Data Portal: https://developer.uspto.gov/
================================================================================
"""


# ---------- HuggingFace Download ----------

HF_ABSTRACT_DATASET = "kaustav16/patent_abstract_uspto"
HF_CLAIMS_DATASET = "mhurhangee/us_patent_claim1"
HF_PATENTSVIEW_2016 = "0zo/google_patentsview_claims_2016"

def download_from_huggingface(args):
    """Download patent data from HuggingFace datasets.

    This is the RECOMMENDED method since PatentsView API v1 is deprecated.
    Downloads patent abstracts and Claim 1 texts, then merges them.
    """
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    # Parse years
    years = [y.strip() for y in args.years.split(",")]

    # Step 1: Download patent abstracts
    abstracts_path = output_dir / "patent_abstracts.parquet"
    if abstracts_path.exists() and not args.redownload:
        print(f"[1/4] Abstracts already downloaded: {abstracts_path}")
    else:
        print("[1/4] Downloading patent abstracts from HuggingFace...")
        url = f"https://huggingface.co/datasets/{HF_ABSTRACT_DATASET}/resolve/main/g_patent_abstract.parquet"
        _download_file(url, abstracts_path, desc="abstracts")

    # Step 2: Download claims for specified years
    all_claims = []
    for year in years:
        claims_path = output_dir / f"claims_{year}.parquet"
        if claims_path.exists() and not args.redownload:
            print(f"[2/4] Claims {year} already downloaded")
        else:
            url = f"https://huggingface.co/datasets/{HF_CLAIMS_DATASET}/resolve/main/data/claims_{year}.parquet"
            print(f"[2/4] Downloading claims {year}...")
            _download_file(url, claims_path, desc=f"claims_{year}")
        all_claims.append(pd.read_parquet(claims_path))

    claims = pd.concat(all_claims, ignore_index=True)
    print(f"  Total claims: {len(claims):,}")

    # Step 3: Download PatentsView 2016 (with dates) if requested
    if args.include_dates:
        pv_path = output_dir / "patentsview_2016.parquet"
        if pv_path.exists() and not args.redownload:
            print(f"[3/4] PatentsView 2016 already downloaded")
        else:
            print("[3/4] Downloading PatentsView 2016 (with dates)...")
            url = f"https://huggingface.co/datasets/{HF_PATENTSVIEW_2016}/resolve/main/data/train-00000-of-00001.parquet"
            _download_file(url, pv_path, desc="patentsview_2016")

    # Step 4: Merge abstracts + claims
    print("[4/4] Merging abstracts + claims...")
    abstracts = pd.read_parquet(abstracts_path)
    merged = abstracts.merge(claims, on="patent_id", how="inner")
    print(f"  Merged: {len(merged):,} rows")

    # Merge with PatentsView 2016 if available
    pv_path = output_dir / "patentsview_2016.parquet"
    if pv_path.exists():
        pv = pd.read_parquet(pv_path)
        pv["patent_id"] = pv["id"].astype(str)
        merged = merged.merge(pv[["patent_id", "date", "cpc_ids"]],
                              on="patent_id", how="left")
        print(f"  With dates: {merged['date'].notna().sum():,}")

    # Save full dataset
    full_path = output_dir / "patents_full.parquet"
    merged.to_parquet(full_path, index=False)
    print(f"  Full dataset: {full_path}")

    # Save benchmark sample
    if args.sample_size > 0:
        sample = merged.head(args.sample_size)
        sample_path = output_dir / f"patents_sample_{args.sample_size//1000}k.parquet"
        sample.to_parquet(sample_path, index=False)
        size_mb = sample_path.stat().st_size / 1024 / 1024
        print(f"  Sample ({args.sample_size:,} rows): {sample_path} ({size_mb:.1f} MB)")

    return merged


def _download_file(url: str, path: Path, desc: str = "file"):
    """Download a file with progress indication."""
    import shutil
    r = requests.get(url, stream=True, timeout=600)
    r.raise_for_status()
    total = int(r.headers.get("content-length", 0))
    downloaded = 0
    with open(path, "wb") as f:
        for chunk in r.iter_content(chunk_size=8*1024*1024):
            f.write(chunk)
            downloaded += len(chunk)
            if total:
                pct = downloaded / total * 100
                mb = downloaded / 1024 / 1024
                total_mb = total / 1024 / 1024
                print(f"\r    {mb:.0f}/{total_mb:.0f} MB ({pct:.0f}%)", end="", flush=True)
    print(f"\r    Done: {downloaded/1024/1024:.0f} MB{' ' * 30}")


# ---------- Main ----------

def main():
    parser = argparse.ArgumentParser(
        description="Download USPTO PatentsView data for Research Policy paper reproduction"
    )
    parser.add_argument("--source", type=str, default="huggingface",
                        choices=["huggingface", "api"],
                        help="Data source: huggingface (recommended) or api (DEPRECATED)")
    parser.add_argument("--sample-size", type=int, default=50000,
                        help="Number of patents in benchmark sample (default: 50000)")
    parser.add_argument("--years", type=str, default="2015,2016,2017,2018,2019",
                        help="Comma-separated years for claims data (default: 2015-2019)")
    parser.add_argument("--year-start", type=int, default=2000,
                        help="Start year (API mode only)")
    parser.add_argument("--year-end", type=int, default=2005,
                        help="End year (API mode only)")
    parser.add_argument("--include-dates", action="store_true",
                        help="Also download PatentsView 2016 data with dates")
    parser.add_argument("--include-citations", action="store_true",
                        help="Also download citation data (API mode only)")
    parser.add_argument("--include-inventors", action="store_true",
                        help="Also download inventor data (API mode only)")
    parser.add_argument("--output-dir", type=str,
                        default=str(OUTPUT_DIR),
                        help="Output directory for parquet files")
    parser.add_argument("--rate-limit", type=float, default=0.5,
                        help="Delay between API requests in seconds")
    parser.add_argument("--redownload", action="store_true",
                        help="Re-download even if files exist")
    parser.add_argument("--health-check", action="store_true",
                        help="Only check data source health and exit")
    args = parser.parse_args()

    print("=" * 70)
    print("  USPTO PatentsView Data Downloader")
    print("=" * 70)
    print()

    # Health check
    print("[1/4] Checking API health...")
    health = check_api_health()
    if health["ok"]:
        print(f"  API is reachable (HTTP {health['status']})")
    else:
        print(f"  WARNING: API check failed: {health.get('error', 'unknown')}")
        print(f"  Status code: {health['status']}")
        print()
        print(BULK_DOWNLOAD_GUIDE)
        print()
        print("The script can still attempt the download, but it may fail.")
        response = input("  Continue anyway? [y/N]: ")
        if response.lower() != 'y':
            print("  Aborted by user.")
            return

    if args.health_check:
        return

    # Create output directory
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    client = PatentsViewClient(rate_limit_delay=args.rate_limit)

    # Download patents
    print(f"\n[2/4] Downloading patent metadata ({args.year_start}-{args.year_end})...")
    df_patents = download_patents_by_year_range(
        client, args.year_start, args.year_end, max_patents=args.sample_size
    )

    # Normalize nested columns
    for col in df_patents.columns:
        if df_patents[col].apply(lambda x: isinstance(x, (list, dict))).any():
            df_patents[col] = df_patents[col].apply(
                lambda x: json.dumps(x) if isinstance(x, (list, dict)) else x
            )

    patents_path = output_dir / "patents.parquet"
    df_patents.to_parquet(patents_path, index=False)
    print(f"  Saved {len(df_patents):,} records to {patents_path}")

    # Download citations
    if args.include_citations:
        print(f"\n[3/4] Downloading citation data...")
        patent_ids = df_patents["patent_id"].dropna().astype(str).tolist()
        df_citations = download_citations_for_patents(client, patent_ids)
        citations_path = output_dir / "citations.parquet"
        df_citations.to_parquet(citations_path, index=False)
        print(f"  Saved {len(df_citations):,} records to {citations_path}")
    else:
        print(f"\n[3/4] Skipping citations (use --include-citations to download)")

    # Download inventors
    if args.include_inventors:
        print(f"\n[4/4] Downloading inventor data...")
        patent_ids = df_patents["patent_id"].dropna().astype(str).tolist()
        df_inventors = download_inventors_for_patents(client, patent_ids)
        inventors_path = output_dir / "inventors.parquet"
        df_inventors.to_parquet(inventors_path, index=False)
        print(f"  Saved {len(df_inventors):,} records to {inventors_path}")
    else:
        print(f"\n[4/4] Skipping inventors (use --include-inventors to download)")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  Download complete!")
    print(f"  Data saved to: {output_dir}")
    print(f"  Sample: {args.sample_size:,} patents, "
          f"date range: {args.year_start}-{args.year_end}")
    print()
    print(f"  Next steps:")
    print(f"    1. Verify: python scripts/download_patentsview.py --sample-size 10 --health-check")
    print(f"    2. Read the README at: {output_dir}/README.md")
    print(f"    3. For larger samples use --sample-size N")
    print(f"{'=' * 70}")


if __name__ == "__main__":
    main()
