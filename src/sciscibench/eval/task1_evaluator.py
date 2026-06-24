"""Task 1 Automated Evaluation.

Compares agent experiment design JSON against gold paper annotation.

Metrics:
  - Variable Match: Semantic similarity + exact match on variable names/definitions
  - Model Match: Statistical method family match + specification similarity
  - Data Protocol Match: Sample scope, time window, filter overlap
  - Robustness Coverage: F1 on robustness check methods
  - Schema Validity: Output passes JSON Schema validation
  - Feasibility: Design actually executes in sandbox (optional, requires SciSciNet)
"""

from __future__ import annotations

import json
import math
from dataclasses import dataclass, field
from typing import Any


def _tokenize(text: str) -> set[str]:
    """Simple whitespace+punctuation tokenizer for overlap scoring."""
    import re
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _jaccard(a: set[str], b: set[str]) -> float:
    if not a and not b:
        return 1.0
    return len(a & b) / len(a | b)


def _semantic_overlap(text_a: str, text_b: str) -> float:
    """Token-level Jaccard similarity as a cheap semantic proxy."""
    return _jaccard(_tokenize(text_a), _tokenize(text_b))


@dataclass
class VariableMatchResult:
    """Per-variable-type match scores."""
    precision: float = 0.0
    recall: float = 0.0
    f1: float = 0.0
    exact_matches: list[str] = field(default_factory=list)
    partial_matches: list[tuple[str, str, float]] = field(default_factory=list)
    missing: list[str] = field(default_factory=list)
    extra: list[str] = field(default_factory=list)

    @property
    def score(self) -> float:
        return self.f1


@dataclass
class Task1EvalResult:
    """Full Task 1 evaluation result."""
    paper_id: str
    condition: str
    schema_valid: bool = False
    schema_violations: list[str] = field(default_factory=list)
    independent_var_match: VariableMatchResult = field(default_factory=VariableMatchResult)
    dependent_var_match: VariableMatchResult = field(default_factory=VariableMatchResult)
    control_var_match: VariableMatchResult = field(default_factory=VariableMatchResult)
    model_match: float = 0.0
    model_match_detail: dict[str, Any] = field(default_factory=dict)
    data_protocol_match: float = 0.0
    data_protocol_detail: dict[str, Any] = field(default_factory=dict)
    robustness_f1: float = 0.0
    robustness_detail: dict[str, Any] = field(default_factory=dict)
    feasibility: float = 0.0
    feasibility_detail: dict[str, Any] = field(default_factory=dict)
    overall_f1: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "condition": self.condition,
            "schema_valid": self.schema_valid,
            "schema_violations": self.schema_violations,
            "independent_var_match": {
                "precision": self.independent_var_match.precision,
                "recall": self.independent_var_match.recall,
                "f1": self.independent_var_match.f1,
                "exact_matches": self.independent_var_match.exact_matches,
                "partial_matches": self.independent_var_match.partial_matches,
                "missing": self.independent_var_match.missing,
                "extra": self.independent_var_match.extra,
            },
            "dependent_var_match": {
                "precision": self.dependent_var_match.precision,
                "recall": self.dependent_var_match.recall,
                "f1": self.dependent_var_match.f1,
                "exact_matches": self.dependent_var_match.exact_matches,
                "partial_matches": self.dependent_var_match.partial_matches,
                "missing": self.dependent_var_match.missing,
                "extra": self.dependent_var_match.extra,
            },
            "control_var_match": {
                "precision": self.control_var_match.precision,
                "recall": self.control_var_match.recall,
                "f1": self.control_var_match.f1,
                "exact_matches": self.control_var_match.exact_matches,
                "partial_matches": self.control_var_match.partial_matches,
                "missing": self.control_var_match.missing,
                "extra": self.control_var_match.extra,
            },
            "model_match": self.model_match,
            "model_match_detail": self.model_match_detail,
            "data_protocol_match": self.data_protocol_match,
            "data_protocol_detail": self.data_protocol_detail,
            "robustness_f1": self.robustness_f1,
            "robustness_detail": self.robustness_detail,
            "feasibility": self.feasibility,
            "feasibility_detail": self.feasibility_detail,
            "overall_f1": self.overall_f1,
        }


