#!/usr/bin/env python3
"""Stratified Task-Card Benchmark: paper-specific tasks at multiple difficulty levels.

Core insight: Fixed-template benchmarks overestimate reproducibility ability.
A valid benchmark must vary the scientific TASK, not just the paper context.

Difficulty levels:
  L1 (formula):    Task target + formula given → implement code
  L2 (abstract):   Abstract + task target → infer method → implement
  L3 (full paper): Full content + task target → extract method → implement

Metric types assigned per paper based on content:
  - disruption:          Papers about innovation, novelty, disruption
  - citation_prediction: Papers about impact, citations, influence
  - team_size_effect:    Papers about teams, collaboration, solo vs group

Usage:
    python scripts/run_stratified_benchmark.py --level L1 --n-papers 50
    python scripts/run_stratified_benchmark.py --level L2 --n-papers 50
    python scripts/run_stratified_benchmark.py --level all --n-papers 30
"""

import sys, os, re, json, tempfile, time, argparse
from pathlib import Path
from dataclasses import dataclass, field
from collections import Counter, defaultdict
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import numpy as np

os.environ.setdefault("OPENAI_API_KEY", "not-needed")
os.environ.setdefault("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1")
os.environ.setdefault("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/")
os.environ.setdefault("LLM_MAX_TOKENS", "4096")
os.environ.setdefault("HF_HUB_OFFLINE", "1")  # data cached locally

from src.sciscigpt_local.llm_backends import load_llm_from_env
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.rei_metric import classify_error, ERROR_WEIGHTS, compute_rei_c
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.metric_templates import (
    get_prompt as get_metric_prompt, parse_metric_output, compute_ground_truth,
    get_primary_metric, get_required_tables, METRIC_CONFIGS,
)

# ── Metric assignment by paper content ──

METRIC_KEYWORDS = {
    "disruption": [
        "disruption", "disruptive", "novelty", "innovation", "breakthrough",
        "paradigm", "consolidation", "destabiliz", "new idea",
    ],
    "citation_count_prediction": [
        "citation", "impact", "influence", "highly cited", "scientometric",
        "bibliometric", "h-index", "impact factor",
    ],
    "team_size_effect": [
        "team", "collaboration", "coauthor", "solo", "group size",
        "large team", "small team", "collective", "individual",
    ],
}

def assign_metric_type(title: str, abstract: str) -> str:
    """Assign a metric type to a paper based on keyword matching in title+abstract."""
    text = f"{title} {abstract}".lower()
    scores = {}
    for metric, keywords in METRIC_KEYWORDS.items():
        scores[metric] = sum(1 for kw in keywords if kw in text)
    if max(scores.values()) == 0:
        return "disruption"  # default
    return max(scores, key=scores.get)


# ── Failure taxonomy ──

def classify_failure(result: dict, condition: str) -> str:
    """Classify a failure into taxonomy categories."""
    if result["status"] == "SUCCESS" and not result.get("is_silent_failure"):
        return "correct"
    if result["status"] == "FAILED":
        errors = result.get("error_types", [])
        if "syntax" in errors:
            return "syntax_error"
        if "import" in errors:
            return "import_error"
        if "timeout" in errors:
            return "timeout"
        return "execution_error"
    if result.get("is_silent_failure"):
        cv = result.get("computed_primary")
        gv = result.get("ground_truth_primary")
        if cv is not None and gv is not None:
            dev = abs(cv - gv)
            if cv in (-1.0, 0.0, 1.0) and gv not in (-1.0, 0.0, 1.0):
                return "degenerate_output"
            if dev > 0.5:
                return "wrong_formula"
            return "wrong_result"
        return "parse_error"
    return "unknown"


# ── Prompt templates per difficulty level ──

def build_l1_prompt(paper_row, metric_type, refs_path, cites_path, papers_path=None):
    """L1: Formula given — same as template benchmark but with metric variety."""
    paper_id = int(paper_row["paper_id"])
    config = METRIC_CONFIGS[metric_type]
    task_desc = config["label"]

    if metric_type == "disruption":
        return get_metric_prompt("disruption", paper_id=paper_id,
                                 refs_path=refs_path, cites_path=cites_path)
    else:
        return get_metric_prompt(metric_type, papers_path=papers_path, paper_id=paper_id)


