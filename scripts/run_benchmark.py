#!/usr/bin/env python3
"""Unified AI Metrology Benchmark Runner.

Single entry point for running the 4-stage paper reproduction chain benchmark.
Replaces run_manual_papers_benchmark.py, run_stage4_benchmark.py,
and run_native_method_benchmark.py.

Usage:
    # MVP: Stage 2 + Stage 4
    python scripts/run_benchmark.py --stages 2,4 --model qwen3-32b

    # Full 4-stage oracle benchmark
    python scripts/run_benchmark.py --stages 1,2,3,4 --condition oracle

    # Multi-model comparison
    python scripts/run_benchmark.py --stages 2 --models qwen3-32b,deepseek-v4-pro

    # Chain condition (error propagation)
    python scripts/run_benchmark.py --stages 1,2,3,4 --condition chain

    # Resume from checkpoint
    python scripts/run_benchmark.py --resume refine-logs/benchmark_20260605_120000.json
"""

from __future__ import annotations

import sys
import os
import json
import time
import argparse
import threading
import traceback
from pathlib import Path
from datetime import datetime
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import numpy as np


class NumpyEncoder(json.JSONEncoder):
    """Custom JSON encoder that handles numpy types."""
    def default(self, obj):
        if isinstance(obj, (np.integer,)):
            return int(obj)
        if isinstance(obj, (np.floating,)):
            return float(obj)
        if isinstance(obj, (np.bool_,)):
            return bool(obj)
        if isinstance(obj, np.ndarray):
            return obj.tolist()
        return super().default(obj)


sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.ai_metrology_benchmark.config import (
    DEFAULT_CONCURRENCY, DEFAULT_STAGES, DEFAULT_MODEL_NAMES,
    DEFAULT_CONDITION, DEFAULT_INFO_LEVEL, N_TEST_PAPERS,
    OUTPUT_DIR,
)
from src.ai_metrology_benchmark.types import (
    StageResult, BenchmarkRun, Condition, InfoLevel,
)
from src.ai_metrology_benchmark.papers import (
    PAPER_REGISTRY, get_paper, enrich_paper_entry,
)
from src.ai_metrology_benchmark.stages.stage2_reproduction import (
    Stage2Reproduction,
)
from src.ai_metrology_benchmark.stages.stage4_judgment import (
    Stage4Judgment,
)
from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config
from src.sciscigpt_local.sciscinet_connector import load_table


# ── LLM loading ──────────────────────────────────────────────────────────

def get_available_models() -> dict[str, LLMConfig]:
    """Discover available models from environment."""
    models = {}

    if os.environ.get("OPENAI_API_KEY") and os.environ.get("OPENAI_BASE_URL"):
        models["qwen3-32b"] = LLMConfig(
            name="qwen3-32b", provider="openai",
            model=os.environ.get("LLM_MODEL", "Qwen/Qwen3-32B"),
            api_key=os.environ["OPENAI_API_KEY"],
            base_url=os.environ["OPENAI_BASE_URL"],
            temperature=0.0,
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
        )

    if os.environ.get("ANTHROPIC_AUTH_TOKEN") and os.environ.get("ANTHROPIC_BASE_URL"):
        models["deepseek-v4-pro"] = LLMConfig(
            name="deepseek-v4-pro", provider="anthropic",
            model="deepseek-v4-pro",
            api_key=os.environ["ANTHROPIC_AUTH_TOKEN"],
            base_url=os.environ["ANTHROPIC_BASE_URL"],
            temperature=0.0, max_tokens=4096,
        )

    return models


def _sanitize_value(val: Any) -> Any:
    """Convert numpy types to native Python for JSON serialization."""
    if val is None:
        return None
    if isinstance(val, (np.integer,)):
        return int(val)
    if isinstance(val, (np.floating,)):
        return float(val)
    if isinstance(val, (np.bool_,)):
        return bool(val)
    if isinstance(val, np.ndarray):
        return val.tolist()
    if isinstance(val, dict):
        return {k: _sanitize_value(v) for k, v in val.items()}
    if isinstance(val, list):
        return [_sanitize_value(v) for v in val]
    return val


def create_llm(model_name: str) -> Any:
    """Create an LLM instance by name."""
    if model_name == "mock":
        from src.sciscigpt_local.mock_llm import MockLLM
        return MockLLM()

    available = get_available_models()
    if model_name not in available:
        raise ValueError(
            f"Model '{model_name}' not available. Available: {list(available.keys())}. "
            f"Set OPENAI_API_KEY/OPENAI_BASE_URL for qwen3-32b, "
            f"ANTHROPIC_AUTH_TOKEN/ANTHROPIC_BASE_URL for deepseek-v4-pro."
        )

    config = available[model_name]
    llm = load_llm_from_config(config)
    llm._label = model_name  # tracking label, not API model name
    return llm


