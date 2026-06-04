#!/usr/bin/env python3
"""Hard Reproduction: paper with nonzero n_j, raw citation data.

Gives the LLM raw CSVs (references + citations), NOT preprocessed data.
LLM must implement citation-set matching logic itself.
This triggers real failures and measures REI.

Design:
  - Paper CSV: references of the focal paper
  - Citations CSV: papers citing the focal paper + what they cite
  - LLM must: merge, count n_i/n_j/n_k, compute D-index
  - This is significantly harder than counting a True/False column
"""

import sys, os, re, json, time, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "4096")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS
from src.sciscigpt_local.reproduction_pipeline import validate_generated_code
from src.sciscigpt_local.sciscinet_connector import load_table


def find_hard_paper(papers, pc, min_n_j=2, max_citing=30, min_abs_D=0.1, seed=42):
    """Find a paper with nonzero n_j (citing papers that also cite references)
    and non-trivial subgraph D-index."""
    valid = papers.dropna(subset=["disruption_score", "citation_count", "title"])
    valid = valid[(valid["citation_count"] >= 10) & (valid["citation_count"] <= 50)]

    for _, row in valid.sample(min(300, len(valid)), random_state=seed).iterrows():
        pid = int(row["paper_id"])
        refs = set(pc[pc["citing_paper_id"] == pid]["cited_paper_id"].values)
        citers = pc[pc["cited_paper_id"] == pid]["citing_paper_id"].values[:max_citing]

        if len(refs) < 5 or len(citers) < 8:
            continue

        # Count n_i, n_j
        n_i, n_j = 0, 0
        for cp in citers:
            cp_refs = set(pc[pc["citing_paper_id"] == cp]["cited_paper_id"].values[:100])
            if cp_refs & refs:
                n_j += 1
            else:
                n_i += 1

        denom = n_i + n_j
        sub_D = (n_i - n_j) / denom if denom > 0 else 0.0

        if n_j >= min_n_j and abs(sub_D) >= min_abs_D:
            return row, refs, citers, n_j

    # Fallback: relax min_abs_D
    for _, row in valid.sample(min(200, len(valid)), random_state=seed + 1000).iterrows():
        pid = int(row["paper_id"])
        refs = set(pc[pc["citing_paper_id"] == pid]["cited_paper_id"].values)
        citers = pc[pc["cited_paper_id"] == pid]["citing_paper_id"].values[:max_citing]
        if len(refs) < 3 or len(citers) < 5:
            continue
        n_j = 0
        for cp in citers:
            cp_refs = set(pc[pc["citing_paper_id"] == cp]["cited_paper_id"].values[:100])
            if cp_refs & refs:
                n_j += 1
        if n_j >= min_n_j:
            return row, refs, citers, n_j

    return None, None, None, 0


def prepare_hard_data(paper_row, refs, citers, pc) -> tuple[str, str, dict]:
    """Prepare TWO raw CSVs: references and citations (NOT preprocessed)."""
    pid = int(paper_row["paper_id"])

    # References CSV: focal_paper_id, reference_id
    ref_csv = tempfile.mktemp(suffix="_refs.csv")
    ref_df = pd.DataFrame({
        "reference_id": list(refs),
    })
    ref_df.to_csv(ref_csv, index=False)

    # Citations CSV: citing_paper_id, cited_paper_id (subset around this paper)
    citing_csv = tempfile.mktemp(suffix="_cites.csv")
    all_citer_refs = []
    for cp in citers:
        cp_cited = pc[pc["citing_paper_id"] == cp]["cited_paper_id"].values[:50]
        for c in cp_cited:
            all_citer_refs.append({"citing_paper_id": cp, "cited_paper_id": c})

    cite_df = pd.DataFrame(all_citer_refs)
    cite_df.to_csv(citing_csv, index=False)

    # Ground truth: compute n_i, n_j, n_k from the exact data we provided
    n_i, n_j, n_k = 0, 0, 0
    for cp in citers:
        cp_refs = set(cite_df[cite_df["citing_paper_id"] == cp]["cited_paper_id"].values)
        if cp_refs & refs:
            n_j += 1
        else:
            n_i += 1
    denom = n_i + n_j + n_k
    true_D = (n_i - n_j) / denom if denom > 0 else 0.0

    gt = {
        "paper_id": pid,
        "precomputed_D": float(paper_row["disruption_score"]),
        "subgraph_D": round(true_D, 6),
        "n_i": n_i, "n_j": n_j, "n_k": n_k,
        "n_refs": len(refs),
        "n_citers": len(citers),
        "title": str(paper_row.get("title", ""))[:150],
        "year": int(paper_row.get("year", 0)),
    }
    return ref_csv, citing_csv, gt


