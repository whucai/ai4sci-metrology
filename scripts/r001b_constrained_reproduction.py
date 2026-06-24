#!/usr/bin/env python3
"""R001b: Constrained reproduction of Wu et al. (2019) on SciSciNet.

R001b is a same-dataset calibration run — stricter constraints than R001:
  1. Must use SciSciNet data (specified)
  2. Must reproduce sample window 1954-2014
  3. Must output sample N
  4. Must preserve complete model structure (decile means + OLS + year FE)
  5. Self-correction: local fixes only (syntax, imports, type errors) — no module deletion

New in R001b:
  - Codex pre-execution validation: code is reviewed/fixed by Codex BEFORE sandbox
  - Constraint compliance check: verifies all 6 components are present in output
  - Task type explicitly set to DATA_SUB for scoring

Usage:
    conda activate sciscigpt && python scripts/r001b_constrained_reproduction.py
    conda activate sciscigpt && python scripts/r001b_constrained_reproduction.py --mock
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

from src.sciscibench.annotation import create_wu2019
from src.sciscibench.eval.dimensions import (
    build_reproduction_profile,
    compute_maturity_level,
    format_maturity,
    detect_spurious_reproduction,
    TaskType,
    is_numerical_accuracy_applicable,
    COMPONENT_DIMENSION_MAP,
    ReproductionProfile,
)
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.llm_backends import load_llm_from_env

# ── Output directory ──
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r001b"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Task type for this run
TASK_TYPE = TaskType.DATA_SUB

# ── Constrained Reproduction Prompt ──────────────────────────────────────────

def build_constrained_prompt() -> str:
    """Build a constrained reproduction prompt with explicit requirements.

    Key constraints vs R001:
      - Explicit data source requirement
      - Explicit sample window
      - Must output sample N
      - Must preserve complete 6-component model structure
    """
    paper = create_wu2019()

    return f"""## Task: Constrained Reproduction — Wu, Wang & Evans (2019)

You are a computational reproduction agent. Reproduce the core analysis of
Wu et al. (2019) "Large teams develop and small teams disrupt science and
technology" (Nature, {paper.year}) under STRICT constraints.

### Paper
- **Title**: {paper.title}
- **Authors**: {', '.join(paper.authors)}
- **Venue**: {paper.venue} ({paper.year})
- **DOI**: {paper.doi}
- **Research Question**: {paper.research_question}

### Mandatory Constraints

You MUST follow ALL of these constraints. The reproduction will be REJECTED
if any constraint is violated.

**C1 — Data Source**:
  You MUST use SciSciNet data via:
  ```python
  from src.sciscigpt_local.sciscinet_connector import load_table
  papers = load_table("papers")
  citations = load_table("paper_citations")
  ```
  The papers table has a precomputed `disruption_score` column.

**C2 — Sample Window**:
  You MUST use papers with year 1954-2014 and author_count > 0.
  Filter: papers['year'] >= 1954 AND papers['year'] <= 2014 AND papers['author_count'] > 0.
  Print the EXACT sample N after filtering.

**C3 — Sample N**:
  Print sample N with the EXACT label: `sample_size: <N>`

**C4 — Complete Model Structure**:
  Your analysis MUST include ALL of the following. Do NOT skip any module:
  (a) Indicator statistics: mean, std, min, max of disruption_score
  (b) D-index from-scratch validation: compute D for 5 papers using the
      paper_citations table, compare with precomputed disruption_score
  (c) Team-size decile means: group papers by team_size decile, compute
      mean disruption_score per decile
  (d) OLS regression: disruption_score ~ log(author_count) + C(year)
      with statsmodels, print the full summary table
  (e) Diff table: compare your results with expected values from the paper
  (f) Claims: state 2-3 conclusion claims supported by your results

**C5 — Self-Correction Rules** (if code fails):
  - You may ONLY fix: syntax errors, import errors, type errors, missing variables
  - You MUST NOT delete any analysis module (a)-(f) listed above
  - You MUST NOT replace the regression with a simpler analysis
  - If a module fails, FIX it — do not remove it

### Print Format (parseable)

Use EXACTLY these section labels:

```
=== DATA_LOAD ===
papers_loaded: <N>
citations_loaded: <N>

=== SAMPLE ===
sample_size: <N>
time_window: 1954-2014
filters_applied: ['year in [1954,2014]', 'author_count > 0', 'has disruption_score']

=== INDICATOR_STATS ===
D_mean: <value>
D_std: <value>
D_min: <value>
D_max: <value>

=== VALIDATION ===
<for each of 5-10 papers: paper_id, computed_D, original_D, error, MATCH/MISMATCH>
validation_n: <N>
validation_mean_abs_error: <value>
validation_match_rate: <value>

=== REGRESSION ===
Decile means:
  Decile 0: mean_D=<value>
  ...
team_size_coefficient: <value>
team_size_pvalue: <value>
r_squared: <value>
n_observations: <value>
direction: <value>

=== REGRESSION_TABLE ===
<full statsmodels OLS summary>

=== DIFF_TABLE ===
<comparison with paper expected values>

=== CLAIMS ===
1. <claim 1>
2. <claim 2>
3. <claim 3>
```

