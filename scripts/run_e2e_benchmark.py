#!/usr/bin/env python3
"""E2E Paper Reproduction Benchmark: LLM reads paper content → reproduces analysis.

Unlike the template benchmark (fixed prompt for all papers), this benchmark
provides each paper's actual title + abstract as context. The LLM must
understand the paper's topic and methodology to compute the relevant metric.

Pipeline conditions (ablations):
  - template:   Fixed prompt "compute D-index for paper X" (baseline)
  - abstract:   LLM reads paper title + abstract → computes metric (E2E-lite)
  - pdf:        PDF → MinerU → markdown → LLM reads → computes metric (full E2E)

Usage:
    python scripts/run_e2e_benchmark.py --condition abstract --n-papers 50
    python scripts/run_e2e_benchmark.py --condition template --n-papers 50
    python scripts/run_e2e_benchmark.py --condition pdf --pdf-dir data/pdfs/ --n-papers 20
    python scripts/run_e2e_benchmark.py --condition all --n-papers 30
"""

import sys, os, re, json, tempfile, time, argparse, textwrap
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "4096")
os.environ.setdefault("HF_HUB_OFFLINE", "1")

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS, compute_rei_c
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import (
    get_prompt, parse_metric_output, compute_ground_truth,
    get_primary_metric, get_required_tables, METRIC_CONFIGS,
)
from src.sciscigpt_local.pdf_ingestion import parse_pdf_to_markdown


# ── Prompt templates for each condition ──

TEMPLATE_PROMPT = """Write Python code to compute the Disruption Index D for paper {paper_id}.

Data files:
- refs CSV at '{refs_path}': columns reference_id — papers cited BY paper {paper_id}
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

CRITICAL: The cites CSV contains all citation edges FROM papers that cite paper {paper_id}.
Every unique citing_paper_id in this file is a paper that cites paper {paper_id}.
For each citing paper, the CSV lists ALL papers it cites (not just paper {paper_id}).

Formula: D = (n_i - n_j) / (n_i + n_j)
- n_i = citing papers that cite paper {paper_id} but NOT its references
- n_j = citing papers that cite BOTH paper {paper_id} AND at least one of its references

Algorithm:
1. Read refs CSV → set R (paper {paper_id}'s references)
2. Read cites CSV → group by citing_paper_id, collect each citer's cited papers
3. For each citing paper, check if its cited papers overlap with R
4. n_i = citing papers with NO overlap with R
5. n_j = citing papers WITH overlap with R
6. D = (n_i - n_j) / (n_i + n_j)

Use pandas. Print: D_INDEX = <value>, n_i = <value>, n_j = <value>
Output ONLY Python code."""


ABSTRACT_PROMPT = """You are reproducing a scientific analysis. Read the paper information below,
then write Python code to compute the metric.

=== PAPER INFORMATION ===
Title: {title}
Year: {year}
Journal: {journal}
Abstract: {abstract}

=== TASK ===
This paper studies disruption in science. Compute its Disruption Index D.

Data files:
- refs CSV at '{refs_path}': columns reference_id — papers cited BY paper {paper_id}
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

CRITICAL: The cites CSV contains all citation edges FROM papers that cite paper {paper_id}.
Every unique citing_paper_id in this file is a paper that cites paper {paper_id}.

Formula: D = (n_i - n_j) / (n_i + n_j)
- n_i = citing papers that cite paper {paper_id} but NOT its references
- n_j = citing papers that cite BOTH paper {paper_id} AND at least one of its references

Algorithm:
1. Read refs CSV → set R = paper {paper_id}'s references
2. Read cites CSV → group by citing_paper_id, collect each citer's cited papers
3. For each citing paper, check if its cited papers overlap with R
4. n_i = citing papers with NO overlap with R, n_j = WITH overlap with R
5. D = (n_i - n_j) / (n_i + n_j)

Use pandas. Print: D_INDEX = <value>, n_i = <value>, n_j = <value>
Output ONLY Python code."""


