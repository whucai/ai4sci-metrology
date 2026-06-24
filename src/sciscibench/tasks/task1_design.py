"""Task 1: Experiment Design Reconstruction.

Given research idea + data description, the agent must produce a structured
experiment design as a JSON Schema output. Supports 4 contamination conditions:
full, blind, obfuscated, logic-only.
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from typing import Any, Literal

from ..annotation import SciSciPaper

ContaminationCondition = Literal["full", "blind", "obfuscated", "logic_only"]


def _extract_text(content: Any) -> str:
    """Extract text from LLM response, handling both string and list-of-blocks formats."""
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        texts = [b["text"] for b in content if isinstance(b, dict) and b.get("type") == "text"]
        return "\n".join(texts)
    return str(content)


@dataclass
class Task1Prompt:
    """Builds the prompt for Task 1 experiment design reconstruction."""

    paper: SciSciPaper
    condition: ContaminationCondition = "full"
    schema_path: str = ""

    def build_system_prompt(self) -> str:
        return (
            "You are an expert in computational scientometrics and experimental design. "
            "Given a research question and available data, design a rigorous experiment "
            "that can test the stated hypotheses.\n\n"
            "CRITICAL: You MUST output valid JSON conforming exactly to the specified schema. "
            "Do NOT include any text outside the JSON object. Do NOT wrap in markdown code blocks. "
            "Start your response with '{' and end with '}'."
        )

    def build_user_prompt(self) -> str:
        """Build the user prompt based on contamination condition."""
        p = self.paper

        if self.condition == "full":
            return self._build_full_prompt(p)
        elif self.condition == "blind":
            return self._build_blind_prompt(p)
        elif self.condition == "obfuscated":
            return self._build_obfuscated_prompt(p)
        elif self.condition == "logic_only":
            return self._build_logic_only_prompt(p)
        else:
            raise ValueError(f"Unknown condition: {self.condition}")

    def _build_full_prompt(self, p: SciSciPaper) -> str:
        return (
            "## Research Paper\n\n"
            f"**Title**: {p.title}\n"
            f"**Authors**: {', '.join(p.authors)}\n"
            f"**Venue**: {p.venue} ({p.year})\n\n"
            "## Research Idea\n\n"
            f"{p.research_idea}\n\n"
            "## Research Question\n\n"
            f"{p.research_question}\n\n"
            "## Hypotheses\n\n"
            + "\n".join(f"- {h}" for h in p.hypotheses) + "\n\n"
            "## Available Data\n\n"
            f"**Source**: {p.data_source}\n\n"
            f"**Description**: {p.data_description}\n\n"
            f"**Fields**: {', '.join(p.available_fields)}\n\n"
            "## Task\n\n"
            "Design an experiment to test these hypotheses using the available data. "
            "Your output must be valid JSON with these sections:\n"
            "- `independent_variables`: list of {name, type, definition}\n"
            "- `dependent_variables`: list of {name, type, formula}\n"
            "- `control_variables`: list of {name, type, rationale}\n"
            "- `statistical_method`: {family, specification, estimation}\n"
            "- `sample_scope`: {time_window, fields, filters}\n"
            "- `network_construction` (if applicable): {node_type, edge_type, directed, weighted, temporal}\n"
            "- `grouping_strategy`: {groups, rationale}\n"
            "- `robustness_checks`: [{method, rationale}]\n"
            "- `expected_result_form`: {type, key_quantities}\n\n"
            "Output ONLY the JSON object, nothing else."
        )

    def _build_blind_prompt(self, p: SciSciPaper) -> str:
        p.generate_blind_versions()
        return (
            "## Research Context\n\n"
            "A study in computational scientometrics investigates the following:\n\n"
            "## Research Idea\n\n"
            f"{p.blind_idea}\n\n"
            "## Available Data\n\n"
            f"**Source**: A large-scale bibliometric database\n\n"
            f"**Description**: {p.data_description}\n\n"
            f"**Fields**: {', '.join(p.available_fields[:20])}\n\n"
            "## Task\n\n"
            "Design an experiment to test this research question using the available data. "
            "Your output must be valid JSON with these sections:\n"
            "- `independent_variables`: list of {name, type, definition}\n"
            "- `dependent_variables`: list of {name, type, formula}\n"
            "- `control_variables`: list of {name, type, rationale}\n"
            "- `statistical_method`: {family, specification, estimation}\n"
            "- `sample_scope`: {time_window, fields, filters}\n"
            "- `network_construction` (if applicable): {node_type, edge_type, directed, weighted, temporal}\n"
            "- `grouping_strategy`: {groups, rationale}\n"
            "- `robustness_checks`: [{method, rationale}]\n"
            "- `expected_result_form`: {type, key_quantities}\n\n"
            "Output ONLY the JSON object, nothing else."
        )

    def _build_obfuscated_prompt(self, p: SciSciPaper) -> str:
        p.generate_blind_versions()
        return (
            "## Research Context\n\n"
            "A study in computational scientometrics investigates the following:\n\n"
            "## Research Question\n\n"
            f"{p.research_question}\n\n"
            "## Variables (names obfuscated for blind evaluation)\n\n"
            f"{p.obfuscated_idea}\n\n"
            "## Available Data\n\n"
            f"**Source**: A large-scale bibliometric database\n\n"
            f"**Description**: {p.data_description}\n\n"
            "## Task\n\n"
            "Design an experiment to test this research question using the available data. "
            "Use the obfuscated variable names (V1, V2, ...) in your output. "
            "Your output must be valid JSON with these sections:\n"
            "- `independent_variables`: list of {name, type, definition}\n"
            "- `dependent_variables`: list of {name, type, formula}\n"
            "- `control_variables`: list of {name, type, rationale}\n"
            "- `statistical_method`: {family, specification, estimation}\n"
            "- `sample_scope`: {time_window, fields, filters}\n"
            "- `network_construction` (if applicable): {node_type, edge_type, directed, weighted, temporal}\n"
            "- `grouping_strategy`: {groups, rationale}\n"
            "- `robustness_checks`: [{method, rationale}]\n"
            "- `expected_result_form`: {type, key_quantities}\n\n"
            "Output ONLY the JSON object, nothing else."
        )

    def _build_logic_only_prompt(self, p: SciSciPaper) -> str:
        p.generate_blind_versions()
        return (
            "## Mathematical Formalism\n\n"
            f"{p.logic_only_idea}\n\n"
            "## Available Data\n\n"
            f"**Source**: A large-scale bibliometric database\n"
            f"**Fields**: {', '.join(p.available_fields[:15])}\n\n"
            "## Task\n\n"
            "Given the mathematical formalism above, design a complete experiment "
            "that implements these formulas and tests their relationships. "
            "Reconstruct the research question and experimental design from the formalism. "
            "Your output must be valid JSON with these sections:\n"
            "- `independent_variables`: list of {name, type, definition}\n"
            "- `dependent_variables`: list of {name, type, formula}\n"
            "- `control_variables`: list of {name, type, rationale}\n"
            "- `statistical_method`: {family, specification, estimation}\n"
            "- `sample_scope`: {time_window, fields, filters}\n"
            "- `network_construction` (if applicable): {node_type, edge_type, directed, weighted, temporal}\n"
            "- `grouping_strategy`: {groups, rationale}\n"
            "- `robustness_checks`: [{method, rationale}]\n"
            "- `expected_result_form`: {type, key_quantities}\n\n"
            "Output ONLY the JSON object, nothing else."
        )


@dataclass
class Task1Runner:
    """Executes Task 1 against an LLM backend."""

    llm: Any = None
    max_retries: int = 3
    schema: dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        if not self.schema:
            self._load_schema()

    def _load_schema(self):
        import json
        from pathlib import Path
        schema_path = Path(__file__).resolve().parent.parent / "schemas" / "task1_schema.json"
        self.schema = json.loads(schema_path.read_text())

    def run(self, prompt: Task1Prompt) -> dict[str, Any]:
        """Run Task 1: send prompt → parse JSON response."""
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

                # Strip markdown code fences if present
                if raw_output.startswith("```"):
                    raw_output = re.sub(r"^```(?:json)?\s*", "", raw_output)
                    raw_output = re.sub(r"\s*```$", "", raw_output)

                parsed = json.loads(raw_output)
                return {"status": "success", "output": parsed, "raw": raw_output,
                        "attempt": attempt + 1}
            except json.JSONDecodeError as e:
                if attempt < self.max_retries - 1:
                    # Retry with feedback
                    feedback = (
                        f"Your previous response was not valid JSON. Error: {e}. "
                        f"Please output ONLY a valid JSON object starting with '{{' and ending with '}}'."
                    )
                    messages.append(HumanMessage(content=feedback))
                else:
                    return {"status": "json_error", "output": {}, "raw": raw_output,
                            "error": str(e), "attempt": attempt + 1}
            except Exception as e:
                return {"status": "error", "output": {}, "raw": raw_output,
                        "error": str(e), "attempt": attempt + 1}

        return {"status": "failed", "output": {}, "raw": "",
                "error": "Max retries exceeded"}

    def validate_schema(self, output: dict) -> list[str]:
        """Validate output against task1_schema.json. Returns list of violations."""
        violations = []

        # Check required top-level keys
        required = ["independent_variables", "dependent_variables", "control_variables",
                     "statistical_method", "sample_scope"]
        for key in required:
            if key not in output:
                violations.append(f"Missing required field: {key}")

        # Validate independent_variables
        ivs = output.get("independent_variables", [])
        if not isinstance(ivs, list) or len(ivs) < 1:
            violations.append("independent_variables must be non-empty array")
        for iv in ivs:
            for field in ["name", "type", "definition"]:
                if field not in iv:
                    violations.append(f"independent_variable missing '{field}': {iv.get('name', '?')}")

        # Validate dependent_variables
        dvs = output.get("dependent_variables", [])
        if not isinstance(dvs, list) or len(dvs) < 1:
            violations.append("dependent_variables must be non-empty array")
        for dv in dvs:
            for field in ["name", "type", "formula"]:
                if field not in dv:
                    violations.append(f"dependent_variable missing '{field}': {dv.get('name', '?')}")

        # Validate statistical_method
        sm = output.get("statistical_method", {})
        if not isinstance(sm, dict):
            violations.append("statistical_method must be an object")
        else:
            for field in ["family", "specification"]:
                if field not in sm:
                    violations.append(f"statistical_method missing '{field}'")

        # Validate sample_scope
        ss = output.get("sample_scope", {})
        if not isinstance(ss, dict):
            violations.append("sample_scope must be an object")
        elif "time_window" not in ss:
            violations.append("sample_scope missing 'time_window'")

        return violations
