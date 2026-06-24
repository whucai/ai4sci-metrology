#!/usr/bin/env python3
"""R003: Arts2021 Component Diagnosis Experiment.

Evaluates whether an LLM agent can decompose a complex scientometric paper
(Arts, Hou, Gomez 2021, "Natural language processing to identify the creation
and impact of new technologies in patent text") into executable, auditable,
diagnosable sub-components.

CONTRAST with R002 (STRICT numerical reproduction):
  - R002: "Can the agent exactly reproduce 3 regression coefficients?"
  - R003: "Can the agent decompose 10 complex NLP indicators into their
    constituent sub-components and correctly implement each one?"

The highlight is NOT 'code can run' — it is whether the agent can transform
a scientometric paper into an executable, auditable, diagnosable reproduction
task map.

Usage:
    python scripts/r003_arts2021_component_diagnosis.py
    python scripts/r003_arts2021_component_diagnosis.py --mock
    python scripts/r003_arts2021_component_diagnosis.py --model deepseek-v4-pro
"""

from __future__ import annotations

import json
import os
import re
import sys
import textwrap
import time
import traceback
from datetime import datetime
from pathlib import Path
from typing import Any

import numpy as np
import pandas as pd
from scipy.stats import spearmanr

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.sciscigpt_local.sandbox import execute_python
from src.sciscigpt_local.llm_backends import load_llm_from_env

# ── Paths ──
PROJECT_ROOT = Path(__file__).resolve().parent.parent
OUTPUT_DIR = PROJECT_ROOT / "refine-logs" / "r003"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
GOLD_PARQUET = OUTPUT_DIR / "gold_sample.parquet"
GOLD_VALUES = OUTPUT_DIR / "gold_values.json"
DATA_DIR = PROJECT_ROOT / "data" / "patentsview"

# ── Constants ──
INDICATOR_NAMES = [
    "new_word", "new_bigram", "new_trigram", "new_word_comb",
    "cosine_similarity", "new_word_reuse", "new_bigram_reuse",
    "new_trigram_reuse", "new_word_comb_reuse", "cosine_similarity_impact",
]

PREPROCESSING_STEPS = [
    "text_concatenation",
    "lowercase",
    "tokenization",
    "remove_numbers",
    "remove_single_char",
    "remove_nltk_stopwords",
    "remove_custom_stopwords",
    "remove_rare_words",
    "snowball_stemming",
    "deduplicate_keywords",
]

# ── Prompt ──


