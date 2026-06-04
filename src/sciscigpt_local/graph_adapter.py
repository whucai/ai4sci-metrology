"""Adapted SciSciGPT LangGraph — local infrastructure version.

Based on sciscigpt_repo/backend/agents/ (nodes.py, sciscigpt.py, evaluation.py).
Key changes vs original:
  - Prompts: embedded text instead of LangChain Hub pulls
  - LLM: configurable backend (mock or Qwen3-32B)
  - Tools: stub implementations (no GCP/Pinecone)
  - Evaluation: synchronous instead of async
  - dispatch_custom_event: removed
"""

from __future__ import annotations

from functools import partial
from typing import Literal

from langgraph.graph import END, START, StateGraph
from langchain_core.messages import HumanMessage, AIMessage, ToolMessage

from src.sciscigpt_local.state import AgentState
from src.sciscigpt_local.messages_utils import (
    _extract_task_from_message,
    _extract_workflows_from_messages,
    _format_workflow,
    _remove_xml_tags_from_messages,
    _extract_xml_tags_from_text,
    return_messages,
)
from src.sciscigpt_local.mock_prompts import (
    research_manager_prompt,
    specialist_prompt_dict,
    tool_eval_prompt,
    visual_eval_prompt,
    task_eval_prompt,
)
from src.sciscigpt_local.prompt_tool_call import invoke_with_prompt_tools


def select_next(state: AgentState) -> Literal[
    "node_research_manager", "node_database_specialist",
    "node_analytics_specialist", "node_literature_specialist",
    "node_evaluation_specialist", "node_specialistset", "node_toolset", END,
]:
    next_val = state["next"]
    return next_val.split(":")[0]


def call_research_manager(load_llm, tools, pruning_func, state: AgentState):
    profile = {"current": "research_manager", "name": "call_research_manager"}
    try:
        llm = load_llm(state["metadata"])
        tools_by_name = {tool.name: tool for tool in tools}
        human = HumanMessage(content="Delegate to a specialist using the <tool_call> format, or provide your final answer.")

        input_msgs = pruning_func([
            *research_manager_prompt.invoke({}).messages,
            *_remove_xml_tags_from_messages(state["messages"], ["thinking"]),
            human,
        ])

        try:
            response = llm.bind_tools(
                list(tools_by_name.values()),
                tool_choice={"type": "auto", "disable_parallel_tool_use": True},
            ).invoke(input_msgs)
        except (NotImplementedError, Exception):
            response = invoke_with_prompt_tools(
                llm, input_msgs, list(tools_by_name.values()), tool_choice="auto",
                extra_instruction="Delegate to one specialist using <tool_call> format, or provide your final answer."
            )

        if len(response.tool_calls) == 0:
            next_step = END
        else:
            next_step = "node_specialistset"
    except Exception as e:
        response = AIMessage(content=f"{type(e).__name__}: {e}")
        next_step = END

    return return_messages([response], "research_manager", next_step, "call_research_manager")


def call_specialist(load_llm, tools, pruning_func, state: AgentState):
    task = _extract_task_from_message(state["messages"])
    if task is None:
        msg = AIMessage(content="No task found. Ending workflow.")
        return return_messages([msg], "specialist", END, "call_specialist")

    specialist_name = task["specialist"]
    task_text = task["task"]
    memory = task.get("memory", False)
    profile = {"current": specialist_name, "name": "call_specialist"}

    try:
        llm = load_llm(state["metadata"])

        workflows = _extract_workflows_from_messages(
            state["messages"], specialist_name, newest=False
        )
        if not workflows:
            # First call — create a fresh workflow with just the task
            newest_msgs = [HumanMessage(content=task_text)]
            historical_msgs: list = []
        else:
            historical_wfs = workflows[:-1]
            newest_wf = workflows[-1]
            historical_msgs = [
                m for w in historical_wfs for m in _format_workflow(w)
            ] if memory else []
            newest_msgs = _format_workflow(newest_wf)

        assert specialist_name in specialist_prompt_dict, (
            f"Invalid specialist: {specialist_name}. "
            f"Valid: {list(specialist_prompt_dict.keys())}"
        )
        sys_msgs = specialist_prompt_dict[specialist_name].invoke({}).messages
        input_msgs = pruning_func([*sys_msgs, *historical_msgs, *newest_msgs])

        try:
            response = llm.bind_tools(
                tools, tool_choice={"type": "auto", "disable_parallel_tool_use": True}
            ).invoke(input_msgs)
        except (NotImplementedError, Exception):
            # Fallback: prompt-based tool calling for LLMs without native tool support
            response = invoke_with_prompt_tools(
                llm, input_msgs, tools, tool_choice="auto"
            )
        response.content = str(response.content)

        if response.tool_calls and response.tool_calls[0]["name"] != "evaluation_specialist":
            next_step = "node_toolset"
            messages = [response]
        else:
            next_step = "node_evaluation_specialist:task_eval"
            response_str = str(response.content)
            if response_str:
                response.tool_calls = []
                response.content = response_str
                messages = [response]
            else:
                messages = []
    except Exception as e:
        next_step = "node_evaluation_specialist:task_eval"
        messages = [AIMessage(content=f"{type(e).__name__}: {e}")]

    return return_messages(messages, specialist_name, next_step, profile["name"])


