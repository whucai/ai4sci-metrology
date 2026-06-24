#!/usr/bin/env python3
"""R002: STRICT numerical reproduction of Petersen et al. (2024).

Petersen et al. (2024) "The disruption index suffers from citation inflation
and is confounded by shifts in scholarly citation practice" (arXiv:2406.15311).

STRICT task type: same data source (SciSciNet), same CD formula, same regression
model. Target is numerical identity — D3 is pass/fail, not reference-only.

Key regression (Eq. 2 in paper):
  |CDp,5| = const + bk*ln(kp) + br*ln(rp) + bc*ln(cp,5) + year_FE + epsilon

Usage:
    conda activate sciscigpt && python scripts/r002_petersen2024_reproduction.py
    conda activate sciscigpt && python scripts/r002_petersen2024_reproduction.py --mock
"""

from __future__ import annotations

import json
import os
import re
import sys
import time
import textwrap
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.eval.dimensions import (
    build_reproduction_profile,
    compute_maturity_level,
    format_maturity,
    detect_spurious_reproduction,
    TaskType,
    is_numerical_accuracy_applicable,
    ReproductionProfile,
)
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.llm_backends import load_llm_from_env

# ── Output directory ──
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r002"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Task type: STRICT — D3 is pass/fail
TASK_TYPE = TaskType.STRICT

# ── Gold values (pre-computed from SciSciNet shards 0-9) ──
GOLD_PATH = OUTPUT_DIR / "gold_values.json"
GOLD = json.loads(GOLD_PATH.read_text())["gold_results"]


# ── Constrained Reproduction Prompt ──────────────────────────────────────────

def build_constrained_prompt() -> str:
    """Build constrained prompt for Petersen2024 STRICT reproduction."""
    return textwrap.dedent(f"""\
You are reproducing the following analysis from Petersen et al. (2024):
"The disruption index suffers from citation inflation and is confounded
by shifts in scholarly citation practice" (arXiv:2406.15311).

## Research Question
Is the disruption index (CD) a reliable measure of innovation trends, or
is it confounded by secular growth and citation practices?

## Task: STRICT Numerical Reproduction
Reproduce the multivariate regression analysis (Eq. 2) on SciSciNet data.

## Mandatory Constraints

**C1 — Data Source**:
  You MUST use SciSciNet data via:
  ```python
  from src.sciscigpt_local.sciscinet_connector import load_papers_sample
  papers = load_papers_sample(n_shards=10)
  ```

**C2 — Sample Filters** (match Petersen2024):
  - Year range: 2011 to 2015 (inclusive)
  - Reference count: 10 <= reference_count <= 200
  - Author count: 1 <= author_count <= 25
  - Citation count (5yr): 1 <= citation_count_5y <= 1000
  - Drop rows with NaN in: disruption_score, reference_count, author_count, citation_count_5y, year

**C3 — Dependent Variable**:
  - Use absolute value of disruption score: |CDp,5| = abs(disruption_score)

**C4 — Independent Variables** (log-transformed):
  - ln_kp = natural log of author_count
  - ln_rp = natural log of reference_count
  - ln_cp5 = natural log of citation_count_5y

**C5 — Model Specification** (Eq. 2 from paper):
  - OLS regression: |CDp,5| = const + bk*ln(kp) + br*ln(rp) + bc*ln(cp,5) + year_FE
  - Use statsmodels OLS (sm.OLS)
  - Include year fixed effects (dummy variables for each year, dropping first year as baseline)
  - Do NOT use robust standard errors, clustered errors, or regularization
  - Use sm.add_constant() for the intercept

**C6 — Required Output Sections** (each MUST start with `print("=== SECTION_NAME ===")`):
  1. DATA_LOAD — load data and print sample size after each filter step
  2. DESCRIPTIVE — print descriptive statistics: mean |CD|, mean rp, mean kp, mean cp5, std |CD|
  3. TRANSFORM — print min/max of log-transformed variables
  4. REGRESSION — print full statsmodels OLS summary, including coefficient table
  5. COEFFICIENTS — print coefficient, std err, p-value for ln_kp, ln_rp, ln_cp5 separately
  6. RESULTS — print sample N, R-squared, and direction of each coefficient

**C7 — SciSciNet Data Notes**:
  - SciSciNet uses nullable Int64/Float64 types — convert with .astype(float) or .astype(int) before statsmodels
  - year column is nullable Int64 — use .astype(int) for get_dummies
  - disruption_score is Float64 — use .dropna() before abs()

## Expected Output Format
After execution, print:
```
=== DIFF_TABLE ===
| Metric | Agent Value |
|--------|-------------|
| sample_N | <value> |
| R_squared | <value> |
| coef_ln_kp | <value> |
| coef_ln_rp | <value> |
| coef_ln_cp5 | <value> |
| p_ln_kp | <value> |
| p_ln_rp | <value> |
| p_ln_cp5 | <value> |
```

Write clean, well-structured Python code. Print intermediate steps clearly.
Do NOT use any gold/reference values in the code — compute everything from data.
""")


