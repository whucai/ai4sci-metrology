#!/usr/bin/env python3
"""M3: Self-Correction Loop + REI — Fast Local Version.

Uses pre-computed SciSciNet data in the sandbox so LLM-generated code
doesn't depend on external API calls. Compares against known ground truth.

Test task: given a CSV with (paper_id, reference_count, citation_count),
compute the mean citation-to-reference ratio, stratified by team size.

LLM gets: CSV data + formula → generates code → execute → compare → fix → REI.
"""

from __future__ import annotations

import sys, os, json, re, time, tempfile
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "2048")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS, FIX_STRATEGIES
from src.sciscigpt_local.sciscinet_connector import load_papers_sample


def prepare_test_data(n_papers: int = 200) -> tuple[str, dict[str, float]]:
    """Create a CSV test file from SciSciNet and compute ground truth."""
    print("  Preparing test data from SciSciNet...")
    papers = load_papers_sample(n_shards=1)
    df = papers[["paper_id", "year", "author_count", "citation_count",
                  "reference_count", "disruption_score"]].dropna().copy()
    sample = df.sample(min(n_papers, len(df)), random_state=42)

    # Ground truth: mean citation-to-reference ratio by team size
    small = sample[sample["author_count"] <= 3]
    large = sample[sample["author_count"] >= 4]

    ground_truth = {
        "small_mean_ratio": round(small["citation_count"].mean() / max(small["reference_count"].mean(), 1), 4),
        "large_mean_ratio": round(large["citation_count"].mean() / max(large["reference_count"].mean(), 1), 4),
        "small_mean_cites": round(small["citation_count"].mean(), 2),
        "large_mean_cites": round(large["citation_count"].mean(), 2),
        "small_count": len(small),
        "large_count": len(large),
        "overall_mean_disruption": round(sample["disruption_score"].mean(), 5),
    }

    # Write CSV
    csv_path = tempfile.mktemp(suffix=".csv")
    sample.to_csv(csv_path, index=False)
    print(f"  Data: {len(sample)} papers, {len(sample.columns)} cols → {csv_path}")
    return csv_path, ground_truth


def generate_code(llm, csv_path: str) -> str:
    """Ask LLM to generate analysis code."""
    prompt = f"""Write Python code to analyze the CSV file at '{csv_path}'.

The CSV has columns: paper_id, year, author_count, citation_count, reference_count, disruption_score.

Tasks:
1. Load the CSV with pandas
2. Split papers into small teams (author_count <= 3) and large teams (author_count >= 4)
3. For each group, compute:
   - mean citation_count
   - mean reference_count
   - citation-to-reference ratio = mean(citation_count) / mean(reference_count)
4. Also compute the overall mean disruption_score
5. Print results as:
   small_mean_ratio = <value>
   large_mean_ratio = <value>
   small_mean_cites = <value>
   large_mean_cites = <value>
   small_count = <value>
   large_count = <value>
   overall_mean_disruption = <value>

Use ONLY pandas. Print each result on its own line.
Output ONLY the Python code in a ```python block, no explanation."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    # Extract code
    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        code = match.group(1).strip()
    else:
        # Take everything that looks like code
        lines = []
        for line in text.split("\n"):
            s = line.strip()
            if not s or s.startswith("#") or s.startswith("import") or s.startswith("from") or \
               s.startswith("df") or s.startswith("small") or s.startswith("large") or \
               s.startswith("print") or s.startswith("ratio") or s.startswith("overall"):
                lines.append(line)
        code = "\n".join(lines).strip()
        if not code:
            code = text.strip()

    # Strip residual thinking tags
    code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL).strip()
    return code


def fix_code(llm, code: str, error: str, error_cat: str, attempt: int) -> str:
    """Apply fix strategy based on error and attempt number."""
    idx = min(attempt, len(FIX_STRATEGIES) - 1)
    strategy = FIX_STRATEGIES[idx]

    prompt = f"""{strategy['prompt']}

Error ({error_cat}):
{error[:600]}

Current code:
```python
{code[:1500]}
```

