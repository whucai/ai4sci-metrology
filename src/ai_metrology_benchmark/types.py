"""Shared dataclasses for the benchmark framework."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Literal

Condition = Literal["oracle", "chain"]
StageStatus = Literal["SUCCESS", "FAILED", "SKIPPED", "ERROR"]
ClaimType = Literal["method", "finding", "interpretation"]
Judgment = Literal["SUPPORTED", "PARTIALLY_SUPPORTED", "NOT_SUPPORTED", "NOT_TESTABLE"]
InfoLevel = Literal["L1", "L2", "L3"]


@dataclass
class PaperEntry:
    """A methodology paper in the benchmark."""

    id: str
    md_path: str
    title: str
    journal: str
    year: int
    doi: str
    metric_type: str
    # IMRaD sections (populated by sections.py)
    abstract: str = ""
    intro: str = ""
    methods: str = ""
    results: str = ""
    conclusion: str = ""
    # Testable claims for Stage 4
    claims: list[dict] = field(default_factory=list)
    # Data requirements
    requires_tables: list[str] = field(default_factory=list)


@dataclass
class StageResult:
    """Result from executing a single stage for one paper."""

    stage: int
    paper_id: str
    test_paper_id: str | None = None
    condition: Condition = "oracle"
    info_level: InfoLevel | None = None
    status: StageStatus = "SUCCESS"
    model: str = "unknown"
    # Stage-specific output
    output: dict[str, Any] = field(default_factory=dict)
    # Evaluation metrics
    score: float = 0.0
    metrics: dict[str, float] = field(default_factory=dict)
    # Execution metadata
    input_chars: int = 0
    elapsed: float = 0.0
    fix_count: int = 0
    error_types: list[str] = field(default_factory=list)
    # For Stage 2 specifically
    rei_c: float | None = None
    is_silent_failure: bool = False
    computed_primary: float | None = None
    ground_truth_primary: float | None = None
    # For Stage 4 specifically
    judgments: list[dict] = field(default_factory=list)
    overall_assessment: str = ""


@dataclass
class BenchmarkRun:
    """Top-level container for a full benchmark run."""

    run_id: str
    timestamp: str
    description: str = ""
    models: list[str] = field(default_factory=list)
    papers: list[str] = field(default_factory=list)
    stages: list[int] = field(default_factory=list)
    conditions: list[Condition] = field(default_factory=list)
    stage_results: list[StageResult] = field(default_factory=list)
    summary: dict[str, Any] = field(default_factory=dict)