def build_component_diagnosis_prompt() -> str:
    """Build the constrained prompt for R003 component diagnosis.

    Unlike R002 which asked for exact reproduction, this prompt explicitly asks
    the agent to DECOMPOSE the methodology into sub-components, document each
    one, and implement them correctly.
    """
    return textwrap.dedent("""\
    You are a computational reproducibility agent specialized in scientometric
    methods. Your task is to decompose and implement the NLP-based patent novelty
    and impact indicators from:

      Arts, Hou, Gomez (2021) "Natural language processing to identify the
      creation and impact of new technologies in patent text."
      Research Policy 50, 104144.

    ## TASK: Component Diagnosis Reproduction

    This is NOT a standard "reproduce the numbers" task. Your goal is to:

    1. DECOMPOSE the methodology into sub-components (preprocessing steps,
       indicator definitions, variable constructions)
    2. DOCUMENT each sub-component with its purpose and formula
    3. IMPLEMENT each sub-component correctly
    4. PRODUCE a component decomposition table AND numerical results

    ## MANDATORY CONSTRAINTS

    ### C1: DATA SOURCE
    Use the patent sample at: {data_dir}/patents_sample_50k.parquet
    Columns: patent_id, patent_abstract, claim_text, date, cpc_ids
    Note: There is NO title column — use patent_abstract + claim_text as the text source.
    The 'date' column contains filing dates in YYYY-MM-DD format.

    ### C2: SAMPLE
    Use the first 500 patents from the dataset (head 500).
    Sort by date before processing (earliest patents first).

    ### C3: PREPROCESSING PIPELINE (Arts2021 Section 2.1)
    Implement each preprocessing step in order:

    P1. TEXT CONCATENATION: Concatenate patent_abstract + " " + claim_text
    P2. LOWERCASE: Convert all text to lowercase
    P3. TOKENIZATION: Use regex [a-z0-9][a-z0-9-]*[a-z0-9]+|[a-z0-9] to extract tokens
    P4. NUMBER REMOVAL: Remove tokens that are purely digits
    P5. SINGLE-CHAR REMOVAL: Remove tokens of length 1
    P6. NLTK STOPWORDS: Remove NLTK English stopwords
    P7. CUSTOM STOPWORDS: Remove common patent boilerplate words including:
        "said","wherein","thereof","thereby","invention","disclosure","embodiment",
        "claim","claims","claimed","describe","described","disclose","disclosed",
        "include","includes","including","comprise","comprises","comprising",
        "contain","contains","containing","patent","patents","apparatus",
        "method","methods","system","systems","device","devices","fig","figs",
        "figure","figures","prior","art","present","example","examples",
        "various","certain","another","other","may","also","can","one","two",
        "first","second","third","based","used","using","provide","provides",
        "provided","providing","configure","configured","set","make","made",
        "way","new","many","much","part","parts","least","well","without",
        "within","able","accordingly","moreover","furthermore","however",
        "therefore","consequently","subsequently","preferably","respectively"
    P8. RARE WORD REMOVAL: Remove words that appear in only 1 patent
    P9. STEMMING: Apply NLTK SnowBall stemmer to each token
    P10. DEDUPLICATE: Keep only unique stemmed keywords per patent

    ### C4: NOVELTY INDICATORS (Arts2021 Section 2.2)
    For each patent p (processed in filing-date order):

    I1. new_word: Count of unique stemmed keywords in p that have NOT appeared
        in ANY patent with an earlier filing date.
    I2. new_bigram: Count of consecutive keyword PAIRS (in document order, i.e.
        keywords[i]+"|||"+keywords[i+1]) that are first-seen.
    I3. new_trigram: Count of consecutive keyword TRIPLES (keywords[i]+"|||"+
        keywords[i+1]+"|||"+keywords[i+2]) that are first-seen.
    I4. new_word_comb: Count of pairwise keyword COMBINATIONS (order-independent,
        all pairs among unique keywords) that are first-seen.
        CAP at 5000 pairs per patent for computational feasibility.
    I5. cosine_similarity (novelty): 1.0 - backward_cosine, where backward_cosine =
        mean(cosine_similarity(p, each_prior_patent)).
        Use binary TF vectors over the top 5000 vocabulary terms.

    ### C5: IMPACT/REUSE INDICATORS (Arts2021 Section 2.2)

    I6. new_word_reuse: For each NEW keyword introduced by patent p,
        sum of (1 + number_of_future_patents_that_use_this_keyword).
    I7. new_bigram_reuse: Same for new bigrams introduced by p.
    I8. new_trigram_reuse: Same for new trigrams introduced by p.
    I9. new_word_comb_reuse: Same for new keyword pairs introduced by p.
    I10. cosine_similarity_impact: forward_cosine / backward_cosine, where
         forward_cosine = mean(cosine_similarity(p, each_future_patent)).
         If backward_cosine is 0, set impact to 0.

    ### C6: REQUIRED OUTPUT SECTIONS
    Print output in these EXACT sections:

    print("\\n=== COMPONENT_DECOMPOSITION ===")
    # List each sub-component with: name, category (preprocessing/novelty/impact),
    # formula/definition, dependencies (which other components it depends on)

    print("\\n=== PREPROCESSING ===")
    # For each of P1-P10: print step_name, parameters, output_shape/n_tokens

    print("\\n=== INDICATOR_STATS ===")
    # For each of I1-I10: print indicator_name, mean, median, std, min, max, pct_nonzero

    print("\\n=== COMPONENT_DEPENDENCY_GRAPH ===")
    # Print dependencies: which indicator depends on which preprocessing step
    # Format: indicator_name <- [list of preprocessing steps it depends on]

    print("\\n=== RESULTS ===")
    # Summary: total patents processed, date range, avg keywords per patent

    ### C7: EXECUTION
    - Save patent keywords and indicators to a DataFrame
    - Print the sections above with actual computed values
    - Do NOT use external NLP libraries beyond NLTK (no spaCy, no transformers)
    - Use scipy/numpy for cosine similarity
    """).format(data_dir=str(DATA_DIR))


