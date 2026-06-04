"""Focused paper reproduction pipeline for M2.

Instead of the full multi-agent graph, this uses a targeted pipeline:
  1. Paper Ingestion — LLM extracts methods, data, analysis steps
  2. Code Generation — LLM generates reproduction code
  3. Sandbox Execution — run the code, capture results
  4. Result Comparison — compare with paper's reported values
  5. Self-Correction — on failure, analyze error, fix, retry
  6. REI Computation — Reproducibility Effort Index

This is more reliable than the full graph for a specific paper reproduction task.
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.paper_ingestion import extract_paper_structure

CODE_GENERATION_PROMPT = """You are a scientific code generator. Generate Python code to reproduce the analysis described below.

Rules:
1. Write complete, runnable Python code.
2. Use only standard scientific packages: pandas, numpy, scipy, matplotlib, requests, json.
3. Include print() statements for all key results.
4. Handle missing data gracefully (try/except for API calls).
5. Do NOT use packages that aren't in the standard scientific Python ecosystem.

Available modules (include inline, the sandbox has NO custom packages installed):
- Use `requests` to call OpenAlex API directly: https://api.openalex.org/works?search=QUERY
- Use `pandas`, `numpy`, `scipy` for computation
- Do NOT import from src.sciscigpt_local or any custom package — they are NOT available

IMPORTANT: Output a SINGLE ```python code block containing the complete runnable script.
Do NOT include any thinking, explanation, or narration — ONLY the Python code inside the code block.
The first character of your response MUST be ``` (backtick)."""


def generate_reproduction_code(
    paper_structure: dict[str, Any],
    data_context: dict[str, Any],
    llm: BaseChatModel,
) -> str:
    """Generate Python code to reproduce a paper's analysis.

    Args:
        paper_structure: Output from extract_paper_structure.
        data_context: Available data (file paths, API endpoints, etc.).
        llm: Language model.

    Returns:
        Python code as a string.
    """
    analysis_steps = paper_structure.get("analysis_steps", [])
    methods = paper_structure.get("methods", [])
    datasets = paper_structure.get("datasets", [])
    dependencies = paper_structure.get("dependencies", [])

    context = f"""## Paper Analysis

Methods:
{json.dumps(methods, indent=2)}

Analysis Steps:
{json.dumps(analysis_steps, indent=2)}

Datasets:
{json.dumps(datasets, indent=2)}

Dependencies:
{json.dumps(dependencies, indent=2)}

## Available Data
{json.dumps(data_context, indent=2)}