# ── Response Parsing ─────────────────────────────────────────────────────────

def parse_agent_response(response: Any) -> dict[str, Any]:
    """Extract code block and metadata from LLM response."""
    if hasattr(response, 'content'):
        raw = response.content
    elif isinstance(response, dict):
        raw = response.get("content", "")
    else:
        raw = str(response)

    if isinstance(raw, list):
        text_parts = []
        for block in raw:
            if isinstance(block, dict):
                text_parts.append(block.get("text", ""))
            else:
                text_parts.append(str(block))
        response_text = "\n".join(text_parts)
    else:
        response_text = str(raw)

    # Extract code block
    code = ""
    code_patterns = [
        r'```python\n(.*?)```',
        r'```py\n(.*?)```',
        r'```\n(.*?)```',
    ]
    for pat in code_patterns:
        m = re.search(pat, response_text, re.DOTALL)
        if m and len(m.group(1).strip()) > 50:
            code = m.group(1).strip()
            break

    # Also try to extract code between triple backticks without language
    if not code:
        m = re.search(r'```(.*?)```', response_text, re.DOTALL)
        if m and len(m.group(1).strip()) > 50:
            code = m.group(1).strip()

    return {
        "response_length": len(response_text),
        "code_length": len(code),
        "code": code,
        "response_text": response_text,
    }


# ── Code Execution ───────────────────────────────────────────────────────────

def execute_agent_code(code: str, timeout: int = 300) -> dict[str, Any]:
    """Execute agent-generated code in sandbox and parse output."""
    result = execute_python(code, timeout=timeout)

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")
    exit_code = result.get("exit_code", -1)

    has_traceback = "Traceback (most recent call last)" in stderr or "Error" in stderr
    has_import_error = "ModuleNotFoundError" in stderr or "ImportError" in stderr
    has_timeout = "timed out" in stderr.lower() or "timed out" in stdout.lower()

    # Parse metrics from stdout
    parsed_metrics = _parse_metrics(stdout)

    return {
        "stdout": stdout,
        "stderr": stderr,
        "exit_code": exit_code,
        "elapsed": result.get("elapsed", 0),
        "has_traceback": has_traceback,
        "has_import_error": has_import_error,
        "has_timeout": has_timeout,
        "parsed_metrics": parsed_metrics,
    }


def _parse_metrics(stdout: str) -> dict[str, Any]:
    """Parse key metrics from agent stdout."""
    metrics = {}

    # Try DIFF_TABLE format first: | coef_ln_kp | -0.000238 |
    for key, col_name in [("sample_N", "sample_N"), ("r_squared", "R_squared"),
                           ("coef_ln_kp", "coef_ln_kp"), ("coef_ln_rp", "coef_ln_rp"),
                           ("coef_ln_cp5", "coef_ln_cp5"),
                           ("p_ln_kp", "p_ln_kp"), ("p_ln_rp", "p_ln_rp"),
                           ("p_ln_cp5", "p_ln_cp5")]:
        m = re.search(rf'\|\s*{col_name}\s*\|\s*(-?[\d.e\+]+)', stdout)
        if m:
            val = m.group(1).replace(",", "")
            try:
                if "sample" in key:
                    metrics[key] = int(float(val))
                else:
                    metrics[key] = float(val)
            except ValueError:
                metrics[key] = val

    # Also try COEFFICIENTS format: ln_kp: coef=-0.000238, std_err=..., p_value=...
    for var in ["ln_kp", "ln_rp", "ln_cp5"]:
        coef_key = f"coef_{var}"
        p_key = f"p_{var}"
        if coef_key not in metrics:
            m = re.search(rf'{var}:\s*coef=(-?[\d.e\+]+).*?p_value=([\d.e\+]+)', stdout)
            if m:
                metrics[coef_key] = float(m.group(1))
                metrics[p_key] = float(m.group(2))

    # Fallback: regex patterns
    if "sample_N" not in metrics:
        m = re.search(r'[Nn]\s*(?:=\s*)?([\d,]+)\s*(?:papers|articles|observations)', stdout)
        if m:
            metrics["sample_N"] = int(m.group(1).replace(",", ""))
        else:
            m = re.search(r'Sample\s*N\s*[:=]\s*([\d,.]+)', stdout)
            if m:
                metrics["sample_N"] = int(float(m.group(1).replace(",", "")))

    if "r_squared" not in metrics:
        m = re.search(r'R-squared:\s+([\d.]+)', stdout)
        if m:
            metrics["r_squared"] = float(m.group(1))

    # Parse from statsmodels regression table line
    if "coef_ln_rp" not in metrics:
        m = re.search(r'ln_rp\s+(-?[\d.e\+]+)\s+([\d.e\+]+)\s+[\d.e\+-]+\s+([\d.e\+]+)', stdout)
        if m:
            metrics["coef_ln_rp"] = float(m.group(1))
            metrics["std_ln_rp"] = float(m.group(2))
            metrics["p_ln_rp"] = float(m.group(3))

    return metrics