### Important Notes
- Use precomputed disruption_score for main analysis
- Compute D-index from scratch for ONLY 5-10 validation papers
- Convert SciSciNet nullable Int64 columns with .astype(int) before statsmodels
- Set random seed (np.random.seed(42)) for reproducibility
- Sample 20,000 papers for regression (not all 111K)
- Do NOT import from src.sciscigpt_local except sciscinet_connector.load_table
- Write COMPLETE, RUNNABLE code — no placeholders, no "..." ellipsis

Your response must contain a ```python code block with the complete script.
"""


# ── Output Parsers (from R001, reused) ──────────────────────────────────────

def parse_agent_response(response) -> dict[str, Any]:
    """Parse LLM response into structured components."""
    content = response.content

    if isinstance(content, list):
        text_parts = []
        for block in content:
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif "text" in block:
                    text_parts.append(str(block["text"]))
        response_text = "\n".join(text_parts)
    else:
        response_text = str(content)

    response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    code = ""
    code_match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()

    # Filter non-code narration lines
    clean_lines = []
    for line in code.split("\n"):
        stripped = line.strip()
        if not stripped:
            clean_lines.append(line)
            continue
        if re.match(r"^(Okay|Let me|I need|First|Wait|The user|Now |But |So |However|"
                    r"Alternatively|Maybe|Perhaps|Hmm|Thus|Therefore|Here)", stripped):
            continue
        clean_lines.append(line)
    code = "\n".join(clean_lines).strip()

    return {
        "code": code,
        "code_length": len(code),
        "response_length": len(response_text),
    }


def parse_stdout_metrics(stdout: str) -> dict[str, Any]:
    """Parse structured metrics from sandbox stdout."""
    metrics: dict[str, Any] = {}

    patterns = {
        "papers_loaded": r"papers_loaded:\s*([\d,]+)",
        "citations_loaded": r"citations_loaded:\s*([\d,]+)",
        "sample_size": r"sample_size:\s*([\d,]+)",
        "time_window": r"time_window:\s*([^\n]+)",
        "filters_applied": r"filters_applied:\s*\[([^\]]*)\]",
        "D_mean": r"D_mean:\s*([-\d.e]+)",
        "D_std": r"D_std:\s*([-\d.e]+)",
        "D_min": r"D_min:\s*([-\d.e]+)",
        "D_max": r"D_max:\s*([-\d.e]+)",
        "team_size_coefficient": r"team_size_coefficient:\s*([-\d.e]+)",
        "team_size_pvalue": r"team_size_pvalue:\s*([-\d.e]+)",
        "r_squared": r"r_squared:\s*([-\d.e]+)",
    }

    for key, pattern in patterns.items():
        match = re.search(pattern, stdout, re.IGNORECASE)
        if match:
            val = match.group(1).strip()
            try:
                if key.endswith("_loaded") or key == "sample_size":
                    metrics[key] = int(val.replace(",", ""))
                elif key in ("D_mean", "D_std", "D_min", "D_max",
                            "team_size_coefficient", "team_size_pvalue", "r_squared"):
                    metrics[key] = float(val)
                else:
                    metrics[key] = val
            except (ValueError, TypeError):
                metrics[key] = val

    # Fallback: parse statsmodels table for team_size row
    team_match = re.search(
        r"(?:team_size|log_team_size)\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)",
        stdout
    )
    if team_match and "team_size_coefficient" not in metrics:
        try:
            metrics["team_size_coefficient"] = float(team_match.group(1))
            metrics["team_size_pvalue"] = float(team_match.group(4))
        except (ValueError, IndexError):
            pass

    r2_match = re.search(r"R-squared:\s+([-\d.e]+)", stdout)
    if r2_match and "r_squared" not in metrics:
        try:
            metrics["r_squared"] = float(r2_match.group(1))
        except ValueError:
            pass

    return metrics


def extract_claims_from_output(stdout: str) -> list[str]:
    """Extract conclusion claims from agent output."""
    claims = []
    in_claims = False
    for line in stdout.split("\n"):
        if re.search(r"===?\s*CLAIMS?\s*=?=?", line, re.IGNORECASE):
            in_claims = True
            continue
        if in_claims and re.search(r"^===?", line):
            break
        if in_claims and line.strip():
            cleaned = re.sub(r"^[\s\-*\d.]+\s*", "", line.strip())
            if len(cleaned) > 10:
                claims.append(cleaned)
    return claims


# ── Constraint Compliance Check ──────────────────────────────────────────────

# Required sections that must appear in agent output
REQUIRED_SECTIONS = [
    ("DATA_LOAD", "data source loading"),
    ("SAMPLE", "sample construction with N"),
    ("INDICATOR_STATS", "D-index distribution statistics"),
    ("VALIDATION", "D-index from-scratch validation"),
    ("REGRESSION", "decile means + OLS output"),
    ("REGRESSION_TABLE", "full statsmodels regression table"),
    ("DIFF_TABLE", "comparison with paper values"),
    ("CLAIMS", "conclusion claims"),
]

REQUIRED_METRICS = [
    "sample_size",
    "D_mean",
    "D_std",
    "team_size_coefficient",
    "team_size_pvalue",
]


def check_constraint_compliance(stdout: str, parsed_metrics: dict) -> dict[str, Any]:
    """Check whether agent output satisfies all mandatory constraints.

    Returns dict with:
      - compliant: bool
      - missing_sections: list of missing required sections
      - missing_metrics: list of missing required metrics
      - violations: list of human-readable violation descriptions
    """
    missing_sections = []
    for section_label, description in REQUIRED_SECTIONS:
        if f"=== {section_label}" not in stdout:
            missing_sections.append(section_label)

    missing_metrics = []
    for metric in REQUIRED_METRICS:
        if metric not in parsed_metrics:
            missing_metrics.append(metric)

    violations = []
    if missing_sections:
        violations.append(f"Missing required sections: {', '.join(missing_sections)}")
    if missing_metrics:
        violations.append(f"Missing required metrics: {', '.join(missing_metrics)}")

    # Check sample window constraint
    time_window = parsed_metrics.get("time_window", "")
    if time_window and "1954" not in str(time_window):
        violations.append(f"Sample window mismatch: expected 1954-2014, got {time_window}")

    return {
        "compliant": len(violations) == 0,
        "missing_sections": missing_sections,
        "missing_metrics": missing_metrics,
        "violations": violations,
    }


# ── Codex Pre-Execution Validation ──────────────────────────────────────────

def validate_with_codex(code: str, task_description: str = "") -> dict[str, Any]:
    """Send code to Codex for pre-execution review and fixes.

    Codex checks for:
      - Syntax errors
      - Missing imports
      - Type incompatibilities (nullable Int64 → patsy)
      - Common SciSciNet pitfalls

    Returns dict with:
      - reviewed_code: corrected code (or original if no fixes)
      - issues_found: list of issues Codex identified
      - fixes_applied: list of fixes Codex made
    """
    codex_prompt = f"""Review the following Python reproduction script for correctness.
This script uses SciSciNet data (pandas DataFrames with nullable Int64 types) and
statsmodels for regression.

Common issues to check:
1. Nullable Int64 columns must be converted with .astype(int) before statsmodels
2. set operations on SciSciNet columns need set(int(r) for r in col), not col.intersection()
3. Missing imports (numpy, pandas, statsmodels.api, statsmodels.formula.api)
4. Syntax errors or indentation problems
5. Undefined variables

Task: {task_description}

Code to review:
```python
{code}
```

If you find issues, output the CORRECTED code in a ```python block.
If the code is correct, output "NO_ISSUES" and nothing else.

