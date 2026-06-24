#!/usr/bin/env python3
"""SciSciBench — Process-level benchmark for AutoResearch agents in computational scientometrics.

Two core tasks, two evaluation tracks:
  Task 1: Idea + Data → Experiment Design (forced JSON Schema output)
  Task 2: Idea + Data + Experiment → Conclusion (L1/L2/L3 difficulty)

Usage:
    # Quick smoke test on one paper with mock LLM
    python scripts/run_sciscibench.py --pilot --model mock

    # Task 2 baseline (L1/L2/L3) on all papers
    python scripts/run_sciscibench.py --task task2 --model qwen3-32b

    # Full contamination audit (4 conditions × 3 papers)
    python scripts/run_sciscibench.py --audit --model qwen3-32b

    # Task 1 baseline (2 conditions: blind + obfuscation)
    python scripts/run_sciscibench.py --task task1 --condition blind,obfuscated

    # Multi-model comparison
    python scripts/run_sciscibench.py --task task2 --models qwen3-32b,deepseek-v4-pro
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
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscibench.annotation import SciSciPaper, create_wu2019, create_ke2023, create_arts2025, ContaminationScore
from src.sciscibench.tasks.task1_design import Task1Prompt, Task1Runner, ContaminationCondition
from src.sciscibench.tasks.task2_conclusion import Task2Prompt, Task2Runner, InfoLevel
from src.sciscibench.eval.task1_evaluator import Task1Evaluator
from src.sciscibench.eval.task2_evaluator import Task2Evaluator
from src.sciscibench.contamination import ContaminationAudit
from src.sciscigpt_local.llm_backends import LLMConfig, load_llm_from_config

# ── Paper registry (pilot papers) ──────────────────────────────────────────

PILOT_PAPERS: dict[str, SciSciPaper] = {
    "wu2019_disruption": create_wu2019(),
    "ke2023_normalized_impact": create_ke2023(),
    "arts2025_frontier_scientists": create_arts2025(),
}


# ── LLM loading ────────────────────────────────────────────────────────────

def get_available_models() -> dict[str, LLMConfig]:
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


def create_llm(model_name: str) -> Any:
    if model_name == "mock":
        from src.sciscigpt_local.mock_llm import MockLLM
        return MockLLM()
    available = get_available_models()
    if model_name not in available:
        raise ValueError(f"Model '{model_name}' not available. Available: {list(available.keys())}")
    config = available[model_name]
    return load_llm_from_config(config)


# ── Runner ─────────────────────────────────────────────────────────────────

class SciSciBenchRunner:
    """Orchestrates SciSciBench benchmark runs."""

    def __init__(
        self,
        papers: dict[str, SciSciPaper] | None = None,
        model_name: str = "mock",
        output_dir: str = "refine-logs",
    ):
        self.papers = papers or PILOT_PAPERS
        self.model_name = model_name
        self.output_dir = Path(output_dir)
        self.output_dir.mkdir(parents=True, exist_ok=True)
        self.llm = create_llm(model_name)
        self.print_lock = threading.Lock()

    def _print(self, msg: str):
        with self.print_lock:
            print(msg)

    def run_smoke(self) -> dict[str, Any]:
        """Run smoke test: validate gold JSON generation and schema."""
        self._print("=" * 60)
        self._print("M0 SMOKE TEST: Gold JSON Validation")
        self._print("=" * 60)

        results = {}
        for paper_id, paper in self.papers.items():
            self._print(f"\n--- {paper_id}: {paper.title[:80]} ---")

            # Assess contamination
            paper.assess_contamination()
            self._print(f"  Contamination: {paper.contamination.level if paper.contamination else 'unknown'}")

            # Generate gold JSON
            gold = paper.to_gold_json()
            self._print(f"  Gold JSON keys: {list(gold.keys())}")

            # Validate against schema
            evaluator = Task1Evaluator()
            valid, violations = evaluator.validate_schema(gold)
            self._print(f"  Schema valid: {valid}")
            if violations:
                for v in violations:
                    self._print(f"    - {v}")

            # Generate blind versions
            paper.generate_blind_versions()
            self._print(f"  Blind idea length: {len(paper.blind_idea)} chars")
            self._print(f"  Obfuscated idea length: {len(paper.obfuscated_idea)} chars")
            self._print(f"  Logic-only idea length: {len(paper.logic_only_idea)} chars")

            results[paper_id] = {
                "schema_valid": valid,
                "violations": violations,
                "contamination": paper.contamination.level if paper.contamination else "unknown",
                "gold_json_keys": list(gold.keys()),
            }

        # Summary
        all_valid = all(r["schema_valid"] for r in results.values())
        self._print(f"\n{'=' * 60}")
        self._print(f"SMOKE TEST: {'PASSED' if all_valid else 'FAILED — fix schema violations'}")
        self._print(f"{'=' * 60}")

        out_path = self.output_dir / f"sciscibench_smoke_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(results, indent=2, ensure_ascii=False))
        self._print(f"Results: {out_path}")
        return results

    def run_task1(self, conditions: list[ContaminationCondition] | None = None) -> dict[str, Any]:
        """Run Task 1 (Experiment Design) on all papers."""
        conditions = conditions or ["blind", "obfuscated"]
        self._print("=" * 60)
        self._print(f"TASK 1: Experiment Design | Model: {self.model_name}")
        self._print(f"  Papers: {len(self.papers)} | Conditions: {conditions}")
        self._print("=" * 60)

        evaluator = Task1Evaluator()
        all_results: dict[str, dict[str, Any]] = {}

        for paper_id, paper in self.papers.items():
            gold = paper.to_gold_json()
            all_results[paper_id] = {}

            for condition in conditions:
                self._print(f"\n  [{paper_id}] Condition: {condition}")

                prompt = Task1Prompt(paper=paper, condition=condition)
                runner = Task1Runner(llm=self.llm)

                t0 = time.time()
                output = runner.run(prompt)
                elapsed = time.time() - t0

                if output["status"] == "success":
                    eval_result = evaluator.evaluate(
                        gold=gold, pred=output["output"],
                        paper_id=paper_id, condition=condition,
                    )
                    self._print(f"    Status: OK ({elapsed:.1f}s)")
                    self._print(f"    Schema valid: {eval_result.schema_valid}")
                    self._print(f"    Overall F1: {eval_result.overall_f1:.3f}")
                    self._print(f"    IV F1: {eval_result.independent_var_match.f1:.3f}")
                    self._print(f"    DV F1: {eval_result.dependent_var_match.f1:.3f}")
                    self._print(f"    Model match: {eval_result.model_match:.3f}")
                    all_results[paper_id][condition] = eval_result.to_dict()
                else:
                    self._print(f"    Status: {output['status']} ({elapsed:.1f}s) "
                                f"error={output.get('error', '')[:80]}")
                    all_results[paper_id][condition] = output

        out_path = self.output_dir / f"sciscibench_task1_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
        self._print(f"\nResults: {out_path}")
        return all_results

    def run_task2(self, levels: list[InfoLevel] | None = None) -> dict[str, Any]:
        """Run Task 2 (Conclusion Inference) on all papers."""
        levels = levels or ["L1", "L2", "L3"]
        self._print("=" * 60)
        self._print(f"TASK 2: Conclusion Inference | Model: {self.model_name}")
        self._print(f"  Papers: {len(self.papers)} | Levels: {levels}")
        self._print("=" * 60)

        evaluator = Task2Evaluator()
        all_results: dict[str, dict[str, Any]] = {}

        for paper_id, paper in self.papers.items():
            gold = paper.to_task2_gold()
            all_results[paper_id] = {}

            for level in levels:
                self._print(f"\n  [{paper_id}] Level: {level}")

                prompt = Task2Prompt(paper=paper, level=level)
                runner = Task2Runner(llm=self.llm)

                t0 = time.time()
                output = runner.run(prompt)
                elapsed = time.time() - t0

                if output["status"] == "success":
                    eval_result = evaluator.evaluate(
                        gold=gold, pred=output, level=level, paper_id=paper_id,
                    )
                    self._print(f"    Status: OK ({elapsed:.1f}s)")
                    self._print(f"    Overall score: {eval_result.overall_score:.3f}")
                    self._print(f"    Direction accuracy: {eval_result.direction_accuracy:.3f}")
                    if level == "L3":
                        self._print(f"    Uncertainty recognition: {eval_result.uncertainty_recognition:.3f}")
                    all_results[paper_id][level] = eval_result.to_dict()
                else:
                    self._print(f"    Status: {output['status']} ({elapsed:.1f}s) "
                                f"error={output.get('error', '')[:80]}")
                    all_results[paper_id][level] = output

        out_path = self.output_dir / f"sciscibench_task2_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
        self._print(f"\nResults: {out_path}")
        return all_results

    def run_contamination_audit(self) -> dict[str, Any]:
        """Run full contamination audit on all papers."""
        self._print("=" * 60)
        self._print(f"CONTAMINATION AUDIT | Model: {self.model_name}")
        self._print(f"  Papers: {len(self.papers)} | Conditions: full, blind, obfuscated, logic_only")
        self._print("=" * 60)

        auditor = ContaminationAudit(llm=self.llm)
        all_results: dict[str, Any] = {"papers": {}, "gaps": {}}

        for paper_id, paper in self.papers.items():
            self._print(f"\n  [{paper_id}] Running 4 conditions...")
            t0 = time.time()
            audit_results = auditor.audit_paper(paper)
            elapsed = time.time() - t0

            all_results["papers"][paper_id] = {
                "title": paper.title,
                "contamination_level": paper.contamination.level if paper.contamination else "unknown",
                "results": [r.to_dict() for r in audit_results],
                "elapsed": round(elapsed, 1),
            }

            # Per-condition summary
            for ar in audit_results:
                t1_score = ar.task1_result.overall_f1 if ar.task1_result else 0.0
                t2_scores = {lvl: r.overall_score for lvl, r in ar.task2_results.items()}
                self._print(f"    [{ar.condition}] T1={t1_score:.3f} T2={t2_scores}")

        # Compute gaps
        flat_results = [r for pr in all_results["papers"].values() for r in pr.get("results", [])]
        # Convert back from dict
        audit_objects = []
        for pr in all_results["papers"].values():
            for rd in pr.get("results", []):
                audit_objects.append(ContaminationAuditResult(
                    paper_id=rd["paper_id"],
                    condition=rd["condition"],
                    contamination_level=rd["contamination_level"],
                ))
        all_results["gaps"] = auditor.compute_gap(audit_objects)

        # Print gaps
        self._print(f"\n{'=' * 60}")
        self._print("CONTAMINATION GAP ANALYSIS")
        for risk_level, gap in all_results["gaps"].items():
            self._print(f"  {risk_level.upper()} risk: Task1 Δ={gap['task1_delta']:.3f} "
                        f"(full={gap['task1_full']:.3f} → blind+obf={gap['task1_blind_obfuscated']:.3f})")
            for lvl, delta in gap.get("task2_deltas", {}).items():
                self._print(f"    Task2 {lvl} Δ={delta:.3f}")
        self._print(f"{'=' * 60}")

        out_path = self.output_dir / f"sciscibench_audit_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        out_path.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
        self._print(f"\nResults: {out_path}")
        return all_results


# ── CLI ────────────────────────────────────────────────────────────────────

def main():
    parser = argparse.ArgumentParser(
        description="SciSciBench — Process-level AutoResearch Benchmark"
    )
    parser.add_argument("--task", type=str, default=None,
                        choices=["task1", "task2", None],
                        help="Task to run (default: smoke test only)")
    parser.add_argument("--model", type=str, default="mock",
                        help="Model name: mock, qwen3-32b, deepseek-v4-pro")
    parser.add_argument("--models", type=str, default=None,
                        help="Comma-separated model names for multi-model comparison")
    parser.add_argument("--condition", type=str, default=None,
                        help="Comma-separated conditions for Task 1: full,blind,obfuscated,logic_only")
    parser.add_argument("--level", type=str, default=None,
                        help="Comma-separated levels for Task 2: L1,L2,L3")
    parser.add_argument("--pilot", action="store_true",
                        help="Run smoke test without LLM")
    parser.add_argument("--audit", action="store_true",
                        help="Run full contamination audit")
    parser.add_argument("--output", type=str, default="refine-logs")
    args = parser.parse_args()

    runner = SciSciBenchRunner(model_name=args.model, output_dir=args.output)

    if args.pilot or (not args.task and not args.audit):
        runner.run_smoke()

    if args.audit:
        runner.run_contamination_audit()

    if args.task == "task1":
        conditions = None
        if args.condition:
            conditions = [c.strip() for c in args.condition.split(",")]
        runner.run_task1(conditions=conditions)

    if args.task == "task2":
        levels = None
        if args.level:
            levels = [l.strip() for l in args.level.split(",")]
        runner.run_task2(levels=levels)


if __name__ == "__main__":
    main()
