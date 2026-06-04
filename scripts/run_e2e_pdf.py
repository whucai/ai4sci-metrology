#!/usr/bin/env python3
"""End-to-End PDF Pipeline: PDF → reproduce → verify → report.

Composes: MinerU → LLM extract → code gen → sandbox → self-correct → REI-c → report

Usage:
    python scripts/run_e2e_pdf.py path/to/paper.pdf
    python scripts/run_e2e_pdf.py path/to/paper.pdf --paper-id 2016964321
    python scripts/run_e2e_pdf.py path/to/paper.pdf --max-fixes 5 --output-dir refine-logs/
"""

import sys, os, re, json, tempfile, time, argparse, textwrap
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "8192")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.pdf_ingestion import parse_pdf_to_markdown
from src.sciscigpt_local.paper_ingestion import extract_paper_structure, format_analysis_plan
from src.sciscigpt_local.reproduction_pipeline import generate_reproduction_code
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS, compute_rei_c
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.report_generator import generate_report, save_report


def match_paper_to_sciscinet(paper_structure: dict, papers: pd.DataFrame) -> dict | None:
    """Try to find this paper in SciSciNet by DOI or title."""
    doi = paper_structure.get("doi", "")
    title = paper_structure.get("title", "")

    # Try DOI first
    if doi:
        doi_clean = doi.strip().lower().rstrip(".")
        for col in ["doi", "paper_id"]:
            if col in papers.columns:
                matches = papers[papers[col].astype(str).str.lower() == doi_clean]
                if len(matches) > 0:
                    row = matches.iloc[0]
                    return {
                        "paper_id": int(row["paper_id"]),
                        "title": str(row.get("title", title)),
                        "disruption_score": float(row.get("disruption_score", np.nan)),
                        "citation_count": int(row.get("citation_count", 0)),
                        "year": int(row.get("year", 0)),
                        "match_method": f"DOI ({col})",
                    }

    # Try title substring
    if title and len(title) > 20:
        title_clean = re.sub(r"[^a-z0-9\s]", "", title.lower())
        words = [w for w in title_clean.split() if len(w) > 3]
        if len(words) >= 3:
            pattern = " ".join(words[:6])
            for _, row in papers.iterrows():
                paper_title = str(row.get("title", "")).lower()
                if pattern in paper_title:
                    return {
                        "paper_id": int(row["paper_id"]),
                        "title": str(row.get("title", title)),
                        "disruption_score": float(row.get("disruption_score", np.nan)),
                        "citation_count": int(row.get("citation_count", 0)),
                        "year": int(row.get("year", 0)),
                        "match_method": "title substring",
                    }

    return None


def compute_paper_d_index(paper_id: int, pc: pd.DataFrame) -> dict | None:
    """Compute D-index ground truth from SciSciNet citation data."""
    refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
    citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
    if len(refs) == 0 or len(citers) == 0:
        return None

    ref_set = set(refs)
    n_i, n_j = 0, 0
    for cid in citers:
        citer_refs = set(pc[pc["citing_paper_id"] == cid]["cited_paper_id"].values)
        if citer_refs & ref_set:
            n_j += 1
        else:
            n_i += 1
    denom = n_i + n_j
    D = (n_i - n_j) / denom if denom > 0 else 0.0
    return {"D_index": round(D, 6), "n_i": n_i, "n_j": n_j, "n_refs": len(refs), "n_citers": len(citers)}


def extract_code(text: str) -> str:
    """Extract Python code from LLM response."""
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
    """Self-correction: fix broken code."""
    strategies = [
        "Fix import errors. Use only pandas and numpy.",
        "Check column names match the CSV files exactly.",
        "Simplify the computation logic.",
        "Rewrite as minimal script. MUST print D_INDEX = <value>.",
    ]
    idx = min(attempt, len(strategies) - 1)
    prompt = f"""Fix this Python code. {strategies[idx]}

Error: {error[:500]}

Code:
```python
{code[:1200]}
```

Output ONLY the fixed Python code."""

    response = llm.invoke([{"role": "user", "content": prompt}])
    return extract_code(str(response.content))


