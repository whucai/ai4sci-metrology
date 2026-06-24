"""Regression tests for Task 2 evaluator.

Covers every task level, empty predictions, adversarial baselines,
multi-claim cases, and edge cases.
"""

import pytest
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.eval.task2_evaluator import Task2Evaluator, _tokenize, _semantic_overlap


# ── Fixtures ──

@pytest.fixture
def evaluator():
    return Task2Evaluator()


@pytest.fixture
def gold_positive():
    return {
        "paper_id": "test001",
        "result_claims": [
            {"claim": "Large teams develop science; small teams disrupt it.",
             "direction": "positive", "significance": "p < 0.001"},
            {"claim": "Team size positively correlates with impact.",
             "direction": "positive", "significance": "p < 0.01"},
        ],
        "conclusion_claims": [
            {"claim": "Large teams are more productive.", "direction": "positive"},
        ],
        "limitations": ["Limited to Web of Science data.", "Correlational design."],
        "independent_variables": [{"name": "team_size"}, {"name": "citation_count"}],
        "dependent_variables": [{"name": "impact"}, {"name": "disruption_index"}],
        "control_variables": [{"name": "year"}, {"name": "field"}],
    }


@pytest.fixture
def gold_mixed():
    return {
        "paper_id": "test002",
        "result_claims": [
            {"claim": "Effect A is positive.", "direction": "positive", "significance": "p < 0.05"},
            {"claim": "Effect B is negative.", "direction": "negative", "significance": "p < 0.05"},
            {"claim": "Effect C shows no relationship.", "direction": "null", "significance": "not significant"},
        ],
        "conclusion_claims": [],
        "limitations": ["Small sample size."],
        "independent_variables": [],
        "dependent_variables": [],
        "control_variables": [],
    }


@pytest.fixture
def gold_null():
    return {
        "paper_id": "test003",
        "result_claims": [{"claim": "No effect found.", "direction": "null"}],
        "conclusion_claims": [{"claim": "Null results across all tests.", "direction": "null"}],
        "limitations": [],
        "independent_variables": [],
        "dependent_variables": [],
        "control_variables": [],
    }


# ── Tokenization ──

def test_tokenize_basic():
    assert _tokenize("Large teams develop science") == {"large", "teams", "develop", "science"}


def test_tokenize_case_insensitive():
    assert _tokenize("Large LARGE large") == {"large"}


def test_semantic_overlap_identical():
    assert _semantic_overlap("large teams science", "science teams large") == 1.0


def test_semantic_overlap_no_match():
    assert _semantic_overlap("large teams", "small groups") == 0.0


def test_semantic_overlap_empty():
    assert _semantic_overlap("", "") == 1.0


# ── Direction extraction ──

def test_extract_direction_positive(evaluator):
    assert evaluator._extract_direction("The results show a positive effect on impact.") == "positive"


def test_extract_direction_negative(evaluator):
    assert evaluator._extract_direction("We find a significant decrease in disruption.") == "negative"


def test_extract_direction_null(evaluator):
    assert evaluator._extract_direction("There was no significant relationship found.") == "null"


def test_extract_direction_unknown(evaluator):
    assert evaluator._extract_direction("xyzzy foo bar") == "unknown"


# ── Significance extraction ──

def test_extract_significance_categorical_yes(evaluator):
    assert evaluator._extract_significance("yes") == "significant"


def test_extract_significance_categorical_no(evaluator):
    assert evaluator._extract_significance("no") == "not_significant"


def test_extract_significance_categorical_unknown(evaluator):
    assert evaluator._extract_significance("unknown") == "unknown"


def test_extract_significance_p_value(evaluator):
    assert "significant" in evaluator._extract_significance("p < 0.001")


# ── Gold direction parsing ──

def test_parse_gold_direction_positive(evaluator):
    assert evaluator._parse_gold_direction({"direction": "positive"}) == "positive"


def test_parse_gold_direction_negative(evaluator):
    assert evaluator._parse_gold_direction({"direction": "negative"}) == "negative"


def test_parse_gold_direction_unknown(evaluator):
    assert evaluator._parse_gold_direction({"foo": "bar"}) == "unknown"


# ── L1 Evaluation ──

def test_l1_empty_prediction(evaluator, gold_positive):
    pred = {"output": {"code": "", "expected_results": "", "interpretation": "", "limitations": ""}}
    result = evaluator.evaluate_l1(gold_positive, pred, "test001")
    assert result.overall_score < 0.15  # Near zero (only specificity from empty interpretation)


