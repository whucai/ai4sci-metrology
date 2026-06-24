#!/usr/bin/env python3
"""Bulk pipeline: select papers → download PDFs → convert to markdown → register.

Extends the benchmark from 13 to ~100 methodology papers.

Usage:
    python scripts/bulk_expand_benchmark.py --select-only     # Select papers, save list
    python scripts/bulk_expand_benchmark.py --download-only   # Download PDFs for selected
    python scripts/bulk_expand_benchmark.py --convert-only    # Convert PDFs to markdown
    python scripts/bulk_expand_benchmark.py --register-only   # Register in benchmark
    python scripts/bulk_expand_benchmark.py --all             # Full pipeline
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
import time
import urllib.request
from pathlib import Path
from collections import Counter
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parent.parent
BENCHMARK_DIR = PROJECT_ROOT / "bench-mark"
FILTERED_PATH = BENCHMARK_DIR / "filtered_results.json"
SELECTED_PATH = BENCHMARK_DIR / "selected_papers.json"
METADATA_PATH = BENCHMARK_DIR / "paper_metadata.json"

# ── Metric type assignment plan (target: ~87 new papers) ─────────────
METRIC_QUOTA: dict[str, int] = {
    "disruption": 20,
    "disruption_temporal": 5,
    "team_size_effect": 8,
    "citation_inflation": 4,
    "citation_count_prediction": 5,
    "network_normalized_impact": 8,
    "frontier_author_impact": 5,
    "sleeping_beauty": 5,
    "career_mobility": 8,
    "novelty_conventionality": 5,
    "interdisciplinarity": 5,
    "altmetrics": 5,
}

# Map search source labels to metric types
SOURCE_TO_METRIC: dict[str, str] = {
    "disruption_index_core": "disruption",
    "disruption_variants": "disruption",
    "citation_analysis": "disruption",
    "citation_distributions": "citation_count_prediction",
    "citation_inflation": "citation_inflation",
    "team_size": "team_size_effect",
    "collaboration": "team_size_effect",
    "collab_creativity": "team_size_effect",
    "sleeping_beauty": "sleeping_beauty",
    "delayed_recognition": "sleeping_beauty",
    "altmetrics": "altmetrics",
    "social_media_metrics": "altmetrics",
    "peer_review": "disruption",
    "research_evaluation": "disruption",
    "science_of_science": "disruption",
    "sci_sci_innovation": "disruption",
    "knowledge_diffusion": "network_normalized_impact",
    "knowledge_flows": "network_normalized_impact",
    "interdisciplinarity": "interdisciplinarity",
    "interdisciplinary_research": "interdisciplinarity",
    "gender_diversity": "team_size_effect",
    "career_dynamics": "career_mobility",
    "career_trajectories": "career_mobility",
    "scientist_mobility": "career_mobility",
    "age_productivity": "career_mobility",
    "novelty_metrics": "novelty_conventionality",
    "conventionality": "novelty_conventionality",
    "journal_impact": "disruption",
    "journal_ranking": "disruption",
    "science_mapping": "disruption",
    "patent_science": "disruption",
    "retraction": "disruption",
    "reproducibility": "disruption",
    "funding_productivity": "frontier_author_impact",
    "obsolescence": "disruption_temporal",
    "citation_network": "network_normalized_impact",
    "cocitation": "network_normalized_impact",
    "bibliometric_indicators": "disruption",
    "h_index_variants": "disruption",
    "open_access": "disruption",
    "self_citation": "disruption",
    "predatory_publishing": "disruption",
    "conf_journal": "disruption",
    "knowledge_recombination": "disruption",
    "research_policy": "disruption",
    "network_metrics": "network_normalized_impact",
    "breakthrough": "frontier_author_impact",
    "null_results": "disruption",
}

# Journal name mapping for priority classification
HIGH_PRIORITY_KEYWORDS = [
    "scientometric", "informetric", "quantitative science",
    "research policy", "research evaluation", "PLoS ONE",
    "eLife", "PeerJ", "EPJ Data", "JASIST", "JASIS",
    "management science", "nature", "science", "PNAS",
    "proceedings of the national academy",
    "science advances", "royal society",
    "journal of technology transfer", "technovation",
    "research policy", "industrial and corporate change",
    "social studies of science", "science technology",
    "american sociological review", "american journal of sociology",
]

# Journals to categorize papers into
JOURNAL_DIRS: dict[str, str] = {
    "Scientometrics": "Scientometrics",
    "Journal of Informetrics": "Scientometrics",
    "Quantitative Science Studies": "Scientometrics",
    "Research Policy": "Research Policy",
    "Research Evaluation": "Research Policy",
    "PLoS ONE": "PLoS ONE",
    "Nature": "Nature",
    "Science": "Science",
    "PNAS": "PNAS",
    "Proceedings of the National Academy": "PNAS",
    "Science Advances": "Science Advances",
    "eLife": "eLife",
    "Management Science": "Management Science",
    "JASIST": "JASIST",
    "EPJ Data Science": "EPJ Data Science",
    "Royal Society": "Royal Society",
    "PeerJ": "PeerJ",
}


def select_papers(target_total: int = 100) -> list[dict]:
    """Select diverse papers from filtered results."""
    if not FILTERED_PATH.exists():
        print(f"ERROR: {FILTERED_PATH} not found. Run search_bib_papers.py first.")
        sys.exit(1)

    data = json.loads(FILTERED_PATH.read_text())
    all_papers = data["papers"]
    print(f"Input: {len(all_papers)} filtered papers")

    # Assign metric types based on source
    for p in all_papers:
        source = p.get("source_label", "")
        p["assigned_metric"] = SOURCE_TO_METRIC.get(source, "disruption")

    # Group by assigned metric
    by_metric: dict[str, list[dict]] = {}
    for p in all_papers:
        mt = p["assigned_metric"]
        by_metric.setdefault(mt, []).append(p)

    print(f"\nAvailable by metric type:")
    for mt, papers in sorted(by_metric.items()):
        print(f"  {mt}: {len(papers)} available (quota: {METRIC_QUOTA.get(mt, 0)})")

    # Select papers to fill quotas, prioritizing:
    # 1. Papers with journal references (published, not just preprint)
    # 2. Higher citation count (more recent is proxy since we don't have real citations)
    # 3. Diversity in years

    selected: list[dict] = []
    seen_ids: set[str] = set()

    for mt, quota in METRIC_QUOTA.items():
        pool = by_metric.get(mt, [])
        # Sort: papers with journal_ref first, then by recency
        pool_sorted = sorted(pool, key=lambda p: (
            -(1 if p.get("journal_ref", "").strip() else 0),
            -p.get("year", 0),
        ))

        count = 0
        for p in pool_sorted:
            aid = p["arxiv_id_clean"]
            if aid in seen_ids:
                continue
            if count >= quota:
                break
            p["assigned_metric"] = mt
            selected.append(p)
            seen_ids.add(aid)
            count += 1

        if count < quota:
            print(f"  WARNING: {mt}: only selected {count}/{quota}")

    # Fill remaining slots with additional papers from disruption
    existing_total = 13
    remaining = target_total - existing_total - len(selected)
    if remaining > 0:
        extra_pool = [p for p in all_papers
                      if p["arxiv_id_clean"] not in seen_ids]
        extra_pool.sort(key=lambda p: -p.get("year", 0))
        for p in extra_pool:
            if len(selected) >= target_total - existing_total:
                break
            p["assigned_metric"] = "disruption"
            selected.append(p)
            seen_ids.add(p["arxiv_id_clean"])

    print(f"\nSelected {len(selected)} new papers (target: {target_total} total, {existing_total} existing)")

    # Stats
    mt_counts = Counter(p["assigned_metric"] for p in selected)
    print("\nBy metric type:")
    for mt, count in mt_counts.most_common():
        print(f"  {mt}: {count}")

    year_counts = Counter(p.get("year", 0) for p in selected)
    print(f"\nYear distribution:")
    for y in sorted(year_counts):
        print(f"  {y}: {year_counts[y]}", end="")
        if y % 5 == 0:
            print()
    print()

    # Save
    output = {
        "selected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_existing": existing_total,
        "total_new": len(selected),
        "target_total": target_total,
        "papers": selected,
    }
    SELECTED_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\nSaved selection to {SELECTED_PATH}")

    return selected


def download_pdfs():
    """Download PDFs for selected papers."""
    if not SELECTED_PATH.exists():
        print("ERROR: No selected papers. Run --select-only first.")
        sys.exit(1)

    data = json.loads(SELECTED_PATH.read_text())
    papers = data["papers"]
    print(f"Downloading PDFs for {len(papers)} papers...")

    others_dir = BENCHMARK_DIR / "others"
    others_dir.mkdir(parents=True, exist_ok=True)

    success = 0
    for i, paper in enumerate(papers, 1):
        aid = paper["arxiv_id"]
        pdf_path = others_dir / f"{aid.replace('/', '_')}.pdf"

        if pdf_path.exists():
            size_kb = pdf_path.stat().st_size / 1024
            if size_kb > 10:  # >10KB, probably not corrupted
                print(f"[{i}/{len(papers)}] EXISTS ({size_kb:.0f}KB): {aid}")
                success += 1
                continue

        url = f"https://arxiv.org/pdf/{aid}.pdf"
        print(f"[{i}/{len(papers)}] Downloading {aid}...", end=" ", flush=True)
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AI4SciMetrology/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                pdf_data = resp.read()
            pdf_path.write_bytes(pdf_data)
            size_kb = len(pdf_data) / 1024
            print(f"OK ({size_kb:.0f}KB)")
            success += 1
        except Exception as e:
            print(f"FAIL: {e}")

        time.sleep(0.5)

    print(f"\nDownloaded {success}/{len(papers)} PDFs")


def convert_pdfs():
    """Convert PDFs to markdown using MinerU (magic_pdf)."""
    if not SELECTED_PATH.exists():
        print("ERROR: No selected papers. Run --select-only first.")
        sys.exit(1)

    data = json.loads(SELECTED_PATH.read_text())
    papers = data["papers"]
    others_dir = BENCHMARK_DIR / "others"

    # Check if magic_pdf is available
    try:
        from magic_pdf.tools.common import do_parse
    except ImportError:
        print("ERROR: magic_pdf not available. Install MinerU first.")
        print("  pip install magic-pdf")
        sys.exit(1)

    success = 0
    for i, paper in enumerate(papers, 1):
        aid = paper["arxiv_id"]
        pdf_path = others_dir / f"{aid.replace('/', '_')}.pdf"
        md_path = others_dir / f"{aid.replace('/', '_')}.md"

        if not pdf_path.exists():
            print(f"[{i}/{len(papers)}] SKIP (no PDF): {aid}")
            continue

        if md_path.exists() and md_path.stat().st_size > 100:
            print(f"[{i}/{len(papers)}] EXISTS ({md_path.stat().st_size} chars): {aid}")
            success += 1
            continue

        print(f"[{i}/{len(papers)}] Converting {aid}...", end=" ", flush=True)
        try:
            do_parse(
                pdf_path=str(pdf_path),
                output_dir=str(others_dir),
                method="auto",
                lang="en",
                output_format="md",
            )
            # magic_pdf saves with a different name pattern, find it
            # Usually: {pdf_stem}/{pdf_stem}.md
            actual_md = others_dir / aid.replace('/', '_') / f"{aid.replace('/', '_')}.md"
            if actual_md.exists() and actual_md != md_path:
                import shutil
                shutil.copy(actual_md, md_path)
            if md_path.exists():
                print(f"OK ({md_path.stat().st_size} chars)")
                success += 1
            else:
                print("WARN (no output)")
        except Exception as e:
            print(f"FAIL: {e}")

    print(f"\nConverted {success}/{len(papers)} PDFs to markdown")


def classify_journal(paper: dict) -> str:
    """Assign a journal directory based on journal_ref or title."""
    jref = paper.get("journal_ref", "").lower()
    title = paper.get("title", "").lower()

    # Check for explicit journal reference
    for name, directory in JOURNAL_DIRS.items():
        if name.lower() in jref:
            return directory

    # Check in title
    for name, directory in JOURNAL_DIRS.items():
        if name.lower() in title:
            return directory

    # Check author list for journal mentions (unlikely but try)
    for kw, directory in [("scientometric", "Scientometrics"),
                           ("informetric", "Scientometrics"),
                           ("research policy", "Research Policy")]:
        if kw in jref:
            return directory

    return "arXiv"


def register_papers():
    """Register converted papers in the benchmark."""
    if not SELECTED_PATH.exists():
        print("ERROR: No selected papers. Run --select-only first.")
        sys.exit(1)

    data = json.loads(SELECTED_PATH.read_text())
    papers = data["papers"]
    others_dir = BENCHMARK_DIR / "others"

    # Load existing papers to avoid duplicates
    existing_ids: set[str] = set()
    if METADATA_PATH.exists():
        existing_meta = json.loads(METADATA_PATH.read_text())
        for entry in existing_meta:
            existing_ids.add(entry.get("arxiv_id", ""))

    new_entries = []
    registry_lines: list[str] = []
    ready_papers: list[str] = []

    for i, paper in enumerate(papers, 1):
        aid = paper.get("arxiv_id_clean", paper["arxiv_id"])
        if aid in existing_ids:
            continue

        md_filename = paper["arxiv_id"].replace("/", "_") + ".md"
        md_path = others_dir / md_filename

        if not md_path.exists():
            print(f"[{i}/{len(papers)}] SKIP (no .md): {aid}")
            continue

        # Determine journal directory
        journal_dir = classify_journal(paper)
        target_dir = BENCHMARK_DIR / journal_dir
        target_dir.mkdir(parents=True, exist_ok=True)

        # Move files from others/ to journal dir
        pdf_name = paper["arxiv_id"].replace("/", "_") + ".pdf"
        src_pdf = others_dir / pdf_name
        src_md = md_path
        dst_pdf = target_dir / pdf_name
        dst_md = target_dir / md_filename

        need_move = False
        if src_pdf.exists() and not dst_pdf.exists():
            import shutil
            shutil.copy(src_pdf, dst_pdf)
            need_move = True
        if src_md.exists() and not dst_md.exists():
            import shutil
            shutil.copy(src_md, dst_md)
            need_move = True

        # Generate paper ID
        paper_id = f"auto_{aid.replace('.', '_')}"

        # Build metadata entry
        authors = paper.get("authors", [])
        author_str = ", ".join(authors[:5])
        if len(authors) > 5:
            author_str += " et al."

        entry = {
            "path": str(dst_pdf.relative_to(BENCHMARK_DIR)) if dst_pdf.exists()
                   else str(src_pdf.relative_to(BENCHMARK_DIR)),
            "subdir": journal_dir,
            "title": paper.get("title", ""),
            "doi": paper.get("doi", ""),
            "arxiv_id": aid,
            "pages": 0,
            "chars": md_path.stat().st_size if md_path.exists() else 0,
            "md_path": str(dst_md.relative_to(BENCHMARK_DIR)) if dst_md.exists()
                       else str(src_md.relative_to(BENCHMARK_DIR)),
            "tags": paper.get("categories", []),
            "metric_type": paper.get("assigned_metric", "disruption"),
        }
        new_entries.append(entry)

        # Generate registry snippet
        metric_type = paper.get("assigned_metric", "disruption")
        year = paper.get("year", 0)
        title = paper.get("title", "").replace('"', '\\"')
        doi = paper.get("doi", "")
        journal_name = journal_dir.replace("_", " ") if journal_dir == "Research_Policy" else journal_dir

        reg_line = f'''    "{paper_id}": PaperEntry(
        id="{paper_id}",
        md_path="bench-mark/{journal_dir}/{md_filename}",
        title="{title}",
        journal="{journal_name}",
        year={year},
        doi="{doi}",
        metric_type="{metric_type}",
        requires_tables={{"papers"}},
        claims=[],
    ),'''
        registry_lines.append(reg_line)
        ready_papers.append(f'"{paper_id}"')

        print(f"[{i}/{len(papers)}] REGISTERED: {aid} → {journal_dir}/{md_filename} [{metric_type}]")

    # Update paper_metadata.json
    if METADATA_PATH.exists():
        all_meta = json.loads(METADATA_PATH.read_text())
    else:
        all_meta = []
    all_meta.extend(new_entries)
    METADATA_PATH.write_text(json.dumps(all_meta, indent=2, ensure_ascii=False))
    print(f"\nUpdated {METADATA_PATH} ({len(all_meta)} total entries)")

    # Print registry code to append
    reg_output_path = BENCHMARK_DIR / "new_registry_entries.py"
    reg_code = "# Auto-generated registry entries — append to PAPER_REGISTRY dict\n"
    reg_code += "# and add to READY_PAPERS set\n\n"
    reg_code += "# ── Registry entries ──\n"
    reg_code += "\n".join(registry_lines)
    reg_code += "\n\n# ── READY_PAPERS additions ──\n"
    reg_code += "# " + ", ".join(ready_papers) + "\n"
    reg_code += f"\n# Total: {len(registry_lines)} new papers\n"

    reg_output_path.write_text(reg_code)
    print(f"\nRegistry entries written to {reg_output_path}")
    print(f"Total new papers registered: {len(new_entries)}")
    print(f"Target total: ~{len(all_meta)} papers in benchmark")


def main():
    parser = argparse.ArgumentParser(description="Bulk expand benchmark to ~100 papers")
    parser.add_argument("--all", action="store_true", help="Run full pipeline")
    parser.add_argument("--select-only", action="store_true", help="Select papers from search results")
    parser.add_argument("--download-only", action="store_true", help="Download PDFs only")
    parser.add_argument("--convert-only", action="store_true", help="Convert PDFs to markdown only")
    parser.add_argument("--register-only", action="store_true", help="Register in benchmark only")
    parser.add_argument("--target", type=int, default=100, help="Target total papers")
    args = parser.parse_args()

    run_all = args.all or not any([
        args.select_only, args.download_only, args.convert_only, args.register_only,
    ])

    if run_all or args.select_only:
        select_papers(args.target)

    if run_all or args.download_only:
        download_pdfs()

    if run_all or args.convert_only:
        convert_pdfs()

    if run_all or args.register_only:
        register_papers()


if __name__ == "__main__":
    main()
