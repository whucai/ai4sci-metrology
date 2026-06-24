#!/usr/bin/env python3
"""Concurrent SciSciBench runner — processes multiple papers in parallel.

Supports loading papers from an extracted annotation registry (produced by
extract_annotations.py) or from PILOT_PAPERS.

Uses ThreadPoolExecutor for concurrent LLM calls to the vLLM endpoint.
"""

from __future__ import annotations

import json
import os
import sys
import time
import argparse
import threading
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.annotation import SciSciPaper, create_wu2019, create_ke2023, create_arts2025
from src.sciscibench.tasks.task1_design import Task1Prompt, Task1Runner
from src.sciscibench.tasks.task2_conclusion import Task2Prompt, Task2Runner
from src.sciscibench.eval.task1_evaluator import Task1Evaluator
from src.sciscibench.eval.task2_evaluator import Task2Evaluator

PILOT_PAPERS: dict[str, SciSciPaper] = {
    "wu2019_disruption": create_wu2019(),
    "ke2023_normalized_impact": create_ke2023(),
    "arts2025_frontier_scientists": create_arts2025(),
}

MAX_WORKERS = 8
print_lock = threading.Lock()


def _print(msg: str):
    with print_lock:
        print(msg)


def load_llm() -> Any:
    """Create LLM client using env vars. Auto-detects DeepSeek vs Qwen vLLM.

    Priority:
      1. ANTHROPIC_AUTH_TOKEN + ANTHROPIC_BASE_URL → DeepSeek (Anthropic API)
      2. OPENAI_API_KEY + OPENAI_BASE_URL → Qwen/vLLM (OpenAI API)
    """
    from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config
    import os

    # DeepSeek via Anthropic-compatible API
    anthro_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if anthro_key:
        return load_llm_from_config(LLMConfig(
            name="deepseek-v4-pro",
            provider="anthropic",
            model=os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "deepseek-v4-pro"),
            api_key=anthro_key,
            base_url=os.environ.get("ANTHROPIC_BASE_URL", ""),
            temperature=0.0,
            max_tokens=4096,
        ))

    # Qwen via vLLM (OpenAI-compatible)
    openai_key = os.environ.get("OPENAI_API_KEY", "not-needed")
    return load_llm_from_config(LLMConfig(
        name="qwen3-32b",
        provider="openai",
        model=os.environ.get("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/"),
        api_key=openai_key,
        base_url=os.environ.get("OPENAI_BASE_URL", "http://172.17.65.41:8032/v1"),
        temperature=0.0,
        max_tokens=4096,
    ))


def paper_from_extraction(entry: dict) -> SciSciPaper:
    """Construct a SciSciPaper from an extracted annotation dict."""
    ed_gold = entry.get("statistical_method", {}) or {}
    return SciSciPaper(
        paper_id=entry.get("paper_id", ""),
        title=entry.get("title", ""),
        authors=entry.get("authors", []),
        venue=entry.get("venue", ""),
        year=entry.get("year", 0),
        doi=entry.get("doi", ""),
        research_idea=entry.get("research_idea", ""),
        research_question=entry.get("research_question", ""),
        hypotheses=entry.get("hypotheses", []),
        data_source=entry.get("data_source", ""),
        data_description=entry.get("data_description", ""),
        available_fields=entry.get("available_fields", []),
        sample_scope=entry.get("sample_scope", {}),
        independent_variables=entry.get("independent_variables", []),
        dependent_variables=entry.get("dependent_variables", []),
        control_variables=entry.get("control_variables", []),
        experiment_design_gold={
            "statistical_method": ed_gold,
            "network_construction": entry.get("network_construction", {}),
            "grouping_strategy": entry.get("grouping_strategy", {}),
            "expected_result_form": entry.get("expected_result_form", {}),
            "robustness_checks": entry.get("robustness_checks", []),
        },
        result_claims=entry.get("result_claims", []),
        partial_results=entry.get("partial_results", []),
        conclusion_claims=entry.get("conclusion_claims", []),
        limitations=entry.get("limitations", []),
        robustness_checks=entry.get("robustness_checks", []),
        text_path=entry.get("text_path", ""),
    )


def load_registry(path: str) -> dict[str, SciSciPaper]:
    """Load papers from extracted annotation registry."""
    data = json.loads(Path(path).read_text())
    papers = {}
    for pid, entry in data.items():
        try:
            papers[pid] = paper_from_extraction(entry)
        except Exception as e:
            _print(f"  SKIP {pid}: {e}")
    return papers


# ── Concurrent task runners ──