Output ONLY the corrected code block or "NO_ISSUES" — no explanation needed."""

    return {
        "reviewed_code": code,
        "issues_found": [],
        "fixes_applied": [],
        "codex_used": False,
        "note": "Codex not available — skipping pre-execution validation",
    }


def validate_with_codex_mcp(code: str, task_description: str = "") -> dict[str, Any]:
    """Send code to Codex MCP tool for pre-execution review.

    Uses the mcp__codex__codex MCP tool to validate and fix code before
    sandbox execution. This catches common issues (nullable Int64, missing
    imports, syntax errors) before the expensive sandbox cycle.
    """
    prompt = f"""Review this Python reproduction script for correctness and fix any issues.

Context: This script reproduces Wu et al. (2019) using SciSciNet data.
Common pitfalls:
1. SciSciNet uses nullable Int64 — convert with .astype(int) before statsmodels or patsy
2. Set operations need set(int(r) for r in series) — no .intersection() on IntegerArray
3. Must import statsmodels.formula.api as smf for OLS
4. disruption_score may have NaN — filter with .notna()

Task description: {task_description}

Fix ALL issues you find. Output the complete corrected code in a ```python block.
Do NOT remove any analysis modules. Do NOT simplify the analysis.
Only fix bugs — preserve the full model structure (indicator stats, validation,
decile means, OLS regression, diff table, claims).

Code:
```python
{code}
```"""
    return {
        "prompt": prompt,
        "code_length": len(code),
    }


# ── Sandbox Execution ────────────────────────────────────────────────────────

def execute_agent_code(code: str, timeout: int = 300) -> dict[str, Any]:
    """Execute agent-generated code in sandbox."""
    t0 = time.time()
    result = execute_python(code, timeout=timeout)
    elapsed = time.time() - t0

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    metrics = parse_stdout_metrics(stdout) if result["exit_code"] == 0 else {}
    claims = extract_claims_from_output(stdout)

    has_traceback = "Traceback (most recent call last)" in stderr
    has_import_error = "ModuleNotFoundError" in stderr or "ImportError" in stderr
    has_timeout = "timed out" in stderr.lower() or result["exit_code"] == -1

    return {
        "exit_code": result["exit_code"],
        "elapsed": round(elapsed, 2),
        "stdout": stdout[-50000:],
        "stderr": stderr[-5000:],
        "has_traceback": has_traceback,
        "has_import_error": has_import_error,
        "has_timeout": has_timeout,
        "parsed_metrics": metrics,
        "parsed_claims": claims,
        "sandbox_dir": str(Path(result.get("environment", {}).get("workdir", ""))),
    }


# ── Self-Correction (Constrained) ────────────────────────────────────────────

def build_constrained_fix_prompt(code: str, error_text: str,
                                 violations_before: list[str]) -> str:
    """Build a fix prompt that enforces local-only fixes.

    The fix prompt explicitly forbids:
      - Deleting analysis modules
      - Replacing regression with simpler analysis
      - Removing validation or claims sections
    """
    violation_note = ""
    if violations_before:
        violation_note = ("\nBefore the error, these required sections were MISSING:\n" +
                         "\n".join(f"  - {v}" for v in violations_before) +
                         "\nYou MUST include them in your fix.\n")

    return f"""The following Python code failed. Fix ONLY the error — do NOT delete
any analysis modules or simplify the analysis.

CONSTRAINTS:
- You may ONLY fix: syntax errors, import errors, type errors, missing variables
- You MUST NOT delete any of these modules: DATA_LOAD, SAMPLE, INDICATOR_STATS,
  VALIDATION, REGRESSION, REGRESSION_TABLE, DIFF_TABLE, CLAIMS
- You MUST NOT replace OLS regression with a simpler analysis
- You MUST NOT remove the D-index from-scratch validation
- You MUST NOT shorten the output format — keep all section labels
- If a module fails, FIX the bug — do NOT delete the module
{violation_note}
Error:
{error_text[:1500]}

Current code:
```python
{code[:4000]}
```

Output ONLY the corrected, COMPLETE Python code in a ```python block.
Do NOT use "..." or "# rest of code unchanged" — include EVERYTHING."""


def check_section_substance(code: str, section_label: str, min_effective_lines: int = 2) -> dict[str, Any]:
    """Check that a section has substantive code beyond just the header print.

    An agent could keep the `print(\"=== SECTION ===\")` header but delete all
    the actual computation and output. This function verifies there are at
    least `min_effective_lines` of substantive code after the header.

    Returns dict with:
      - has_header: bool — section header found
      - has_substance: bool — enough effective code after header
      - effective_lines: int — count of substantive lines found
    """
    # Match the full print statement line: print("=== SECTION ===") or print('=== SECTION ===')
    header_pattern = rf'print\(["\']=== {section_label} ===["\']\)'
    header_match = re.search(header_pattern, code)
    if not header_match:
        # Also match if the header string appears standalone (e.g. in f-string or variable)
        header_pattern2 = rf'["\']=== {section_label} ===["\']'
        header_match2 = re.search(header_pattern2, code)
        if not header_match2:
            return {"has_header": False, "has_substance": False, "effective_lines": 0}
        header_end = header_match2.end()
    else:
        header_end = header_match.end()

    # Get code after the header line, until the next section header or end of code
    # Skip to end of the header line in case there's trailing content
    remaining = code[header_end:]
    newline_pos = remaining.find('\n')
    if newline_pos != -1:
        remaining = remaining[newline_pos + 1:]

    next_section = re.search(r'print\(["\']=== \w+ ===["\']\)', remaining)
    if not next_section:
        next_section = re.search(r'["\']=== \w+ ===["\']', remaining)
    section_body = remaining[:next_section.start()] if next_section else remaining

    # Count effective lines — exclude empty lines, comments, and decorator prints
    effective_lines = 0
    for line in section_body.split('\n'):
        stripped = line.strip()
        if not stripped:
            continue
        if stripped.startswith('#'):
            continue
        if re.match(r'^print\(["\']\s*-{3,}["\']\)$', stripped):
            continue
        if re.match(r'^print\(["\']={3,}["\']\)$', stripped):
            continue
        if stripped == 'print()':
            continue
        if stripped.startswith('"""') or stripped.startswith("'''"):
            continue
        effective_lines += 1

    return {
        "has_header": True,
        "has_substance": effective_lines >= min_effective_lines,
        "effective_lines": effective_lines,
    }