def build_l2_prompt(paper_row, metric_type, refs_path=None, cites_path=None, papers_path=None):
    """L2: Abstract + task target — LLM must infer method from paper context."""
    paper_id = int(paper_row["paper_id"])
    title = str(paper_row.get("title", ""))
    abstract = str(paper_row.get("abstract", ""))
    year = int(paper_row.get("year", 0))
    journal = str(paper_row.get("journal_name", ""))

    config = METRIC_CONFIGS[metric_type]
    task_label = config["label"]

    # Build output format spec from metric config
    out_keys = list(config["output_patterns"].keys())
    if metric_type == "disruption":
        out_fmt = "D_INDEX = <value>, n_i = <value>, n_j = <value>"
    elif metric_type == "citation_count_prediction":
        out_fmt = "CITATION_COUNT_PREDICTED = <value>, MEDIAN = <value>, SAME_YEAR_COUNT = <value>"
    elif metric_type == "team_size_effect":
        out_fmt = "SMALL_MEAN = <value>, LARGE_MEAN = <value>, DIFFERENCE = <value>, N_SMALL = <value>, N_LARGE = <value>"
    else:
        out_fmt = ", ".join(f"{k} = <value>" for k in out_keys)

    if metric_type == "disruption":
        data_section = f"""Data files:
- refs CSV at '{refs_path}': columns reference_id — papers cited BY paper {paper_id}
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id

CRITICAL: The cites CSV contains all citation edges FROM papers that cite paper {paper_id}.
Every unique citing_paper_id cites paper {paper_id}.

You must INFER the correct computation method from the paper's abstract above.
The paper studies how science builds on prior work — determine what metric would
measure novelty/disruption from citation patterns and implement it."""
    else:
        data_section = f"""Data file:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
- Focal paper: paper_id = {paper_id}"""

    return f"""You are a research reproducibility analyst. Read the paper context below,
then write Python code to reproduce the specified analysis.

=== PAPER CONTEXT ===
Title: {title}
Year: {year}
Journal: {journal}
Abstract: {abstract[:2000]}

=== TASK ===
This paper relates to: {task_label}.
Reproduce this analysis using the provided data.

{data_section}

IMPORTANT: Understand what the paper studies and how the metric captures it.
Use pandas. Print results with EXACTLY these labels on separate lines:
  {out_fmt}
Output ONLY Python code."""


def build_l3_prompt(paper_row, metric_type, markdown="", refs_path=None, cites_path=None, papers_path=None):
    """L3: Full paper content + task target — LLM extracts methodology."""
    paper_id = int(paper_row["paper_id"])
    title = str(paper_row.get("title", ""))
    abstract = str(paper_row.get("abstract", ""))
    year = int(paper_row.get("year", 0))

    config = METRIC_CONFIGS[metric_type]
    task_label = config["label"]

    # Build output format spec from metric config
    if metric_type == "disruption":
        out_fmt = "D_INDEX = <value>, n_i = <value>, n_j = <value>"
    elif metric_type == "citation_count_prediction":
        out_fmt = "CITATION_COUNT_PREDICTED = <value>, MEDIAN = <value>, SAME_YEAR_COUNT = <value>"
    elif metric_type == "team_size_effect":
        out_fmt = "SMALL_MEAN = <value>, LARGE_MEAN = <value>, DIFFERENCE = <value>, N_SMALL = <value>, N_LARGE = <value>"
    else:
        out_fmt = ", ".join(f"{k} = <value>" for k in config["output_patterns"].keys())

    content = markdown[:8000] if markdown else f"Title: {title}\n\nAbstract: {abstract[:2000]}"

    if metric_type == "disruption":
        data_section = f"""Data files:
- refs CSV at '{refs_path}': columns reference_id
- cites CSV at '{cites_path}': columns citing_paper_id, cited_paper_id (pre-filtered: all rows cite paper {paper_id})"""
    else:
        data_section = f"""Data file:
- papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
- Focal paper: paper_id = {paper_id}"""

    return f"""You are reproducing a scientific paper's analysis. Read the full paper content,
understand its methodology, then write Python code to reproduce the specified analysis.

=== FULL PAPER CONTENT ===
{content}

=== TASK ===
This paper's analysis relates to: {task_label}.
Extract the relevant methodology from the paper and implement it.

{data_section}

Use pandas. Print results with EXACTLY these labels on separate lines:
  {out_fmt}
Output ONLY Python code."""