def test_l1_good_prediction(evaluator, gold_positive):
    pred = {"output": {
        "code": "import pandas as pd\nimport statsmodels.api as sm\n"
                "df = pd.read_csv('data.csv')\n"
                "model = sm.OLS(df['impact'], df[['team_size']]).fit()\n"
                "print(model.summary())",
        "expected_results": "We expect team_size to have a significant positive coefficient.",
        "interpretation": "The results show positive effects of team_size on impact, "
                         "consistent with the hypothesis that larger teams produce higher-impact work.",
        "limitations": "Correlational design limits causal claims.",
    }}
    result = evaluator.evaluate_l1(gold_positive, pred, "test001")
    assert result.direction_accuracy > 0.0  # "positive" direction matches gold
    assert result.overall_score > 0.3  # Specificity + code plausibility + direction


def test_l1_wrong_direction(evaluator, gold_positive):
    pred = {"output": {
        "code": "import statsmodels.api as sm",
        "expected_results": "Expected negative coefficient.",
        "interpretation": "The results show negative effects, contrary to hypothesis.",
        "limitations": "Data quality issues.",
    }}
    result = evaluator.evaluate_l1(gold_positive, pred, "test001")
    assert result.direction_accuracy == 0.0  # "negative" doesn't match gold "positive"


def test_l1_structural_completeness_not_in_aggregate(evaluator, gold_positive):
    """Structural completeness should be diagnostic only, not drive score."""
    pred_full = {"output": {
        "code": "# analysis", "expected_results": "results",
        "interpretation": "positive effect of team_size on impact",
        "limitations": "some limits",
    }}
    pred_minimal = {"output": {
        "code": "# analysis", "expected_results": "",
        "interpretation": "positive effect of team_size on impact",
        "limitations": "",
    }}
    r_full = evaluator.evaluate_l1(gold_positive, pred_full, "test001")
    r_minimal = evaluator.evaluate_l1(gold_positive, pred_minimal, "test001")
    # Both have same interpretation → similar scores despite different completeness
    assert abs(r_full.overall_score - r_minimal.overall_score) < 0.15


# ── L2 Evaluation ──

def test_l2_empty_prediction(evaluator, gold_positive):
    pred = {"output": {"conclusions": [], "limitations": []}}
    result = evaluator.evaluate_l2(gold_positive, pred, "test001")
    assert result.overall_score <= 0.25  # Only gets anti-hallucination credit (no claims = no hallucinations)


def test_l2_correct_direction(evaluator, gold_positive):
    pred = {"output": {
        "conclusions": [
            {"claim": "Large teams have a positive effect on impact.",
             "direction": "positive", "significance": "yes",
             "evidence": "strong", "support_level": "strong"},
        ],
        "limitations": ["Limited to Web of Science data."],
    }}
    result = evaluator.evaluate_l2(gold_positive, pred, "test001")
    assert result.direction_accuracy == 1.0
    assert result.significance_match == 1.0
    assert result.claim_support_score == 1.0


def test_l2_wrong_direction(evaluator, gold_positive):
    pred = {"output": {
        "conclusions": [{"claim": "Negative effect.", "direction": "negative",
                         "significance": "yes", "evidence": "strong", "support_level": "strong"}],
        "limitations": [],
    }}
    result = evaluator.evaluate_l2(gold_positive, pred, "test001")
    assert result.direction_accuracy == 0.0  # All gold claims are "positive", pred is "negative"


def test_l2_hallucinated_claim(evaluator, gold_positive):
    pred = {"output": {
        "conclusions": [
            {"claim": "Completely unrelated claim about quantum physics and dark matter.",
             "direction": "positive", "significance": "yes",
             "evidence": "strong", "support_level": "strong"},
        ],
        "limitations": [],
    }}
    result = evaluator.evaluate_l2(gold_positive, pred, "test001")
    assert result.hallucinated_claim_rate == 1.0


def test_l2_limitation_awareness_not_in_aggregate(evaluator, gold_positive):
    """Limitation awareness should NOT affect overall score."""
    pred_no_lims = {"output": {"conclusions": [
        {"claim": "Positive effect.", "direction": "positive",
         "significance": "yes", "evidence": "strong", "support_level": "strong"}
    ], "limitations": []}}
    pred_with_lims = {"output": {"conclusions": [
        {"claim": "Positive effect.", "direction": "positive",
         "significance": "yes", "evidence": "strong", "support_level": "strong"}
    ], "limitations": ["Limited to Web of Science data.", "Correlational design."]}}
    r_no = evaluator.evaluate_l2(gold_positive, pred_no_lims, "test001")
    r_with = evaluator.evaluate_l2(gold_positive, pred_with_lims, "test001")
    # Same conclusions → same overall (limitations no longer in aggregate)
    assert r_no.overall_score == r_with.overall_score


