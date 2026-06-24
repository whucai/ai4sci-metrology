"""Stage 4: Conclusion-Evidence Consistency Judgment.

Given a paper's claims + Stage 2 reproduced results, the LLM acts as a
peer reviewer and judges whether the evidence supports each claim.

This is a pure reasoning task — no code generation.

Judgment scale: SUPPORTED / PARTIALLY_SUPPORTED / NOT_SUPPORTED / NOT TESTABLE

Wraps the core logic from run_stage4_benchmark.py into the BaseStage interface.
"""

from __future__ import annotations

import json
import re
from typing import Any

from .base import BaseStage
from ..types import PaperEntry, StageResult, Condition

from src.sciscigpt_local.metric_templates import METRIC_CONFIGS, get_primary_metric


def _parse_json_response(text: str) -> dict | None:
    """Extract and parse JSON from LLM response."""
    if "```json" in text:
        text = text.split("```json", 1)[1].split("```", 1)[0]
    elif "```" in text:
        text = text.split("```", 1)[1].split("```", 1)[0]
    try:
        return json.loads(text.strip())
    except json.JSONDecodeError:
        m = re.search(r'\{.*"judgments".*\}', text, re.DOTALL)
        if m:
            try:
                return json.loads(m.group())
            except json.JSONDecodeError:
                pass
        return None


class Stage4Judgment(BaseStage):
    """Stage 4: Judge whether reproduced evidence supports paper claims."""

    stage_number = 4
    stage_name = "Conclusion-Evidence Consistency Judgment"

    def build_oracle_prompt(
        self, paper: PaperEntry, test_paper: dict | None = None, **kwargs
    ) -> str:
        """Build prompt using paper's original claims and Stage 2 result."""
        stage2_result = kwargs.get("stage2_result", {})
        return self._build_judgment_prompt(paper, stage2_result)

    def build_chain_prompt(
        self, paper: PaperEntry, previous_output: StageResult, **kwargs
    ) -> str:
        """Build prompt using Stage 3 derived conclusions instead of paper claims."""
        stage2_result = kwargs.get("stage2_result", {})
        derived = previous_output.output.get("conclusions", [])

        # Use derived conclusions as the claims to judge
        claims_text = "\n".join(
            f"  [{i}] {c.get('claim', '')}"
            for i, c in enumerate(derived)
        )
        paper_title = paper.title
        paper_journal = f"{paper.journal} ({paper.year})"

        # Build evidence section from Stage 2 result
        evidence = self._format_evidence(stage2_result, paper_title, "chain")

        return f"""You are a scientific peer reviewer evaluating whether experimental results support derived conclusions.

## Derived Conclusions (from Stage 3)

**Source Paper**: {paper_title}
**Journal**: {paper_journal}

{claims_text}

## Experimental Evidence

{evidence}

## Task

For EACH conclusion listed above, judge whether the evidence supports it.
Use: SUPPORTED / PARTIALLY SUPPORTED / NOT SUPPORTED / NOT TESTABLE

Important:
1. A FAILED reproduction does NOT mean the conclusion is wrong — it means the method could not be implemented
2. A numerically correct result (REI-c < 1) provides strong evidence
3. A silent failure (code ran but wrong) provides misleading evidence

Respond in this JSON format:
```json
{{
  "judgments": [
    {{
      "claim_id": "0",
      "judgment": "SUPPORTED",
      "confidence": "high|medium|low",
      "rationale": "One sentence explaining why."
    }}
  ],
  "overall_assessment": {{
    "reproduction_quality": "good|acceptable|poor",
    "main_finding_supported": true,
    "summary": "2-3 sentence overall assessment."
  }}
}}
```

Output ONLY the JSON (no other text)."""

    def parse_output(self, response: str) -> dict[str, Any]:
        """Parse LLM judgment response into structured dict."""
        parsed = _parse_json_response(response)
        if parsed:
            judgments = parsed.get("judgments", [])
            j_types = {}
            for j in judgments:
                jt = j.get("judgment", "UNKNOWN")
                j_types[jt] = j_types.get(jt, 0) + 1
            return {
                "parsed": True,
                "judgments": judgments,
                "overall_assessment": parsed.get("overall_assessment", {}),
                "judgment_counts": j_types,
            }
        return {
            "parsed": False,
            "judgments": [],
            "overall_assessment": {"error": "Failed to parse LLM response"},
            "judgment_counts": {"PARSE_ERROR": 0},
        }

    def evaluate(
        self, output: dict, ground_truth: dict, paper: PaperEntry
    ) -> dict[str, Any]:
        """Compare LLM judgments against human annotations (if available)."""
        if not ground_truth:
            return {"calibrated": False, "note": "No human annotations for comparison"}
        return {
            "calibrated": True,
            "note": "Human comparison requires annotation data (Phase 5)",
        }

    # ── Internal helpers ─────────────────────────────────────────────

    def _build_judgment_prompt(
        self, paper: PaperEntry, stage2_result: dict
    ) -> str:
        """Build the full Stage 4 judgment prompt."""
        claims_text = "\n".join(
            f"  [{c['id']}] ({c.get('type', 'finding')}) {c['text']}"
            for c in paper.claims
        )

        evidence = self._format_evidence(stage2_result, paper.title, "oracle")

        return f"""You are a scientific peer reviewer evaluating whether reproduced experimental results support a published paper's claims.

## Paper Under Review

**Title**: {paper.title}
**Journal**: {paper.journal} ({paper.year})

### Paper's Claims

{claims_text}

## Reproduced Evidence

{evidence}

## Task

For EACH claim listed above, judge whether the reproduced evidence supports it.

Use this scale:
- **SUPPORTED**: The evidence directly confirms the claim
- **PARTIALLY SUPPORTED**: The evidence is consistent with the claim but incomplete or weak
- **NOT SUPPORTED**: The evidence contradicts or fails to confirm the claim
- **NOT TESTABLE**: The reproduced evidence does not directly address this claim

Important considerations:
1. A FAILED reproduction does NOT necessarily mean the claim is wrong — it means the method could not be implemented
2. A numerically correct result (REI-c < 1) provides strong evidence; a silent failure (code ran but wrong) provides misleading evidence
3. Consider whether the test is appropriate for the claim (e.g., computing D-index for one paper ≠ testing "declining trend over decades")

Respond in this JSON format:
```json
{{
  "judgments": [
    {{
      "claim_id": "D1",
      "judgment": "SUPPORTED",
      "confidence": "high|medium|low",
      "rationale": "One sentence explaining why."
    }}
  ],
  "overall_assessment": {{
    "reproduction_quality": "good|acceptable|poor",
    "main_finding_supported": true,
    "summary": "2-3 sentence overall assessment of what this reproduction tells us about the paper."
  }}
}}
```

Output ONLY the JSON (no other text)."""

    def _format_evidence(
        self, result_entry: dict, paper_title: str, condition: str
    ) -> str:
        """Format a Stage 2 result as evidence text."""
        level = result_entry.get("level", result_entry.get("info_level", "L2"))
        metric_type = result_entry.get("metric_type", "disruption")
        metric_label = METRIC_CONFIGS.get(metric_type, {}).get("label", metric_type)
        primary_key = get_primary_metric(metric_type)

        computed = result_entry.get("computed_primary")
        gt = result_entry.get("ground_truth_primary")
        status = result_entry.get("status", "FAILED")
        rei_c = result_entry.get("rei_c", 100)
        silent = result_entry.get("is_silent_failure", False)

        if status == "SUCCESS" and computed is not None:
            denom = max(abs(gt), 1e-8) if gt else 1.0
            rel_err = abs(computed - gt) / denom
            return (
                f"**Stage 2 Reproduction Result:**\n"
                f"- Methodology paper: {paper_title}\n"
                f"- Information level: {level}\n"
                f"- Metric: {metric_label}\n"
                f"- Computed {primary_key}: {computed}\n"
                f"- Ground truth (SciSciNet): {gt}\n"
                f"- Relative error: {rel_err:.4%}\n"
                f"- REI-c: {rei_c:.2f} (0=perfect, >10=serious failure)\n"
                f"- Silent failure: {'YES — code ran but result is wrong' if silent else 'NO — result is numerically correct'}\n"
            )
        else:
            return (
                f"**Stage 2 Reproduction Result:**\n"
                f"- Methodology paper: {paper_title}\n"
                f"- Information level: {level}\n"
                f"- Metric: {metric_label}\n"
                f"- Status: FAILED — could not produce valid output\n"
                f"- REI-c: {rei_c:.2f}\n"
            )


