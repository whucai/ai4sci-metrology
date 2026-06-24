#!/usr/bin/env python3
"""R005: METHOD reproduction of Zhao & Zhang (2025) novelty measurement taxonomy.

Zhao & Zhang (2025) "A Review on the Novelty Measurements of Academic Papers"
Scientometrics, 2025.

METHOD task type: No numerical targets. Evaluates structural fidelity —
can the agent correctly categorize and describe the novelty measurement
taxonomy without executing code?

Usage:
    python scripts/r005_zhao2025_method_reproduction.py
    python scripts/r005_zhao2025_method_reproduction.py --mock
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
import time
from datetime import datetime
from pathlib import Path
from typing import Any

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.llm_backends import load_llm_from_env

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r005"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# Gold taxonomy extracted from the paper
GOLD_TAXONOMY = {
    "conceptual_distinctions": {
        "novelty": "Studies that contribute something new to human knowledge — the quality of being new, original, or unusual",
        "originality": "Something that is both novel and useful/usefulness dimension; emphasis on creativity and unexpectedness",
        "innovation": "The implementation/commercialization of novel ideas; broader than academic novelty, includes practical adoption",
    },
    "novelty_types": [
        "Radical vs incremental novelty",
        "Technical vs scientific novelty",
        "Theoretical vs methodological vs empirical novelty",
        "Combinational novelty (new combinations of existing knowledge)",
        "Result novelty vs approach novelty",
    ],
    "measurement_approaches_by_data_type": {
        "text_based": [
            "Bag-of-words / TF-IDF based similarity",
            "Topic model based (LDA, word embeddings)",
            "Deep learning / BERT-based semantic similarity",
            "N-gram / phrase-level novelty detection",
        ],
        "citation_based": [
            "Reference combination analysis (atypical combinations of references)",
            "Bibliographic coupling / co-citation novelty",
            "Disruption index (CD index — new directions vs consolidation)",
            "Network-based propagation measures",
        ],
        "metadata_based": [
            "Journal/venue novelty (cross-field publishing)",
            "Author team novelty (new collaborations)",
            "Keyword/concept co-occurrence novelty",
        ],
        "hybrid_approaches": [
            "Combining text + citation features",
            "Multi-dimensional novelty indicators",
            "Machine learning with multi-modal features",
        ],
    },
    "validation_approaches": [
        "Peer/expert assessment correlation",
        "Award/prize prediction (Nobel, Milestone papers)",
        "Citation impact correlation",
        "Disruption/citation pattern comparison",
        "Known benchmark datasets",
        "Inter-rater reliability with human judgments",
    ],
    "key_challenges": [
        "Delayed recognition — novel work may take years to be recognized",
        "Interdisciplinary evaluation — domain expertise gap",
        "Ground truth scarcity — no gold-standard novelty labels",
        "Dimensionality — novelty is multi-faceted, not a scalar",
        "Temporal dynamics — what is novel changes over time",
    ],
}


def build_prompt() -> str:
    return textwrap.dedent("""\
    Reproduce the taxonomy and methodological structure from:

      Zhao & Zhang (2025) "A Review on the Novelty Measurements of Academic Papers"
      Scientometrics, 2025. DOI: 10.1007/s11192-025-05234-0

    ## TASK

    This is a SURVEY/METHOD paper. Reproduce the conceptual framework and
    taxonomy of novelty measurements. No code execution is needed — this
    task evaluates whether you can correctly identify, categorize, and
    describe the methodological structure of the paper.

    ## REQUIRED OUTPUT SECTIONS

    ### 1. CONCEPTUAL_DISTINCTIONS
    Define and distinguish: novelty, originality, and innovation.
    Print in format:
      novelty: <definition>
      originality: <definition>
      innovation: <definition>

    ### 2. NOVELTY_TYPES
    List at least 4 types/dimensions of scientific novelty discussed in the paper.
    Print each on a new line with a brief description.

    ### 3. MEASUREMENT_APPROACHES
    Categorize novelty measurement approaches by data type.
    For each category, list at least 3 specific methods/techniques.
    Format:
      CATEGORY: <name>
        - <method 1>
        - <method 2>
        - <method 3>

    ### 4. VALIDATION_APPROACHES
    List approaches used to validate novelty measures.
    Print each on a new line.

    ### 5. KEY_CHALLENGES
    List at least 4 open challenges in novelty measurement.
    Print each on a new line.

    ### 6. DIFF_TABLE
    Print a markdown table summarizing the taxonomy:
    | Category | Data Type | Example Methods | Validation |
    |----------|-----------|-----------------|------------|
    """)


def parse_agent_response(response: Any) -> str:
    content = ""
    if hasattr(response, "content"):
        raw = response.content
        if isinstance(raw, list):
            text_parts = []
            for item in raw:
                if isinstance(item, dict) and item.get("type") == "text":
                    text_parts.append(item.get("text", ""))
            content = "\n".join(text_parts)
        else:
            content = str(raw)
    elif isinstance(response, str):
        content = response
    elif isinstance(response, list):
        text_parts = []
        for item in response:
            if isinstance(item, dict) and item.get("type") == "text":
                text_parts.append(item.get("text", ""))
        content = "\n".join(text_parts)
    else:
        content = str(response)
    return content


def evaluate_taxonomy(stdout: str) -> dict:
    """Evaluate structural fidelity of the agent's taxonomy reproduction."""
    results = {
        "conceptual_distinctions": {},
        "novelty_types_count": 0,
        "measurement_categories": {},
        "validation_approaches_count": 0,
        "challenges_count": 0,
        "overall_coverage": 0.0,
    }

    # Count novelty types mentioned
    novel_type_keywords = ["radical", "incremental", "technical", "scientific",
                           "theoretical", "methodological", "empirical",
                           "combinat", "result", "approach"]
    for kw in novel_type_keywords:
        count = len(re.findall(kw, stdout.lower()))
        if count > 0:
            results["novelty_types_count"] += 1

    # Identify measurement categories
    cat_keywords = {
        "text_based": ["text", "bag.of.word", "tf.idf", "topic.model", "lda", "bert", "word.embed", "n.gram", "semantic"],
        "citation_based": ["citation", "reference.combin", "bibliograph", "co.cit", "disruption", "cd.index", "network"],
        "metadata_based": ["journal", "venue", "author.team", "collaboration", "keyword", "metadata"],
        "hybrid": ["hybrid", "combin", "multi.dimension", "multi.modal", "machine.learning"],
    }
    for cat, keywords in cat_keywords.items():
        score = sum(1 for kw in keywords if re.search(kw, stdout.lower()))
        results["measurement_categories"][cat] = min(score / max(len(keywords), 1), 1.0)

    # Count validation approaches
    val_keywords = ["peer", "expert", "award", "prize", "nobel", "milestone",
                    "citation.impact", "disruption", "benchmark", "inter.rater",
                    "human.judgment"]
    results["validation_approaches_count"] = sum(
        1 for kw in val_keywords if re.search(kw, stdout.lower())
    )

    # Count challenges
    challenge_keywords = ["delay", "recogni", "interdisciplin", "ground.truth",
                          "gold.standard", "multi.dimension", "multi.facet",
                          "temporal", "time", "scalability"]
    results["challenges_count"] = sum(
        1 for kw in challenge_keywords if re.search(kw, stdout.lower())
    )

    # Check conceptual distinctions
    for concept in ["novelty", "originality", "innovation"]:
        # Look for definition-like patterns
        patterns = [
            rf"{concept}\s*[:=-]\s*(.+?)(?:\n|$)",
            rf"{concept}\s+is\s+(.+?)(?:\.|\n)",
            rf"{concept}\s+refers\s+to\s+(.+?)(?:\.|\n)",
        ]
        found = False
        for pat in patterns:
            m = re.search(pat, stdout.lower())
            if m:
                results["conceptual_distinctions"][concept] = True
                found = True
                break
        if not found:
            results["conceptual_distinctions"][concept] = False

    # Overall coverage score
    scores = []
    scores.append(sum(results["conceptual_distinctions"].values()) / 3.0)
    scores.append(min(results["novelty_types_count"] / 5.0, 1.0))
    scores.append(sum(results["measurement_categories"].values()) / max(len(results["measurement_categories"]), 1))
    scores.append(min(results["validation_approaches_count"] / 4.0, 1.0))
    scores.append(min(results["challenges_count"] / 4.0, 1.0))
    results["overall_coverage"] = round(sum(scores) / len(scores), 3)

    return results


