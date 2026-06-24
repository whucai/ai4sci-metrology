#!/usr/bin/env python3
"""
Download SciSciNet datasets from HuggingFace to data/sciscinet/

Datasets downloaded:
  1. cssi/SciSciGPT-SciSciNet  — Official SciSciGPT companion dataset
     Key files: paper_patents.parquet, papers/shard_*.parquet,
                paper_citations.parquet, authors.parquet, fields.parquet,
                institutions.parquet

  2. Northwestern-CSSI/sciscinet-v2 — Refreshed SciSciNet v2
     Key files: sciscinet_link_patents.parquet, sciscinet_paperrefs.parquet,
                sciscinet_authors.parquet, sciscinet_affiliations.parquet,
                hit_papers_level0.parquet, hit_papers_level1.parquet

Usage:
    python scripts/download_sciscinet.py                    # Download both datasets
    python scripts/download_sciscinet.py --dataset sciscigpt  # Only SciSciGPT-SciSciNet
    python scripts/download_sciscinet.py --dataset v2         # Only sciscinet-v2
    python scripts/download_sciscinet.py --dry-run           # List files only

Requires: pip install huggingface_hub pandas pyarrow tqdm
"""

import os
import sys
import argparse
import time
from pathlib import Path

# Ensure proxy is set before importing huggingface_hub
PROXY = "http://127.0.0.1:7897"
os.environ.setdefault("all_proxy", PROXY)
os.environ.setdefault("ALL_PROXY", PROXY)
os.environ.setdefault("http_proxy", PROXY)
os.environ.setdefault("https_proxy", PROXY)

# HF token for gated datasets (set via env or pass explicitly)
HF_TOKEN = os.environ.get("HF_TOKEN", "")

from huggingface_hub import hf_hub_download, list_repo_files, snapshot_download

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "data" / "sciscinet"

# ---- Dataset definitions ----

SCISCIGPT_DATASET = "cssi/SciSciGPT-SciSciNet"
SCISCIGPT_PRIORITY_FILES = [
    "paper_patents.parquet",
    "paper_citations.parquet",
    "authors.parquet",
    "fields.parquet",
    "institutions.parquet",
    "paper_fields.parquet",
    "paper_author_affiliations.parquet",
    "nct.parquet",
    "nih.parquet",
    "nsf.parquet",
    "newsfeed.parquet",
    "paper_nct.parquet",
    "paper_nih.parquet",
    "paper_nsf.parquet",
    "paper_newsfeed.parquet",
    "paper_twitter.parquet",
]

SCISCINET_V2 = "Northwestern-CSSI/sciscinet-v2"
SCISCINET_V2_PRIORITY = [
    "sciscinet_link_patents.parquet",
    "sciscinet_paperrefs.parquet",
    "sciscinet_authors.parquet",
    "sciscinet_author_details.parquet",
    "sciscinet_authors_paperid.parquet",
    "sciscinet_affiliations.parquet",
    "sciscinet_affl_assoc_affl.parquet",
    "sciscinet_paper_author_affiliation.parquet",
    "sciscinet_paperfields.parquet",
    "sciscinet_fields.parquet",
    "hit_papers_level0.parquet",
    "hit_papers_level1.parquet",
    "normalized_citations_level0.parquet",
    "normalized_citations_level1.parquet",
    "sciscinet_link_clinicaltrials.parquet",
    "sciscinet_link_newsfeed.parquet",
    "sciscinet_link_nih.parquet",
    "sciscinet_link_nsf.parquet",
    "sciscinet_link_nobellaureates.parquet",
    "sciscinet_clinicaltrials_metadata.parquet",
    "sciscinet_newsfeed_metadata.parquet",
    "sciscinet_nih_metadata.parquet",
    "sciscinet_nsf_metadata.parquet",
]


def list_all_files(dataset_id: str) -> list[str]:
    """List all files in a HuggingFace dataset repo."""
    try:
        files = list_repo_files(dataset_id, repo_type="dataset")
        return files
    except Exception as e:
        print(f"  Error listing files: {e}")
        return []


