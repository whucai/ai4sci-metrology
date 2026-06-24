"""Task 2 Automated Evaluation.

Compares agent conclusion inference against gold paper claims.

Metrics:
  - Direction Accuracy: Is the conclusion direction (positive/negative/null) correct?
  - Effect-size Similarity: Are coefficient/magnitude claims close?
  - Significance Match: Is the significance judgment consistent?
  - Claim Support Score: Are conclusions supported by provided results?
  - Limitation Awareness: Does agent identify key limitations?
  - Hallucinated Claim Rate: What fraction of claims lack evidence?
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal


def _tokenize(text: str) -> set[str]:
    return set(re.findall(r"[a-z0-9]+", text.lower()))


def _semantic_overlap(a: str, b: str) -> float:
    ta = _tokenize(a)
    tb = _tokenize(b)
    if not ta and not tb:
        return 1.0
    return len(ta & tb) / len(ta | tb)


def _variable_specificity(text: str, gold: dict[str, Any]) -> float:
    """Fraction of gold variable tokens that appear in text.

    Handles compound names: "team_size" matches "team size" and "TEAM_SIZE".
    Also includes the full variable name as a single token.
    """
    gold_var_tokens: set[str] = set()
    for v_list in [gold.get("independent_variables", []),
                   gold.get("dependent_variables", []),
                   gold.get("control_variables", [])]:
        for v in v_list:
            if isinstance(v, dict):
                name = v.get("name", "")
            else:
                name = str(v)
            if name and len(name) > 1:
                name_lower = name.lower()
                # Add the full name
                gold_var_tokens.add(name_lower)
                # Add individual tokens: "team_size" → ["team", "size"]
                for token in re.split(r"[_\-\s]+", name_lower):
                    if len(token) > 1:
                        gold_var_tokens.add(token)

    if not gold_var_tokens:
        return 0.0

    text_lower = text.lower()
    text_tokens = _tokenize(text_lower)
    # Also check raw substring for compound matches (e.g., "team size" matching "team_size")
    substring_matches = sum(1 for vt in gold_var_tokens if vt in text_lower)
    token_matches = sum(1 for vt in gold_var_tokens if vt in text_tokens)
    # Use the better of substring and token matching
    matched = max(substring_matches, token_matches)
    return matched / len(gold_var_tokens)


@dataclass
class DirectionResult:
    """Direction accuracy per conclusion."""
    correct: int = 0
    total: int = 0
    details: list[dict[str, Any]] = field(default_factory=list)

    @property
    def accuracy(self) -> float:
        return self.correct / max(self.total, 1)


@dataclass
class Task2EvalResult:
    """Full Task 2 evaluation result."""
    paper_id: str
    level: str
    direction_accuracy: float = 0.0
    direction_detail: DirectionResult = field(default_factory=DirectionResult)
    significance_match: float = 0.0
    significance_detail: dict[str, Any] = field(default_factory=dict)
    claim_support_score: float = 0.0
    claim_support_detail: dict[str, Any] = field(default_factory=dict)
    limitation_awareness: float = 0.0
    limitation_detail: dict[str, Any] = field(default_factory=dict)
    hallucinated_claim_rate: float = 0.0
    hallucinated_detail: dict[str, Any] = field(default_factory=dict)
    uncertainty_recognition: float = 0.0   # L3-specific
    overall_score: float = 0.0

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "level": self.level,
            "direction_accuracy": self.direction_accuracy,
            "direction_detail": {
                "correct": self.direction_detail.correct,
                "total": self.direction_detail.total,
                "details": self.direction_detail.details,
            },
            "significance_match": self.significance_match,
            "significance_detail": self.significance_detail,
            "claim_support_score": self.claim_support_score,
            "claim_support_detail": self.claim_support_detail,
            "limitation_awareness": self.limitation_awareness,
            "limitation_detail": self.limitation_detail,
            "hallucinated_claim_rate": self.hallucinated_claim_rate,
            "hallucinated_detail": self.hallucinated_detail,
            "uncertainty_recognition": self.uncertainty_recognition,
            "overall_score": self.overall_score,
        }


@dataclass
class Task2Evaluator:
    """Evaluates Task 2 outputs against gold claims."""

    direction_keywords: dict[str, list[str]] = field(default_factory=lambda: {
        "positive": ["positive", "increase", "increases", "higher", "greater", "more",
                      "enhanced", "improved", "positively", "develop", "development",
                      "consolidat", "large team"],
        "negative": ["negative", "decrease", "decreases", "lower", "less", "fewer",
                      "reduced", "diminished", "negatively", "inverse", "disrupt",
                      "disruption", "destabiliz", "small team", "novel"],
        "null": ["null", "no effect", "no significant", "no relationship",
                 "not significant", "no association", "no difference", "no evidence",
                 "insignificant", "unrelated"],
    })

    def _extract_direction(self, text: str) -> str | None:
        """Classify the direction of a claim from text."""
        text_lower = text.lower()
        scores = {}
        for direction, keywords in self.direction_keywords.items():
            scores[direction] = sum(1 for kw in keywords if kw in text_lower)
        max_score = max(scores.values())
        if max_score == 0:
            return "unknown"
        # If both positive and negative tie, prefer the higher-signal direction
        return max(scores, key=scores.get)

    @staticmethod
    def _parse_gold_direction(gold_claim: dict | str) -> str:
        """Extract direction from gold claim, handling both dict and string forms."""
        if isinstance(gold_claim, dict):
            direction = gold_claim.get("direction", "")
            if direction:
                d = str(direction).lower()
                if any(kw in d for kw in ["negative", "decreas", "lower", "less", "disrupt", "inverse"]):
                    return "negative"
                if any(kw in d for kw in ["positive", "increas", "higher", "greater", "more"]):
                    return "positive"
                if any(kw in d for kw in ["null", "no effect", "no significant"]):
                    return "null"
        return "unknown"

    def _extract_significance(self, text: str) -> str | None:
        """Extract significance judgment from text or category label.

        Accepts both explicit p-value thresholds and categorical yes/no/unknown labels
        (the L2 prompt asks for yes/no/unknown; gold annotations may have p-value strings).
        """
        text_lower = text.lower().replace("_", " ")
        # Categorical labels (from LLM output — L2 prompt asks for yes/no/unknown)
        if text_lower in ("yes", "true", "significant"):
            return "significant"
        if text_lower in ("no", "false", "not significant"):
            return "not_significant"
        if text_lower in ("unknown", "unclear", "n/a", ""):
            return "unknown"
        # Explicit p-value thresholds (from gold annotations)
        if any(kw in text_lower for kw in ["p < 0.001", "p<0.001", "highly significant"]):
            return "highly_significant"
        if any(kw in text_lower for kw in ["p < 0.01", "p<0.01"]):
            return "significant_p01"
        if any(kw in text_lower for kw in ["p < 0.05", "p<0.05", "significant", "statistically significant"]):
            return "significant_p05"
        if any(kw in text_lower for kw in ["not significant", "no significant", "p > 0.05", "p>0.05",
                                            "non-significant", "nonsignificant", "marginally"]):
            return "not_significant"
        return "unknown"

    def evaluate_l1(self, gold: dict[str, Any], pred: dict[str, Any],
                    paper_id: str = "") -> Task2EvalResult:
        """Evaluate L1: Execute + Interpret.

        Direction accuracy is the primary non-gameable metric.
        Structural completeness is reported as a diagnostic, not scored.
        """
        result = Task2EvalResult(paper_id=paper_id, level="L1")
        pred_output = pred.get("output", {})

        has_code = bool(pred_output.get("code", ""))
        has_results = bool(pred_output.get("expected_results", ""))
        has_interpretation = bool(pred_output.get("interpretation", ""))
        has_limitations = bool(pred_output.get("limitations", ""))
        completeness = (has_code + has_results + has_interpretation + has_limitations) / 4.0

        # Report completeness as diagnostic only
        result.claim_support_detail["structural_completeness"] = completeness

        # Compare interpretation direction against gold result claims
        gold_directions = []
        gold_dirs_parsed = []
        for c in gold.get("result_claims", []):
            d = c.get("direction", "")
            if isinstance(d, str) and d:
                gold_directions.append(d.lower())
                gold_dirs_parsed.append(self._parse_gold_direction(c))

        pred_interpretation = str(pred_output.get("interpretation", ""))
        pred_direction = self._extract_direction(pred_interpretation)

        direction_result = DirectionResult(total=1)
        if gold_dirs_parsed:
            matches = sum(1 for gd in gold_dirs_parsed if pred_direction == gd)
            direction_result.correct = 1 if matches > 0 else 0
            direction_result.details.append({
                "gold_directions": gold_dirs_parsed,
                "pred_direction": pred_direction,
                "matches_found": matches,
                "total_gold": len(gold_dirs_parsed),
                "match": matches > 0,
            })

        result.direction_accuracy = direction_result.accuracy
        result.direction_detail = direction_result

        # Specificity: does interpretation mention actual variable names from gold?
        # Uses word-level matching (e.g., "team_size" matches "team size")
        specificity = _variable_specificity(pred_interpretation, gold)

        # Code plausibility: does code attempt real analysis?
        code_text = str(pred_output.get("code", ""))
        code_keywords = ["import", "def ", "load", "read_csv", "fit", "regress",
                         "model", "plot", "stat", "test", "analy", "dataframe",
                         "ols", "glm", "corr", "describe", "summary"]
        has_plausible_code = (len(code_text) > 50 and
                              any(kw in code_text.lower() for kw in code_keywords))

        # Limitation awareness (diagnostic only, not in aggregate)
        gold_lims = gold.get("limitations", [])
        pred_lim_text = str(pred_output.get("limitations", ""))
        lim_matches = sum(1 for gl in gold_lims if _semantic_overlap(gl, pred_lim_text) >= 0.15)
        result.limitation_awareness = lim_matches / max(len(gold_lims), 1)

        # Overall: specificity is the primary anti-template signal (harder to game
        # than direction, since 80% of gold directions are "positive").
        # Direction still contributes but at reduced weight.
        result.overall_score = (0.30 * result.direction_accuracy +
                                0.50 * specificity +
                                0.20 * float(has_plausible_code))
        # Multiplicative penalty for completely generic predictions that never
        # mention a single paper-specific variable (same mechanism as L3).
        if specificity < 0.05:
            result.overall_score *= 0.75
        return result

    def evaluate_l2(self, gold: dict[str, Any], pred: dict[str, Any],
                    paper_id: str = "") -> Task2EvalResult:
        """Evaluate L2: Results → Conclusions.

        Compares induced conclusions against gold conclusion claims.
        """
        result = Task2EvalResult(paper_id=paper_id, level="L2")
        pred_output = pred.get("output", {})

        gold_conclusions = [c for c in gold.get("conclusion_claims", [])]
        pred_conclusions = pred_output.get("conclusions", [])
        gold_results = gold.get("result_claims", [])

        # --- Direction Accuracy ---
        # Prefer result_claims for direction (they have explicit direction fields)
        # Fall back to conclusion_claims
        direction_result = DirectionResult()
        direction_sources = gold_results if gold_results else gold_conclusions

        for gs in direction_sources:
            if isinstance(gs, dict):
                gs_text = gs.get("claim", " ".join(str(v) for v in gs.values()))
            else:
                gs_text = str(gs)
            gold_dir = self._parse_gold_direction(gs) if isinstance(gs, dict) and "direction" in gs else self._extract_direction(gs_text)
            direction_result.total += 1

            # For direction accuracy: check if ANY predicted conclusion has the correct direction
            pred_directions = [
                pc.get("direction", self._extract_direction(pc.get("claim", "")))
                if isinstance(pc, dict) else self._extract_direction(str(pc))
                for pc in pred_conclusions
            ]
            match = gold_dir in pred_directions
            if match:
                direction_result.correct += 1
            direction_result.details.append({
                "gold_claim": gs_text[:120],
                "gold_direction": gold_dir,
                "pred_directions": pred_directions,
                "match": match,
            })

        result.direction_accuracy = direction_result.accuracy
        result.direction_detail = direction_result

        # --- Significance Match ---
        gold_sigs = []
        for c in gold.get("result_claims", []):
            sig = c.get("significance", "")
            if sig:
                gold_sigs.append(sig.lower())

        sig_match = 0.0
        pred_sig = "n/a"
        gold_category = "n/a"
        if gold_sigs:
            # Collect significance from ALL predicted conclusions
            pred_sig_texts = []
            for pc in pred_conclusions:
                if isinstance(pc, dict):
                    sig_val = str(pc.get("significance", "")).strip()
                    if sig_val:
                        pred_sig_texts.append(sig_val)
            pred_sig_text = " ".join(pred_sig_texts)
            pred_sig = self._extract_significance(pred_sig_text)

            # Map gold significance to simplified categories (compatible with LLM output)
            gold_sig_text = " ".join(gold_sigs)
            gold_sig_parsed = self._extract_significance(gold_sig_text)
            # Map to simplified 3-way
            if gold_sig_parsed in ("highly_significant", "significant_p01", "significant_p05",
                                    "significant", "yes"):
                gold_category = "significant"
            elif gold_sig_parsed in ("not_significant", "no"):
                gold_category = "not_significant"
            else:
                gold_category = "unknown"

            # Map pred to simplified 3-way
            if pred_sig in ("highly_significant", "significant_p01", "significant_p05",
                            "significant", "yes"):
                pred_category = "significant"
            elif pred_sig in ("not_significant", "no"):
                pred_category = "not_significant"
            else:
                pred_category = "unknown"

            sig_match = 1.0 if (pred_category == gold_category and pred_sig_texts) else 0.0

        result.significance_match = sig_match
        result.significance_detail = {
            "gold_significance": gold_sigs,
            "gold_significance_category": gold_category,
            "pred_significance": pred_sig,
            "pred_category": pred_category if gold_sigs else "n/a",
            "match": bool(sig_match > 0),
        }

        # --- Claim Support Score ---
        # Each predicted conclusion should reference supporting evidence
        supported = 0
        for pc in pred_conclusions:
            if isinstance(pc, dict):
                evidence = pc.get("evidence", pc.get("support_level", ""))
                if evidence and evidence not in ("none", "weak", ""):
                    supported += 1
        result.claim_support_score = supported / max(len(pred_conclusions), 1)
        result.claim_support_detail = {
            "total_claims": len(pred_conclusions),
            "supported_claims": supported,
        }

        # --- Limitation Awareness ---
        gold_lims = gold.get("limitations", [])
        pred_lims_raw = pred_output.get("limitations", pred_output.get("boundary_conditions", []))
        if isinstance(pred_lims_raw, str):
            pred_lims_raw = [pred_lims_raw]
        elif isinstance(pred_lims_raw, dict):
            pred_lims_raw = list(pred_lims_raw.values())
        # Use threshold 0.15 for L2/L3 (limitations are often semantically equivalent
        # but use different wording — token overlap threshold of 0.3 only catches
        # near-verbatim matches)
        lim_matches = sum(
            1 for gl in gold_lims
            if any(_semantic_overlap(gl, str(pl)) >= 0.15 for pl in pred_lims_raw)
        )
        result.limitation_awareness = lim_matches / max(len(gold_lims), 1)
        result.limitation_detail = {
            "gold_limitations": gold_lims,
            "pred_limitations": [str(p)[:100] for p in pred_lims_raw[:5]],
            "matches_found": lim_matches,
        }

        # --- Hallucinated Claim Rate ---
        # Claims without any overlap with gold conclusions
        hallucinated = 0
        for pc in pred_conclusions:
            pc_text = pc.get("claim", "") if isinstance(pc, dict) else str(pc)
            max_sim = max(
                (_semantic_overlap(pc_text,
                    gc.get("claim", " ".join(str(v) for v in gc.values())) if isinstance(gc, dict) else str(gc))
                 for gc in gold_conclusions),
                default=0.0,
            )
            if max_sim < 0.15:
                hallucinated += 1
        result.hallucinated_claim_rate = hallucinated / max(len(pred_conclusions), 1)
        result.hallucinated_detail = {
            "total_predicted": len(pred_conclusions),
            "hallucinated": hallucinated,
        }

        # --- Overall L2 Score ---
        # Limitation awareness excluded from aggregate (semantic overlap metric
        # is too noisy — scores near zero despite reasonable outputs).
        result.overall_score = (
            0.30 * result.direction_accuracy +
            0.20 * result.significance_match +
            0.30 * result.claim_support_score +
            0.20 * (1.0 - result.hallucinated_claim_rate)
        )
        return result

    def evaluate_l3(self, gold: dict[str, Any], pred: dict[str, Any],
                    paper_id: str = "") -> Task2EvalResult:
        """Evaluate L3: Partial Results → Calibrated Inference.

        Uses direction calibration scoring: tentative directions get partial credit,
        unknown gets low credit when gold has a directional signal, and full
        credit only when evidence is genuinely insufficient.
        """
        # --- Direction calibration matrix ---
        # Score for (gold_dir, pred_dir) pairs
        DIRECTION_SCORE = {
            # Exact matches
            ("positive", "positive"): 1.0,
            ("negative", "negative"): 1.0,
            # Tentative matches (correct sign, appropriate uncertainty)
            ("positive", "tentative_positive"): 0.75,
            ("negative", "tentative_negative"): 0.75,
            ("null", "tentative_positive"): 0.50,
            ("null", "tentative_negative"): 0.50,
            ("null", "unknown"): 1.0,  # null effect correctly identified
            # Unknown/avoidance penalties
            ("positive", "unknown"): 0.25,
            ("negative", "unknown"): 0.25,
            ("null", "positive"): 0.0,
            ("null", "negative"): 0.0,
            # Direction reversal
            ("positive", "negative"): 0.0,
            ("positive", "tentative_negative"): 0.10,
            ("negative", "positive"): 0.0,
            ("negative", "tentative_positive"): 0.10,
        }

        # Normalize prompt output format
        pred_output = pred.get("output", {})
        if "supported_conclusions" in pred_output and "conclusions" not in pred_output:
            pred_output = dict(pred_output)
            sc_list = pred_output.get("supported_conclusions", [])
            pred_output["conclusions"] = [
                {"claim": sc.get("claim", ""),
                 "direction": sc.get("direction", "unknown"),
                 "significance": sc.get("support_strength", "unknown"),
                 "support_level": sc.get("support_strength", "weak"),
                 "evidence": sc.get("missing_evidence", sc.get("evidence_anchor", "")),
                 "_support_strength": sc.get("support_strength", "weak")}
                for sc in sc_list
            ]
            pred = dict(pred)
            pred["output"] = pred_output

        result = self.evaluate_l2(gold, pred, paper_id)
        result.level = "L3"
        pred_output = pred.get("output", {})

        # --- L3 Calibrated Direction Scoring ---
        # Get gold directions and predicted directions, score via matrix
        gold_dirs = []
        for c in gold.get("result_claims", gold.get("conclusion_claims", [])):
            gold_dirs.append(self._parse_gold_direction(c))
        if not gold_dirs:
            gold_dirs = ["unknown"]  # fallback

        pred_claims = pred_output.get("conclusions", [])
        pred_dirs = [
            pc.get("direction", "unknown") if isinstance(pc, dict) else "unknown"
            for pc in pred_claims
        ]

        dir_total = 0.0
        dir_count = 0
        dir_details = []
        for i, gd in enumerate(gold_dirs):
            pd = pred_dirs[i] if i < len(pred_dirs) else "unknown"
            score = DIRECTION_SCORE.get((gd, pd), 0.0)
            dir_total += score
            dir_count += 1
            dir_details.append({
                "gold_direction": gd,
                "pred_direction": pd,
                "score": score,
            })

        result.direction_accuracy = dir_total / max(dir_count, 1)
        result.direction_detail.details = dir_details
        result.direction_detail.correct = sum(1 for d in dir_details if d["score"] >= 0.75)
        result.direction_detail.total = dir_count

        # --- L3 Graded Claim Support ---
        strength_weight = {"strong": 1.0, "moderate": 0.6, "weak": 0.3}
        graded_support = 0.0
        l3_conclusions = pred_output.get("conclusions", [])
        for pc in l3_conclusions:
            if isinstance(pc, dict):
                ss = pc.get("_support_strength", "weak")
                graded_support += strength_weight.get(ss, 0.0)
        result.claim_support_score = graded_support / max(len(l3_conclusions), 1)
        result.claim_support_detail["graded_by_support_strength"] = True

        # --- L3 Limitation Awareness ---
        # New prompt v2 requires limitation per claim — extract and compare
        gold_lims = gold.get("limitations", [])
        pred_lims_raw = []
        for pc in pred_claims:
            if isinstance(pc, dict):
                lim = pc.get("limitation", pred_output.get("limitations", ""))
                if lim and isinstance(lim, str):
                    pred_lims_raw.append(lim)
        if not pred_lims_raw:
            pred_lims_raw = pred_output.get("limitations", [])
            if isinstance(pred_lims_raw, str):
                pred_lims_raw = [pred_lims_raw]
            elif isinstance(pred_lims_raw, dict):
                pred_lims_raw = list(pred_lims_raw.values())

        lim_matches = sum(
            1 for gl in gold_lims
            if any(_semantic_overlap(gl, str(pl)) >= 0.12 for pl in pred_lims_raw)
        )
        result.limitation_awareness = lim_matches / max(len(gold_lims), 1)
        result.limitation_detail = {
            "gold_limitations": gold_lims,
            "pred_limitations": [str(p)[:100] for p in pred_lims_raw[:5]],
            "matches_found": lim_matches,
        }

        # --- Evidence Anchor Check ---
        # Each conclusion must have a non-empty evidence_anchor
        sc_list = pred_output.get("supported_conclusions", [])
        anchored = sum(
            1 for sc in sc_list
            if isinstance(sc, dict) and len(sc.get("evidence_anchor", "").strip()) > 10
        )
        evidence_anchor_rate = anchored / max(len(sc_list), 1)
        # Two-sided: reward appropriate uncertainty, penalize blanket abstention.
        # The optimal strategy is to make correct specific claims when evidence
        # supports them AND flag uncertainty when evidence is missing.
        insufficient_flag = pred_output.get("insufficient_evidence_flag", False)
        if isinstance(insufficient_flag, str):
            insufficient_flag = insufficient_flag.lower() in ("true", "yes", "1")

        uncertainty_assessment = pred_output.get("uncertainty_assessment", "").lower()

        unsupported = pred_output.get("unsupported_claims", [])
        if not isinstance(unsupported, list):
            unsupported = []

        # Count specific supported claims (from the mapped conclusions)
        supported_claims = pred_output.get("conclusions", [])
        n_supported = len([c for c in supported_claims
                          if isinstance(c, dict) and c.get("claim", "").strip()])
        n_unsupported = len(unsupported)

        # Blanket abstention: flagged insufficient but made zero specific claims
        blanket_abstention = insufficient_flag and n_supported == 0

        # Empty response: no supported AND no unsupported claims → zero credit
        empty_response = (n_supported == 0 and n_unsupported == 0)

        ur_score = 0.0
        ur_detail = {}

        if empty_response:
            ur_score = 0.0
            ur_detail["empty_response"] = True
        else:
            if insufficient_flag:
                if blanket_abstention:
                    ur_score += 0.15
                    ur_detail["blanket_abstention"] = True
                else:
                    ur_score += 0.40
                    ur_detail["flagged_insufficient"] = True
            if uncertainty_assessment in ("high", "moderate"):
                if blanket_abstention:
                    ur_score += 0.05
                else:
                    ur_score += 0.20
                ur_detail["high_uncertainty"] = True
            if n_unsupported > 0 and not blanket_abstention:
                ur_score += 0.20
                ur_detail["identified_unsupported"] = True
                ur_detail["unsupported_count"] = n_unsupported
            elif n_unsupported > 0 and blanket_abstention:
                ur_score += 0.10
                ur_detail["identified_unsupported"] = True

        result.uncertainty_recognition = min(ur_score, 1.0)
        result.uncertainty_detail = ur_detail

        # --- Claim Specificity (L3 anti-template measure) ---
        l3_claim_text = " ".join(
            c.get("claim", "") if isinstance(c, dict) else str(c)
            for c in supported_claims
        )
        claim_specificity = _variable_specificity(l3_claim_text, gold)
        result.claim_support_detail["l3_specificity"] = claim_specificity
        result.claim_support_detail["evidence_anchor_rate"] = evidence_anchor_rate

        # --- L3 Overall Score (v2 weights) ---
        # Rebalanced to emphasize calibrated direction + evidence anchoring.
        # Limitation awareness now included (prompt v2 requires per-claim limitation).
        # Direction accuracy uses the calibration matrix (tentative=0.75, unknown=0.25).
        result.overall_score = (
            0.25 * result.direction_accuracy +
            0.25 * result.claim_support_score +
            0.15 * claim_specificity +
            0.15 * result.limitation_awareness +
            0.10 * evidence_anchor_rate +
            0.10 * (1.0 - result.hallucinated_claim_rate)
        )

        # Multiplicative penalty for completely generic claims
        if claim_specificity < 0.05:
            result.overall_score *= 0.65
            result.claim_support_detail["generic_claim_penalty"] = True

        # Also check uncertainty claims for specificity: if the unsupported claims
        # and missing_evidence are all generic, reduce uncertainty credit.
        uc_text = " ".join(str(u) for u in unsupported)
        uc_specificity = _variable_specificity(uc_text, gold)
        if n_unsupported > 0 and uc_specificity < 0.05 and claim_specificity < 0.05:
            # Both claims and uncertainty statements are generic → template-like
            result.uncertainty_recognition *= 0.60
            result.claim_support_detail["generic_uncertainty_penalty"] = True

        return result

    def evaluate(self, gold: dict[str, Any], pred: dict[str, Any],
                 level: str = "L2", paper_id: str = "") -> Task2EvalResult:
        """Run Task 2 evaluation at the specified level."""
        if level == "L1":
            return self.evaluate_l1(gold, pred, paper_id)
        elif level == "L2":
            return self.evaluate_l2(gold, pred, paper_id)
        elif level == "L3":
            return self.evaluate_l3(gold, pred, paper_id)
        else:
            raise ValueError(f"Unknown level: {level}")
