#!/usr/bin/env python3
"""Error Injection Framework — calibrate REI by systematically injecting errors.

Injects known errors into working reproduction code, runs through self-correction,
and measures REI per error type. This validates REI as a measurement instrument.

Error catalog:
  syntax:   missing colon, wrong indentation, typo in keyword
  import:   hallucinated module, wrong import name
  logic:    incorrect formula, wrong variable name, off-by-one
  data:     wrong column name, missing filter, wrong data type
  timeout:  infinite loop, very large computation
"""

import sys, os, re, json, tempfile, copy
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "8192")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS

# Baseline working D-index code (verified correct)
BASELINE_CODE = '''import pandas as pd
import sys
sys.path.insert(0, '/mnt/mydisk/PycharmProjects/ai4sci-metrology')

refs = pd.read_csv("{refs_path}")
cites = pd.read_csv("{cites_path}")

ref_set = set(refs["reference_id"].values)
n_i, n_j = 0, 0
unique_citers = cites["citing_paper_id"].unique()

for cid in unique_citers:
    citer_refs = set(cites[cites["citing_paper_id"] == cid]["cited_paper_id"].values)
    if citer_refs & ref_set:
        n_j += 1
    else:
        n_i += 1

denom = n_i + n_j
D = (n_i - n_j) / denom if denom > 0 else 0.0

print(f"D_INDEX = {{D}}")
print(f"n_i = {{n_i}}")
print(f"n_j = {{n_j}}")
'''

ERROR_INJECTIONS = {
    "syntax_missing_colon": {
        "type": "syntax",
        "description": "Missing colon in if statement",
        "inject": lambda code: code.replace("if citer_refs & ref_set:", "if citer_refs & ref_set"),
    },
    "syntax_bad_indent": {
        "type": "syntax",
        "description": "Wrong indentation inside for loop",
        "inject": lambda code: code.replace("        citer_refs", "       citer_refs"),
    },
    "syntax_keyword_typo": {
        "type": "syntax",
        "description": "Typo in keyword (def → df)",
        "inject": lambda code: code.replace("    if citer_refs & ref_set", "    df citer_refs & ref_set"),
    },
    "import_hallucinated": {
        "type": "import",
        "description": "Import a module that doesn't exist",
        "inject": lambda code: "from scipy.special import cohen_effect_size\n" + code,
    },
    "import_wrong_name": {
        "type": "import",
        "description": "Correct package, wrong function name",
        "inject": lambda code: "from pandas import read_csvfile\n" + code,
    },
    "import_missing": {
        "type": "import",
        "description": "Missing required import",
        "inject": lambda code: code.replace("import pandas as pd\n", ""),
    },
    "logic_wrong_formula": {
        "type": "logic",
        "description": "Incorrect formula: D = n_j/(n_i+n_j) instead of (n_i-n_j)/(n_i+n_j)",
        "inject": lambda code: code.replace("D = (n_i - n_j) / denom if denom > 0 else 0.0",
                                            "D = n_j / denom if denom > 0 else 0.0"),
    },
    "logic_off_by_one": {
        "type": "logic",
        "description": "Off-by-one: n_i += 1 inside wrong branch",
        "inject": lambda code: code.replace(
            "    if citer_refs & ref_set:\n        n_j += 1\n    else:\n        n_i += 1",
            "    if citer_refs & ref_set:\n        n_i += 1\n    else:\n        n_j += 1"),
    },
    "logic_wrong_var": {
        "type": "logic",
        "description": "Wrong variable name: denom → denom_wrong",
        "inject": lambda code: code.replace("denom = n_i + n_j", "denom = n_i + n_j\n    denom_wrong = 0"),
    },
    "data_wrong_column": {
        "type": "data",
        "description": "Wrong column name: reference_id → ref_id",
        "inject": lambda code: code.replace('"reference_id"', '"ref_id"'),
    },
    "data_missing_filter": {
        "type": "data",
        "description": "Missing set() conversion on refs",
        "inject": lambda code: code.replace("ref_set = set(refs", "ref_set = list(refs"),
    },
    "data_wrong_type": {
        "type": "data",
        "description": "Dictionary instead of set lookup",
        "inject": lambda code: code.replace("refs[\"reference_id\"].values", "dict(refs[\"reference_id\"])"),
    },
}


def inject_error(code: str, error_key: str) -> str:
    """Inject a specific error into working code."""
    injection = ERROR_INJECTIONS.get(error_key)
    if injection is None:
        raise ValueError(f"Unknown error: {error_key}")
    return injection["inject"](code)