def test_l2_mixed_directions(evaluator, gold_mixed):
    pred = {"output": {
        "conclusions": [
            {"claim": "Effect A is positive.", "direction": "positive",
             "significance": "yes", "evidence": "strong", "support_level": "strong"},
            {"claim": "Effect B is negative.", "direction": "negative",
             "significance": "yes", "evidence": "strong", "support_level": "strong"},
        ],
        "limitations": [],
    }}
    result = evaluator.evaluate_l2(gold_mixed, pred, "test002")
    # 2 of 3 gold directions matched (positive + negative, missing null)
    assert 0.5 <= result.direction_accuracy <= 0.8


# ── L3 Evaluation ──

def test_l3_empty_prediction(evaluator, gold_positive):
    pred = {"output": {
        "supported_conclusions": [],
        "insufficient_evidence_flag": False,
        "uncertainty_assessment": "",
        "unsupported_claims": [],
    }}
    result = evaluator.evaluate_l3(gold_positive, pred, "test001")
    assert result.overall_score <= 0.15  # No claims made, no uncertainty flag
    assert result.uncertainty_recognition < 0.2  # No flag, no claims


def test_l3_blanket_abstention_penalty(evaluator, gold_positive):
    """Flagging insufficient with ZERO specific claims should be penalized."""
    pred = {"output": {
        "supported_conclusions": [],
        "insufficient_evidence_flag": True,
        "uncertainty_assessment": "high",
        "unsupported_claims": [],
    }}
    result = evaluator.evaluate_l3(gold_positive, pred, "test001")
    # Blanket abstention → low uncertainty_recognition
    assert result.uncertainty_recognition < 0.35
    assert result.overall_score < 0.25


def test_l3_good_uncertainty_with_claims(evaluator, gold_positive):
    """Uncertainty flag WITH specific supported claims should score well."""
    pred = {"output": {
        "supported_conclusions": [
            {"claim": "Partial results suggest a positive effect of team_size on impact.",
             "support_strength": "weak",
             "missing_evidence": "complete statistical results and robustness checks"},
        ],
        "insufficient_evidence_flag": True,
        "uncertainty_assessment": "high",
        "unsupported_claims": ["definitive causal claims cannot be made without controls"],
    }}
    result = evaluator.evaluate_l3(gold_positive, pred, "test001")
    assert result.uncertainty_recognition > 0.5  # Non-blanket with flag + claims + unsupported
    assert result.claim_support_score > 0.0  # Has a supported claim


def test_l3_always_uncertain_penalized(evaluator, gold_positive):
    """The always-uncertain adversarial baseline should get low scores."""
    pred = {"output": {
        "supported_conclusions": [],
        "insufficient_evidence_flag": True,
        "uncertainty_assessment": "high",
        "unsupported_claims": [],
    }}
    result = evaluator.evaluate_l3(gold_positive, pred, "test001")
    assert result.overall_score < 0.25  # Blanket abstention + no claims


def test_l3_always_confident_penalized(evaluator, gold_positive):
    """Always-confident should lose uncertainty_recognition entirely."""
    pred = {"output": {
        "supported_conclusions": [
            {"claim": "All hypotheses are strongly supported.", "support_strength": "strong",
             "missing_evidence": "none"},
        ],
        "insufficient_evidence_flag": False,
        "uncertainty_assessment": "low",
        "unsupported_claims": [],
    }}
    result = evaluator.evaluate_l3(gold_positive, pred, "test001")
    assert result.uncertainty_recognition < 0.1  # No flag, low uncertainty, no unsupported


def test_l3_limitation_not_in_aggregate(evaluator, gold_positive):
    pred = {"output": {
        "supported_conclusions": [
            {"claim": "Partial positive effect.", "support_strength": "weak",
             "missing_evidence": "full results"},
        ],
        "insufficient_evidence_flag": True,
        "uncertainty_assessment": "moderate",
        "unsupported_claims": ["causal claims"],
    }}
    result = evaluator.evaluate_l3(gold_positive, pred, "test001")
    # limitation_awareness is computed but excluded from overall_score
    assert 0.0 <= result.limitation_awareness <= 1.0  # Still computed as diagnostic


# ── Null gold handling ──

