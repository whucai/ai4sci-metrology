"""Abstract base class for all four reproduction benchmark stages."""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from typing import Any

from ..types import PaperEntry, StageResult, Condition, StageStatus


class BaseStage(ABC):
    """Abstract interface for a single benchmark stage.

    Each stage implements:
      - build_oracle_prompt: prompt using paper's original text sections
      - build_chain_prompt: prompt using previous stage's LLM output
      - parse_output: extract structured output from LLM response
      - evaluate: score the output against ground truth
    """

    stage_number: int
    stage_name: str

    def extract_text(self, response: Any) -> str:
        """Extract text from LLM response, handling multiple content formats."""
        content = response.content if hasattr(response, "content") else response
        if isinstance(content, list):
            text_parts = [
                b["text"] for b in content
                if isinstance(b, dict) and b.get("type") == "text" and "text" in b
            ]
            return "\n".join(text_parts)
        return str(content)

    @abstractmethod
    def build_oracle_prompt(
        self, paper: PaperEntry, test_paper: dict | None = None, **kwargs
    ) -> str:
        """Build prompt using paper's original text sections."""
        ...

    @abstractmethod
    def build_chain_prompt(
        self, paper: PaperEntry, previous_output: StageResult, **kwargs
    ) -> str:
        """Build prompt using previous stage's LLM output."""
        ...

    @abstractmethod
    def parse_output(self, response: str) -> dict[str, Any]:
        """Parse LLM response into structured output."""
        ...

    @abstractmethod
    def evaluate(
        self, output: dict, ground_truth: dict, paper: PaperEntry
    ) -> dict[str, Any]:
        """Score stage output against ground truth."""
        ...

    def run(
        self,
        llm: Any,
        paper: PaperEntry,
        condition: Condition = "oracle",
        test_paper: dict | None = None,
        previous_output: StageResult | None = None,
        **kwargs,
    ) -> StageResult:
        """Execute this stage for one paper.

        Args:
            llm: LangChain-compatible LLM instance.
            paper: The methodology PaperEntry.
            condition: "oracle" (paper text) or "chain" (previous stage output).
            test_paper: Test paper dict (for Stage 2).
            previous_output: Required for chain condition.

        Returns:
            StageResult with output and metrics.
        """
        t0 = time.time()

        try:
            if condition == "chain" and previous_output is not None:
                prompt = self.build_chain_prompt(paper, previous_output, **(kwargs or {}))
                input_source = f"chain_stage{previous_output.stage}"
            else:
                prompt = self.build_oracle_prompt(paper, test_paper, **(kwargs or {}))
                input_source = "oracle"

            response = llm.invoke([{"role": "user", "content": prompt}])
            text = self.extract_text(response)
            output = self.parse_output(text)

            result = StageResult(
                stage=self.stage_number,
                paper_id=paper.id,
                test_paper_id=str(test_paper.get("paper_id")) if test_paper else None,
                condition=condition,
                status="SUCCESS",
                model=getattr(llm, "model_name", "unknown"),
                output=output,
                input_chars=len(prompt),
                elapsed=round(time.time() - t0, 2),
            )

        except Exception as e:
            result = StageResult(
                stage=self.stage_number,
                paper_id=paper.id,
                test_paper_id=str(test_paper.get("paper_id")) if test_paper else None,
                condition=condition,
                status="ERROR",
                model=getattr(llm, "model_name", "unknown"),
                output={"error": str(e)},
                elapsed=round(time.time() - t0, 2),
            )

        return result