def parse_d_index(stdout: str) -> float | None:
    """Extract D-index from stdout."""
    m = re.search(r"D_INDEX\s*=\s*([-+]?\d*\.?\d+(?:[eE][-+]?\d+)?)", stdout)
    if m:
        return float(m.group(1))
    return None


def run_e2e_pdf(
    pdf_path: str,
    llm,
    papers: pd.DataFrame,
    pc: pd.DataFrame,
    max_fixes: int = 5,
    output_dir: str | None = None,
) -> dict:
    """Run complete PDF-to-report pipeline.

    Stages:
      1. MinerU: PDF → Markdown
      2. LLM: Markdown → structured JSON (paper_ingestion)
      3. Match paper to SciSciNet (DOI/title lookup)
      4. LLM: structure → Python reproduction code
      5. Sandbox: execute + self-correct
      6. REI-c: compute correctness-aware REI
      7. Report: generate Markdown report
    """
    output_dir = output_dir or str(Path(__file__).resolve().parent.parent / "refine-logs")
    result = {
        "pdf_path": str(pdf_path),
        "stages": {},
        "status": "PENDING",
        "error_types": [],
    }

    # Stage 1: PDF → Markdown
    print("\n[Stage 1/7] Parsing PDF with MinerU...", flush=True)
    t0 = time.time()
    try:
        parsed = parse_pdf_to_markdown(pdf_path)
        markdown = parsed["markdown"]
        result["stages"]["pdf_parse"] = {
            "status": "OK",
            "pages": parsed.get("pages", 0),
            "chars": len(markdown),
            "time": round(time.time() - t0, 1),
        }
        print(f"  {parsed.get('pages', '?')} pages, {len(markdown):,} chars ({result['stages']['pdf_parse']['time']}s)")
    except Exception as e:
        result["stages"]["pdf_parse"] = {"status": "FAILED", "error": str(e)[:200]}
        result["status"] = "ERROR"
        return result

    # Stage 2: LLM structured extraction
    print("[Stage 2/7] Extracting paper structure via LLM...", flush=True)
    t0 = time.time()
    try:
        structure = extract_paper_structure(markdown, llm)
        result["stages"]["extraction"] = {
            "status": "OK",
            "title": structure.get("title", "")[:200],
            "n_methods": len(structure.get("methods", [])),
            "n_datasets": len(structure.get("datasets", [])),
            "n_analysis_steps": len(structure.get("analysis_steps", [])),
            "dependencies": structure.get("dependencies", [])[:10],
            "time": round(time.time() - t0, 1),
        }
        ex = result["stages"]["extraction"]
        print(f"  Title: {ex['title'][:80]}")
        print(f"  Methods: {ex['n_methods']}, Datasets: {ex['n_datasets']}, Steps: {ex['n_analysis_steps']}")
        print(f"  Dependencies: {ex['dependencies']}")
    except Exception as e:
        result["stages"]["extraction"] = {"status": "FAILED", "error": str(e)[:200]}
        result["status"] = "ERROR"
        return result

    # Stage 3: Match to SciSciNet
    print("[Stage 3/7] Matching paper to SciSciNet...", flush=True)
    match = match_paper_to_sciscinet(structure, papers)
    if match:
        result["sciscinet_match"] = match
        print(f"  Matched: paper_id={match['paper_id']} ({match['match_method']})")
        print(f"  Disruption score: {match.get('disruption_score', 'N/A')}")
    else:
        print("  No SciSciNet match found — will skip ground truth comparison")

    # Stage 4: Generate reproduction code
    print("[Stage 4/7] Generating reproduction code via LLM...", flush=True)
    t0 = time.time()
    try:
        data_context = {
            "tables": ["papers (111K rows)", "paper_citations (78M edges)"],
            "available_via": "SciSciNet — pre-loaded as CSV files in /tmp/",
        }

        # Write data files for the code
        if match:
            paper_id = match["paper_id"]
            refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
            citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
            refs_path = tempfile.mktemp(suffix="_refs.csv")
            cites_path = tempfile.mktemp(suffix="_cites.csv")
            pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
            citer_cites = pc[pc["citing_paper_id"].isin(citers)][
                ["citing_paper_id", "cited_paper_id"]
            ].head(2000)
            citer_cites.to_csv(cites_path, index=False)

            # Custom prompt with real data paths
            prompt = f"""Write Python code to compute the Disruption Index D for paper {paper_id}.

Data files:
- refs CSV at '{refs_path}': columns reference_id — papers cited BY paper {paper_id}
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

CRITICAL: The cites CSV contains all citation edges FROM papers that cite paper {paper_id}.
Every unique citing_paper_id in this file is a paper that cites paper {paper_id}.
For each citing paper, the CSV lists ALL papers it cites (not just paper {paper_id}).

Formula: D = (n_i - n_j) / (n_i + n_j)
- n_i = citing papers that cite paper {paper_id} but NOT its references
- n_j = citing papers that cite BOTH paper {paper_id} AND its references

Paper: {structure.get('title', 'Unknown')[:200]}
Year: {match.get('year', 'Unknown')}

Use pandas. Print: D_INDEX = <value>, n_i = <value>, n_j = <value>
Output ONLY Python code."""

            response = llm.invoke([{"role": "user", "content": prompt}])
            code = extract_code(str(response.content))
        else:
            # Generate code based on paper structure alone (no SciSciNet match)
            code = generate_reproduction_code(structure, data_context, llm)

        result["stages"]["code_gen"] = {
            "status": "OK",
            "code": code[:3000],
            "code_lines": len(code.split("\n")),
            "time": round(time.time() - t0, 1),
        }
        print(f"  Generated {len(code.split(chr(10)))} lines of Python")
    except Exception as e:
        result["stages"]["code_gen"] = {"status": "FAILED", "error": str(e)[:200]}
        result["status"] = "ERROR"
        return result

    # Stage 5-6: Execute with self-correction
    print(f"[Stage 5/7] Executing + self-correcting (max {max_fixes} fixes)...", flush=True)
    t0 = time.time()
    error_types = []
    fix_count = 0
    final_code = code
    execution_result = None

    for attempt in range(max_fixes + 1):
        exec_result = execute_python(final_code, timeout=120)
        stderr = exec_result.get("stderr", "")
        has_error = any(p in stderr for p in [
            "Traceback", "Error:", "Exception", "ModuleNotFound",
            "SyntaxError", "NameError", "TypeError", "ValueError",
            "KeyError", "IndexError", "AttributeError", "ImportError",
        ])

        if exec_result["exit_code"] == 0 and not has_error:
            execution_result = exec_result
            break

        error_text = stderr or exec_result.get("stdout", "")
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        if attempt < max_fixes:
            final_code = fix_code(llm, final_code, error_text, attempt)

    result["stages"]["execution"] = {
        "status": "OK" if execution_result is not None else "FAILED",
        "fix_count": fix_count,
        "error_types": error_types,
        "time": round(time.time() - t0, 1),
    }
    status = "✓" if execution_result else "✗"
    print(f"  {status} Fixes: {fix_count}, Errors: {error_types}")

    # Stage 7: REI-c and report
    print("[Stage 6/7] Computing REI-c...", flush=True)
    if execution_result:
        computed_D = parse_d_index(execution_result["stdout"])

        if match:
            gt_d = compute_paper_d_index(match["paper_id"], pc)
            if gt_d and computed_D is not None:
                weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0
                rei_c, c_ratio, silent = compute_rei_c(rei, gt_d["D_index"], computed_D)

                result["metrics"] = {
                    "computed_D": computed_D,
                    "ground_truth_D": gt_d["D_index"],
                    "d_deviation": round(abs(computed_D - gt_d["D_index"]), 6),
                    "REI": rei,
                    "REI_c": rei_c,
                    "correctness_ratio": c_ratio,
                    "is_silent_failure": silent,
                }
                print(f"  D: computed={computed_D:+.4f}, gt={gt_d['D_index']:+.4f}")
                print(f"  REI={rei}, REI-c={rei_c}" + (" ⚠️SILENT FAILURE" if silent else ""))
            else:
                result["metrics"] = {"computed_D": computed_D, "ground_truth_D": None}
                print(f"  D: computed={computed_D:+.4f}, no ground truth available")
        else:
            result["metrics"] = {"computed_D": computed_D, "ground_truth_D": None}
            print(f"  D: computed={computed_D:+.4f}, no SciSciNet match")
    else:
        weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
        rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0
        result["metrics"] = {"REI": rei, "computed_D": None}
        print(f"  All fixes exhausted. REI={rei}")

    result["status"] = "SUCCESS" if execution_result else "FAILED"
    result["REI"] = result["metrics"].get("REI", 100.0)
    result["REI_c"] = result["metrics"].get("REI_c", result["REI"])
    result["error_types"] = error_types
    result["fix_count"] = fix_count

    # Stage 7: Generate report
    print("[Stage 7/7] Generating report...", flush=True)
    report_result = {
        "status": result["status"],
        "REI": result["REI"],
        "REI_c": result.get("REI_c"),
        "fix_iterations": fix_count,
        "error_types": error_types,
        "paper_title": match.get("title", structure.get("title", "Unknown")) if match else structure.get("title", "Unknown"),
        "parsed_metrics": {"D_index": result["metrics"].get("computed_D")},
        "ground_truth_D": result["metrics"].get("ground_truth_D"),
        "is_silent_failure": result["metrics"].get("is_silent_failure", False),
        "stages": result["stages"],
    }

    paper_info = {
        "title": match.get("title", "") if match else structure.get("title", ""),
        "doi": structure.get("doi", ""),
    }

    report_text = generate_report(report_result, paper_info)
    report_path = save_report(report_text, output_dir)
    result["report_path"] = report_path
    print(f"  Report: {report_path}")

    # Save full result
    result_path = os.path.join(output_dir, f"e2e_result_{int(time.time())}.json")
    with open(result_path, "w") as f:
        json.dump(result, f, indent=2, default=str)
    result["result_path"] = result_path
    print(f"  Full result: {result_path}")

    return result


