#!/usr/bin/env python3
"""Search arXiv for bibliometrics / Science of Science papers.

Searches multiple queries across cs.DL, physics.soc-ph, stat.AP and collects
unique paper metadata for the benchmark expansion to ~100 papers.

Usage:
    python scripts/search_bib_papers.py                    # search + save results
    python scripts/search_bib_papers.py --list             # show results
    python scripts/search_bib_papers.py --download         # download PDFs
    python scripts/search_bib_papers.py --max 200          # max results per query
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
import urllib.request
import urllib.parse
from pathlib import Path
from xml.etree import ElementTree

PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "bench-mark"
RESULTS_PATH = PROJECT_ROOT / "bench-mark" / "search_results.json"

# ── arXiv search queries ──────────────────────────────────────────────
# Each query targets a specific bibliometrics topic area
SEARCH_QUERIES: list[dict] = [
    # Core bibliometrics / disruption
    {
        "query": 'all:"disruption index" AND (all:bibliometric OR all:scientometric)',
        "label": "disruption_index_core",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"CD index" OR all:"disruption score" OR all:"disruptiveness"',
        "label": "disruption_variants",
        "metric_type": "disruption",
    },
    # Citation analysis
    {
        "query": 'all:"citation analysis" AND (all:science OR all:research)',
        "label": "citation_analysis",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"citation distributions" OR all:"citation dynamics" OR all:"citation behavior"',
        "label": "citation_distributions",
        "metric_type": "citation_count_prediction",
    },
    {
        "query": 'all:"citation inflation" OR all:"reference inflation" OR all:"citation bias"',
        "label": "citation_inflation",
        "metric_type": "citation_inflation",
    },
    # Team science
    {
        "query": 'all:"team size" AND all:science AND (all:disruption OR all:impact OR all:innovation)',
        "label": "team_size",
        "metric_type": "team_size_effect",
    },
    {
        "query": 'all:"scientific collaboration" AND (all:impact OR all:productivity OR all:creativity)',
        "label": "collaboration",
        "metric_type": "team_size_effect",
    },
    # Sleeping beauty / delayed recognition
    {
        "query": 'all:"sleeping beauty" AND (all:citation OR all:science)',
        "label": "sleeping_beauty",
        "metric_type": "sleeping_beauty",
    },
    {
        "query": 'all:"delayed recognition" AND (all:citation OR all:paper OR all:science)',
        "label": "delayed_recognition",
        "metric_type": "sleeping_beauty",
    },
    # Altmetrics / social media
    {
        "query": 'all:altmetrics AND (all:citation OR all:impact OR all:scholarly)',
        "label": "altmetrics",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"social media" AND (all:citation OR all:scholarly OR all:academic)',
        "label": "social_media_metrics",
        "metric_type": "disruption",
    },
    # Peer review / research evaluation
    {
        "query": 'all:"peer review" AND (all:metric OR all:quality OR all:prediction)',
        "label": "peer_review",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"research evaluation" AND (all:bibliometric OR all:indicator OR all:metric)',
        "label": "research_evaluation",
        "metric_type": "disruption",
    },
    # Science of Science (general)
    {
        "query": 'all:"science of science" AND (all:measure OR all:metric OR all:indicator OR all:quantify)',
        "label": "science_of_science",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"science of science" AND (all:disruption OR all:innovation OR all:impact)',
        "label": "sci_sci_innovation",
        "metric_type": "disruption",
    },
    # Knowledge diffusion / flows
    {
        "query": 'all:"knowledge diffusion" AND (all:patent OR all:citation OR all:science)',
        "label": "knowledge_diffusion",
        "metric_type": "network_normalized_impact",
    },
    {
        "query": 'all:"knowledge flows" AND (all:science OR all:technology OR all:patent)',
        "label": "knowledge_flows",
        "metric_type": "network_normalized_impact",
    },
    # Interdisciplinarity
    {
        "query": 'all:interdisciplinarity AND (all:measure OR all:metric OR all:indicator OR all:index)',
        "label": "interdisciplinarity",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"interdisciplinary research" AND (all:impact OR all:citation OR all:evaluation)',
        "label": "interdisciplinary_research",
        "metric_type": "disruption",
    },
    # Gender / diversity in science
    {
        "query": 'all:(gender OR diversity) AND all:science AND (all:citation OR all:productivity OR all:impact OR all:career)',
        "label": "gender_diversity",
        "metric_type": "disruption",
    },
    # Career dynamics
    {
        "query": 'all:"scientific career" AND (all:productivity OR all:impact OR all:mobility)',
        "label": "career_dynamics",
        "metric_type": "career_mobility",
    },
    {
        "query": 'all:"career" AND all:scientist AND (all:trajectory OR all:productivity OR all:impact)',
        "label": "career_trajectories",
        "metric_type": "career_mobility",
    },
    # Novelty / creativity metrics
    {
        "query": 'all:novelty AND (all:measure OR all:metric OR all:index) AND all:science',
        "label": "novelty_metrics",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"conventionality" OR all:"atypical combination" AND all:science',
        "label": "conventionality",
        "metric_type": "disruption",
    },
    # Journal impact / ranking
    {
        "query": 'all:"journal impact factor" AND (all:critique OR all:alternative OR all:limitation)',
        "label": "journal_impact",
        "metric_type": "disruption",
    },
    {
        "query": 'all:"journal ranking" AND (all:citation OR all:indicator OR all:bibliometric)',
        "label": "journal_ranking",
        "metric_type": "disruption",
    },
    # Science mapping / visualization
    {
        "query": 'all:"science mapping" AND (all:bibliometric OR all:visualization OR all:network)',
        "label": "science_mapping",
        "metric_type": "disruption",
    },
    # Patent-science linkage
    {
        "query": 'all:(patent AND science) AND (all:citation OR all:linkage OR all:knowledge)',
        "label": "patent_science",
        "metric_type": "disruption",
    },
    # Retraction / misconduct
    {
        "query": 'all:retraction AND (all:citation OR all:impact OR all:science)',
        "label": "retraction",
        "metric_type": "disruption",
    },
    # Reproducibility
    {
        "query": 'all:reproducibility AND all:science AND (all:metric OR all:measure OR all:assessment)',
        "label": "reproducibility",
        "metric_type": "disruption",
    },
    # Funding and productivity
    {
        "query": 'all:(funding OR grant) AND all:(productivity OR impact) AND all:science',
        "label": "funding_productivity",
        "metric_type": "disruption",
    },
    # Scientist mobility
    {
        "query": 'all:"scientist mobility" OR all:"researcher mobility" OR all:"academic mobility"',
        "label": "scientist_mobility",
        "metric_type": "career_mobility",
    },
    # Aging / obsolescence
    {
        "query": 'all:"obsolescence" AND (all:citation OR all:science OR all:knowledge)',
        "label": "obsolescence",
        "metric_type": "disruption_temporal",
    },
    # Network analysis of science
    {
        "query": 'all:"citation network" AND (all:analysis OR all:measure OR all:metric)',
        "label": "citation_network",
        "metric_type": "network_normalized_impact",
    },
    {
        "query": 'all:"co-citation" AND (all:analysis OR all:network OR all:cluster)',
        "label": "cocitation",
        "metric_type": "network_normalized_impact",
    },
    # Bibliometric indicators (general)
    {
        "query": 'all:"bibliometric indicator" AND (all:new OR all:novel OR all:improved OR all:proposed)',
        "label": "bibliometric_indicators",
        "metric_type": "disruption",
    },
    # h-index and variants
    {
        "query": 'all:"h-index" AND (all:variant OR all:limitation OR all:improvement OR all:alternative)',
        "label": "h_index_variants",
        "metric_type": "disruption",
    },
    # Open science / open access
    {
        "query": 'all:"open access" AND (all:citation OR all:impact OR all:advantage)',
        "label": "open_access",
        "metric_type": "disruption",
    },
    # Self-citation
    {
        "query": 'all:"self-citation" OR all:"self citation" AND (all:impact OR all:bias OR all:metric)',
        "label": "self_citation",
        "metric_type": "disruption",
    },
    # Predatory publishing
    {
        "query": 'all:"predatory" AND (all:journal OR all:publishing) AND (all:citation OR all:impact)',
        "label": "predatory_publishing",
        "metric_type": "disruption",
    },
    # Conference vs journal
    {
        "query": 'all:(conference OR journal) AND (all:citation AND all:impact AND all:computer science)',
        "label": "conf_journal",
        "metric_type": "disruption",
    },
    # Collaboration and creativity
    {
        "query": 'all:collaboration AND all:creativity AND (all:science OR all:research OR all:innovation)',
        "label": "collab_creativity",
        "metric_type": "team_size_effect",
    },
    # Aging and scientific impact
    {
        "query": 'all:"age" AND (all:productivity OR all:creativity) AND all:scientist',
        "label": "age_productivity",
        "metric_type": "career_mobility",
    },
    # Knowledge recombination
    {
        "query": 'all:"knowledge recombination" AND (all:innovation OR all:patent OR all:science)',
        "label": "knowledge_recombination",
        "metric_type": "disruption",
    },
    # Science policy / research policy
    {
        "query": 'all:"research policy" AND (all:bibliometric OR all:evaluation OR all:indicator)',
        "label": "research_policy",
        "metric_type": "disruption",
    },
    # Network-based metrics
    {
        "query": 'all:"network-based" AND (all:citation OR all:impact OR all:ranking)',
        "label": "network_metrics",
        "metric_type": "network_normalized_impact",
    },
    # Breakthrough / high-impact papers
    {
        "query": 'all:"breakthrough" AND (all:paper OR all:discovery OR all:innovation) AND (all:citation OR all:measure)',
        "label": "breakthrough",
        "metric_type": "disruption",
    },
    # Negative results / null findings
    {
        "query": 'all:"null result" OR all:"negative result" AND all:science AND (all:publication OR all:bias)',
        "label": "null_results",
        "metric_type": "disruption",
    },
]

# Already-owned arXiv IDs (from bench-mark/)
EXISTING_ARXIV_IDS = {
    "2306.14364", "2308.16363", "1505.06454", "2207.11116",
    "2303.15988", "2301.04369", "2405.03977", "2308.00405",
    "2306.01949", "2308.02383",
}

# Papers we DON'T want (false positives, preprints of already-owned papers, etc.)
EXCLUDE_ARXIV_IDS: set[str] = set()

# High-priority journals to prefer
PRIORITY_JOURNALS = {
    "Scientometrics", "Journal of Informetrics", "Quantitative Science Studies",
    "Research Policy", "Research Evaluation", "PLoS ONE", "eLife",
    "PeerJ", "Royal Society Open Science", "Science Advances",
    "EPJ Data Science", "Journal of the Association for Information Science and Technology",
}


def fetch_arxiv_results(query: str, max_results: int = 100, start: int = 0) -> list[dict]:
    """Search arXiv API and return paper metadata list."""
    encoded = urllib.parse.quote(query)
    url = (
        f"http://export.arxiv.org/api/query?"
        f"search_query={encoded}&start={start}&max_results={max_results}"
        f"&sortBy=relevance&sortOrder=descending"
    )
    try:
        req = urllib.request.Request(url, headers={"User-Agent": "AI4SciMetrology/1.0"})
        with urllib.request.urlopen(req, timeout=60) as resp:
            xml_data = resp.read().decode("utf-8")
    except Exception as e:
        print(f"  ERROR: {e}")
        return []

    root = ElementTree.fromstring(xml_data)
    ns = {
        "atom": "http://www.w3.org/2005/Atom",
        "arxiv": "http://arxiv.org/schemas/atom",
    }

    results = []
    for entry in root.findall("atom:entry", ns):
        arxiv_id_full = entry.find("atom:id", ns).text.strip()
        arxiv_id = arxiv_id_full.split("/abs/")[-1]
        # Remove version suffix
        arxiv_id_clean = arxiv_id.split("v")[0] if arxiv_id.count("v") >= 1 else arxiv_id

        title_el = entry.find("atom:title", ns)
        title = title_el.text.strip().replace("\n", " ") if title_el is not None else ""

        authors = []
        for author_el in entry.findall("atom:author", ns):
            name_el = author_el.find("atom:name", ns)
            if name_el is not None and name_el.text:
                authors.append(name_el.text.strip())

        published_el = entry.find("atom:published", ns)
        year = int(published_el.text[:4]) if published_el is not None else 0

        summary_el = entry.find("atom:summary", ns)
        summary = summary_el.text.strip() if summary_el is not None else ""

        # Get primary category
        cat_el = entry.find("arxiv:primary_category", ns)
        primary_cat = cat_el.get("term", "") if cat_el is not None else ""

        # Get all categories
        categories = [
            c.get("term", "")
            for c in entry.findall("atom:category", ns)
        ]

        # Try to extract journal reference
        journal_el = entry.find("arxiv:journal_ref", ns)
        journal_ref = journal_el.text.strip() if journal_el is not None else ""

        # Try DOI
        doi_el = entry.find("arxiv:doi", ns)
        doi = doi_el.text.strip() if doi_el is not None else ""

        results.append({
            "arxiv_id": arxiv_id,
            "arxiv_id_clean": arxiv_id_clean,
            "title": title,
            "authors": authors,
            "year": year,
            "summary": summary[:500],
            "primary_category": primary_cat,
            "categories": categories,
            "journal_ref": journal_ref,
            "doi": doi,
            "published": published_el.text if published_el is not None else "",
        })

    return results


def main():
    parser = argparse.ArgumentParser(description="Search arXiv for bibliometrics papers")
    parser.add_argument("--list", action="store_true", help="Show collected results")
    parser.add_argument("--download", action="store_true", help="Download PDFs for collected papers")
    parser.add_argument("--max", type=int, default=100, dest="max_results",
                        help="Max results per query (default: 100)")
    parser.add_argument("--queries", type=str, default="", help="Comma-separated query labels to run")
    parser.add_argument("--dry-run", action="store_true", help="Just print queries, don't execute")
    args = parser.parse_args()

    if args.dry_run:
        print(f"\n{len(SEARCH_QUERIES)} queries configured:\n")
        for i, q in enumerate(SEARCH_QUERIES, 1):
            print(f"{i}. [{q['label']}] {q['query'][:120]}...")
        return

    if args.list:
        if RESULTS_PATH.exists():
            results = json.loads(RESULTS_PATH.read_text())
            papers = results.get("papers", [])
            print(f"\n{len(papers)} papers collected:\n")
            for i, p in enumerate(papers, 1):
                authors = ", ".join(p.get("authors", [])[:3])
                if len(p.get("authors", [])) > 3:
                    authors += " et al."
                print(f"{i}. [{p.get('arxiv_id_clean', p['arxiv_id'])}] "
                      f"({p.get('year', '?')}) {p['title'][:100]}")
                print(f"   Authors: {authors}")
                print(f"   Source: {p.get('source_label', '?')}")
                if p.get("journal_ref"):
                    print(f"   Journal: {p['journal_ref']}")
                print()
        else:
            print("No results file found. Run without --list first.")
        return

    if args.download:
        return download_pdfs()

    # ── Search phase ────────────────────────────────────────────────
    queries_to_run = SEARCH_QUERIES
    if args.queries:
        labels = {l.strip() for l in args.queries.split(",")}
        queries_to_run = [q for q in SEARCH_QUERIES if q["label"] in labels]
        print(f"Filtered to {len(queries_to_run)} queries: {labels}")

    all_papers: dict[str, dict] = {}  # keyed by arxiv_id_clean

    for i, sq in enumerate(queries_to_run, 1):
        label = sq["label"]
        query = sq["query"]
        print(f"\n[{i}/{len(queries_to_run)}] Searching: {label}")
        print(f"  Query: {query[:120]}...")

        results = fetch_arxiv_results(query, max_results=args.max_results)
        new_count = 0
        for paper in results:
            aid = paper["arxiv_id_clean"]
            if aid in EXISTING_ARXIV_IDS or aid in EXCLUDE_ARXIV_IDS:
                continue
            if aid not in all_papers:
                paper["source_label"] = label
                paper["source_metric_type"] = sq["metric_type"]
                all_papers[aid] = paper
                new_count += 1

        print(f"  Got {len(results)} results, {new_count} new (total unique: {len(all_papers)})")
        time.sleep(1)  # Be polite to arXiv

    # ── Save results ─────────────────────────────────────────────────
    papers_list = sorted(all_papers.values(), key=lambda p: -p["year"])

    output = {
        "collected_at": time.strftime("%Y-%m-%d %H:%M:%S"),
        "total_papers": len(papers_list),
        "papers": papers_list,
    }
    RESULTS_PATH.write_text(json.dumps(output, indent=2, ensure_ascii=False))
    print(f"\n{'='*60}")
    print(f"Saved {len(papers_list)} unique papers to {RESULTS_PATH}")
    print(f"{'='*60}")


def download_pdfs():
    """Download PDFs for papers in search_results.json."""
    if not RESULTS_PATH.exists():
        print("No search results. Run search first.")
        return

    results = json.loads(RESULTS_PATH.read_text())
    papers = results.get("papers", [])
    print(f"Downloading PDFs for {len(papers)} papers...")

    success = 0
    for i, paper in enumerate(papers, 1):
        aid = paper["arxiv_id"]
        # PDFs go to bench-mark/others/ for now (journal sorting later)
        pdf_path = OUTPUT_DIR / "others" / f"{aid.replace('/', '_')}.pdf"
        pdf_path.parent.mkdir(parents=True, exist_ok=True)

        if pdf_path.exists():
            print(f"[{i}/{len(papers)}] EXISTS: {aid}")
            success += 1
            continue

        url = f"https://arxiv.org/pdf/{aid}.pdf"
        print(f"[{i}/{len(papers)}] Downloading {aid}...")
        try:
            req = urllib.request.Request(url, headers={"User-Agent": "AI4SciMetrology/1.0"})
            with urllib.request.urlopen(req, timeout=120) as resp:
                pdf_path.write_bytes(resp.read())
            success += 1
            time.sleep(0.5)
        except Exception as e:
            print(f"  ERROR: {e}")

    print(f"\nDownloaded {success}/{len(papers)} PDFs")


if __name__ == "__main__":
    main()