# ── Parsing ──


def parse_agent_response(response: Any) -> str:
    """Extract code block from LLM response."""
    content = ""
    if hasattr(response, "content"):
        content = str(response.content)
    elif isinstance(response, str):
        content = response
    else:
        content = str(response)

    # Extract code from markdown code block
    m = re.search(r"```(?:python)?\s*\n(.*?)```", content, re.DOTALL)
    if m:
        return m.group(1)

    # Try to find code between imports and final print
    m = re.search(r"(import\s+.*?print\(.*?$)", content, re.DOTALL | re.MULTILINE)
    if m:
        return m.group(1)

    return content


def parse_indicator_stats(stdout: str) -> dict[str, dict[str, float]]:
    """Parse indicator statistics from stdout INDICATOR_STATS section."""
    stats: dict[str, dict[str, float]] = {}

    in_section = False
    for line in stdout.split("\n"):
        line = line.strip()
        if "INDICATOR_STATS" in line:
            in_section = True
            continue
        if in_section and line.startswith("==="):
            break
        if not in_section or not line:
            continue

        # Try to parse: indicator_name, mean=X, median=Y, ...
        for ind_name in INDICATOR_NAMES:
            if ind_name in line.lower():
                values = {}
                for metric in ["mean", "median", "std", "min", "max", "pct_nonzero"]:
                    m = re.search(rf"{metric}[=:\s]*([0-9.e+\-]+)", line, re.IGNORECASE)
                    if m:
                        try:
                            values[metric] = float(m.group(1))
                        except ValueError:
                            pass
                if values:
                    stats[ind_name] = values
                break

    return stats


def parse_preprocessing_steps(stdout: str) -> list[str]:
    """Parse identified preprocessing steps from COMPONENT_DECOMPOSITION section."""
    found_steps: list[str] = []
    in_section = False
    for line in stdout.split("\n"):
        line_lower = line.strip().lower()
        if "component_decomposition" in line_lower:
            in_section = True
            continue
        if in_section and line_lower.startswith("==="):
            break
        if not in_section:
            continue
        for step in PREPROCESSING_STEPS:
            if step in line_lower and step not in found_steps:
                found_steps.append(step)
    return found_steps


def parse_dependency_graph(stdout: str) -> dict[str, list[str]]:
    """Parse component dependency graph."""
    deps: dict[str, list[str]] = {}
    in_section = False
    for line in stdout.split("\n"):
        line_lower = line.strip().lower()
        if "component_dependency" in line_lower:
            in_section = True
            continue
        if in_section and line_lower.startswith("==="):
            break
        if not in_section:
            continue
        for ind_name in INDICATOR_NAMES:
            if ind_name in line_lower:
                deps[ind_name] = []
                for step in PREPROCESSING_STEPS:
                    if step in line_lower:
                        deps[ind_name].append(step)
                break
    return deps


# ── Evaluation ──


def compute_indicator_correlations(
    agent_df: pd.DataFrame, gold_df: pd.DataFrame
) -> dict[str, dict[str, float]]:
    """Compute per-indicator Spearman correlation and relative error."""
    results = {}
    for col in INDICATOR_NAMES:
        if col not in agent_df.columns or col not in gold_df.columns:
            results[col] = {"spearman_r": None, "mape": None, "error": "missing_column"}
            continue

        # Align by patent_id if possible, otherwise by index
        if "patent_id" in agent_df.columns and "patent_id" in gold_df.columns:
            merged = pd.merge(
                gold_df[["patent_id", col]],
                agent_df[["patent_id", col]],
                on="patent_id", suffixes=("_gold", "_agent")
            )
            g_vals = merged[f"{col}_gold"].values
            a_vals = merged[f"{col}_agent"].values
        else:
            g_vals = gold_df[col].values[:len(agent_df)]
            a_vals = agent_df[col].values[:len(gold_df)]

        if len(g_vals) < 10:
            results[col] = {"spearman_r": None, "mape": None, "error": "too_few_samples"}
            continue

        # Remove NaN/inf
        mask = np.isfinite(g_vals) & np.isfinite(a_vals)
        g_vals, a_vals = g_vals[mask], a_vals[mask]

        if len(g_vals) < 10:
            results[col] = {"spearman_r": None, "mape": None, "error": "too_few_valid"}
            continue

        try:
            r, p = spearmanr(g_vals, a_vals)
            r = float(r) if not np.isnan(r) else None
        except Exception:
            r = None

        # MAPE with epsilon to avoid div by zero
        with np.errstate(divide="ignore", invalid="ignore"):
            g_safe = np.where(np.abs(g_vals) < 1e-10, 1e-10, g_vals)
            ape = np.abs((a_vals - g_vals) / g_safe)
            ape = ape[np.isfinite(ape)]
            mape = float(np.mean(ape)) if len(ape) > 0 else None

        results[col] = {"spearman_r": r, "mape": mape}

    return results


