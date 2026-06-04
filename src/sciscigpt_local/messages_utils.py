"""Message utilities — extracted from SciSciGPT agents/utils/messages.py.

Stripped of LangChain Hub dependencies, dispatch_custom_event removed
(simplified for local testing).
"""

from __future__ import annotations

import re
import json
from copy import deepcopy
from typing import Any

from langchain_core.messages import HumanMessage, AIMessage, AnyMessage, ToolMessage
from langchain_core.load import dumps


def _extract_xml_tag_from_text(text: str, tag: str) -> str:
    match = re.search(rf"<{tag}>(.*?)</{tag}>", text, re.DOTALL)
    return match.group(1).strip() if (match and match.group(1)) else ""


def _extract_xml_tags_from_text(text: str, tags: list[str]) -> str:
    xml_dict = {tag: _extract_xml_tag_from_text(text, tag) for tag in tags}
    extracted = "\n".join(
        f"<{tag}>{xml_dict[tag]}</{tag}>" for tag in tags if xml_dict[tag]
    )
    return extracted.strip() if extracted else ""


def _remove_xml_tags_from_messages(messages: list[AnyMessage], tags: list[str]):
    messages = deepcopy(messages)
    for tag in tags:
        pattern = re.compile(rf"<{tag}>(.*?)</{tag}>", re.DOTALL)
        for msg in messages:
            if isinstance(msg, AIMessage) and msg.content:
                msg.content = pattern.sub("", str(msg.content)).strip()
    messages = [_format_message(m) for m in messages]
    return messages


def _extract_task_from_message(message):
    current = getattr(message, "metadata", {}).get("current", "")
    if isinstance(message, AIMessage) and "research_manager" in current:
        if not message.tool_calls or len(message.tool_calls) == 0:
            return None
        tc = message.tool_calls[0]
        return {
            "specialist": tc["name"],
            "task": tc["args"].get("task", ""),
            "memory": tc["args"].get("memory", False),
        }
    elif isinstance(message, list):
        for m in reversed(message):
            task = _extract_task_from_message(m)
            if task:
                return task
    return None


def _extract_workflows_from_messages(
    messages: list[AnyMessage], specialist: str, newest: bool = False
) -> list[list[AnyMessage]]:
    workflows = []
    for start in range(len(messages)):
        metadata = getattr(messages[start], "metadata", {})
        task = _extract_task_from_message(messages[start])
        if (
            "research_manager" in metadata.get("current", "")
            and task
            and task.get("specialist", "") in specialist
        ):
            workflow = []
            for i in range(start, len(messages)):
                meta = getattr(messages[i], "metadata", {})
                workflow.append(messages[i])
                if meta.get("current") == "task_eval":
                    break
            workflows.append(workflow)
    if newest:
        return workflows[-1] if workflows else []
    return workflows


def _format_workflow(workflow: list[AnyMessage]) -> list[AnyMessage]:
    task = _extract_task_from_message(workflow)
    messages = [HumanMessage(content=task["task"])]
    for msg in workflow:
        meta = getattr(msg, "metadata", {})
        if "research_manager" in meta.get("current", "") and "specialistset" in meta.get(
            "name", ""
        ):
            continue
        messages.append(msg)
    return messages


def _format_message(message: AnyMessage) -> AnyMessage:
    content = message.content
    if isinstance(content, str):
        content = [{"text": content, "type": "text"}]
    if "text" not in content[0] or content[0]["text"].strip() == "":
        content = [{"text": "EMPTY MESSAGE", "type": "text"}] + content
    message.content = content
    return message


def return_messages(messages, current, next, name):
    for m in messages:
        m.metadata = {"current": current, "next": next, "name": name}
    messages = [_format_message(m) for m in messages]
    return {"messages": messages, "current": current, "next": next}