@dataclass
class Task1Evaluator:
    """Evaluates Task 1 outputs against gold annotations."""

    similarity_threshold: float = 0.75
    exact_match_weight: float = 0.5
    semantic_weight: float = 0.5

    @staticmethod
    def validate_schema(output: dict) -> tuple[bool, list[str]]:
        """Validate output against required structure."""
        violations = []

        required = ["independent_variables", "dependent_variables", "control_variables",
                     "statistical_method", "sample_scope"]
        for key in required:
            if key not in output:
                violations.append(f"Missing required field: {key}")

        ivs = output.get("independent_variables", [])
        if not isinstance(ivs, list) or len(ivs) == 0:
            violations.append("independent_variables must be non-empty array")
        else:
            for i, iv in enumerate(ivs):
                for f in ["name", "type", "definition"]:
                    if f not in iv:
                        violations.append(f"independent_variable[{i}] missing '{f}'")

        dvs = output.get("dependent_variables", [])
        if not isinstance(dvs, list) or len(dvs) == 0:
            violations.append("dependent_variables must be non-empty array")
        else:
            for i, dv in enumerate(dvs):
                for f in ["name", "type", "formula"]:
                    if f not in dv:
                        violations.append(f"dependent_variable[{i}] missing '{f}'")

        sm = output.get("statistical_method", {})
        if not isinstance(sm, dict):
            violations.append("statistical_method must be an object")
        else:
            for f in ["family", "specification"]:
                if f not in sm:
                    violations.append(f"statistical_method missing '{f}'")

        ss = output.get("sample_scope", {})
        if not isinstance(ss, dict):
            violations.append("sample_scope must be an object")
        elif "time_window" not in ss:
            violations.append("sample_scope missing 'time_window'")

        return len(violations) == 0, violations

    def _match_variables(
        self,
        gold: list[dict[str, Any]],
        pred: list[dict[str, Any]],
    ) -> VariableMatchResult:
        """Match predicted variables to gold variables by name and definition similarity.

        Each variable pair scores max(exact_name_match, semantic_similarity).
        Precision = average best-score per prediction. Recall = average best-score per gold.
        """
        result = VariableMatchResult()

        gold_names = {v.get("name", "").lower().strip(): v for v in gold}
        pred_names = {v.get("name", "").lower().strip(): v for v in pred}

        # Exact name matches
        exact = set(gold_names.keys()) & set(pred_names.keys())
        result.exact_matches = sorted(exact)
        result.missing = sorted(set(gold_names.keys()) - set(pred_names.keys()))
        result.extra = sorted(set(pred_names.keys()) - set(gold_names.keys()))

        # For each gold variable, find best matching pred variable score
        gold_scores: list[float] = []
        for gn, gv in gold_names.items():
            if gn in exact:
                gold_scores.append(1.0)
            else:
                gdef = gv.get("definition", gv.get("formula", ""))
                best = 0.0
                best_pn = ""
                for pn in result.extra:
                    pdef = pred_names[pn].get("definition", pred_names[pn].get("formula", ""))
                    sim = _semantic_overlap(gdef, pdef)
                    if sim > best:
                        best = sim
                        best_pn = pn
                gold_scores.append(best)
                if best >= self.similarity_threshold:
                    result.partial_matches.append((gn, best_pn, best))

        # For each pred variable, find best matching gold variable score
        pred_scores: list[float] = []
        for pn, pv in pred_names.items():
            if pn in exact:
                pred_scores.append(1.0)
            else:
                pdef = pv.get("definition", pv.get("formula", ""))
                best = 0.0
                for gn in result.missing:
                    gdef = gold_names[gn].get("definition", gold_names[gn].get("formula", ""))
                    sim = _semantic_overlap(pdef, gdef)
                    best = max(best, sim)
                pred_scores.append(best)

        result.precision = sum(pred_scores) / max(len(pred_scores), 1)
        result.recall = sum(gold_scores) / max(len(gold_scores), 1)

        if result.precision + result.recall > 0:
            result.f1 = 2 * result.precision * result.recall / (result.precision + result.recall)

        return result

    # Model family categories for lenient matching
    MODEL_FAMILY_GROUPS: dict[str, set[str]] = field(default_factory=lambda: {
        "regression": {"ols", "regression", "linear_regression", "logistic", "logit",
                       "probit", "glm", "generalized_linear_model", "poisson",
                       "negative_binomial", "fixed_effects", "random_effects",
                       "mixed_effects", "multilevel", "hierarchical", "panel"},
        "descriptive": {"descriptive", "descriptive_statistics", "summary_statistics",
                        "exploratory", "eda", "distribution", "mean", "median",
                        "percentile", "decile", "trend", "time_series_plot"},
        "network_analysis": {"network_analysis", "graph_analysis", "network_science",
                            "network_measure", "centrality", "community_detection"},
        "nonparametric_test": {"nonparametric", "nonparametric_test", "non_parametric",
                               "permutation", "bootstrap", "ks_test", "mann_whitney",
                               "wilcoxon", "kruskal_wallis", "chi_squared", "fisher_exact"},
        "causal_inference": {"causal", "causal_inference", "difference_in_differences",
                            "did", "instrumental_variable", "iv", "rdd",
                            "regression_discontinuity", "propensity_score",
                            "matching", "synthetic_control"},
        "machine_learning": {"machine_learning", "ml", "random_forest", "xgboost",
                            "neural_network", "deep_learning", "svm", "knn",
                            "clustering", "pca", "topic_modeling", "lda"},
        "bayesian": {"bayesian", "mcmc", "hierarchical_bayes", "stan", "bugs"},
        "survival_analysis": {"survival", "cox", "hazard", "kaplan_meier"},
        "text_analysis": {"text_analysis", "nlp", "tfidf", "word2vec", "bert",
                         "embedding", "topic_model", "sentiment"},
    })

    def _classify_family(self, family: str) -> str:
        """Map a model family string to its broad category."""
        f = family.lower().strip().replace(" ", "_")
        f_clean = f.replace("-", "_")
        for category, keywords in self.MODEL_FAMILY_GROUPS.items():
            if f in keywords or f_clean in keywords:
                return category
            # Check if any keyword is a substring of family or vice versa
            for kw in keywords:
                if len(kw) > 3 and (kw in f or f in kw):
                    return category
        return f  # unknown, return as-is

    def _match_model(self, gold: dict, pred: dict) -> tuple[float, dict]:
        """Compare statistical method specifications with lenient family matching."""
        detail = {}

        g_family = gold.get("family", "").lower().strip()
        p_family = pred.get("family", "").lower().strip()

        # Lenient category matching
        g_category = self._classify_family(g_family)
        p_category = self._classify_family(p_family)
        family_match = 1.0 if g_category == p_category else (
            0.5 if g_category and p_category else 0.0
        )
        detail["family_match"] = family_match
        detail["gold_family"] = g_family
        detail["pred_family"] = p_family
        detail["gold_category"] = g_category
        detail["pred_category"] = p_category

        g_spec = gold.get("specification", "")
        p_spec = pred.get("specification", "")
        spec_sim = _semantic_overlap(g_spec, p_spec)
        detail["specification_similarity"] = spec_sim

        g_est = gold.get("estimation", "")
        p_est = pred.get("estimation", "")
        # Lenient estimation matching
        g_est_cat = self._classify_family(g_est) if g_est else ""
        p_est_cat = self._classify_family(p_est) if p_est else ""
        est_match = 1.0 if g_est.lower() == p_est.lower() else (
            0.5 if g_est_cat and p_est_cat and g_est_cat == p_est_cat else 0.0
        )
        detail["estimation_match"] = est_match

        score = 0.4 * family_match + 0.4 * spec_sim + 0.2 * est_match
        return score, detail

    def _match_data_protocol(self, gold: dict, pred: dict) -> tuple[float, dict]:
        """Compare sample scope: time window, fields, filters."""
        detail = {}

        g_tw = gold.get("time_window", "").strip()
        p_tw = pred.get("time_window", "").strip()
        tw_match = 1.0 if g_tw == p_tw else (_semantic_overlap(g_tw, p_tw) if g_tw and p_tw else 0.0)
        detail["time_window_match"] = tw_match
        detail["gold_time_window"] = g_tw
        detail["pred_time_window"] = p_tw

        g_fields = set(f.lower().strip() for f in gold.get("fields", []))
        p_fields = set(f.lower().strip() for f in pred.get("fields", []))
        field_f1 = _jaccard(g_fields, p_fields) if g_fields or p_fields else 1.0
        detail["field_f1"] = field_f1

        g_filters = set(f.lower().strip() for f in gold.get("filters", []))
        p_filters = set(f.lower().strip() for f in pred.get("filters", []))
        filter_f1 = _jaccard(g_filters, p_filters) if g_filters or p_filters else 1.0
        detail["filter_f1"] = filter_f1

        score = 0.4 * tw_match + 0.3 * field_f1 + 0.3 * filter_f1
        return score, detail

    def _match_robustness(self, gold: list[dict], pred: list[dict]) -> tuple[float, dict]:
        """F1 on robustness check methods."""
        g_methods = set()
        for g in gold:
            m = g.get("method", "").lower().strip()
            if m:
                g_methods.add(m)

        p_methods = set()
        for p in pred:
            m = p.get("method", "").lower().strip()
            if m:
                p_methods.add(m)

        # Exact match + soft match via token overlap
        exact_matches = g_methods & p_methods
        unmatched_g = g_methods - p_methods
        unmatched_p = p_methods - g_methods

        soft_matches = 0
        soft_pairs = []
        for gm in list(unmatched_g):
            best = 0.0
            best_pm = ""
            for pm in list(unmatched_p):
                sim = _semantic_overlap(gm, pm)
                if sim > best:
                    best = sim
                    best_pm = pm
            if best >= self.similarity_threshold:
                soft_matches += 1
                soft_pairs.append((gm, best_pm, best))

        tp = len(exact_matches) + soft_matches
        fp = len(p_methods) - tp
        fn = len(g_methods) - tp

        precision = tp / max(tp + fp, 1)
        recall = tp / max(tp + fn, 1)
        f1 = 2 * precision * recall / max(precision + recall, 0.001)

        return f1, {
            "exact_matches": sorted(exact_matches),
            "soft_matches": soft_pairs,
            "precision": precision,
            "recall": recall,
            "f1": f1,
        }

    def _check_feasibility(self, output: dict) -> tuple[float, dict]:
        """Assess whether the design is executable (structural check, no actual run)."""
        checks = {}
        score = 0.0
        count = 0

        # Check 1: Has enough variables
        ivs = output.get("independent_variables", [])
        dvs = output.get("dependent_variables", [])
        has_min_vars = len(ivs) >= 1 and len(dvs) >= 1
        checks["has_min_variables"] = has_min_vars
        score += 1.0 if has_min_vars else 0.0
        count += 1

        # Check 2: Variables have definitions/formulas
        iv_defined = all("definition" in v for v in ivs) if ivs else False
        dv_formula = all("formula" in v for v in dvs) if dvs else False
        vars_defined = iv_defined and dv_formula
        checks["variables_defined"] = vars_defined
        score += 1.0 if vars_defined else 0.0
        count += 1

        # Check 3: Statistical method has specification
        sm = output.get("statistical_method", {})
        has_spec = bool(sm.get("specification", ""))
        checks["has_method_spec"] = has_spec
        score += 1.0 if has_spec else 0.0
        count += 1

        # Check 4: Sample scope has time window
        ss = output.get("sample_scope", {})
        has_tw = bool(ss.get("time_window", ""))
        checks["has_time_window"] = has_tw
        score += 1.0 if has_tw else 0.0
        count += 1

        # Check 5: No obvious contradictions (type consistency)
        valid_types = {"continuous", "categorical", "binary", "count"}
        iv_types_ok = all(v.get("type", "") in valid_types for v in ivs)
        dv_types_ok = all(v.get("type", "") in valid_types for v in dvs)
        types_ok = iv_types_ok and dv_types_ok
        checks["variable_types_valid"] = types_ok
        score += 1.0 if types_ok else 0.0
        count += 1

        return score / max(count, 1), checks

    def evaluate(self, gold: dict[str, Any], pred: dict[str, Any],
                 paper_id: str = "", condition: str = "") -> Task1EvalResult:
        """Run full Task 1 evaluation."""
        result = Task1EvalResult(paper_id=paper_id, condition=condition)

        # Schema validation
        result.schema_valid, result.schema_violations = self.validate_schema(pred)
        if not result.schema_valid:
            # Major schema violations → overall score penalized heavily
            result.overall_f1 = 0.0
            return result

        # Independent variables match
        result.independent_var_match = self._match_variables(
            gold.get("independent_variables", []),
            pred.get("independent_variables", []),
        )

        # Dependent variables match
        result.dependent_var_match = self._match_variables(
            gold.get("dependent_variables", []),
            pred.get("dependent_variables", []),
        )

        # Control variables match
        result.control_var_match = self._match_variables(
            gold.get("control_variables", []),
            pred.get("control_variables", []),
        )

        # Model match
        result.model_match, result.model_match_detail = self._match_model(
            gold.get("statistical_method", {}),
            pred.get("statistical_method", {}),
        )

        # Data protocol match
        result.data_protocol_match, result.data_protocol_detail = self._match_data_protocol(
            gold.get("sample_scope", {}),
            pred.get("sample_scope", {}),
        )

        # Robustness coverage
        result.robustness_f1, result.robustness_detail = self._match_robustness(
            gold.get("robustness_checks", []),
            pred.get("robustness_checks", []),
        )

        # Feasibility
        result.feasibility, result.feasibility_detail = self._check_feasibility(pred)

        # Overall weighted F1
        weights = {
            "independent_var": 0.20,
            "dependent_var": 0.25,
            "control_var": 0.10,
            "model": 0.20,
            "data_protocol": 0.10,
            "robustness": 0.10,
            "feasibility": 0.05,
        }
        result.overall_f1 = (
            weights["independent_var"] * result.independent_var_match.f1 +
            weights["dependent_var"] * result.dependent_var_match.f1 +
            weights["control_var"] * result.control_var_match.f1 +
            weights["model"] * result.model_match +
            weights["data_protocol"] * result.data_protocol_match +
            weights["robustness"] * result.robustness_f1 +
            weights["feasibility"] * result.feasibility
        )

        return result
