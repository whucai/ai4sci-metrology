"""Stage 2: Bibliometric Experiment Reproduction.

Given a paper's methodology description (or formula, or concept), the LLM must:
  1. Understand the computational method
  2. Generate Python code implementing it
  3. Execute against SciSciNet data
  4. Self-correct on errors (up to 4 attempts)

Supports three information levels:
  - L1 (Specification Translation): exact formula + algorithm given
  - L2 (Text Extraction): paper title+abstract, formula must be extracted
  - L3 (Conceptual Inference): full paper text, method must be located and understood

Wraps the core logic from run_manual_papers_benchmark.py into the BaseStage interface.
"""

from __future__ import annotations

import os
import re
import tempfile
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd

from .base import BaseStage
from ..types import PaperEntry, StageResult, Condition, InfoLevel
from ..config import SANDBOX_TIMEOUT, MAX_FIX_ITERATIONS, MAX_PAPER_CHARS, CORRECTNESS_TOLERANCE
from ..papers.registry import METRIC_TYPE_MAP

# Reuse existing stable modules
from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.metric_templates import (
    get_prompt as get_metric_prompt,
    parse_metric_output,
    compute_ground_truth,
    get_primary_metric,
    METRIC_CONFIGS,
)
from src.sciscigpt_local.sciscinet_connector import load_table
from src.sciscigpt_local.rei_metric import compute_rei_c, flag_silent_failure

ERROR_WEIGHTS = {"syntax": 1, "import": 2, "runtime": 3, "timeout": 5}

PER_PAPER_METRICS = {"disruption", "citation_count_prediction", "network_normalized_impact",
                    "sleeping_beauty"}
DATASET_METRICS = {"team_size_effect", "disruption_temporal", "citation_inflation",
                   "frontier_author_impact", "career_mobility",
                   "novelty_conventionality", "interdisciplinarity", "altmetrics"}


def _extract_code(text: str) -> str:
    """Extract Python code from LLM response."""
    if "```python" in text:
        parts = text.split("```python", 1)[1].split("```")
        if parts:
            return parts[0].strip()
    if "```" in text:
        parts = text.split("```", 1)[1].split("```")
        if parts:
            return parts[0].strip()
    return text.strip()


def _build_patent_section(kwargs: dict) -> tuple[str, str, str]:
    """Build patent-specific prompt sections when patent data is available."""
    has_patent = kwargs.get("has_patent_data", False)
    patents_path = kwargs.get("patents_path", "")

    if not has_patent or not patents_path:
        return "", "", ""

    patent_section = (
        f"- Patent abstracts CSV at '{patents_path}': "
        f"columns patent_id, patent_abstract, claim_text"
    )
    patent_steps = (
        "7. Load patent data from the patents CSV\n"
        "8. Count patents per CPC class (comma-separated cpc_ids), "
        "compute patent technology diversity\n"
        "9. Compare paper metrics with patent landscape: "
        "mean patent count per year, patent technology breadth"
    )
    patent_output = (
        ", PATENT_COUNT = <count>, PATENT_CPC_DIVERSITY = <unique_classes>"
    )
    return patent_section, patent_steps, patent_output


def _classify_error(stderr: str) -> str:
    """Classify error type from stderr."""
    s = stderr.lower()
    if "syntaxerror" in s or "indentationerror" in s:
        return "syntax"
    if "modulenotfounderror" in s or "importerror" in s:
        return "import"
    if "timeout" in s or "timed out" in s:
        return "timeout"
    return "runtime"


