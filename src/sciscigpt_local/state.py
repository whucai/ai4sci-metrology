"""AgentState — shared graph state for LangGraph workflow."""

from __future__ import annotations

from typing import Any, Dict, List
from typing_extensions import Annotated, TypedDict
from langchain_core.messages import AnyMessage
from langgraph.graph import add_messages


class AgentState(TypedDict):
    messages: Annotated[list[AnyMessage], add_messages]
    messages_str: str
    metadata: Dict[str, Any]
    current: str
    next: str
