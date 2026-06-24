"""LLM-as-judge for Stages 1, 3, and 4.

Provides a uniform interface for using one LLM to evaluate the output of
another LLM. Supports calibration against human annotations.

For Stages 1 and 3, the judge compares LLM output against the paper's
actual content (Methods section for Stage 1, Conclusions for Stage 3).

For Stage 4, judge evaluation is embedded in stage4_judgment.py since
judgment IS the task (not a separate evaluation step).
"""

from __future__ import annotations

from typing import Any


def judge_design_quality(
    llm: Any,
    proposed_design: str,
    actual_methods: str,
    paper_title: str,
) -> dict[str, Any]:
    """Evaluate a Stage 1 research design proposal against the paper's actual Methods.

    Args:
        llm: LangChain-compatible LLM for judging.
        proposed_design: The LLM's proposed experimental design.
        actual_methods: The paper's actual Methods section text.
        paper_title: Paper title for context.

    Returns:
        Dict with {alignment, feasibility, completeness, overall, rationale}.
        Each dimension is scored 1-5.
    """
    prompt = f"""You are evaluating an AI's research design proposal against the actual methods used in a scientific paper.

## Paper: {paper_title}

## AI-Proposed Research Design
{proposed_design[:5000]}

## Actual Methods (from the paper)
{actual_methods[:5000]}

## Task
Rate the AI's proposed design on three dimensions (1=poor, 5=excellent):

1. **alignment** (1-5): How well does the proposed design match what the paper actually did?
   - 5 = Nearly identical to the actual methods
   - 3 = Some overlap but different approach
   - 1 = Completely different approach

2. **feasibility** (1-5): Is the proposed design executable with bibliometric data?
   - 5 = Fully specified, clearly implementable
   - 3 = Vague but directionally feasible
   - 1 = Impractical or impossible

3. **completeness** (1-5): Does it cover data, variables, analysis, and expected results?
   - 5 = All elements specified
   - 3 = Missing 1-2 elements
   - 1 = Only mentions the topic without specifics

Output ONLY JSON:
```json
{{"alignment": <1-5>, "feasibility": <1-5>, "completeness": <1-5>,
 "overall": <mean of 3>, "rationale": "<2-3 sentences>"}}
```
"""
    response = llm.invoke([{"role": "user", "content": prompt}])
    text = response.content if hasattr(response, "content") else str(response)
    if isinstance(text, list):
        text = "\n".join(b.get("text", "") for b in text if isinstance(b, dict))

    import json, re
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        m = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {"alignment": 0, "feasibility": 0, "completeness": 0,
                "overall": 0, "rationale": "JSON parse failed",
                "raw": text[:500]}


def judge_conclusion_quality(
    llm: Any,
    derived_conclusions: str,
    actual_conclusions: str,
    paper_title: str,
) -> dict[str, Any]:
    """Evaluate Stage 3 derived conclusions against the paper's actual Conclusions.

    Args:
        llm: LangChain-compatible LLM for judging.
        derived_conclusions: LLM-derived conclusions from experimental results.
        actual_conclusions: The paper's actual Discussion/Conclusion section.
        paper_title: Paper title for context.

    Returns:
        Dict with {coverage, consistency, over_inference, overall, rationale}.
        Each dimension is scored 1-5.
    """
    prompt = f"""You are evaluating an AI's derived conclusions against a published paper's actual conclusions.

## Paper: {paper_title}

## AI-Derived Conclusions (from experimental results only)
{derived_conclusions[:5000]}

## Paper's Actual Conclusions
{actual_conclusions[:5000]}

## Task
Rate the AI's derived conclusions on three dimensions (1=poor, 5=excellent):

1. **coverage** (1-5): How many of the paper's key claims did the AI identify?
   - 5 = Nearly all major claims covered
   - 3 = About half the claims covered
   - 1 = Missed most or all claims

2. **consistency** (1-5): Do the derived conclusions align in direction/strength?
   - 5 = Same direction and similar magnitude
   - 3 = Same direction but different interpretation
   - 1 = Contradicts the paper's conclusions

3. **over_inference** (1-5, reversed): Did the AI claim more than data supports?
   - 5 = Claims are appropriately scoped to what data shows
   - 3 = Some over-reaching claims
   - 1 = Multiple unsupported claims

Output ONLY JSON:
```json
{{"coverage": <1-5>, "consistency": <1-5>, "over_inference": <1-5>,
 "overall": <mean of 3>, "rationale": "<2-3 sentences>"}}
```
"""
    response = llm.invoke([{"role": "user", "content": prompt}])
    text = response.content if hasattr(response, "content") else str(response)
    if isinstance(text, list):
        text = "\n".join(b.get("text", "") for b in text if isinstance(b, dict))

    import json, re
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        m = re.search(r'\{[^}]+\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return {"coverage": 0, "consistency": 0, "over_inference": 0,
                "overall": 0, "rationale": "JSON parse failed",
                "raw": text[:500]}