## Task
Generate Python code that reproduces the analysis described above.
The code will be executed in a sandbox with these packages: pandas, numpy, scipy, requests, json, matplotlib.
"""

    messages = [
        SystemMessage(content=CODE_GENERATION_PROMPT),
        HumanMessage(content=context),
    ]

    response = llm.invoke(messages)
    response_text = str(response.content)

    # Strip thinking tags (Qwen3 feature)
    response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    # Find ALL ```python code blocks, take the LAST one
    # (Qwen3 puts thinking first, then actual code last)
    code_blocks = list(re.finditer(r"```(?:python)?\s*\n(.*?)\n\s*```", response_text, re.DOTALL))
    if code_blocks:
        # Take the last/largest code block (most likely the actual code)
        code = code_blocks[-1].group(1).strip()
        # Filter lines that look like thinking
        lines = []
        for line in code.split("\n"):
            stripped = line.strip()
            if not stripped:
                lines.append(line)
                continue
            # Skip thinking-like lines
            if re.match(r"^(Okay|Let me|I need|First|Wait|The user|Now|But|So|However|Alternatively|Maybe|Perhaps|Hmm|Thus|Therefore)", stripped):
                continue
            if stripped.startswith("//") or stripped.startswith("#"):
                # Allow Python comments
                lines.append(line)
                continue
            lines.append(line)
        clean_code = "\n".join(lines).strip()
        if clean_code:
            return clean_code

    # No code block found — try to extract code from the response
    # Remove lines that look like thinking/narration
    lines = response_text.split("\n")
    code_lines = []
    for line in lines:
        stripped = line.strip()
        if not stripped:
            code_lines.append(line)
            continue
        if re.match(r"^(Okay|Let me|I need|First|Wait|The user|Now|But|So|However|Alternatively|Maybe|Perhaps|Hmm|Thus|Therefore)", stripped):
            continue
        if "<think>" in stripped or "</think>" in stripped:
            continue
        code_lines.append(line)
    return "\n".join(code_lines).strip()


def compare_results(
    reproduced: dict[str, Any],
    expected: dict[str, Any],
    tolerance: float = 0.2,
) -> dict[str, Any]:
    """Compare reproduced results with expected paper results.

    Args:
        reproduced: Results from sandbox execution.
        expected: Expected values from paper extraction.
        tolerance: Relative tolerance for numerical comparison.

    Returns:
        Comparison report with match status and deviations.
    """
    comparisons = []

    for metric_name, expected_val in expected.items():
        if metric_name in reproduced:
            rep_val = reproduced[metric_name]
            try:
                ev = float(expected_val)
                rv = float(rep_val)
                if ev != 0:
                    deviation = abs(rv - ev) / abs(ev)
                else:
                    deviation = abs(rv - ev) if rv != 0 else 0.0
                match = deviation <= tolerance
                comparisons.append({
                    "metric": metric_name,
                    "expected": ev,
                    "reproduced": rv,
                    "deviation": round(deviation, 4),
                    "match": match,
                })
            except (ValueError, TypeError):
                comparisons.append({
                    "metric": metric_name,
                    "expected": str(expected_val),
                    "reproduced": str(rep_val),
                    "deviation": None,
                    "match": str(expected_val) == str(rep_val),
                })

    matched = sum(1 for c in comparisons if c["match"])
    total = len(comparisons)

    return {
        "comparisons": comparisons,
        "match_rate": round(matched / total, 4) if total > 0 else 0.0,
        "all_match": matched == total and total > 0,
    }


def run_reproduction(
    paper_text: str,
    data_context: dict[str, Any],
    llm: BaseChatModel,
    max_fix_iterations: int = 5,
) -> dict[str, Any]:
    """Run the full paper reproduction pipeline.

    Args:
        paper_text: Full or partial text of the paper to reproduce.
        data_context: Available data sources.
        llm: Language model.
        max_fix_iterations: Maximum number of self-correction iterations.

    Returns:
        Full reproduction report including REI.
    """
    fix_iterations = 0
    errors: list[str] = []
    final_result: dict[str, Any] = {}

    # Step 1: Extract paper structure
    structure = extract_paper_structure(paper_text, llm)
    if "error" in structure:
        return {"status": "FAILED", "stage": "extraction", "error": structure["error"], "fix_iterations": 0}

    # Step 2: Generate reproduction code
    code = generate_reproduction_code(structure, data_context, llm)

    # Step 3-5: Execute with self-correction
    while fix_iterations <= max_fix_iterations:
        result = execute_python(code, timeout=120)

        if result["exit_code"] == 0 and not _has_errors(result["stderr"]) and not _code_has_think_tags(code):
            # Success — parse output
            final_result = {
                "stdout": result["stdout"],
                "stderr": result["stderr"],
                "exit_code": result["exit_code"],
                "elapsed": result["elapsed"],
            }
            break

        # Failure — analyze and fix
        fix_iterations += 1
        error_info = result["stderr"] or result["stdout"]
        errors.append(f"Iteration {fix_iterations}: {error_info[:500]}")

        if fix_iterations <= max_fix_iterations:
            code = _fix_code(code, error_info, llm)

    # Step 6: Compare with expected results
    expected = {}
    if "evaluation" in structure and "expected_values" in structure["evaluation"]:
        expected = structure["evaluation"]["expected_values"]

    comparison = {}
    if expected and final_result:
        # Parse numerical values from stdout
        parsed = _parse_metrics_from_output(final_result.get("stdout", ""))
        comparison = compare_results(parsed, expected)

    # Compute REI
    successful_steps = 3  # extraction + generation + execution
    dei = fix_iterations / successful_steps if successful_steps > 0 else float("inf")

    return {
        "status": "SUCCESS" if final_result else "FAILED",
        "paper_structure": structure,
        "code": code,
        "result": final_result,
        "comparison": comparison,
        "fix_iterations": fix_iterations,
        "errors": errors,
        "REI": round(dei, 4),
    }


def _has_errors(stderr: str) -> bool:
    """Check if stderr contains actual errors (not just warnings)."""
    error_patterns = [
        "Traceback (most recent call last)",
        "Error:",
        "ModuleNotFoundError",
        "ImportError",
        "NameError",
        "TypeError",
        "SyntaxError",
        "ValueError",
        "KeyError",
        "IndexError",
        "AttributeError",
    ]
    return any(p in stderr for p in error_patterns)


def _code_has_think_tags(code: str) -> bool:
    """Check if generated code still has Qwen3 thinking tokens."""
    return "<think>" in code or "</think>" in code


def _fix_code(code: str, error: str, llm: BaseChatModel) -> str:
    """Generate a fix for broken code based on the error message."""
    fix_prompt = HumanMessage(content=f"""The following Python code failed with this error:

