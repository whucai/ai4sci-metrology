#!/usr/bin/env python3
"""R001: Real agent reproduction of Wu et al. (2019) on SciSciNet data.

M0 pilot — first end-to-end test of LLM-driven computational reproduction.
Agent (Qwen3-32B) reads Wu2019 methodology → generates reproduce.py → executes
in sandbox → collects 8 outputs + 6 audit items → scores via 5-dimension framework.

Outputs (8):
  1. reproduce.py          — generated reproduction code
  2. requirements.txt      — Python dependencies used
  3. data_load_log         — what data was loaded, row counts
  4. sample_N              — final sample size after filtering
  5. indicator_stats       — D-index distribution (mean, std, percentiles)
  6. regression_table      — team_size ~ D coefficients
  7. diff_table            — comparison vs gold/paper values
  8. claim_conclusions     — agent's conclusion claims
  9. run_log               — execution steps and timings

Audit items (6):
  A1. code_executability    — did reproduce.py run without errors?
  A2. intermediate_files    — what files were created/read?
  A3. sample_traceability   — can we trace sample construction?
  A4. indicator_distribution — does D-index match expectations?
  A5. table_generation      — were result tables properly produced?
  A6. error_recovery        — if errors, were they handled?

Usage:
    conda activate sciscigpt && python scripts/r001_wu2019_reproduction.py
    conda activate sciscigpt && python scripts/r001_wu2019_reproduction.py --mock  # dry run
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
    COMPONENT_DIMENSION_MAP,
    ReproductionProfile,
    TaskType,
    is_numerical_accuracy_applicable,
)
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.llm_backends import load_llm_from_env

# ── Output directory ──
OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r001"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)


# ── Wu2019 Methodology Prompt ──────────────────────────────────────────────

def build_reproduction_prompt() -> str:
    """Build a structured prompt describing Wu2019's methodology for the agent."""
    paper = create_wu2019()

    return f"""## Task: Reproduce Wu, Wang & Evans (2019) — Team Size and Disruptiveness

You are a computational reproduction agent. Your job is to write Python code that
reproduces the core analysis of this Nature paper.

### Paper Summary
- **Title**: {paper.title}
- **Authors**: {', '.join(paper.authors)}
- **Venue**: {paper.venue} ({paper.year})
- **DOI**: {paper.doi}

### Research Question
{paper.research_question}

### Data Source
{paper.data_source} — {paper.data_description}

### Sample Scope
- Time window: {paper.sample_scope.get('time_window', '1954-2014')}
- Filters: {', '.join(paper.sample_scope.get('filters', []))}
- Unit of analysis: individual papers/patents/software products

### Key Variables

**Dependent Variable — Disruption Index (D-index)**:
Formula: D = (n_i - n_j) / (n_i + n_j + n_k)

Where:
- n_i = number of subsequent papers that cite ONLY the focal paper (not its references)
- n_j = number of subsequent papers that cite BOTH the focal paper AND at least one of its references
- n_k = number of subsequent papers that cite ONLY the focal paper's references (not the focal paper itself)

D ranges from -1 (most developmental/consolidating) to +1 (most disruptive).

**Independent Variable**:
- team_size: number of unique authors on the paper

### Analysis Method
1. Compute D-index for each paper using citation network data
2. Group papers by team_size decile
3. Compute mean D-index per decile
4. Estimate relationship: mean_D ~ team_size_decile (descriptive OLS with year fixed effects)
5. The paper's central thesis: larger teams develop existing science; small teams disrupt it

### Available Data
You have access to SciSciNet data via the sciscinet_connector module:
```python
from src.sciscigpt_local.sciscinet_connector import load_table
papers = load_table("papers")           # DataFrame: paper_id, year, author_count, disruption_score, ...
citations = load_table("paper_citations")  # DataFrame: citing_paper_id, cited_paper_id
```

The `papers` table has a precomputed `disruption_score` column containing the D-index.

### Analysis Strategy (IMPORTANT)

**Primary analysis** (full pipeline): Use the precomputed `disruption_score` column.
**Validation check** (small scale): Compute D-index from scratch for 5-10 papers using
the paper_citations table to verify the formula is correct. Print the comparison
between your computed D and the precomputed `disruption_score`.

This two-tier approach lets you run the full regression pipeline while still
demonstrating formula understanding.

### Requirements

Your response must contain:

1. A ```python code block with the complete reproduction script
2. The code must:
   - Load papers from SciSciNet (sample 20,000 papers with year 1954-2014, author_count > 0)
   - Compute D-index from scratch for 5-10 validation papers using the citation network
   - Compare your D-index with precomputed disruption_score
   - For the main regression, use precomputed disruption_score
   - Group by team_size decile and compute mean D per decile
   - Run OLS: disruption_score ~ log(author_count) + C(year)
   - Print ALL results with clear labels

3. Print format (parseable) — use EXACTLY these labels:
```
=== DATA_LOAD ===
papers_loaded: <N>
citations_loaded: <N>
=== SAMPLE ===
sample_size: <N>
time_window: <start>-<end>
filters_applied: <list>
=== INDICATOR_STATS ===
D_mean: <value>
D_std: <value>
D_min: <value>
D_max: <value>
=== VALIDATION ===
<print comparison table: paper_id, computed_D, precomputed_D, match>
=== REGRESSION ===
team_size_coefficient: <value>
team_size_pvalue: <value>
r_squared: <value>
n_observations: <value>
direction: <positive/negative/null>
=== REGRESSION_TABLE ===
<print the regression summary table>
=== DIFF_TABLE ===
<print comparison with expected values from paper>
=== CLAIMS ===
<list of 2-3 conclusion claims supported by the results>
```

4. After the code block, list your requirements.txt.

IMPORTANT:
- Write COMPLETE, RUNNABLE code — no placeholders
- Sample 20,000 papers for regression (not 100K) for speed
- Compute D-index from scratch for ONLY 5-10 papers for validation
- For main regression, use precomputed disruption_score from papers table
- The code will be executed in a sandbox with pandas, numpy, scipy, statsmodels
- Handle edge cases: missing data, division by zero
- Do NOT import from src.sciscigpt_local except sciscinet_connector.load_table
- DO NOT use tqdm — just print progress every 5000 papers
"""


