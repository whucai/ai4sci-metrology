"""SciSci SDK — High-level Science of Science operations.

Wraps OpenAlex API calls into domain-specific functions so AI agents
can perform SciSci research without writing raw pandas/networkx code.

SDK functions:
  sci.disruption_index(doi_or_id)       → D-index computation (Wu et al. 2019)
  sci.citation_cascade(doi_or_id, depth)→ Multi-hop citation traversal
  sci.coauthor_network(author_id)       → Co-author graph + centrality
  sci.field_normalize(metric, field, yr) → Field × Year Z-score normalization
  sci.search_papers(query)              → Search works with metadata
  sci.cem_match(treatment, pool, on)    → Coarsened Exact Matching (Iacus et al. 2012)
"""

from __future__ import annotations

import json
import time
import urllib.request
import urllib.parse
from typing import Any
from collections import Counter

# -- Internal helpers ----------------------------------------------------------

BASE_URL = "https://api.openalex.org"
USER_AGENT = "mailto:sciscigpt-local@example.com"


def _api_get(endpoint: str, params: dict | None = None) -> dict:
    url = f"{BASE_URL}/{endpoint}"
    if params:
        url += "?" + urllib.parse.urlencode(params)
    req = urllib.request.Request(url)
    req.add_header("User-Agent", USER_AGENT)
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode())


def _api_get_all(endpoint: str, params: dict | None = None, max_results: int = 100) -> list[dict]:
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
        per_page = int(params["per_page"])
        if len(data.get("results", [])) < per_page:
            break
        params["page"] = str(int(params["page"]) + 1)
        time.sleep(0.11)
    return results[:max_results]


def _reconstruct_abstract(inv_idx: dict | None) -> str:
    if not inv_idx:
        return ""
    wp = {}
    for w, ps in inv_idx.items():
        for p in ps:
            wp[p] = w
    return " ".join(wp[i] for i in sorted(wp))


def _resolve_id(doi_or_id: str) -> str:
    """Resolve a DOI or OpenAlex ID to an OpenAlex work ID (e.g. 'W...')."""
    doi_or_id = doi_or_id.strip()
    # Already an OpenAlex ID
    if doi_or_id.startswith("W") and len(doi_or_id) >= 8:
        return doi_or_id
    # DOI format
    doi = doi_or_id.replace("https://doi.org/", "").strip()
    try:
        data = _api_get(f"works/doi:{urllib.parse.quote(doi, safe='')}")
        return data["id"].split("/")[-1]
    except Exception:
        # Try search as fallback
        results = _api_get_all("works", {"search": doi_or_id}, max_results=3)
        if results:
            return results[0]["id"].split("/")[-1]
        raise ValueError(f"Could not resolve: {doi_or_id}")


def _normalize_openalex_id(id_str: str) -> str:
    """Extract the ID part from an OpenAlex URL or return as-is."""
    return id_str.split("/")[-1] if "/" in id_str else id_str


# -- Public SDK functions ------------------------------------------------------


def search_papers(query: str, max_results: int = 25) -> list[dict]:
    """Search OpenAlex for papers by title, author, or keyword.

    Returns list of dicts with: id, doi, title, publication_date, cited_by_count,
    authorships, concepts, abstract.
    """
    results = _api_get_all("works", {"search": query}, max_results)
    for r in results:
        r["abstract"] = _reconstruct_abstract(r.get("abstract_inverted_index"))
    return results


def get_paper(doi_or_id: str) -> dict:
    """Get full metadata for a paper by DOI or OpenAlex ID."""
    oa_id = _resolve_id(doi_or_id)
    work = _api_get(f"works/{oa_id}")
    work["abstract"] = _reconstruct_abstract(work.get("abstract_inverted_index"))
    return work


def disruption_index(doi_or_id: str, max_citing: int = 50) -> dict:
    """Compute the Disruption Index (Wu et al. 2019) for a paper.

    D = (n_i - n_j) / (n_i + n_j + n_k)

    where:
      n_i: citing papers that cite the focal paper but NOT its references (disruptive)
      n_j: citing papers that cite BOTH the focal paper and its references (consolidating)
      n_k: citing papers that cite ONLY the focal paper's references (irrelevant)

    Returns:
      dict with n_i, n_j, n_k, D-index, and metadata.
    """
    oa_id = _resolve_id(doi_or_id)
    focal = _api_get(f"works/{oa_id}")

    # Use referenced_works from the focal paper metadata
    ref_ids = set()
    ref_urls = focal.get("referenced_works", [])
    for ref_url in ref_urls[:100]:
        ref_ids.add(_normalize_openalex_id(ref_url))

    # Get papers that cite the focal paper
    citing_data = _api_get_all("works", {"filter": f"cites:{oa_id}"}, max_results=max_citing)

    n_i, n_j, n_k = 0, 0, 0
    for citing_paper in citing_data:
        citing_refs = set()
        citing_ref_urls = citing_paper.get("referenced_works", [])
        for cr in citing_ref_urls[:100]:
            citing_refs.add(_normalize_openalex_id(cr))

        has_focal = oa_id in citing_refs
        has_refs = bool(citing_refs & ref_ids)

        if has_focal and not has_refs:
            n_i += 1
        elif has_focal and has_refs:
            n_j += 1
        elif not has_focal and has_refs:
            n_k += 1
        # else: cites neither — not relevant

    total = n_i + n_j + n_k
    d_val = (n_i - n_j) / total if total > 0 else 0.0

    return {
        "title": focal.get("title", ""),
        "doi": focal.get("doi", ""),
        "openalex_id": oa_id,
        "year": focal.get("publication_year"),
        "cited_by_count": focal.get("cited_by_count", 0),
        "n_i": n_i,
        "n_j": n_j,
        "n_k": n_k,
        "n_total": total,
        "disruption_index": round(d_val, 4),
    }


