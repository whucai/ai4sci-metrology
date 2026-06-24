"""Contamination audit for SciSciBench.

Quantifies the effect of LLM memorization on benchmark validity by running
Task 1 + Task 2 across 4 contamination conditions:
  - Full paper (baseline, no defense)
  - Blind (title/authors removed, idea paraphrased)
  - Blind + Obfuscation (variables renamed to neutral tokens)
  - Logic-Only (pure mathematical formalism)

Hypothesis: Δ(Full − Blind+Obfuscation) for High-risk papers > Δ for Low-risk papers
→ memorization is real and measurable.
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from typing import Any, Literal

from .annotation import SciSciPaper, ContaminationScore
from .tasks.task1_design import Task1Prompt, Task1Runner, ContaminationCondition
from .tasks.task2_conclusion import Task2Prompt, Task2Runner, InfoLevel
from .eval.task1_evaluator import Task1Evaluator, Task1EvalResult
from .eval.task2_evaluator import Task2Evaluator, Task2EvalResult


@dataclass
class ContaminationAuditResult:
    """Results from one contamination condition."""
    paper_id: str
    condition: ContaminationCondition
    contamination_level: str
    task1_result: Task1EvalResult | None = None
    task2_results: dict[str, Task2EvalResult] = field(default_factory=dict)  # L1/L2/L3

    def to_dict(self) -> dict[str, Any]:
        return {
            "paper_id": self.paper_id,
            "condition": self.condition,
            "contamination_level": self.contamination_level,
            "task1": self.task1_result.to_dict() if self.task1_result else None,
            "task2": {lvl: r.to_dict() for lvl, r in self.task2_results.items()},
        }


@dataclass
class ContaminationAudit:
    """Runs a full contamination audit across conditions and papers."""

    llm: Any = None
    conditions: list[ContaminationCondition] = field(default_factory=lambda: [
        "full", "blind", "obfuscated", "logic_only",
    ])
    task2_levels: list[InfoLevel] = field(default_factory=lambda: ["L1", "L2", "L3"])
    task1_evaluator: Task1Evaluator = field(default_factory=Task1Evaluator)
    task2_evaluator: Task2Evaluator = field(default_factory=Task2Evaluator)

    def audit_paper(self, paper: SciSciPaper) -> list[ContaminationAuditResult]:
        """Run all conditions for a single paper."""
        paper.assess_contamination()
        results: list[ContaminationAuditResult] = []

        for condition in self.conditions:
            audit_result = ContaminationAuditResult(
                paper_id=paper.paper_id,
                condition=condition,
                contamination_level=paper.contamination.level if paper.contamination else "unknown",
            )

            # Task 1
            if self.llm:
                t1_prompt = Task1Prompt(paper=paper, condition=condition)
                t1_runner = Task1Runner(llm=self.llm)
                t1_output = t1_runner.run(t1_prompt)

                if t1_output["status"] == "success":
                    gold = paper.to_gold_json()
                    audit_result.task1_result = self.task1_evaluator.evaluate(
                        gold=gold,
                        pred=t1_output["output"],
                        paper_id=paper.paper_id,
                        condition=condition,
                    )

                # Task 2 (all levels)
                t2_runner = Task2Runner(llm=self.llm)
                for level in self.task2_levels:
                    t2_prompt = Task2Prompt(paper=paper, level=level)
                    t2_output = t2_runner.run(t2_prompt)
                    if t2_output["status"] == "success":
                        audit_result.task2_results[level] = self.task2_evaluator.evaluate(
                            gold=paper.to_task2_gold(),
                            pred=t2_output,
                            level=level,
                            paper_id=paper.paper_id,
                        )

            results.append(audit_result)

        return results

    def compute_gap(self, results: list[ContaminationAuditResult]) -> dict[str, Any]:
        """Compute the performance gap between Full and Blind+Obfuscation conditions.

        Groups by contamination risk level and computes Δ for each.
        """
        by_risk: dict[str, dict[str, ContaminationAuditResult]] = {}
        for r in results:
            risk = r.contamination_level
            if risk not in by_risk:
                by_risk[risk] = {}
            by_risk[risk][r.condition] = r

        gaps = {}
        for risk_level, conditions in by_risk.items():
            full = conditions.get("full")
            blind_obf = conditions.get("obfuscated")

            if full and blind_obf:
                # Task 1 gap
                t1_full = full.task1_result.overall_f1 if full.task1_result else 0.0
                t1_blind = blind_obf.task1_result.overall_f1 if blind_obf.task1_result else 0.0
                t1_delta = t1_full - t1_blind

                # Task 2 gap (average across levels)
                t2_deltas = {}
                for level in self.task2_levels:
                    f_score = full.task2_results.get(level).overall_score if level in full.task2_results else 0.0
                    b_score = blind_obf.task2_results.get(level).overall_score if level in blind_obf.task2_results else 0.0
                    t2_deltas[level] = f_score - b_score

                gaps[risk_level] = {
                    "task1_delta": t1_delta,
                    "task2_deltas": t2_deltas,
                    "task1_full": t1_full,
                    "task1_blind_obfuscated": t1_blind,
                }

        return gaps