PDF_PROMPT = """You are reproducing a scientific analysis. Below is the full text of a paper
(extracted from PDF). Read the paper, understand its methodology, then write Python code
to compute the metric described in the paper.

=== PAPER FULL TEXT (Markdown) ===
{markdown}

=== TASK ===
Based on the paper's methodology, compute its Disruption Index D.

Paper ID: {paper_id}
Year: {year}

Data files:
- refs CSV at '{refs_path}': columns reference_id — papers cited BY paper {paper_id}
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

CRITICAL: The cites CSV contains all citation edges FROM papers that cite paper {paper_id}.
Every unique citing_paper_id in this file is a paper that cites paper {paper_id}.

Formula: D = (n_i - n_j) / (n_i + n_j)
- n_i = citing papers that cite paper {paper_id} but NOT its references
- n_j = citing papers that cite BOTH paper {paper_id} AND at least one of its references

Algorithm:
1. Read refs CSV → set R = paper {paper_id}'s references
2. Read cites CSV → group by citing_paper_id, collect each citer's cited papers
3. For each citing paper, check if its cited papers overlap with R
4. n_i = citing papers with NO overlap with R, n_j = WITH overlap with R
5. D = (n_i - n_j) / (n_i + n_j)

Use pandas. Print: D_INDEX = <value>, n_i = <value>, n_j = <value>
Output ONLY Python code."""


# ── Paper sampling ──