def generate_code(llm, ref_csv: str, cite_csv: str, gt: dict) -> str:
    """Generate D-index code from raw citation CSVs (harder task)."""
    prompt = f"""You are given two CSV files:

1. References: '{ref_csv}' — columns: reference_id
   These are ALL papers cited BY the focal paper (its bibliography).

2. Citations: '{cite_csv}' — columns: citing_paper_id, cited_paper_id
   Each row means (citing_paper_id) cites (cited_paper_id).
   IMPORTANT: Every unique citing_paper_id in this file is a paper that cites the focal paper.
   You do NOT need to identify the focal paper — it is not in these CSVs.

Task: Compute the Disruption Index (D-index) for the focal paper.

D = (n_i - n_j) / (n_i + n_j + n_k)

Where:
  n_i = number of citing papers that cite the focal paper but NONE of its references
  n_j = number of citing papers that cite the focal paper AND at least one of its references
  n_k = 0

Algorithm (follow exactly):
1. Load both CSVs with pandas
2. Get the set of ALL reference_ids from the references CSV
3. Get all unique citing_paper_ids from the citations CSV (these ALL cite the focal paper)
4. For each unique citing_paper_id:
   a. Get the set of all cited_paper_ids for this citing paper from the citations CSV
   b. Check if this set has any intersection with the reference set
   c. If intersection is non-empty → n_j += 1, else → n_i += 1
5. n_k = 0
6. D = (n_i - n_j) / (n_i + n_j) if denominator > 0 else 0.0
7. Print exactly: D_INDEX = <value>, n_i = <value>, n_j = <value>, n_k = 0

Use ONLY pandas. Handle empty DataFrames and division-by-zero.
Output ONLY the Python code, nothing else."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Extract code from markdown block — try multiple patterns
    code = None
    # Pattern 1: standard ```python block
    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        # Pattern 2: just ``` block
        match = re.search(r"```\s*\n(.*?)```", text, re.DOTALL)
        if match:
            code = match.group(1).strip()
    if code is None:
        # Fallback: strip ``` markers manually
        code = text.strip()
        if code.startswith("```"):
            code = re.sub(r"^```(?:python)?\s*\n?", "", code)
            code = re.sub(r"\n?\s*```$", "", code)
    return code


def fix_code(llm, code: str, error: str, attempt: int) -> str:
    """Fix broken code."""
    idx = min(attempt, 3)
    strategies = [
        "Fix any syntax errors, missing imports, or markdown formatting issues.",
        "Add proper error handling for missing files, empty DataFrames, division by zero.",
        "Simplify the approach. The citations CSV contains ALL citations FROM papers that cite the focal paper. For each unique citing_paper_id, check if any of its cited_paper_ids are in the reference set. Do NOT try to identify the focal paper.",
        "Rewrite from scratch. Use set() operations on reference IDs. Print D_INDEX, n_i, n_j, n_k=0 on one line.",
    ]
    prompt = f"""Fix this Python code that computes Disruption Index from citation data. {strategies[idx]}

Error from execution:
{error[:600]}

Current broken code:
```python
{code[:1500]}
```

