#!/usr/bin/env python3
"""Download high-impact bibliometrics papers from arXiv for the benchmark.

PAPERS:
  arxiv:2306.14364  Bentley et al. 2023 — Is disruption decreasing, or is it accelerating?
  arxiv:2308.16363  Gebhart & Funk 2023 — A Mathematical Framework for Citation Disruption
  arxiv:1505.06454  Ke et al. 2015 — Defining and Identifying Sleeping Beauties in Science
  arxiv:2207.11116  Traag 2022 — Citation models and research evaluation
  arxiv:2303.15988  — Ranking mobility and impact inequality in early academic careers
  arxiv:2301.04369  Akella et al. 2023 — Reproducibility Signals in Science
  arxiv:2405.03977  Obadage et al. 2024 — Citations and reproducibility of ML papers
  arxiv:2308.00405  — Who benefits from altmetrics?

Usage:
    python scripts/download_bib_papers.py              # download all
    python scripts/download_bib_papers.py --list       # list papers
    python scripts/download_bib_papers.py --ids 2306.14364,1505.06454  # specific papers
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
from pathlib import Path
from xml.etree import ElementTree

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "bench-mark" / "others"
METADATA_PATH = PROJECT_ROOT / "bench-mark" / "paper_metadata.json"

TARGET_PAPERS: list[dict] = [
    {
        "arxiv_id": "2306.14364",
        "title": "Is disruption decreasing, or is it accelerating?",
        "authors": "Bentley, R.A., Valverde, S., Borycz, J., Vidiella, B., Horne, B.D., Duran-Nebreda, S., O'Brien, M.J.",
        "year": 2023,
        "journal": "Advances in Complex Systems",
        "doi": "10.1142/S0219525923500066",
        "metric_type": "disruption_temporal",
        "tags": ["disruption", "citation-weighting", "replication"],
    },
    {
        "arxiv_id": "2308.16363",
        "title": "A Mathematical Framework for Citation Disruption",
        "authors": "Gebhart, T., Funk, R.J.",
        "year": 2023,
        "journal": "arXiv preprint",
        "doi": "",
        "metric_type": "disruption",
        "tags": ["disruption", "network-centrality", "mathematical-framework"],
    },
    {
        "arxiv_id": "1505.06454",
        "title": "Defining and Identifying Sleeping Beauties in Science",
        "authors": "Ke, Q., Ferrara, E., Radicchi, F., Flammini, A.",
        "year": 2015,
        "journal": "PNAS",
        "doi": "10.1073/pnas.1424329112",
        "metric_type": "sleeping_beauty",
        "tags": ["delayed-recognition", "beauty-coefficient", "citation-dynamics"],
    },
    {
        "arxiv_id": "2207.11116",
        "title": "Citation models and research evaluation",
        "authors": "Traag, V.A.",
        "year": 2022,
        "journal": "arXiv preprint",
        "doi": "",
        "metric_type": "citation_models",
        "tags": ["citation-distributions", "research-evaluation", "review"],
    },
    {
        "arxiv_id": "2303.15988",
        "title": "Ranking mobility and impact inequality in early academic careers",
        "authors": "Sun, Y., Caccioli, F., Li, X., Livan, G.",
        "year": 2023,
        "journal": "PNAS",
        "doi": "10.1073/pnas.2301537120",
        "metric_type": "ranking_mobility",
        "tags": ["Matthew-effect", "career-dynamics", "impact-inequality"],
    },
    {
        "arxiv_id": "2301.04369",
        "title": "Reproducibility Signals in Science: A preliminary analysis",
        "authors": "Akella, A.P., Alhoori, H., Koop, D.",
        "year": 2023,
        "journal": "arXiv preprint",
        "doi": "",
        "metric_type": "reproducibility_signals",
        "tags": ["reproducibility", "scholarly-communication", "feature-analysis"],
    },
    {
        "arxiv_id": "2405.03977",
        "title": "Can citations tell us about a paper's reproducibility? A case study of ML papers",
        "authors": "Obadage, R.R., Rajtmajer, S.M., Wu, J.",
        "year": 2024,
        "journal": "arXiv preprint",
        "doi": "",
        "metric_type": "citation_reproducibility",
        "tags": ["citation-context", "reproducibility", "sentiment-analysis"],
    },
    {
        "arxiv_id": "2308.00405",
        "title": "Who benefits from altmetrics? The effect of team gender composition",
        "authors": "",
        "year": 2023,
        "journal": "arXiv preprint",
        "doi": "",
        "metric_type": "altmetrics_gender",
        "tags": ["altmetrics", "gender-bias", "team-composition"],
    },
]


def fetch_arxiv_metadata(arxiv_id: str) -> dict | None:
    """Fetch paper metadata from arXiv API."""
    url = f"http://export.arxiv.org/api/query?id_list={arxiv_id}&max_results=1"
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI4SciMetrology/1.0"})
        with urllib.request.urlopen(req, timeout=30) as resp:
            xml_data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  WARNING: arXiv API query failed: {e}")
        return None

    root = ElementTree.fromstring(xml_data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    entry = root.find("atom:entry", ns)
    if entry is None:
        return None

    title_el = entry.find("atom:title", ns)
    title = title_el.text.strip() if title_el is not None and title_el.text else ""

    authors = []
    for author_el in entry.findall("atom:author", ns):
        name_el = author_el.find("atom:name", ns)
        if name_el is not None and name_el.text:
            authors.append(name_el.text.strip())

    published_el = entry.find("atom:published", ns)
    year = int(published_el.text[:4]) if published_el is not None and published_el.text else 0

    return {
        "arxiv_id": arxiv_id,
        "title": title,
        "authors": authors,
        "year": year,
    }


def download_pdf(arxiv_id: str, output_dir: Path) -> Path | None:
    """Download PDF from arXiv. Returns path or None."""
    pdf_path = output_dir / f"{arxiv_id.replace('/', '_')}.pdf"
    if pdf_path.exists():
        print(f"  Already exists: {pdf_path.name}")
        return pdf_path

    url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"
    print(f"  Downloading {url} ...")
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI4SciMetrology/1.0"})
        with urllib.request.urlopen(req, timeout=120) as resp:
            pdf_data = resp.read()
        pdf_path.write_bytes(pdf_data)
        size_kb = len(pdf_data) / 1024
        print(f"  Saved {pdf_path.name} ({size_kb:.0f} KB)")
        return pdf_path
    except Exception as e:
        print(f"  ERROR downloading {arxiv_id}: {e}")
        return None


def update_metadata(pdf_path: Path, paper_info: dict) -> None:
    """Append or update paper entry in paper_metadata.json."""
    if METADATA_PATH.exists():
        metadata = json.loads(METADATA_PATH.read_text())
    else:
        metadata = []

    subdir = str(pdf_path.parent.relative_to(PROJECT_ROOT / "bench-mark"))
    rel_path = str(pdf_path.relative_to(PROJECT_ROOT / "bench-mark"))

    # Check if already exists
    for entry in metadata:
        if entry.get("path") == rel_path:
            print(f"  Already in metadata: {rel_path}")
            return

    entry = {
        "path": rel_path,
        "subdir": subdir,
        "title": paper_info.get("title", ""),
        "doi": paper_info.get("doi", ""),
        "arxiv_id": paper_info.get("arxiv_id", ""),
        "pages": 0,
        "chars": 0,
        "md_path": rel_path.replace(".pdf", ".md"),
        "tags": paper_info.get("tags", []),
        "metric_type": paper_info.get("metric_type", ""),
    }
    metadata.append(entry)
    METADATA_PATH.write_text(json.dumps(metadata, indent=2, ensure_ascii=False))
    print(f"  Added to metadata: {rel_path}")


def main():
    parser = argparse.ArgumentParser(description="Download bibliometrics papers from arXiv")
    parser.add_argument("--list", action="store_true", help="List target papers and exit")
    parser.add_argument("--ids", type=str, default="", help="Comma-separated arXiv IDs")
    parser.add_argument("--no-metadata", action="store_true", help="Skip metadata update")
    args = parser.parse_args()

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    if args.list:
        print(f"\n{'='*80}")
        print(f"Target papers ({len(TARGET_PAPERS)}):")
        print(f"{'='*80}")
        for i, p in enumerate(TARGET_PAPERS, 1):
            print(f"\n{i}. arXiv:{p['arxiv_id']}")
            print(f"   Title: {p['title']}")
            print(f"   Authors: {p.get('authors', 'N/A')}")
            print(f"   Year: {p.get('year', 'N/A')} | Journal: {p.get('journal', 'N/A')}")
            print(f"   Tags: {', '.join(p.get('tags', []))}")
        return

    # Filter papers
    if args.ids:
        id_set = {i.strip() for i in args.ids.split(",")}
        papers = [p for p in TARGET_PAPERS if p["arxiv_id"] in id_set]
        print(f"Selected {len(papers)}/{len(TARGET_PAPERS)} papers by ID filter")
    else:
        papers = TARGET_PAPERS
        print(f"Downloading all {len(papers)} target papers")

    success = 0
    for i, paper in enumerate(papers, 1):
        arxiv_id = paper["arxiv_id"]
        print(f"\n[{i}/{len(papers)}] arXiv:{arxiv_id} — {paper['title'][:80]}")

        # Fetch live metadata from arXiv
        live_meta = fetch_arxiv_metadata(arxiv_id)
        if live_meta:
            paper["title"] = live_meta["title"]
            paper["authors"] = ", ".join(live_meta["authors"])
            paper["year"] = paper.get("year") or live_meta["year"]
            print(f"  Title: {paper['title'][:100]}")
            print(f"  Authors: {paper['authors'][:120]}")
            print(f"  Year: {paper['year']}")
        else:
            print(f"  Using local metadata (arXiv API unreachable)")

        pdf_path = download_pdf(arxiv_id, OUTPUT_DIR)
        if pdf_path:
            success += 1
            if not args.no_metadata:
                update_metadata(pdf_path, paper)

        time.sleep(1)  # Be polite to arXiv

    print(f"\n{'='*60}")
    print(f"Done. Downloaded {success}/{len(papers)} papers to {OUTPUT_DIR}")
    print(f"Next: convert PDFs to markdown (MinerU or similar) and update registry")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