def run_task1_single(llm, paper: SciSciPaper, condition: str,
                      evaluator: Task1Evaluator, gold: dict) -> dict:
    """Run Task 1 on one paper × condition."""
    prompt = Task1Prompt(paper=paper, condition=condition)
    runner = Task1Runner(llm=llm)
    t0 = time.time()
    output = runner.run(prompt)
    elapsed = time.time() - t0

    result = {
        "paper_id": paper.paper_id,
        "condition": condition,
        "elapsed": round(elapsed, 1),
    }

    if output["status"] == "success":
        eval_result = evaluator.evaluate(
            gold=gold, pred=output["output"],
            paper_id=paper.paper_id, condition=condition,
        )
        result.update(eval_result.to_dict())
        result["status"] = "success"
    else:
        result["status"] = output["status"]
        result["error"] = output.get("error", "")[:200]

    return result


def run_task2_single(llm, paper: SciSciPaper, level: str,
                      evaluator: Task2Evaluator, gold: dict) -> dict:
    """Run Task 2 on one paper × level."""
    prompt = Task2Prompt(paper=paper, level=level)
    runner = Task2Runner(llm=llm)
    t0 = time.time()
    output = runner.run(prompt)
    elapsed = time.time() - t0

    result = {
        "paper_id": paper.paper_id,
        "level": level,
        "elapsed": round(elapsed, 1),
    }

    if output["status"] == "success":
        eval_result = evaluator.evaluate(
            gold=gold, pred=output, level=level, paper_id=paper.paper_id,
        )
        result.update(eval_result.to_dict())
        result["status"] = "success"
    else:
        result["status"] = output["status"]
        result["error"] = output.get("error", "")[:200]

    return result


# ── Main concurrent runners ──

def run_task1_concurrent(llm, papers: dict[str, SciSciPaper],
                         conditions: list[str],
                         max_workers: int = MAX_WORKERS) -> list[dict]:
    """Run Task 1 concurrently across all papers × conditions."""
    evaluator = Task1Evaluator()
    tasks = []

    for paper_id, paper in papers.items():
        paper.assess_contamination()
        paper.generate_blind_versions()
        gold = paper.to_gold_json()
        for condition in conditions:
            tasks.append((paper, condition, evaluator, gold))

    _print(f"Task 1: {len(papers)} papers × {len(conditions)} conditions = {len(tasks)} tasks")
    t0 = time.time()
    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_task1_single, llm, paper, cond, evalr, gold): (paper.paper_id, cond)
            for paper, cond, evalr, gold in tasks
        }
        for future in as_completed(futures):
            pid, cond = futures[future]
            try:
                r = future.result()
                results.append(r)
                completed += 1
                f1 = r.get("overall_f1", 0)
                _print(f"  [{completed}/{len(tasks)}] {pid}/{cond} F1={f1:.3f} ({r['elapsed']}s)")
            except Exception as e:
                completed += 1
                _print(f"  [{completed}/{len(tasks)}] {pid}/{cond} ERROR: {e}")
                results.append({"paper_id": pid, "condition": cond, "status": "error", "error": str(e)})

    elapsed = time.time() - t0
    _print(f"Task 1 complete: {len(tasks)} tasks in {elapsed:.1f}s ({elapsed/len(tasks):.1f}s/task)")
    return results


def run_task2_concurrent(llm, papers: dict[str, SciSciPaper],
                         levels: list[str],
                         max_workers: int = MAX_WORKERS) -> list[dict]:
    """Run Task 2 concurrently across all papers × levels."""
    evaluator = Task2Evaluator()
    tasks = []

    for paper_id, paper in papers.items():
        gold = paper.to_task2_gold()
        for level in levels:
            tasks.append((paper, level, evaluator, gold))

    _print(f"Task 2: {len(papers)} papers × {len(levels)} levels = {len(tasks)} tasks")
    t0 = time.time()
    results = []
    completed = 0

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        futures = {
            executor.submit(run_task2_single, llm, paper, lvl, evalr, gold): (paper.paper_id, lvl)
            for paper, lvl, evalr, gold in tasks
        }
        for future in as_completed(futures):
            pid, lvl = futures[future]
            try:
                r = future.result()
                results.append(r)
                completed += 1
                score = r.get("overall_score", 0)
                _print(f"  [{completed}/{len(tasks)}] {pid}/{lvl} score={score:.3f} ({r['elapsed']}s)")
            except Exception as e:
                completed += 1
                _print(f"  [{completed}/{len(tasks)}] {pid}/{lvl} ERROR: {e}")
                results.append({"paper_id": pid, "level": lvl, "status": "error", "error": str(e)})

    elapsed = time.time() - t0
    _print(f"Task 2 complete: {len(tasks)} tasks in {elapsed:.1f}s ({elapsed/len(tasks):.1f}s/task)")
    return results


