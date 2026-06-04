#!/usr/bin/env python3
"""Regression tests for the stratified benchmark evaluator.

Tests:
  1. Benign stderr (FutureWarning, DeprecationWarning) not flagged as error
  2. Output parser handles multiple output formats
  3. Silent failure detection with known values
  4. Ground truth computation consistency
  5. Error type classification
"""

import sys
import os
import tempfile
from pathlib import Path

# Add project root to path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np


def test_benign_stderr_not_flagged_as_error():
    """FutureWarning in stderr must NOT trigger error detection."""
    from src.sciscigpt_local.sandbox import execute_python

    code = """
import warnings
warnings.warn("FutureWarning: pandas.foo is deprecated", FutureWarning)
print("D_INDEX = 0.5")
"""
    result = execute_python(code, timeout=30)
    stderr = result.get("stderr", "")
    exit_code = result["exit_code"]

    # Correct detection: no error
    has_traceback = "Traceback (most recent call last)" in stderr
    is_error = exit_code != 0 or has_traceback

    assert exit_code == 0, f"Expected exit_code=0, got {exit_code}"
    assert not is_error, f"Benign stderr should not trigger error, but got is_error=True"
    assert "D_INDEX = 0.5" in result["stdout"], "Expected output not found"
    print("  PASS: Benign stderr not flagged as error")


def test_output_parser_multiple_formats():
    """Parser must handle D_INDEX = X, Disruption Index (D): X, D = X."""
    from src.sciscigpt_local.metric_templates import parse_metric_output

    # Format 1: D_INDEX = value
    out1 = "D_INDEX = 0.0321\nn_i = 50\nn_j = 30"
    r1 = parse_metric_output(out1, "disruption")
    assert abs(r1.get("D_index", -999) - 0.0321) < 1e-6, f"Format 1 failed: {r1}"
    assert r1.get("n_i") == 50, f"n_i wrong: {r1}"
    assert r1.get("n_j") == 30, f"n_j wrong: {r1}"
    print(f"  PASS: Format 'D_INDEX = value': {r1}")

    # Format 2: Disruption Index (D): value
    out2 = "Disruption Index (D): -0.05\nn_i = 10"
    r2 = parse_metric_output(out2, "disruption")
    assert abs(r2.get("D_index", -999) - (-0.05)) < 1e-6, f"Format 2 failed: {r2}"
    print(f"  PASS: Format 'Disruption Index (D): value': {r2}")

    # Format 3: D = value
    out3 = "n_i = 100\nD = 0.75\nn_j = 25"
    r3 = parse_metric_output(out3, "disruption")
    assert abs(r3.get("D_index", -999) - 0.75) < 1e-6, f"Format 3 failed: {r3}"
    print(f"  PASS: Format 'D = value': {r3}")


def test_silent_failure_detection():
    """REI=0 + large deviation → silent failure. REI=0 + small deviation → not."""
    from src.sciscigpt_local.rei_metric import compute_rei_c, flag_silent_failure

    # Case 1: REI=0, correct result → no silent failure
    rei1, cr1 = 0.0, 0.0
    assert not flag_silent_failure(rei1, cr1), "Correct result should not be silent failure"

    # Case 2: REI=0, wrong result (50% deviation) → silent failure
    rei2, cr2 = 0.0, 0.5
    assert flag_silent_failure(rei2, cr2), "Large deviation should be silent failure"

    # Case 3: REI=1.0 (had fix iterations), wrong result → not silent (error was detected)
    rei3, cr3 = 1.0, 0.5
    assert not flag_silent_failure(rei3, cr3), "REI>0.5 should not be silent failure"

    # Full compute_rei_c test
    rei_c, cr, silent = compute_rei_c(0.0, 1.0, 0.5)  # 50% deviation
    assert silent, f"50% deviation should be silent failure, got silent={silent}"
    assert rei_c > 0, f"REI-c should be > 0 for wrong result, got {rei_c}"

    rei_c2, cr2, silent2 = compute_rei_c(0.0, 1.0, 1.0)  # 0% deviation
    assert not silent2, f"0% deviation should not be silent, got silent={silent2}"
    assert rei_c2 == 0.0, f"REI-c should be 0 for correct result, got {rei_c2}"

    print("  PASS: Silent failure detection correct")