def citation_cascade(doi_or_id: str, depth: int = 2, max_per_level: int = 30) -> dict:
    """Multi-hop citation cascade analysis.

    Traverses the citation graph up to `depth` levels from the focal paper.

    Returns:
      dict with levels: [{papers}, {papers_from_citing}, ...]
    """
    oa_id = _resolve_id(doi_or_id)
    focal = get_paper(oa_id)

    cascade: dict[str, Any] = {
        "focal": {"id": oa_id, "title": focal.get("title"), "cited_by": focal.get("cited_by_count", 0)},
        "levels": [],
    }

    current_ids = {oa_id}
    for level in range(depth):
        level_papers = []
        next_ids = set()
        for pid in list(current_ids)[:5]:  # limit branching
            try:
                citing = _api_get_all("works", {"filter": f"cites:{pid}"}, max_results=min(max_per_level, 20))
                for p in citing:
                    pid_norm = _normalize_openalex_id(p["id"])
                    level_papers.append({
                        "id": pid_norm,
                        "title": p.get("title", ""),
                        "year": p.get("publication_year"),
                        "cited_by": p.get("cited_by_count", 0),
                    })
                    next_ids.add(pid_norm)
            except Exception:
                pass
            time.sleep(0.12)
        cascade["levels"].append({"depth": level + 1, "count": len(level_papers), "papers": level_papers})
        current_ids = next_ids
        if not current_ids:
            break

    return cascade


def coauthor_network(author_name: str, max_papers: int = 50) -> dict:
    """Build a co-author network from an author's recent publications.

    Searches for an author by name, gets their recent papers, extracts co-authors,
    and returns a graph structure (nodes = authors, edges = co-authorship).

    Returns:
      dict with author, papers_count, network: {nodes: [{id, name, count}], edges: [{source, target, weight}]}
    """
    # Search for author
    author_results = _api_get_all("authors", {"search": author_name}, max_results=3)
    if not author_results:
        return {"error": f"Author not found: {author_name}"}

    author = author_results[0]
    author_id = _normalize_openalex_id(author["id"])

    # Get their works
    works = _api_get_all("works", {"filter": f"authorships.author.id:{author_id}"}, max_results=max_papers)

    nodes: dict[str, dict] = {}
    edges: list[dict] = []

    for work in works:
        work_authors = work.get("authorships", [])
        for i, a1 in enumerate(work_authors):
            aid1 = _normalize_openalex_id(a1.get("author", {}).get("id", ""))
            name1 = a1.get("author", {}).get("display_name", "")
            if aid1 not in nodes:
                nodes[aid1] = {"id": aid1, "name": name1, "paper_count": 0}
            nodes[aid1]["paper_count"] += 1

            for a2 in work_authors[i + 1:]:
                aid2 = _normalize_openalex_id(a2.get("author", {}).get("id", ""))
                name2 = a2.get("author", {}).get("display_name", "")
                if aid2 not in nodes:
                    nodes[aid2] = {"id": aid2, "name": name2, "paper_count": 0}
                nodes[aid2]["paper_count"] += 1
                edges.append({"source": aid1, "target": aid2, "weight": 1})

    # Merge duplicate edges
    edge_weights: dict[tuple, int] = {}
    for e in edges:
        key = tuple(sorted([e["source"], e["target"]]))
        edge_weights[key] = edge_weights.get(key, 0) + 1

    merged_edges = [
        {"source": s, "target": t, "weight": w}
        for (s, t), w in edge_weights.items()
    ]

    # Sort nodes by paper count
    sorted_nodes = sorted(nodes.values(), key=lambda x: x["paper_count"], reverse=True)

    return {
        "author": {"id": author_id, "name": author.get("display_name", author_name)},
        "papers_analyzed": len(works),
        "network": {
            "nodes": sorted_nodes[:50],  # max 50 co-authors
            "edges": merged_edges[:100],  # max 100 edges
        },
        "top_coauthors": [
            {"name": n["name"], "papers_together": n["paper_count"]}
            for n in sorted_nodes[:10] if n["id"] != author_id
        ],
    }


