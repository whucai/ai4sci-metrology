#!/usr/bin/env python3
"""Test Alibaba Cloud LLM connection via OpenAI-compatible API.

Reads credentials from environment variables or .litellm/config.yaml.

Environment variables (optional):
  ALIYUN_API_KEY   API key
  ALIYUN_BASE_URL  e.g. https://...cn-beijing.maas.aliyuncs.com/compatible-mode/v1
  ALIYUN_MODEL     e.g. glm-5.2

Usage:
  python scripts/test_aliyun_openai.py
  python scripts/test_aliyun_openai.py --config .litellm/config.yaml --model glm-5.2
  ALIYUN_API_KEY=sk-... ALIYUN_BASE_URL=... ALIYUN_MODEL=glm-5.2 python scripts/test_aliyun_openai.py
"""

from __future__ import annotations

import argparse
import os
import sys
from pathlib import Path

try:
    import yaml
except ImportError:
    yaml = None

try:
    from openai import OpenAI
except ImportError:
    print("ERROR: openai package not installed. Run: pip install openai", file=sys.stderr)
    sys.exit(1)


DEFAULT_CONFIG = Path(__file__).resolve().parents[1] / ".litellm" / "config.yaml"
DEFAULT_MODEL_ALIAS = "glm-5.2"
TEST_PROMPT = "Reply with exactly: OK"


def load_from_litellm_config(config_path: Path, model_alias: str) -> tuple[str, str, str]:
    if yaml is None:
        raise RuntimeError("PyYAML not installed. Run: pip install pyyaml")

    data = yaml.safe_load(config_path.read_text(encoding="utf-8"))
    for entry in data.get("model_list", []):
        if entry.get("model_name") == model_alias:
            params = entry.get("litellm_params", {})
            api_base = params.get("api_base", "").rstrip("/")
            api_key = params.get("api_key", "")
            model = params.get("model", model_alias)
            if model.startswith("openai/"):
                model = model.split("/", 1)[1]
            if not api_base or not api_key:
                raise ValueError(f"Incomplete config for model '{model_alias}'")
            return api_key, api_base, model
    raise ValueError(f"Model alias '{model_alias}' not found in {config_path}")


def resolve_credentials(args: argparse.Namespace) -> tuple[str, str, str]:
    api_key = args.api_key or os.environ.get("ALIYUN_API_KEY", "")
    base_url = (args.base_url or os.environ.get("ALIYUN_BASE_URL", "")).rstrip("/")
    model = args.model or os.environ.get("ALIYUN_MODEL", "")

    if not (api_key and base_url and model):
        config_path = Path(args.config)
        loaded_key, loaded_base, loaded_model = load_from_litellm_config(
            config_path, args.model_alias
        )
        api_key = api_key or loaded_key
        base_url = base_url or loaded_base
        model = model or loaded_model

    if not api_key:
        raise ValueError("Missing API key. Set ALIYUN_API_KEY or use --config.")
    if not base_url:
        raise ValueError("Missing base URL. Set ALIYUN_BASE_URL or use --config.")
    if not model:
        raise ValueError("Missing model name. Set ALIYUN_MODEL or use --config.")

    return api_key, base_url, model


def mask_key(key: str) -> str:
    if len(key) <= 8:
        return "***"
    return f"{key[:4]}...{key[-4:]}"


def test_connection(api_key: str, base_url: str, model: str, timeout: float) -> None:
    client = OpenAI(api_key=api_key, base_url=base_url, timeout=timeout)

    print("Alibaba Cloud OpenAI-compatible connection test")
    print(f"  base_url : {base_url}")
    print(f"  model    : {model}")
    print(f"  api_key  : {mask_key(api_key)}")
    print(f"  prompt   : {TEST_PROMPT!r}")
    print()

    response = client.chat.completions.create(
        model=model,
        messages=[{"role": "user", "content": TEST_PROMPT}],
        max_tokens=32,
        temperature=0,
    )

    choice = response.choices[0]
    content = (choice.message.content or "").strip()
    usage = response.usage

    print("SUCCESS")
    print(f"  reply      : {content!r}")
    print(f"  finish     : {choice.finish_reason}")
    if usage:
        print(
            f"  tokens     : prompt={usage.prompt_tokens}, "
            f"completion={usage.completion_tokens}, total={usage.total_tokens}"
        )
    if response.id:
        print(f"  request_id : {response.id}")


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--config", type=Path, default=DEFAULT_CONFIG)
    parser.add_argument("--model-alias", default=DEFAULT_MODEL_ALIAS)
    parser.add_argument("--api-key", default="")
    parser.add_argument("--base-url", default="")
    parser.add_argument("--model", default="")
    parser.add_argument("--timeout", type=float, default=60.0)
    args = parser.parse_args()

    try:
        api_key, base_url, model = resolve_credentials(args)
        test_connection(api_key, base_url, model, args.timeout)
        return 0
    except Exception as exc:
        print("FAILED", file=sys.stderr)
        print(f"  error: {exc}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