def run_r005(model_name: str = "deepseek-v4-pro", use_mock: bool = False) -> dict[str, Any]:
    print("=" * 70)
    print("R005: Zhao2025 Novelty Measurement Taxonomy — METHOD Reproduction")
    print("=" * 70)

    print("\n[1/4] Loading LLM...")
    if use_mock:
        from src.sciscigpt_local.mock_llm import MockLLM
        llm = MockLLM()
    else:
        llm = load_llm_from_env(model_name)

    print("\n[2/4] Generating agent response...")
    prompt = build_prompt()
    with open(OUTPUT_DIR / "prompt_v0.txt", "w") as f:
        f.write(prompt)

    t0 = time.time()
    response = llm.invoke(prompt)
    agent_text = parse_agent_response(response)
    gen_time = time.time() - t0

    with open(OUTPUT_DIR / "agent_response_v0.txt", "w") as f:
        if hasattr(response, "content"):
            f.write(str(response.content))
        elif isinstance(response, list):
            f.write(str(response))
        else:
            f.write(str(response))
    with open(OUTPUT_DIR / "agent_output.txt", "w") as f:
        f.write(agent_text)

    print(f"  Generated {len(agent_text)} chars in {gen_time:.1f}s")

    print("\n[3/4] Evaluating structural fidelity...")
    evaluation = evaluate_taxonomy(agent_text)

    print(f"  Conceptual distinctions: {evaluation['conceptual_distinctions']}")
    print(f"  Novelty types found: {evaluation['novelty_types_count']}")
    print(f"  Measurement categories: {evaluation['measurement_categories']}")
    print(f"  Validation approaches: {evaluation['validation_approaches_count']}")
    print(f"  Challenges found: {evaluation['challenges_count']}")
    print(f"  Overall coverage: {evaluation['overall_coverage']:.2f}")

    # D1: structural fidelity (section compliance)
    sections = {}
    for s in ["CONCEPTUAL_DISTINCTIONS", "NOVELTY_TYPES", "MEASUREMENT_APPROACHES",
              "VALIDATION_APPROACHES", "KEY_CHALLENGES", "DIFF_TABLE"]:
        s_space = s.replace('_', ' ')
        # Check multiple patterns: ### SECTION, === SECTION, or section keyword
        sections[s] = bool(
            re.search(rf"#+\s*(?:\d+\.\s*)?{s_space}", agent_text, re.I) or
            re.search(rf"#+\s*(?:\d+\.\s*)?{s}", agent_text, re.I) or
            re.search(rf"===\s*{s}", agent_text) or
            s_space.lower() in agent_text.lower()
        )

    # D4: claim consistency (check for factual alignment with paper)
    # Agent should not claim to have "computed" or "simulated" anything
    spurious_flags = []
    if re.search(r"compute|calculate|simulate|run.experiment|execute", agent_text.lower()):
        if not re.search(r"(?:not|doesn't|won't)\s+(?:compute|calculate|simulate|run)", agent_text.lower()):
            # Only flag if agent incorrectly claims to have done computation
            spurious_flags.append("agent_claims_computation")

    d1_score = sum(sections.values()) / max(len(sections), 1)
    d4_score = 1.0 - len(spurious_flags) * 0.2
    d5_score = 1.0 if len(agent_text) > 500 else 0.5  # Auditability: sufficient detail

    overall = round((d1_score * 0.25 + evaluation["overall_coverage"] * 0.5 + d4_score * 0.15 + d5_score * 0.1), 2)

    print(f"\n  === METHOD Evaluation ===")
    print(f"  D1 (structural fidelity): {d1_score:.2f}")
    print(f"  D2 (coverage): {evaluation['overall_coverage']:.2f}")
    print(f"  D4 (claim consistency): {d4_score:.2f}")
    print(f"  D5 (auditability): {d5_score:.2f}")
    print(f"  Overall: {overall:.2f}")

    results = {
        "experiment": "R005",
        "paper": "Zhao2025 (Novelty Measurement Taxonomy, Scientometrics)",
        "task_type": "method",
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "generation_time_s": round(gen_time, 1),
        "section_compliance": sections,
        "all_sections_found": all(sections.values()),
        "evaluation": evaluation,
        "d1_score": d1_score,
        "d4_score": d4_score,
        "d5_score": d5_score,
        "overall_score": overall,
        "spurious_flags": spurious_flags,
        "gold_taxonomy": GOLD_TAXONOMY,
    }

    with open(OUTPUT_DIR / "r005_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"\n  Results saved to {OUTPUT_DIR / 'r005_results.json'}")
    print(f"{'=' * 70}")
    return results


if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="R005 Zhao2025 Novelty Measurement Taxonomy")
    parser.add_argument("--mock", action="store_true")
    parser.add_argument("--model", default="deepseek-v4-pro")
    args = parser.parse_args()
    run_r005(model_name=args.model, use_mock=args.mock)
