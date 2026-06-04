#!/usr/bin/env python3
"""Non-D-index reproduction: Field-Year Trend Analysis.

Reproduces the claim "disruption is declining over time within fields"
by having the LLM compute field-normalized disruption trends from raw CSVs.
This is a DIFFERENT task from D-index computation, demonstrating generality.
"""
import sys, os, re, json, tempfile
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
from src.sciscigpt_local.reproduction_pipeline import validate_generated_code
from src.sciscigpt_local.sciscinet_connector import load_table


def prepare_trend_data(papers, paper_fields, fields, n_fields=10) -> tuple[str, str, dict]:
    """Prepare CSV with paper-level field+year+disruption data for trend analysis."""
    # Sample fields
    sample_fields = fields.sample(min(n_fields, len(fields)), random_state=42)
    field_ids = sample_fields["field_id"].values

    pf = paper_fields[paper_fields["field_id"].isin(field_ids)]
    pf = pf.merge(papers[["paper_id", "year", "disruption_score", "citation_count"]],
                  on="paper_id", how="inner")
    pf = pf.dropna(subset=["disruption_score", "year"])
    pf["year"] = pf["year"].astype(int)
    pf = pf[(pf["year"] >= 1970) & (pf["year"] <= 2010)]
    pf = pf.sample(min(2000, len(pf)), random_state=42)

    csv_path = tempfile.mktemp(suffix="_trend_data.csv")
    pf[["paper_id", "field_id", "year", "disruption_score"]].to_csv(csv_path, index=False)

    # Field names
    fields_csv = tempfile.mktemp(suffix="_fields.csv")
    fields[fields["field_id"].isin(field_ids)][["field_id", "field_name"]].to_csv(
        fields_csv, index=False)

    # Ground truth: compute Spearman rho for disruption vs year
    from scipy import stats
    pf["year"] = pf["year"].astype(int)
    yearly = pf.groupby("year")["disruption_score"].mean()
    rho, pval = stats.spearmanr(yearly.index, yearly.values)

    gt = {
        "n_papers": len(pf),
        "n_fields": len(field_ids),
        "year_range": f"{pf['year'].min()}-{pf['year'].max()}",
        "spearman_rho": round(rho, 4),
        "spearman_p": round(pval, 6),
        "mean_D_early": round(float(pf[pf["year"] < 1990]["disruption_score"].mean()), 6),
        "mean_D_late": round(float(pf[pf["year"] >= 1990]["disruption_score"].mean()), 6),
    }
    return csv_path, fields_csv, gt