def main():
    parser = argparse.ArgumentParser(description="E2E PDF → Reproduce → Verify → Report")
    parser.add_argument("pdf_path", help="Path to paper PDF")
    parser.add_argument("--paper-id", type=int, default=None,
                        help="SciSciNet paper ID (skip matching)")
    parser.add_argument("--max-fixes", type=int, default=5,
                        help="Max self-correction attempts")
    parser.add_argument("--output-dir", default=None,
                        help="Output directory for reports")
    args = parser.parse_args()

    pdf_path = args.pdf_path
    if not os.path.exists(pdf_path):
        print(f"Error: PDF not found: {pdf_path}")
        return 1

    print("=" * 70)
    print("E2E PDF PIPELINE: PDF → Reproduce → Verify → Report")
    print("=" * 70)
    print(f"  PDF: {pdf_path}")

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}")

    print("  Loading SciSciNet...", end=" ", flush=True)
    papers = load_table("papers")
    pc = load_table("paper_citations")
    print(f"OK ({len(papers):,} papers, {len(pc):,} citations)")

    result = run_e2e_pdf(pdf_path, llm, papers, pc, args.max_fixes, args.output_dir)

    print("\n" + "=" * 70)
    print(f"PIPELINE COMPLETE — Status: {result['status']}")
    if result.get("REI") is not None:
        print(f"  REI: {result['REI']}, REI-c: {result.get('REI_c', 'N/A')}")
    if result.get("report_path"):
        print(f"  Report: {result['report_path']}")
    print("=" * 70)

    return 0 if result["status"] == "SUCCESS" else 1


if __name__ == "__main__":
    sys.exit(main())