def call_toolset(tools, state: AgentState):
    import json as _json
    try:
        tools_by_name = {tool.name: tool for tool in tools}
        tool_call = state["messages"][-1].tool_calls[0]
        tool_name = tool_call["name"]
        tool_call_id = tool_call["id"]
        tool_args = tool_call["args"]

        if tool_name not in tools_by_name:
            tool_msg = ToolMessage(
                content=[{"type": "text", "text": _json.dumps(
                    {"error": f"Unknown tool '{tool_name}'. Available: {list(tools_by_name.keys())}"}
                )}],
                tool_call_id=tool_call_id,
            )
            return return_messages([tool_msg], "toolset",
                                  "node_evaluation_specialist:tool_eval", "call_toolset")

        required = tools_by_name[tool_name].args_schema.schema()["properties"].keys()
        tool_args = {k: v for k, v in tool_args.items() if k in required}
        tool_args["state"] = state

        result = tools_by_name[tool_name].invoke(tool_args)
        result = _json.loads(result) if isinstance(result, str) else result
        tool_msg = ToolMessage(
            content=[{"type": "text", "text": _json.dumps(result)}],
            tool_call_id=tool_call_id,
        )
        next_step = "node_evaluation_specialist:tool_eval"
    except Exception as e:
        tool_msg = ToolMessage(
            content=[{"type": "text", "text": _json.dumps({"error": f"{type(e).__name__}: {e}"})}],
            tool_call_id="unknown",
        )
        next_step = "node_evaluation_specialist:tool_eval"

    return return_messages([tool_msg], "toolset", next_step, "call_toolset")


def call_specialistset(specialists, state: AgentState):
    try:
        specialists_by_name = {s.name: s for s in specialists}
        call_data = state["messages"][-1].tool_calls[0]
        specialist_name = call_data["name"]
        specialist_call_id = call_data["id"]
        specialist_args = call_data["args"]

        assert specialist_name in specialists_by_name, (
            f"Invalid specialist: {specialist_name}. "
            f"Valid: {list(specialists_by_name.keys())}"
        )
        result = specialists_by_name[specialist_name].invoke(specialist_args)
        import json
        specialist_msg = ToolMessage(
            content=[{"type": "text", "text": json.dumps(result)}],
            tool_call_id=specialist_call_id,
        )
        next_step = f"node_{specialist_name}"
    except Exception as e:
        specialist_msg = ToolMessage(
            content=[{"type": "text", "text": json.dumps({"error": f"{type(e).__name__}: {e}"})}],
            tool_call_id="unknown",
        )
        next_step = "node_evaluation_specialist:task_eval"

    return return_messages([specialist_msg], "specialistset", next_step, "call_specialistset")