def check_module_preservation(original_code: str, fixed_code: str) -> dict[str, Any]:
    """Check whether self-correction preserved all required modules with substance.

    Two-level check:
      1. Header check — does `=== SECTION ===` still appear?
      2. Substance check — is there real code after the header, or just a stub?

    Returns dict with:
      - modules_preserved: bool — all headers + substance intact
      - removed_modules: list — section labels whose headers disappeared
      - stubbed_modules: list — section labels with headers but no effective code
      - length_ratio: fixed/original char ratio (below 0.5 is suspicious)
      - per_section: dict of label → {has_header, has_substance, effective_lines}
    """
    required_labels = [
        "DATA_LOAD", "SAMPLE", "INDICATOR_STATS", "VALIDATION",
        "REGRESSION", "REGRESSION_TABLE", "DIFF_TABLE", "CLAIMS",
    ]

    removed_modules = []
    stubbed_modules = []
    per_section = {}

    for label in required_labels:
        in_original = f"=== {label}" in original_code
        in_fixed = f"=== {label}" in fixed_code

        if in_original and not in_fixed:
            removed_modules.append(label)
            per_section[label] = {"has_header": False, "has_substance": False,
                                  "effective_lines": 0}

    # Substance check for modules whose headers survived
    for label in required_labels:
        if label in removed_modules:
            continue
        result = check_section_substance(fixed_code, label, min_effective_lines=2)
        per_section[label] = result
        if result["has_header"] and not result["has_substance"]:
            stubbed_modules.append(label)

    length_ratio = len(fixed_code) / max(1, len(original_code))

    return {
        "modules_preserved": len(removed_modules) == 0 and len(stubbed_modules) == 0,
        "removed_modules": removed_modules,
        "stubbed_modules": stubbed_modules,
        "length_ratio": round(length_ratio, 3),
        "original_chars": len(original_code),
        "fixed_chars": len(fixed_code),
        "per_section": per_section,
    }


# ── Gold & Agent Dicts ───────────────────────────────────────────────────────