def test_error_messages():
    """Test real tracebacks ARE detected, but warnings are NOT."""
    from src.sciscigpt_local.sandbox import execute_python

    # Real error (NameError)
    code_err = "print(undefined_var)"
    r = execute_python(code_err, timeout=10)
    assert r["exit_code"] != 0, "NameError should have non-zero exit"
    assert "Traceback (most recent call last)" in r.get("stderr", ""), "Should have traceback"
    print("  PASS: Real Python errors correctly detected")

    # Mixed case: code runs fine, pandas emits warning
    code_mixed = """
import warnings
warnings.warn("FutureWarning: the default value of regex will change", FutureWarning)
result = sum([1, 2, 3])
print(f"SUM = {result}")
"""
    r2 = execute_python(code_mixed, timeout=10)
    stderr2 = r2.get("stderr", "")
    has_traceback = "Traceback (most recent call last)" in stderr2
    is_error = r2["exit_code"] != 0 or has_traceback
    assert not is_error, f"Warning-only stderr should not be error. stderr={stderr2[:200]}"
    print("  PASS: Mixed warning+success correctly classified")


def test_ground_truth_computation():
    """Ground truth D-index matches expected formula."""
    from src.sciscigpt_local.metric_templates import compute_ground_truth

    # Create simple test data
    papers = pd.DataFrame({"paper_id": [1, 2, 3, 4, 5], "year": [2020]*5,
                           "citation_count": [10]*5, "disruption_score": [0.1]*5})

    # Paper 1 cites papers 2,3. Papers 4,5 cite paper 1.
    # Paper 4 also cites paper 2 (overlap). Paper 5 does not cite 2 or 3.
    pc = pd.DataFrame({
        "citing_paper_id": [1, 1, 4, 4, 5],
        "cited_paper_id":  [2, 3, 1, 2, 1],
    })

    gt = compute_ground_truth("disruption", 1, papers, pc)
    # refs = {2, 3}, citers = {4, 5}
    # Paper 4: cites {1, 2}, overlap with {2} → n_j
    # Paper 5: cites {1}, no overlap → n_i
    # n_i=1, n_j=1, D = (1-1)/(1+1) = 0.0
    assert abs(gt["D_index"] - 0.0) < 1e-6, f"D-index should be 0.0, got {gt}"
    assert gt["n_i"] == 1, f"n_i should be 1, got {gt['n_i']}"
    assert gt["n_j"] == 1, f"n_j should be 1, got {gt['n_j']}"
    print(f"  PASS: Ground truth D-index correct: D={gt['D_index']}, n_i={gt['n_i']}, n_j={gt['n_j']}")


def test_l2_no_formula_leak():
    """L2 prompt must NOT contain the D-index formula directly."""
    from scripts.run_stratified_benchmark import build_l2_prompt

    paper_row = pd.Series({
        "paper_id": 12345, "title": "Test Paper on Innovation",
        "abstract": "We study how novel ideas emerge in science.",
        "year": 2020, "journal_name": "Nature",
    })

    prompt = build_l2_prompt(paper_row, "disruption", refs_path="/tmp/r.csv", cites_path="/tmp/c.csv")
    assert "D = (n_i - n_j)" not in prompt, f"L2 prompt leaks D-index formula!\n{prompt[:500]}"
    assert "n_i = citers with NO overlap" not in prompt, "L2 prompt leaks algorithm hint!"
    print("  PASS: L2 prompt has no formula leakage (disruption)")


if __name__ == "__main__":
    print("=" * 60)
    print("BENCHMARK EVALUATOR REGRESSION TESTS")
    print("=" * 60)

    tests = [
        ("Benign stderr", test_benign_stderr_not_flagged_as_error),
        ("Output parser", test_output_parser_multiple_formats),
        ("Silent failure", test_silent_failure_detection),
        ("Error detection", test_error_messages),
        ("Ground truth", test_ground_truth_computation),
        ("L2 formula leak", test_l2_no_formula_leak),
    ]

    passed = 0
    failed = 0
    for name, test_fn in tests:
        try:
            test_fn()
            passed += 1
        except Exception as e:
            print(f"  FAIL: {name} — {e}")
            failed += 1

    print(f"\n{'='*60}")
    print(f"  Results: {passed} passed, {failed} failed, {len(tests)} total")
    print(f"{'='*60}")
    sys.exit(0 if failed == 0 else 1)
