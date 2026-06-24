"""Central configuration for the AI Metrology Benchmark.

All paths, model definitions, and benchmark settings are centralized here.
Environment variables override defaults.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

# ── Project root ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# ── Data paths ──
SCISCINET_DIR = os.environ.get(
    "SCISCINET_DIR",
    str(PROJECT_ROOT.parent / "lzz" / "HC_ARF_20250723" / "data" / "SciSciNet"),
)
BENCHMARK_DIR = PROJECT_ROOT / "bench-mark"
OUTPUT_DIR = PROJECT_ROOT / "refine-logs"
PAPER_METADATA_PATH = BENCHMARK_DIR / "paper_metadata.json"

# ── Sandbox settings ──
SANDBOX_TIMEOUT = int(os.environ.get("SANDBOX_TIMEOUT", "120"))
MAX_FIX_ITERATIONS = int(os.environ.get("MAX_FIX_ITERATIONS", "4"))
CORRECTNESS_TOLERANCE = float(os.environ.get("CORRECTNESS_TOLERANCE", "0.01"))

# ── Paper limits ──
MAX_PAPER_CHARS = int(os.environ.get("MAX_PAPER_CHARS", "30000"))

# ── Test paper sampling ──
N_TEST_PAPERS = int(os.environ.get("N_TEST_PAPERS", "5"))


@dataclass
class ModelConfig:
    """Configuration for a single LLM model."""

    name: str
    provider: str  # "openai" or "anthropic"
    model: str
    api_key_env: str
    base_url_env: str | None = None
    temperature: float = 0.0
    max_tokens: int = 4096
    extra_body: dict[str, Any] = field(default_factory=dict)

    @property
    def api_key(self) -> str | None:
        return os.environ.get(self.api_key_env)

    @property
    def base_url(self) -> str | None:
        if self.base_url_env:
            return os.environ.get(self.base_url_env)
        return None


# ── Available models ──

DEFAULT_MODELS: list[ModelConfig] = [
    ModelConfig(
        name="qwen3-32b",
        provider="openai",
        model=os.environ.get("LLM_MODEL", "Qwen/Qwen3-32B"),
        api_key_env="OPENAI_API_KEY",
        base_url_env="OPENAI_BASE_URL",
        temperature=0.0,
        max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
        extra_body={"enable_thinking": False},
    ),
    ModelConfig(
        name="deepseek-v4-pro",
        provider="anthropic",
        model="deepseek-v4-pro",
        api_key_env="ANTHROPIC_AUTH_TOKEN",
        base_url_env="ANTHROPIC_BASE_URL",
        temperature=0.0,
        max_tokens=4096,
    ),
]


# ── Benchmark defaults ──
DEFAULT_CONCURRENCY = int(os.environ.get("BENCHMARK_WORKERS", "4"))
DEFAULT_STAGES = [2, 4]  # MVP: Stage 2 + Stage 4
DEFAULT_MODEL_NAMES = ["qwen3-32b"]
DEFAULT_CONDITION: str = "oracle"
DEFAULT_INFO_LEVEL: str = "L2"