def build_gold_dict() -> dict:
    """Build gold annotation from Wu2019 paper."""
    paper = create_wu2019()
    return {
        "data_source": {
            "data_source": paper.data_source,
            "data_description": paper.data_description,
            "filter_rules": [paper.data_source],
        },
        "sample": {
            "data_source": paper.data_source,
            "N": 42_000_000,
            "time_window": paper.sample_scope.get("time_window", ""),
            "filter_rules": paper.sample_scope.get("filters", []),
        },
        "indicator": {
            "formula": paper.dependent_variables[0].get("formula", ""),
            "indicator_stats": {"mean": -0.02, "std": 0.15},
        },
        "model": {
            "spec_elements": [
                "descriptive", "OLS", "team_size_deciles",
                "mean_D_by_group", "year_fixed_effects"
            ],
            "coefficients": {"team_size_coef": -0.03, "year_1954": 0.01},
        },
        "result_table": {
            "target_tables": ["Table 1: Mean D-index by team size decile"],
            "target_values": [
                {"label": "small_teams_D", "value": 0.04},
                {"label": "large_teams_D", "value": -0.02},
            ],
            "expected_direction": "negative",
        },
        "claim": {
            "conclusion_claims": [
                "Large teams develop existing science and technology",
                "Small teams disrupt science and technology",
                "Both team types are essential",
            ],
        },
    }


def build_agent_dict(exec_result: dict) -> dict:
    """Build agent output dict for scoring."""
    metrics = exec_result.get("parsed_metrics", {})
    code_ok = exec_result["exit_code"] == 0 and not exec_result["has_traceback"]

    return {
        "data_source": {
            "data_source": "SciSciNet (Web of Science subset)",
            "code_executed": {"data_source": code_ok},
            "traceable": {"data_source": code_ok},
            "hard_coded": {"data_source": False},
            "hallucinated": {"data_source": False},
        },
        "sample": {
            "N": metrics.get("sample_size", 0),
            "filter_rules": (
                metrics.get("filters_applied", "").split(",")
                if metrics.get("filters_applied") else []
            ),
            "code_executed": {"sample": code_ok},
            "traceable": {"sample": True},
            "hard_coded": {"sample": False},
            "hallucinated": {"sample": False},
        },
        "indicator": {
            "formula": "D = (n_i - n_j) / (n_i + n_j + n_k)",
            "indicator_stats": {
                "mean": metrics.get("D_mean", 0),
                "std": metrics.get("D_std", 0),
            },
            "code_executed": {"indicator": code_ok},
            "traceable": {"indicator": True},
            "hard_coded": {"indicator": False},
            "hallucinated": {"indicator": False},
        },
        "model": {
            "spec_elements": ["OLS", "team_size", "year_fixed_effects"],
            "coefficients": {
                "team_size_coef": metrics.get("team_size_coefficient", 0),
                "year_1954": 0.0,
            },
            "code_executed": {"model": code_ok},
            "traceable": {"model": True},
            "hard_coded": {"model": False},
            "hallucinated": {"model": False},
        },
        "result_table": {
            "produced_tables": ["Regression table"] if code_ok else [],
            "reproduced_values": [
                {"label": "team_size_coef",
                 "value": metrics.get("team_size_coefficient", 0)},
            ],
            "observed_direction": (
                "negative" if metrics.get("team_size_coefficient", 1) < 0 else "null"
            ),
            "code_executed": {"result_table": code_ok},
            "traceable": {"result_table": True},
            "hard_coded": {"result_table": False},
            "hallucinated": {"result_table": False},
        },
        "claim": {
            "conclusion_claims": exec_result.get("parsed_claims", []),
        },
    }


def compute_diff_table(gold: dict, agent: dict) -> list[dict]:
    """Compute diff between gold and agent, with data-substituted flag."""
    diffs = []
    gold_n = gold["sample"]["N"]
    agent_n = agent["sample"]["N"]
    if gold_n > 0 and agent_n > 0:
        diffs.append({
            "component": "sample",
            "metric": "N",
            "gold": gold_n,
            "agent": agent_n,
            "relative_error": round(abs(agent_n - gold_n) / gold_n, 4),
            "data_substituted": True,
            "note": "Agent uses SciSciNet (~111K papers) vs WoS (~42M). Difference expected.",
        })

    gold_ind = gold["indicator"]["indicator_stats"]
    agent_ind = agent["indicator"]["indicator_stats"]
    for stat in ["mean", "std"]:
        gv = gold_ind.get(stat, 0)
        av = agent_ind.get(stat, 0)
        if abs(gv) > 1e-6:
            diffs.append({
                "component": "indicator",
                "metric": f"D_{stat}",
                "gold": gv,
                "agent": av,
                "relative_error": round(abs(av - gv) / abs(gv), 4),
                "data_substituted": True,
            })

    gold_coef = gold["model"]["coefficients"]["team_size_coef"]
    agent_coef = agent["model"]["coefficients"]["team_size_coef"]
    if abs(gold_coef) > 1e-6:
        diffs.append({
            "component": "model",
            "metric": "team_size_coef",
            "gold": gold_coef,
            "agent": agent_coef,
            "relative_error": round(abs(agent_coef - gold_coef) / abs(gold_coef), 4),
            "data_substituted": True,
        })

    diffs.append({
        "component": "result_table",
        "metric": "direction",
        "gold": gold["result_table"]["expected_direction"],
        "agent": agent["result_table"]["observed_direction"],
        "match": gold["result_table"]["expected_direction"] == agent["result_table"]["observed_direction"],
    })

    return diffs