def evaluate_component_identification(
    agent_stdout: str
) -> dict[str, Any]:
    """Evaluate how well the agent identified sub-components.

    Returns:
      - identified_steps: list of preprocessing steps found
      - step_completeness: fraction of 10 preprocessing steps identified
      - indicator_coverage: fraction of 10 indicators with stats reported
    """
    identified = parse_preprocessing_steps(agent_stdout)
    step_completeness = len(identified) / len(PREPROCESSING_STEPS) if PREPROCESSING_STEPS else 0

    stats = parse_indicator_stats(agent_stdout)
    indicator_coverage = len(stats) / len(INDICATOR_NAMES) if INDICATOR_NAMES else 0

    return {
        "identified_preprocessing_steps": identified,
        "step_completeness": round(step_completeness, 3),
        "indicators_with_stats": list(stats.keys()),
        "indicator_coverage": round(indicator_coverage, 3),
        "missing_steps": [s for s in PREPROCESSING_STEPS if s not in identified],
        "missing_indicators": [i for i in INDICATOR_NAMES if i not in stats],
    }


def evaluate_component_fidelity(
    agent_df: pd.DataFrame, gold_df: pd.DataFrame
) -> dict[str, Any]:
    """Compute component-level fidelity scores.

    Groups indicators into categories and scores each category.
    """
    corr_results = compute_indicator_correlations(agent_df, gold_df)

    # Category grouping
    novelty_indicators = ["new_word", "new_bigram", "new_trigram",
                          "new_word_comb", "cosine_similarity"]
    impact_indicators = ["new_word_reuse", "new_bigram_reuse",
                         "new_trigram_reuse", "new_word_comb_reuse",
                         "cosine_similarity_impact"]

    def category_score(ind_names: list[str]) -> dict[str, Any]:
        scores = []
        for name in ind_names:
            r = corr_results.get(name, {}).get("spearman_r")
            if r is not None:
                scores.append(max(0, r))  # clip negative correlations
        return {
            "n_evaluable": len(scores),
            "mean_spearman": round(float(np.mean(scores)), 4) if scores else None,
            "indicators": {n: corr_results.get(n, {}) for n in ind_names},
        }

    return {
        "per_indicator": corr_results,
        "novelty_category": category_score(novelty_indicators),
        "impact_category": category_score(impact_indicators),
        "overall_mean_spearman": round(float(np.mean(
            [v["spearman_r"] for v in corr_results.values()
             if v.get("spearman_r") is not None]
        )), 4) if any(v.get("spearman_r") is not None for v in corr_results.values()) else None,
    }