# ── Summary ──

def print_summary(results: list[dict], task: str):
    """Print aggregate summary statistics."""
    success = [r for r in results if r.get("status") == "success"]
    failed = [r for r in results if r.get("status") != "success"]

    _print(f"\n{'='*60}")
    _print(f"{task} SUMMARY: {len(success)}/{len(results)} success, {len(failed)} failed")

    if task == "Task 1":
        scores = [r["overall_f1"] for r in success if "overall_f1" in r]
        if scores:
            _print(f"  Overall F1: mean={sum(scores)/len(scores):.3f}, min={min(scores):.3f}, max={max(scores):.3f}")
        # By condition
        for cond in ["blind", "obfuscated"]:
            cond_scores = [r["overall_f1"] for r in success
                          if r.get("condition") == cond and "overall_f1" in r]
            if cond_scores:
                _print(f"  {cond}: mean={sum(cond_scores)/len(cond_scores):.3f} (n={len(cond_scores)})")

    elif task == "Task 2":
        scores = [r["overall_score"] for r in success if "overall_score" in r]
        if scores:
            _print(f"  Overall: mean={sum(scores)/len(scores):.3f}, min={min(scores):.3f}, max={max(scores):.3f}")
        for lvl in ["L1", "L2", "L3"]:
            lvl_scores = [r["overall_score"] for r in success
                         if r.get("level") == lvl and "overall_score" in r]
            if lvl_scores:
                _print(f"  {lvl}: mean={sum(lvl_scores)/len(lvl_scores):.3f} (n={len(lvl_scores)})")

    _print(f"{'='*60}")


# ── CLI ──

def main():
    parser = argparse.ArgumentParser(description="Concurrent SciSciBench runner")
    parser.add_argument("--task", type=str, default="both", choices=["task1", "task2", "both"])
    parser.add_argument("--registry", type=str, default="bench-mark/extracted_registry.json",
                        help="Path to extracted annotation registry JSON")
    parser.add_argument("--pilot", action="store_true", help="Run on 3 pilot papers only")
    parser.add_argument("--conditions", type=str, default="blind,obfuscated",
                        help="Comma-separated Task 1 conditions")
    parser.add_argument("--levels", type=str, default="L1,L2,L3",
                        help="Comma-separated Task 2 levels")
    parser.add_argument("--workers", type=int, default=MAX_WORKERS)
    parser.add_argument("--output", "--output-dir", type=str, default="refine-logs",
                        dest="output")
    parser.add_argument("--max-papers", type=int, default=0, help="Max papers (0=all)")
    args = parser.parse_args()

    # Load papers
    if args.pilot:
        papers = PILOT_PAPERS
        _print(f"Using {len(papers)} pilot papers")
    else:
        registry_path = Path(args.registry)
        if not registry_path.exists():
            _print(f"ERROR: Registry not found: {registry_path}")
            _print("Run scripts/extract_annotations.py first to extract annotations.")
            sys.exit(1)
        papers = load_registry(str(registry_path))
        if args.max_papers > 0:
            papers = dict(list(papers.items())[:args.max_papers])
        _print(f"Loaded {len(papers)} papers from registry")

    # Load LLM
    _print("Loading LLM...")
    llm = load_llm()

    output_dir = Path(args.output)
    output_dir.mkdir(parents=True, exist_ok=True)
    ts = datetime.now().strftime('%Y%m%d_%H%M%S')

    conditions = [c.strip() for c in args.conditions.split(",")]
    levels = [l.strip() for l in args.levels.split(",")]

    # Run
    if args.task in ("task1", "both"):
        t1_results = run_task1_concurrent(llm, papers, conditions, max_workers=args.workers)
        t1_path = output_dir / f"sciscibench_task1_concurrent_{ts}.json"
        t1_path.write_text(json.dumps(t1_results, indent=2, ensure_ascii=False))
        print_summary(t1_results, "Task 1")
        _print(f"Results: {t1_path}")

    if args.task in ("task2", "both"):
        t2_results = run_task2_concurrent(llm, papers, levels, max_workers=args.workers)
        t2_path = output_dir / f"sciscibench_task2_concurrent_{ts}.json"
        t2_path.write_text(json.dumps(t2_results, indent=2, ensure_ascii=False))
        print_summary(t2_results, "Task 2")
        _print(f"Results: {t2_path}")


if __name__ == "__main__":
    main()
