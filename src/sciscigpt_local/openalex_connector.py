"""OpenAlex API connector — open scholarly data for SciSci analysis.

OpenAlex is an open, free catalog of ~250M scholarly works, authors, institutions,
concepts, and funders. It replaces the gated SciSciNet/BigQuery stack for local use.

API docs: https://docs.openalex.org/
Base URL: https://api.openalex.org/

No API key required (polite pool: 10 req/s, no bursts).
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse
from typing import Any, Optional


BASE_URL = "https://api.openalex.org"
USER_AGENT = "mailto:sciscigpt-local@example.com"


def _api_get(endpoint: str, params: dict | None = None) -> dict:
    """Make a polite request to the OpenAlex API."""
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)

    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)

    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _api_get_all(endpoint: str, params: dict | None = None, max_results: int = 100) -> list[dict]:
    """Paginate through OpenAlex API results."""
    params = dict(params or {})
    params.setdefault("per_page", min(max_results, 200))
    params.setdefault("page", "1")

    results = []
    while True:
        data = _api_get(endpoint, params)
        results.extend(data.get("results", []))
        if len(results) >= max_results:
            break
        meta = data.get("meta", {})
        if params["page"] >= meta.get("per_page", 1):
            break
        params["page"] = str(int(params["page"]) + 1)
        time.sleep(0.11)  # stay within 10 req/s limit

    return results[:max_results]


# --- Public API ---

def search_works(query: str, max_results: int = 25) -> list[dict]:
    """Search for scholarly works by title/keyword.

    Returns list of works with: id, doi, title, publication_date, cited_by_count,
    authorships, primary_location, abstract_inverted_index, concepts.
    """
    # Un-invert abstract index to plain text
    def _reconstruct_abstract(inv_idx: dict | None) -> str:
        if not inv_idx:
            return ""
        word_positions = {}
        for word, positions in inv_idx.items():
            for pos in positions:
                word_positions[pos] = word
        return " ".join(word_positions[i] for i in sorted(word_positions))

    works = _api_get_all("works", {"search": query}, max_results)
    for w in works:
        inv = w.get("abstract_inverted_index")
        w["abstract"] = _reconstruct_abstract(inv) if inv else ""
    return works


def get_work(openalex_id: str) -> dict:
    """Get a single work by OpenAlex ID (e.g., 'W2741809807')."""
    work = _api_get(f"works/{openalex_id}")
    inv = work.get("abstract_inverted_index")
    work["abstract"] = _reconstruct_abstract(inv) if inv else ""
    return work


def get_citations(openalex_id: str, max_results: int = 50) -> list[dict]:
    """Get works that cite a given work."""
    return _api_get_all("works", {"filter": f"cites:{openalex_id}"}, max_results)


def get_references(openalex_id: str, max_results: int = 50) -> list[dict]:
    """Get works cited by a given work."""
    return _api_get_all("works", {"filter": f"cited_by:{openalex_id}"}, max_results)


def search_authors(query: str, max_results: int = 10) -> list[dict]:
    """Search for authors by name."""
    return _api_get_all("authors", {"search": query}, max_results)


def get_author(openalex_id: str) -> dict:
    """Get author details by OpenAlex ID."""
    return _api_get(f"authors/{openalex_id}")


def search_concepts(query: str, max_results: int = 10) -> list[dict]:
    """Search for concepts (research topics/fields) by name."""
    return _api_get_all("concepts", {"search": query}, max_results)


def get_field_works(field_name: str, max_results: int = 50) -> list[dict]:
    """Get top-cited works in a field/concept area.

    Searches by concept name and returns works sorted by citation count.
    """
    # First find the concept
    concepts = search_concepts(field_name, max_results=3)
    if not concepts:
        return []

    concept_id = concepts[0]["id"].split("/")[-1]
    return _api_get_all(
        "works",
        {
            "filter": f"concepts.id:{concept_id}",
            "sort": "cited_by_count:desc",
        },
        max_results,
    )


# --- SciSci-specific helpers ---

def compute_citation_fan(openalex_id: str, depth: int = 1) -> dict:
    """Build a citation fan for a focal paper.

    Returns {work: focal_paper, cited_by: [...], references: [...]}
    """
    focal = get_work(openalex_id)
    result: dict[str, Any] = {"work": focal, "cited_by": [], "references": []}

    if depth >= 1:
        result["cited_by"] = get_citations(openalex_id, max_results=30)
        result["references"] = get_references(openalex_id, max_results=30)

    return result


def get_disruption_basics(openalex_id: str) -> dict:
    """Get basic data needed for disruption index calculation.

    D-index = (n_i - n_j) / (n_i + n_j + n_k) per Wu et al. (2019)

    where:
      n_i = # subsequent papers that cite the focal paper BUT NOT its references
      n_j = # subsequent papers that cite BOTH focal paper and its references
      n_k = # subsequent papers that cite ONLY the focal paper's references (not the focal)

    This returns the citation fan needed to compute these counts.
    """
    focal = get_work(openalex_id)
    cited_by = get_citations(openalex_id, max_results=100)
    references = get_references(openalex_id, max_results=100)

    ref_ids = {r["id"] for r in references}

    n_i, n_j, n_k = 0, 0, 0
    for paper in cited_by:
        paper_refs = set()
        try:
            # For each citing paper, get what it references
            paper_refs_data = get_references(paper["id"].split("/")[-1], max_results=50)
            paper_refs = {r["id"] for r in paper_refs_data}
        except Exception:
            pass

        cites_focal = openalex_id.split("/")[-1] in str(paper.get("referenced_works", []))
        cites_refs = bool(paper_refs & ref_ids)

        if cites_focal and not cites_refs:
            n_i += 1
        elif cites_focal and cites_refs:
            n_j += 1
        elif not cites_focal and cites_refs:
            n_k += 1

    total = n_i + n_j + n_k
    d_index = (n_i - n_j) / total if total > 0 else 0.0

    return {
        "work": focal.get("title", ""),
        "openalex_id": openalex_id,
        "cited_by_count": len(cited_by),
        "n_i": n_i,
        "n_j": n_j,
        "n_k": n_k,
        "disruption_index": round(d_index, 4),
    }


# Shared helper for abstract reconstruction
def _reconstruct_abstract(inv_idx: dict | None) -> str:
    if not inv_idx:
        return ""
    word_positions = {}
    for word, positions in inv_idx.items():
        for pos in positions:
            word_positions[pos] = word
    return " ".join(word_positions[i] for i in sorted(word_positions))