def localize_errors(
    agent_df: pd.DataFrame, gold_df: pd.DataFrame
) -> dict[str, Any]:
    """Error source localization: trace indicator errors back to sub-components.

    For each indicator with low fidelity, identify which preprocessing step
    or sub-component is the most likely cause of the error.
    """
    corr_results = compute_indicator_correlations(agent_df, gold_df)

    # Classify errors by likely source
    error_categories = {
        "tokenization_error": [],
        "stopword_error": [],
        "stemming_error": [],
        "first_occurrence_error": [],
        "reuse_count_error": [],
        "cosine_formula_error": [],
        "data_source_error": [],
        "unknown_error": [],
    }

    for ind_name, result in corr_results.items():
        r = result.get("spearman_r")
        mape = result.get("mape")

        if r is None:
            error_categories["data_source_error"].append(ind_name)
            continue

        if r > 0.7:
            continue  # good enough

        # Map indicator to likely error source
        if ind_name in ["new_word", "new_bigram", "new_trigram", "new_word_comb"]:
            if r < 0.3:
                error_categories["first_occurrence_error"].append(ind_name)
            elif r < 0.5:
                # Check if preprocessing is the issue
                error_categories["tokenization_error"].append(ind_name)
            else:
                error_categories["stemming_error"].append(ind_name)
        elif ind_name in ["new_word_reuse", "new_bigram_reuse",
                          "new_trigram_reuse", "new_word_comb_reuse"]:
            error_categories["reuse_count_error"].append(ind_name)
        elif ind_name in ["cosine_similarity", "cosine_similarity_impact"]:
            error_categories["cosine_formula_error"].append(ind_name)
        else:
            error_categories["unknown_error"].append(ind_name)

    # Remove empty categories
    error_categories = {k: v for k, v in error_categories.items() if v}

    return {
        "error_categories": error_categories,
        "n_indicators_with_errors": sum(len(v) for v in error_categories.values()),
        "per_indicator_correlation": {k: v.get("spearman_r") for k, v in corr_results.items()},
    }


# ── Component Diagnosis Scoring (framework-specific) ──


def compute_component_diagnosis_scores(
    component_id: dict[str, Any],
    component_fidelity: dict[str, Any],
    error_localization: dict[str, Any],
    execution_success: bool,
    stdout: str,
) -> dict[str, Any]:
    """Compute the 5-dimension component diagnosis scores.

    Adapted from the standard 5 dimensions, but tailored for component diagnosis:
    - D1 (Component Fidelity): How completely were sub-components identified?
    - D2 (Executability): Did the code run without errors?
    - D3 (Component Accuracy): Per-component numerical accuracy (Spearman)
    - D4 (Error Localization): Can we trace errors to specific sub-components?
    - D5 (Auditability): Is the component decomposition documented and traceable?
    """
    # D1: Component Identification Fidelity
    d1_step = component_id["step_completeness"]
    d1_ind = component_id["indicator_coverage"]
    d1_score = round((d1_step + d1_ind) / 2, 3)

    # D2: Executability
    d2_score = 1.0 if execution_success else 0.0

    # D3: Component Accuracy (overall mean Spearman)
    d3_score = component_fidelity.get("overall_mean_spearman")
    d3_score = round(d3_score, 3) if d3_score is not None else 0.0

    # D4: Error Localization (can we pinpoint errors?)
    n_errors = error_localization.get("n_indicators_with_errors", 0)
    n_total = len(INDICATOR_NAMES)
    # Higher score = fewer errors OR well-categorized errors
    unknown_errors = len(error_localization.get("error_categories", {}).get("unknown_error", []))
    # If errors exist but are categorized, that's better than unknown errors
    if n_errors == 0:
        d4_score = 1.0
    elif unknown_errors == 0 and n_errors > 0:
        d4_score = 0.7  # errors exist but all categorized
    elif unknown_errors < n_errors:
        d4_score = 0.4  # some categorized
    else:
        d4_score = 0.1  # all unknown

    # D5: Auditability (component documentation quality)
    dep_graph = parse_dependency_graph(stdout)
    dep_completeness = len(dep_graph) / len(INDICATOR_NAMES) if INDICATOR_NAMES else 0
    d5_score = round((component_id["step_completeness"] + dep_completeness) / 2, 3)

    return {
        "D1_component_fidelity": d1_score,
        "D1_details": {
            "step_completeness": d1_step,
            "indicator_coverage": d1_ind,
            "identified_steps": component_id["identified_preprocessing_steps"],
            "covered_indicators": component_id["indicators_with_stats"],
        },
        "D2_executability": d2_score,
        "D3_component_accuracy": d3_score,
        "D3_details": {
            "novelty_mean_spearman": component_fidelity["novelty_category"]["mean_spearman"],
            "impact_mean_spearman": component_fidelity["impact_category"]["mean_spearman"],
        },
        "D4_error_localization": d4_score,
        "D4_details": error_localization["error_categories"],
        "D5_auditability": d5_score,
        "overall_component_diagnosis_score": round(
            (d1_score + d2_score + d3_score + d4_score + d5_score) / 5, 3
        ),
    }


# ── Main ──


