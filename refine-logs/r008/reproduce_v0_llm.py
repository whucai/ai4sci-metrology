```python
import numpy as np
import pandas as pd
from collections import defaultdict
from scipy.stats import spearmanr

# Import SciSciNet connector
from src.sciscigpt_local.sciscinet_connector import load_papers_sample, load_table

def main():
    # ------------------------------------------------------------
    # DATA LOAD
    # ------------------------------------------------------------
    print("Loading data...")
    papers = load_papers_sample(n_shards=3)
    pc = load_table("paper_citations")

    # Filter papers
    mask = (
        (papers['year'] >= 1945) &
        papers['disruption_score'].notna() &
        (papers['citation_count'] > 0) &
        (papers['reference_count'] > 0)
    )
    valid = papers[mask].copy()
    n_loaded = len(papers)
    n_valid = len(valid)

    # Sample 500 focal papers
    np.random.seed(42)
    focal_indices = np.random.choice(valid.index, size=min(500, n_valid), replace=False)
    focal = valid.loc[focal_indices].reset_index(drop=True)
    focal_ids = focal['paper_id'].tolist()

    print("\n=== DATA_LOAD ===")
    print(f"{n_loaded} papers loaded, {n_valid} valid, {len(focal_ids)} focal sampled")

    # ------------------------------------------------------------
    # BUILD CITATION GRAPH AND LOCAL DICTIONARIES
    # ------------------------------------------------------------
    # focal -> references (papers it cites)
    focal_refs = {}
    # focal -> citers (papers that cite it)
    focal_citers = {}

    print("Building focal reference and citer sets...")
    for pid in focal_ids:
        refs = pc[pc['citing_paper_id'] == pid]['cited_paper_id'].drop_duplicates()
        focal_refs[pid] = set(refs)
        citers = pc[pc['cited_paper_id'] == pid]['citing_paper_id'].drop_duplicates()
        focal_citers[pid] = set(citers)

    # All unique citers of the focal papers (we'll need their reference lists)
    all_citers = set()
    for s in focal_citers.values():
        all_citers.update(s)

    # All unique references cited by focal papers
    all_refs = set()
    for s in focal_refs.values():
        all_refs.update(s)

    # Citer -> references (what each citer of a focal paper cites)
    print("Building citer_references...")
    citer_refs_df = pc[pc['citing_paper_id'].isin(all_citers)]
    citer_refs = defaultdict(set)
    for citing, cited in zip(citer_refs_df['citing_paper_id'], citer_refs_df['cited_paper_id']):
        citer_refs[citing].add(cited)

    # Reference -> citers (who cites each reference)
    print("Building reference_citers...")
    ref_citers_df = pc[pc['cited_paper_id'].isin(all_refs)]
    ref_citers = defaultdict(set)
    for cited, citing in zip(ref_citers_df['cited_paper_id'], ref_citers_df['citing_paper_id']):
        ref_citers[cited].add(citing)

    n_edges = len(pc)
    unique_cited_in_graph = pc['cited_paper_id'].nunique()
    in_degree_range = (pc.groupby('cited_paper_id').size().min(),
                       pc.groupby('cited_paper_id').size().max())

    print("\n=== CITATION_GRAPH ===")
    print(f"{n_edges} edges in paper_citations, {unique_cited_in_graph} unique cited papers, "
          f"in-degree range {in_degree_range[0]}-{in_degree_range[1]}")

    # ------------------------------------------------------------
    # HOT‑SPOT IDENTIFICATION
    # ------------------------------------------------------------
    # Compute in‑degree for every reference cited by any focal paper
    ref_degree = {r: len(ref_citers.get(r, set())) for r in all_refs}
    sorted_refs = sorted(all_refs, key=lambda x: ref_degree[x], reverse=True)
    n_refs_total = len(all_refs)
    top_k = int(np.ceil(0.03 * n_refs_total)) if n_refs_total > 0 else 0
    hotspot_ids = set(sorted_refs[:top_k]) if top_k > 0 else set()

    print("\n=== HOTSPOT ===")
    print(f"{n_refs_total} unique references, threshold top {top_k} papers, "
          f"{len(hotspot_ids)} hotspot papers identified")

    # ------------------------------------------------------------
    # BASELINE CD5
    # ------------------------------------------------------------
    baseline_cd5 = []
    print("Computing baseline CD5...")
    for i, pid in enumerate(focal_ids):
        A = focal_citers[pid]
        refs = focal_refs[pid]

        # B: union of papers citing any reference of the focal paper
        B = set()
        for r in refs:
            B.update(ref_citers.get(r, set()))

        nk = len(B - A)
        ni = 0
        nj = 0
        for c in A:
            overlap = citer_refs.get(c, set()) & refs
            if overlap:
                nj += 1
            else:
                ni += 1

        denom = ni + nj + nk
        cd5 = (ni - nj) / denom if denom > 0 else np.nan
        baseline_cd5.append(cd5)

        if (i + 1) % 100 == 0:
            print(f"  processed {i+1}/{len(focal_ids)}")

    baseline_mean = np.nanmean(baseline_cd5)
    baseline_std = np.nanstd(baseline_cd5)

    print("\n=== CD5_BASELINE ===")
    print(f"Mean: {baseline_mean:.4f}, Std: {baseline_std:.4f}")

    # ------------------------------------------------------------
    # CD5 AFTER EDGE REMOVAL
    # ------------------------------------------------------------
    new_cd5 = []
    n_changed = 0
    print("Computing CD5 after edge removal...")

    for i, pid in enumerate(focal_ids):
        A = focal_citers[pid]
        refs = focal_refs[pid]

        # B' : ignore citations to hot‑spot references
        B_prime = set()
        for r in refs:
            if r not in hotspot_ids:
                B_prime.update(ref_citers.get(r, set()))

        nk_prime = len(B_prime - A)
        ni_prime = 0
        nj_prime = 0
        for c in A:
            overlap = (citer_refs.get(c, set()) - hotspot_ids) & refs
            if overlap:
                nj_prime += 1
            else:
                ni_prime += 1

        denom = ni_prime + nj_prime + nk_prime
        cd5_p = (ni_prime - nj_prime) / denom if denom > 0 else np.nan
        new_cd5.append(cd5_p)

        # track change
        if not np.isnan(cd5_p) and (np.isnan(baseline_cd5[i]) or cd5_p != baseline_cd5[i]):
            n_changed += 1

        if (i + 1) % 100 == 0:
            print(f"  processed {i+1}/{len(focal_ids)}")

    new_mean = np.nanmean(new_cd5)
    new_std = np.nanstd(new_cd5)
    delta = np.nanmean(np.array(new_cd5) - np.array(baseline_cd5))

    print("\n=== CD5_EDGE_REMOVAL ===")
    print(f"Mean new CD5: {new_mean:.4f}, Std: {new_std:.4f}")
    print(f"Mean Δ CD5: {delta:.4f}")
    print(f"Papers with CD5 change: {n_changed}")

    # ------------------------------------------------------------
    # COMPARISON
    # ------------------------------------------------------------
    # Spearman rank correlation (ignore nans)
    mask_nan = ~np.isnan(baseline_c