def run_stage4_from_results(
    llm: Any,
    paper_registry: dict[str, PaperEntry],
    stage2_results: list[dict],
) -> list[dict]:
    """Convenience function: run Stage 4 given a list of Stage 2 result dicts.

    This provides backward compatibility with the existing
    run_stage4_benchmark.py workflow.
    """
    stage4 = Stage4Judgment()
    judgments = []

    for s2_result in stage2_results:
        paper_id = s2_result.get("methodology_paper", "")
        if paper_id not in paper_registry:
            continue

        paper = paper_registry[paper_id]
        try:
            result = stage4.run(
                llm, paper, condition="oracle",
                stage2_result=s2_result,
            )
            judgment_entry = {
                "methodology_paper": paper_id,
                "test_paper_id": s2_result.get("paper_id"),
                "level": s2_result.get("level"),
                "stage2_status": s2_result.get("status"),
                "stage2_rei_c": s2_result.get("rei_c"),
                "parsed": result.output.get("parsed", False),
                "judgments": result.output.get("judgments", []),
                "overall_assessment": result.output.get("overall_assessment", {}),
                "judgment_counts": result.output.get("judgment_counts", {}),
            }
            judgments.append(judgment_entry)
        except Exception as e:
            judgments.append({
                "methodology_paper": paper_id,
                "test_paper_id": s2_result.get("paper_id"),
                "error": str(e),
                "parsed": False,
                "judgments": [],
            })

    return judgments