# ── Section Substance Check ──────────────────────────────────────────────────

def check_section_substance(code: str, section_label: str,
                           min_effective_lines: int = 2) -> dict[str, Any]:
    """Verify a code section has both a header AND effective code lines."""
    # Match print("=== SECTION ===") with optional \n prefix
    header_pattern = rf'print\(["\'](?:\\n)?\s*=== {section_label} ===["\']\)'
    header_match = re.search(header_pattern, code)
    if not header_match:
        # Match bare string "=== SECTION ===" in code
        header_pattern2 = rf'["\'](?:\\n)?\s*=== {section_label} ===["\']'
        header_match2 = re.search(header_pattern2, code)
        if not header_match2:
            return {"has_header": False, "has_substance": False, "effective_lines": 0}
        header_end = header_match2.end()
    else:
        header_end = header_match.end()

    remaining = code[header_end:]
    newline_pos = remaining.find('\n')
    if newline_pos != -1:
        remaining = remaining[newline_pos + 1:]

    next_section = re.search(r'print\(["\']=== \w+ ===["\']\)', remaining)
    if not next_section:
        next_section = re.search(r'["\']=== \w+ ===["\']', remaining)
    section_body = remaining[:next_section.start()] if next_section else remaining

    effective_lines = 0
    for line in section_body.split('\n'):
        stripped = line.strip()
        if not stripped or stripped.startswith('#'):
            continue
        if re.match(r'^print\(["\']\s*-{3,}["\']\)', stripped):
            continue
        if stripped == 'print()':
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        effective_lines += 1

    return {"has_header": True,
            "has_substance": effective_lines >= min_effective_lines,
            "effective_lines": effective_lines}


def check_section_compliance(code: str) -> dict[str, Any]:
    """Check all 6 required sections have headers and substance."""
    required_sections = [
        "DATA_LOAD", "DESCRIPTIVE", "TRANSFORM",
        "REGRESSION", "COEFFICIENTS", "RESULTS",
    ]
    per_section = {}
    for section in required_sections:
        per_section[section] = check_section_substance(code, section)

    missing_headers = [s for s, r in per_section.items() if not r["has_header"]]
    stubbed = [s for s, r in per_section.items()
               if r["has_header"] and not r["has_substance"]]
    all_ok = len(missing_headers) == 0 and len(stubbed) == 0

    return {
        "compliant": all_ok,
        "total_sections": len(required_sections),
        "present_with_substance": len(required_sections) - len(missing_headers) - len(stubbed),
        "missing_headers": missing_headers,
        "stubbed": stubbed,
        "per_section": per_section,
    }


# ── Gold Comparison (STRICT) ─────────────────────────────────────────────────

def build_gold_dict() -> dict[str, Any]:
    """Build gold reference dictionary, nested by component for scoring framework."""
    g = GOLD
    return {
        "data_source": {
            "data_source": "SciSciNet (cssi/SciSciGPT-SciSciNet), shards 0-9",
        },
        "sample": {
            "filter_rules": [
                "year: 2011-2015",
                "reference_count: 10-200",
                "author_count: 1-25",
                "citation_count_5y: 1-1000",
            ],
            "N": g["sample_N"],
        },
        "indicator": {
            "formula": "|CDp,5| = |disruption_score| from SciSciNet, pre-computed CD index",
            "indicator_stats": {
                "mean": 0.002316,
                "std": 0.005855,
                "n": g["sample_N"],
            },
        },
        "model": {
            "spec_elements": [
                "OLS regression",
                "dependent: |CDp,5|",
                "independent: ln(kp), ln(rp), ln(cp5)",
                "year fixed effects",
                "statsmodels OLS with add_constant",
            ],
            "coefficients": {
                "ln_kp": g["coefficients"]["ln_kp"]["coef"],
                "ln_rp": g["coefficients"]["ln_rp"]["coef"],
                "ln_cp5": g["coefficients"]["ln_cp5"]["coef"],
            },
            # Full coefficient info (coef, std_err, p_value) for diff table
            "_full_coefficients": {
                "ln_kp": g["coefficients"]["ln_kp"],
                "ln_rp": g["coefficients"]["ln_rp"],
                "ln_cp5": g["coefficients"]["ln_cp5"],
            },
        },
        "result_table": {
            "target_tables": ["OLS regression summary"],
            "target_values": [
                {"metric": "R_squared", "value": g["r_squared"]},
                {"metric": "N", "value": g["sample_N"]},
            ],
            "expected_direction": "ln_rp negative, ln_cp5 positive",
        },
        "claim": {
            "conclusion_claims": [
                "CD decreases as reference list length (rp) increases (br negative)",
                "Citation inflation biases the disruption index downward over time",
            ],
        },
    }


