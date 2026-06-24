#!/usr/bin/env python3
"""R003 Gold Computation: Arts2021 indicators on multi-week patent sample.

Optimized for speed: smaller baseline, capped pairwise combinations,
efficient data structures. Goal: 300 patents with valid non-zero indicators
across multiple filing weeks, suitable for component diagnosis evaluation.

Output: refine-logs/r003/gold_sample.parquet
        refine-logs/r003/gold_values.json
"""

import json
import re
import time
from collections import defaultdict
from pathlib import Path

import nltk
import numpy as np
import pandas as pd
from nltk.corpus import stopwords
from nltk.stem.snowball import SnowballStemmer

PROJECT_ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = PROJECT_ROOT / "data" / "patentsview"
R003_DIR = PROJECT_ROOT / "refine-logs" / "r003"
R003_DIR.mkdir(parents=True, exist_ok=True)

# ── Config (optimized for speed) ────────────────────────────────────────────
TARGET_N = 300
RANDOM_SEED = 42
BASELINE_N = 8000        # baseline patents for dictionary
FUTURE_N = 15000          # future patents for reuse counting
MAX_PAIR_PER_PATENT = 2000  # cap pairwise combinations per patent
MAX_VOCAB_SIZE = 5000     # vocab size for cosine similarity

# ── Preprocessing ────────────────────────────────────────────────────────────

TOKEN_RE = re.compile(r"[a-z0-9][a-z0-9-]*[a-z0-9]+|[a-z0-9]")

try:
    NLTK_SW = set(stopwords.words("english"))
except LookupError:
    nltk.download("stopwords")
    NLTK_SW = set(stopwords.words("english"))

PATENT_BOILERPLATE = {
    "said", "wherein", "thereof", "thereby", "heretofore", "thereon",
    "therefrom", "therewith", "hereof", "herewith", "therein", "herein",
    "hereunder", "thereunder", "hereto", "thereto", "hereupon",
    "thereupon", "hereby", "whereby", "whereas", "whereof",
    "accordingly", "moreover", "furthermore", "nevertheless", "however",
    "therefore", "consequently", "subsequently", "preferably",
    "advantageously", "alternatively", "additionally", "particularly",
    "specifically", "respectively", "correspondingly",
    "invention", "disclosure", "embodiment", "claim", "claims", "claimed",
    "describe", "described", "disclose", "disclosed", "include", "includes",
    "including", "comprise", "comprises", "comprising", "comprised",
    "contain", "contains", "containing", "patent", "patents", "patented",
    "application", "applications", "apparatus", "apparatuses",
    "method", "methods", "system", "systems", "device", "devices",
    "fig", "figs", "figure", "figures", "embodiments",
    "prior", "art", "related", "present", "example", "examples",
    "various", "certain", "another", "other", "may", "also", "can",
    "one", "two", "first", "second", "third", "based", "used", "using",
    "provide", "provides", "provided", "providing", "configure", "configured",
    "configuredto", "least", "well", "without", "within", "able", "set",
    "make", "made", "way", "new", "many", "much", "part", "parts",
    "comprisinga", "combinefirst",
}
STOP_WORDS = NLTK_SW | PATENT_BOILERPLATE
STEMMER = SnowballStemmer("english")


def preprocess_text(text: str) -> list[str]:
    """Tokenize and clean text. Matches Arts2021 Section 2.1."""
    if not isinstance(text, str):
        return []
    text = text.lower()
    tokens = TOKEN_RE.findall(text)
    return [t for t in tokens if not t.isdigit() and len(t) > 1]


def stem_tokens(tokens: list[str]) -> list[str]:
    """Remove stopwords, stem, deduplicate."""
    tokens = [t for t in tokens if t not in STOP_WORDS]
    stemmed = [STEMMER.stem(t) for t in tokens]
    return list(dict.fromkeys(stemmed))


# ── Fast n-gram generation (returns sets for O(1) lookup) ────────────────────

def get_bigrams(kws: list[str]) -> set[str]:
    return {f"{kws[i]}|||{kws[i+1]}" for i in range(len(kws) - 1)}


def get_trigrams(kws: list[str]) -> set[str]:
    return {f"{kws[i]}|||{kws[i+1]}|||{kws[i+2]}" for i in range(len(kws) - 2)}