Error:
{error[:1000]}

Current code:
```python
{code[:2000]}
```

Fix the code to address this error. Output ONLY the complete fixed Python code, no explanation.
""")

    response = llm.invoke([fix_prompt])
    response_text = str(response.content)
    response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    code_match = re.search(r"```(?:python)?\s*\n?(.*?)\n?```", response_text, re.DOTALL)
    if code_match:
        return code_match.group(1).strip()

    return response_text.strip()


def validate_generated_code(code: str) -> dict:
    """Code generation guardrail — validate structure before execution.

    Checks:
      1. No thinking tags (<think> or </think>)
      2. Has at least one import statement
      3. Has at least one print() call
      4. No obvious natural language narration
      5. Has at least one recognizable Python keyword

    Returns dict with pass/fail and specific failures.
    """
    failures = []

    # Check 1: No thinking tags
    if "<think>" in code or "</think>" in code:
        failures.append("thinking_tags_present")

    # Check 2: Has imports
    if not re.search(r"^(?:import|from)\s+\w", code, re.MULTILINE):
        failures.append("no_imports")

    # Check 3: Has print() calls
    if "print(" not in code and "print (" not in code:
        failures.append("no_print_calls")

    # Check 4: No natural language narration
    narration_markers = [
        r"^(Okay|Let me|I need|First,|Wait,|The user|Now,|But |So,|However|Alternatively|Maybe|Perhaps|Hmm)",
        r"^(Here.?s|This code|The following|Below is|Above)",
    ]
    lines = code.strip().split("\n")
    narration_lines = 0
    for line in lines:
        stripped = line.strip()
        if not stripped:
            continue
        for marker in narration_markers:
            if re.match(marker, stripped, re.IGNORECASE):
                narration_lines += 1
                break
    if narration_lines > 3:
        failures.append(f"narration_detected_{narration_lines}_lines")

    # Check 5: Has Python keywords (def, class, =, for, if, etc.)
    has_python = bool(re.search(
        r"\b(def|class|import|from|for|if|while|with|return|try|except)\b",
        code,
    ))
    has_assignment = "=" in code
    if not has_python and not has_assignment:
        failures.append("no_python_syntax")

    return {
        "valid": len(failures) == 0,
        "failures": failures,
        "code_length": len(code),
        "code_lines": len(code.split("\n")),
    }


def _parse_metrics_from_output(stdout: str) -> dict[str, float]:
    """Extract numerical metrics from stdout text.

    Looks for patterns like:
      metric_name: value
      metric_name = value
    """
    metrics = {}
    patterns = [
        (r"(\w+(?:_\w+)*)\s*[:=]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", 1),
        (r"(\w+(?:_\w+)*)\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", 0),
    ]

    for pattern, val_group in patterns:
        for match in re.finditer(pattern, stdout):
            name = match.group(1)
            if name not in metrics:
                try:
                    metrics[name] = float(match.group(val_group + 1))
                except (ValueError, TypeError):
                    pass

    return metrics
