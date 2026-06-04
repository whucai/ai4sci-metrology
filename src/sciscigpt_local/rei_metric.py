"""M3: Self-Correction Loop + Reproducibility Effort Index (REI).

Uses SciSciNet pre-computed disruption_score as ground truth to validate
the self-correction pipeline. The LLM generates code to compute D-index
from citation data; we compare the output against SciSciNet's known value.

REI = Σ(weighted fix iterations) / successful_steps
  - Syntax error: weight 1
  - Import/missing dep: weight 2
  - Runtime error: weight 3
  - Logic/calculation error: weight 5

Self-correction strategies (tried in order):
  1. Fix syntax/indentation
  2. Add missing imports
  3. Fix API call patterns
  4. Fix calculation logic
  5. Simplify approach entirely
"""

from __future__ import annotations

import json
import re
import time
import traceback
from typing import Any, Optional
from dataclasses import dataclass, field

import pandas as pd
import numpy as np
from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.sciscinet_connector import load_table


# ── Error classification ──

ERROR_PATTERNS = {
    "syntax": [
        "SyntaxError", "IndentationError", "TabError",
        "EOL while scanning", "EOF while scanning",
    ],
    "import": [
        "ModuleNotFoundError", "ImportError",
        "No module named", "cannot import",
    ],
    "runtime": [
        "TypeError", "ValueError", "KeyError", "IndexError",
        "AttributeError", "NameError", "ZeroDivisionError",
        "FileNotFoundError",
    ],
    "timeout": ["timed out", "TimeoutExpired", "timeout"],
    "logic": [
        "AssertionError", "ValueError: math domain",
        "invalid literal for", "could not convert",
    ],
}

ERROR_WEIGHTS = {"syntax": 1, "import": 2, "runtime": 3, "timeout": 5, "logic": 5}


def classify_error(stderr: str) -> str:
    """Classify error type from stderr output."""
    for category, patterns in ERROR_PATTERNS.items():
        for p in patterns:
            if p in stderr:
                return category
    return "unknown"


# ── Self-correction prompts ──

FIX_STRATEGIES = [
    {
        "name": "syntax",
        "prompt": """Fix syntax errors in the following Python code. Pay attention to:
- Unclosed strings, parentheses, brackets
- Indentation
- Missing colons
- Invalid escape sequences
Output ONLY the fixed code in a ```python block.""",
    },
    {
        "name": "import",
        "prompt": """The following Python code has import errors. Fix by:
- Using only standard library + pandas, numpy, scipy, json, requests
- Removing imports from non-existent packages
- If the code imports from custom packages, inline the needed logic using standard libraries
Output ONLY the fixed code in a ```python block.""",
    },
    {
        "name": "runtime",
        "prompt": """The following Python code has runtime errors. Fix by:
- Adding proper error handling (try/except)
- Checking for None/empty values before operations
- Converting types appropriately
- Handling edge cases (empty lists, missing keys)
Output ONLY the fixed code in a ```python block.""",
    },
    {
        "name": "logic",
        "prompt": """The following Python code produces wrong results. The calculation logic has errors.
Rewrite the code from scratch to:
- Use the correct formula/method
- Verify intermediate steps with print() statements
- Handle edge cases properly
Output ONLY the corrected code in a ```python block.""",
    },
    {
        "name": "simplify",
        "prompt": """The following Python code is too complex and keeps failing.
Rewrite it as a MINIMAL, SIMPLE version:
- Remove unnecessary abstractions
- Use the simplest possible approach
- Include print() for all results
- Use only: pandas, numpy, scipy, json, requests
Output ONLY the simple code in a ```python block.""",
    },
]


@dataclass
class REIResult:
    """Result of a single REI measurement."""
    paper_id: str
    ground_truth: float
    reproduced_value: Optional[float] = None
    status: str = "PENDING"  # SUCCESS, FAILED, TIMEOUT
    fix_iterations: int = 0
    error_types: list[str] = field(default_factory=list)
    weighted_errors: int = 0
    REI: float = 0.0
    elapsed_total: float = 0.0
    code_final: str = ""
    stdout_final: str = ""


def compute_rei(fix_iterations: int, error_types: list[str], successful: bool) -> float:
    """Compute weighted REI.

    REI = Σ(weight per error type) / (successful_steps + 1)
    If not successful, REI = ∞ (capped at 100 for reporting).
    """
    if not successful:
        return 100.0  # cap
    if fix_iterations == 0:
        return 0.0
    total_weight = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
    return round(total_weight / (fix_iterations + 1), 4)