Output ONLY the fixed code in a ```python block."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    text = str(response.content)
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)

    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    return text.strip()


def parse_output(stdout: str) -> dict[str, float]:
    """Parse metric values from stdout."""
    metrics = {}
    for line in stdout.split("\n"):
        m = re.match(r"(\w+)\s*[=:]\s*([-+]?\d*\.?\d+)", line.strip())
        if m:
            try:
                metrics[m.group(1)] = float(m.group(2))
            except ValueError:
                pass
    return metrics


def run_single_rei(llm, csv_path: str, gt: dict, max_fixes: int = 5) -> dict:
    """Run one REI measurement cycle."""
    fix_count = 0
    errors = []

    # Generate code
    code = generate_code(llm, csv_path)

    # Execute with self-correction
    for attempt in range(max_fixes + 1):
        # Strip thinking tags if present
        if "<think>" in code or "</think>" in code:
            code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)

        result = execute_python(code, timeout=60)

        stderr = result.get("stderr", "")
        has_error = any(p in stderr for p in [
            "Traceback", "Error:", "Exception", "ModuleNotFound",
            "SyntaxError", "NameError", "TypeError", "ValueError",
            "KeyError", "IndexError", "AttributeError", "FileNotFound",
        ])

        if result["exit_code"] == 0 and not has_error:
            parsed = parse_output(result["stdout"])
            # Check if we got meaningful results
            if len(parsed) >= 3:
                # Compare with ground truth
                comparisons = {}
                for k in ["small_mean_ratio", "large_mean_ratio", "overall_mean_disruption"]:
                    if k in parsed and k in gt:
                        ev = gt[k]
                        rv = parsed[k]
                        dev = abs(rv - ev) / max(abs(ev), 0.001)
                        comparisons[k] = {
                            "expected": ev,
                            "reproduced": rv,
                            "deviation": round(dev, 4),
                            "match": dev <= 0.01,
                        }

                match_count = sum(1 for c in comparisons.values() if c["match"])
                all_match = match_count == len(comparisons) and len(comparisons) >= 2

                return {
                    "status": "SUCCESS" if all_match else "PARTIAL",
                    "fix_iterations": fix_count,
                    "errors": errors,
                    "comparisons": comparisons,
                    "match_count": match_count,
                    "match_total": len(comparisons),
                    "code_final": code,
                    "stdout": result["stdout"][:1000],
                }

        # Failure — classify and fix
        error_text = stderr or result.get("stdout", "")
        error_cat = classify_error(error_text)
        errors.append({"iteration": attempt + 1, "category": error_cat, "error": error_text[:300]})
        fix_count += 1

        if attempt < max_fixes:
            code = fix_code(llm, code, error_text, error_cat, attempt)

    return {
        "status": "FAILED",
        "fix_iterations": fix_count,
        "errors": errors,
        "comparisons": {},
        "match_count": 0,
        "match_total": 0,
        "code_final": code,
        "stdout": "",
    }


def compute_rei(status: str, fix_count: int, errors: list[dict]) -> float:
    """Compute REI from results."""
    if status == "FAILED":
        return 100.0
    if fix_count == 0:
        return 0.0
    weights = sum(ERROR_WEIGHTS.get(e["category"], 3) for e in errors)
    return round(weights / (fix_count + 1), 4)


def main():
    print("=" * 70)
    print("M3: Self-Correction Loop + REI (Fast Local Version)")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    # Prepare test data
    csv_path, gt = prepare_test_data(200)
    print(f"  Ground truth: {json.dumps(gt, indent=2)}\n")

    # Run 3 trials with slight variations
    trials = []
    for i in range(3):
        label = ["Baseline", "Malformed prompt", "Missing import"][i] if i < 3 else f"Trial {i+1}"
        print(f"--- Trial {i+1}/3: {label} ---")

        # On trial 2, truncate CSV path to force error
        use_path = csv_path
        if i == 1:
            use_path = csv_path + "x"  # intentional wrong path — forces FileNotFoundError

        result = run_single_rei(llm, use_path, gt, max_fixes=3)
        rei = compute_rei(result["status"], result["fix_iterations"], result["errors"])

        print(f"  Status: {result['status']}")
        print(f"  Fixes: {result['fix_iterations']}")
        print(f"  REI: {rei}")
        print(f"  Matches: {result['match_count']}/{result['match_total']}")

        if result["errors"]:
            for e in result["errors"]:
                print(f"    [{e['category']}] {e['error'][:100]}")

        if result.get("comparisons"):
            for k, v in result["comparisons"].items():
                icon = "✓" if v["match"] else "✗"
                print(f"    {icon} {k}: expected={v['expected']}, got={v['reproduced']}, dev={v['deviation']}")

        trials.append({"label": label, "status": result["status"], "REI": rei,
                        "fixes": result["fix_iterations"], "errors": result["errors"]})
        print()

    # Summary
    print("=" * 70)
    print("M3 SUMMARY")
    print("=" * 70)
    successes = [t for t in trials if t["status"] in ("SUCCESS", "PARTIAL")]
    print(f"  Trials: {len(trials)}")
    print(f"  Successful/Partial: {len(successes)}/{len(trials)}")
    if successes:
        reis = [t["REI"] for t in successes]
        print(f"  Mean REI: {np.mean(reis):.4f}")
        print(f"  REI range: [{min(reis):.4f}, {max(reis):.4f}]")

    for t in trials:
        icons = {"SUCCESS": "✓", "PARTIAL": "~", "FAILED": "✗"}
        print(f"  {icons.get(t['status'], '?')} {t['label']:20s} REI={t['REI']:.4f}  fixes={t['fixes']}")

    # Save
    out = {
        "trials": [{k: str(v) if not isinstance(v, (int, float, list, dict, bool, type(None))) else v
                     for k, v in t.items()} for t in trials],
        "ground_truth": gt,
        "data_csv": csv_path,
    }
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "m3_results.json"
    out_path.write_text(json.dumps(out, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return 0 if len(successes) >= 2 else 1


if __name__ == "__main__":
    sys.exit(main())
