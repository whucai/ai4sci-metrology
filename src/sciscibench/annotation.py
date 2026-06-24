"""Paper annotation schema and gold JSON generation for SciSciBench.

Each paper is decomposed into 6 gold components with structured JSON for Task 1.
Includes contamination suspicion scoring and blind version generation.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Literal

# ── Contamination suspicion levels ──
ContaminationLevel = Literal["high", "medium", "low"]


@dataclass
class ContaminationScore:
    """Per-paper contamination risk assessment."""

    level: ContaminationLevel
    reasons: list[str] = field(default_factory=list)
    model_cutoff_date: str = "2024-06-01"

    @classmethod
    def assess(
        cls,
        venue: str,
        year: int,
        citation_count: int | None = None,
        has_code: bool = False,
    ) -> ContaminationScore:
        reasons: list[str] = []
        score = 0

        # High-impact venue → +2
        high_venues = {"Nature", "Science", "PNAS", "Cell", "Nature Computational Science", "Nature Human Behaviour"}
        mid_venues = {"Scientometrics", "JASIST", "QSS", "Research Policy", "PLoS ONE", "arXiv"}
        if venue in high_venues:
            score += 2
            reasons.append(f"High-impact venue: {venue}")
        elif venue in mid_venues:
            score += 1
            reasons.append(f"Mid-impact venue: {venue}")

        # Published before cutoff → +2
        if year <= 2024:
            score += 2
            reasons.append(f"Published {year} (before model cutoff {cls.model_cutoff_date})")
        elif year == 2025:
            score += 1
            reasons.append(f"Published 2025 (near cutoff)")
        else:
            reasons.append(f"Published {year} (after cutoff — low risk)")

        # Highly cited → +1
        if citation_count and citation_count > 100:
            score += 1
            reasons.append(f"Highly cited ({citation_count} citations)")
        elif citation_count and citation_count > 10:
            reasons.append(f"Moderately cited ({citation_count} citations)")

        # Has public code → +1 (easier for LLM to have seen patterns)
        if has_code:
            score += 1
            reasons.append("Public code repository")

        if score >= 4:
            return cls(level="high", reasons=reasons)
        elif score >= 2:
            return cls(level="medium", reasons=reasons)
        else:
            return cls(level="low", reasons=reasons)


@dataclass
class SciSciPaper:
    """A fully annotated scientometric paper for the SciSciBench benchmark."""

    # ── Paper identity ──
    paper_id: str
    title: str
    authors: list[str] = field(default_factory=list)
    venue: str = ""
    year: int = 0
    doi: str = ""

    # ── Gold components ──
    research_idea: str = ""
    research_question: str = ""
    hypotheses: list[str] = field(default_factory=list)

    # Data design
    data_source: str = ""
    data_description: str = ""
    available_fields: list[str] = field(default_factory=list)
    sample_scope: dict[str, Any] = field(default_factory=dict)

    # Variable definitions (gold)
    independent_variables: list[dict[str, Any]] = field(default_factory=list)
    dependent_variables: list[dict[str, Any]] = field(default_factory=list)
    control_variables: list[dict[str, Any]] = field(default_factory=list)

    # Experiment design (gold JSON for Task 1)
    experiment_design_gold: dict[str, Any] = field(default_factory=dict)

    # Result claims (for Task 2 L2/L3)
    result_claims: list[dict[str, Any]] = field(default_factory=list)
    partial_results: list[dict[str, Any]] = field(default_factory=list)

    # Conclusion claims
    conclusion_claims: list[str] = field(default_factory=list)
    limitations: list[str] = field(default_factory=list)

    # Robustness
    robustness_checks: list[dict[str, Any]] = field(default_factory=list)

    # ── Contamination ──
    contamination: ContaminationScore | None = None
    text_path: str = ""

    # ── Blind versions ──
    blind_idea: str = ""          # Title/authors removed, idea paraphrased
    obfuscated_idea: str = ""     # Variables renamed to neutral tokens
    logic_only_idea: str = ""     # Pure mathematical formalism

    def assess_contamination(self) -> ContaminationScore:
        self.contamination = ContaminationScore.assess(
            venue=self.venue,
            year=self.year,
            citation_count=None,
            has_code=False,
        )
        return self.contamination

    def generate_blind_versions(self) -> None:
        """Generate three blind versions of the research idea."""
        # Layer 1: Blind — remove identifiers, paraphrase
        self.blind_idea = (
            f"Research question: {self.research_question}\n"
            f"Data available: {self.data_description}\n"
            f"Fields: {', '.join(self.available_fields[:20])}"
        )

        # Layer 2: Obfuscation — neutral token renaming
        var_map: dict[str, str] = {}
        token_idx = 1
        for var_list in [self.independent_variables, self.dependent_variables, self.control_variables]:
            for v in var_list:
                name = v.get("name", "")
                if name and name not in var_map:
                    var_map[name] = f"V{token_idx}"
                    token_idx += 1

        obfuscated_parts = [f"Research question: {self.research_question}"]
        for var_list_name, var_list in [
            ("Independent variables", self.independent_variables),
            ("Dependent variables", self.dependent_variables),
            ("Control variables", self.control_variables),
        ]:
            obfuscated = []
            for v in var_list:
                v_copy = dict(v)
                orig_name = v_copy.get("name", "")
                v_copy["name"] = var_map.get(orig_name, orig_name)
                if "definition" in v_copy:
                    for orig, neutral in var_map.items():
                        v_copy["definition"] = v_copy["definition"].replace(orig, neutral)
                obfuscated.append(v_copy)
            obfuscated_parts.append(f"{var_list_name}: {json.dumps(obfuscated)}")
        self.obfuscated_idea = "\n".join(obfuscated_parts)

        # Layer 3: Logic-Only — pure mathematical formalism
        logic_parts = []
        for v in self.dependent_variables:
            if "formula" in v:
                logic_parts.append(f"Dependent variable formula: {v['formula']}")
        for v in self.independent_variables:
            logic_parts.append(f"Independent variable: {v.get('name', '')} ({v.get('type', '')})")
        if self.experiment_design_gold.get("statistical_method"):
            sm = self.experiment_design_gold["statistical_method"]
            logic_parts.append(f"Statistical method: {sm.get('family', '')} — {sm.get('specification', '')}")
        self.logic_only_idea = "\n".join(logic_parts)

    def to_gold_json(self) -> dict[str, Any]:
        """Export the Task 1 gold JSON (experiment design fields)."""
        return {
            "paper_id": self.paper_id,
            "independent_variables": self.independent_variables,
            "dependent_variables": self.dependent_variables,
            "control_variables": self.control_variables,
            "statistical_method": self.experiment_design_gold.get("statistical_method", {}),
            "network_construction": self.experiment_design_gold.get("network_construction", {}),
            "sample_scope": self.experiment_design_gold.get("sample_scope", self.sample_scope),
            "grouping_strategy": self.experiment_design_gold.get("grouping_strategy", {}),
            "robustness_checks": self.experiment_design_gold.get("robustness_checks", self.robustness_checks),
            "expected_result_form": self.experiment_design_gold.get("expected_result_form", {}),
        }

    def to_task2_gold(self) -> dict[str, Any]:
        """Export the Task 2 gold fields (conclusion/result fields for evaluation)."""
        return {
            "paper_id": self.paper_id,
            "result_claims": self.result_claims,
            "partial_results": self.partial_results,
            "conclusion_claims": self.conclusion_claims,
            "limitations": self.limitations,
            "independent_variables": self.independent_variables,
            "dependent_variables": self.dependent_variables,
            "control_variables": self.control_variables,
        }

    def to_registry_entry(self) -> dict[str, Any]:
        """Export to benchmark paper registry format."""
        self.assess_contamination()
        self.generate_blind_versions()
        return {
            "paper_id": self.paper_id,
            "title": self.title,
            "authors": self.authors,
            "venue": self.venue,
            "year": self.year,
            "doi": self.doi,
            "contamination_level": self.contamination.level if self.contamination else "unknown",
            "contamination_reasons": self.contamination.reasons if self.contamination else [],
            "research_question": self.research_question,
            "data_source": self.data_source,
            "available_fields": self.available_fields,
            "conclusion_claims": self.conclusion_claims,
            "limitations": self.limitations,
            "result_claims": self.result_claims,
            "partial_results": self.partial_results,
            "blind_idea": self.blind_idea,
            "obfuscated_idea": self.obfuscated_idea,
            "logic_only_idea": self.logic_only_idea,
            "gold_json": self.to_gold_json(),
            "text_path": self.text_path,
        }


# ── Pilot papers ──

def create_wu2019() -> SciSciPaper:
    """Wu, Wang & Evans (2019) — Large teams develop and small teams disrupt science and technology."""
    paper = SciSciPaper(
        paper_id="wu2019_disruption",
        title="Large teams develop and small teams disrupt science and technology",
        authors=["Lingfei Wu", "Dashun Wang", "James A. Evans"],
        venue="Nature",
        year=2019,
        doi="10.1038/s41586-019-0941-4",
        research_idea="Investigate the relationship between team size and the disruptiveness of scientific outputs, testing whether larger teams produce more developmental (consolidating) work while smaller teams produce more disruptive (destabilizing) work.",
        research_question="How does team size affect the disruptiveness of scientific papers, patents, and software products?",
        hypotheses=["Larger teams produce less disruptive work", "Smaller teams produce more disruptive work"],
        data_source="Web of Science, USPTO, GitHub",
        data_description="Citation network of ~42 million papers, ~6 million patents, ~16 million software products. Each work linked to its references via citation graph.",
        available_fields=["paper_id", "year", "team_size", "references", "citations", "field", "journal"],
        sample_scope={"time_window": "1954-2014", "fields": ["all"], "filters": ["article type", "has references"]},
        independent_variables=[
            {"name": "team_size", "type": "count", "definition": "Number of unique authors on a paper/patent/software product"}
        ],
        dependent_variables=[
            {"name": "disruption_index", "type": "continuous", "formula": "D = (n_i - n_j) / (n_i + n_j + n_k) where n_i = papers citing only the focal work, n_j = papers citing both focal work and its references, n_k = papers citing only references"}
        ],
        control_variables=[
            {"name": "year", "type": "categorical"},
            {"name": "field", "type": "categorical"},
            {"name": "journal", "type": "categorical"},
            {"name": "citation_count", "type": "count"},
        ],
        experiment_design_gold={
            "statistical_method": {
                "family": "descriptive",
                "specification": "Compute D-index for each paper/patent/product; group by team_size decile; compute mean D per decile; plot trend",
                "estimation": "OLS",
            },
            "network_construction": {
                "node_type": "paper",
                "edge_type": "citation",
                "directed": True,
                "weighted": False,
                "temporal": True,
                "construction_method": "Citation graph from Web of Science reference lists",
            },
            "grouping_strategy": {
                "groups": ["team_size_deciles"],
                "rationale": "Compare mean disruptiveness across team size deciles",
            },
            "expected_result_form": {
                "type": "descriptive_table",
                "key_quantities": ["mean_D_per_decile", "D_trend_coefficient", "p_value"],
            },
        },
        robustness_checks=[
            {"method": "alternative D-index variants using different citation windows", "rationale": "Verify D-index stability"},
            {"method": "field-normalized D-index", "rationale": "Control for field-specific citation patterns"},
            {"method": "cohort analysis by year", "rationale": "Verify trend holds within each year"},
        ],
        result_claims=[
            {"metric": "D-index", "value": "small_teams higher", "direction": "negative correlation with team_size", "significance": "p < 0.001"},
            {"metric": "D-index trend", "value": "monotonically decreasing", "direction": "negative", "significance": "p < 0.001"},
        ],
        partial_results=[
            {"metric": "D-index", "small_teams": "higher", "large_teams": "lower", "note": "Only 5 years of data shown, full range not provided"},
        ],
        conclusion_claims=[
            "Large teams develop existing science and technology",
            "Small teams disrupt science and technology with new ideas and opportunities",
            "Both large and small teams are essential to a flourishing scientific ecosystem",
        ],
        limitations=[
            "D-index definition depends on citation window choice",
            "Team size is a proxy — doesn't capture collaboration structure",
            "Correlational, not causal",
        ],
    )
    return paper


def create_ke2023() -> SciSciPaper:
    """Ke, Gates & Barabási (2023) — A network-based normalized impact measure.

    PNAS 120(48), e2309378120.
    Proposes C-hat: cocitation-normalized citation indicator correcting
    temporal and field biases without a priori discipline labels.
    """
    paper = SciSciPaper(
        paper_id="ke2023_normalized_impact",
        title="A network-based normalized impact measure reveals successful periods of scientific discovery across disciplines",
        authors=["Qing Ke", "Alexander J. Gates", "Albert-László Barabási"],
        venue="PNAS",
        year=2023,
        doi="10.1073/pnas.2309378120",
        research_idea="Propose a cocitation-based paper-level normalized citation indicator (C-hat) that corrects for both temporal and field biases without requiring a priori discipline labels. Each paper's citations are normalized against the average citations of papers it is cocited with, providing a personalized comparison set.",
        research_question="Can a cocitation-network-based citation normalization eliminate temporal and field biases in citation counts and reveal successful periods of scientific discovery across all disciplines?",
        hypotheses=[
            "Cocited papers form a meaningful local comparison set for normalization",
            "C-hat is invariant across publication years (no temporal bias)",
            "C-hat is invariant across disciplines (no field bias)",
            "C-hat outperforms raw citations and journal-normalized citations in identifying expert-selected milestone papers",
        ],
        data_source="Web of Science (WoS) via Clarivate Analytics",
        data_description="65M+ papers with yearly citation counts and reference lists. Cocitation pairs extracted from citing papers' reference lists for each citing year.",
        available_fields=["paper_id", "year", "yearly_citations", "references", "cocited_papers",
                          "journal", "field", "T_year_window"],
        sample_scope={"time_window": "1945-2007", "fields": ["all"],
                       "filters": ["article type", "has references", "T=10 year citation window"]},
        independent_variables=[
            {"name": "paper_year", "type": "categorical",
             "definition": "Publication year of the focal paper"},
            {"name": "field", "type": "categorical",
             "definition": "Discipline classification (used as baseline only)"},
        ],
        dependent_variables=[
            {"name": "C_hat_T", "type": "continuous",
             "formula": "Ĉ_i,T = Σ_{t=0}^T ĉ_i,t where ĉ_i,t = c_i,t / ⟨c_n,t⟩_{n∈N_i,t}. c_i,t = yearly raw citations to paper i in year t. N_i,t = set of papers cocited with i by citing papers published in year t. ⟨c_n,t⟩ = mean yearly citations of papers in N_i,t."},
            {"name": "C_raw_T", "type": "count",
             "formula": "C_i,T = Σ_{t=0}^T c_i,t, total raw citations over T years"},
            {"name": "C_field_normalized_T", "type": "continuous",
             "formula": "C̃_i,T = C_i,T / ⟨C_T⟩_field, normalized by average citations of papers in same year and journal-based field"},
        ],
        control_variables=[
            {"name": "journal", "type": "categorical",
             "rationale": "Control for venue-specific citation practices"},
            {"name": "citing_year_volume", "type": "continuous",
             "rationale": "Control for overall growth in publishing and references"},
            {"name": "citation_window_T", "type": "count",
             "rationale": "Primary analysis uses T=10, robustness checks vary T"},
        ],
        experiment_design_gold={
            "statistical_method": {
                "family": "nonparametric_test",
                "specification": "Compute ĉ_i,t for each paper-year pair. Sum to Ĉ_10. Compare yearly distributions of Ĉ_10 vs C_10 and C̃_10. Test temporal stability via log-normal distribution fit per year (check σ invariance). Test field bias via KS-test across fields. Rank papers by Ĉ_10 and identify top 5% as high-impact.",
                "estimation": "permutation",
            },
            "network_construction": {
                "node_type": "paper",
                "edge_type": "cocitation",
                "directed": False,
                "weighted": True,
                "temporal": True,
                "construction_method": "For each citing paper published in year t, cocitation pairs among its references form edges. N_i,t dynamically changes each year as new citing papers appear.",
            },
            "grouping_strategy": {
                "groups": ["publication_year", "field", "journal"],
                "rationale": "Test invariance of Ĉ distributions across years and fields; compare against C and C̃ baselines",
            },
            "expected_result_form": {
                "type": "distribution_plot",
                "key_quantities": ["Ĉ distribution σ (expect ~1 across years)", "KS statistic across fields",
                                   "Top-5% field representation per year", "Rank comparison with milestone papers"],
            },
        },
        robustness_checks=[
            {"method": "Alternative citation windows T=5, 15, 20",
             "rationale": "Verify Ĉ stability independent of window choice"},
            {"method": "Milestone paper recovery test (PRL, PNAS, PRE, Human Relations milestone lists)",
             "rationale": "External validation against expert-curated lists of important papers"},
            {"method": "Comparison with RCR (Relative Citation Ratio)",
             "rationale": "Benchmark against the closest existing cocitation-based normalized indicator"},
            {"method": "Log-normal distribution fit per year",
             "rationale": "Quantitative test of distributional invariance across time"},
        ],
        result_claims=[
            {"metric": "Ĉ distribution shape", "value": "log-normal σ≈1.0-1.2 across all years",
             "direction": "null (invariant)", "significance": "consistent across 1945-2007"},
            {"metric": "Field bias correction", "value": "Ĉ eliminates field-level citation disparities",
             "direction": "null (unbiased)", "significance": "KS-test: Ĉ shows no field bias"},
            {"metric": "Milestone paper recovery", "value": "Ĉ ranks milestone papers consistently higher than C_raw",
             "direction": "positive for Ĉ", "significance": "Milestone rank improvement: higher percentiles under Ĉ"},
        ],
        partial_results=[
            {"metric": "RCR comparison", "note": "Limited to papers indexed by NIH iCite; Ĉ has broader coverage"},
            {"metric": "Citation window sensitivity", "note": "Main results shown for T=10 only; appendix has T=5,15,20"},
        ],
        conclusion_claims=[
            "Ĉ provides a universal, time- and field-invariant citation impact measure without requiring pre-defined discipline labels",
            "Cocitation-defined comparison sets automatically capture a paper's local research context, outperforming field-label-based normalization",
            "Ĉ reveals successful periods of discovery in smaller fields (geosciences, radiology, optics) that are systematically overlooked by raw citation counts",
            "The methodology enables fair comparison of scientific impact across diverse fields and time periods",
        ],
        limitations=[
            "Relies on Web of Science coverage; may underrepresent non-English or non-journal literature",
            "Cocitation data requires reference lists; older papers with incomplete reference data may be affected",
            "T=10 citation window may disadvantage very recent papers with insufficient citation accumulation",
            "Does not address citation motives (positive vs. negative citations)",
        ],
    )
    return paper


def create_arts2025() -> SciSciPaper:
    """Schaper, Arts & Veugelers (2025) — Frontier scientists for inventive performance.

    Research Policy 54 (2025) 105339.
    Studies whether corporate inventors who are frontier scientists
    (recent authors in top-general biomedical journals) produce more
    impactful patents.
    """
    paper = SciSciPaper(
        paper_id="arts2025_frontier_scientists",
        title="Not like the others: Frontier scientists for inventive performance",
        authors=["Thomas Schaper", "Sam Arts", "Reinhilde Veugelers"],
        venue="Research Policy",
        year=2025,
        doi="10.1016/j.respol.2025.105339",
        research_idea="Examine whether corporate inventors who publish frontier science (recent articles in top-general biomedical journals) produce more impactful patents than non-author inventors and non-frontier author-inventors. Investigate boundary-spanning and frontier-science-referencing as mechanisms.",
        research_question="Do corporate patents invented by frontier scientists have higher technological impact and private value compared to patents by other inventors, and what mechanisms explain this premium?",
        hypotheses=[
            "Patents by frontier authors receive more forward citations (higher technology impact)",
            "Patents by frontier authors are more likely to become technology hits",
            "Patents by frontier authors have broader technology impact across fields",
            "Frontier-author patents have higher private value for the firm",
            "The frontier-author premium is partially mediated by greater use of frontier science prior art references",
        ],
        data_source="USPTO, PubMed, Microsoft Academic Graph, OpenAlex, CRSP/Compustat",
        data_description="237,345 U.S. biomedical patents (1980-2009) linked to PubMed articles via inventor-author disambiguation (Torvik 2018, Li et al. 2014). Patent-level dependent variables: forward citations, hit probability, generality index, Kogan private value.",
        available_fields=["patent_id", "filing_year", "grant_year", "inventor_ids", "assignee_firm",
                          "forward_citations", "generality_index", "kogan_value",
                          "frontier_author_flag", "author_pub_years", "journal_tier",
                          "science_references", "frontier_science_refs", "firm_age", "firm_size"],
        sample_scope={"time_window": "1980-2009 (patent filing)",
                       "fields": ["biomedical"],
                       "filters": ["USPTO utility patents", "corporate assignees",
                                    "biomedical IPC classes", "PubMed-indexed publications"]},
        independent_variables=[
            {"name": "frontier_author", "type": "binary",
             "definition": "Patent has at least one inventor who published an article in a top-general biomedical journal (Nature, Science, Cell, NEJM, JAMA, Lancet, PNAS) within the past 3 years before patent filing"},
            {"name": "non_frontier_author", "type": "binary",
             "definition": "Patent has inventor-authors who published but NOT recently in top-general journals (comparison group)"},
            {"name": "first_frontier_author", "type": "binary",
             "definition": "At least one first-author position among frontier authors on the patent"},
        ],
        dependent_variables=[
            {"name": "forward_citations", "type": "count",
             "formula": "Number of citations received by the patent within 5 years after grant (excluding self-citations)"},
            {"name": "tech_hit", "type": "binary",
             "formula": "1 if patent is in top 5% of forward citation distribution within its 3-digit IPC×year cohort, 0 otherwise"},
            {"name": "generality_index", "type": "continuous",
             "formula": "G = 1 - Σ_k s_k² where s_k is the share of forward citations from IPC class k. Higher G means broader technology impact."},
            {"name": "kogan_private_value", "type": "continuous",
             "formula": "Stock market reaction-adjusted patent value from Kogan et al. (2017), log-transformed"},
        ],
        control_variables=[
            {"name": "firm_fixed_effects", "type": "categorical",
             "rationale": "Absorb time-invariant firm heterogeneity"},
            {"name": "patent_filing_year_fe", "type": "categorical",
             "rationale": "Control for secular trends in patenting and citations"},
            {"name": "IPC_3digit_fe", "type": "categorical",
             "rationale": "Control for technology-field-specific citation patterns"},
            {"name": "inventor_team_size", "type": "count",
             "rationale": "Larger teams may produce more impactful patents"},
            {"name": "firm_patent_stock", "type": "count",
             "rationale": "Control for firm R&D scale and patent portfolio size"},
            {"name": "firm_age", "type": "continuous",
             "rationale": "Young vs mature firm innovation patterns differ"},
            {"name": "science_ref_count", "type": "count",
             "rationale": "Number of non-patent scientific references on the patent"},
        ],
        experiment_design_gold={
            "statistical_method": {
                "family": "fixed_effects",
                "specification": "Y_i = α + β₁·FrontierAuthor_i + γ·Controls_i + δ_firm + θ_year + λ_IPC + ε_i. Logit for binary outcomes (tech_hit), OLS for log-transformed continuous outcomes (citations, generality, Kogan value). Standard errors clustered at firm level.",
                "estimation": "OLS",
            },
            "network_construction": {
                "node_type": "none",
                "edge_type": "none",
                "directed": False,
                "weighted": False,
                "temporal": False,
                "construction_method": "Not a network study. Patent citation counts and generality index computed from USPTO citation data.",
            },
            "grouping_strategy": {
                "groups": ["frontier_author", "non_frontier_author (not frontier)", "non_author_inventor"],
                "rationale": "Compare frontier-author patents against two control groups to isolate frontier effect from general author effect",
                "treatment": "Frontier author status is the treatment of interest; comparison groups are non-frontier authors and non-author inventors",
            },
            "expected_result_form": {
                "type": "regression_table",
                "key_quantities": ["β_frontier_author (main effect)", "marginal effect on hit probability",
                                   "coefficient on frontier_science_refs (mechanism)", "firm_FE × frontier interaction"],
            },
        },
        robustness_checks=[
            {"method": "Firm fixed effects + inventor fixed effects",
             "rationale": "Absorb unobserved firm and inventor heterogeneity"},
            {"method": "Alternative frontier definitions: field-specific top journals, 5-year window, lower journal tiers",
             "rationale": "Test sensitivity to frontier operationalization; premium should weaken with broader definitions"},
            {"method": "First-author frontier specification",
             "rationale": "Test whether lead-author frontier status matters more than team-member status"},
            {"method": "Subsample analysis: young scaled-up biopharma firms vs others",
             "rationale": "Theory predicts frontier science matters more in R&D-intensive young firms"},
            {"method": "Internal vs external frontier authors",
             "rationale": "Test whether internally employed frontier scientists confer more benefit than external collaborators"},
            {"method": "Matching on propensity score for frontier author status",
             "rationale": "Address selection on observables; compare frontier and non-frontier patents with similar ex-ante characteristics"},
        ],
        result_claims=[
            {"metric": "Frontier-author patent forward citations", "value": "+15-25% premium",
             "direction": "positive", "significance": "p < 0.01"},
            {"metric": "Technology hit probability", "value": "+30-50% higher likelihood",
             "direction": "positive", "significance": "p < 0.01"},
            {"metric": "Generality/broad impact", "value": "significantly broader",
             "direction": "positive", "significance": "p < 0.05"},
            {"metric": "Kogan private value", "value": "+20-30% premium",
             "direction": "positive", "significance": "p < 0.05"},
            {"metric": "Frontier science reference mechanism", "value": "Partial mediation confirmed",
             "direction": "positive", "significance": "Frontier-author premium persists even without frontier refs"},
        ],
        partial_results=[
            {"metric": "Exact mechanism decomposition",
             "note": "Premiums exist for both frontier-science-referencing and non-referencing patents; full mechanism remains partially unexplained"},
            {"metric": "External frontier authors",
             "note": "Sample size limited for externally-employed frontier author analysis; results suggestive but not conclusive"},
            {"metric": "Non-biomedical industries",
             "note": "Analysis limited to biomedical sector; generalizability to other industries untested"},
        ],
        conclusion_claims=[
            "Corporate patents by frontier scientists have significantly higher technology impact than patents by non-author inventors and non-frontier authors",
            "The frontier-author premium is strongest in young scaled-up biopharmaceutical firms and for internally employed frontier scientists",
            "Greater use of frontier science as prior art partially explains but does not fully account for the frontier-author premium",
            "Recency and top-general nature of the science matter: the premium weakens when using lower-tier journals or longer publication windows",
        ],
        limitations=[
            "Analysis limited to biomedical sector; findings may not generalize to other industries (e.g., software, chemicals)",
            "Selection on unobservables: frontier authors may select into firms/projects with inherently higher innovative potential",
            "Author-inventor disambiguation may have false positives/negatives despite using validated linkage methods",
            "Kogan private value data available for only 36% of sample (public firms only)",
            "Causal interpretation limited: despite FE and matching, unobserved time-varying confounders may remain",
            "Frontier science definition based on top-general journals may miss important frontier work in specialized outlets",
        ],
    )
    return paper