def build_l3_prompt(
    paper_text: str,
    paper: PaperEntry,
    test_paper_id: int,
    test_title: str,
    metric_type: str,
    papers_path: str = "",
    refs_path: str | None = None,
    cites_path: str | None = None,
    **extra_kwargs: Any,
) -> str:
    """L3 prompt: full paper text + SciSciNet test paper data."""
    config = METRIC_CONFIGS[metric_type]
    task_label = config["label"]

    max_chars = MAX_PAPER_CHARS
    if len(paper_text) > max_chars:
        paper_content = paper_text[:max_chars] + "\n\n[... truncated ...]\n\n" + paper_text[-3000:]
    else:
        paper_content = paper_text

    output_hint = config.get("output_patterns", {})
    print_keys = list(output_hint.keys())[:4]

    if metric_type == "disruption" and refs_path and cites_path:
        data_section = f"""Data files:
- References CSV at '{refs_path}': columns reference_id — papers cited BY test paper {test_paper_id}
- Citation network CSV at '{cites_path}': columns citing_paper_id, cited_paper_id
  Lists ALL citations FROM papers that cite paper {test_paper_id}.

Test paper {test_paper_id}: "{test_title}"

Implement the metric described in the methodology paper.
Print: {', '.join(f'{k} = <value>' for k in print_keys)}
"""
    elif metric_type in PER_PAPER_METRICS:
        data_section = f"""Data files:
- Papers CSV at '{papers_path}': columns paper_id, year, citation_count, disruption_score, author_count
{f"- Citation network CSV at '{cites_path}': columns citing_paper_id, cited_paper_id" if cites_path else ""}

Test paper {test_paper_id}: "{test_title}"

Implement the metric from the methodology paper.
Print: {', '.join(f'{k} = <value>' for k in print_keys)}
"""
    elif metric_type in DATASET_METRICS:
        data_section = f"""Data file:
- Papers CSV at '{papers_path}': includes year, citation_count, disruption_score, author_count

This is a dataset-level analysis. Apply the method from the paper to the entire dataset.
Print: {', '.join(f'{k} = <value>' for k in print_keys)}
"""
    else:
        extra_files = ""
        if extra_kwargs.get("paper_fields_path"):
            extra_files += f"\n- Paper-Fields CSV at '{extra_kwargs['paper_fields_path']}': columns paper_id, field_id"
        if extra_kwargs.get("paper_twitter_path"):
            extra_files += f"\n- Paper-Twitter CSV at '{extra_kwargs['paper_twitter_path']}': columns paper_id, tweet_id"
        if extra_kwargs.get("patents_path"):
            extra_files += f"\n- Patent Abstracts CSV at '{extra_kwargs['patents_path']}': columns patent_id, patent_abstract, claim_text"
        data_section = f"""Data file:
- Papers CSV at '{papers_path}'{extra_files}

Implement the metric from the methodology paper.
Print results with appropriate labels.
"""

    return f"""## Methodology Paper (full text)

{paper_content}

## Task: Reproduce the Method

{data_section}

IMPORTANT: Write Python code that implements the method described in the paper above.
Study the paper's description carefully. Output ONLY Python code in a ```python block.
"""