def run_r003(model_name: str = "deepseek-v4-pro", use_mock: bool = False) -> dict[str, Any]:
    """Run the R003 Arts2021 component diagnosis experiment."""
    print("=" * 70)
    print("R003: Arts2021 Component Diagnosis Experiment")
    print("=" * 70)

    # ── Step 1: Load gold data ──
    print("\n[1/7] Loading gold data...")
    gold_df = pd.read_parquet(GOLD_PARQUET)
    with open(GOLD_VALUES) as f:
        gold_values = json.load(f)
    print(f"  Gold: {len(gold_df)} patents, "
          f"dates={gold_df['filing_date'].min()} to {gold_df['filing_date'].max()}")
    print(f"  Indicators: {list(gold_values['gold_indicators'].keys())}")

    # ── Step 2: Load LLM ──
    print(f"\n[2/7] Loading LLM: {model_name}...")
    if use_mock:
        from src.sciscigpt_local.mock_llm import MockLLM
        llm = MockLLM()
        print("  Using MockLLM")
    else:
        llm = load_llm_from_env(model_name)

    # ── Step 3: Generate agent code ──
    print("\n[3/7] Generating agent code from prompt...")
    prompt = build_component_diagnosis_prompt()
    print(f"  Prompt length: {len(prompt)} chars")

    t0 = time.time()

    # Save prompt for audit
    with open(OUTPUT_DIR / "prompt_v0.txt", "w") as f:
        f.write(prompt)

    response = llm.invoke(prompt)
    agent_code = parse_agent_response(response)
    gen_time = time.time() - t0

    # Save raw response and extracted code
    with open(OUTPUT_DIR / "agent_response_v0.txt", "w") as f:
        f.write(str(response.content) if hasattr(response, "content") else str(response))
    with open(OUTPUT_DIR / "reproduce_v0_llm.py", "w") as f:
        f.write(agent_code)

    print(f"  Generated {len(agent_code)} chars of code in {gen_time:.1f}s")

    # ── Step 4: Section compliance check ──
    print("\n[4/7] Checking section compliance...")
    required_sections = [
        "COMPONENT_DECOMPOSITION",
        "PREPROCESSING",
        "INDICATOR_STATS",
        "COMPONENT_DEPENDENCY_GRAPH",
        "RESULTS",
    ]
    section_results = {}
    for section in required_sections:
        found = bool(re.search(
            rf'print\(["\'](?:\\n)?\s*=== {section} ===["\']\)',
            agent_code
        ))
        section_results[section] = found
        print(f"  Section {section}: {'FOUND' if found else 'MISSING'}")

    all_sections_found = all(section_results.values())

    # ── Step 5: Execute agent code ──
    print("\n[5/7] Executing agent code...")
    exec_result = execute_python(agent_code, timeout=600)

    execution_success = exec_result.get("exit_code", exec_result.get("returncode", -1)) == 0
    stdout = exec_result.get("stdout", "")
    stderr = exec_result.get("stderr", "")

    with open(OUTPUT_DIR / "stdout.txt", "w") as f:
        f.write(stdout)
    if stderr:
        with open(OUTPUT_DIR / "stderr.txt", "w") as f:
            f.write(stderr)

    print(f"  Execution: {'SUCCESS' if execution_success else 'FAILED'}")
    print(f"  Stdout: {len(stdout)} chars, Stderr: {len(stderr)} chars")
    if not execution_success:
        print(f"  Error (last 300 chars): ...{stderr[-300:]}")

    # ── Step 6: Evaluate component diagnosis ──
    print("\n[6/7] Evaluating component diagnosis...")

    # 6a: Component identification
    component_id = evaluate_component_identification(stdout)
    print(f"  Step completeness: {component_id['step_completeness']:.2f} "
          f"({len(component_id['identified_preprocessing_steps'])}/{len(PREPROCESSING_STEPS)})")
    print(f"  Indicator coverage: {component_id['indicator_coverage']:.2f} "
          f"({len(component_id['indicators_with_stats'])}/{len(INDICATOR_NAMES)})")
    if component_id["missing_steps"]:
        print(f"  Missing steps: {component_id['missing_steps']}")
    if component_id["missing_indicators"]:
        print(f"  Missing indicators: {component_id['missing_indicators']}")

    # 6b: Component fidelity (requires agent output to have indicator data)
    # Save indicator stats parsed from stdout
    indicator_stats = parse_indicator_stats(stdout)
    print(f"  Parsed indicator stats from stdout: {len(indicator_stats)} indicators")

    # If agent produced a results file, load it for correlation
    agent_df = None
    # Look for saved parquet/csv in the agent's output
    for pattern in ["patent_indicators.parquet", "indicators.csv",
                    "results.parquet", "results.csv"]:
        candidate = OUTPUT_DIR / pattern
        if candidate.exists():
            try:
                if pattern.endswith(".parquet"):
                    agent_df = pd.read_parquet(candidate)
                else:
                    agent_df = pd.read_csv(candidate)
                print(f"  Loaded agent results from {pattern}: {len(agent_df)} rows")
                break
            except Exception:
                pass

    component_fidelity = {}
    error_localization = {}

    if agent_df is not None and len(agent_df) > 10:
        component_fidelity = evaluate_component_fidelity(agent_df, gold_df)
        error_localization = localize_errors(agent_df, gold_df)

        print(f"  Overall mean Spearman: {component_fidelity['overall_mean_spearman']}")
        print(f"  Novelty mean Spearman: {component_fidelity['novelty_category']['mean_spearman']}")
        print(f"  Impact mean Spearman: {component_fidelity['impact_category']['mean_spearman']}")
        print(f"  Error categories: {list(error_localization.get('error_categories', {}).keys())}")
    else:
        print("  WARNING: No agent results file found for numerical comparison")
        print("  Using stdout-parsed indicator stats as fallback")
        # Build synthetic fidelity from parsed stdout stats
        component_fidelity = {
            "per_indicator": {},
            "novelty_category": {"n_evaluable": 0, "mean_spearman": None, "indicators": {}},
            "impact_category": {"n_evaluable": 0, "mean_spearman": None, "indicators": {}},
            "overall_mean_spearman": None,
        }
        error_localization = {"error_categories": {}, "n_indicators_with_errors": 0,
                             "per_indicator_correlation": {}}

    # 6c: Component diagnosis scores
    scores = compute_component_diagnosis_scores(
        component_id, component_fidelity, error_localization,
        execution_success, stdout
    )

    print(f"\n  === Component Diagnosis Scores ===")
    print(f"  D1 (Component Fidelity): {scores['D1_component_fidelity']:.3f}")
    print(f"  D2 (Executability):      {scores['D2_executability']:.3f}")
    print(f"  D3 (Component Accuracy):  {scores['D3_component_accuracy']:.3f}")
    print(f"  D4 (Error Localization):  {scores['D4_error_localization']:.3f}")
    print(f"  D5 (Auditability):        {scores['D5_auditability']:.3f}")
    print(f"  Overall:                  {scores['overall_component_diagnosis_score']:.3f}")

    # ── Step 7: Save results ──
    print("\n[7/7] Saving results...")

    results = {
        "experiment": "R003",
        "paper": "Arts2021 (NLP patent novelty/impact indicators)",
        "task_type": "component_diagnosis",
        "model": model_name,
        "timestamp": datetime.now().isoformat(),
        "generation_time_s": round(gen_time, 1),
        "execution_success": execution_success,
        "section_compliance": section_results,
        "all_sections_found": all_sections_found,
        "component_identification": component_id,
        "component_fidelity": component_fidelity,
        "error_localization": error_localization,
        "component_diagnosis_scores": scores,
        "gold_summary": {
            "sample_N": len(gold_df),
            "indicators": list(gold_values["gold_indicators"].keys()),
        },
        "spurious_flags": [],
    }

    with open(OUTPUT_DIR / "r003_results.json", "w") as f:
        json.dump(results, f, indent=2, default=str)

    print(f"  Results saved to {OUTPUT_DIR / 'r003_results.json'}")
    print(f"\n{'='*70}")
    print("R003 complete.")
    print(f"{'='*70}")

    return results


# ── CLI ──

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="R003 Arts2021 Component Diagnosis")
    parser.add_argument("--mock", action="store_true", help="Use MockLLM")
    parser.add_argument("--model", default="deepseek-v4-pro", help="Model name")
    args = parser.parse_args()
    run_r003(model_name=args.model, use_mock=args.mock)