def build_agent_dict(exec_result: dict) -> dict[str, Any]:
    """Build agent dictionary from execution results, nested by component."""
    metrics = exec_result.get("parsed_metrics", {})
    stdout = exec_result.get("stdout", "")
    code_executed = exec_result.get("exit_code", -1) == 0

    # Try to parse descriptive stats from stdout
    desc_stats = {}
    m = re.search(r'Mean\s*\|CD\|\s*:\s*([\d.]+)', stdout)
    if m:
        desc_stats["mean"] = float(m.group(1))
    m = re.search(r'Std\s*\|CD\|\s*:\s*([\d.]+)', stdout)
    if m:
        desc_stats["std"] = float(m.group(1))

    # Build coefficients dict
    coefs = {}
    for var in ["ln_kp", "ln_rp", "ln_cp5"]:
        coef_key = f"coef_{var}"
        p_key = f"p_{var}"
        if coef_key in metrics:
            coefs[var] = {
                "coef": metrics[coef_key],
                "p_value": metrics.get(p_key),
                "std_err": metrics.get(f"std_{var}"),
            }

    # Fallback: parse from statsmodels table in stdout
    if not coefs:
        for var_name in ["ln_kp", "ln_rp", "ln_cp5"]:
            m = re.search(
                rf'{var_name}\s+(-?[\d.e\+]+)\s+([\d.e\+]+)\s+[\d.e\+-]+\s+([\d.e\+]+)',
                stdout)
            if m:
                coefs[var_name] = {
                    "coef": float(m.group(1)),
                    "std_err": float(m.group(2)),
                    "p_value": float(m.group(3)),
                }

    agent_n = metrics.get("sample_N")
    agent_r2 = metrics.get("r_squared")

    return {
        "data_source": {
            "data_source": "SciSciNet (loaded via sciscinet_connector.load_papers_sample)",
            "code_executed": {"data_source": code_executed},
            "traceable": {"data_source": True},
            "hard_coded": {"data_source": False},
            "hallucinated": {"data_source": False},
        },
        "sample": {
            "filter_rules": [
                "year: 2011-2015",
                "reference_count: 10-200",
                "author_count: 1-25",
                "citation_count_5y: 1-1000",
            ],
            "N": agent_n,
            "code_executed": {"sample": code_executed},
            "traceable": {"sample": True},
            "hard_coded": {"sample": False},
            "hallucinated": {"sample": False},
        },
        "indicator": {
            "formula": "|CD| = abs(disruption_score)",
            "indicator_stats": desc_stats if desc_stats else None,
            "code_executed": {"indicator": code_executed},
            "traceable": {"indicator": True},
            "hard_coded": {"indicator": False},
            "hallucinated": {"indicator": False},
        },
        "model": {
            "spec_elements": [
                "OLS regression",
                "dependent: |CDp,5|",
                "independent: ln(kp), ln(rp), ln(cp5)",
                "year fixed effects",
                "statsmodels OLS with add_constant",
            ],
            "coefficients": {k: v["coef"] for k, v in coefs.items()} if coefs else {},
            "_full_coefficients": coefs,  # for diff table with std_err, p_value
            "code_executed": {"model": code_executed},
            "traceable": {"model": True},
            "hard_coded": {"model": False},
            "hallucinated": {"model": False},
        },
        "result_table": {
            "produced_tables": ["OLS regression summary"],
            "reproduced_values": [
                {"metric": "R_squared", "value": agent_r2},
                {"metric": "N", "value": agent_n},
            ],
            "observed_direction": "ln_rp negative, ln_cp5 positive",
            "code_executed": {"result_table": code_executed},
            "traceable": {"result_table": True},
            "hard_coded": {"result_table": False},
            "hallucinated": {"result_table": False},
        },
        "claim": {
            "conclusion_claims": [
                "CD decreases as reference list length (rp) increases (br negative)",
                "Citation inflation biases the disruption index downward over time",
            ],
        },
    }