Output ONLY the fixed Python code, nothing else."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Extract code — same robust extraction
    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    # Fallback: strip markers
    code = text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?\s*```$", "", code)
    return code


def parse_output(stdout: str) -> dict:
    """Parse D-index output from stdout. Handles both one-per-line and comma-separated formats."""
    result = {}
    for line in stdout.split("\n"):
        # Use search (not match) to find all key=value pairs on the line
        for m in re.finditer(r"(D_INDEX|d_index|n_i|n_j|n_k)\s*[=:]\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", line.strip(), re.IGNORECASE):
            try:
                result[m.group(1).lower()] = float(m.group(2))
            except ValueError:
                pass
    return result


def run_hard_reproduction(llm, ref_csv, cite_csv, gt, max_fixes=4):
    """Run the hard reproduction with self-correction."""
    fix_count = 0
    error_types = []
    env_info = None

    print("  Generating code for hard reproduction...")
    code = generate_code(llm, ref_csv, cite_csv, gt)

    # Code guardrail check
    guard = validate_generated_code(code)
    print(f"  Code guardrail: valid={guard['valid']}, failures={guard['failures']}")
    if not guard["valid"] and "thinking_tags_present" in guard["failures"]:
        code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)

    for attempt in range(max_fixes + 1):
        if "<think>" in code or "</think>" in code:
            code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)

        result = execute_python(code, timeout=90)
        if result.get("environment"):
            env_info = result["environment"]

        stderr = result.get("stderr", "")
        has_error = any(p in stderr for p in [
            "Traceback", "Error:", "Exception", "ModuleNotFound",
            "SyntaxError", "NameError", "TypeError", "ValueError",
            "KeyError", "IndexError", "AttributeError", "FileNotFound",
        ])

        if result["exit_code"] == 0 and not has_error:
            parsed = parse_output(result["stdout"])
            if "d_index" in parsed:
                sub_D = gt["subgraph_D"]
                comp_D = parsed["d_index"]
                dev = abs(comp_D - sub_D) / max(abs(sub_D), 0.001)

                return {
                    "status": "SUCCESS" if dev < 0.1 else "PARTIAL",
                    "fix_iterations": fix_count,
                    "error_types": error_types,
                    "computed_D": comp_D,
                    "subgraph_D": sub_D,
                    "precomputed_D": gt["precomputed_D"],
                    "deviation": round(dev, 4),
                    "n_i_parsed": parsed.get("n_i"),
                    "n_j_parsed": parsed.get("n_j"),
                    "env_info": env_info,
                    "guardrail_failures": guard["failures"],
                }

        error_text = stderr or result.get("stdout", "")
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        print(f"  Fix attempt {fix_count}: {error_cat} — {error_text[:100]}")
        if attempt < max_fixes:
            code = fix_code(llm, code, error_text, attempt)

    return {
        "status": "FAILED",
        "fix_iterations": fix_count,
        "error_types": error_types,
        "computed_D": None,
        "env_info": env_info,
        "guardrail_failures": guard["failures"] if 'guard' in dir() else [],
    }


def main():
    print("=" * 70)
    print("HARD REPRODUCTION: Raw Citation Data + Self-Correction")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    print("Loading SciSciNet and finding hard paper (nonzero n_j)...")
    papers = load_table("papers")
    pc = load_table("paper_citations")

    row, refs, citers, n_j = find_hard_paper(papers, pc, min_n_j=2)
    if row is None:
        print("  Could not find paper with n_j>=2 in sample. Using fallback...")
        row = papers.dropna(subset=["disruption_score", "citation_count"]).sample(1, random_state=42).iloc[0]
        pid = int(row["paper_id"])
        refs = set(pc[pc["citing_paper_id"] == pid]["cited_paper_id"].values[:10])
        citers = pc[pc["cited_paper_id"] == pid]["citing_paper_id"].values[:15]
        n_j = 0

    pid = str(int(row["paper_id"]))
    D = row["disruption_score"]
    print(f"  Paper: {pid}")
    print(f"  Title: {str(row.get('title',''))[:80]}...")
    print(f"  Precomputed D: {D:+.4f}")
    print(f"  Refs: {len(refs)}, Citers: {len(citers)}, n_j: {n_j}\n")

    ref_csv, cite_csv, gt = prepare_hard_data(row, refs, citers, pc)
    print(f"  Refs CSV: {ref_csv}")
    print(f"  Cites CSV: {cite_csv} ({len(pd.read_csv(cite_csv))} edges)")
    print(f"  Ground truth: n_i={gt['n_i']}, n_j={gt['n_j']}, subgraph_D={gt['subgraph_D']}\n")

    # Run hard reproduction
    print("--- Running Hard Reproduction ---")
    result = run_hard_reproduction(llm, ref_csv, cite_csv, gt, max_fixes=4)

    # Compute REI
    if result["status"] in ("SUCCESS", "PARTIAL"):
        weights = sum(ERROR_WEIGHTS.get(e, 3) for e in result["error_types"])
        rei = round(weights / max(result["fix_iterations"], 1), 4) if result["fix_iterations"] > 0 else 0.0
    else:
        rei = 100.0

    result["REI"] = rei
    result["paper_id"] = pid
    result["precomputed_D"] = gt["precomputed_D"]

    print(f"\n--- Hard Reproduction Result ---")
    print(f"  Status: {result['status']}")
    print(f"  Fixes: {result['fix_iterations']}")
    print(f"  REI: {rei}")
    print(f"  Errors: {result.get('error_types', [])}")
    print(f"  Guardrail failures: {result.get('guardrail_failures', [])}")
    if result.get("env_info"):
        e = result["env_info"]
        print(f"  Environment: {e.get('python_version', 'unknown')}")
    if result.get("computed_D") is not None:
        print(f"  Computed D: {result['computed_D']:+.4f}")
        print(f"  Subgraph D: {result['subgraph_D']:+.4f}")
        print(f"  Precomputed D: {result['precomputed_D']:+.4f}")
        print(f"  n_i={result.get('n_i_parsed')}, n_j={result.get('n_j_parsed')}")

    # Save
    out = {k: str(v) if not isinstance(v, (int, float, list, dict, bool, type(None))) else v
           for k, v in result.items()}
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "hard_reproduction.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nSaved to {out_path}")

    return 0 if result["status"] != "FAILED" else 1


if __name__ == "__main__":
    sys.exit(main())
