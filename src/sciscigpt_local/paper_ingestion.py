"""Paper ingestion module — extract structured methods, data, and analysis steps.

Uses LLM to parse a paper's text content (PDF or markdown) and extract:
  - Title, authors, abstract
  - Method descriptions (algorithms, models, hyperparameters)
  - Dataset references (names, sources, preprocessing)
  - Analysis steps (sequential operations needed to reproduce results)
  - Evaluation metrics
"""

from __future__ import annotations

import json
import re
from typing import Any, Optional

from langchain_core.messages import HumanMessage, SystemMessage
from langchain_core.language_models import BaseChatModel

EXTRACTION_PROMPT = """You are a scientific paper analyzer. Extract structured information from the paper text below.
Output ONLY valid JSON with these fields:

{
  "title": "paper title",
  "authors": ["author1", "author2"],
  "abstract": "concise summary",
  "methods": [
    {"name": "method name", "description": "what it does", "parameters": {"key": "value"}, "implementation": "how to implement"}
  ],
  "datasets": [
    {"name": "dataset name", "source": "where to get it", "size": "N samples", "fields": ["col1", "col2"]}
  ],
  "analysis_steps": [
    {"step": 1, "action": "what to do", "input": "input data", "output": "expected output", "tool": "Python/R/SQL/..."}
  ],
  "evaluation": {
    "metrics": ["metric1", "metric2"],
    "expected_values": {"metric1": "value", "metric2": "value"},
    "comparison_method": "how to compare results"
  },
  "dependencies": ["package1", "package2"],
  "reproducibility_notes": "any special notes about reproducing this paper"
}

If a field is not found in the paper, use an empty list or null.
Do not include any text outside the JSON."""


def extract_paper_structure(text: str, llm: BaseChatModel) -> dict[str, Any]:
    """Extract structured information from paper text using LLM.

    Args:
        text: Full paper text (from PDF or markdown).
        llm: Language model to use for extraction.

    Returns:
        Dict with structured paper information.
    """
    # Truncate to avoid context overflow (~32K chars max for 32B model)
    truncated = text[:25000] if len(text) > 25000 else text

    messages = [
        SystemMessage(content=EXTRACTION_PROMPT),
        HumanMessage(content=f"Paper text:\n\n{truncated}"),
    ]

    response = llm.invoke(messages)
    response_text = str(response.content)

    # Strip thinking tags if present
    response_text = re.sub(r"<think>.*?</think>", "", response_text, flags=re.DOTALL)

    # Extract JSON from response
    json_match = re.search(r"\{.*\}", response_text, re.DOTALL)
    if json_match:
        try:
            return json.loads(json_match.group(0))
        except json.JSONDecodeError:
            pass

    # Fallback: return raw text
    return {"raw_extraction": response_text, "error": "Could not parse JSON from response"}


def format_analysis_plan(structure: dict[str, Any]) -> str:
    """Convert extracted paper structure into an executable analysis plan.

    Args:
        structure: Output from extract_paper_structure.

    Returns:
        A formatted string describing the reproduction plan.
    """
    lines = ["# Paper Reproduction Plan\n"]

    if "title" in structure and structure["title"]:
        lines.append(f"**Paper**: {structure['title']}\n")

    # Datasets
    if structure.get("datasets"):
        lines.append("## Datasets")
        for ds in structure["datasets"]:
            lines.append(f"- **{ds.get('name', 'Unknown')}**: {ds.get('source', 'N/A')}")
            if ds.get("fields"):
                lines.append(f"  Fields: {', '.join(ds['fields'])}")
        lines.append("")

    # Dependencies
    if structure.get("dependencies"):
        lines.append("## Dependencies")
        lines.append(f"```\n{' '.join(structure['dependencies'])}\n```\n")

    # Analysis steps
    if structure.get("analysis_steps"):
        lines.append("## Analysis Steps")
        for s in structure["analysis_steps"]:
            lines.append(f"**Step {s.get('step', '?')}**: {s.get('action', 'N/A')}")
            lines.append(f"  - Input: {s.get('input', 'N/A')}")
            lines.append(f"  - Output: {s.get('output', 'N/A')}")
            lines.append(f"  - Tool: {s.get('tool', 'N/A')}")
        lines.append("")

    # Evaluation
    if structure.get("evaluation"):
        ev = structure["evaluation"]
        lines.append("## Expected Results")
        if ev.get("metrics"):
            lines.append(f"Metrics: {', '.join(ev['metrics'])}")
        if ev.get("expected_values"):
            for k, v in ev["expected_values"].items():
                lines.append(f"  - {k}: {v}")
        lines.append("")

    # Notes
    if structure.get("reproducibility_notes"):
        lines.append(f"## Notes\n{structure['reproducibility_notes']}\n")

    return "\n".join(lines)