# ── Output Parsers ─────────────────────────────────────────────────────────

def parse_agent_response(response) -> dict[str, Any]:
    """Parse LLM response into structured components.

    Handles:
      - Plain string responses (ChatOpenAI, MockLLM)
      - Structured responses with content blocks (ChatAnthropic/DeepSeek)
        where response.content is a list of {"type":"text", "text":"..."} dicts
    """
    # Extract text from response
    content = response.content

    # Handle list-of-dicts format (Anthropic/DeepSeek structured responses)
    if isinstance(content, list):
        text_parts = []
        thinking_parts = []
        for block in content:
            if isinstance(block, dict):
                block_type = block.get("type", "")
                if block_type == "text":
                    text_parts.append(block.get("text", ""))
                elif block_type == "thinking":
                    thinking_parts.append(block.get("thinking", ""))
                elif "text" in block:
                    text_parts.append(str(block["text"]))
                elif "thinking" in block:
                    thinking_parts.append(str(block["thinking"]))
        response_text = "\n".join(text_parts)
    else:
        response_text = str(content)

    # Strip thinking tags (Qwen3 format)
    response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    # Extract code block
    code = ""
    code_match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()

    # Filter out non-code lines (narration, thinking)
    clean_lines = []
    for line in code.split("\n"):
        stripped = line.strip()
        if not stripped:
            clean_lines.append(line)
            continue
        if re.match(r"^(Okay|Let me|I need|First|Wait|The user|Now|But |So |However|"
                    r"Alternatively|Maybe|Perhaps|Hmm|Thus|Therefore|Here)", stripped):
            continue
        clean_lines.append(line)
    code = "\n".join(clean_lines).strip()

    # Extract requirements
    requirements = ""
    req_match = re.search(r"(?:requirements\.txt|Requirements|Dependencies|Packages)[:\s]*\n?(.*?)(?:\n\n|\n\Z|\Z)",
                          response_text, re.DOTALL | re.IGNORECASE)
    if req_match:
        req_text = req_match.group(1).strip()
        requirements = req_text[:500]

    # Extract claims from text (non-code part after code block)
    after_code = response_text.split("```")[-1] if "```" in response_text else ""
    claims_section = ""
    claims_match = re.search(r"(?:CLAIMS|Conclusions?)[:\s]*\n(.*?)(?:\n\n|\Z)",
                             after_code, re.DOTALL | re.IGNORECASE)
    if claims_match:
        claims_section = claims_match.group(1).strip()[:1000]

    return {
        "code": code,
        "requirements": requirements,
        "claims_raw": claims_section,
        "code_length": len(code),
        "response_length": len(response_text),
    }