# ── Benchmark Runner ─────────────────────────────────────────────────────

class BenchmarkRunner:
    """Orchestrates multi-stage, multi-model benchmark runs."""

    def __init__(
        self,
        stages: list[int] | None = None,
        models: list[str] | None = None,
        condition: Condition = "oracle",
        info_level: InfoLevel = "L2",
        n_test_papers: int = N_TEST_PAPERS,
        workers: int = DEFAULT_CONCURRENCY,
        output_dir: str | Path = OUTPUT_DIR,
        paper_ids: list[str] | None = None,
    ):
        self.stages = stages or DEFAULT_STAGES
        self.model_names = models or DEFAULT_MODEL_NAMES
        self.condition: Condition = condition
        self.info_level: InfoLevel = info_level
        self.n_test_papers = n_test_papers
        self.workers = workers
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)

        if paper_ids:
            self.papers = {pid: enrich_paper_entry(get_paper(pid)) for pid in paper_ids}
        else:
            self.papers = {pid: enrich_paper_entry(p) for pid, p in PAPER_REGISTRY.items()}

        self._papers_df = None
        self._pc = None
        self.print_lock = threading.Lock()

    @property
    def papers_df(self):
        if self._papers_df is None:
            with self.print_lock:
                print("Loading SciSciNet papers table...")
            self._papers_df = load_table("papers")
        return self._papers_df

    @property
    def pc(self):
        if self._pc is None:
            with self.print_lock:
                print("Loading SciSciNet paper_citations table...")
            self._pc = load_table("paper_citations")
        return self._pc

    def _stage2_to_dict(self, result: StageResult) -> dict:
        """Convert StageResult to raw dict (backward compat with Stage 4 input)."""
        return {
            "paper_id": result.test_paper_id,
            "methodology_paper": result.paper_id,
            "level": result.info_level or self.info_level,
            "metric_type": self.papers[result.paper_id].metric_type,
            "status": result.status,
            "rei": 0.0 if result.rei_c is None else max(0, float(result.rei_c) * 0.1),
            "rei_c": result.rei_c or 100,
            "computed_primary": _sanitize_value(result.computed_primary),
            "ground_truth_primary": _sanitize_value(result.ground_truth_primary),
            "is_silent_failure": bool(result.is_silent_failure),
            "fix_count": result.fix_count,
            "error_types": result.error_types,
            "input_source": result.condition,
            "paper_chars": result.input_chars,
        }

    def run_stage2(self, model_name: str, llm: Any) -> tuple[list[StageResult], list[dict]]:
        """Run Stage 2 for all papers with test papers."""
        stage2 = Stage2Reproduction(
            papers_df=self.papers_df, pc=self.pc, level=self.info_level,
        )

        test_papers = Stage2Reproduction.select_test_papers(
            self.papers_df, self.pc, n=self.n_test_papers,
        )
        with self.print_lock:
            print(f"\nSelected {len(test_papers)} test papers")
            for tp in test_papers:
                print(f"  {tp['paper_id']} [{tp['year']}]: {tp['title'][:80]} "
                      f"(D={tp['disruption']:.4f})")

        tasks = []
        for test_paper in test_papers:
            for paper_id, paper in self.papers.items():
                tasks.append({"paper": paper, "test_paper": test_paper, "model_name": model_name})

        with self.print_lock:
            print(f"\nRunning {len(tasks)} Stage 2 tasks with {self.workers} workers...")

        t0 = time.time()
        results: list[StageResult] = []
        raw_results: list[dict] = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {}
            for task in tasks:
                worker_llm = create_llm(task["model_name"])
                future = executor.submit(
                    stage2.run_with_execution,
                    worker_llm, task["paper"], task["test_paper"], self.condition,
                )
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    results.append(result)
                    raw_results.append(self._stage2_to_dict(result))
                    with self.print_lock:
                        tag = f"[{result.info_level or 'S2'}] Test={result.test_paper_id} Paper={result.paper_id}"
                        if result.status == "SUCCESS":
                            print(f"  {tag} computed={result.computed_primary} "
                                  f"gt={result.ground_truth_primary} REI-c={result.rei_c}")
                        elif result.status == "SKIPPED":
                            print(f"  {tag} SKIPPED: {result.output.get('reason', '')}")
                        else:
                            print(f"  {tag} {result.status} errors={result.error_types}")
                except Exception:
                    with self.print_lock:
                        print(f"  ERROR Stage2 {task['paper'].id}/{task['test_paper']['paper_id']}")
                    traceback.print_exc()

        if results:
            elapsed = time.time() - t0
            with self.print_lock:
                print(f"\nStage 2: {len(results)} tasks in {elapsed:.1f}s "
                      f"({elapsed/len(results):.1f}s/task)")

        return results, raw_results

    def run_stage4(self, model_name: str, llm: Any, stage2_results: list[dict]) -> list[dict]:
        """Run Stage 4 judgment on Stage 2 results."""
        stage4 = Stage4Judgment()

        tasks = []
        for s2r in stage2_results:
            paper_id = s2r.get("methodology_paper", "")
            if paper_id in self.papers:
                tasks.append({"paper": self.papers[paper_id], "stage2_result": s2r,
                              "model_name": model_name})

        with self.print_lock:
            print(f"\nRunning {len(tasks)} Stage 4 tasks with {self.workers} workers...")

        t0 = time.time()
        judgments: list[dict] = []

        with ThreadPoolExecutor(max_workers=self.workers) as executor:
            futures = {}
            for task in tasks:
                worker_llm = create_llm(task["model_name"])
                future = executor.submit(
                    self._run_single_stage4, worker_llm, stage4, task,
                )
                futures[future] = task

            for future in as_completed(futures):
                task = futures[future]
                try:
                    result = future.result()
                    judgments.append(result)
                    with self.print_lock:
                        jc = result.get("judgment_counts", {})
                        print(f"  [S4] Paper={task['paper'].id} "
                              f"parsed={result.get('parsed')} judgments={jc}")
                except Exception:
                    with self.print_lock:
                        print(f"  ERROR Stage4 {task['paper'].id}")
                    traceback.print_exc()

        if judgments:
            elapsed = time.time() - t0
            with self.print_lock:
                print(f"\nStage 4: {len(judgments)} judgments in {elapsed:.1f}s")

        return judgments

    def _run_single_stage4(self, llm: Any, stage4: Stage4Judgment, task: dict) -> dict:
        paper = task["paper"]
        s2r = task["stage2_result"]
        result = stage4.run(llm, paper, condition=self.condition, stage2_result=s2r)
        return {
            "methodology_paper": paper.id,
            "test_paper_id": s2r.get("paper_id"),
            "level": s2r.get("level"),
            "metric_type": s2r.get("metric_type", paper.metric_type),
            "stage2_status": s2r.get("status"),
            "stage2_rei_c": s2r.get("rei_c"),
            "parsed": result.output.get("parsed", False),
            "judgments": result.output.get("judgments", []),
            "overall_assessment": result.output.get("overall_assessment", {}),
            "judgment_counts": result.output.get("judgment_counts", {}),
        }

    def run(self, model_name: str | None = None) -> BenchmarkRun:
        """Execute the full benchmark."""
        models_to_run = [model_name] if model_name else self.model_names
        run_id = datetime.now().strftime("%Y%m%d_%H%M%S")

        all_stage_results: list[StageResult] = []
        all_stage2_raw: list[dict] = []
        all_judgments: list[dict] = []

        for mn in models_to_run:
            with self.print_lock:
                print(f"\n{'='*60}")
                print(f"Model: {mn} | Stages: {self.stages} | "
                      f"Condition: {self.condition} | Level: {self.info_level}")
                print(f"{'='*60}")

            llm = create_llm(mn)

            if 2 in self.stages:
                s2r, s2raw = self.run_stage2(mn, llm)
                all_stage_results.extend(s2r)
                all_stage2_raw.extend(s2raw)

            if 4 in self.stages and all_stage2_raw:
                judgments = self.run_stage4(mn, llm, all_stage2_raw)
                all_judgments.extend(judgments)

        run = BenchmarkRun(
            run_id=run_id,
            timestamp=datetime.now().isoformat(),
            description=f"Stages={self.stages} condition={self.condition} level={self.info_level}",
            models=models_to_run,
            papers=list(self.papers.keys()),
            stages=self.stages,
            conditions=[self.condition],
            stage_results=all_stage_results,
        )
        run.summary = self._compute_summary(all_stage_results, all_judgments)

        out_path = self.output_dir / f"benchmark_{run_id}.json"
        output_data = {
            "run_id": run.run_id,
            "timestamp": run.timestamp,
            "description": run.description,
            "models": run.models,
            "papers": run.papers,
            "stages": run.stages,
            "conditions": run.conditions,
            "n_stage2_results": len(all_stage_results),
            "n_stage4_judgments": len(all_judgments),
            "summary": run.summary,
            "stage2_results": [self._stage2_to_dict(r) for r in all_stage_results],
            "stage4_judgments": all_judgments,
        }
        out_path.write_text(json.dumps(output_data, indent=2, ensure_ascii=False, cls=NumpyEncoder))
        print(f"\nResults saved to {out_path}")
        return run

    def _compute_summary(self, s2_results: list[StageResult],
                         judgments: list[dict]) -> dict[str, Any]:
        s2_success = [r for r in s2_results if r.status == "SUCCESS"]
        s2_failed = [r for r in s2_results if r.status == "FAILED"]
        silent = [r for r in s2_success if r.is_silent_failure]

        summary: dict[str, Any] = {
            "stage2_total": len(s2_results),
            "stage2_success": len(s2_success),
            "stage2_failed": len(s2_failed),
            "stage2_success_rate": round(len(s2_success) / max(len(s2_results), 1), 3),
            "silent_failures": len(silent),
            "silent_failure_rate": round(len(silent) / max(len(s2_success), 1), 3),
            "stage4_total": len(judgments),
        }

        if s2_success:
            rei_c_vals = [r.rei_c for r in s2_success if r.rei_c is not None]
            if rei_c_vals:
                summary["rei_c_mean"] = round(np.mean(rei_c_vals), 2)
                summary["rei_c_median"] = round(np.median(rei_c_vals), 2)

        if judgments:
            parsed = [j for j in judgments if j.get("parsed")]
            summary["stage4_parsed"] = len(parsed)
            summary["stage4_parse_rate"] = round(len(parsed) / max(len(judgments), 1), 3)
            all_jc: dict[str, int] = {}
            for j in parsed:
                for jt, count in j.get("judgment_counts", {}).items():
                    all_jc[jt] = all_jc.get(jt, 0) + count
            summary["judgment_distribution"] = all_jc

        return summary


