"""Pluggable LLM backends for SciSciGPT local.

Supports:
  - OpenAI-compatible API (Qwen, DeepSeek, etc.)
  - Anthropic-compatible API (Claude via DeepSeek proxy)
  - Local vLLM servers (no auth needed)
  - Mock (deterministic, for testing)

Configuration via environment variables or passed config dict.

Environment variables:
  OPENAI_API_KEY:  API key for OpenAI-compatible endpoints (use "not-needed" for local vLLM)
  OPENAI_BASE_URL: Base URL for OpenAI-compatible endpoint (e.g. http://localhost:8032/v1)
  LLM_MODEL:       Model name/path override
  LLM_MAX_TOKENS:  Max tokens override (default 4096)
  LLM_TEMPERATURE: Temperature override (default 0.0)
"""

from __future__ import annotations

import os
import re
from dataclasses import dataclass
from typing import Any, Optional

from langchain_core.language_models import BaseChatModel
from langchain_core.messages import BaseMessage, AIMessage, HumanMessage, SystemMessage
from langchain_core.outputs import ChatResult, ChatGeneration


@dataclass
class LLMConfig:
    """Structured configuration for an LLM backend."""
    name: str
    provider: str  # "openai" or "anthropic"
    model: str
    api_key: str
    base_url: str = ""
    temperature: float = 0.0
    max_tokens: int = 4096


def _strip_thinking_tags(text: str) -> str:
    """Remove <｜end▁of▁thinking｜> contains `…` tags from Qwen3 thinking mode."""
    return re.sub(r"</?think>", "", text).strip()


def load_llm_from_env(model: str | None = None) -> BaseChatModel:
    """Create an LLM instance based on environment configuration.

    Priority:
      1. OPENAI_API_KEY + OPENAI_BASE_URL → ChatOpenAI (covers local vLLM, Qwen, DeepSeek)
      2. ANTHROPIC_API_KEY + ANTHROPIC_BASE_URL → ChatAnthropic

    Falls back to MockLLM if no credentials found.

    For local vLLM (no auth), set:
      export OPENAI_API_KEY="not-needed"
      export OPENAI_BASE_URL="http://host:port/v1"
      export LLM_MODEL="/path/to/model"
    """
    # OpenAI-compatible path (highest priority, covers vLLM + cloud providers)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        try:
            from langchain_openai import ChatOpenAI

            default_model = model or os.environ.get("LLM_MODEL", "gpt-4o")
            max_tokens = int(os.environ.get("LLM_MAX_TOKENS", "4096"))
            temperature = float(os.environ.get("LLM_TEMPERATURE", "0.0"))

            kwargs: dict[str, Any] = dict(
                model=default_model,
                api_key=openai_key,
                temperature=temperature,
                max_tokens=max_tokens,
                extra_body={"chat_template_kwargs": {"enable_thinking": False}},
            )
            openai_base = os.environ.get("OPENAI_BASE_URL", "")
            if openai_base:
                kwargs["base_url"] = openai_base
            return ChatOpenAI(**kwargs)
        except ImportError:
            pass

    # Anthropic path
    api_key = os.environ.get("ANTHROPIC_API_KEY", "") or os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if api_key:
        try:
            from langchain_anthropic import ChatAnthropic
            base_url = os.environ.get("ANTHROPIC_BASE_URL", "")
            return ChatAnthropic(
                model=model or "claude-sonnet-4-6",
                anthropic_api_key=api_key,
                anthropic_api_url=base_url or None,
                temperature=0.0,
                max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "8192")),
            )
        except ImportError:
            pass

    # Mock fallback
    print("WARNING: No API keys found. Using MockLLM.")
    from src.sciscigpt_local.mock_llm import MockLLM
    return MockLLM()


def load_llm_from_config(config: LLMConfig) -> BaseChatModel:
    """Create an LLM instance from a structured config (bypasses env vars).

    Args:
        config: LLMConfig with provider, model, api_key, base_url, etc.

    Returns:
        A LangChain BaseChatModel instance.

    Raises:
        ValueError: If the provider is unsupported or required packages missing.
    """
    if config.provider == "openai":
        try:
            from langchain_openai import ChatOpenAI
        except ImportError:
            raise ValueError("langchain-openai not installed. pip install langchain-openai")

        kwargs: dict[str, Any] = dict(
            model=config.model,
            api_key=config.api_key,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
            extra_body={"chat_template_kwargs": {"enable_thinking": False}},
        )
        if config.base_url:
            kwargs["base_url"] = config.base_url
        return ChatOpenAI(**kwargs)

    elif config.provider == "anthropic":
        try:
            from langchain_anthropic import ChatAnthropic
        except ImportError:
            raise ValueError("langchain-anthropic not installed. pip install langchain-anthropic")

        return ChatAnthropic(
            model=config.model,
            anthropic_api_key=config.api_key,
            anthropic_api_url=config.base_url or None,
            temperature=config.temperature,
            max_tokens=config.max_tokens,
        )

    raise ValueError(f"Unknown provider: {config.provider}. Use 'openai' or 'anthropic'.")


def get_available_llm_configs() -> list[LLMConfig]:
    """Discover available LLM backends from environment variables.

    Checks OPENAI_API_KEY (Qwen/vLLM) and ANTHROPIC_AUTH_TOKEN (DeepSeek proxy).
    Returns a list of LLMConfig for all configured backends.

    Returns:
        List of LLMConfig, empty if no backends configured.
    """
    configs = []

    # OpenAI-compatible (Qwen via vLLM)
    openai_key = os.environ.get("OPENAI_API_KEY", "")
    if openai_key:
        configs.append(LLMConfig(
            name="qwen3-32b",
            provider="openai",
            model=os.environ.get("LLM_MODEL", "/public/data_share/model_hub/Qwen3-32B/"),
            api_key=openai_key,
            base_url=os.environ.get("OPENAI_BASE_URL", ""),
            temperature=0.0,
            max_tokens=int(os.environ.get("LLM_MAX_TOKENS", "4096")),
        ))

    # Anthropic via DeepSeek proxy
    anthro_key = os.environ.get("ANTHROPIC_AUTH_TOKEN", "")
    if anthro_key:
        configs.append(LLMConfig(
            name="deepseek-v4-pro",
            provider="anthropic",
            model=os.environ.get("ANTHROPIC_DEFAULT_SONNET_MODEL", "claude-sonnet-4-6"),
            api_key=anthro_key,
            base_url=os.environ.get("ANTHROPIC_BASE_URL", ""),
            temperature=0.0,
            max_tokens=4096,
        ))

    return configs
