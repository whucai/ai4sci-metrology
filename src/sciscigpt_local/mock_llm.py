"""Mock LLM for M0 sanity testing.

Returns canned responses that exercise the full agent graph cycle:
ResearchManager → Specialist → Tool → Evaluation → END
"""

from __future__ import annotations

from typing import Any, Optional
from langchain_core.language_models import BaseChatModel
from langchain_core.messages import AIMessage, BaseMessage
from langchain_core.outputs import ChatResult, ChatGeneration


class MockLLM(BaseChatModel):
    """Deterministic mock that cycles through predefined responses.

    The sequence exercises: RM delegates → specialist uses tool →
    tool returns result → specialist finishes → evaluation → END.
    """

    step: int = 0

    def _generate(
        self, messages: list[BaseMessage], stop: list[str] | None = None, **kwargs: Any
    ) -> ChatResult:
        self.step += 1
        step = self.step

        if step == 1:
            # ResearchManager: delegate to analytics_specialist
            msg = AIMessage(
                content="I'll delegate this analysis to the analytics specialist.",
                tool_calls=[{
                    "name": "analytics_specialist",
                    "args": {
                        "task": "Load data.csv and compute summary statistics (mean, std, min, max) for all numeric columns.",
                        "memory": False,
                    },
                    "id": "call_001",
                    "type": "tool_call",
                }],
            )
        elif step == 2:
            # AnalyticsSpecialist: call python_jupyter tool
            msg = AIMessage(
                content="I'll run the analysis in Python.",
                tool_calls=[{
                    "name": "python_jupyter",
                    "args": {
                        "code": "import pandas as pd\ndf = pd.read_csv('data.csv')\nprint(df.describe())",
                    },
                    "id": "call_002",
                    "type": "tool_call",
                }],
            )
        elif step == 3:
            # AnalyticsSpecialist: done with analysis, call evaluation
            msg = AIMessage(
                content="Analysis complete. Summary statistics computed successfully.",
                tool_calls=[{
                    "name": "evaluation_specialist",
                    "args": {},
                    "id": "call_003",
                    "type": "tool_call",
                }],
            )
        elif step == 4:
            # EvaluationSpecialist: task_eval → approve, go back to RM
            msg = AIMessage(
                content="<reflection>The analysis was completed correctly.</reflection>\n<reward>0.9</reward>",
            )
        else:
            # ResearchManager: task complete → END
            msg = AIMessage(
                content="All tasks completed. The analysis has been verified.",
            )

        return ChatResult(generations=[ChatGeneration(message=msg)])

    @property
    def _llm_type(self) -> str:
        return "mock-llm"