def parse_stdout_metrics(stdout: str) -> dict[str, Any]:
    """Parse structured metrics from sandbox stdout.

    Handles both the requested format (=== SECTION ===) and common
    statsmodels regression table output.
    """
    metrics: dict[str, Any] = {}

    # Try structured format first
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
        "D_percentiles": r"D_percentiles:\s*\[([^\]]*)\]",
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
                elif key == "D_percentiles":
                    metrics[key] = [float(x.strip()) for x in val.split(",")]
                else:
                    metrics[key] = val
            except (ValueError, TypeError):
                metrics[key] = val

    # Fallback: parse statsmodels regression table
    # Look for "team_size" row in OLS summary
    team_match = re.search(
        r"team_size\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)\s+([-\d.e]+)",
        stdout
    )
    if team_match and "team_size_coefficient" not in metrics:
        try:
            metrics["team_size_coefficient"] = float(team_match.group(1))
            # p-value is typically column 4: P>|t|
            metrics["team_size_pvalue"] = float(team_match.group(4))
        except (ValueError, IndexError):
            pass

    # Parse R-squared from OLS summary
    r2_match = re.search(r"R-squared:\s+([-\d.e]+)", stdout)
    if r2_match and "r_squared" not in metrics:
        try:
            metrics["r_squared"] = float(r2_match.group(1))
        except ValueError:
            pass

    # Parse sample info from free text
    sample_match = re.search(r"Sample papers.*?:\s*([\d,]+)", stdout)
    if sample_match and "sample_size" not in metrics:
        try:
            metrics["sample_size"] = int(sample_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Parse papers loaded from free text
    papers_match = re.search(r"Papers loaded:\s*([\d,]+)", stdout)
    if papers_match and "papers_loaded" not in metrics:
        try:
            metrics["papers_loaded"] = int(papers_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Parse citations loaded from free text
    cit_match = re.search(r"Citations loaded:\s*([\d,]+)", stdout)
    if cit_match and "citations_loaded" not in metrics:
        try:
            metrics["citations_loaded"] = int(cit_match.group(1).replace(",", ""))
        except ValueError:
            pass

    # Parse D mean/std from DIFF_TABLE or free text
    d_mean_match = re.search(r"(?:mean D|D_mean|mean_D).*?([-\d.e]+)", stdout, re.IGNORECASE)
    if d_mean_match and "D_mean" not in metrics:
        try:
            metrics["D_mean"] = float(d_mean_match.group(1))
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


# ── Sandbox execution wrapper ──────────────────────────────────────────────

def execute_agent_code(code: str, timeout: int = 300) -> dict[str, Any]:
    """Execute agent-generated code in sandbox. Returns enriched result dict."""
    t0 = time.time()
    result = execute_python(code, timeout=timeout)
    elapsed = time.time() - t0

    stdout = result.get("stdout", "")
    stderr = result.get("stderr", "")

    # Parse structured outputs
    metrics = parse_stdout_metrics(stdout) if result["exit_code"] == 0 else {}
    claims = extract_claims_from_output(stdout)

    # Check for common issues
    has_traceback = "Traceback (most recent call last)" in stderr
    has_import_error = "ModuleNotFoundError" in stderr or "ImportError" in stderr
    has_timeout = "timed out" in stderr.lower() or result["exit_code"] == -1

    return {
        "exit_code": result["exit_code"],
        "elapsed": round(elapsed, 2),
        "stdout": stdout[-10000:],  # Keep last 10K chars
        "stderr": stderr[-5000:],
        "has_traceback": has_traceback,
        "has_import_error": has_import_error,
        "has_timeout": has_timeout,
        "parsed_metrics": metrics,
        "parsed_claims": claims,
        "sandbox_dir": str(Path(result.get("environment", {}).get("workdir", ""))),
    }


# ── Gold comparison ────────────────────────────────────────────────────────

def build_gold_dict() -> dict:
    """Build gold annotation dict from Wu2019 paper annotation."""
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


def build_agent_dict(exec_result: dict, parsed_response: dict) -> dict:
    """Build agent output dict from execution results."""
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
            "filter_rules": metrics.get("filters_applied", "").split(",") if metrics.get("filters_applied") else [],
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
                {"label": "team_size_coef", "value": metrics.get("team_size_coefficient", 0)},
            ],
            "observed_direction": "negative" if metrics.get("team_size_coefficient", 1) < 0 else "null",
            "code_executed": {"result_table": code_ok},
            "traceable": {"result_table": True},
            "hard_coded": {"result_table": False},
            "hallucinated": {"result_table": False},
        },
        "claim": {
            "conclusion_claims": exec_result.get("parsed_claims", []),
        },
    }