def generate_trend_code(llm, data_csv: str, fields_csv: str) -> str:
    """Generate code to analyze disruption trend over time."""
    prompt = f"""You are given two CSV files:

1. Data: '{data_csv}' — columns: paper_id, field_id, year, disruption_score
   Each row is a paper with its disruption score and publication year.

2. Fields: '{fields_csv}' — columns: field_id, field_name
   Field name lookup table.

Task: Analyze whether disruption scores are declining over time.

Analysis steps:
1. Load both CSVs with pandas
2. Compute mean disruption_score per year (across all fields)
3. Compute the Spearman rank correlation between year and mean disruption
4. Compute mean disruption for early period (<1990) vs late period (>=1990)
5. Print results in exactly this format:
   SPEARMAN_RHO = <value>
   SPEARMAN_P = <value>
   MEAN_D_EARLY = <value>
   MEAN_D_LATE = <value>
   N_PAPERS = <value>

Use pandas and scipy.stats.spearmanr. Handle edge cases.
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


def parse_trend_output(stdout: str) -> dict:
    """Parse trend analysis output."""
    result = {}
    patterns = [
        (r"SPEARMAN_RHO\s*=\s*([-+]?\d*\.?\d+)", "spearman_rho"),
        (r"SPEARMAN_P\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", "spearman_p"),
        (r"MEAN_D_EARLY\s*=\s*([-+]?\d*\.?\d+)", "mean_D_early"),
        (r"MEAN_D_LATE\s*=\s*([-+]?\d*\.?\d+)", "mean_D_late"),
        (r"N_PAPERS\s*=\s*(\d+)", "n_papers"),
    ]
    for pat, key in patterns:
        m = re.search(pat, stdout, re.IGNORECASE)
        if m:
            try:
                result[key] = float(m.group(1))
            except ValueError:
                pass
    return result


def main():
    print("=" * 70)
    print("NON-D-INDEX REPRODUCTION: Field-Year Trend Analysis")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}\n")

    print("Loading SciSciNet...")
    papers = load_table("papers")
    paper_fields = load_table("paper_fields")
    fields = load_table("fields")

    print("Preparing trend data...")
    data_csv, fields_csv, gt = prepare_trend_data(papers, paper_fields, fields)
    print(f"  Data: {data_csv} ({gt['n_papers']} papers, {gt['n_fields']} fields)")
    print(f"  Ground truth: ρ={gt['spearman_rho']:.4f} (p={gt['spearman_p']:.6f})")
    print(f"  Mean D: early={gt['mean_D_early']:.4f}, late={gt['mean_D_late']:.4f}\n")

    print("--- Running Trend Reproduction ---")
    code = generate_trend_code(llm, data_csv, fields_csv)
    guard = validate_generated_code(code)
    print(f"  Guardrail: valid={guard['valid']}, failures={guard['failures']}")
    print(f"  Code: {len(code)} chars, {len(code.split(chr(10)))} lines")

    if not guard["valid"]:
        code = re.sub(r"<think>.*?</think>", "", code, flags=re.DOTALL)
        guard2 = validate_generated_code(code)
        print(f"  After strip: valid={guard2['valid']}")

    max_fixes = 4
    fix_count = 0
    error_types = []

    for attempt in range(max_fixes + 1):
        result = execute_python(code, timeout=90)

        stderr = result.get("stderr", "")
        has_error = any(p in stderr for p in [
            "Traceback", "Error:", "Exception", "ModuleNotFound",
            "SyntaxError", "NameError", "TypeError", "ValueError",
            "KeyError", "IndexError", "AttributeError", "FileNotFound",
        ])

        if result["exit_code"] == 0 and not has_error:
            parsed = parse_trend_output(result["stdout"])
            if "spearman_rho" in parsed:
                rho_gt = gt["spearman_rho"]
                rho_comp = parsed["spearman_rho"]
                rho_dev = abs(rho_comp - rho_gt) / max(abs(rho_gt), 0.001)

                status = "SUCCESS" if rho_dev < 0.2 else "PARTIAL"
                rei = (sum(ERROR_WEIGHTS.get(e, 3) for e in error_types) /
                       max(fix_count, 1)) if fix_count > 0 else 0.0

                print(f"\n  Status: {status}")
                print(f"  Computed ρ: {rho_comp:.4f} (GT: {rho_gt:.4f}, dev: {rho_dev:.4f})")
                print(f"  Computed early D: {parsed.get('mean_D_early', 'N/A')}")
                print(f"  Computed late D: {parsed.get('mean_D_late', 'N/A')}")
                print(f"  REI: {rei}, fixes: {fix_count}, errors: {error_types}")

                out = {
                    "status": status, "REI": rei,
                    "fix_iterations": fix_count, "error_types": error_types,
                    "computed_rho": parsed.get("spearman_rho"),
                    "gt_rho": rho_gt,
                    "computed_early_D": parsed.get("mean_D_early"),
                    "computed_late_D": parsed.get("mean_D_late"),
                    "gt_early_D": gt["mean_D_early"],
                    "gt_late_D": gt["mean_D_late"],
                    "task": "field_year_trend_analysis",
                }
                out_path = Path(__file__).resolve().parent.parent / "refine-logs" / "trend_reproduction.json"
                out_path.write_text(json.dumps(out, indent=2, default=str))
                print(f"  Saved to {out_path}")
                return 0 if status == "SUCCESS" else 1

        error_text = stderr or result.get("stdout", "")
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        print(f"  Fix attempt {fix_count}: {error_cat} — {error_text[:100]}")

        if attempt < max_fixes:
            strategies = [
                "Fix syntax errors or missing imports.",
                "Add error handling for missing columns, empty DataFrames.",
                "Simplify: just compute yearly means, scipy.stats.spearmanr.",
                "Rewrite minimal: groupby year, mean, then spearmanr.",
            ]
            idx = min(attempt, 3)
            fix_prompt = f"Fix this Python code. {strategies[idx]}\n\nError:\n{error_text[:600]}\n\nCode:\n```python\n{code[:1500]}\n```\n\nOutput ONLY the fixed Python code."
            response = llm.invoke([{"role": "user", "content": fix_prompt}])
            text = str(response.content)
            text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
            m = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
            code = m.group(1).strip() if m else text.strip()

    print(f"\n  FAILED after {fix_count} attempts")
    return 1


if __name__ == "__main__":
    sys.exit(main())
