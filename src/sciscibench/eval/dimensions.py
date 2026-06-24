"""5-dimension reproduction quality evaluation.

Dimensions:
  D1 - Fidelity:         Was the right thing done?
  D2 - Executability:    Does the code actually run?
  D3 - Numerical Accuracy: Are the numbers close?
  D4 - Claim Consistency:  Do conclusions match?
  D5 - Auditability:     Is the process traceable and honest?

Each dimension is scored 0-1, applied to applicable components per the
Components × Dimensions matrix defined in EXPERIMENT_PLAN.md.

Task Type Taxonomy (from EXPERIMENT_PLAN.md):
  STRICT       — Same data, same sample, same model; target is numerical identity
  DATA_SUB     — Different data source; target is direction/mechanism consistency
  METHOD       — Only reproduce method; no original numerical targets
  CLAIM_ROBUST — Use new data to test whether original conclusions hold

For DATA_SUB and METHOD types, D3 (Numerical Accuracy) is computed but
labeled "reference-only" — it documents the difference but does not factor
into pass/fail. The decisive metrics shift to direction match (D4) and
fidelity (D1).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Optional


class TaskType(str, Enum):
    """Task type determines how dimension scores are interpreted."""
    STRICT = "strict"
    DATA_SUB = "data_sub"
    METHOD = "method"
    CLAIM_ROBUST = "claim_robust"

    @classmethod
    def from_label(cls, label: str) -> "TaskType":
        """Parse from short labels used in EXPERIMENT_TRACKER.md."""
        label = label.upper().replace("-", "_").replace(" ", "_")
        mapping = {
            "STRICT": cls.STRICT,
            "DATA_SUB": cls.DATA_SUB,
            "DATA_SUBSTITUTED": cls.DATA_SUB,
            "METHOD": cls.METHOD,
            "METHOD_REIMPLEMENTATION": cls.METHOD,
            "CLAIM_ROBUST": cls.CLAIM_ROBUST,
            "CLAIM_ROBUSTNESS": cls.CLAIM_ROBUST,
        }
        return mapping.get(label, cls.METHOD)


def is_numerical_accuracy_applicable(task_type: TaskType) -> bool:
    """Whether D3 should be treated as a pass/fail criterion.

    For DATA_SUB and METHOD types, D3 is reference-only.
    """
    return task_type == TaskType.STRICT


@dataclass
class DimensionScore:
    """Score for one dimension on one component."""
    dimension: str
    component: str
    score: float  # 0-1
    rationale: str = ""
    evidence: dict[str, Any] = field(default_factory=dict)


@dataclass
class ComponentScore:
    """Aggregate score for one component across all applicable dimensions."""
    component: str
    dimension_scores: dict[str, DimensionScore] = field(default_factory=dict)

    @property
    def aggregate(self) -> float:
        if not self.dimension_scores:
            return 0.0
        return sum(d.score for d in self.dimension_scores.values()) / len(self.dimension_scores)


@dataclass
class ReproductionProfile:
    """Full 6×5 reproduction profile for one paper."""
    paper_id: str
    component_scores: dict[str, ComponentScore] = field(default_factory=dict)
    maturity_level: int = 0
    spurious_flags: list[str] = field(default_factory=list)

    def to_matrix(self) -> dict[str, dict[str, float]]:
        """Return {component: {dimension: score}} matrix."""
        matrix = {}
        for comp_name, comp in self.component_scores.items():
            matrix[comp_name] = {d.dimension: d.score for d in comp.dimension_scores.values()}
        return matrix

    def dimension_correlations(self) -> dict[str, float]:
        """Placeholder: compute pairwise dimension correlations across components."""
        return {}


# ── Dimension scoring rubrics ──

# Which dimensions apply to which components
COMPONENT_DIMENSION_MAP = {
    "data_source":       ["fidelity", "executability", "auditability"],
    "sample":            ["fidelity", "executability", "numerical_accuracy", "auditability"],
    "indicator":         ["fidelity", "executability", "numerical_accuracy", "auditability"],
    "model":             ["fidelity", "executability", "numerical_accuracy", "auditability"],
    "result_table":      ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"],
    "claim":             ["fidelity", "claim_consistency"],
}


def score_fidelity(component: str, gold: dict, agent: dict) -> DimensionScore:
    """D1: Fidelity — did the agent do the right thing?

    Per component:
      data_source: source name match (exact or semantic equivalent)
      sample: filter rule coverage (F1 on rules)
      indicator: formula match (structural + semantic)
      model: specification match (variables, FE, SE type)
      result_table: table structure match
      claim: claim coverage (which claims were addressed)
    """
    if component == "data_source":
        gold_source = gold.get("data_source", "").lower()
        agent_source = agent.get("data_source", "").lower()
        # Simple substring or semantic match
        if gold_source and agent_source:
            # Check key identifiers
            gold_tokens = set(gold_source.replace(",", " ").split())
            agent_tokens = set(agent_source.replace(",", " ").split())
            overlap = len(gold_tokens & agent_tokens)
            total = len(gold_tokens) if gold_tokens else 1
            score = min(1.0, overlap / total)
        else:
            score = 0.0
            overlap = 0
            total = 1
        return DimensionScore("fidelity", component, score,
                             f"Source name overlap: {overlap}/{total}",
                             {"gold_source": gold_source, "agent_source": agent_source})

    elif component == "sample":
        gold_rules = set(gold.get("filter_rules", []))
        agent_rules = set(agent.get("filter_rules", []))
        if gold_rules:
            tp = len(gold_rules & agent_rules)
            fp = len(agent_rules - gold_rules)
            fn = len(gold_rules - agent_rules)
            precision = tp / (tp + fp) if (tp + fp) > 0 else 0
            recall = tp / (tp + fn) if (tp + fn) > 0 else 0
            f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0
            score = f1
        else:
            score = 1.0 if not agent_rules else 0.5
        return DimensionScore("fidelity", component, score,
                             f"Rule F1: {score:.2f}",
                             {"gold_rules": list(gold_rules), "agent_rules": list(agent_rules)})

    elif component == "indicator":
        gold_formula = gold.get("formula", "")
        agent_formula = agent.get("formula", "")

        if not gold_formula:
            score = 0.5 if agent_formula else 0.0
            return DimensionScore("fidelity", component, score,
                                 "No gold formula available",
                                 {"gold_formula": gold_formula, "agent_formula": agent_formula})

        if not agent_formula:
            return DimensionScore("fidelity", component, 0.0,
                                 "Agent provided no formula",
                                 {"gold_formula": gold_formula, "agent_formula": ""})

        gold_lower = gold_formula.lower()
        agent_lower = agent_formula.lower()

        # ── Operation-level matching (4 sub-scores) ──

        # 1. Entity definition match (0.25): focal paper, citing paper, references
        entity_keywords = [
            "focal", "citing", "reference", "cited",
            "paper", "patent", "publication",
            "n_i", "n_j", "n_k", "ni", "nj", "nk",
            "only the focal", "both", "cites",
        ]
        entity_hits = sum(1 for kw in entity_keywords
                         if kw in gold_lower and kw in agent_lower)
        entity_score = entity_hits / max(1, sum(1 for kw in entity_keywords if kw in gold_lower))
        entity_score = max(0.1, entity_score)  # Floor: basic terms exist

        # 2. Component variable match (0.30): ni, nj, nk, D, c_i, etc.
        var_keywords = ["n_i", "n_j", "n_k", "ni", "nj", "nk",
                       "c_i", "ci", "d=", "ĉ", "ĉ", "disruption"]
        var_hits = sum(1 for kw in var_keywords
                      if kw in gold_lower and kw in agent_lower)
        var_total = max(1, sum(1 for kw in var_keywords if kw in gold_lower))
        var_score = var_hits / var_total if var_total > 0 else 0.5

        # 3. Mathematical operation match (0.30): fraction, subtraction, sum, ratio
        math_keywords = ["/", "÷", "−", "-", "+", "*", "×",
                        "numerator", "denominator", "ratio", "fraction",
                        "sum", "σ", "average", "mean", "⟨", "⟩"]
        math_hits = sum(1 for kw in math_keywords
                       if kw in gold_lower and kw in agent_lower)
        math_total = max(1, sum(1 for kw in math_keywords if kw in gold_lower))
        math_score = math_hits / math_total if math_total > 0 else 0.5

        # 4. Window/normalization/aggregation match (0.15)
        norm_keywords = ["window", "year", "t=", "t =",
                        "normaliz", "field", "discipline",
                        "log", "percentile", "decile"]
        norm_hits = sum(1 for kw in norm_keywords
                       if kw in gold_lower and kw in agent_lower)
        norm_total = max(1, sum(1 for kw in norm_keywords if kw in gold_lower))
        norm_score = norm_hits / norm_total if norm_total > 0 else 0.5

        # Weighted composite
        score = (0.25 * entity_score + 0.30 * var_score +
                 0.30 * math_score + 0.15 * norm_score)

        # Clamp to [0, 1]
        score = max(0.0, min(1.0, score))

        return DimensionScore("fidelity", component, score,
                             f"entity={entity_score:.2f}, var={var_score:.2f}, "
                             f"math={math_score:.2f}, norm={norm_score:.2f} → {score:.2f}",
                             {"entity_score": entity_score, "var_score": var_score,
                              "math_score": math_score, "norm_score": norm_score})

    elif component == "model":
        gold_spec = set(gold.get("spec_elements", []))
        agent_spec = set(agent.get("spec_elements", []))
        if gold_spec:
            overlap = len(gold_spec & agent_spec)
            score = min(1.0, overlap / len(gold_spec))
        else:
            overlap = 0
            score = 0.5
        return DimensionScore("fidelity", component, score,
                             f"Spec overlap: {overlap}/{len(gold_spec)}",
                             {"gold_spec": list(gold_spec), "agent_spec": list(agent_spec)})

    elif component == "result_table":
        gold_tables = gold.get("target_tables", [])
        agent_tables = agent.get("produced_tables", [])
        if gold_tables:
            score = min(1.0, len(agent_tables) / len(gold_tables)) if agent_tables else 0.0
        else:
            score = 0.5
        return DimensionScore("fidelity", component, score,
                             f"Tables: {len(agent_tables)}/{len(gold_tables)}",
                             {})

    elif component == "claim":
        gold_claims = gold.get("conclusion_claims", [])
        agent_claims = agent.get("conclusion_claims", [])
        if gold_claims:
            # Simple claim coverage
            addressed = sum(1 for gc in gold_claims
                           if any(gc.lower()[:30] in ac.lower() for ac in agent_claims))
            score = addressed / len(gold_claims)
        else:
            score = 0.0
        return DimensionScore("fidelity", component, score,
                             f"Claims addressed: {addressed}/{len(gold_claims)}" if gold_claims else "No gold claims",
                             {})

    return DimensionScore("fidelity", component, 0.5, "Unknown component", {})


def score_executability(component: str, agent: dict) -> DimensionScore:
    """D2: Executability — does the code run end-to-end?

    Binary per component (can run / cannot run), or 0.5 for partial.
    """
    if component in ("data_source", "sample", "indicator", "model", "result_table"):
        exec_ok = agent.get("code_executed", {}).get(component, False)
        score = 1.0 if exec_ok else 0.0
        return DimensionScore("executability", component, score,
                             "Code executed" if exec_ok else "Code failed or not run",
                             {"executed": exec_ok})
    return DimensionScore("executability", component, 0.0, "N/A", {})


def score_numerical_accuracy(component: str, gold: dict, agent: dict,
                            task_type: TaskType = TaskType.METHOD) -> DimensionScore:
    """D3: Numerical Accuracy — are the numbers close?

    Applies to: sample, indicator, model, result_table.

    For DATA_SUB and METHOD task types, D3 is computed but labeled
    "reference-only" — numerical differences are expected due to different
    data sources or sample populations. The decisive metrics shift to
    direction match (D4) and fidelity (D1).
    """
    reference_only = not is_numerical_accuracy_applicable(task_type)
    ref_note = " [reference-only — data-substituted]" if reference_only else ""

    if component == "sample":
        gold_n = gold.get("N", 0)
        agent_n = agent.get("N", 0)
        if gold_n > 0:
            error = abs(agent_n - gold_n) / gold_n
            score = max(0.0, 1.0 - error)
        else:
            score = 0.0
        return DimensionScore("numerical_accuracy", component, score,
                             f"N error: {error:.2%}{ref_note}" if gold_n > 0 else f"No gold N{ref_note}",
                             {"gold_N": gold_n, "agent_N": agent_n,
                              "reference_only": reference_only})

    elif component == "indicator":
        gold_dist = gold.get("indicator_stats", {})
        agent_dist = agent.get("indicator_stats", {})
        if gold_dist and agent_dist:
            mean_err = abs(agent_dist.get("mean", 0) - gold_dist.get("mean", 0))
            mean_err = mean_err / (abs(gold_dist.get("mean", 0)) + 1e-6)
            score = max(0.0, 1.0 - mean_err)
        else:
            score = 0.0
        return DimensionScore("numerical_accuracy", component, score,
                             f"Mean error: {mean_err:.2%}{ref_note}" if gold_dist else f"No distribution data{ref_note}",
                             {"reference_only": reference_only})

    elif component == "model":
        gold_coefs = gold.get("coefficients", {})
        agent_coefs = agent.get("coefficients", {})
        common_vars = set(gold_coefs) & set(agent_coefs)
        if common_vars:
            errors = []
            for v in common_vars:
                g = gold_coefs[v]
                a = agent_coefs[v]
                if abs(g) > 1e-6:
                    errors.append(abs(a - g) / abs(g))
            score = max(0.0, 1.0 - (sum(errors) / len(errors)) if errors else 0.0)
        else:
            score = 0.0
        return DimensionScore("numerical_accuracy", component, score,
                             f"Coefficient errors: {sum(errors)/len(errors):.2%}{ref_note}" if common_vars else f"No matching coefficients{ref_note}",
                             {"reference_only": reference_only})

    elif component == "result_table":
        gold_cells = gold.get("target_values", [])
        agent_cells = agent.get("reproduced_values", [])
        cell_errors = []
        if gold_cells and agent_cells and len(gold_cells) == len(agent_cells):
            for g, a in zip(gold_cells, agent_cells):
                gv = g.get("value", 0)
                av = a.get("value", 0)
                if abs(gv) > 1e-6:
                    cell_errors.append(abs(av - gv) / abs(gv))
            score = max(0.0, 1.0 - (sum(cell_errors) / len(cell_errors)) if cell_errors else 0.0)
        else:
            score = 0.0
        return DimensionScore("numerical_accuracy", component, score,
                             f"Cell error: {sum(cell_errors)/len(cell_errors):.2%}{ref_note}" if cell_errors else f"No matching cells{ref_note}",
                             {"reference_only": reference_only})

    return DimensionScore("numerical_accuracy", component, 0.0, f"N/A{ref_note}",
                         {"reference_only": reference_only})


def score_claim_consistency(component: str, gold: dict, agent: dict) -> DimensionScore:
    """D4: Claim Consistency — do conclusions match?

    Applies to: result_table, claim.
    """
    if component == "result_table":
        gold_dir = gold.get("expected_direction", "")
        agent_dir = agent.get("observed_direction", "")
        if gold_dir and agent_dir:
            score = 1.0 if gold_dir == agent_dir else 0.0
        else:
            score = 0.5
        return DimensionScore("claim_consistency", component, score,
                             f"Direction: gold={gold_dir}, agent={agent_dir}",
                             {"gold_direction": gold_dir, "agent_direction": agent_dir})

    elif component == "claim":
        gold_claims = gold.get("conclusion_claims", [])
        agent_claims = agent.get("conclusion_claims", [])
        agreements = 0
        if gold_claims and agent_claims:
            for gc in gold_claims:
                gc_lower = gc.lower()
                for ac in agent_claims:
                    ac_lower = ac.lower()
                    gc_words = set(gc_lower.split()) - {"the", "a", "an", "is", "are", "was", "were", "in", "of", "to", "and", "that"}
                    ac_words = set(ac_lower.split()) - {"the", "a", "an", "is", "are", "was", "were", "in", "of", "to", "and", "that"}
                    overlap = len(gc_words & ac_words) / max(1, len(gc_words))
                    if overlap > 0.5:
                        agreements += 1
                        break
            score = agreements / len(gold_claims) if gold_claims else 0.0
        else:
            score = 0.0
        return DimensionScore("claim_consistency", component, score,
                             f"Claims matched: {agreements}/{len(gold_claims)}" if gold_claims else "None",
                             {})

    return DimensionScore("claim_consistency", component, 0.0, "N/A", {})


def score_auditability(component: str, agent: dict) -> DimensionScore:
    """D5: Auditability — is the process traceable and honest?

    Applies to: data_source, sample, indicator, model, result_table.
    """
    if component in ("data_source", "sample", "indicator", "model", "result_table"):
        # Check for hard-coded values
        hard_coded = agent.get("hard_coded", {}).get(component, False)
        # Check for traceability
        traceable = agent.get("traceable", {}).get(component, False)
        # Check for hallucinations
        hallucinated = agent.get("hallucinated", {}).get(component, False)

        if hard_coded:
            score = 0.0
            reason = "Hard-coded values detected"
        elif hallucinated:
            score = 0.2
            reason = "Hallucinated variables/steps"
        elif traceable:
            score = 1.0
            reason = "Fully traceable"
        else:
            score = 0.5
            reason = "Partially traceable"

        return DimensionScore("auditability", component, score, reason,
                             {"hard_coded": hard_coded, "traceable": traceable, "hallucinated": hallucinated})

    return DimensionScore("auditability", component, 0.0, "N/A", {})


# ── Profile builder ──

def build_reproduction_profile(
    paper_id: str,
    gold: dict[str, Any],
    agent: dict[str, Any],
    task_type: TaskType = TaskType.METHOD,
) -> ReproductionProfile:
    """Build a full 6×5 reproduction profile from gold and agent outputs.

    Args:
        paper_id: Paper identifier
        gold: Gold annotation dict with per-component ground truth
              Keys: data_source, sample, indicator, model, result_table, claim
        agent: Agent output dict with per-component results
               Same key structure as gold
        task_type: Reproduction task type (STRICT, DATA_SUB, METHOD, CLAIM_ROBUST).
                   Determines whether D3 scores are pass/fail or reference-only.

    Returns:
        ReproductionProfile with all component × dimension scores
    """
    profile = ReproductionProfile(paper_id=paper_id)
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]

    for comp in components:
        comp_gold = gold.get(comp, {})
        comp_agent = agent.get(comp, {})
        dim_scores = {}

        applicable_dims = COMPONENT_DIMENSION_MAP.get(comp, [])

        for dim in applicable_dims:
            if dim == "fidelity":
                ds = score_fidelity(comp, comp_gold, comp_agent)
            elif dim == "executability":
                ds = score_executability(comp, comp_agent)
            elif dim == "numerical_accuracy":
                ds = score_numerical_accuracy(comp, comp_gold, comp_agent, task_type)
            elif dim == "claim_consistency":
                ds = score_claim_consistency(comp, comp_gold, comp_agent)
            elif dim == "auditability":
                ds = score_auditability(comp, comp_agent)
            else:
                continue
            dim_scores[dim] = ds

        profile.component_scores[comp] = ComponentScore(comp, dim_scores)

    return profile


def compute_maturity_level(profile: ReproductionProfile,
                         task_type: TaskType = TaskType.METHOD) -> int:
    """Determine reproduction maturity level (L0-L5) from profile.

    L0: No component executable
    L1: At least data + sample code runs
    L2: L1 + sample/indicator fidelity >= 0.5
    L3: L2 + (numerical accuracy >= 0.5 on model/result for STRICT)
              OR (direction match for DATA_SUB/METHOD)
    L4: L3 + claim consistency >= 0.5
    L5: L4 + auditability >= 0.7 on all applicable components, no hard-coding

    For DATA_SUB and METHOD task types, L3 uses direction match (D4)
    instead of numerical accuracy (D3), since numerical differences
    are expected with different data sources.
    """
    # L0 check: anything executable?
    exec_scores = [cs.dimension_scores.get("executability")
                   for cs in profile.component_scores.values()
                   if "executability" in cs.dimension_scores]
    any_exec = any(es and es.score > 0 for es in exec_scores)
    if not any_exec:
        return 0

    # L1: code runs for at least data + sample
    data_exec = profile.component_scores.get("data_source", ComponentScore("data_source"))
    sample_exec = profile.component_scores.get("sample", ComponentScore("sample"))
    if not (data_exec.dimension_scores.get("executability", DimensionScore("", "", 0)).score > 0 or
            sample_exec.dimension_scores.get("executability", DimensionScore("", "", 0)).score > 0):
        return 0

    # L2: fidelity check — which components matter depends on task type
    # STRICT: sample + indicator fidelity must both be reasonable
    # DATA_SUB/METHOD: indicator + model fidelity (sample N expected to differ)
    if is_numerical_accuracy_applicable(task_type):
        fidelity_components = ["sample", "indicator"]
    else:
        fidelity_components = ["indicator", "model"]

    avg_fidelity = 0.0
    fidelity_count = 0
    for comp_name in fidelity_components:
        comp = profile.component_scores.get(comp_name)
        if comp and "fidelity" in comp.dimension_scores:
            avg_fidelity += comp.dimension_scores["fidelity"].score
            fidelity_count += 1
    avg_fidelity = avg_fidelity / fidelity_count if fidelity_count > 0 else 0
    if avg_fidelity < 0.5:
        return 1

    # L3: numerical accuracy (STRICT) or direction match (DATA_SUB/METHOD)
    if is_numerical_accuracy_applicable(task_type):
        # STRICT: check numerical accuracy on model + result_table
        num_acc = 0.0
        num_count = 0
        for comp_name in ["model", "result_table"]:
            comp = profile.component_scores.get(comp_name)
            if comp and "numerical_accuracy" in comp.dimension_scores:
                num_acc += comp.dimension_scores["numerical_accuracy"].score
                num_count += 1
        avg_num = num_acc / num_count if num_count > 0 else 0
        if avg_num < 0.5:
            return 2
    else:
        # DATA_SUB/METHOD: check direction match instead of numerical accuracy
        claim_comp = profile.component_scores.get("result_table")
        if claim_comp and "claim_consistency" in claim_comp.dimension_scores:
            if claim_comp.dimension_scores["claim_consistency"].score < 0.5:
                return 2
    return 3  # Placeholder — L3-L5 require deeper analysis


def format_maturity(level: int, task_type: TaskType = TaskType.METHOD) -> str:
    """Format maturity level with task-type qualifier.

    STRICT types get unadorned labels (L0-L5) because every level is
    backed by numerical accuracy.  Non-STRICT types get a suffix because
    L3+ is based on direction match / fidelity rather than numerical
    agreement — an L3(ds) is NOT equivalent to an L3.

    Suffixes:
      (ds) = data-substituted — D3 is reference-only, L3 uses direction match
      (m)  = method reimplementation — same as data-sub
      (cr) = claim robustness check — same as data-sub
    """
    if task_type == TaskType.STRICT:
        return f"L{level}"
    suffix = {TaskType.DATA_SUB: "ds", TaskType.METHOD: "m",
              TaskType.CLAIM_ROBUST: "cr"}.get(task_type, "?")
    return f"L{level}({suffix})"


def detect_spurious_reproduction(profile: ReproductionProfile) -> list[str]:
    """Apply S-I to S-IV spurious detection rules.

    Returns list of spurious type labels that triggered.
    """
    flags = []

    # Extract key scores
    rrf_comp = profile.component_scores.get("result_table")
    dsf_comp = profile.component_scores.get("sample")
    vmf_comp = profile.component_scores.get("indicator")
    prf_scores = [cs.dimension_scores.get("auditability", DimensionScore("", "", 0)).score
                  for cs in profile.component_scores.values()
                  if "auditability" in cs.dimension_scores]
    avg_prf = sum(prf_scores) / len(prf_scores) if prf_scores else 0

    rrf = rrf_comp.dimension_scores.get("numerical_accuracy", DimensionScore("", "", 0)).score if rrf_comp else 0
    dsf = dsf_comp.dimension_scores.get("fidelity", DimensionScore("", "", 0)).score if dsf_comp else 0
    vmf = vmf_comp.dimension_scores.get("fidelity", DimensionScore("", "", 0)).score if vmf_comp else 0
    crs = 0.0
    if rrf_comp and "claim_consistency" in rrf_comp.dimension_scores:
        crs = rrf_comp.dimension_scores["claim_consistency"].score

    # S-I: Result-close but process-wrong
    # Two-tier: Strong (RRF≥0.8, audit≤0.4, ≥1 core process module<0.4)
    #           Weak   (RRF≥0.7, ≥2 core process modules <0.5)
    core_process_modules = [dsf, vmf,
                            (profile.component_scores.get("model").dimension_scores.get("fidelity", DimensionScore("", "", 0)).score
                             if profile.component_scores.get("model") else 0)]

    # Strong Spurious: results very close, but unauditable and at least one core module broken
    if rrf >= 0.8 and avg_prf <= 0.4:
        low_core = sum(1 for m in core_process_modules if m <= 0.4)
        if low_core >= 1:
            flags.append("S-I (Strong): Result-close, Process-wrong — high result fidelity but audit trail broken")

    # Weak Spurious: results close, but ≥2 core process modules suspiciously low
    if rrf >= 0.7:
        low_core = sum(1 for m in core_process_modules if m <= 0.5)
        if low_core >= 2 and avg_prf <= 0.6:
            if not any("S-I (Strong)" in f for f in flags):  # Don't double-count
                flags.append("S-I (Weak): Result-close, Process-questionable")

    # S-II: Claim-correct but evidence-missing
    if crs >= 0.7 and avg_prf <= 0.4:
        flags.append("S-II: Claim-correct, Evidence-missing")

    # S-III and S-IV require code/pipeline analysis, flagged for manual review
    for comp_name, comp in profile.component_scores.items():
        if "auditability" in comp.dimension_scores:
            aud = comp.dimension_scores["auditability"]
            if aud.evidence.get("hard_coded", False):
                flags.append(f"S-III: Hard-coded in {comp_name}")

    return flags
