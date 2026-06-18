"""Task 2: Conclusion Inference.

Given research idea + data + experiment design (and optionally results),
the agent must infer conclusions at three difficulty levels:
  L1: Execute experiment → interpret results
  L2: Given results → induce conclusions
  L3: Given partial results → recognize uncertainty
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ..annotation import SciSciPaper

InfoLevel = Literal["L1", "L2", "L3"]


def _extract_text(content: Any) -> str:
    """Extract text from LLM response, handling both string and list-of-blocks formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(texts)
    return str(content)


@dataclass
class Task2Prompt:
    """Builds the prompt for Task 2 conclusion inference."""

    paper: SciSciPaper
    level: InfoLevel = "L2"
    experiment_design: dict[str, Any] = field(default_factory=dict)
    experimental_results: dict[str, Any] = field(default_factory=dict)

    def build_system_prompt(self) -> str:
        return (
            "You are an expert in computational scientometrics and statistical reasoning. "
            "Your task is to draw valid scientific conclusions from experimental evidence, "
            "distinguishing between what the data supports, what it suggests, and what it cannot say.\n\n"
            "CRITICAL: Output ONLY valid JSON. Start with '{' and end with '}'. "
            "No markdown code blocks, no explanatory text."
        )

    def build_user_prompt(self) -> str:
        if self.level == "L1":
            return self._build_l1_prompt()
        elif self.level == "L2":
            return self._build_l2_prompt()
        elif self.level == "L3":
            return self._build_l3_prompt()
        else:
            raise ValueError(f"Unknown level: {self.level}")

    def _research_context(self) -> str:
        p = self.paper
        return (
            f"**Research Question**: {p.research_question}\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Hypotheses**:\n" + "\n".join(f"- {h}" for h in p.hypotheses)
        )

    def _experiment_spec(self) -> str:
        ed = self.experiment_design
        if not ed:
            ed = self.paper.to_gold_json()
        return (
            f"**Independent Variables**: {json.dumps(ed.get('independent_variables', []), indent=2)}\n\n"
            f"**Dependent Variables**: {json.dumps(ed.get('dependent_variables', []), indent=2)}\n\n"
            f"**Control Variables**: {json.dumps(ed.get('control_variables', []), indent=2)}\n\n"
            f"**Statistical Method**: {json.dumps(ed.get('statistical_method', {}), indent=2)}\n\n"
            f"**Sample Scope**: {json.dumps(ed.get('sample_scope', {}), indent=2)}"
        )

    def _build_l1_prompt(self) -> str:
        """L1: idea + data + experiment spec → execute + interpret."""
        return (
            "## Task L1: Execute Experiment and Interpret Results\n\n"
            "You are given a research question, available data, and an experiment specification. "
            "Write Python code to execute this experiment, then interpret the results.\n\n"
            "## Context\n\n"
            f"{self._research_context()}\n\n"
            "## Experiment Specification\n\n"
            f"{self._experiment_spec()}\n\n"
            "## Output Format\n\n"
            "Output a JSON object with:\n"
            "- `code`: Python code to execute the experiment\n"
            "- `expected_results`: What results you expect to see and why\n"
            "- `interpretation`: How to interpret those results relative to the hypotheses\n"
            "- `limitations`: Known limitations of this experimental design\n"
            "- `confidence`: Your confidence in the expected results (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_l2_prompt(self) -> str:
        """L2: idea + data + experiment spec + results table → induce conclusions."""
        results_str = json.dumps(self.experimental_results, indent=2) if self.experimental_results else (
            f"**Result Claims from paper**:\n" +
            "\n".join(f"- {json.dumps(c)}" for c in self.paper.result_claims)
        )
        return (
            "## Task L2: Induce Conclusions from Results\n\n"
            "You are given: research question, experiment design, and experimental results. "
            "Your job is to determine what conclusions the data actually supports.\n\n"
            "## Context\n\n"
            f"{self._research_context()}\n\n"
            "## Experiment Specification\n\n"
            f"{self._experiment_spec()}\n\n"
            "## Experimental Results\n\n"
            f"{results_str}\n\n"
            "## Output Format\n\n"
            "Output a JSON object with:\n"
            "- `conclusions`: List of conclusion claims, each with:\n"
            "  - `claim`: The conclusion statement\n"
            "  - `direction`: The direction of the effect (positive/negative/null/unknown)\n"
            "  - `significance`: Is this statistically significant? (yes/no/unknown)\n"
            "  - `support_level`: How strongly the results support this claim (strong/moderate/weak/none)\n"
            "  - `evidence`: Which specific result(s) support this claim\n"
            "- `boundary_conditions`: Under what conditions do these conclusions hold?\n"
            "- `limitations`: Limitations of the study that qualify the conclusions\n"
            "- `alternative_explanations`: Plausible alternative explanations for the results\n\n"
            "Output ONLY the JSON."
        )

    def _build_l3_prompt(self) -> str:
        """L3: idea + data + experiment spec + PARTIAL results → recognize uncertainty."""
        partial_str = json.dumps(self.experimental_results, indent=2) if self.experimental_results else (
            f"**Partial Results from paper**:\n" +
            "\n".join(f"- {json.dumps(c)}" for c in self.paper.partial_results)
        )
        return (
            "## Task L3: Recognize Uncertainty from Partial Results\n\n"
            "You are given: research question, experiment design, and PARTIAL experimental results. "
            "The results are incomplete — some analyses failed, some data is missing, "
            "some effects are marginal. Your job is to identify what can and CANNOT be concluded.\n\n"
            "## Context\n\n"
            f"{self._research_context()}\n\n"
            "## Experiment Specification\n\n"
            f"{self._experiment_spec()}\n\n"
            "## Partial Results (INCOMPLETE)\n\n"
            f"{partial_str}\n\n"
            "## Critical Guidance\n\n"
            "These results are INCOMPLETE. Be honest about uncertainty. "
            "Do NOT fabricate conclusions the data doesn't support. "
            "If evidence is insufficient, say so explicitly.\n\n"
            "IMPORTANT: Even when evidence is partial, you MUST infer at least "
            "ONE tentative conclusion based on what IS available. State the "
            "direction (positive/negative/null) if any trend is visible, and "
            "note the uncertainty. An empty response is NOT acceptable.\n\n"
            "## Output Format\n\n"
            "Output a JSON object with:\n"
            "- `supported_conclusions`: Claims that CAN be made given the available evidence, each with:\n"
            "  - `claim`: The conclusion statement\n"
            "  - `support_strength`: strong/moderate/weak\n"
            "  - `missing_evidence`: What additional evidence would strengthen this claim\n"
            "- `unsupported_claims`: Claims that CANNOT be made yet, each with:\n"
            "  - `claim`: The unsupported conclusion\n"
            "  - `why_unsupported`: Why the current evidence is insufficient\n"
            "  - `whats_needed`: What additional data/analysis would be needed\n"
            "- `uncertainty_assessment`: Overall assessment of uncertainty (high/moderate/low)\n"
            "- `insufficient_evidence_flag`: true if the evidence is broadly insufficient\n\n"
            "Output ONLY the JSON."
        )


@dataclass
class Task2Runner:
    """Executes Task 2 against an LLM backend."""

    llm: Any = None
    max_retries: int = 3

    def run(self, prompt: Task2Prompt) -> dict[str, Any]:
        """Run Task 2: send prompt → parse JSON response."""
        from langchain_core.messages import SystemMessage, HumanMessage

        messages = [
            SystemMessage(content=prompt.build_system_prompt()),
            HumanMessage(content=prompt.build_user_prompt()),
        ]

        raw_output = ""
        for attempt in range(self.max_retries):
            try:
                response = self.llm.invoke(messages)
                raw_output = _extract_text(response.content if hasattr(response, "content") else str(response))
                raw_output = raw_output.strip()

                if raw_output.startswith("```"):
                    raw_output = re.sub(r"^```(?:json)?\s*", "", raw_output)
                    raw_output = re.sub(r"\s*```$", "", raw_output)

                # Fix invalid JSON escapes from code blocks (e.g. \s, \d, \p in regex or paths)
                raw_output = re.sub(r'\\(?!["\\/bfnrtu])', r'\\\\', raw_output)

                parsed = json.loads(raw_output)
                return {"status": "success", "output": parsed, "raw": raw_output,
                        "level": prompt.level, "attempt": attempt + 1}
            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    feedback = f"Invalid JSON: {e}. Output ONLY a valid JSON object."
                    messages.append(HumanMessage(content=feedback))
                else:
                    return {"status": "json_error", "output": {}, "raw": raw_output,
                            "error": str(e), "level": prompt.level, "attempt": attempt + 1}
            except Exception as e:
                return {"status": "error", "output": {}, "raw": raw_output,
                        "error": str(e), "level": prompt.level, "attempt": attempt + 1}

        return {"status": "failed", "output": {}, "raw": "",
                "error": "Max retries exceeded", "level": prompt.level}