def download_file(dataset_id: str, filename: str, output_dir: Path) -> bool:
    """Download a single file from HuggingFace. Returns True on success."""
    output_path = output_dir / filename
    output_path.parent.mkdir(parents=True, exist_ok=True)

    if output_path.exists():
        size_mb = output_path.stat().st_size / 1024 / 1024
        print(f"    [skip] {filename} ({size_mb:.1f} MB)")
        return True

    max_retries = 3
    for attempt in range(max_retries):
        try:
            kwargs = {
                "repo_id": dataset_id,
                "filename": filename,
                "repo_type": "dataset",
                "local_dir": output_dir,
                "local_dir_use_symlinks": False,
            }
            if HF_TOKEN:
                kwargs["token"] = HF_TOKEN
            path = hf_hub_download(**kwargs)
            size_mb = Path(path).stat().st_size / 1024 / 1024
            print(f"    [OK] {filename} ({size_mb:.1f} MB)")
            return True
        except Exception as e:
            if attempt < max_retries - 1:
                wait = 2 ** attempt * 5
                print(f"    [retry {attempt+1}/{max_retries}] {filename}: {e} (waiting {wait}s)")
                time.sleep(wait)
            else:
                print(f"    [FAIL] {filename}: {e}")
                return False
    return False


def download_dataset(dataset_id: str, priority_files: list[str],
                     output_dir: Path, download_papers: bool = True,
                     max_paper_shards: int = 100) -> dict:
    """Download a HuggingFace dataset. Returns stats dict."""
    print(f"\n{'='*70}")
    print(f"  Dataset: {dataset_id}")
    print(f"  Output:  {output_dir}")
    print(f"{'='*70}")

    output_dir.mkdir(parents=True, exist_ok=True)

    # List all files
    print("\n[1/3] Listing files...")
    all_files = list_all_files(dataset_id)
    if not all_files:
        print("  ERROR: Could not list files (check proxy/internet)")
        return {"error": "list_failed"}

    paper_files = [f for f in all_files if f.startswith("papers/")]
    patent_files = [f for f in all_files if f.startswith("patents/")]
    other_files = [f for f in all_files
                   if not f.startswith("papers/")
                   and not f.startswith("patents/")
                   and f != ".gitattributes" and f != "README.md"]

    print(f"  Total: {len(all_files)} files")
    print(f"  Papers: {len(paper_files)} shards")
    print(f"  Patents: {len(patent_files)} shards")
    print(f"  Other: {len(other_files)} files")

    # Stats
    stats = {"downloaded": 0, "skipped": 0, "failed": 0, "total_mb": 0.0}

    # Download priority files
    print(f"\n[2/3] Downloading metadata files...")
    for fname in other_files:
        # Only download priority files + any that match
        priority_set = set(priority_files)
        if fname in priority_set or any(fname.endswith(p) for p in priority_files):
            ok = download_file(dataset_id, fname, output_dir)
            if ok:
                if (output_dir / fname).exists():
                    stats["total_mb"] += (output_dir / fname).stat().st_size / 1024 / 1024
                stats["downloaded" if not (output_dir / fname).exists() or
                        (output_dir / fname).stat().st_size > 0 else "skipped"] += 1
            else:
                stats["failed"] += 1
        else:
            # Still download if it's in the original priority list match
            pass

    # Actually download ALL non-paper files to be thorough
    for fname in other_files:
        if not (output_dir / fname).exists():
            ok = download_file(dataset_id, fname, output_dir)
            if ok:
                stats["total_mb"] += (output_dir / fname).stat().st_size / 1024 / 1024
                stats["downloaded"] += 1
            else:
                stats["failed"] += 1
        else:
            stats["skipped"] += 1
            stats["total_mb"] += (output_dir / fname).stat().st_size / 1024 / 1024

    # Download paper shards
    if download_papers and paper_files:
        n_shards = min(len(paper_files), max_paper_shards)
        print(f"\n[3/4] Downloading paper shards ({n_shards} files)...")
        for fname in paper_files[:n_shards]:
            ok = download_file(dataset_id, fname, output_dir)
            if ok:
                stats["downloaded"] += 1
                if (output_dir / fname).exists():
                    stats["total_mb"] += (output_dir / fname).stat().st_size / 1024 / 1024
            else:
                stats["failed"] += 1

    # Download patent shards
    if download_papers and patent_files:
        n_shards = min(len(patent_files), max_paper_shards)
        print(f"\n[4/4] Downloading patent shards ({n_shards} files)...")
        for fname in patent_files[:n_shards]:
            ok = download_file(dataset_id, fname, output_dir)
            if ok:
                stats["downloaded"] += 1
                if (output_dir / fname).exists():
                    stats["total_mb"] += (output_dir / fname).stat().st_size / 1024 / 1024
            else:
                stats["failed"] += 1

    return stats