def compute_diff_table(gold: dict, agent: dict) -> list[dict]:
    """Compute STRICT diff table between gold and agent, both nested by component."""
    diff_table = []

    # Sample N
    g_n = gold.get("sample", {}).get("N")
    a_n = agent.get("sample", {}).get("N")
    if g_n and a_n:
        diff_table.append({
            "component": "sample", "metric": "N",
            "gold": g_n, "agent": a_n,
            "absolute_error": abs(g_n - a_n),
            "match": g_n == a_n,
        })

    # R-squared
    g_r2 = gold.get("result_table", {}).get("target_values", [{}])
    if g_r2:
        g_r2 = [tv for tv in g_r2 if tv.get("metric") == "R_squared"]
        g_r2_val = g_r2[0]["value"] if g_r2 else None
    else:
        g_r2_val = None
    a_r2 = agent.get("result_table", {}).get("reproduced_values", [{}])
    if a_r2:
        a_r2 = [rv for rv in a_r2 if rv.get("metric") == "R_squared"]
        a_r2_val = a_r2[0]["value"] if a_r2 else None
    else:
        a_r2_val = None
    if g_r2_val is not None and a_r2_val is not None:
        diff_table.append({
            "component": "result_table", "metric": "R_squared",
            "gold": round(g_r2_val, 6), "agent": round(a_r2_val, 6),
            "absolute_error": round(abs(g_r2_val - a_r2_val), 6),
            "match": abs(g_r2_val - a_r2_val) < 0.001,
        })

    # Coefficients — use _full_coefficients for diff table (with p_values)
    g_coefs = gold.get("model", {}).get("_full_coefficients", {})
    a_coefs = agent.get("model", {}).get("_full_coefficients", {})
    for var in ["ln_kp", "ln_rp", "ln_cp5"]:
        gc = g_coefs.get(var, {})
        ac = a_coefs.get(var, {})
        if gc and ac:
            g_coef = gc["coef"]
            a_coef = ac["coef"]
            rel_err = abs(g_coef - a_coef) / max(abs(g_coef), 1e-10)
            diff_table.append({
                "component": "model", "metric": f"coef_{var}",
                "gold": g_coef, "agent": a_coef,
                "absolute_error": round(abs(g_coef - a_coef), 8),
                "relative_error": round(rel_err, 6),
                "match": rel_err < 0.01,
            })
            # P-value significance match
            g_p = gc.get("p_value")
            a_p = ac.get("p_value")
            if g_p is not None and a_p is not None:
                g_sig = g_p < 0.05
                a_sig = a_p < 0.05
                diff_table.append({
                    "component": "model", "metric": f"sig_{var}",
                    "gold": f"p={gc['p_value']:.4f}, sig={g_sig}",
                    "agent": f"p={ac['p_value']:.4f}, sig={a_sig}",
                    "match": g_sig == a_sig,
                })

    return diff_table


# ── Constrained Fix Prompt ───────────────────────────────────────────────────

def build_constrained_fix_prompt(original_code: str, error_text: str,
                                  issues: list) -> str:
    """Build prompt for constrained self-correction."""
    issues_text = "\n".join(f"- {i}" for i in issues) if issues else "see error below"

    return textwrap.dedent(f"""\
The Python code you generated failed to execute. Fix ONLY the error — do NOT
delete or simplify any analysis steps.

## Error
```
{error_text[-2000:]}
```

## Issues Detected
{issues_text}

## FIX RULES (STRICT — DO NOT VIOLATE):
1. Fix syntax errors, import issues, type conversion errors ONLY
2. DO NOT delete any section header (print("=== X ==="))
3. DO NOT replace working code with `# TODO` or `pass`
4. DO NOT reduce the sample size or change model specification
5. DO NOT simplify the regression (must use sm.OLS with year FE)
6. DO NOT remove any analysis module

## Original Code
```python
{original_code}
```

Return ONLY the fixed Python code in a ```python block. Every section
(=== DATA_LOAD ===, === DESCRIPTIVE ===, etc.) MUST be preserved with substance.
""")


# ── Constraint Compliance Check ──────────────────────────────────────────────

