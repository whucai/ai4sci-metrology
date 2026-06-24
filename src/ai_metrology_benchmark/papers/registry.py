"""Paper registry — unified definitions for all 13+97 methodology papers.

Merges data from three sources:
  - run_manual_papers_benchmark.py (PAPERS: paths, metric types)
  - run_native_method_benchmark.py (PAPER_REGISTRY: tiers, expected methods/conclusions)
  - run_stage4_benchmark.py (PAPER_CLAIMS: 24 claims across 8 papers)
  - registry_auto.py (AUTO_PAPER_REGISTRY: 97 papers from bulk arXiv search)
"""

from __future__ import annotations

from ..types import PaperEntry, ClaimType
from .registry_auto import AUTO_PAPER_REGISTRY, AUTO_READY_PAPERS

# ── Paper registry (13 hand-curated + 97 auto-collected = 110 papers) ───

PAPER_REGISTRY: dict[str, PaperEntry] = {
    "ms_dynamic_network": PaperEntry(
        id="ms_dynamic_network",
        md_path="bench-mark/Management Science/A_Dynamic_Network_Measure_of_Technological_Change.md",
        title="A Dynamic Network Measure of Technological Change",
        journal="Management Science",
        year=2017,
        doi="10.1287/mnsc.2015.2366",
        metric_type="disruption",
        requires_tables=["paper_citations"],
        claims=[
            {
                "id": "D1",
                "text": "The disruption index D = (n_i - n_j)/(n_i + n_j + n_k) measures "
                        "whether an innovation disrupts or consolidates existing knowledge.",
                "type": "method",
                "testable_with": "disruption computation on any paper with citation data",
            },
            {
                "id": "D2",
                "text": "The dynamic network measure captures technological evolution better "
                        "than static citation counts alone.",
                "type": "finding",
                "testable_with": "comparison of D-index vs raw citation count on same papers",
            },
            {
                "id": "D3",
                "text": "The method can be applied to any citation network to identify "
                        "disruptive technologies.",
                "type": "method",
                "testable_with": "successful computation across diverse test papers",
            },
        ],
    ),
    "nber_w18958": PaperEntry(
        id="nber_w18958",
        md_path="bench-mark/Management Science/w18958.md",
        title="Exploring Tradeoffs in the Organization of Scientific Work: "
              "Collaboration and Scientific Reward",
        journal="NBER Working Paper",
        year=2013,
        doi="10.3386/w18958",
        metric_type="team_size_effect",
        requires_tables=["papers"],
        claims=[
            {
                "id": "T1",
                "text": "There is a tradeoff between collaboration scale and individual "
                        "scientific contribution recognition.",
                "type": "finding",
                "testable_with": "team size effect (small vs large team disruption difference)",
            },
            {
                "id": "T2",
                "text": "Small teams (≤3 authors) produce more individually disruptive work "
                        "than large teams (>3 authors).",
                "type": "finding",
                "testable_with": "SMALL_MEAN - LARGE_MEAN > 0 → supported",
            },
            {
                "id": "T3",
                "text": "The team size effect is a robust pattern that should replicate "
                        "across different datasets.",
                "type": "interpretation",
                "testable_with": "consistency of effect direction across test conditions",
            },
        ],
    ),
    "arxiv_2306_01949": PaperEntry(
        id="arxiv_2306_01949",
        md_path="bench-mark/arXiv/2306.01949v1.md",
        title="The disruption index is biased by citation inflation",
        journal="Scientometrics (arXiv:2306.01949)",
        year=2023,
        doi="",
        metric_type="citation_inflation",
        requires_tables=["papers"],
        claims=[
            {
                "id": "C1",
                "text": "The disruption index is systematically biased by citation inflation — "
                        "papers with longer reference lists produce lower D-index values.",
                "type": "finding",
                "testable_with": "negative correlation between reference_count and disruption_score",
            },
            {
                "id": "C2",
                "text": "Temporal normalization is needed to compare disruption scores "
                        "across different time periods.",
                "type": "interpretation",
                "testable_with": "correlation magnitude indicates bias severity",
            },
            {
                "id": "C3",
                "text": "The bias exists in standard bibliometric datasets including SciSciNet.",
                "type": "finding",
                "testable_with": "replication on SciSciNet data",
            },
        ],
    ),
    "arxiv_2308_02383": PaperEntry(
        id="arxiv_2308_02383",
        md_path="bench-mark/Scientometrics/2308.02383v2.md",
        title="What do we know about the disruption index in scientometrics? An overview",
        journal="Scientometrics",
        year=2024,
        doi="",
        metric_type="disruption",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "R1",
                "text": "The disruption index D = (n_i - n_j)/(n_i + n_j + n_k) is the "
                        "standard formula for measuring scientific disruption.",
                "type": "method",
                "testable_with": "disruption computation matches SciSciNet ground truth",
            },
            {
                "id": "R2",
                "text": "Multiple variants of the disruption index exist (D-index, CD-index), "
                        "each capturing different aspects of disruption.",
                "type": "method",
                "testable_with": "implementation can distinguish D from CD variants",
            },
            {
                "id": "R3",
                "text": "The disruption index has known limitations including sensitivity to "
                        "citation window and field effects.",
                "type": "interpretation",
                "testable_with": "consistency of results across different test papers",
            },
        ],
    ),
    "nature_2023_disruption": PaperEntry(
        id="nature_2023_disruption",
        md_path="bench-mark/Nature/s41586-022-05543-x.md",
        title="Papers and patents are becoming less disruptive over time",
        journal="Nature",
        year=2023,
        doi="10.1038/s41586-022-05543-x",
        metric_type="disruption_temporal",
        requires_tables=["papers"],
        claims=[
            {
                "id": "N1",
                "text": "Papers and patents are becoming less disruptive over time across "
                        "all fields of science and technology.",
                "type": "finding",
                "testable_with": "negative trend correlation between decade and mean disruption",
            },
            {
                "id": "N2",
                "text": "The decline in disruptiveness persists after controlling for "
                        "changes in citation and authorship practices.",
                "type": "finding",
                "testable_with": "trend remains negative after controlling for reference_count",
            },
            {
                "id": "N3",
                "text": "The CD-index (a variant of D-index) shows the same declining trend.",
                "type": "finding",
                "testable_with": "trend consistency between D and CD variants",
            },
        ],
    ),
    "pnas_network_impact": PaperEntry(
        id="pnas_network_impact",
        md_path="bench-mark/PNAS/ke-et-al-2023-a-network-based-normalized-impact-measure-reveals-successful-periods-of-scientific-discovery-across.md",
        title="A network-based normalized impact measure reveals successful periods "
              "of scientific discovery across disciplines",
        journal="PNAS",
        year=2023,
        doi="10.1073/pnas.2301234120",
        metric_type="network_normalized_impact",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "P1",
                "text": "Network-normalized impact better identifies breakthrough discoveries "
                        "than raw citation counts.",
                "type": "finding",
                "testable_with": "network_impact ≠ focal_citations (normalization changes ranking)",
            },
            {
                "id": "P2",
                "text": "The measure normalizes by co-cited papers' mean citations, "
                        "comparing a paper against its citation context.",
                "type": "method",
                "testable_with": "NETWORK_IMPACT = focal_cit / mean_co_cited",
            },
            {
                "id": "P3",
                "text": "The method reveals hidden impact in fields with lower absolute citation rates.",
                "type": "interpretation",
                "testable_with": "network_impact > 1.0 for papers in low-citation fields",
            },
        ],
    ),
    "rp_2021_ccby": PaperEntry(
        id="rp_2021_ccby",
        md_path="bench-mark/Research Policy/1-s2.0-S0048733320302195-main.md",
        title="Research Policy 2021 — CC-BY Open Access",
        journal="Research Policy",
        year=2021,
        doi="10.1016/j.respol.2020.104144",
        metric_type="disruption",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "O1",
                "text": "The disruption index can be computed from standard citation data "
                        "and reflects a paper's novel contribution.",
                "type": "method",
                "testable_with": "disruption computation on SciSciNet test papers",
            },
            {
                "id": "O2",
                "text": "Disruption patterns differ across research fields and publication types.",
                "type": "finding",
                "testable_with": "variation in D-index across test papers of different types",
            },
        ],
    ),
    "rp_2025_sam_arts": PaperEntry(
        id="rp_2025_sam_arts",
        md_path="bench-mark/Research Policy/1-s2.0-S0048733325001684-main.md",
        title="Not like the others: Frontier scientists for inventive performance",
        journal="Research Policy",
        year=2025,
        doi="10.1016/j.respol.2025.105339",
        metric_type="frontier_author_impact",
        requires_tables=["papers"],
        claims=[
            {
                "id": "F1",
                "text": "Frontier scientists produce more inventive and higher-impact work "
                        "than non-frontier scientists.",
                "type": "finding",
                "testable_with": "FRONTIER_MEAN_CITATIONS > NON_FRONTIER_MEAN_CITATIONS",
            },
            {
                "id": "F2",
                "text": "Being 'not like the others' (statistically distinct research profile) "
                        "predicts inventive performance.",
                "type": "finding",
                "testable_with": "FRONTIER_MEAN_D differs from NON_FRONTIER_MEAN_D",
            },
            {
                "id": "F3",
                "text": "Frontier scientists are a distinct and identifiable group within "
                        "the scientific workforce.",
                "type": "finding",
                "testable_with": "frontier papers show distinct bibliometric profile",
            },
        ],
    ),
    # ── New papers (2026-06-06 collection) ──
    "pnas_sleeping_beauty": PaperEntry(
        id="pnas_sleeping_beauty",
        md_path="bench-mark/PNAS/1505.06454.md",
        title="Defining and Identifying Sleeping Beauties in Science",
        journal="PNAS",
        year=2015,
        doi="10.1073/pnas.1424329112",
        metric_type="sleeping_beauty",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "SB1",
                "text": "The beauty coefficient B quantifies delayed recognition: "
                       "B = sum_t (c_t * max(0, t - t_0) / T) where c_t is citations in year t.",
                "type": "method",
                "testable_with": "computation of B on papers with multi-year citation history",
            },
            {
                "id": "SB2",
                "text": "Sleeping Beauties follow a continuous spectrum — they are not "
                       "exceptional but follow power-law distribution.",
                "type": "finding",
                "testable_with": "B distribution fits power-law across large citation datasets",
            },
            {
                "id": "SB3",
                "text": "Many SBs achieve delayed importance in disciplines different "
                       "from where they were originally published.",
                "type": "finding",
                "testable_with": "multidisciplinary analysis of top B-scoring papers",
            },
        ],
    ),
    "acs_disruption_weighted": PaperEntry(
        id="acs_disruption_weighted",
        md_path="bench-mark/Advances in Complex Systems/2306.14364.md",
        title="Is disruption decreasing, or is it accelerating?",
        journal="Advances in Complex Systems",
        year=2023,
        doi="10.1142/S0219525923500066",
        metric_type="disruption_temporal",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "W1",
                "text": "The citation-weighted disruption mCD5 shows disruption has been "
                       "close to zero for ~50 years, NOT declining.",
                "type": "finding",
                "testable_with": "mCD5 trend correlation ≈ 0 vs CD5 < 0 on same data",
            },
            {
                "id": "W2",
                "text": "The original CD5 decline is an artifact of exponential growth "
                       "in publications and citations.",
                "type": "interpretation",
                "testable_with": "compare weighted vs unweighted trends controlling for corpus growth",
            },
            {
                "id": "W3",
                "text": "mCD5 has increased modestly since 2000, contradicting the "
                       "'science is becoming less disruptive' narrative.",
                "type": "finding",
                "testable_with": "mCD5 post-2000 trend positive on SciSciNet data",
            },
        ],
    ),
    "scientometrics_robust_disruption": PaperEntry(
        id="scientometrics_robust_disruption",
        md_path="bench-mark/Scientometrics/s11192-023-04644-2.md",
        title="Enhancing the robustness of the disruption metric against noise",
        journal="Scientometrics",
        year=2023,
        doi="10.1007/s11192-023-04644-2",
        metric_type="disruption",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "RD1",
                "text": "The modified disruption metric better distinguishes Nobel-prize "
                       "winning papers from others by reducing noise from highly-cited references.",
                "type": "finding",
                "testable_with": "comparison of original vs modified D on Nobel papers",
            },
            {
                "id": "RD2",
                "text": "The improved method is more stable against random link removal "
                       "in the citation network.",
                "type": "finding",
                "testable_with": "rank correlation under random edge perturbation",
            },
        ],
    ),
    "pnas_ranking_mobility": PaperEntry(
        id="pnas_ranking_mobility",
        md_path="bench-mark/PNAS/2303.15988.md",
        title="Ranking mobility and impact inequality in early academic careers",
        journal="PNAS",
        year=2023,
        doi="10.1073/pnas.2301537120",
        metric_type="career_mobility",
        requires_tables=["papers"],
        claims=[
            {
                "id": "RM1",
                "text": "Top and bottom-ranked authors experience the lowest ranking "
                       "mobility — Matthew effect signature.",
                "type": "finding",
                "testable_with": "transition matrix analysis of author impact deciles over 5yr windows",
            },
            {
                "id": "RM2",
                "text": "Mobility has increased over time while impact inequality has "
                       "decreased, with consistent negative correlation.",
                "type": "finding",
                "testable_with": "Pearson correlation between mobility D and Gini coefficient across cohorts",
            },
            {
                "id": "RM3",
                "text": "Top stability is most pronounced in Physical Sciences; "
                       "bottom stability highest in Life Sciences.",
                "type": "finding",
                "testable_with": "discipline-separated transition matrix comparison",
            },
        ],
    ),
    "arxiv_disruption_framework": PaperEntry(
        id="arxiv_disruption_framework",
        md_path="bench-mark/arXiv/2308.16363.md",
        title="A Mathematical Framework for Citation Disruption",
        journal="arXiv preprint",
        year=2023,
        doi="",
        metric_type="disruption",
        requires_tables=["papers", "paper_citations"],
        claims=[
            {
                "id": "DF1",
                "text": "The CD Index and its variants are special cases of betweenness "
                       "centrality on citation ego-networks.",
                "type": "method",
                "testable_with": "equivalence proof: compute betweenness on ego-net and compare to CD",
            },
            {
                "id": "DF2",
                "text": "Centrality-based disruption over larger ego-network radii "
                       "better identifies award-winning innovations than local CD.",
                "type": "finding",
                "testable_with": "AUC comparison of CD vs radius-2 ego-network disruption on award papers",
            },
        ],
    ),
}

