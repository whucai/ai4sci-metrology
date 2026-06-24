"""Task 3 evaluation: Progressive Information Disclosure + Failure Taxonomy.

Evaluates Task 3 outputs against gold annotations, computing:
  - Performance curve across C0-C6 disclosure levels
  - Scaffold Dependence Index (SDI)
  - Failure taxonomy (11 error types)
  - Conclusion reliability / calibration metrics
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Any

from .task1_evaluator import Task1Evaluator, _semantic_overlap, _jaccard, _tokenize


# ── Failure taxonomy (11 types) ──

FAILURE_TYPES = [
    "data_misunderstanding",
    "metric_misdefinition",
    "sample_boundary_error",
    "confounder_omission",
    "model_mismatch",
    "robustness_superficiality",
    "direction_error",
    "significance_overclaim",
    "mechanism_hallucination",
    "limitation_blindness",
    "novelty_overstatement",
]


@dataclass
class FailureAnalysis:
    """Classifies failure modes in agent outputs."""

    paper_id: str
    failure_counts: dict[str, int] = field(default_factory=lambda: {ft: 0 for ft in FAILURE_TYPES})
    failure_details: list[dict[str, Any]] = field(default_factory=list)

    def add_failure(self, failure_type: str, detail: str, evidence: str = ""):
        if failure_type in self.failure_counts:
            self.failure_counts[failure_type] += 1
        self.failure_details.append({
            "type": failure_type,
            "detail": detail,
            "evidence": evidence,
        })

    def dominant_failures(self, top_k: int = 3) -> list[tuple[str, int]]:
        sorted_failures = sorted(self.failure_counts.items(), key=lambda x: -x[1])
        return sorted_failures[:top_k]


def classify_task1_failures(gold: dict, pred: dict) -> list[dict]:
    """Classify Task 1 output failures against gold."""
    failures = []

    # Data misunderstanding: sample scope mismatch
    g_ss = gold.get("sample_scope", {})
    p_ss = pred.get("sample_scope", {})
    g_tw = g_ss.get("time_window", "").strip()
    p_tw = p_ss.get("time_window", "").strip()
    if g_tw and p_tw and _semantic_overlap(g_tw, p_tw) < 0.3:
        failures.append({
            "type": "data_misunderstanding",
            "detail": f"Sample time window mismatch: gold='{g_tw}' vs pred='{p_tw}'",
            "severity": "major",
        })

    # Metric misdefinition: dependent variable formula mismatch
    for gv in gold.get("dependent_variables", []):
        gname = gv.get("name", "").lower()
        gformula = gv.get("formula", "")
        for pv in pred.get("dependent_variables", []):
            pname = pv.get("name", "").lower()
            pformula = pv.get("formula", "")
            if gname == pname and gformula and pformula:
                if _semantic_overlap(gformula, pformula) < 0.3:
                    failures.append({
                        "type": "metric_misdefinition",
                        "detail": f"Formula mismatch for '{gname}': gold='{gformula[:100]}' vs pred='{pformula[:100]}'",
                        "severity": "critical",
                    })

    # Sample boundary error: field filters mismatch
    g_fields = set(f.lower().strip() for f in g_ss.get("fields", []))
    p_fields = set(f.lower().strip() for f in p_ss.get("fields", []))
    if g_fields and p_fields and _jaccard(g_fields, p_fields) < 0.3:
        failures.append({
            "type": "sample_boundary_error",
            "detail": f"Field selection mismatch: gold={g_fields} vs pred={p_fields}",
            "severity": "major",
        })

    # Confounder omission: control variables missing
    g_cv = {v.get("name", "").lower() for v in gold.get("control_variables", [])}
    p_cv = {v.get("name", "").lower() for v in pred.get("control_variables", [])}
    omitted = g_cv - p_cv
    if len(omitted) >= 2:
        failures.append({
            "type": "confounder_omission",
            "detail": f"Missing control variables: {omitted}",
            "severity": "major",
        })

    # Model mismatch
    g_sm = gold.get("statistical_method", {})
    p_sm = pred.get("statistical_method", {})
    g_family = g_sm.get("family", "").lower()
    p_family = p_sm.get("family", "").lower()
    if g_family and p_family and g_family != p_family:
        failures.append({
            "type": "model_mismatch",
            "detail": f"Method family mismatch: gold='{g_family}' vs pred='{p_family}'",
            "severity": "critical",
        })

    # Robustness superficiality
    g_rob = gold.get("robustness_checks", [])
    p_rob = pred.get("robustness_checks", [])
    if len(p_rob) < len(g_rob) // 2:
        failures.append({
            "type": "robustness_superficiality",
            "detail": f"Only {len(p_rob)} robustness checks vs {len(g_rob)} gold checks",
            "severity": "minor",
        })

    return failures


def classify_task2_failures(gold: dict, pred: dict) -> list[dict]:
    """Classify Task 2 failure modes."""
    failures = []

    # Direction error
    pred_conclusions = pred.get("conclusions", []) or pred.get("output", {}).get("conclusions", [])
    gold_claims = gold.get("result_claims", [])

    for gc in gold_claims:
        gdir = gc.get("direction", "").lower() if isinstance(gc, dict) else ""
        if gdir:
            matched = False
            for pc in pred_conclusions:
                pdir = pc.get("direction", "").lower() if isinstance(pc, dict) else ""
                if pdir == gdir:
                    matched = True
                    break
            if not matched:
                failures.append({
                    "type": "direction_error",
                    "detail": f"Gold direction '{gdir}' not found in predicted conclusions",
                    "severity": "critical",
                })

    # Significance overclaim
    for pc in pred_conclusions:
        sig = pc.get("significance", "").lower() if isinstance(pc, dict) else ""
        support = pc.get("support_level", "").lower() if isinstance(pc, dict) else ""
        if "significant" in sig and support in ("weak", "none"):
            failures.append({
                "type": "significance_overclaim",
                "detail": f"Claim marked significant but support_level='{support}': {pc.get('claim', str(pc)[:100])}",
                "severity": "major",
            })

    # Limitation blindness
    gold_lims = gold.get("limitations", [])
    pred_lims = pred.get("limitations", []) or pred.get("output", {}).get("limitations", [])
    if len(gold_lims) >= 3 and len(pred_lims) <= 1:
        failures.append({
            "type": "limitation_blindness",
            "detail": f"Only {len(pred_lims)} limitations identified vs {len(gold_lims)} gold limitations",
            "severity": "major",
        })

    # Mechanism hallucination: check for unsupported causal claims
    for pc in pred_conclusions:
        claim_text = pc.get("claim", "") if isinstance(pc, dict) else str(pc)
        causal_keywords = ["because", "causes", "leads to", "drives", "mechanism", "due to"]
        evidence = pc.get("evidence", "") if isinstance(pc, dict) else ""
        if any(kw in claim_text.lower() for kw in causal_keywords) and not evidence:
            failures.append({
                "type": "mechanism_hallucination",
                "detail": f"Causal claim without evidence citation: '{claim_text[:150]}'",
                "severity": "critical",
            })

    # Novelty overstatement
    novelty_keywords = ["first", "novel", "new", "previously unknown", "pioneer"]
    for pc in pred_conclusions:
        claim_text = pc.get("claim", "") if isinstance(pc, dict) else str(pc)
        if any(kw in claim_text.lower() for kw in novelty_keywords):
            failures.append({
                "type": "novelty_overstatement",
                "detail": f"Novelty claim without verification: '{claim_text[:150]}'",
                "severity": "minor",
            })

    return failures


# ── Calibration metrics ──

@dataclass
class CalibrationResult:
    """Conclusion reliability calibration metrics."""

    calibration_error: float = 0.0
    unsupported_high_confidence_rate: float = 0.0
    abstention_accuracy: float = 0.0
    evidence_citation_accuracy: float = 0.0

    def to_dict(self) -> dict:
        return {
            "calibration_error": self.calibration_error,
            "unsupported_high_confidence_rate": self.unsupported_high_confidence_rate,
            "abstention_accuracy": self.abstention_accuracy,
            "evidence_citation_accuracy": self.evidence_citation_accuracy,
        }


def compute_calibration(pred_conclusions: list[dict],
                        gold_claims: list[dict]) -> CalibrationResult:
    """Compute calibration metrics for predicted conclusions.

    - calibration_error: |confidence - correctness|
    - unsupported_high_confidence_rate: claims with confidence > 0.7 but no evidence
    - abstention_accuracy: whether "not enough evidence" claims are correct
    - evidence_citation_accuracy: whether cited evidence actually supports the claim
    """
    result = CalibrationResult()
    if not pred_conclusions:
        return result

    total = len(pred_conclusions)

    # Confidence calibration
    gold_directions = {gc.get("claim", str(gc)): gc.get("direction", "")
                       for gc in gold_claims if isinstance(gc, dict)}
    conf_errors = []
    unsupported_high = 0
    evidence_ok = 0

    for pc in pred_conclusions:
        if not isinstance(pc, dict):
            continue
        confidence = pc.get("confidence", 0.5)
        evidence = pc.get("evidence", "")
        pdir = pc.get("direction", "")
        claim = pc.get("claim", "")

        # Calibration: direction match → correctness proxy
        any_match = any(
            (isinstance(gc, dict) and gc.get("direction", "").lower() == pdir.lower())
            for gc in gold_claims
        )
        correctness = 1.0 if any_match else 0.0
        conf_errors.append(abs(confidence - correctness))

        # Unsupported high confidence
        if confidence > 0.7 and not evidence:
            unsupported_high += 1

        # Evidence citation: if evidence is cited, check it's plausible
        if evidence:
            evidence_ok += 1  # Simple: count evidence presence, deeper check would need more

    result.calibration_error = sum(conf_errors) / max(len(conf_errors), 1)
    result.unsupported_high_confidence_rate = unsupported_high / max(total, 1)
    result.abstention_accuracy = 1.0  # Placeholder — needs explicit "not enough evidence" labels
    result.evidence_citation_accuracy = evidence_ok / max(total, 1)

    return result


# ── Task 3 Evaluator ──

@dataclass
class Task3EvalResult:
    """Full Task 3 evaluation result for one paper × level."""
    paper_id: str
    level: str
    experiment_design_f1: float = 0.0
    conclusion_score: float = 0.0
    failures: list[dict] = field(default_factory=list)
    calibration: CalibrationResult = field(default_factory=CalibrationResult)
    confidence: float = 0.0

    def to_dict(self) -> dict:
        return {
            "paper_id": self.paper_id,
            "level": self.level,
            "experiment_design_f1": self.experiment_design_f1,
            "conclusion_score": self.conclusion_score,
            "failures": self.failures,
            "calibration": self.calibration.to_dict(),
            "confidence": self.confidence,
        }


@dataclass
class Task3Evaluator:
    """Evaluates Task 3 progressive disclosure outputs."""

    task1_evaluator: Task1Evaluator = field(default_factory=Task1Evaluator)

    def evaluate(self, gold: dict, pred: dict, paper_id: str, level: str) -> Task3EvalResult:
        """Evaluate a single Task 3 output."""
        result = Task3EvalResult(paper_id=paper_id, level=level)

        pred_output = pred.get("output", {})
        result.confidence = pred_output.get("confidence", 0.5)

        # C0-C4: evaluate experiment design
        if level in ("C0", "C1", "C2", "C3", "C4"):
            t1_result = self.task1_evaluator.evaluate(
                gold=gold, pred=pred_output, paper_id=paper_id, condition=level,
            )
            result.experiment_design_f1 = t1_result.overall_f1
            result.failures = classify_task1_failures(gold, pred_output)

        # C5-C6: evaluate conclusions + calibration
        if level in ("C5", "C6"):
            from ..eval.task2_evaluator import Task2Evaluator
            t2_eval = Task2Evaluator()
            t2_result = t2_eval.evaluate(
                gold=gold, pred=pred, level="L2", paper_id=paper_id,
            )
            result.conclusion_score = t2_result.overall_score
            result.failures = classify_task2_failures(gold, pred_output)
            result.calibration = compute_calibration(
                pred_output.get("conclusions", []),
                gold.get("result_claims", []),
            )

        return result


# ── Performance curve analysis ──

@dataclass
class ProgressiveDisclosureAnalysis:
    """Aggregates results across all disclosure levels for a paper/model."""

    paper_id: str
    level_results: dict[str, Task3EvalResult] = field(default_factory=dict)

    def performance_curve(self) -> dict[str, float]:
        """Returns experiment_design_f1 for C0-C4, conclusion_score for C5-C6."""
        curve = {}
        for lvl in ["C0", "C1", "C2", "C3", "C4"]:
            if lvl in self.level_results:
                curve[lvl] = self.level_results[lvl].experiment_design_f1
        for lvl in ["C5", "C6"]:
            if lvl in self.level_results:
                curve[lvl] = self.level_results[lvl].conclusion_score
        return curve

    def sdi(self, high: str = "C4", low: str = "C0") -> float:
        curve = self.performance_curve()
        return curve.get(high, 0) - curve.get(low, 0)

    def total_failures_by_type(self) -> dict[str, int]:
        counts: dict[str, int] = {ft: 0 for ft in FAILURE_TYPES}
        for result in self.level_results.values():
            for f in result.failures:
                ft = f.get("type", "")
                if ft in counts:
                    counts[ft] += 1
        return counts