# ── Correctness-Aware REI (REI-c) ──

DEFAULT_CORRECTNESS_WEIGHT = 10.0
EPSILON = 0.001


def compute_rei_c(
    rei: float,
    ground_truth: float,
    reproduced_value: float | None,
    correctness_weight: float = DEFAULT_CORRECTNESS_WEIGHT,
) -> tuple[float, float, bool]:
    """Compute correctness-aware REI (REI-c).

    REI-c = REI + correctness_ratio * correctness_weight

    correctness_ratio = |reproduced - ground_truth| / max(|ground_truth|, EPSILON)
    This normalizes the deviation so it's comparable across papers with
    different D-index magnitudes.

    Silent failure = code ran fine (low REI) but results are wrong (high deviation).

    Returns:
        (REI_c, correctness_ratio, is_silent_failure)
    """
    if reproduced_value is None:
        # Failed to produce any output — already captured by REI penalty
        return rei, 1.0, False

    denom = max(abs(ground_truth), EPSILON)
    correctness_ratio = min(abs(reproduced_value - ground_truth) / denom, 10.0)
    rei_c = round(rei + correctness_ratio * correctness_weight, 4)
    is_silent = flag_silent_failure(rei, correctness_ratio)

    return rei_c, round(correctness_ratio, 6), is_silent


def flag_silent_failure(
    rei: float,
    correctness_ratio: float,
    rei_threshold: float = 0.5,
    correctness_threshold: float = 0.1,
) -> bool:
    """Flag when code runs without meaningful errors but produces wrong results.

    A silent failure means the LLM generated syntactically valid code that
    produces numerically wrong output — the most dangerous failure mode
    because it can go undetected in automated pipelines.
    """
    return rei <= rei_threshold and correctness_ratio > correctness_threshold


def fix_code(
    code: str,
    error: str,
    error_category: str,
    llm: BaseChatModel,
    attempt: int,
) -> str:
    """Generate a fix using the appropriate strategy."""
    # Progress through strategies: syntax → import → runtime → logic → simplify
    strategy_idx = min(attempt, len(FIX_STRATEGIES) - 1)
    strategy = FIX_STRATEGIES[strategy_idx]

    prompt = HumanMessage(content=f"""{strategy['prompt']}

Error ({error_category}):
{error[:800]}

Current code:
```python
{code[:2000]}
```""")

    response = llm.invoke([prompt])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Extract code from response
    code_match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    # If no code block, check if response itself is code
    lines = text.split("\n")
    filtered = []
    for line in lines:
        s = line.strip()
        if not s:
            filtered.append(line)
            continue
        if re.match(r"^(Okay|Let me|Here|I'll|The|This|First|Now|But|So|However)", s):
            continue
        if "<think>" in s or "</think>" in s:
            continue
        filtered.append(line)
    return "\n".join(filtered).strip()