def fix_code(llm, code: str, error: str) -> str:
    """Ask LLM to fix broken code."""
    prompt = f"""Fix this Python code. The code should compute the D-index:
D = (n_i - n_j) / (n_i + n_j)

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


def parse_d_index(stdout: str) -> float | None:
    """Extract D-index value from stdout."""
    m = re.search(r"D_INDEX\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", stdout)
    if m:
        return float(m.group(1))
    return None


def run_injection_experiment(
    llm, refs_path: str, cites_path: str,
    error_key: str, max_fixes: int = 3,
) -> dict:
    """Run a single error injection experiment."""
    code = BASELINE_CODE.format(refs_path=refs_path, cites_path=cites_path)
    injection = ERROR_INJECTIONS[error_key]
    injected_code = inject_error(code, error_key)

    error_types = []
    fix_count = 0
    attempts = []

    current_code = injected_code

    for attempt in range(max_fixes + 1):
        if "<think>" in current_code:
            current_code = re.sub(r"<think>.*?</think>", "", current_code, flags=re.DOTALL)

        result = execute_python(current_code, timeout=60)
        stderr = result.get("stderr", "")
        has_error = any(p in stderr for p in [
            "Traceback", "Error:", "Exception", "ModuleNotFound",
            "SyntaxError", "NameError", "TypeError", "ValueError",
            "KeyError", "IndexError", "AttributeError", "FileNotFound",
            "ImportError",
        ])

        attempts.append({
            "attempt": attempt,
            "exit_code": result["exit_code"],
            "has_error": has_error,
            "stderr_preview": stderr[:200],
        })

        if result["exit_code"] == 0 and not has_error:
            parsed_d = parse_d_index(result["stdout"])
            return {
                "error_key": error_key,
                "error_type": injection["type"],
                "status": "fixed" if fix_count > 0 else "resilient",
                "fix_count": fix_count,
                "error_types": error_types,
                "parsed_D": parsed_d,
                "attempts": attempts,
            }

        error_text = stderr or result.get("stdout", "")
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        if attempt < max_fixes:
            current_code = fix_code(llm, current_code, error_text)

    return {
        "error_key": error_key,
        "error_type": injection["type"],
        "status": "unfixed",
        "fix_count": fix_count,
        "error_types": error_types,
        "parsed_D": None,
        "attempts": attempts,
    }


def main():
    print("=" * 70)
    print("ERROR INJECTION FRAMEWORK — REI Calibration")
    print("=" * 70)

    from src.sciscigpt_local.sciscinet_connector import load_table

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    # Prepare test data
    print("Preparing test data...")
    pc = load_table("paper_citations")
    paper_id = 2016964321
    refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
    citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
    citer_cites = pc[pc["citing_paper_id"].isin(citers)][
        ["citing_paper_id", "cited_paper_id"]
    ].head(500)

    refs_path = tempfile.mktemp(suffix="_refs.csv")
    cites_path = tempfile.mktemp(suffix="_cites.csv")
    pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
    citer_cites.to_csv(cites_path, index=False)
    print(f"  Paper {paper_id}: {len(refs)} refs, {len(citer_cites)} citation rows\n")

    # Verify baseline
    baseline_result = execute_python(
        BASELINE_CODE.format(refs_path=refs_path, cites_path=cites_path), timeout=30)
    baseline_D = parse_d_index(baseline_result["stdout"])
    print(f"  Baseline D-index: {baseline_D}")
    print(f"  Baseline exit code: {baseline_result['exit_code']}\n")

    # Run all error injections
    n_fixes = 3
    print(f"Running {len(ERROR_INJECTIONS)} error injections ({n_fixes} fix attempts each)...\n")

    results = {}
    for error_key in sorted(ERROR_INJECTIONS.keys()):
        info = ERROR_INJECTIONS[error_key]
        print(f"  [{info['type']}] {error_key}: {info['description']}...", end=" ", flush=True)
        r = run_injection_experiment(llm, refs_path, cites_path, error_key, max_fixes=n_fixes)
        results[error_key] = r

        # Compute REI
        weights = sum(ERROR_WEIGHTS.get(e, 3) for e in r["error_types"])
        rei = round(weights / max(r["fix_count"], 1), 2) if r["fix_count"] > 0 else 0.0
        r["REI"] = rei
        print(f"{r['status']} (fixes={r['fix_count']}, REI={rei})", flush=True)

    # Summary by error type
    print("\n" + "=" * 70)
    print("SUMMARY BY ERROR TYPE")
    print("=" * 70)

    by_type = {}
    for r in results.values():
        t = r["error_type"]
        by_type.setdefault(t, {"total": 0, "fixed": 0, "resilient": 0, "unfixed": 0, "rei_sum": 0.0})
        by_type[t]["total"] += 1
        by_type[t]["fixed" if r["status"] == "fixed" else r["status"]] += 1
        by_type[t]["rei_sum"] += r.get("REI", 0)

    print(f"{'Error Type':<12} {'Count':>6} {'Fixed':>6} {'Resilient':>10} {'Unfixed':>8} {'Avg REI':>8}")
    print("-" * 55)
    for t in ["syntax", "import", "logic", "data"]:
        if t in by_type:
            s = by_type[t]
            avg_rei = s["rei_sum"] / s["total"] if s["total"] > 0 else 0
            print(f"{t:<12} {s['total']:>6} {s['fixed']:>6} {s['resilient']:>10} {s['unfixed']:>8} {avg_rei:>8.1f}")

    # Save results
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "error_injection_results.json"
    out_path.write_text(json.dumps(results, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
