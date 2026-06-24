"""Task 3: Progressive Information Disclosure.

Measures how AutoResearch agent performance changes as more information is given,
from vague idea only (C0) to full experiment + results (C6).

Information conditions:
  C0: Vague research direction only
  C1: Idea + data source name
  C2: Idea + data source + field schema
  C3: Idea + data + variable hints (names only, no definitions)
  C4: Idea + data + experiment hints (method family, but no specification)
  C5: Idea + data + experiment spec + result tables (equivalent to Task 2 L2)
  C6: Idea + data + experiment spec + results + conclusions (full oracle)

Outputs:
  - Per-condition experiment design score and conclusion accuracy
  - Performance curve across C0-C6
  - Scaffold Dependence Index (SDI)
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ..annotation import SciSciPaper

DisclosureLevel = Literal["C0", "C1", "C2", "C3", "C4", "C5", "C6"]


def _extract_text(content: Any) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(texts)
    return str(content)


@dataclass
class Task3Prompt:
    """Builds the prompt for progressive information disclosure experiment design."""

    paper: SciSciPaper
    level: DisclosureLevel = "C4"
    experiment_design: dict[str, Any] = field(default_factory=dict)
    experimental_results: dict[str, Any] = field(default_factory=dict)

    def build_system_prompt(self) -> str:
        return (
            "You are an expert in computational scientometrics and experimental design. "
            "You are given partial information about a research project and must design "
            "appropriate experiments or draw conclusions based on what you know.\n\n"
            "CRITICAL: Output ONLY valid JSON. Start with '{' and end with '}'. "
            "No markdown code blocks, no explanatory text."
        )

    def build_user_prompt(self) -> str:
        p = self.paper
        ed = self.experiment_design or p.to_gold_json()

        if self.level == "C0":
            return self._build_c0(p)
        elif self.level == "C1":
            return self._build_c1(p)
        elif self.level == "C2":
            return self._build_c2(p)
        elif self.level == "C3":
            return self._build_c3(p)
        elif self.level == "C4":
            return self._build_c4(p, ed)
        elif self.level == "C5":
            return self._build_c5(p, ed)
        elif self.level == "C6":
            return self._build_c6(p, ed)
        else:
            raise ValueError(f"Unknown disclosure level: {self.level}")

    def _build_c0(self, p: SciSciPaper) -> str:
        """C0: Vague research direction only — no paper-specific info."""
        return (
            "## Task C0: Vague Research Direction\n\n"
            "You are told that someone is studying the following general topic in "
            "computational scientometrics:\n\n"
            f"**Topic**: {p.research_idea[:200]}...\n\n"
            "You do NOT know the specific hypotheses, data source, variables, or methods.\n\n"
            "## Task\n\n"
            "Given only this vague direction, propose a reasonable experiment design. "
            "Output JSON with:\n"
            "- `research_question`: What specific question would you investigate?\n"
            "- `hypotheses`: List of hypotheses you would test\n"
            "- `independent_variables`: list of {{name, type, definition}}\n"
            "- `dependent_variables`: list of {{name, type, formula}}\n"
            "- `control_variables`: list of {{name, type, rationale}}\n"
            "- `statistical_method`: {{family, specification, estimation}}\n"
            "- `sample_scope`: {{time_window, fields, filters}}\n"
            "- `confidence`: Your confidence in this design (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_c1(self, p: SciSciPaper) -> str:
        """C1: Idea + data source name."""
        return (
            "## Task C1: Idea + Data Source\n\n"
            "You are given a research direction and the name of a data source.\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Data Source**: {p.data_source}\n\n"
            "You do NOT know the field schema or specific variables available.\n\n"
            "## Task\n\n"
            "Design an experiment using this data source. Output JSON with:\n"
            "- `research_question`: Refined research question\n"
            "- `hypotheses`: List of testable hypotheses\n"
            "- `independent_variables`: list of {{name, type, definition}}\n"
            "- `dependent_variables`: list of {{name, type, formula}}\n"
            "- `control_variables`: list of {{name, type, rationale}}\n"
            "- `statistical_method`: {{family, specification, estimation}}\n"
            "- `sample_scope`: {{time_window, fields, filters}}\n"
            "- `assumptions_about_data`: What you assumed about the data\n"
            "- `confidence`: Your confidence in this design (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_c2(self, p: SciSciPaper) -> str:
        """C2: Idea + data source + field schema."""
        return (
            "## Task C2: Idea + Data Source + Field Schema\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Data Source**: {p.data_source}\n\n"
            f"**Data Description**: {p.data_description}\n\n"
            f"**Available Fields**: {', '.join(p.available_fields)}\n\n"
            "You know what fields are available but NOT how to construct variables.\n\n"
            "## Task\n\n"
            "Design an experiment using the available fields. Output JSON with:\n"
            "- `research_question`: Refined research question\n"
            "- `hypotheses`: List of testable hypotheses\n"
            "- `independent_variables`: list of {{name, type, definition}}\n"
            "- `dependent_variables`: list of {{name, type, formula}}\n"
            "- `control_variables`: list of {{name, type, rationale}}\n"
            "- `statistical_method`: {{family, specification, estimation}}\n"
            "- `sample_scope`: {{time_window, fields, filters}}\n"
            "- `data_processing_plan`: How you would preprocess/clean the data\n"
            "- `confidence`: Your confidence in this design (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_c3(self, p: SciSciPaper) -> str:
        """C3: Idea + data + variable hints (names only)."""
        iv_names = [v.get("name", "") for v in p.independent_variables]
        dv_names = [v.get("name", "") for v in p.dependent_variables]
        cv_names = [v.get("name", "") for v in p.control_variables]
        return (
            "## Task C3: Idea + Data + Variable Hints\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Data Source**: {p.data_source}\n\n"
            f"**Available Fields**: {', '.join(p.available_fields)}\n\n"
            f"**Suggested Independent Variables (names only)**: {', '.join(iv_names) if iv_names else 'not provided'}\n"
            f"**Suggested Dependent Variables (names only)**: {', '.join(dv_names) if dv_names else 'not provided'}\n"
            f"**Suggested Control Variables (names only)**: {', '.join(cv_names) if cv_names else 'not provided'}\n\n"
            "You know variable names but NOT their exact definitions, types, or formulas.\n\n"
            "## Task\n\n"
            "Design an experiment using these variable hints. Output JSON with:\n"
            "- `research_question`: Refined research question\n"
            "- `hypotheses`: List of testable hypotheses\n"
            "- `independent_variables`: list of {{name, type, definition}}\n"
            "- `dependent_variables`: list of {{name, type, formula}}\n"
            "- `control_variables`: list of {{name, type, rationale}}\n"
            "- `statistical_method`: {{family, specification, estimation}}\n"
            "- `sample_scope`: {{time_window, fields, filters}}\n"
            "- `confidence`: Your confidence in this design (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_c4(self, p: SciSciPaper, ed: dict) -> str:
        """C4: Idea + data + experiment hints (method family, no full spec)."""
        sm = ed.get("statistical_method", {})
        return (
            "## Task C4: Idea + Data + Method Family Hint\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Research Question**: {p.research_question}\n\n"
            f"**Hypotheses**:\n" + "\n".join(f"- {h}" for h in p.hypotheses) + "\n\n"
            f"**Data Source**: {p.data_source}\n\n"
            f"**Available Fields**: {', '.join(p.available_fields)}\n\n"
            f"**Statistical Method Family**: {sm.get('family', 'unknown')}\n\n"
            "You know the method family but NOT the full specification.\n\n"
            "## Task\n\n"
            "Design a complete experiment. Output JSON with:\n"
            "- `independent_variables`: list of {{name, type, definition}}\n"
            "- `dependent_variables`: list of {{name, type, formula}}\n"
            "- `control_variables`: list of {{name, type, rationale}}\n"
            "- `statistical_method`: {{family, specification, estimation}}\n"
            "- `sample_scope`: {{time_window, fields, filters}}\n"
            "- `robustness_checks`: [{{method, rationale}}]\n"
            "- `confidence`: Your confidence in this design (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_c5(self, p: SciSciPaper, ed: dict) -> str:
        """C5: Idea + data + experiment spec + results."""
        results_str = json.dumps(self.experimental_results, indent=2) if self.experimental_results else (
            "\n".join(f"- {json.dumps(c)}" for c in p.result_claims)
        )
        return (
            "## Task C5: Full Experiment + Results → Conclusions\n\n"
            "You are given the complete research context and experimental results.\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Research Question**: {p.research_question}\n\n"
            f"**Hypotheses**:\n" + "\n".join(f"- {h}" for h in p.hypotheses) + "\n\n"
            f"**Data Source**: {p.data_source}\n"
            f"**Available Fields**: {', '.join(p.available_fields)}\n\n"
            f"**Statistical Method**: {json.dumps(ed.get('statistical_method', {}))}\n\n"
            "## Experimental Results\n\n"
            f"{results_str}\n\n"
            "## Task\n\n"
            "Draw conclusions from these results. Output JSON with:\n"
            "- `conclusions`: List of conclusion claims, each with:\n"
            "  - `claim`, `direction`, `significance`, `support_level`, `evidence`\n"
            "- `limitations`: Limitations of the study\n"
            "- `alternative_explanations`: Plausible alternatives\n"
            "- `confidence`: Your overall confidence (0-1)\n\n"
            "Output ONLY the JSON."
        )

    def _build_c6(self, p: SciSciPaper, ed: dict) -> str:
        """C6: Oracle — everything including conclusions."""
        return (
            "## Task C6: Oracle — Full Information\n\n"
            "You are given the complete research paper — idea, data, experiment, results, "
            "and the original authors' conclusions.\n\n"
            f"**Research Idea**: {p.research_idea}\n\n"
            f"**Research Question**: {p.research_question}\n\n"
            f"**Original Conclusions**:\n" + "\n".join(f"- {c}" for c in p.conclusion_claims) + "\n\n"
            f"**Original Limitations**:\n" + "\n".join(f"- {l}" for l in p.limitations) + "\n\n"
            "## Task\n\n"
            "Given all this information, evaluate the original conclusions. Output JSON with:\n"
            "- `conclusions_validated`: Which original conclusions the data supports\n"
            "- `conclusions_challenged`: Which may be overstated or unsupported\n"
            "- `missing_limitations`: Limitations the authors should have mentioned\n"
            "- `improvement_suggestions`: How the study could be made stronger\n"
            "- `confidence`: Your confidence in your evaluation (0-1)\n\n"
            "Output ONLY the JSON."
        )


@dataclass
class Task3Runner:
    """Executes Task 3 (progressive disclosure) against an LLM backend."""

    llm: Any = None
    max_retries: int = 3

    def run(self, prompt: Task3Prompt) -> dict[str, Any]:
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


@dataclass
class ScaffoldDependenceIndex:
    """Computes SDI metrics from progressive disclosure results.

    SDI = Performance(C-high) - Performance(C-low)
    Measures drop when human scaffolding is removed.
    """

    results: dict[str, dict[str, float]] = field(default_factory=dict)
    # results[paper_id][level] = score

    def compute_sdi(self, high_level: str = "C4", low_level: str = "C0") -> dict[str, float]:
        """Compute per-paper SDI between two disclosure levels."""
        sdi: dict[str, float] = {}
        for pid, scores in self.results.items():
            h = scores.get(high_level, 0)
            l = scores.get(low_level, 0)
            sdi[pid] = h - l
        return sdi

    def compute_performance_curve(self) -> dict[str, list[float]]:
        """Compute mean scores at each disclosure level (across papers)."""
        levels = ["C0", "C1", "C2", "C3", "C4", "C5", "C6"]
        curve: dict[str, list[float]] = {lvl: [] for lvl in levels}
        for pid, scores in self.results.items():
            for lvl in levels:
                if lvl in scores:
                    curve[lvl].append(scores[lvl])
        return curve

    def summary(self) -> dict[str, Any]:
        """Produce summary statistics."""
        curve = self.compute_performance_curve()
        means = {lvl: sum(vals) / len(vals) if vals else 0 for lvl, vals in curve.items()}
        sdi_c0_c4 = means.get("C4", 0) - means.get("C0", 0)
        sdi_c0_c3 = means.get("C3", 0) - means.get("C0", 0)
        return {
            "per_level_means": means,
            "SDI_C0_to_C4": sdi_c0_c4,
            "SDI_C0_to_C3": sdi_c0_c3,
            "interpretation": {
                "sdi_c0_c4": _interpret_sdi(sdi_c0_c4),
                "sdi_c0_c3": _interpret_sdi(sdi_c0_c3),
            },
        }


def _interpret_sdi(sdi: float) -> str:
    if sdi > 0.4:
        return "High scaffold dependence — agent relies heavily on human-provided experiment structure"
    elif sdi > 0.2:
        return "Moderate scaffold dependence — agent benefits from hints but shows some autonomous reasoning"
    elif sdi > 0.05:
        return "Low scaffold dependence — agent can largely reason from first principles"
    else:
        return "Minimal scaffold dependence — agent shows strong autonomous experimental design ability"