def run_rei_measurement(
    paper_id: str,
    ground_truth: float,
    paper_context: dict[str, Any],
    llm: BaseChatModel,
    max_fix_iterations: int = 5,
) -> REIResult:
    """Run a single REI measurement: generate code → execute → correct → compare.

    Args:
        paper_id: SciSciNet paper ID.
        ground_truth: Pre-computed disruption_score from SciSciNet.
        paper_context: Paper metadata (title, year, authors, etc.).
        llm: Language model.
        max_fix_iterations: Maximum self-correction attempts.

    Returns:
        REIResult with full details.
    """
    result = REIResult(paper_id=paper_id, ground_truth=ground_truth)
    t0 = time.time()

    # Step 1: Generate initial code
    gen_prompt = HumanMessage(content=f"""Write Python code to compute the Disruption Index (D-index) for a focal paper.

D-index formula:
  D = (n_i - n_j) / (n_i + n_j + n_k)

Where:
  n_i = number of citing papers that cite ONLY the focal paper
  n_j = number of citing papers that cite BOTH the focal paper AND its references
  n_k = number of citing papers that cite ONLY the references (not the focal paper)

Paper: {paper_context.get('title', 'Unknown')}
Year: {paper_context.get('year', 'Unknown')}
Paper ID: {paper_id}

The code should:
1. Use the OpenAlex API (https://api.openalex.org/works/{paper_id}) to get citations and references
2. Compute n_i, n_j, n_k by comparing citation sets
3. Calculate D-index = (n_i - n_j) / (n_i + n_j + n_k)
4. Print results as: D_INDEX = <value>

Use only: requests, json, time. Handle API errors gracefully.
Output ONLY the Python code in a ```python block.""")

    response = llm.invoke([gen_prompt])
    code = str(response.content)
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)

    code_match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", code, re.DOTALL)
    if code_match:
        code = code_match.group(1).strip()
    else:
        lines = code.split("\n")
        code = "\n".join(l for l in lines if not re.match(
            r"^(Okay|Let me|Here|I'll|The|This|First|<think>)", l.strip()
        ))

    result.code_final = code

    # Step 2-4: Execute with self-correction
    for attempt in range(max_fix_iterations + 1):
        exec_result = execute_python(code, timeout=120)

        # Check for thinking tag pollution
        if "<think>" in code or "</think>" in code:
            code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)
            exec_result = execute_python(code, timeout=120)

        if exec_result["exit_code"] == 0:
            stderr = exec_result.get("stderr", "")
            # Check for real errors in stderr
            has_real_error = any(
                p in stderr for p in ["Traceback", "Error:", "Exception"]
            )
            if not has_real_error:
                # Parse D-index from stdout
                parsed = _parse_dindex(exec_result["stdout"])
                if parsed is not None:
                    result.reproduced_value = parsed
                    result.status = "SUCCESS"
                    result.stdout_final = exec_result["stdout"]
                    result.fix_iterations = attempt
                    break

        # Failure — classify and fix
        error_text = exec_result["stderr"] or exec_result["stdout"]
        error_cat = classify_error(error_text)
        result.error_types.append(error_cat)

        if attempt < max_fix_iterations:
            code = fix_code(code, error_text, error_cat, llm, attempt)
            result.code_final = code

    # Compute REI
    result.weighted_errors = sum(ERROR_WEIGHTS.get(e, 3) for e in result.error_types)
    result.REI = compute_rei(
        result.fix_iterations, result.error_types,
        result.status == "SUCCESS",
    )
    result.elapsed_total = round(time.time() - t0, 2)

    return result


def _parse_dindex(stdout: str) -> Optional[float]:
    """Extract D-index value from stdout."""
    patterns = [
        r"D_INDEX\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        r"d_index\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        r"D(?:-index)?\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        r"disruption\w*\s*(?:score|index)?\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
        r"([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)\s*$",
    ]
    for pat in patterns:
        matches = list(re.finditer(pat, stdout, re.IGNORECASE))
        if matches:
            try:
                return float(matches[-1].group(1))
            except (ValueError, TypeError):
                continue
    return None


def select_test_papers(n: int = 10) -> list[dict[str, Any]]:
    """Select N papers from SciSciNet for REI measurement.

    Stratifies by disruption score: 3 high (D>0.1), 4 mid, 3 low (D<0).
    """
    papers = load_table("papers")
    df = papers.dropna(subset=["disruption_score", "title", "doi"]).copy()

    high = df[df["disruption_score"] > 0.1].sample(min(3, len(df[df["disruption_score"] > 0.1])), random_state=42)
    mid = df[(df["disruption_score"] >= 0) & (df["disruption_score"] <= 0.1)].sample(min(4, len(df)), random_state=42)
    low = df[df["disruption_score"] < 0].sample(min(3, len(df[df["disruption_score"] < 0])), random_state=42)

    selected = pd.concat([high, mid, low], ignore_index=True)

    results = []
    for _, row in selected.iterrows():
        results.append({
            "paper_id": row["paper_id"],
            "ground_truth": round(row["disruption_score"], 5),
            "title": str(row.get("title", ""))[:200],
            "year": int(row.get("year", 0)),
            "citation_count": int(row.get("citation_count", 0)),
        })
    return results


def compute_field_rei_distribution(
    papers: pd.DataFrame,
    paper_fields: pd.DataFrame,
    fields: pd.DataFrame,
) -> pd.DataFrame:
    """Compute per-field mean disruption as proxy for 'field reproducibility difficulty'."""
    merged = papers[["paper_id", "disruption_score"]].merge(
        paper_fields, on="paper_id"
    ).merge(fields, on="field_id")

    stats = merged.groupby("field_name").agg(
        mean_disruption=("disruption_score", "mean"),
        std_disruption=("disruption_score", "std"),
        n_papers=("paper_id", "count"),
    ).reset_index()

    stats["abs_mean"] = stats["mean_disruption"].abs()
    return stats.sort_values("abs_mean")


