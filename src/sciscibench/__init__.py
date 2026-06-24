"""SciSciBench — Process-level benchmark for AutoResearch agents in computational scientometrics.

Two core tasks:
  Task 1: Idea + Data → Experiment Design (forced JSON Schema output)
  Task 2: Idea + Data + Experiment → Conclusion (L1/L2/L3 difficulty)

Three engineering defenses:
  1. Forced JSON Schema output (Task 1)
  2. Three-layer contamination defense (blind / obfuscation / logic-only)
  3. Dual-track evaluation (original-fidelity + expert-quality subset)
"""

from .annotation import SciSciPaper, ContaminationScore, create_wu2019, create_ke2023, create_arts2025
from .tasks.task1_design import Task1Prompt, Task1Runner
from .tasks.task2_conclusion import Task2Prompt, Task2Runner
from .eval.task1_evaluator import Task1Evaluator
from .eval.task2_evaluator import Task2Evaluator
from .eval.task3_evaluator import Task3Evaluator, FailureAnalysis, compute_calibration
from .tasks.task3_progressive_disclosure import Task3Prompt, Task3Runner, ScaffoldDependenceIndex

__all__ = [
    "SciSciPaper",
    "ContaminationScore",
    "create_wu2019",
    "create_ke2023",
    "create_arts2025",
    "Task1Prompt",
    "Task1Runner",
    "Task2Prompt",
    "Task2Runner",
    "Task3Prompt",
    "Task3Runner",
    "Task1Evaluator",
    "Task2Evaluator",
    "Task3Evaluator",
    "FailureAnalysis",
    "ScaffoldDependenceIndex",
    "compute_calibration",
]