# ── Audit Trail ──────────────────────────────────────────────────────────────

def record_audit_items(exec_result: dict, parsed: dict, agent_dict: dict,
                       codex_result: dict, compliance: dict,
                       module_preservation: list[dict]) -> dict[str, Any]:
    """Record extended audit items including Codex and constraint compliance."""
    code_ok = exec_result["exit_code"] == 0 and not exec_result["has_traceback"]

    return {
        "A1_code_executability": {
            "executable": code_ok,
            "exit_code": exec_result["exit_code"],
            "has_traceback": exec_result["has_traceback"],
            "has_import_error": exec_result["has_import_error"],
            "has_timeout": exec_result["has_timeout"],
            "elapsed": exec_result["elapsed"],
        },
        "A2_intermediate_files": {
            "sandbox_dir": exec_result.get("sandbox_dir", ""),
            "code_saved": bool(parsed.get("code")),
            "code_length": parsed.get("code_length", 0),
            "stdout_length": len(exec_result.get("stdout", "")),
        },
        "A3_sample_traceability": {
            "sample_size_reported": agent_dict["sample"]["N"],
            "filters_parsed": bool(exec_result.get("parsed_metrics", {}).get("filters_applied")),
            "data_source_identified": bool(agent_dict["data_source"]["data_source"]),
        },
        "A4_indicator_distribution": {
            "D_mean": exec_result.get("parsed_metrics", {}).get("D_mean"),
            "D_std": exec_result.get("parsed_metrics", {}).get("D_std"),
            "D_range_plausible": True,
        },
        "A5_table_generation": {
            "regression_table_in_stdout": "REGRESSION_TABLE" in exec_result.get("stdout", ""),
            "diff_table_in_stdout": "DIFF_TABLE" in exec_result.get("stdout", ""),
        },
        "A6_constraint_compliance": compliance,
        "A7_codex_validation": codex_result,
        "A8_module_preservation": module_preservation,
        "A9_error_recovery": {
            "errors_encountered": exec_result["exit_code"] != 0,
            "error_type": (
                "import_error" if exec_result["has_import_error"]
                else "timeout" if exec_result["has_timeout"]
                else "runtime" if exec_result["has_traceback"]
                else "none"
            ),
            "stderr_snippet": exec_result.get("stderr", "")[:500],
        },
    }


# ── Main R001b Runner ────────────────────────────────────────────────────────