def sample_papers_for_benchmark(papers, pc, n, target_journals=None, seed=42):
    """Sample papers with journal stratification.

    Args:
        papers: SciSciNet papers DataFrame.
        pc: paper_citations DataFrame.
        n: Total papers to sample.
        target_journals: List of journal name patterns to prioritize.
        seed: Random seed.

    Returns:
        List of paper_id.
    """
    rng = np.random.default_rng(seed)
    pc_pids = set(pc["citing_paper_id"].unique()) & set(pc["cited_paper_id"].unique())
    valid = papers[papers["paper_id"].isin(pc_pids)].copy()

    # Ensure required columns
    for col in ["title", "abstract", "journal_name"]:
        if col not in valid.columns:
            valid[col] = ""

    sampled = []

    # Priority 1: Target journals
    if target_journals:
        for pattern in target_journals:
            pool = valid[valid["journal_name"].str.contains(pattern, case=False, na=False)]
            k = min(n // len(target_journals), len(pool))
            if k > 0:
                chosen = pool.sample(k, random_state=seed)
                sampled.extend(chosen["paper_id"].tolist())

    # Priority 2: Top journals (Science, Nature, PNAS, PLOS ONE, etc.)
    top_journals = ["Science", "Nature", "PNAS", "PLOS ONE", "Physical Review",
                    "Journal of", "Proceedings of"]
    remaining_n = n - len(sampled)
    if remaining_n > 0:
        for pattern in top_journals:
            pool = valid[
                valid["journal_name"].str.contains(pattern, case=False, na=False) &
                ~valid["paper_id"].isin(sampled)
            ]
            k = min(remaining_n // len(top_journals), len(pool))
            if k > 0:
                chosen = pool.sample(k, random_state=seed + 1)
                sampled.extend(chosen["paper_id"].tolist())

    # Priority 3: Fill remaining with random papers
    remaining_n = n - len(sampled)
    if remaining_n > 0:
        pool = valid[~valid["paper_id"].isin(sampled)]
        if len(pool) > 0:
            chosen = pool.sample(min(remaining_n, len(pool)), random_state=seed + 2)
            sampled.extend(chosen["paper_id"].tolist())

    return sampled[:n]


# ── Code extraction ──

def _extract_code(text: str) -> str:
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
        "Simplify the computation logic. Focus on correct D-index formula.",
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
    return _extract_code(str(response.content))


# ── Single paper reproduction ──

@dataclass
class E2EResult:
    paper_id: int
    condition: str  # "template", "abstract", "pdf"
    status: str  # "SUCCESS", "FAILED", "SKIPPED"
    rei: float = 0.0
    rei_c: float = 0.0
    computed_d: float | None = None
    gt_d: float | None = None
    is_silent_failure: bool = False
    error_types: list = field(default_factory=list)
    fix_count: int = 0
    paper_title: str = ""
    paper_journal: str = ""
    paper_year: int = 0
    extra: dict = field(default_factory=dict)


def reproduce_one_paper_e2e(
    llm,
    paper_row,
    pc: pd.DataFrame,
    condition: str = "abstract",
    max_fixes: int = 3,
    pdf_dir: str | None = None,
) -> E2EResult:
    """Run E2E reproduction for a single paper.

    Args:
        llm: LLM instance.
        paper_row: Row from papers DataFrame.
        pc: paper_citations DataFrame.
        condition: "template", "abstract", or "pdf".
        max_fixes: Max self-correction attempts.
        pdf_dir: Directory containing PDF files (for pdf condition).

    Returns:
        E2EResult dataclass.
    """
    paper_id = int(paper_row["paper_id"])
    title = str(paper_row.get("title", ""))
    journal = str(paper_row.get("journal_name", ""))
    year = int(paper_row.get("year", 0))
    abstract = str(paper_row.get("abstract", ""))
    doi = str(paper_row.get("doi", ""))

    # Compute ground truth
    full_papers = load_table("papers")
    gt_row = full_papers[full_papers["paper_id"] == paper_id]
    if len(gt_row) == 0:
        return E2EResult(paper_id=paper_id, condition=condition, status="SKIPPED")

    gt = compute_ground_truth("disruption", paper_id, full_papers, pc)
    if not gt or "D_index" not in gt:
        return E2EResult(paper_id=paper_id, condition=condition, status="SKIPPED")

    gt_d = gt["D_index"]

    # Prepare data files
    refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
    citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
    if len(refs) == 0 or len(citers) == 0:
        return E2EResult(paper_id=paper_id, condition=condition, status="SKIPPED",
                         paper_title=title[:100], paper_journal=journal, paper_year=year)

    refs_path = tempfile.mktemp(suffix="_refs.csv")
    cites_path = tempfile.mktemp(suffix="_cites.csv")
    pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
    citer_cites = pc[pc["citing_paper_id"].isin(citers)][
        ["citing_paper_id", "cited_paper_id"]
    ].head(5000)
    citer_cites.to_csv(cites_path, index=False)

    # Build prompt based on condition
    if condition == "template":
        prompt = TEMPLATE_PROMPT.format(
            paper_id=paper_id, refs_path=refs_path, cites_path=cites_path)
    elif condition == "abstract":
        prompt = ABSTRACT_PROMPT.format(
            title=title, year=year, journal=journal, abstract=abstract[:2000],
            paper_id=paper_id, refs_path=refs_path, cites_path=cites_path)
    elif condition == "pdf":
        # Try to find and parse PDF
        markdown = ""
        if pdf_dir:
            pdf_path = os.path.join(pdf_dir, f"{paper_id}.pdf")
            if not os.path.exists(pdf_path):
                # Try DOI-based filename
                for f in os.listdir(pdf_dir):
                    if str(paper_id) in f and f.endswith(".pdf"):
                        pdf_path = os.path.join(pdf_dir, f)
                        break
            if os.path.exists(pdf_path):
                try:
                    parsed = parse_pdf_to_markdown(pdf_path)
                    markdown = parsed.get("markdown", "")[:8000]
                except Exception:
                    pass
        if not markdown:
            # Fallback to abstract
            return reproduce_one_paper_e2e(
                llm, paper_row, pc, condition="abstract", max_fixes=max_fixes, pdf_dir=pdf_dir)
        prompt = PDF_PROMPT.format(
            markdown=markdown, paper_id=paper_id, year=year,
            refs_path=refs_path, cites_path=cites_path)
    else:
        raise ValueError(f"Unknown condition: {condition}")

    # Generate code
    response = llm.invoke([{"role": "user", "content": prompt}])
    code = _extract_code(str(response.content))

    # Execute with self-correction
    error_types = []
    fix_count = 0

    for attempt in range(max_fixes + 1):
        result = execute_python(code, timeout=60)
        stderr = result.get("stderr", "")
        stdout = result.get("stdout", "")

        # Only flag as error if exit_code != 0 or stderr contains an actual Python traceback
        has_traceback = "Traceback (most recent call last)" in stderr
        is_error = result["exit_code"] != 0 or has_traceback

        if not is_error:
            parsed = parse_metric_output(stdout, "disruption")
            if "D_index" in parsed:
                weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0
                computed_d = parsed["D_index"]
                rei_c, c_ratio, silent = compute_rei_c(rei, gt_d, computed_d)
                return E2EResult(
                    paper_id=paper_id, condition=condition, status="SUCCESS",
                    rei=rei, rei_c=rei_c, computed_d=computed_d, gt_d=gt_d,
                    is_silent_failure=silent, error_types=error_types, fix_count=fix_count,
                    paper_title=title[:100], paper_journal=journal, paper_year=year,
                    extra={"n_i": parsed.get("n_i"), "n_j": parsed.get("n_j"),
                           "gt_n_i": gt.get("n_i"), "gt_n_j": gt.get("n_j")},
                )
            if "D_INDEX" in stdout.upper():
                continue  # output has expected label but parser missed it; retry

        error_text = stderr or stdout
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        if attempt < max_fixes:
            code = fix_code(llm, code, error_text, attempt)

    # All fixes exhausted
    weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
    rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0
    return E2EResult(
        paper_id=paper_id, condition=condition, status="FAILED",
        rei=rei, rei_c=rei, gt_d=gt_d,
        error_types=error_types, fix_count=fix_count,
        paper_title=title[:100], paper_journal=journal, paper_year=year)


# ── Cross-condition comparison ──

def compare_conditions(results: dict[str, list[E2EResult]]) -> dict:
    """Compare benchmark results across conditions."""
    comparison = {}

    for condition, cond_results in results.items():
        ok = [r for r in cond_results if r.status == "SUCCESS"]
        silent = [r for r in ok if r.is_silent_failure]

        rei_vals = [r.rei for r in ok]
        rei_c_vals = [r.rei_c for r in ok]

        comparison[condition] = {
            "n_total": len(cond_results),
            "n_success": len(ok),
            "n_silent": len(silent),
            "success_rate": round(len(ok) / len(cond_results), 3) if cond_results else 0,
            "silent_rate": round(len(silent) / len(ok), 3) if ok else 0,
            "rei_mean": round(float(np.mean(rei_vals)), 3) if rei_vals else None,
            "rei_c_mean": round(float(np.mean(rei_c_vals)), 3) if rei_c_vals else None,
            "rei_median": round(float(np.median(rei_vals)), 3) if rei_vals else None,
        }

        # D-index deviation stats
        deviations = []
        for r in ok:
            if r.computed_d is not None and r.gt_d is not None:
                deviations.append(abs(r.computed_d - r.gt_d))
        if deviations:
            comparison[condition]["d_mean_abs_dev"] = round(float(np.mean(deviations)), 6)
            comparison[condition]["d_exact_match"] = sum(1 for d in deviations if d < 1e-6)

        # Error type distribution
        all_errors = []
        for r in cond_results:
            all_errors.extend(r.error_types)
        comparison[condition]["error_distribution"] = dict(Counter(all_errors))

    # Cross-condition: papers succeeded in all conditions
    if len(results) >= 2:
        conditions = list(results.keys())
        common_ok = set(r.paper_id for r in results[conditions[0]] if r.status == "SUCCESS")
        for c in conditions[1:]:
            common_ok &= set(r.paper_id for r in results[c] if r.status == "SUCCESS")
        comparison["papers_succeeded_in_all_conditions"] = len(common_ok)

    return comparison


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        description="E2E Paper Reproduction Benchmark (multi-condition)")
    parser.add_argument("--condition", default="abstract",
                        choices=["template", "abstract", "pdf", "all"],
                        help="Benchmark condition: template (baseline), abstract (E2E-lite), "
                             "pdf (full E2E), all (compare all three)")
    parser.add_argument("--n-papers", type=int, default=30,
                        help="Number of papers to benchmark")
    parser.add_argument("--max-fixes", type=int, default=3,
                        help="Max self-correction attempts")
    parser.add_argument("--pdf-dir", default=None,
                        help="Directory containing PDF files (for pdf condition)")
    parser.add_argument("--target-journals", nargs="*",
                        default=["Management Science", "Research Policy"],
                        help="Journal name patterns to prioritize")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None,
                        help="Output JSON path")

    args = parser.parse_args()

    print("=" * 70)
    print("E2E PAPER REPRODUCTION BENCHMARK")
    print(f"  Condition: {args.condition}, Papers: {args.n_papers}")
    if args.condition == "all":
        print(f"  Comparing: template vs abstract vs pdf")
    print("=" * 70)

    # Load LLM
    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}")

    # Load data
    print("  Loading SciSciNet...", end=" ", flush=True)
    papers = load_table("papers")
    pc = load_table("paper_citations")
    print(f"OK ({len(papers):,} papers, {len(pc):,} citations)")

    # Sample papers with journal priority
    print(f"\n  Sampling {args.n_papers} papers...")
    print(f"    Target journals: {args.target_journals}")
    paper_ids = sample_papers_for_benchmark(papers, pc, args.n_papers, args.target_journals, args.seed)

    # Count journal distribution
    sampled_papers = papers[papers["paper_id"].isin(paper_ids)]
    journal_counts = sampled_papers["journal_name"].value_counts()
    print(f"    Journal distribution:")
    for jn, cnt in journal_counts.head(10).items():
        print(f"      {jn}: {cnt}")

    # Determine which conditions to run
    conditions = [args.condition] if args.condition != "all" else ["template", "abstract", "pdf"]

    all_results = {}
    total_start = time.time()

    for condition in conditions:
        print(f"\n{'='*70}")
        print(f"CONDITION: {condition}")
        print(f"{'='*70}")

        cond_results = []
        cond_start = time.time()

        for i, pid in enumerate(paper_ids):
            elapsed = time.time() - cond_start
            eta = (elapsed / (i + 1)) * (len(paper_ids) - i - 1) if i > 0 else 0

            paper_row = papers[papers["paper_id"] == pid].iloc[0]
            journal = str(paper_row.get("journal_name", ""))
            title_short = str(paper_row.get("title", ""))[:60]

            print(f"  [{i+1}/{len(paper_ids)}] Paper {pid} ({title_short}...)",
                  end=" ", flush=True)

            r = reproduce_one_paper_e2e(
                llm, paper_row, pc, condition=condition,
                max_fixes=args.max_fixes, pdf_dir=args.pdf_dir)
            cond_results.append(r)

            icon = {"SUCCESS": "✓", "FAILED": "✗", "SKIPPED": "→"}.get(r.status, "?")
            print(f"{icon} REI={r.rei}" +
                  (" ⚠️" if r.is_silent_failure else "") +
                  f" [ETA: {eta:.0f}s]", flush=True)

        cond_time = time.time() - cond_start
        ok = [r for r in cond_results if r.status == "SUCCESS"]
        silent = [r for r in ok if r.is_silent_failure]
        print(f"\n  {condition} summary: {len(ok)}/{len(cond_results)} success, "
              f"{len(silent)} silent failures, {cond_time:.0f}s")

        all_results[condition] = cond_results

    total_time = time.time() - total_start

    # Cross-condition comparison
    print(f"\n{'='*70}")
    print("CROSS-CONDITION COMPARISON")
    print(f"{'='*70}")

    comparison = compare_conditions(all_results)

    print(f"\n{'Condition':<12} {'Success':>8} {'REI':>6} {'REI-c':>6} {'Silent':>8} {'D_dev':>8}")
    print("-" * 55)
    for cond, stats in comparison.items():
        if cond == "papers_succeeded_in_all_conditions":
            continue
        print(f"{cond:<12} {stats['n_success']:>3}/{stats['n_total']:<4} "
              f"{stats['rei_mean'] or 0:>6.3f} {stats['rei_c_mean'] or 0:>6.3f} "
              f"{stats['silent_rate']:>7.1%} {stats.get('d_mean_abs_dev', 0):>8.6f}")

    if "papers_succeeded_in_all_conditions" in comparison:
        print(f"\n  Papers succeeded in all conditions: "
              f"{comparison['papers_succeeded_in_all_conditions']}")

    # Journal-level breakdown
    print(f"\n{'='*70}")
    print("PER-JOURNAL BREAKDOWN (abstract condition)")
    print(f"{'='*70}")

    if "abstract" in all_results:
        by_journal = {}
        for r in all_results["abstract"]:
            jn = r.paper_journal or "Unknown"
            if jn not in by_journal:
                by_journal[jn] = {"total": 0, "success": 0, "silent": 0}
            by_journal[jn]["total"] += 1
            if r.status == "SUCCESS":
                by_journal[jn]["success"] += 1
                if r.is_silent_failure:
                    by_journal[jn]["silent"] += 1

        print(f"\n{'Journal':<40} {'Papers':>7} {'Success':>8} {'Silent':>7}")
        print("-" * 65)
        for jn in sorted(by_journal, key=lambda j: by_journal[j]["total"], reverse=True):
            stats = by_journal[jn]
            print(f"{jn[:40]:<40} {stats['total']:>7} {stats['success']:>7} {stats['silent']:>7}")

    # Save results
    out_name = args.output or f"e2e_benchmark_{args.condition}.json"
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / out_name

    output = {
        "config": {
            "condition": args.condition,
            "n_papers": args.n_papers,
            "max_fixes": args.max_fixes,
            "target_journals": args.target_journals,
            "seed": args.seed,
            "total_time_s": round(total_time, 1),
        },
        "comparison": comparison,
        "results": {
            cond: [
                {
                    "paper_id": r.paper_id,
                    "status": r.status,
                    "rei": r.rei,
                    "rei_c": r.rei_c,
                    "computed_d": r.computed_d,
                    "gt_d": r.gt_d,
                    "is_silent_failure": r.is_silent_failure,
                    "error_types": r.error_types,
                    "fix_count": r.fix_count,
                    "paper_title": r.paper_title,
                    "paper_journal": r.paper_journal,
                    "paper_year": r.paper_year,
                }
                for r in cond_results
            ]
            for cond, cond_results in all_results.items()
        },
    }
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