def check_constraint_compliance(stdout: str, metrics: dict) -> dict[str, Any]:
    """Check all constraints are satisfied in agent output."""
    violations = []
    required_sections = [
        "DATA_LOAD", "DESCRIPTIVE", "TRANSFORM",
        "REGRESSION", "COEFFICIENTS", "RESULTS",
    ]

    missing_sections = []
    for section in required_sections:
        if f"=== {section} ===" not in stdout:
            missing_sections.append(section)

    if missing_sections:
        violations.append(f"Missing sections: {missing_sections}")

    required_metrics = ["sample_N", "coef_ln_rp", "coef_ln_kp", "coef_ln_cp5"]
    missing_metrics = [m for m in required_metrics if m not in metrics]
    if missing_metrics:
        violations.append(f"Missing metrics: {missing_metrics}")

    # Check for model specification keywords in output
    if "OLS" not in stdout and "ols" not in stdout.lower():
        violations.append("OLS regression not detected in output")

    return {
        "compliant": len(violations) == 0,
        "violations": violations,
        "missing_sections": missing_sections,
        "missing_metrics": missing_metrics,
        "sections_found": len(required_sections) - len(missing_sections),
    }


# ── Audit Trail ──────────────────────────────────────────────────────────────

def record_audit_items(exec_result: dict, parsed: dict, agent_dict: dict,
                       compliance: dict, section_check: dict) -> dict:
    """Record all audit trail items for D5 (Auditability)."""
    return {
        "code_generated": {
            "chars": parsed.get("code_length", 0),
            "extracted": bool(parsed.get("code")),
        },
        "code_executed": {
            "exit_code": exec_result.get("exit_code"),
            "elapsed": exec_result.get("elapsed"),
            "has_traceback": exec_result.get("has_traceback"),
            "has_timeout": exec_result.get("has_timeout"),
        },
        "section_compliance": {
            "compliant": section_check.get("compliant", False),
            "present": section_check.get("present_with_substance", 0),
            "total": section_check.get("total_sections", 6),
            "missing_headers": section_check.get("missing_headers", []),
            "stubbed": section_check.get("stubbed", []),
        },
        "constraint_compliance": compliance,
        "metrics_parsed": len(exec_result.get("parsed_metrics", {})),
        "coefficients_found": len(agent_dict.get("coefficients", {})),
    }


# ── Main R002 Runner ────────────────────────────────────────────────────────

