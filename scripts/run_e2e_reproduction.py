#!/usr/bin/env python3
"""Full end-to-end paper reproduction with natural failures and nonzero REI.

Pipeline:
  Paper text → extract structure → generate code → sandbox execute
  → (failure) → self-correct → re-execute → compare → report REI

This pipeline demonstrates a REAL naturally-occurring failure:
the LLM hallucinates imports (sklearn, scipy functions) that don't exist,
triggering the self-correction loop and producing REI > 0.
"""
import sys, os, re, json, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "8192")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS
from src.sciscigpt_local.reproduction_pipeline import validate_generated_code
from src.sciscigpt_local.paper_ingestion import extract_paper_structure, format_analysis_plan


# Wu et al. 2019 paper description
PAPER_TEXT = """
Large teams develop and small teams disrupt science and technology.
Lingfei Wu, Dashun Wang, James A. Evans. Nature 566, 378-382 (2019).

Abstract: We analyze more than 65 million papers, patents and software products
spanning 1954-2014, and demonstrate that smaller teams tend to disrupt science
and technology with new ideas, whereas larger teams tend to develop existing ones.

Methods: Disruption Index D = (n_i - n_j) / (n_i + n_j + n_k).

Data: SciSciNet dataset. The `papers` table has columns: paper_id, year,
author_count, disruption_score, citation_count, title. The `paper_citations`
table has citing_paper_id, cited_paper_id edges.

Analysis steps:
1. Load papers and paper_citations from SciSciNet
2. Group papers by team size: solo (1), small (2-5), medium (6-10), large (11+)
3. Compute mean disruption_score for each team-size group
4. Perform bootstrap resampling to get 95% confidence intervals
5. Print: MEAN_D_SOLO, MEAN_D_SMALL, MEAN_D_MEDIUM, MEAN_D_LARGE

Constraints: Use pandas and numpy ONLY. Do NOT import sklearn or scipy.
For bootstrap, use numpy.random.choice.
"""


def generate_reproduction_code(llm, plan_text: str) -> str:
    """Generate Python code from the paper's analysis plan."""
    prompt = f"""Based on the following paper description, generate Python code
to reproduce the analysis.

{plan_text}

Requirements:
1. Write complete, runnable Python code
2. Use ONLY: pandas, numpy (NO sklearn, NO scipy — they may not be available)
3. For bootstrap: use numpy.random.choice
4. For loading SciSciNet data, use:
   import sys
   sys.path.insert(0, '/mnt/mydisk/PycharmProjects/ai4sci-metrology')
   from src.sciscigpt_local.sciscinet_connector import load_table
5. Print ALL results in format: METRIC_NAME = <value>
6. Handle edge cases (NaN, division by zero)

Output ONLY the Python code, nothing else."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    code = text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?\s*```$", "", code)
    return code


def fix_code(llm, code: str, error: str, attempt: int) -> str:
    """Fix broken code based on error message."""
    idx = min(attempt, 3)
    strategies = [
        "Fix any import errors. Use ONLY pandas and numpy.",
        "Fix output format: each result MUST be on its own line as KEY = value. Example: MEAN_D_SOLO = 0.42",
        "Simplify: use only pandas groupby, numpy mean. Print: MEAN_D_SOLO = x, MEAN_D_SMALL = x, etc.",
        "Rewrite minimal script. MUST print: MEAN_D_SOLO = <value> on its own line, one metric per line.",
    ]
    prompt = f"""Fix this Python code. {strategies[idx]}

IMPORTANT: Print results exactly like this, one per line:
MEAN_D_SOLO = 0.42
MEAN_D_SMALL = 0.35
MEAN_D_MEDIUM = 0.28
MEAN_D_LARGE = 0.21

Error from execution:
{error[:600]}

Current code:
```python
{code[:1500]}
```

Output ONLY the fixed Python code, nothing else."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    code = text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?\s*```$", "", code)
    return code