# Merge 97 auto-collected papers from bulk arXiv search
PAPER_REGISTRY.update(AUTO_PAPER_REGISTRY)

# ── Metric type mapping ──
METRIC_TYPE_MAP: dict[str, str] = {
    "disruption": "Disruption Index (D)",
    "citation_count_prediction": "Citation Count Prediction",
    "team_size_effect": "Team Size Effect (Wu et al. 2019)",
    "network_normalized_impact": "Network-Normalized Impact (Ke et al. 2023)",
    "disruption_temporal": "Disruption Temporal Trend (Park et al. 2023)",
    "citation_inflation": "Citation Inflation Bias (Petersen et al. 2023)",
    "frontier_author_impact": "Frontier Author Impact (Arts et al. 2025)",
    # New metric types (2026-06-06)
    "sleeping_beauty": "Sleeping Beauty Coefficient B (Ke et al. 2015)",
    "career_mobility": "Career Ranking Mobility (Sun et al. 2023)",
    "novelty_conventionality": "Novelty-Conventionality Analysis (Uzzi et al. 2013)",
    "interdisciplinarity": "Interdisciplinarity Index",
    "altmetrics": "Altmetrics (Twitter/X Attention)",
}

# Papers with fully implemented metric templates (can run Stage 2)
READY_PAPERS = {
    "ms_dynamic_network", "nber_w18958", "arxiv_2306_01949",
    "arxiv_2308_02383", "nature_2023_disruption", "pnas_network_impact",
    "rp_2021_ccby", "rp_2025_sam_arts",
    "acs_disruption_weighted", "scientometrics_robust_disruption",
    "arxiv_disruption_framework",
    "pnas_sleeping_beauty",   # beauty_coefficient template added
    "pnas_ranking_mobility",  # career_mobility template added
}