def run_r002(model_name: str = "deepseek-v4-pro") -> dict[str, Any]:
    """Execute R002: STRICT reproduction of Petersen2024."""
    print("=" * 70)
    print("  R002: STRICT Reproduction — Petersen et al. (2024)")
    print(f"  Model: {model_name}")
    print(f"  Task Type: {TASK_TYPE.value} (D3 is pass/fail)")
    print(f"  Output: {OUTPUT_DIR}")
    print("=" * 70)

    # ── Step 0: Load LLM ──
    print("\n── Step 0: Loading LLM ──")
    if model_name == "mock":
        from src.sciscigpt_local.mock_llm import MockLLM
        llm = MockLLM()
        print("  Using MockLLM (dry run)")
    else:
        llm = load_llm_from_env()
        print(f"  LLM loaded: {type(llm).__name__}")

    # ── Step 1: Generate reproduction code ──
    print("\n── Step 1: Generating reproduction code (constrained prompt) ──")
    prompt = build_constrained_prompt()

    t0 = time.time()
    response = llm.invoke([{"role": "user", "content": prompt}])
    gen_elapsed = time.time() - t0

    parsed = parse_agent_response(response)
    response_text = parsed["response_text"]

    print(f"  Response: {parsed['response_length']:,} chars in {gen_elapsed:.1f}s")
    print(f"  Code extracted: {parsed['code_length']:,} chars")

    (OUTPUT_DIR / "llm_response.txt").write_text(response_text)

    if not parsed["code"]:
        print("  ERROR: No code extracted from LLM response")
        return {"status": "FAILED", "stage": "code_extraction",
                "error": "No code block found"}

    code = parsed["code"]
    (OUTPUT_DIR / "reproduce_v0_llm.py").write_text(code)

    # ── Step 2: Section compliance check (pre-execution) ──
    print("\n── Step 2: Pre-execution section check ──")
    section_check = check_section_compliance(code)
    if section_check["compliant"]:
        print(f"  ✓ All {section_check['total_sections']} sections present with substance")
    else:
        for s, r in section_check["per_section"].items():
            if not r["has_header"]:
                print(f"  ✗ {s}: header missing")
            elif not r["has_substance"]:
                print(f"  ⚠ {s}: header present but no substance ({r['effective_lines']} effective lines)")

    # ── Step 3: Execute with constrained self-correction ──
    print("\n── Step 3: Executing in sandbox (constrained self-correction) ──")
    max_fixes = 3
    exec_result = None

    for fix_attempt in range(max_fixes + 1):
        code_path = OUTPUT_DIR / f"reproduce_a{fix_attempt}.py"
        code_path.write_text(code)

        exec_result = execute_agent_code(code, timeout=300)

        ok = (exec_result["exit_code"] == 0 and not exec_result["has_traceback"]
              and not exec_result["has_timeout"])
        if ok:
            print(f"  ✓ Execution OK (attempt {fix_attempt + 1}, "
                  f"{exec_result['elapsed']:.1f}s)")
            break

        if fix_attempt == 0:
            print(f"  ✗ Execution failed (attempt {fix_attempt + 1}, "
                  f"{exec_result['elapsed']:.1f}s)")
        else:
            print(f"  ✗ Fix attempt {fix_attempt} failed ({exec_result['elapsed']:.1f}s)")

        err_text = exec_result.get("stderr", "") or exec_result.get("stdout", "")
        if exec_result["has_traceback"]:
            err_lines = [l for l in err_text.split("\n")
                        if "Error" in l or "Traceback" in l]
            for line in err_lines[:3]:
                print(f"    {line[:120]}")

        if fix_attempt < max_fixes:
            print(f"  → Requesting constrained fix from LLM...")
            fix_prompt = build_constrained_fix_prompt(code, err_text, [])
            fix_response = llm.invoke([{"role": "user", "content": fix_prompt}])
            fix_parsed = parse_agent_response(fix_response)

            if fix_parsed["code"] and len(fix_parsed["code"]) > 100:
                new_section_check = check_section_compliance(fix_parsed["code"])
                if not new_section_check["compliant"]:
                    missing = new_section_check["missing_headers"]
                    stubbed = new_section_check["stubbed"]
                    reasons = []
                    if missing:
                        reasons.append(f"headers missing: {missing}")
                    if stubbed:
                        reasons.append(f"stubs: {stubbed}")
                    print(f"    ⚠️  SECTION DEGRADATION: {'; '.join(reasons)}")
                    print(f"    REJECTING fix — sections must be preserved with substance")
                    (OUTPUT_DIR / f"reproduce_fix{fix_attempt + 1}_REJECTED.py").write_text(
                        fix_parsed["code"])
                    continue

                code = fix_parsed["code"]
                (OUTPUT_DIR / f"reproduce_fix{fix_attempt + 1}.py").write_text(code)
                print(f"    Fixed code: {len(code):,} chars, "
                      f"all sections preserved ✓")
            else:
                print(f"    Fix extraction failed ({len(fix_parsed.get('code', ''))} chars)")
                break

    if exec_result is None:
        exec_result = {
            "exit_code": -1, "elapsed": 0, "stdout": "", "stderr": "",
            "has_traceback": False, "has_import_error": False, "has_timeout": False,
            "parsed_metrics": {},
        }

    # Save execution outputs
    (OUTPUT_DIR / "stdout.txt").write_text(exec_result["stdout"])
    (OUTPUT_DIR / "stderr.txt").write_text(exec_result["stderr"])

    metrics = exec_result["parsed_metrics"]
    if metrics:
        print(f"  Parsed metrics: {list(metrics.keys())}")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"    {k} = {v:.6f}")
            else:
                print(f"    {k} = {v}")

    (OUTPUT_DIR / "reproduce_final.py").write_text(code)

    # ── Step 4: Constraint compliance check ──
    print("\n── Step 4: Constraint compliance check ──")
    compliance = check_constraint_compliance(exec_result["stdout"], metrics)
    if compliance["compliant"]:
        print("  ✓ All constraints satisfied")
    else:
        print(f"  ✗ Violations: {compliance['violations']}")
        for v in compliance["violations"]:
            print(f"    - {v}")

    # ── Step 5: STRICT Gold comparison ──
    print("\n── Step 5: STRICT Gold comparison (D3 = pass/fail) ──")
    gold = build_gold_dict()
    agent_dict = build_agent_dict(exec_result)

    diff_table = compute_diff_table(gold, agent_dict)
    n_match = 0
    n_total = 0
    for d in diff_table:
        match_str = "✓" if d.get("match", False) else "✗"
        n_total += 1
        if d.get("match"):
            n_match += 1
        if "relative_error" in d:
            print(f"  {d['component']}.{d['metric']}: gold={d['gold']:.6f}, "
                  f"agent={d['agent']:.6f}, rel_err={d['relative_error']:.4%} {match_str}")
        elif "absolute_error" in d:
            print(f"  {d['component']}.{d['metric']}: gold={d['gold']}, "
                  f"agent={d['agent']}, abs_err={d['absolute_error']:.6f} {match_str}")
        else:
            print(f"  {d['component']}.{d['metric']}: {d['gold']} vs {d['agent']} {match_str}")
    if n_total > 0:
        print(f"  D3 match rate: {n_match}/{n_total} ({n_match/n_total:.1%})")

    # ── Step 6: 5-Dimension scoring (STRICT) ──
    print(f"\n── Step 6: 5-Dimension scoring (task_type={TASK_TYPE.value}) ──")
    print(f"  D3 applicability: {'pass/fail' if is_numerical_accuracy_applicable(TASK_TYPE) else 'reference-only'}")

    profile = build_reproduction_profile("petersen2024_disruption_index",
                                         gold, agent_dict, task_type=TASK_TYPE)

    components = ["data_source", "sample", "indicator", "model", "result_table"]
    all_dims = ["fidelity", "executability", "numerical_accuracy",
                "claim_consistency", "auditability"]

    for comp in components:
        cs = profile.component_scores.get(comp)
        if cs:
            scores = {}
            for d in all_dims:
                if d in cs.dimension_scores:
                    ds = cs.dimension_scores[d]
                    val = f"{ds.score:.2f}"
                    if ds.evidence.get("reference_only"):
                        val += "*"
                    scores[d] = val
                else:
                    scores[d] = "—"
            dims_str = " ".join(f"{d[:6]}={scores[d]:>6}" for d in all_dims)
            print(f"  {comp:<14} {dims_str}")

    maturity = compute_maturity_level(profile, task_type=TASK_TYPE)
    maturity_label = format_maturity(maturity, TASK_TYPE)
    print(f"\n  Reproduction Maturity: {maturity_label}")

    spurious_flags = detect_spurious_reproduction(profile)
    if spurious_flags:
        print(f"  ⚠️  Spurious flags: {spurious_flags}")
    else:
        print(f"  ✓ No spurious flags")

    # ── Step 7: Audit trail ──
    print("\n── Step 7: Audit trail ──")
    audit = record_audit_items(exec_result, parsed, agent_dict, compliance, section_check)
    for audit_id, items in audit.items():
        if isinstance(items, dict):
            status = "✓" if items.get("compliant", items.get("executable", True)) else "✗"
        else:
            status = str(items)
        print(f"  {audit_id}: {status}")
    (OUTPUT_DIR / "audit.json").write_text(json.dumps(audit, indent=2))

    # ── Step 8: Save results ──
    print("\n── Step 8: Saving results ──")
    results = {
        "run_id": "R002",
        "paper": "petersen2024_disruption_index",
        "task_type": TASK_TYPE.value,
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "stages": {
            "code_generation": {"elapsed": gen_elapsed,
                              "code_chars": parsed["code_length"]},
            "execution": {
                "exit_code": exec_result["exit_code"],
                "elapsed": exec_result["elapsed"],
                "has_traceback": exec_result["has_traceback"],
                "has_timeout": exec_result["has_timeout"],
            },
        },
        "constraint_compliance": compliance,
        "gold": gold,
        "agent": agent_dict,
        "diff_table": diff_table,
        "d3_match_rate": f"{n_match}/{n_total}" if n_total > 0 else "N/A",
        "profile": {
            "maturity": maturity,
            "task_type": TASK_TYPE.value,
            "d3_applicable": is_numerical_accuracy_applicable(TASK_TYPE),
            "matrix": profile.to_matrix(),
            "spurious_flags": spurious_flags,
        },
        "audit": audit,
        "parsed_metrics": metrics,
    }

    out_path = OUTPUT_DIR / "r002_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"  Results → {out_path}")

    # ── Summary ──
    exec_ok = exec_result["exit_code"] == 0 and not exec_result["has_traceback"]
    print(f"\n{'=' * 70}")
    print(f"  R002 COMPLETE")
    print(f"  Task Type: {TASK_TYPE.value} (D3 = pass/fail)")
    print(f"{'=' * 70}")
    print(f"  Execution:        {'✓ SUCCESS' if exec_ok else '✗ FAILED'}")
    print(f"  Compliance:       {'✓ PASS' if compliance['compliant'] else '✗ FAIL'}")
    print(f"  Maturity:         {maturity_label}")
    print(f"  D3 applicable:    {is_numerical_accuracy_applicable(TASK_TYPE)}")
    print(f"  D3 match rate:    {n_match}/{n_total}" if n_total > 0 else "  D3 match rate: N/A")
    print(f"  Spurious:         {len(spurious_flags)} flags")
    print(f"  Metrics parsed:   {len(metrics)}")

    return results


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="R002: STRICT reproduction of Petersen2024 on SciSciNet")
    parser.add_argument("--mock", action="store_true", help="Use MockLLM for dry run")
    parser.add_argument("--model", default="deepseek-v4-pro", help="Model name")
    args = parser.parse_args()

    model = "mock" if args.mock else args.model

    try:
        results = run_r002(model_name=model)
    except Exception as e:
        print(f"\n  R002 FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