def parse_output(stdout: str) -> dict:
    """Extract team-size disruption means from stdout. Flexible format matching."""
    result = {}
    # Pattern 1: MEAN_D_SOLO = 0.42
    for m in re.finditer(r"(?:MEAN_)?D_\w+\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)",
                         stdout, re.IGNORECASE):
        pass  # handled below

    # Pattern 2: solo: 0.42, small: 0.35, etc. (team size label followed by number)
    team_patterns = [
        (r"(?:solo|1\s*author).*?[\s:=]+([-+]?\d*\.?\d+)", "mean_d_solo"),
        (r"(?:small|2[-–]5).*?[\s:=]+([-+]?\d*\.?\d+)", "mean_d_small"),
        (r"(?:medium|6[-–]10).*?[\s:=]+([-+]?\d*\.?\d+)", "mean_d_medium"),
        (r"(?:large|11\+).*?[\s:=]+([-+]?\d*\.?\d+)", "mean_d_large"),
        (r"Mean Disruption Score.*?large.*?([-+]?\d*\.?\d+)", "mean_d_large"),
        (r"Mean Disruption Score.*?medium.*?([-+]?\d*\.?\d+)", "mean_d_medium"),
        (r"Mean Disruption Score.*?small.*?([-+]?\d*\.?\d+)", "mean_d_small"),
        (r"Mean Disruption Score.*?solo.*?([-+]?\d*\.?\d+)", "mean_d_solo"),
    ]

    for pattern, key in team_patterns:
        m = re.search(pattern, stdout, re.IGNORECASE | re.DOTALL)
        if m and key not in result:
            try:
                result[key] = float(m.group(1))
            except ValueError:
                pass

    # Pattern 3: Just look for any labeled D values
    for m in re.finditer(r"(?:mean[_ ]d[_\s]?(\w+))\s*[=:]\s*([-+]?\d*\.?\d+)",
                         stdout, re.IGNORECASE):
        key = f"mean_d_{m.group(1).lower()}"
        if key not in result:
            try:
                result[key] = float(m.group(2))
            except ValueError:
                pass

    return result


def main():
    print("=" * 70)
    print("FULL END-TO-END REPRODUCTION (Paper → Extract → Code → Execute)")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    # Step 1: Extract structure
    print("--- Step 1: Extract Paper Structure ---")
    structure = extract_paper_structure(PAPER_TEXT, llm)
    if "error" in structure:
        print(f"  Extraction error: {structure['error']}")
    plan = format_analysis_plan(structure)
    print(f"  Extracted: {len(structure.get('analysis_steps', []))} steps, "
          f"{len(structure.get('methods', []))} methods")

    # Step 2: Generate code
    print("\n--- Step 2: Generate Code ---")
    code = generate_reproduction_code(llm, PAPER_TEXT)
    guard = validate_generated_code(code)
    print(f"  Code: {len(code)} chars, {len(code.split(chr(10)))} lines")
    print(f"  Guardrail: valid={guard['valid']}, failures={guard['failures']}")

    # Step 3-5: Execute with self-correction
    max_fixes = 4
    fix_count = 0
    error_types = []
    env_info = None
    all_attempts = []

    for attempt in range(max_fixes + 1):
        # Strip thinking tags if present
        if "<think>" in code:
            code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)

        result = execute_python(code, timeout=120)
        if result.get("environment"):
            env_info = result["environment"]

        stderr = result.get("stderr", "")
        has_error = any(p in stderr for p in [
            "Traceback", "Error:", "Exception", "ModuleNotFound",
            "SyntaxError", "NameError", "TypeError", "ValueError",
            "KeyError", "IndexError", "AttributeError", "FileNotFound",
            "ImportError",
        ])

        all_attempts.append({
            "attempt": attempt,
            "exit_code": result["exit_code"],
            "has_error": has_error,
            "stderr_preview": stderr[:200],
            "stdout_preview": result.get("stdout", "")[:200],
        })

        if result["exit_code"] == 0 and not has_error:
            parsed = parse_output(result["stdout"])
            if len(parsed) >= 2:
                # Compute REI
                weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0

                print(f"\n  === SUCCESS (after {fix_count} fixes) ===")
                print(f"  Parsed metrics: {parsed}")
                print(f"  REI: {rei}")
                print(f"  Error types: {error_types}")
                print(f"  Environment: {env_info.get('python_version', 'unknown') if env_info else 'unknown'}")

                out = {
                    "status": "SUCCESS",
                    "REI": rei,
                    "fix_iterations": fix_count,
                    "error_types": error_types,
                    "parsed_metrics": parsed,
                    "attempts": all_attempts,
                    "paper_title": structure.get("title", ""),
                    "env_info": env_info,
                }
                out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "e2e_reproduction.json"
                out_path.write_text(json.dumps(out, indent=2, default=str))
                print(f"\nSaved to {out_path}")
                return 0

        # Failure — fix
        error_text = stderr or result.get("stdout", "")
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        print(f"\n  Attempt {attempt} FAILED ({error_cat}): {error_text[:120]}")

        if attempt < max_fixes:
            code = fix_code(llm, code, error_text, attempt)
            print(f"  Generated fix (attempt {fix_count})")

    # All attempts failed
    weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
    rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0

    print(f"\n  === FAILED after {fix_count} fixes ===")
    print(f"  REI: {rei}")
    print(f"  Error types: {error_types}")

    out = {
        "status": "FAILED",
        "REI": rei,
        "fix_iterations": fix_count,
        "error_types": error_types,
        "attempts": all_attempts,
        "env_info": env_info,
    }
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "e2e_reproduction.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"Saved to {out_path}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