def field_normalize(metric: float | int, field_name: str, year: int) -> dict:
    """Normalize a metric within a specific field and year (Z-score).

    Computes the field×year mean and std of the metric using papers in that
    concept area, then returns the Z-score and percentile.

    Note: This is a sampling-based approximation — for precise normalization,
    you'd need the full dataset distribution. This samples up to 200 papers
    from the specified field and year to estimate the distribution.

    Returns:
      dict with z_score, percentile, field_mean, field_std, sample_size.
    """
    # Find field concept
    concepts = _api_get_all("concepts", {"search": field_name}, max_results=3)
    if not concepts:
        return {"error": f"Field not found: {field_name}"}

    concept_id = _normalize_openalex_id(concepts[0]["id"])

    # Sample papers from field×year
    papers = _api_get_all(
        "works",
        {
            "filter": f"concepts.id:{concept_id},publication_year:{year}",
            "sort": "cited_by_count:desc",
        },
        max_results=200,
    )

    if not papers:
        return {"error": f"No papers found for {field_name} in {year}"}

    counts = [p.get("cited_by_count", 0) for p in papers if p.get("cited_by_count") is not None]

    if not counts:
        return {"error": "No citation count data available"}

    mean = sum(counts) / len(counts)
    var = sum((c - mean) ** 2 for c in counts) / len(counts)
    std = var ** 0.5

    z_score = (metric - mean) / std if std > 0 else 0.0

    # Percentile (empirical)
    below = sum(1 for c in counts if c <= metric)
    percentile = below / len(counts)

    return {
        "metric": metric,
        "field": field_name,
        "year": year,
        "z_score": round(z_score, 4),
        "percentile": round(percentile, 4),
        "field_mean": round(mean, 2),
        "field_std": round(std, 2),
        "sample_size": len(counts),
    }


def cem_match(
    treatment: list[dict],
    pool: list[dict],
    on: list[str],
    k: int = 1,
) -> dict:
    """Coarsened Exact Matching (Iacus et al. 2012).

    Matches treatment units to control units from the pool based on
    exact matching on coarsened (binned) variables.

    Args:
        treatment: List of dicts with keys matching `on` fields.
        pool: List of dicts with same keys.
        on: List of variable names to match on.
        k: Number of matches per treatment unit.

    Returns:
        dict with matched_pairs, balance_stats, match_rate.
    """
    if not treatment or not pool:
        return {"error": "Empty treatment or pool", "matched_pairs": [], "match_rate": 0.0}

    # Build bins for each variable
    numeric_bins: dict[str, dict] = {}
    for var in on:
        all_vals = []
        for item in treatment + pool:
            val = item.get(var)
            if isinstance(val, (int, float)):
                all_vals.append(val)

        if all_vals:
            sorted_vals = sorted(all_vals)
            n_bins = min(5, len(set(all_vals)))
            if n_bins == 1:
                numeric_bins[var] = {"min": all_vals[0], "max": all_vals[0], "bins": [all_vals[0]]}
            else:
                bin_size = len(sorted_vals) // n_bins
                bin_edges = [sorted_vals[i * bin_size] for i in range(n_bins)] + [sorted_vals[-1] + 1]
                numeric_bins[var] = {"edges": bin_edges, "n_bins": n_bins}
        else:
            numeric_bins[var] = {}

    def _coarsen(item: dict) -> tuple:
        result = []
        for var in on:
            val = item.get(var, "")
            if var in numeric_bins and "edges" in numeric_bins[var]:
                edges = numeric_bins[var]["edges"]
                for i in range(len(edges) - 1):
                    if isinstance(val, (int, float)) and edges[i] <= val < edges[i + 1]:
                        result.append(f"bin_{i}")
                        break
                else:
                    result.append("bin_other")
            elif isinstance(val, str):
                result.append(val.lower())
            elif isinstance(val, (int, float)):
                result.append(str(round(val, 2)))
            else:
                result.append(str(val))
        return tuple(result)

    # Index pool by coarsened key
    pool_index: dict[tuple, list[int]] = {}
    for i, item in enumerate(pool):
        key = _coarsen(item)
        pool_index.setdefault(key, []).append(i)

    matched_pairs = []
    matched_pool = set()
    total = 0
    matched = 0

    for t_item in treatment:
        total += 1
        t_key = _coarsen(t_item)
        candidates = [idx for idx in pool_index.get(t_key, []) if idx not in matched_pool]
        if candidates:
            matched += 1
            for idx in candidates[:k]:
                matched_pairs.append({"treatment": t_item, "control": pool[idx]})
                matched_pool.add(idx)

    # Balance check
    balance_stats = {}
    for var in on:
        t_vals = [p["treatment"].get(var) for p in matched_pairs if isinstance(p["treatment"].get(var), (int, float))]
        c_vals = [p["control"].get(var) for p in matched_pairs if isinstance(p["control"].get(var), (int, float))]
        if t_vals and c_vals:
            t_mean = sum(t_vals) / len(t_vals)
            c_mean = sum(c_vals) / len(c_vals)
            balance_stats[var] = {
                "treatment_mean": round(t_mean, 4),
                "control_mean": round(c_mean, 4),
                "diff": round(abs(t_mean - c_mean), 4),
            }

    return {
        "matched_pairs": matched_pairs[:50],  # limit output
        "n_matched": matched,
        "n_total": total,
        "match_rate": round(matched / total, 4) if total else 0.0,
        "balance_stats": balance_stats,
    }
