"""Prompt-based tool calling for LLMs that don't support native tool calling.

Qwen3-32B via vLLM without --enable-auto-tool-choice cannot use bind_tools().
This module implements a fallback: embed tool descriptions in the prompt and
parse structured tool calls from the LLM's text response.

Format: The LLM is instructed to output tool calls within <tool_call> XML tags:
<tool_call>
{"name": "tool_name", "args": {"arg1": "value1"}}
</tool_call>
"""

from __future__ import annotations

import json
import re
import uuid
from typing import Any

from langchain_core.messages import AIMessage, HumanMessage
from langchain_core.language_models import BaseChatModel


def format_tools_for_prompt(tools: list) -> str:
    """Convert tool definitions into a text description for the prompt."""
    lines = ["Available tools:"]
    for i, tool in enumerate(tools, 1):
        name = tool.name
        desc = tool.description or "No description"
        param_info = ""
        if hasattr(tool, "args_schema") and tool.args_schema:
            try:
                schema = tool.args_schema.schema()
                props = schema.get("properties", {})
                required = schema.get("required", [])
                params = []
                for pname, pinfo in props.items():
                    if pname == "state":
                        continue  # internal, not for LLM
                    req = " (required)" if pname in required else ""
                    ptype = pinfo.get("type", "any")
                    pdesc = pinfo.get("description", "")
                    pdesc = pdesc.split("(ignored)")[0].strip()
                    params.append(f"      {pname}: {ptype}{req} — {pdesc}")
                if params:
                    param_info = "\n" + "\n".join(params)
            except Exception:
                pass
        lines.append(f"  {i}. {name}: {desc}{param_info}")
    return "\n".join(lines)


TOOL_CALL_PROMPT = """
To use a tool, output EXACTLY:

<tool_call>
{"name": "<tool_name>", "args": {"<param>": "<value>"}}
</tool_call>

Only use tool names from the "Available tools" list above.
If you don't need a tool, just write your response directly without any <tool_call> tags.
"""


def parse_tool_calls_from_text(text: str) -> tuple[list[dict[str, Any]], str]:
    """Parse tool calls from <tool_call> tags in LLM output.

    Returns:
        (tool_calls: list of {name, args, id}, remaining_text: str with tags stripped)
    """
    tool_calls = []
    pattern = r'<tool_call>\s*\n?(.*?)\n?\s*</tool_call>'
    matches = re.findall(pattern, text, re.DOTALL)

    for match_text in matches:
        # Try to extract JSON from within the tags
        json_text = match_text.strip()
        # Remove optional ```json fences inside tags
        json_text = re.sub(r'^```(?:json)?\s*\n?', '', json_text)
        json_text = re.sub(r'\n?```$', '', json_text)
        try:
            obj = json.loads(json_text)
            if isinstance(obj, dict) and "name" in obj and "args" in obj:
                tool_calls.append({
                    "name": obj["name"],
                    "args": obj.get("args", {}),
                    "id": f"call_{uuid.uuid4().hex[:12]}",
                })
        except json.JSONDecodeError:
            pass

    # Strip tool_call tags from remaining text
    remaining = re.sub(pattern, '', text, flags=re.DOTALL).strip()

    return tool_calls, remaining


def invoke_with_prompt_tools(
    llm: BaseChatModel,
    messages: list,
    tools: list,
    tool_choice: str = "auto",
    extra_instruction: str | None = None,
) -> AIMessage:
    """Invoke LLM with tools described in prompt, parse tool calls from response.

    Args:
        llm: The chat model instance (without bind_tools).
        messages: List of LangChain messages.
        tools: List of tool objects (must have name and description attributes).
        tool_choice: "auto" (default) — model decides; "required" — must call a tool.
        extra_instruction: Optional extra instruction appended after tool list.
            If None, uses default TOOL_CALL_PROMPT.

    Returns:
        AIMessage with tool_calls populated if the model chose to call a tool.
    """
    tools_text = format_tools_for_prompt(tools)
    instruction = extra_instruction if extra_instruction is not None else TOOL_CALL_PROMPT
    tool_msg = HumanMessage(content=f"{tools_text}\n\n{instruction}")

    all_msgs = list(messages) + [tool_msg]
    response = llm.invoke(all_msgs)
    response_text = str(response.content)

    tool_calls, remaining_text = parse_tool_calls_from_text(response_text)

    if tool_calls:
        response.content = remaining_text or response_text
        response.tool_calls = tool_calls

    return response