# ── CLI ───────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(description="Unified AI Metrology Benchmark Runner")
    parser.add_argument("--stages", type=str, default="2,4",
                       help="Comma-separated stages (default: 2,4)")
    parser.add_argument("--models", type=str, default="qwen3-32b",
                       help="Comma-separated model names")
    parser.add_argument("--condition", type=str, default=DEFAULT_CONDITION,
                       choices=["oracle", "chain"])
    parser.add_argument("--level", type=str, default=DEFAULT_INFO_LEVEL,
                       choices=["L1", "L2", "L3"],
                       help="Information level for Stage 2")
    parser.add_argument("--n-test", type=int, default=N_TEST_PAPERS)
    parser.add_argument("--workers", type=int, default=DEFAULT_CONCURRENCY)
    parser.add_argument("--output", type=str, default=str(OUTPUT_DIR))
    parser.add_argument("--papers", type=str, default="all",
                       help="Paper IDs (comma-separated) or 'all'")
    parser.add_argument("--resume", type=str, default=None)
    args = parser.parse_args()

    stages = [int(s.strip()) for s in args.stages.split(",")]
    model_names = [m.strip() for m in args.models.split(",")]
    paper_ids = None if args.papers == "all" else \
        [p.strip() for p in args.papers.split(",")]

    available = get_available_models()
    for mn in model_names:
        if mn != "mock" and mn not in available:
            print(f"Warning: Model '{mn}' may not be available. "
                  f"Detected: {list(available.keys())}")

    print("=" * 60)
    print("AI METROLOGY BENCHMARK RUNNER")
    print(f"  Stages: {stages} | Models: {model_names}")
    print(f"  Condition: {args.condition} | Level: {args.level}")
    print(f"  Test Papers: {args.n_test} | Workers: {args.workers}")
    print("=" * 60)

    runner = BenchmarkRunner(
        stages=stages, models=model_names,
        condition=args.condition, info_level=args.level,
        n_test_papers=args.n_test, workers=args.workers,
        output_dir=args.output, paper_ids=paper_ids,
    )

    if args.resume:
        print(f"\nResuming from {args.resume}...")
        prev = json.loads(Path(args.resume).read_text())
        print(f"  Previous run: {prev.get('run_id')} "
              f"with {prev.get('n_stage2_results', 0)} results")
        print("  (Resume not fully implemented — running fresh)")

    run = runner.run()

    s = run.summary
    print(f"\n{'='*60}")
    print("FINAL SUMMARY")
    print(f"  Stage 2: {s['stage2_success']}/{s['stage2_total']} "
          f"({s['stage2_success_rate']:.1%})")
    print(f"  Silent failures: {s['silent_failures']} "
          f"({s.get('silent_failure_rate', 0):.1%} of successes)")
    if "rei_c_mean" in s:
        print(f"  REI-c: mean={s['rei_c_mean']}, median={s['rei_c_median']}")
    if s.get("stage4_total", 0) > 0:
        print(f"  Stage 4: {s.get('stage4_parsed', 0)}/{s['stage4_total']} "
              f"({s.get('stage4_parse_rate', 0):.1%})")
        if "judgment_distribution" in s:
            print(f"  Judgments: {s['judgment_distribution']}")
    print(f"{'='*60}")


if __name__ == "__main__":
    main()