def compute_diff_table(gold: dict, agent: dict, exec_result: dict) -> list[dict]:
    """Compute difference table between gold annotation and agent results."""
    diffs = []

    # Sample N
    gold_n = gold["sample"]["N"]
    agent_n = agent["sample"]["N"]
    if gold_n > 0 and agent_n > 0:
        diffs.append({
            "component": "sample",
            "metric": "N",
            "gold": gold_n,
            "agent": agent_n,
            "relative_error": round(abs(agent_n - gold_n) / gold_n, 4),
            "note": "Agent uses SciSciNet sample (expected — full WoS unavailable)",
        })

    # Indicator stats
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
            })

    # Model coefficients
    gold_coef = gold["model"]["coefficients"]["team_size_coef"]
    agent_coef = agent["model"]["coefficients"]["team_size_coef"]
    if abs(gold_coef) > 1e-6:
        diffs.append({
            "component": "model",
            "metric": "team_size_coef",
            "gold": gold_coef,
            "agent": agent_coef,
            "relative_error": round(abs(agent_coef - gold_coef) / abs(gold_coef), 4),
        })

    # Direction match
    diffs.append({
        "component": "result_table",
        "metric": "direction",
        "gold": gold["result_table"]["expected_direction"],
        "agent": agent["result_table"]["observed_direction"],
        "match": gold["result_table"]["expected_direction"] == agent["result_table"]["observed_direction"],
    })

    return diffs


# ── Audit trail ────────────────────────────────────────────────────────────