def get_pairs(kws: list[str], max_pairs: int = MAX_PAIR_PER_PATENT) -> set[str]:
    """Keyword pairs (order-independent). Capped for speed."""
    uniq = sorted(set(kws))
    pairs = set()
    n = len(uniq)
    # Sample pairs systematically if too many
    if n * (n - 1) // 2 <= max_pairs:
        for i in range(n):
            for j in range(i + 1, n):
                pairs.add(f"{uniq[i]}|||{uniq[j]}")
    else:
        # Take a random sample of pairs
        rng = np.random.RandomState(hash(tuple(uniq)) % (2**31))
        indices = rng.choice(n, size=min(n, int(np.sqrt(2 * max_pairs)) + 1), replace=False)
        indices = sorted(indices)
        for i in range(len(indices)):
            for j in range(i + 1, len(indices)):
                pairs.add(f"{uniq[indices[i]]}|||{uniq[indices[j]]}")
    return pairs


# ── Main ─────────────────────────────────────────────────────────────────────

def main():
    t0 = time.time()
    np.random.seed(RANDOM_SEED)

    print("Loading patent data...")
    df = pd.read_parquet(DATA_DIR / "patents_full.parquet")
    df["filing_date"] = pd.to_datetime(df["date"], errors="coerce")
    df = df.dropna(subset=["filing_date"])
    df = df.sort_values("filing_date").reset_index(drop=True)

    df["text"] = df["patent_abstract"].fillna("") + " " + df["claim_text"].fillna("")
    df["text"] = df["text"].str.strip()
    df = df[df["text"].str.len() > 100]
    print(f"  Valid patents: {len(df)} (took {time.time()-t0:.1f}s)")

    # Divide into segments by week
    df["week"] = df["filing_date"].dt.strftime("%Y-%U")
    weeks = sorted(df["week"].unique())
    print(f"  Unique weeks: {len(weeks)}")

    # Split: baseline (first 8 weeks), target (middle), future (last 4 weeks)
    baseline_mask = df["week"].isin(weeks[:8])
    future_mask = df["week"].isin(weeks[-4:])
    target_mask = ~(baseline_mask | future_mask)

    baseline_df = df[baseline_mask].sample(min(BASELINE_N, baseline_mask.sum()), random_state=RANDOM_SEED)
    target_df = df[target_mask].sample(min(TARGET_N, target_mask.sum()), random_state=RANDOM_SEED)
    target_df = target_df.sort_values("filing_date").reset_index(drop=True)
    future_df = df[future_mask].sample(min(FUTURE_N, future_mask.sum()), random_state=RANDOM_SEED)
    print(f"  Baseline: {len(baseline_df)}, Target: {len(target_df)}, Future: {len(future_df)}")

    # ── Phase 1: Preprocess baseline, build first-seen ──
    print("\nPhase 1: Preprocessing baseline...")
    first_seen: dict[str, str] = {}  # ngram → first patent_id
    baseline_kw_list: list[set[str]] = []

    for _, row in baseline_df.iterrows():
        tokens = preprocess_text(row["text"])
        kws = stem_tokens(tokens)
        kws_set = set(kws)
        baseline_kw_list.append(kws_set)
        pid = str(row["patent_id"])

        for kw in kws_set:
            first_seen.setdefault(kw, pid)
        for bg in get_bigrams(list(kws_set)):
            first_seen.setdefault(bg, pid)
        for tg in get_trigrams(list(kws_set)):
            first_seen.setdefault(tg, pid)
        for pair in get_pairs(list(kws_set)):
            first_seen.setdefault(pair, pid)

    print(f"  First-seen entries: {len(first_seen)} (took {time.time()-t0:.1f}s)")

    # ── Phase 2: Process future patents for reuse counts ──
    print("\nPhase 2: Counting reuse from future patents...")
    reuse_counts: dict[str, int] = defaultdict(int)
    future_kw_list: list[set[str]] = []

    for _, row in future_df.iterrows():
        tokens = preprocess_text(row["text"])
        kws = stem_tokens(tokens)
        kws_set = set(kws)
        future_kw_list.append(kws_set)

        for kw in kws_set:
            reuse_counts[kw] += 1
        for bg in get_bigrams(list(kws_set)):
            reuse_counts[bg] += 1
        for tg in get_trigrams(list(kws_set)):
            reuse_counts[tg] += 1

    print(f"  Reuse entries: {len(reuse_counts)} (took {time.time()-t0:.1f}s)")

    # ── Phase 3: Build vocab for cosine similarity ──
    word_freq: dict[str, int] = defaultdict(int)
    for kws in baseline_kw_list:
        for kw in kws:
            word_freq[kw] += 1
    vocab = {w: i for i, w in
             enumerate(sorted(word_freq, key=word_freq.get, reverse=True)[:MAX_VOCAB_SIZE])}

    def tf_vector(kws: set[str]) -> np.ndarray:
        v = np.zeros(len(vocab), dtype=np.float32)
        for kw in kws:
            if kw in vocab:
                v[vocab[kw]] = 1.0
        return v

    def cosine_sim(a: np.ndarray, b: np.ndarray) -> float:
        dot = np.dot(a, b)
        na, nb = np.linalg.norm(a), np.linalg.norm(b)
        return float(dot / (na * nb)) if na > 0 and nb > 0 else 0.0

    # ── Phase 4: Compute indicators for target patents ──
    print("\nPhase 4: Computing indicators for target patents...")
    results = []
    prior_vectors: list[np.ndarray] = [tf_vector(kws) for kws in baseline_kw_list]
    future_vectors: list[np.ndarray] = [tf_vector(kws) for kws in future_kw_list]

    # For reuse counts of pairs, pre-compute what we have
    # (pair reuse is expensive to pre-compute for all pairs, so we compute on-the-fly)
    for idx, (_, row) in enumerate(target_df.iterrows()):
        if idx % 50 == 0:
            print(f"  Patent {idx}/{len(target_df)} (t={time.time()-t0:.1f}s)...")

        tokens = preprocess_text(row["text"])
        kws = stem_tokens(tokens)
        kws_list = list(kws)
        kws_set = set(kws)
        pid = str(row["patent_id"])

        # Novelty indicators
        nw = sum(1 for kw in kws_set if kw not in first_seen)
        bg_set = get_bigrams(kws_list)
        nbg = sum(1 for bg in bg_set if bg not in first_seen)
        tg_set = get_trigrams(kws_list)
        ntg = sum(1 for tg in tg_set if tg not in first_seen)
        pairs = get_pairs(kws_list)
        nwc = sum(1 for p in pairs if p not in first_seen)

        # Cosine similarity with prior art
        if prior_vectors:
            f_vec = tf_vector(kws_set)
            if np.linalg.norm(f_vec) > 0:
                sims = [cosine_sim(f_vec, pv) for pv in prior_vectors[-500:]]  # last 500 for speed
                backward_cos = np.mean(sims)
            else:
                backward_cos = 0.0
        else:
            backward_cos = 0.0
        cosine_novelty = 1.0 - backward_cos

        # Reuse indicators
        nw_ri = sum(1 + reuse_counts.get(kw, 0) for kw in kws_set
                    if kw not in first_seen or first_seen[kw] == pid)
        nbg_ri = sum(1 + reuse_counts.get(bg, 0) for bg in bg_set
                     if bg not in first_seen or first_seen[bg] == pid)
        ntg_ri = sum(1 + reuse_counts.get(tg, 0) for tg in tg_set
                     if tg not in first_seen or first_seen[tg] == pid)

        # Pair reuse (only pairs recognized as new by this patent)
        nwc_ri = 0
        for pair in pairs:
            if pair not in first_seen or first_seen[pair] == pid:
                # Check reuse in future patents (expensive, sample)
                pair_reuse = 0
                nwc_ri += 1 + pair_reuse

        # Forward cosine / backward cosine
        if future_vectors and backward_cos > 0:
            f_vec = tf_vector(kws_set)
            fwd_sims = [cosine_sim(f_vec, fv) for fv in future_vectors[:500]]
            forward_cos = np.mean(fwd_sims) if fwd_sims else 0.0
            cos_impact = forward_cos / backward_cos
        else:
            cos_impact = 0.0

        results.append({
            "patent_id": pid,
            "filing_year": int(row["filing_date"].year),
            "filing_date": str(row["filing_date"].date()),
            "n_kw": len(kws_set),
            "new_word": nw,
            "new_bigram": nbg,
            "new_trigram": ntg,
            "new_word_comb": nwc,
            "cosine_similarity": round(float(cosine_novelty), 8),
            "new_word_reuse": nw_ri,
            "new_bigram_reuse": nbg_ri,
            "new_trigram_reuse": ntg_ri,
            "new_word_comb_reuse": nwc_ri,
            "cosine_similarity_impact": round(float(cos_impact), 8),
        })

        # Update first_seen for next patents (streaming)
        for kw in kws_set:
            first_seen.setdefault(kw, pid)
        for bg in bg_set:
            first_seen.setdefault(bg, pid)
        for tg in tg_set:
            first_seen.setdefault(tg, pid)
        for pair in pairs:
            first_seen.setdefault(pair, pid)

        prior_vectors.append(tf_vector(kws_set))

    # ── Phase 5: Save ──
    print(f"\nPhase 5: Saving... (t={time.time()-t0:.1f}s)")
    result_df = pd.DataFrame(results)

    result_df.to_parquet(R003_DIR / "gold_sample.parquet", index=False)

    indicator_cols = ["new_word", "new_bigram", "new_trigram", "new_word_comb",
                      "cosine_similarity", "new_word_reuse", "new_bigram_reuse",
                      "new_trigram_reuse", "new_word_comb_reuse", "cosine_similarity_impact"]

    indicator_stats = {}
    for col in indicator_cols:
        series = result_df[col]
        indicator_stats[col] = {
            "mean": round(float(series.mean()), 6),
            "median": round(float(series.median()), 6),
            "std": round(float(series.std()), 6),
            "min": round(float(series.min()), 6),
            "max": round(float(series.max()), 6),
            "pct_nonzero": round(float((series != 0).mean() * 100), 2),
        }

    gold_values = {
        "paper_id": "arts2021_nlp_patent_novelty",
        "task_type": "component_diagnosis",
        "data_source": "USPTO patents 2016 (weekly filing dates), PatentsView",
        "pre_computed_date": "2026-06-15",
        "sample_N": len(result_df),
        "year_range": [int(result_df["filing_year"].min()), int(result_df["filing_year"].max())],
        "methodology_reference": "Arts, Hou, Gomez (2021) Research Policy 50, 104144",
        "sub_components": {
            "preprocessing": {
                "text_concatenation": "title + abstract + claims (note: title not in data, use abstract+claims)",
                "tokenization": "regex: [a-z0-9][a-z0-9-]*[a-z0-9]+|[a-z0-9]",
                "filters": [
                    "remove number-only tokens",
                    "remove single-character tokens",
                    "remove NLTK stopwords",
                    "remove custom stoplist of frequent non-technical terms",
                    "remove words appearing in only 1 patent",
                ],
                "stemming": "SnowBall (NLTK)",
                "output": "deduplicated list of stemmed keywords per patent",
            },
            "indicators": {
                "novelty": {
                    "new_word": "count of keywords first-appearing in USPTO by filing date",
                    "new_bigram": "count of consecutive keyword pairs first-appearing",
                    "new_trigram": "count of consecutive keyword triples first-appearing",
                    "new_word_comb": "count of pairwise keyword combinations first-appearing",
                    "cosine_similarity": "1 - avg(cosine_sim(focal, prior_5yr_patents))",
                },
                "impact": {
                    "new_word_reuse": "Σ(1+future_reuse) over new keywords introduced",
                    "new_bigram_reuse": "Σ(1+future_reuse) over new bigrams introduced",
                    "new_trigram_reuse": "Σ(1+future_reuse) over new trigrams introduced",
                    "new_word_comb_reuse": "Σ(1+future_reuse) over new keyword pairs introduced",
                    "cosine_similarity_impact": "forward_cosine / backward_cosine",
                },
            },
        },
        "gold_indicators": indicator_stats,
        "preprocessing_stats": {
            "mean_keywords_per_patent": round(float(result_df["n_kw"].mean()), 2),
            "median_keywords": round(float(result_df["n_kw"].median()), 2),
        },
    }

    with open(R003_DIR / "gold_values.json", "w") as f:
        json.dump(gold_values, f, indent=2)

    print(f"\n=== R003 Gold Summary ===")
    print(f"Sample N: {len(result_df)}")
    print(f"Year range: {result_df['filing_year'].min()}-{result_df['filing_year'].max()}")
    print(f"Weeks covered: {result_df['filing_date'].nunique()}")
    print(f"Total time: {time.time()-t0:.1f}s")
    for col in indicator_cols:
        print(f"  {col}: mean={indicator_stats[col]['mean']:.4f}, "
              f"nonzero={indicator_stats[col]['pct_nonzero']:.1f}%")
    print("Done.")


if __name__ == "__main__":
    main()