# ── Code extraction ──

def _extract_code(text: str) -> str:
    text = re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL)
    match = re.search(r"```(?:python)?\s*\n(.*?)\n\s*```", text, re.DOTALL)
    if match:
        return match.group(1).strip()
    code = text.strip()
    if code.startswith("```"):
        code = re.sub(r"^```(?:python)?\s*\n?", "", code)
        code = re.sub(r"\n?\s*```$", "", code)
    return code


def fix_code(llm, code: str, error: str, metric_type: str, attempt: int) -> str:
    metric_label = METRIC_CONFIGS[metric_type]["label"]
    primary = get_primary_metric(metric_type)
    strategies = [
        f"Fix import errors. Use only pandas and numpy.",
        f"Check column names match the CSV files exactly.",
        f"Simplify the {metric_label} computation.",
        f"Rewrite minimal script. MUST print {primary} = <value>.",
    ]
    idx = min(attempt, len(strategies) - 1)
    prompt = f"""Fix this {metric_label} code. {strategies[idx]}

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
class TaskResult:
    paper_id: int
    metric_type: str
    level: str
    status: str
    rei: float = 0.0
    rei_c: float = 0.0
    computed_primary: float | None = None
    ground_truth_primary: float | None = None
    is_silent_failure: bool = False
    failure_category: str = "correct"
    error_types: list = field(default_factory=list)
    fix_count: int = 0
    paper_title: str = ""
    paper_journal: str = ""
    paper_year: int = 0
    input_source: str = ""          # "formula", "abstract", "abstract+extraction_prompt", "pdf_fulltext"
    markdown_chars: int = 0         # chars of full-text content actually passed to prompt
    abstract_chars: int = 0         # chars of abstract passed to prompt
    extra: dict = field(default_factory=dict)


def reproduce_task_card(
    llm,
    paper_row,
    pc: pd.DataFrame,
    metric_type: str,
    level: str = "L1",
    max_fixes: int = 3,
    papers_path: str | None = None,
    markdown: str = "",
) -> TaskResult:
    """Reproduce a single task card."""
    paper_id = int(paper_row["paper_id"])
    title = str(paper_row.get("title", ""))
    journal = str(paper_row.get("journal_name", ""))
    year = int(paper_row.get("year", 0))

    # Compute ground truth
    full_papers = load_table("papers")
    gt = compute_ground_truth(metric_type, paper_id, full_papers, pc)
    if not gt:
        return TaskResult(paper_id=paper_id, metric_type=metric_type, level=level,
                          status="SKIPPED", paper_title=title[:100], paper_journal=journal, paper_year=year,
                          input_source="", markdown_chars=0, abstract_chars=0)

    primary_key = get_primary_metric(metric_type)
    gt_value = gt.get(primary_key, 0.0)

    # Prepare data files
    refs_path, cites_path = None, None
    if metric_type == "disruption":
        refs = pc[pc["citing_paper_id"] == paper_id]["cited_paper_id"].unique()
        citers = pc[pc["cited_paper_id"] == paper_id]["citing_paper_id"].unique()
        if len(refs) == 0 or len(citers) == 0:
            return TaskResult(paper_id=paper_id, metric_type=metric_type, level=level,
                              status="SKIPPED", paper_title=title[:100], paper_journal=journal, paper_year=year,
                              input_source="", markdown_chars=0, abstract_chars=0)
        refs_path = tempfile.mktemp(suffix="_refs.csv")
        cites_path = tempfile.mktemp(suffix="_cites.csv")
        pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
        citer_cites = pc[pc["citing_paper_id"].isin(citers)][
            ["citing_paper_id", "cited_paper_id"]
        ].head(5000)
        citer_cites.to_csv(cites_path, index=False)

    # Build prompt
    if level == "L1":
        prompt = build_l1_prompt(paper_row, metric_type, refs_path, cites_path, papers_path)
        input_source = "formula"
        md_chars, ab_chars = 0, 0
    elif level == "L2":
        prompt = build_l2_prompt(paper_row, metric_type, refs_path, cites_path, papers_path)
        input_source = "abstract"
        ab = str(paper_row.get("abstract", ""))
        md_chars, ab_chars = 0, len(ab)
    elif level == "L3":
        prompt = build_l3_prompt(paper_row, metric_type, markdown, refs_path, cites_path, papers_path)
        input_source = "pdf_fulltext" if markdown and len(markdown) > 100 else "abstract+extraction_prompt"
        md_chars = len(markdown) if markdown else 0
        ab_chars = len(str(paper_row.get("abstract", ""))) if not markdown else 0
    else:
        raise ValueError(f"Unknown level: {level}")

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
            parsed = parse_metric_output(stdout, metric_type)
            if primary_key in parsed:
                weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0
                computed_val = parsed[primary_key]
                rei_c, c_ratio, silent = compute_rei_c(rei, gt_value, computed_val)

                tr = TaskResult(
                    paper_id=paper_id, metric_type=metric_type, level=level,
                    status="SUCCESS", rei=rei, rei_c=rei_c,
                    computed_primary=computed_val, ground_truth_primary=gt_value,
                    is_silent_failure=silent, error_types=error_types, fix_count=fix_count,
                    paper_title=title[:100], paper_journal=journal, paper_year=year,
                    input_source=input_source, markdown_chars=md_chars, abstract_chars=ab_chars,
                    extra={"gt": gt, "parsed": parsed},
                )
                tr.failure_category = classify_failure({
                    "status": tr.status, "is_silent_failure": tr.is_silent_failure,
                    "computed_primary": tr.computed_primary,
                    "ground_truth_primary": tr.ground_truth_primary,
                    "error_types": tr.error_types,
                }, level)
                return tr
            # Parse succeeded but primary key missing — genuine issue
            if "D_INDEX" in stdout.upper() or primary_key.lower() in stdout.lower():
                continue  # output has expected label but parser missed it; retry

        error_text = stderr or stdout
        error_cat = classify_error(error_text)
        error_types.append(error_cat)
        fix_count += 1

        if attempt < max_fixes:
            code = fix_code(llm, code, error_text, metric_type, attempt)

    weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
    rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0
    tr = TaskResult(
        paper_id=paper_id, metric_type=metric_type, level=level,
        status="FAILED", rei=rei, rei_c=rei, ground_truth_primary=gt_value,
        error_types=error_types, fix_count=fix_count,
        paper_title=title[:100], paper_journal=journal, paper_year=year,
        input_source=input_source, markdown_chars=md_chars, abstract_chars=ab_chars,
    )
    tr.failure_category = classify_failure({
        "status": tr.status, "is_silent_failure": False,
        "computed_primary": None, "ground_truth_primary": gt_value,
        "error_types": tr.error_types,
    }, level)
    return tr


# ── Paper sampling with metric assignment ──

def build_task_cards(papers, pc, n, target_journals=None, seed=42):
    """Build stratified task cards: each paper gets an assigned metric type.

    Returns list of dicts: {paper_id, metric_type, paper_row}
    """
    rng = np.random.default_rng(seed)
    pc_pids = set(pc["citing_paper_id"].unique()) & set(pc["cited_paper_id"].unique())
    valid = papers[papers["paper_id"].isin(pc_pids)].copy()

    for col in ["title", "abstract", "journal_name"]:
        if col not in valid.columns:
            valid[col] = ""

    sampled = []

    # Priority 1: Target journals
    if target_journals:
        for pattern in target_journals:
            # Clean match: exact journal name, not substring
            pool = valid[valid["journal_name"].str.fullmatch(pattern, case=False, na=False)]
            if len(pool) == 0:
                # Fall back to contains
                pool = valid[valid["journal_name"].str.contains(pattern, case=False, na=False)]
            k = min(n // (len(target_journals) + 3), len(pool))
            if k > 0:
                chosen = pool.sample(k, random_state=seed)
                sampled.extend(chosen["paper_id"].tolist())

    # Priority 2: Other top journals (broad coverage)
    remaining_n = n - len(sampled)
    if remaining_n > 0:
        broad_journals = ["Science", "Nature", "PNAS", "PLOS ONE",
                          "Physical Review", "Journal of"]
        for pattern in broad_journals:
            pool = valid[
                valid["journal_name"].str.contains(pattern, case=False, na=False) &
                ~valid["paper_id"].isin(sampled)
            ]
            k = min(remaining_n // len(broad_journals), len(pool))
            if k > 0:
                chosen = pool.sample(k, random_state=seed + 1)
                sampled.extend(chosen["paper_id"].tolist())

    # Priority 3: Fill remaining
    remaining_n = n - len(sampled)
    if remaining_n > 0:
        pool = valid[~valid["paper_id"].isin(sampled)]
        if len(pool) > 0:
            chosen = pool.sample(min(remaining_n, len(pool)), random_state=seed + 2)
            sampled.extend(chosen["paper_id"].tolist())

    # Build task cards with metric assignment
    cards = []
    for pid in sampled[:n]:
        row = papers[papers["paper_id"] == pid].iloc[0]
        metric = assign_metric_type(
            str(row.get("title", "")), str(row.get("abstract", "")))
        cards.append({"paper_id": pid, "metric_type": metric, "paper_row": row})

    return cards


# ── Main ──

def main():
    parser = argparse.ArgumentParser(
        description="Stratified Task-Card Benchmark: paper-specific tasks at L1/L2/L3")
    parser.add_argument("--level", default="all",
                        choices=["L1", "L2", "L3", "all"],
                        help="Difficulty level(s)")
    parser.add_argument("--n-papers", type=int, default=50,
                        help="Number of papers")
    parser.add_argument("--max-fixes", type=int, default=3)
    parser.add_argument("--target-journals", nargs="*",
                        default=["Management Science", "Research Policy"],
                        help="Priority journals")
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", default=None)

    args = parser.parse_args()

    print("=" * 70)
    print("STRATIFIED TASK-CARD BENCHMARK")
    print(f"  Levels: {args.level}, Papers: {args.n_papers}")
    print("=" * 70)

    llm = load_llm_from_env()
    print(f"  LLM: {type(llm).__name__}")

    print("  Loading SciSciNet...", end=" ", flush=True)
    papers = load_table("papers")
    pc = load_table("paper_citations")
    print(f"OK ({len(papers):,} papers, {len(pc):,} citations)")

    # Build task cards
    print(f"\n  Building task cards for {args.n_papers} papers...")
    cards = build_task_cards(papers, pc, args.n_papers, args.target_journals, args.seed)

    # Metric distribution
    metric_dist = Counter(c["metric_type"] for c in cards)
    print(f"  Metric distribution: {dict(metric_dist)}")

    # Journal distribution
    journal_dist = Counter(str(c["paper_row"].get("journal_name", "")) for c in cards)
    print(f"  Journal distribution (top 10):")
    for jn, cnt in journal_dist.most_common(10):
        print(f"    {jn}: {cnt}")

    # Pre-write papers CSV for non-disruption metrics
    papers_csv_path = tempfile.mktemp(suffix="_papers.csv")
    cols = ["paper_id", "year", "citation_count", "disruption_score"]
    if "author_count" in papers.columns:
        cols.append("author_count")
    papers[cols].to_csv(papers_csv_path, index=False)

    # Run levels
    levels = [args.level] if args.level != "all" else ["L1", "L2", "L3"]
    all_results = {}
    total_start = time.time()

    for level in levels:
        print(f"\n{'='*70}")
        print(f"LEVEL: {level}")
        print(f"{'='*70}")

        level_results = []
        level_start = time.time()

        for i, card in enumerate(cards):
            elapsed = time.time() - level_start
            eta = (elapsed / (i + 1)) * (len(cards) - i - 1) if i > 0 else 0

            pid = card["paper_id"]
            metric = card["metric_type"]
            paper_row = card["paper_row"]
            title_short = str(paper_row.get("title", ""))[:50]

            print(f"  [{i+1}/{len(cards)}] Paper {pid} [{metric[:8]}] ({title_short}...)",
                  end=" ", flush=True)

            r = reproduce_task_card(
                llm, paper_row, pc, metric_type=metric, level=level,
                max_fixes=args.max_fixes, papers_path=papers_csv_path)
            level_results.append(r)

            icon = {"SUCCESS": "✓", "FAILED": "✗", "SKIPPED": "→"}.get(r.status, "?")
            print(f"{icon} REI={r.rei} [{r.failure_category}]" +
                  (" ⚠️" if r.is_silent_failure else "") +
                  f" [ETA: {eta:.0f}s]", flush=True)

        level_time = time.time() - level_start
        ok = [r for r in level_results if r.status == "SUCCESS"]
        silent = [r for r in ok if r.is_silent_failure]
        print(f"\n  {level} summary: {len(ok)}/{len(level_results)} success, "
              f"{len(silent)} silent failures, {level_time:.0f}s")

        all_results[level] = level_results

    total_time = time.time() - total_start

    # ── Cross-level comparison ──
    print(f"\n{'='*70}")
    print("CROSS-LEVEL COMPARISON")
    print(f"{'='*70}")

    for level, results in all_results.items():
        ok = [r for r in results if r.status == "SUCCESS"]
        silent = [r for r in ok if r.is_silent_failure]
        failed = [r for r in results if r.status == "FAILED"]

        rei_vals = [r.rei for r in ok + failed]
        rei_c_vals = [r.rei_c for r in ok + failed]

        # By metric type
        by_metric = defaultdict(list)
        for r in ok:
            by_metric[r.metric_type].append(r)

        print(f"\n--- {level} ---")
        print(f"  Success: {len(ok)}/{len(results)} ({100*len(ok)/len(results):.0f}%)")
        print(f"  Failed: {len(failed)}, Silent failures: {len(silent)}")
        if rei_vals:
            print(f"  REI: mean={np.mean(rei_vals):.3f}, median={np.median(rei_vals):.2f}")
        if rei_c_vals:
            print(f"  REI-c: mean={np.mean(rei_c_vals):.3f}, median={np.median(rei_c_vals):.2f}")

        # Per-metric breakdown
        print(f"  By metric type:")
        for mt, mresults in sorted(by_metric.items()):
            mrei = [r.rei_c for r in mresults]
            msilent = sum(1 for r in mresults if r.is_silent_failure)
            print(f"    {mt}: n={len(mresults)}, REI-c={np.mean(mrei):.3f}, silent={msilent}")

        # Input source breakdown
        source_counts = Counter(r.input_source for r in results if r.input_source)
        if source_counts:
            print(f"  Input sources:")
            for src, cnt in source_counts.most_common():
                avg_md = np.mean([r.markdown_chars for r in results if r.input_source == src])
                print(f"    {src}: {cnt}/{len(results)}, avg markdown_chars={avg_md:.0f}")

        # Failure taxonomy
        taxonomy = Counter(r.failure_category for r in results)
        print(f"  Failure taxonomy: {dict(taxonomy)}")

    # Cross-level success comparison
    if len(all_results) >= 2:
        levels_list = list(all_results.keys())
        common_ok = set(
            r.paper_id for r in all_results[levels_list[0]] if r.status == "SUCCESS"
        )
        for lvl in levels_list[1:]:
            common_ok &= set(r.paper_id for r in all_results[lvl] if r.status == "SUCCESS")
        print(f"\n  Papers succeeded at ALL levels: {len(common_ok)}/{args.n_papers}")

    # Save results
    out_name = args.output or f"stratified_benchmark_{args.level}.json"
    out_path = Path(__file__).resolve().parent.parent / "refine-logs" / out_name

    output = {
        "config": {
            "level": args.level,
            "n_papers": args.n_papers,
            "max_fixes": args.max_fixes,
            "target_journals": args.target_journals,
            "seed": args.seed,
            "total_time_s": round(total_time, 1),
            "metric_distribution": dict(metric_dist),
        },
        "results": {
            level: [
                {
                    "paper_id": r.paper_id,
                    "metric_type": r.metric_type,
                    "level": r.level,
                    "status": r.status,
                    "rei": r.rei,
                    "rei_c": r.rei_c,
                    "computed_primary": r.computed_primary,
                    "ground_truth_primary": r.ground_truth_primary,
                    "is_silent_failure": r.is_silent_failure,
                    "failure_category": r.failure_category,
                    "error_types": r.error_types,
                    "fix_count": r.fix_count,
                    "paper_title": r.paper_title,
                    "paper_journal": r.paper_journal,
                    "paper_year": r.paper_year,
                    "input_source": r.input_source,
                    "markdown_chars": r.markdown_chars,
                    "abstract_chars": r.abstract_chars,
                }
                for r in level_results
            ]
            for level, level_results in all_results.items()
        },
    }
    out_path.write_text(json.dumps(output, indent=2, default=str))
    print(f"\nResults saved to {out_path}")

    return 0


if __name__ == "__main__":
    sys.exit(main())