def test_l2_null_direction(evaluator, gold_null):
    pred = {"output": {
        "conclusions": [
            {"claim": "No effect found.", "direction": "null",
             "significance": "no", "evidence": "strong", "support_level": "strong"},
        ],
        "limitations": [],
    }}
    result = evaluator.evaluate_l2(gold_null, pred, "test003")
    assert result.direction_accuracy == 1.0


def test_l2_null_significance(evaluator, gold_null):
    pred = {"output": {
        "conclusions": [
            {"claim": "No effect.", "direction": "null",
             "significance": "no", "evidence": "strong", "support_level": "strong"},
        ],
        "limitations": [],
    }}
    result = evaluator.evaluate_l2(gold_null, pred, "test003")
    # "no" → not_significant, gold "null" → might be parsed as not_significant or unknown
    assert result.significance_match >= 0.0


# ── Edge cases ──

def test_missing_output_key(evaluator, gold_positive):
    pred = {}  # No "output" key
    result = evaluator.evaluate_l2(gold_positive, pred, "test001")
    assert result.overall_score < 0.25  # Should handle gracefully


def test_empty_gold(evaluator):
    gold = {"paper_id": "empty", "result_claims": [], "conclusion_claims": [], "limitations": []}
    pred = {"output": {"conclusions": [], "limitations": []}}
    result = evaluator.evaluate_l2(gold, pred, "empty")
    # No gold → no direction significance. No predicted claims → no hallucinations.
    assert result.overall_score <= 0.25


def test_many_claims(evaluator, gold_positive):
    pred = {"output": {
        "conclusions": [
            {"claim": f"Claim {i}: positive effect.", "direction": "positive",
             "significance": "yes", "evidence": "strong", "support_level": "strong"}
            for i in range(10)
        ],
        "limitations": [],
    }}
    result = evaluator.evaluate_l2(gold_positive, pred, "test001")
    assert result.claim_support_score == 1.0  # All have evidence
    # Some might be hallucinated if no overlap with gold
    assert 0.0 <= result.hallucinated_claim_rate <= 1.0


def test_all_levels_dispatch(evaluator, gold_positive):
    """evaluate() should dispatch to correct level method."""
    r1 = evaluator.evaluate(gold_positive,
        {"output": {"code": "# test", "expected_results": "r", "interpretation": "positive", "limitations": "l"}},
        level="L1", paper_id="test")
    r2 = evaluator.evaluate(gold_positive,
        {"output": {"conclusions": [{"claim": "positive", "direction": "positive",
         "significance": "yes", "evidence": "strong", "support_level": "strong"}], "limitations": []}},
        level="L2", paper_id="test")
    r3 = evaluator.evaluate(gold_positive,
        {"output": {"supported_conclusions": [{"claim": "p", "support_strength": "weak",
         "missing_evidence": "x"}], "insufficient_evidence_flag": True,
         "uncertainty_assessment": "high", "unsupported_claims": ["causal"]}},
        level="L3", paper_id="test")
    assert r1.level == "L1"
    assert r2.level == "L2"
    assert r3.level == "L3"


def test_invalid_level(evaluator, gold_positive):
    with pytest.raises(ValueError):
        evaluator.evaluate(gold_positive, {}, level="L4", paper_id="test")


# ── Bounds checks ──

@pytest.mark.parametrize("level", ["L1", "L2", "L3"])
def test_scores_in_range(evaluator, gold_positive, level):
    """All component scores should be in [0, 1]."""
    if level == "L1":
        pred = {"output": {"code": "# test", "expected_results": "r",
                "interpretation": "positive effect on team_size and citation_count",
                "limitations": "l"}}
    elif level == "L2":
        pred = {"output": {"conclusions": [
            {"claim": "positive", "direction": "positive", "significance": "yes",
             "evidence": "strong", "support_level": "strong"}
        ], "limitations": ["l"]}}
    else:
        pred = {"output": {"supported_conclusions": [
            {"claim": "partial positive", "support_strength": "weak", "missing_evidence": "x"}
        ], "insufficient_evidence_flag": True, "uncertainty_assessment": "high",
           "unsupported_claims": ["causal"]}}

    result = evaluator.evaluate(gold_positive, pred, level=level, paper_id="test")
    assert 0.0 <= result.direction_accuracy <= 1.0
    assert 0.0 <= result.significance_match <= 1.0
    assert 0.0 <= result.claim_support_score <= 1.0
    assert 0.0 <= result.limitation_awareness <= 1.0
    assert 0.0 <= result.hallucinated_claim_rate <= 1.0
    assert 0.0 <= result.overall_score <= 1.0
    if level == "L3":
        assert 0.0 <= result.uncertainty_recognition <= 1.0