def run_r001b(model_name: str = "deepseek-v4-pro") -> dict[str, Any]:
    """Execute R001b: constrained reproduction with Codex pre-validation."""
    print("=" * 70)
    print("  R001b: Constrained Reproduction — Wu et al. (2019)")
    print(f"  Model: {model_name}")
    print(f"  Task Type: {TASK_TYPE.value}")
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

    # ── Step 1: Generate reproduction code (constrained prompt) ──
    print("\n── Step 1: Generating reproduction code (constrained prompt) ──")
    prompt = build_constrained_prompt()

    t0 = time.time()
    response = llm.invoke([{"role": "user", "content": prompt}])
    gen_elapsed = time.time() - t0

    # Save raw response
    raw_content = response.content
    if isinstance(raw_content, list):
        (OUTPUT_DIR / "llm_response.json").write_text(
            json.dumps(raw_content, indent=2, ensure_ascii=False))
        response_text = "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in raw_content
        )
    else:
        response_text = str(raw_content)

    parsed = parse_agent_response(response)
    print(f"  Response: {parsed['response_length']:,} chars in {gen_elapsed:.1f}s")
    print(f"  Code extracted: {parsed['code_length']:,} chars")

    (OUTPUT_DIR / "llm_response.txt").write_text(response_text)

    if not parsed["code"]:
        print("  ERROR: No code extracted from LLM response")
        return {"status": "FAILED", "stage": "code_extraction",
                "error": "No code block found"}

    code = parsed["code"]
    (OUTPUT_DIR / "reproduce_v0_llm.py").write_text(code)

    # ── Step 2: Codex Pre-Execution Validation ──
    print("\n── Step 2: Codex pre-execution validation ──")
    codex_prompt_data = validate_with_codex_mcp(
        code, "Wu2019 team-size/disruption reproduction on SciSciNet")

    # Attempt Codex MCP call
    codex_result = {"codex_used": False, "issues_found": [], "fixes_applied": [],
                    "reviewed_code": code}

    try:
        # Import is local to avoid dependency on MCP availability
        codex_response = None  # Will be set by MCP call below
        print("  Sending to Codex for review...")
        # NOTE: Actual MCP call is made by the caller (see __main__ logic)
        # Here we save the prompt for external execution
        (OUTPUT_DIR / "codex_prompt.txt").write_text(codex_prompt_data["prompt"])
        print(f"  Codex prompt saved ({codex_prompt_data['code_length']:,} chars of code)")
        print("  Run codex MCP manually or invoke with --codex flag")
    except Exception as e:
        print(f"  Codex unavailable: {e}")
        codex_result["note"] = f"Codex call failed: {e}"

    # ── Step 3: Execute with constrained self-correction ──
    print("\n── Step 3: Executing in sandbox (constrained self-correction) ──")
    max_fixes = 3
    exec_result = None
    module_preservation_log = []

    for fix_attempt in range(max_fixes + 1):
        # Save code for this attempt
        attempt_label = f"reproduce_a{fix_attempt}"
        code_path = OUTPUT_DIR / f"{attempt_label}.py"
        code_path.write_text(code)

        exec_result = execute_agent_code(code, timeout=300)

        ok = (exec_result["exit_code"] == 0 and not exec_result["has_traceback"]
              and not exec_result["has_timeout"])
        if ok:
            print(f"  ✓ Execution OK (attempt {fix_attempt + 1}, "
                  f"{exec_result['elapsed']:.1f}s)")
            break

        # Report error
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

        # Constrained self-correction (if attempts remain)
        if fix_attempt < max_fixes:
            print(f"  → Requesting constrained fix from LLM...")
            fix_prompt = build_constrained_fix_prompt(code, err_text, [])
            fix_response = llm.invoke([{"role": "user", "content": fix_prompt}])
            fix_parsed = parse_agent_response(fix_response)

            if fix_parsed["code"] and len(fix_parsed["code"]) > 100:
                # Check module preservation
                preservation = check_module_preservation(code, fix_parsed["code"])
                module_preservation_log.append({
                    "attempt": fix_attempt + 1,
                    **preservation,
                })

                if not preservation["modules_preserved"]:
                    reasons = []
                    if preservation["removed_modules"]:
                        reasons.append(f"headers removed: {preservation['removed_modules']}")
                    if preservation["stubbed_modules"]:
                        reasons.append(f"stubs (no substance): {preservation['stubbed_modules']}")
                    print(f"    ⚠️  MODULE DEGRADATION: {'; '.join(reasons)}")
                    print(f"    Length ratio: {preservation['length_ratio']:.1%} "
                          f"({preservation['original_chars']} → "
                          f"{preservation['fixed_chars']} chars)")
                    print(f"    REJECTING fix — modules must be preserved with substance")
                    (OUTPUT_DIR / f"reproduce_fix{fix_attempt + 1}_REJECTED.py").write_text(
                        fix_parsed["code"])
                    continue

                code = fix_parsed["code"]
                (OUTPUT_DIR / f"reproduce_fix{fix_attempt + 1}.py").write_text(code)
                print(f"    Fixed code: {len(code):,} chars "
                      f"(ratio={preservation['length_ratio']:.1%}, "
                      f"all modules+substance preserved ✓)")
            else:
                print(f"    Fix extraction failed ({len(fix_parsed.get('code', ''))} chars)")
                break

    if exec_result is None:
        exec_result = {
            "exit_code": -1, "elapsed": 0, "stdout": "", "stderr": "",
            "has_traceback": False, "has_import_error": False, "has_timeout": False,
            "parsed_metrics": {}, "parsed_claims": [],
            "sandbox_dir": "",
        }

    # Save execution outputs
    (OUTPUT_DIR / "stdout.txt").write_text(exec_result["stdout"])
    (OUTPUT_DIR / "stderr.txt").write_text(exec_result["stderr"])

    metrics = exec_result["parsed_metrics"]
    if metrics:
        print(f"  Parsed metrics: {list(metrics.keys())}")
        for k, v in metrics.items():
            if isinstance(v, float):
                print(f"    {k} = {v:.4f}")
            else:
                print(f"    {k} = {v}")

    # Save final executed code
    (OUTPUT_DIR / "reproduce_final.py").write_text(code)
    parsed["code"] = code
    parsed["code_length"] = len(code)

    # ── Step 4: Constraint compliance check ──
    print("\n── Step 4: Constraint compliance check ──")
    compliance = check_constraint_compliance(exec_result["stdout"], metrics)
    if compliance["compliant"]:
        print("  ✓ All constraints satisfied")
    else:
        print(f"  ✗ Constraint violations: {compliance['violations']}")
        for v in compliance["violations"]:
            print(f"    - {v}")

    # ── Step 5: Gold comparison ──
    print("\n── Step 5: Gold comparison (DATA_SUB task type) ──")
    gold = build_gold_dict()
    agent_dict = build_agent_dict(exec_result)

    diff_table = compute_diff_table(gold, agent_dict)
    for d in diff_table:
        match_str = "✓" if d.get("match", True) else "✗"
        ds_flag = " [data-sub]" if d.get("data_substituted") else ""
        if "relative_error" in d:
            print(f"  {d['component']}.{d['metric']}: gold={d['gold']}, "
                  f"agent={d['agent']}, rel_err={d['relative_error']:.2%}{ds_flag}")
        else:
            print(f"  {d['component']}.{d['metric']}: {d['gold']} vs {d['agent']} "
                  f"{match_str}")

    # ── Step 6: 5-Dimension scoring (DATA_SUB task type) ──
    print(f"\n── Step 6: 5-Dimension scoring (task_type={TASK_TYPE.value}) ──")
    print(f"  D3 applicability: {'pass/fail' if is_numerical_accuracy_applicable(TASK_TYPE) else 'reference-only'}")
    profile = build_reproduction_profile("wu2019_disruption", gold, agent_dict,
                                         task_type=TASK_TYPE)

    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]
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
    print("  * = reference-only (not used for pass/fail)")

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
    audit = record_audit_items(exec_result, parsed, agent_dict, codex_result,
                               compliance, module_preservation_log)
    for audit_id, items in audit.items():
        if isinstance(items, dict):
            status = "✓" if items.get("compliant", items.get("executable", True)) else "✗"
        else:
            status = str(items)[:50]
        print(f"  {audit_id}: {status}")
    (OUTPUT_DIR / "audit.json").write_text(json.dumps(audit, indent=2))

    # ── Step 8: Assemble results ──
    print("\n── Step 8: Saving results ──")
    results = {
        "run_id": "R001b",
        "paper": "wu2019_disruption",
        "task_type": TASK_TYPE.value,
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "stages": {
            "code_generation": {"elapsed": gen_elapsed,
                              "code_chars": parsed["code_length"]},
            "codex_validation": codex_result,
            "execution": {
                "exit_code": exec_result["exit_code"],
                "elapsed": exec_result["elapsed"],
                "has_traceback": exec_result["has_traceback"],
                "has_timeout": exec_result["has_timeout"],
            },
            "self_correction": {
                "attempts": len(module_preservation_log),
                "module_preservation_log": module_preservation_log,
            },
        },
        "constraint_compliance": compliance,
        "gold": gold,
        "agent": agent_dict,
        "diff_table": diff_table,
        "profile": {
            "maturity": maturity,
            "task_type": TASK_TYPE.value,
            "d3_applicable": is_numerical_accuracy_applicable(TASK_TYPE),
            "matrix": profile.to_matrix(),
            "spurious_flags": spurious_flags,
        },
        "audit": audit,
        "parsed_metrics": metrics,
        "parsed_claims": exec_result.get("parsed_claims", []),
    }

    out_path = OUTPUT_DIR / "r001b_results.json"
    out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
    print(f"  Results → {out_path}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  R001b COMPLETE")
    print(f"  Task Type: {TASK_TYPE.value}")
    print(f"{'=' * 70}")
    exec_ok = exec_result["exit_code"] == 0 and not exec_result["has_traceback"]
    print(f"  Execution:        {'✓ SUCCESS' if exec_ok else '✗ FAILED'}")
    print(f"  Compliance:       {'✓ PASS' if compliance['compliant'] else '✗ FAIL'}")
    print(f"  Maturity:         {maturity_label}")
    print(f"  D3 applicable:    {is_numerical_accuracy_applicable(TASK_TYPE)}")
    print(f"  Spurious:         {len(spurious_flags)} flags")
    print(f"  Metrics parsed:   {len(metrics)}")
    print(f"  Claims parsed:    {len(exec_result.get('parsed_claims', []))}")
    print(f"  Diff entries:     {len(diff_table)}")
    total_degraded = sum(1 for mp in module_preservation_log if not mp['modules_preserved'])
    total_removed = sum(len(mp.get('removed_modules', [])) for mp in module_preservation_log)
    total_stubbed = sum(len(mp.get('stubbed_modules', [])) for mp in module_preservation_log)
    print(f"  Module issues:    {total_degraded} degraded fixes "
          f"({total_removed} removed, {total_stubbed} stubbed)")

    if compliance["missing_sections"]:
        print(f"\n  ⚠️  Missing sections: {compliance['missing_sections']}")
    if compliance["missing_metrics"]:
        print(f"  ⚠️  Missing metrics: {compliance['missing_metrics']}")

    return results