# Merge 97 auto-collected papers
READY_PAPERS |= AUTO_READY_PAPERS

# No pending papers — all have metric templates
PENDING_PAPERS: set[str] = set()

# ── All claims flattened ──
ALL_CLAIMS: dict[str, list[dict]] = {
    paper_id: entry.claims for paper_id, entry in PAPER_REGISTRY.items()
}


def get_paper(paper_id: str) -> PaperEntry:
    """Look up a paper by id, raises KeyError if not found."""
    if paper_id not in PAPER_REGISTRY:
        raise KeyError(f"Paper '{paper_id}' not found. Available: {list(PAPER_REGISTRY.keys())}")
    return PAPER_REGISTRY[paper_id]


def get_papers_by_metric(metric_type: str) -> list[PaperEntry]:
    """Get all papers associated with a given metric type."""
    return [p for p in PAPER_REGISTRY.values() if p.metric_type == metric_type]


def get_all_paper_ids() -> list[str]:
    """Return all paper IDs in the registry."""
    return list(PAPER_REGISTRY.keys())


def get_all_claims() -> list[tuple[str, str, dict]]:
    """Return all claims as (paper_id, paper_title, claim_dict) tuples."""
    result = []
    for pid, entry in PAPER_REGISTRY.items():
        for claim in entry.claims:
            result.append((pid, entry.title, claim))
    return result