def run_m3_suite(
    llm: BaseChatModel,
    n_papers: int = 6,
    max_fixes: int = 5,
) -> dict[str, Any]:
    """Run the full M3 REI measurement suite.

    Args:
        llm: Language model.
        n_papers: Number of test papers.
        max_fixes: Max self-correction iterations per paper.

    Returns:
        Full M3 report dict.
    """
    print("=" * 70)
    print("M3: Self-Correction Loop + REI Validation")
    print("=" * 70)

    # Select test papers
    print(f"\nSelecting {n_papers} test papers from SciSciNet...")
    test_papers = select_test_papers(n_papers)
    for tp in test_papers:
        print(f"  {tp['paper_id']}: D={tp['ground_truth']:+.4f}  "
              f"cites={tp['citation_count']}  \"{tp['title'][:60]}...\"")

    # Run REI measurements
    print(f"\nRunning REI measurements (max {max_fixes} fixes each)...")
    results: list[REIResult] = []
    for i, tp in enumerate(test_papers):
        print(f"\n  [{i+1}/{n_papers}] Paper {tp['paper_id']} (D={tp['ground_truth']:+.4f})...")
        r = run_rei_measurement(
            paper_id=tp["paper_id"],
            ground_truth=tp["ground_truth"],
            paper_context=tp,
            llm=llm,
            max_fix_iterations=max_fixes,
        )
        results.append(r)
        status_icon = "OK" if r.status == "SUCCESS" else "FAIL"
        print(f"    Status: {status_icon}  Fixes: {r.fix_iterations}  "
              f"REI: {r.REI:.2f}  Errors: {r.error_types}")

        if r.reproduced_value is not None:
            dev = abs(r.reproduced_value - r.ground_truth)
            print(f"    Reproduced D={r.reproduced_value:+.4f}  "
                  f"Ground truth D={r.ground_truth:+.4f}  Δ={dev:.4f}")

    # Aggregate stats
    successful = [r for r in results if r.status == "SUCCESS"]
    failed = [r for r in results if r.status != "SUCCESS"]
    rei_values = [r.REI for r in successful]

    report = {
        "total": len(results),
        "successful": len(successful),
        "failed": len(failed),
        "mean_REI": round(np.mean(rei_values), 4) if rei_values else None,
        "median_REI": round(np.median(rei_values), 4) if rei_values else None,
        "max_REI": round(max(rei_values), 4) if rei_values else None,
        "min_REI": round(min(rei_values), 4) if rei_values else None,
        "per_paper": [
            {
                "paper_id": r.paper_id,
                "ground_truth": r.ground_truth,
                "reproduced": r.reproduced_value,
                "status": r.status,
                "fix_iterations": r.fix_iterations,
                "error_types": r.error_types,
                "REI": r.REI,
                "elapsed": r.elapsed_total,
            }
            for r in results
        ],
        "error_distribution": {},
    }

    # Error type distribution
    all_errors = []
    for r in results:
        all_errors.extend(r.error_types)
    from collections import Counter
    report["error_distribution"] = dict(Counter(all_errors))

    # Print summary
    print("\n" + "-" * 50)
    print("M3 SUMMARY")
    print("-" * 50)
    print(f"  Papers tested: {report['total']}")
    print(f"  Successful: {report['successful']}")
    print(f"  Failed: {report['failed']}")
    if report["mean_REI"] is not None:
        print(f"  Mean REI: {report['mean_REI']:.4f}")
        print(f"  Median REI: {report['median_REI']:.4f}")
        print(f"  REI range: [{report['min_REI']:.4f}, {report['max_REI']:.4f}]")
    print(f"  Error distribution: {report['error_distribution']}")

    return report


# ── Standalone test ──

if __name__ == "__main__":
    import os
    os.environ.setdefault("OPENAI_API_KEY", "not-needed")
    os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
    os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
    os.environ.setdefault("LLM_MAX_TOKENS", "2048")

    from src.sciscigpt_local.llm_backends import load_llm_from_env

    llm = load_llm_from_env()
    report = run_m3_suite(llm, n_papers=6, max_fixes=3)

    # Save
    import json
    out_path = "refine-logs/m3_results.json"
    from pathlib import Path
    Path(out_path).write_text(json.dumps(report, indent=2, default=str))
    print(f"\nResults saved to {out_path}")