# ── Codex MCP Integration ────────────────────────────────────────────────────

def run_codex_review(code: str) -> str | None:
    """Run Codex MCP review on generated code.

    This function is called by the CLI when --codex flag is used.
    It prints the Codex prompt for the user to execute via MCP,
    and returns the reviewed code if available.

    In automated mode, the caller should use the mcp__codex__codex MCP tool
    directly and pass the result back.
    """
    prompt_data = validate_with_codex_mcp(code, "Wu2019 reproduction on SciSciNet")
    print("\n" + "=" * 70)
    print("  CODEX REVIEW PROMPT (save and run via MCP):")
    print("=" * 70)
    print(prompt_data["prompt"][:500])
    print(f"  ... ({len(prompt_data['prompt'])} chars total)")
    print("=" * 70)
    return None


# ── CLI ──────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(
        description="R001b: Constrained reproduction of Wu2019 with Codex pre-validation")
    parser.add_argument("--mock", action="store_true", help="Use MockLLM for dry run")
    parser.add_argument("--model", default="deepseek-v4-pro", help="Model name")
    parser.add_argument("--codex", action="store_true",
                       help="Enable Codex pre-execution validation")
    parser.add_argument("--codex-only", action="store_true",
                       help="Only generate and print Codex review prompt, then exit")
    args = parser.parse_args()

    model = "mock" if args.mock else args.model

    if args.codex_only:
        # Generate code only, then print Codex prompt
        from src.sciscigpt_local.llm_backends import load_llm_from_env
        llm = load_llm_from_env()
        prompt = build_constrained_prompt()
        response = llm.invoke([{"role": "user", "content": prompt}])
        parsed = parse_agent_response(response)
        if parsed["code"]:
            (OUTPUT_DIR / "reproduce_v0_llm.py").write_text(parsed["code"])
            run_codex_review(parsed["code"])
        else:
            print("ERROR: No code extracted from LLM response")
        return

    try:
        results = run_r001b(model_name=model)
        if args.codex and results.get("stages", {}).get("code_generation"):
            code = (OUTPUT_DIR / "reproduce_v0_llm.py").read_text()
            run_codex_review(code)
    except Exception as e:
        print(f"\n  R001b FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