def main():
    parser = argparse.ArgumentParser(
        description="Download SciSciNet datasets from HuggingFace"
    )
    parser.add_argument("--dataset", type=str, default="all",
                        choices=["all", "sciscigpt", "v2"],
                        help="Which dataset to download (default: all)")
    parser.add_argument("--output-dir", type=str, default=str(OUTPUT_DIR),
                        help="Output directory")
    parser.add_argument("--dry-run", action="store_true",
                        help="Only list files, don't download")
    parser.add_argument("--max-shards", type=int, default=100,
                        help="Max paper shards to download (default: all)")
    parser.add_argument("--skip-papers", action="store_true",
                        help="Skip paper shards (download metadata only)")
    args = parser.parse_args()

    output_dir = Path(args.output_dir)
    print("=" * 70)
    print("  SciSciNet Data Downloader")
    print(f"  Output: {output_dir}")
    print(f"  Proxy:  {PROXY}")
    print("=" * 70)

    # Download SciSciGPT-SciSciNet
    if args.dataset in ("all", "sciscigpt"):
        if args.dry_run:
            files = list_all_files(SCISCIGPT_DATASET)
            print(f"\n{SCISCIGPT_DATASET}: {len(files)} files")
            for f in files:
                print(f"  {f}")
        else:
            stats = download_dataset(
                SCISCIGPT_DATASET,
                SCISCIGPT_PRIORITY_FILES,
                output_dir,
                download_papers=not args.skip_papers,
                max_paper_shards=args.max_shards,
            )
            print(f"\n  SciSciGPT-SciSciNet stats: {stats}")

    # Download sciscinet-v2
    if args.dataset in ("all", "v2"):
        v2_dir = output_dir / "v2"
        if args.dry_run:
            files = list_all_files(SCISCINET_V2)
            print(f"\n{SCISCINET_V2}: {len(files)} files")
            for f in files:
                print(f"  {f}")
        else:
            stats = download_dataset(
                SCISCINET_V2,
                SCISCINET_V2_PRIORITY,
                v2_dir,
                download_papers=False,  # v2 has no paper shards
            )
            print(f"\n  sciscinet-v2 stats: {stats}")

    # Summary
    if not args.dry_run:
        print(f"\n{'='*70}")
        print(f"  Download complete!")
        print(f"  Data saved to: {output_dir}")
        print(f"")

        # Quick verification
        print(f"  Quick verification...")
        for f in sorted(output_dir.rglob("*.parquet")):
            size_mb = f.stat().st_size / 1024 / 1024
            print(f"    {f.relative_to(output_dir)}  ({size_mb:.1f} MB)")

        print(f"\n  Total files: {sum(1 for _ in output_dir.rglob('*.parquet'))}")
        total_gb = sum(f.stat().st_size for f in output_dir.rglob("*.parquet")) / 1024 / 1024 / 1024
        print(f"  Total size:  {total_gb:.2f} GB")
        print(f"{'='*70}")


if __name__ == "__main__":
    main()