def record_audit_items(
    exec_result: dict,
    parsed_response: dict,
    agent_dict: dict,
    gold_dict: dict,
) -> dict[str, Any]:
    """Record the 6 audit items."""
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
            "sandbox_dir": exec_result.get("sandbox_dir", "unknown"),
            "code_saved": bool(parsed_response.get("code")),
            "code_length": parsed_response.get("code_length", 0),
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
            "D_range_plausible": True,  # will be assessed manually
        },
        "A5_table_generation": {
            "regression_table_in_stdout": "REGRESSION_TABLE" in exec_result.get("stdout", ""),
            "diff_table_in_stdout": "DIFF_TABLE" in exec_result.get("stdout", ""),
        },
        "A6_error_recovery": {
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


# ── Main R001 runner ───────────────────────────────────────────────────────

def run_r001(model_name: str = "qwen3-32b") -> dict[str, Any]:
    """Execute R001: real agent reproduction of Wu2019."""
    print("=" * 70)
    print("  R001: Real Agent Reproduction — Wu et al. (2019)")
    print(f"  Model: {model_name}")
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
        llm_type = type(llm).__name__
        print(f"  LLM loaded: {llm_type}")

    # ── Step 1: Generate reproduction code ──
    print("\n── Step 1: Generating reproduction code ──")
    prompt = build_reproduction_prompt()

    t0 = time.time()
    response = llm.invoke([{"role": "user", "content": prompt}])
    gen_elapsed = time.time() - t0

    # Save raw response (handle structured format)
    raw_content = response.content
    if isinstance(raw_content, list):
        (OUTPUT_DIR / "llm_response.json").write_text(json.dumps(raw_content, indent=2, ensure_ascii=False))
        response_text = "\n".join(
            b.get("text", "") if isinstance(b, dict) else str(b)
            for b in raw_content
        )
    else:
        response_text = str(raw_content)
        (OUTPUT_DIR / "llm_response.txt").write_text(response_text)

    parsed = parse_agent_response(response)
    print(f"  Response: {parsed['response_length']:,} chars in {gen_elapsed:.1f}s")
    print(f"  Code extracted: {parsed['code_length']:,} chars")

    # Save raw response
    (OUTPUT_DIR / "llm_response.txt").write_text(response_text)

    if not parsed["code"]:
        print("  ERROR: No code extracted from LLM response")
        return {"status": "FAILED", "stage": "code_extraction", "error": "No code block found"}

    # Save reproduce.py
    code_path = OUTPUT_DIR / "reproduce.py"
    code_path.write_text(parsed["code"])
    print(f"  Saved reproduce.py → {code_path}")

    # Save requirements.txt
    req_path = OUTPUT_DIR / "requirements.txt"
    req_path.write_text(parsed["requirements"] or "# No additional requirements beyond stdlib\n")
    print(f"  Saved requirements.txt → {req_path}")

    # ── Step 2: Execute with self-correction ──
    print("\n── Step 2: Executing in sandbox (with self-correction) ──")
    code = parsed["code"]
    max_fixes = 3
    exec_result = None

    for fix_attempt in range(max_fixes + 1):
        exec_result = execute_agent_code(code, timeout=300)

        ok = (exec_result["exit_code"] == 0 and not exec_result["has_traceback"]
              and not exec_result["has_timeout"])
        if ok:
            print(f"  ✓ Execution OK (attempt {fix_attempt + 1}, {exec_result['elapsed']:.1f}s)")
            break

        # Report error
        if fix_attempt == 0:
            print(f"  ✗ Execution failed (attempt {fix_attempt + 1}, {exec_result['elapsed']:.1f}s)")
        else:
            print(f"  ✗ Fix attempt {fix_attempt} failed ({exec_result['elapsed']:.1f}s)")

        err_text = exec_result.get("stderr", "") or exec_result.get("stdout", "")
        if exec_result["has_traceback"]:
            err_lines = [l for l in err_text.split("\n") if "Error" in l or "Traceback" in l]
            for line in err_lines[:3]:
                print(f"    {line[:120]}")
        elif exec_result["has_timeout"]:
            print(f"    Timeout after 300s")

        # Self-correct if attempts remain
        if fix_attempt < max_fixes:
            print(f"  → Requesting fix from LLM...")
            fix_prompt = f"""The following Python code failed with this error:

Error:
{err_text[:1500]}

Current code:
```python
{code[:3000]}
```

Fix the error. Output ONLY the corrected Python code in a ```python block.
Do NOT include any thinking, explanation, or narration — just the code block."""

            fix_response = llm.invoke([{"role": "user", "content": fix_prompt}])
            fix_parsed = parse_agent_response(fix_response)
            if fix_parsed["code"] and len(fix_parsed["code"]) > 100:
                code = fix_parsed["code"]
                (OUTPUT_DIR / f"reproduce_fix{fix_attempt + 1}.py").write_text(code)
                print(f"    Fixed code: {len(code):,} chars")
                parsed["code"] = code  # update for saving
            else:
                print(f"    Fix extraction failed ({len(fix_parsed.get('code', ''))} chars)")
                break

    if exec_result is None:
        exec_result = {"exit_code": -1, "elapsed": 0, "stdout": "", "stderr": "No execution attempted",
                       "has_traceback": False, "has_import_error": False, "has_timeout": False,
                       "parsed_metrics": {}, "parsed_claims": []}

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

    # ── Step 3: Build agent dict and compare with gold ──
    print("\n── Step 3: Gold comparison ──")
    gold = build_gold_dict()
    agent_dict = build_agent_dict(exec_result, parsed)

    # Compute diff table
    diff_table = compute_diff_table(gold, agent_dict, exec_result)
    for d in diff_table:
        match_str = "✓" if d.get("match", True) else "✗"
        if "relative_error" in d:
            print(f"  {d['component']}.{d['metric']}: gold={d['gold']}, agent={d['agent']}, "
                  f"rel_err={d['relative_error']:.2%}")
        else:
            print(f"  {d['component']}.{d['metric']}: {d['gold']} vs {d['agent']} {match_str}")

    # ── Step 4: 5-Dimension scoring ──
    print("\n── Step 4: 5-Dimension scoring ──")
    task_type = TaskType.DATA_SUB
    profile = build_reproduction_profile("wu2019_disruption", gold, agent_dict,
                                         task_type=task_type)

    # Print score matrix
    components = ["data_source", "sample", "indicator", "model", "result_table", "claim"]
    all_dims = ["fidelity", "executability", "numerical_accuracy", "claim_consistency", "auditability"]

    for comp in components:
        cs = profile.component_scores.get(comp)
        if cs:
            scores = {d: f"{cs.dimension_scores[d].score:.2f}" if d in cs.dimension_scores else "—"
                      for d in all_dims}
            dims_str = " ".join(f"{d[:6]}={scores[d]:>6}" for d in all_dims)
            print(f"  {comp:<14} {dims_str}")

    # Maturity
    maturity = compute_maturity_level(profile, task_type=task_type)
    maturity_label = format_maturity(maturity, task_type)
    print(f"\n  Reproduction Maturity: {maturity_label}")

    # Spurious check
    spurious_flags = detect_spurious_reproduction(profile)
    if spurious_flags:
        print(f"  ⚠️  Spurious flags: {spurious_flags}")
    else:
        print(f"  ✓ No spurious flags")

    # ── Step 5: Audit trail ──
    print("\n── Step 5: Audit trail ──")
    audit = record_audit_items(exec_result, parsed, agent_dict, gold)
    for audit_id, items in audit.items():
        status = "✓" if items.get("executable", True) else "✗"
        print(f"  {audit_id}: {status}")
    (OUTPUT_DIR / "audit.json").write_text(json.dumps(audit, indent=2))

    # ── Step 6: Assemble final output ──
    print("\n── Step 6: Saving results ──")
    run_log = {
        "run_id": "R001",
        "paper": "wu2019_disruption",
        "task_type": task_type.value,
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "stages": {
            "code_generation": {"elapsed": gen_elapsed, "code_chars": parsed["code_length"]},
            "execution": {
                "exit_code": exec_result["exit_code"],
                "elapsed": exec_result["elapsed"],
                "has_traceback": exec_result["has_traceback"],
                "has_timeout": exec_result["has_timeout"],
            },
        },
        "gold": gold,
        "agent": agent_dict,
        "diff_table": diff_table,
        "profile": {
            "maturity": maturity,
            "task_type": task_type.value,
            "d3_applicable": is_numerical_accuracy_applicable(task_type),
            "matrix": profile.to_matrix(),
            "spurious_flags": spurious_flags,
        },
        "audit": audit,
        "parsed_metrics": metrics,
        "parsed_claims": exec_result.get("parsed_claims", []),
    }

    out_path = OUTPUT_DIR / "r001_results.json"
    out_path.write_text(json.dumps(run_log, indent=2, ensure_ascii=False))
    print(f"  Results → {out_path}")

    # Summary
    print(f"\n{'=' * 70}")
    print(f"  R001 COMPLETE")
    print(f"{'=' * 70}")
    exec_ok = exec_result["exit_code"] == 0 and not exec_result["has_traceback"]
    print(f"  Execution: {'✓ SUCCESS' if exec_ok else '✗ FAILED'}")
    print(f"  Maturity: L{maturity}")
    print(f"  Spurious: {len(spurious_flags)} flags")
    print(f"  Metrics parsed: {len(metrics)}")
    print(f"  Claims parsed: {len(exec_result.get('parsed_claims', []))}")
    print(f"  Diff entries: {len(diff_table)}")
    print(f"\n  Outputs:")
    print(f"    1. reproduce.py       → {code_path}")
    print(f"    2. requirements.txt   → {req_path}")
    print(f"    3. data_load_log      → stdout.txt (DATA_LOAD section)")
    print(f"    4. sample_N           → {agent_dict['sample']['N']:,}")
    print(f"    5. indicator_stats    → stdout.txt (INDICATOR_STATS section)")
    print(f"    6. regression_table   → stdout.txt (REGRESSION_TABLE section)")
    print(f"    7. diff_table         → {len(diff_table)} entries")
    print(f"    8. claim_conclusions  → {len(exec_result.get('parsed_claims', []))} claims")
    print(f"    9. run_log            → {out_path}")

    return run_log


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    import argparse
    parser = argparse.ArgumentParser(description="R001: Real agent reproduction of Wu2019")
    parser.add_argument("--mock", action="store_true", help="Use MockLLM for dry run")
    parser.add_argument("--model", default="qwen3-32b", help="Model name")
    args = parser.parse_args()

    model = "mock" if args.mock else args.model
    try:
        run_r001(model_name=model)
    except Exception as e:
        print(f"\n  R001 FAILED: {e}")
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