class Stage2Reproduction(BaseStage):
    """Stage 2: Reproduce bibliometric experiments from method descriptions."""

    stage_number = 2
    stage_name = "Bibliometric Experiment Reproduction"

    def __init__(
        self,
        papers_df: pd.DataFrame | None = None,
        pc: pd.DataFrame | None = None,
        metric_type: str | None = None,
        level: InfoLevel = "L2",
    ):
        """Initialize Stage 2 with data and settings.

        Args:
            papers_df: SciSciNet papers DataFrame (loaded lazily if None).
            pc: SciSciNet paper_citations DataFrame.
            metric_type: Override paper's default metric type.
            level: L1 (formula), L2 (abstract), or L3 (full paper).
        """
        self._papers_df = papers_df
        self._pc = pc
        self._override_metric = metric_type
        self.level = level

    @property
    def papers_df(self) -> pd.DataFrame:
        if self._papers_df is None:
            self._papers_df = load_table("papers")
        return self._papers_df

    @property
    def pc(self) -> pd.DataFrame:
        if self._pc is None:
            self._pc = load_table("paper_citations")
        return self._pc

    def get_metric_type(self, paper: PaperEntry) -> str:
        return self._override_metric or paper.metric_type

    # ── Prompt building ──────────────────────────────────────────────

    def build_oracle_prompt(
        self, paper: PaperEntry, test_paper: dict | None = None, **kwargs
    ) -> str:
        """Build prompt from paper text sections."""
        test_paper = test_paper or {}
        test_id = test_paper.get("paper_id", 0)
        test_title = str(test_paper.get("title", ""))[:80]
        metric_type = self.get_metric_type(paper)
        config = METRIC_CONFIGS[metric_type]

        papers_path = test_paper.get("papers_path", test_paper.get("full_papers_path", ""))
        refs_path = test_paper.get("_refs_path")
        cites_path = test_paper.get("_cites_path")

        if self.level == "L3":
            # Full paper text as the methodology source
            paper_text = paper.methods or paper.intro or ""
            if not paper_text:
                md_path = Path(paper.md_path)
                if not md_path.is_absolute():
                    md_path = Path(__file__).resolve().parent.parent.parent.parent / md_path
                paper_text = md_path.read_text(encoding="utf-8", errors="replace") if md_path.exists() else ""
            patent_section, patent_steps, patent_output = _build_patent_section(kwargs)
            return build_l3_prompt(
                paper_text, paper, test_id, test_title,
                metric_type, papers_path, refs_path, cites_path,
                patent_section=patent_section, patent_steps=patent_steps,
                patent_output=patent_output,
                **kwargs,
            )

        elif self.level == "L2":
            # Abstract/title only — LLM must infer method
            data_path = papers_path
            if metric_type in DATASET_METRICS:
                data_path = test_paper.get("full_papers_path", papers_path)
            # Build patent data section if available
            patent_section, patent_steps, patent_output = _build_patent_section(kwargs)
            prompt_kwargs = dict(
                paper_id=test_id, papers_path=data_path,
                cites_path=cites_path or "", refs_path=refs_path or "",
                patent_section=patent_section, patent_steps=patent_steps,
                patent_output=patent_output,
                **kwargs,
            )
            return f"""Read about this methodology:
{paper.title}

{config['prompt'].format(**prompt_kwargs)}
"""

        else:  # L1: formula + algorithm given directly
            data_path = papers_path
            if metric_type in DATASET_METRICS:
                data_path = test_paper.get("full_papers_path", papers_path)
            patent_section, patent_steps, patent_output = _build_patent_section(kwargs)
            prompt_kwargs = dict(
                paper_id=test_id, papers_path=data_path,
                patent_section=patent_section, patent_steps=patent_steps,
                patent_output=patent_output,
                **kwargs,
            )
            if refs_path:
                prompt_kwargs["refs_path"] = refs_path
            if cites_path:
                prompt_kwargs["cites_path"] = cites_path
            return get_metric_prompt(metric_type, **prompt_kwargs)

    def build_chain_prompt(
        self, paper: PaperEntry, previous_output: StageResult, **kwargs
    ) -> str:
        """Build prompt from Stage 1 design output."""
        design = previous_output.output.get("design", {})
        strategy = design.get("strategy", design.get("analysis_strategy", ""))
        variables = design.get("variables", "")

        test_paper = kwargs.get("test_paper", {})
        test_id = test_paper.get("paper_id", 0)
        metric_type = self.get_metric_type(paper)

        design_text = f"""## Research Design (from Stage 1)

Analysis Strategy: {strategy}

Key Variables: {variables}

## Task

Implement the analysis strategy described above for test paper {test_id}.
Use SciSciNet data. Output ONLY Python code in a ```python block.
"""
        return design_text

    # ── Output parsing ───────────────────────────────────────────────

    def parse_output(self, response: str) -> dict[str, Any]:
        """Extract code from LLM response. Execution happens in run_with_execution()."""
        code = _extract_code(response)
        return {"code": code, "raw_response": response}

    # ── Evaluation ───────────────────────────────────────────────────

    def evaluate(
        self, output: dict, ground_truth: dict, paper: PaperEntry
    ) -> dict[str, Any]:
        """Not used directly — evaluation is embedded in run_with_execution."""
        return {}

    # ── Full execution with sandbox ──────────────────────────────────

    def run_with_execution(
        self,
        llm: Any,
        paper: PaperEntry,
        test_paper: dict,
        condition: Condition = "oracle",
        previous_output: StageResult | None = None,
        **kwargs,
    ) -> StageResult:
        """Run Stage 2 end-to-end: prompt → code → execute → self-correct.

        This is the main entry point. It extends BaseStage.run() with
        sandbox execution and the self-correction loop.
        """
        t0 = __import__("time").time()

        test_id = test_paper["paper_id"]
        metric_type = self.get_metric_type(paper)

        # Prepare temp citation data files (needed by most metrics)
        refs = self.pc[self.pc["citing_paper_id"] == test_id]["cited_paper_id"].unique()
        citers = self.pc[self.pc["cited_paper_id"] == test_id]["citing_paper_id"].unique()

        refs_path = None
        cites_path = None
        if metric_type in PER_PAPER_METRICS:
            # Per-paper metrics strictly require citation data
            if len(refs) == 0 or len(citers) == 0:
                return StageResult(
                    stage=2, paper_id=paper.id,
                    test_paper_id=str(test_id), condition=condition,
                    info_level=self.level, status="SKIPPED",
                    model=getattr(llm, "model_name", "unknown"),
                    output={"reason": "No citation data for test paper"},
                    elapsed=0.0,
                )

        if len(citers) > 0:
            refs_path = tempfile.mktemp(suffix="_refs.csv")
            cites_path = tempfile.mktemp(suffix="_cites.csv")
            pd.DataFrame({"reference_id": refs}).to_csv(refs_path, index=False)
            citer_cites = self.pc[self.pc["citing_paper_id"].isin(citers)][
                ["citing_paper_id", "cited_paper_id"]
            ].head(100000)
            citer_cites.to_csv(cites_path, index=False)
            test_paper["_refs_path"] = refs_path
            test_paper["_cites_path"] = cites_path

        # Prepare extra data files for metrics that need them
        extra_kwargs: dict[str, Any] = {}
        if metric_type == "interdisciplinarity":
            pf_path = tempfile.mktemp(suffix="_paper_fields.csv")
            pf = load_table("paper_fields")
            pf.to_csv(pf_path, index=False)
            extra_kwargs["paper_fields_path"] = pf_path
        elif metric_type == "altmetrics":
            pt_path = tempfile.mktemp(suffix="_paper_twitter.csv")
            pt = load_table("paper_twitter")
            pt.to_csv(pt_path, index=False)
            extra_kwargs["paper_twitter_path"] = pt_path
        elif metric_type == "frontier_author_impact":
            # Check if patent data is available
            patent_sample_path = Path("data/patentsview/patents_sample_100k.parquet")
            if patent_sample_path.exists():
                patent_df = pd.read_parquet(patent_sample_path)
                patent_csv = tempfile.mktemp(suffix="_patents.csv")
                patent_df.to_csv(patent_csv, index=False)
                extra_kwargs["patents_path"] = patent_csv
                extra_kwargs["has_patent_data"] = True
            else:
                extra_kwargs["has_patent_data"] = False

        # Merge extra kwargs (e.g. paper_fields_path, paper_twitter_path)
        all_kwargs = {**(kwargs or {}), **extra_kwargs}

        # Build prompt
        try:
            if condition == "chain" and previous_output is not None:
                prompt = self.build_chain_prompt(paper, previous_output,
                                                 test_paper=test_paper, **all_kwargs)
                input_source = f"chain_s{previous_output.stage}"
            else:
                prompt = self.build_oracle_prompt(paper, test_paper, **all_kwargs)
                input_source = "oracle"
        except Exception as e:
            return StageResult(
                stage=2, paper_id=paper.id, test_paper_id=str(test_id),
                condition=condition, info_level=self.level, status="ERROR",
                model=getattr(llm, "model_name", "unknown"),
                output={"error": f"Prompt build failed: {e}"},
                elapsed=0.0,
            )

        # Generate code
        response = llm.invoke([{"role": "user", "content": prompt}])
        code = _extract_code(self.extract_text(response))

        # ── Self-correction loop ──
        error_types: list[str] = []
        fix_count = 0
        result_entry: dict[str, Any] | None = None

        # Compute ground truth
        gt = compute_ground_truth(metric_type, test_id, self.papers_df, self.pc)
        gt_value = gt.get(get_primary_metric(metric_type), 0.0) if gt else 0.0

        for attempt in range(MAX_FIX_ITERATIONS):
            exec_result = execute_python(code, timeout=SANDBOX_TIMEOUT)
            stderr = exec_result.get("stderr", "")
            stdout = exec_result.get("stdout", "")

            has_traceback = "Traceback (most recent call last)" in stderr
            is_error = exec_result["exit_code"] != 0 or has_traceback

            if not is_error:
                parsed = parse_metric_output(stdout, metric_type)
                primary_key = get_primary_metric(metric_type)
                if primary_key in parsed:
                    weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
                    rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 0.0
                    computed_val = parsed[primary_key]
                    rei_c, c_ratio, silent = compute_rei_c(rei, gt_value, computed_val)

                    result_entry = {
                        "paper_id": test_id,
                        "methodology_paper": paper.id,
                        "level": self.level, "metric_type": metric_type,
                        "status": "SUCCESS", "rei": rei, "rei_c": rei_c,
                        "computed_primary": computed_val,
                        "ground_truth_primary": gt_value,
                        "is_silent_failure": silent,
                        "fix_count": fix_count, "error_types": error_types,
                        "input_source": input_source,
                        "paper_chars": len(paper.methods or ""),
                        "stdout": stdout,
                    }
                    break

            error_text = stderr or stdout
            error_cat = _classify_error(error_text)
            error_types.append(error_cat)
            fix_count += 1

            if attempt < MAX_FIX_ITERATIONS - 1:
                code = self._fix_code(llm, code, error_text, metric_type, attempt)

        # Clean up temp files
        for p in [refs_path, cites_path]:
            if p:
                try:
                    os.unlink(p)
                except OSError:
                    pass

        elapsed = __import__("time").time() - t0

        if result_entry is None:
            weights = sum(ERROR_WEIGHTS.get(e, 3) for e in error_types)
            rei = round(weights / max(fix_count, 1), 2) if fix_count > 0 else 100.0
            return StageResult(
                stage=2, paper_id=paper.id, test_paper_id=str(test_id),
                condition=condition, info_level=self.level, status="FAILED",
                model=getattr(llm, "model_name", "unknown"),
                output={"code": code, "error_types": error_types, "fix_count": fix_count},
                rei_c=rei, fix_count=fix_count, error_types=error_types,
                computed_primary=None, ground_truth_primary=gt_value,
                is_silent_failure=False, elapsed=round(elapsed, 2),
            )

        return StageResult(
            stage=2, paper_id=paper.id, test_paper_id=str(test_id),
            condition=condition, info_level=self.level, status="SUCCESS",
            model=getattr(llm, "model_name", "unknown"),
            output={"code": code, "stdout": result_entry.get("stdout", "")},
            rei_c=result_entry["rei_c"], fix_count=fix_count,
            error_types=error_types,
            computed_primary=result_entry["computed_primary"],
            ground_truth_primary=result_entry["ground_truth_primary"],
            is_silent_failure=result_entry.get("is_silent_failure", False),
            input_chars=len(prompt), elapsed=round(elapsed, 2),
        )

    def _fix_code(self, llm: Any, code: str, error: str,
                  metric_type: str, attempt: int) -> str:
        """Self-correction: ask LLM to fix code based on error."""
        metric_label = METRIC_CONFIGS[metric_type]["label"]
        prompt = f"""Your Python code for "{metric_label}" produced this error:

```
{error[:800]}
```

Your previous code:
```python
{code[:2000]}
```

Fix the error. Output ONLY the corrected Python code in a ```python block.
The code must print results as: <primary_key> = <value>
"""
        response = llm.invoke([{"role": "user", "content": prompt}])
        return _extract_code(self.extract_text(response))

    # ── Test paper selection ─────────────────────────────────────────

    @staticmethod
    def select_test_papers(
        papers_df: pd.DataFrame,
        pc: pd.DataFrame,
        n: int = 5,
        seed: int = 42,
    ) -> list[dict]:
        """Select SciSciNet papers with good citation data as test cases.

        Stratified by disruption score: high-D, neutral-D, low-D.
        """
        rng = np.random.default_rng(seed)

        df = papers_df.dropna(
            subset=["citation_count", "reference_count", "title", "year"]
        ).copy()
        df = df[(df["reference_count"] >= 2) & (df["citation_count"] >= 5)]

        full_cols = [
            "paper_id", "year", "citation_count", "disruption_score",
            "author_count", "reference_count", "title",
            "novelty_score", "conventionality_score",
        ]
        full_papers_path = tempfile.mktemp(suffix="_papers_full.csv")
        papers_df.dropna(subset=["year", "citation_count"])[full_cols].to_csv(
            full_papers_path, index=False,
        )

        papers_csv_path = tempfile.mktemp(suffix="_papers.csv")
        cols = ["paper_id", "year", "citation_count", "disruption_score", "author_count"]
        df[cols].to_csv(papers_csv_path, index=False)

        df_pos = df[df["disruption_score"] > 0.05]
        df_neu = df[(df["disruption_score"] >= -0.02) & (df["disruption_score"] <= 0.05)]
        df_neg = df[df["disruption_score"] < -0.02]

        selected = []
        for subset, _label in [(df_pos, "high-D"), (df_neu, "neutral-D"), (df_neg, "low-D")]:
            top = subset.nlargest(min(3, len(subset)), "citation_count")
            for _, row in top.iterrows():
                selected.append({
                    "paper_id": int(row["paper_id"]),
                    "title": str(row["title"])[:100],
                    "year": int(row["year"]),
                    "citations": int(row["citation_count"]),
                    "disruption": float(row["disruption_score"]),
                    "papers_path": papers_csv_path,
                    "full_papers_path": full_papers_path,
                })

        seen: set[int] = set()
        unique = [s for s in selected if s["paper_id"] not in seen and not seen.add(s["paper_id"])]  # type: ignore[func-returns-value]
        rng.shuffle(unique)
        return unique[:n]