def call_evaluation(load_llm, specialists, pruning_func, state: AgentState):
    llm = load_llm(state["metadata"])
    task = _extract_task_from_message(state["messages"])

    eval_type = state["next"].split(":")[1]
    assert eval_type in ("task_eval", "visual_eval", "tool_eval"), (
        f"Invalid eval type: {eval_type}"
    )

    specialist_name = task["specialist"] if task else "unknown"
    memory = task.get("memory", False) if task else False

    workflows = _extract_workflows_from_messages(
        state["messages"], specialist_name, newest=False
    )
    if workflows:
        hist_wfs = workflows[:-1]
        newest_wf = workflows[-1]
        hist_msgs = [m for w in hist_wfs for m in _format_workflow(w)] if memory else []
        newest_msgs = _format_workflow(newest_wf)
    else:
        hist_msgs = []
        newest_msgs = [HumanMessage(content=task["task"] if task else "")]

    if eval_type == "task_eval":
        sys_msg = HumanMessage(content=task_eval_prompt.invoke({}).messages[0].content)
        input_msgs = pruning_func([*hist_msgs, *newest_msgs])
        response = llm.invoke([*input_msgs, sys_msg])
        response.content = _extract_xml_tags_from_text(str(response.content), ["reflection", "reward"])
        next_step = "node_research_manager"
    elif eval_type == "visual_eval":
        sys_msg = HumanMessage(content=visual_eval_prompt.invoke({}).messages[0].content)
        input_msgs = pruning_func([*newest_msgs])
        response = llm.invoke([*input_msgs, sys_msg])
        response.content = _extract_xml_tags_from_text(str(response.content), ["caption", "reflection", "reward"])
        next_step = f"node_{specialist_name}"
    else:  # tool_eval
        sys_msg = HumanMessage(content=tool_eval_prompt.invoke({}).messages[0].content)
        input_msgs = pruning_func([*newest_msgs])
        response = llm.invoke([*input_msgs, sys_msg])
        response.content = _extract_xml_tags_from_text(str(response.content), ["reflection", "reward"])
        next_step = f"node_{specialist_name}"

    response.tool_calls = []
    return return_messages([response], eval_type, next_step, "call_evaluation")


class SpecialistTool:
    """Minimal specialist wrapper — replaces SciSciGPT's BaseTool subclass."""

    def __init__(self, name: str, description: str, tools: list = None):
        self.name = name
        self.description = description
        self.tools = tools or []

    def invoke(self, args):
        import json
        return json.dumps({"response": f"Connected to {self.name}:"})


def make_specialist(name: str, description: str, tools: list = None) -> SpecialistTool:
    return SpecialistTool(name, description, tools)


def define_sciscigpt_graph(load_llm, db_tools=None, analytics_tools=None, lit_tools=None):
    """Build the SciSciGPT LangGraph with locally-adaptable components.

    Args:
        load_llm: callable(metadata) -> BaseChatModel
        db_tools: list of BaseTool for database specialist (SQL, name search, etc.)
        analytics_tools: list of BaseTool for analytics specialist (Python, R, Julia sandbox)
        lit_tools: list of BaseTool for literature specialist (paper search)

    Returns:
        Compiled LangGraph StateGraph ready for invocation.
    """
    db_tools = db_tools or []
    analytics_tools = analytics_tools or []
    lit_tools = lit_tools or []

    DS = make_specialist("database_specialist", "Database specialist for data extraction and SQL queries.")
    AS = make_specialist("analytics_specialist", "Analytics specialist for statistical analysis and visualization.")
    LS = make_specialist("literature_specialist", "Literature specialist for paper search and synthesis.")
    ES = make_specialist("evaluation_specialist", "Evaluation specialist for quality assessment.")

    id_func = lambda x: x

    node_rm = partial(call_research_manager, load_llm, [DS, AS, LS], id_func)
    node_ds = partial(call_specialist, load_llm, db_tools + [ES], id_func)
    node_as = partial(call_specialist, load_llm, analytics_tools + [ES], id_func)
    node_ls = partial(call_specialist, load_llm, lit_tools + [ES], id_func)
    node_es = partial(call_evaluation, load_llm, [DS, AS, LS], id_func)
    node_ss = partial(call_specialistset, [DS, AS, LS])
    node_ts = partial(call_toolset, db_tools + analytics_tools + lit_tools)

    graph = StateGraph(AgentState)
    graph.add_node("node_research_manager", node_rm)
    graph.add_node("node_database_specialist", node_ds)
    graph.add_node("node_analytics_specialist", node_as)
    graph.add_node("node_literature_specialist", node_ls)
    graph.add_node("node_evaluation_specialist", node_es)
    graph.add_node("node_specialistset", node_ss)
    graph.add_node("node_toolset", node_ts)

    graph.add_edge(START, "node_research_manager")
    for node in [
        "node_research_manager", "node_database_specialist",
        "node_analytics_specialist", "node_literature_specialist",
        "node_evaluation_specialist", "node_specialistset", "node_toolset",
    ]:
        graph.add_conditional_edges(node, select_next)

    return graph.compile()
