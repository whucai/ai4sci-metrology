#!/usr/bin/env python3
"""R008 Gold Computation: Deng2023 edge-removal disruption robustness.

Deng & Zeng (2023) "Enhancing the robustness of the disruption metric against noise"
Scientometrics, 2023. DOI: 10.1007/s11192-023-04644-2

Method: Remove edges to "hot-spot papers" (top k% most cited references),
recompute CD5 disruption index, and compare paper rankings before/after.

CD5 formula: D = (ni - nj) / (ni + nj + nk)
  ni = # citing focal but NONE of focal's references
  nj = # citing both focal AND at least one reference
  nk = # citing references but NOT focal

Hot-spot: references in top P% of citation count among all references.
After removal: edges from citers to hot-spot refs are ignored when computing nj.

Usage:
    python scripts/r008_deng2023_gold_computation.py [--n-focal 500] [--top-pct 3]
"""

import json, sys, time
from collections import defaultdict
from pathlib import Path

import numpy as np

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
from src.sciscigpt_local.sciscinet_connector import load_papers_sample, load_table

OUTPUT_DIR = Path(__file__).resolve().parent.parent / "refine-logs" / "r008"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
np.random.seed(42)


def compute_cd5(ni, nj, nk):
    denom = ni + nj + nk
    if denom == 0:
        return 0.0
    return (ni - nj) / denom


def main():
    import argparse
    parser = argparse.ArgumentParser()
    parser.add_argument("--n-focal", type=int, default=500)
    parser.add_argument("--top-pct", type=float, default=3.0)
    parser.add_argument("--n-shards", type=int, default=3)
    args = parser.parse_args()

    print("=" * 70)
    print(f"R008 Gold: Deng2023 Edge-Removal (n_focal={args.n_focal}, top_pct={args.top_pct}%)")
    print("=" * 70)

    # 1. Load papers metadata
    print("\n[1/5] Loading papers metadata...")
    papers = load_papers_sample(n_shards=args.n_shards)
    valid = papers[
        papers["disruption_score"].notna() &
        (papers["citation_count"] > 0) &
        (papers["reference_count"] > 0) &
        (papers["year"] >= 1945)
    ].copy()
    print(f"  {len(papers):,} papers loaded, {len(valid):,} valid")

    # Sample focal papers
    indices = np.random.choice(len(valid), size=min(args.n_focal, len(valid)), replace=False)
    focal = valid.iloc[indices].copy()
    focal_ids = set(focal["paper_id"].values)
    print(f"  Sampled {len(focal):,} focal papers")

    # 2. Load citation graph
    print("\n[2/5] Loading paper_citations (78M edges)...")
    t0 = time.time()
    pc = load_table("paper_citations")
    print(f"  Loaded {len(pc):,} edges in {time.time()-t0:.1f}s")

    # 3. Build citation counts from paper_citations for hot-spot ranking
    print("\n[3/5] Computing citation counts from paper_citations...")
    t0 = time.time()
    # In-degree: how many papers cite each paper
    in_degree = pc.groupby("cited_paper_id").size()
    print(f"  {len(in_degree):,} unique cited papers, in-degree range [{in_degree.min()}, {in_degree.max()}]")
    citation_counts = in_degree.to_dict()
    print(f"  Done in {time.time()-t0:.1f}s")

    # 4. Build citation indices for focal papers
    print("\n[4/5] Building citation indices...")
    t0 = time.time()

    # Focal → references (papers focal cites)
    focal_cites = pc[pc["citing_paper_id"].isin(focal_ids)]
    refs = defaultdict(set)
    for row in focal_cites.itertuples(index=False):
        refs[row.citing_paper_id].add(row.cited_paper_id)
    print(f"  refs: {len(refs)} focal papers → {sum(len(v) for v in refs.values())} total refs")

    # Focal → citers (papers that cite focal)
    focal_cited_by = pc[pc["cited_paper_id"].isin(focal_ids)]
    citers = defaultdict(set)
    for row in focal_cited_by.itertuples(index=False):
        citers[row.cited_paper_id].add(row.citing_paper_id)
    print(f"  citers: {len(citers)} focal papers → {sum(len(v) for v in citers.values())} total citers")

    # Citer → references (for nj computation)
    all_citer_ids = set()
    for cs in citers.values():
        all_citer_ids.update(cs)
    print(f"  Building citer_refs for {len(all_citer_ids):,} unique citers...")
    citer_cites = pc[pc["citing_paper_id"].isin(all_citer_ids)]
    citer_refs = defaultdict(set)
    for row in citer_cites.itertuples(index=False):
        citer_refs[row.citing_paper_id].add(row.cited_paper_id)
    print(f"  citer_refs: {len(citer_refs)} citers")

    print(f"  Indices built in {time.time()-t0:.1f}s")

    # 5. Compute disruption (baseline + edge-removal)
    print(f"\n[5/5] Computing disruption...")

    # Identify hot-spot papers: top top_pct% most cited among ALL references of focal papers
    all_ref_ids = set()
    for rset in refs.values():
        all_ref_ids.update(rset)

    ref_cit_counts = {}
    for rid in all_ref_ids:
        cnt = citation_counts.get(rid, 0)
        if cnt > 0:
            ref_cit_counts[rid] = cnt

    n_refs_with_cites = len(ref_cit_counts)
    threshold_idx = int(n_refs_with_cites * (1 - args.top_pct / 100))
    threshold = sorted(ref_cit_counts.values())[max(0, threshold_idx - 1)]
    hotspot_ids = {rid for rid, cnt in ref_cit_counts.items() if cnt >= threshold}
    print(f"  Unique references: {len(all_ref_ids):,}")
    print(f"  References with citation data: {n_refs_with_cites:,}")
    print(f"  Hot-spot threshold (top {args.top_pct}%): ≥{threshold} citations")
    print(f"  Hot-spot papers: {len(hotspot_ids):,}")

    results = []
    t0 = time.time()
    for i, (_, row) in enumerate(focal.iterrows()):
        pid = row["paper_id"]
        f_refs = refs.get(pid, set())
        f_citers = citers.get(pid, set())

        # Baseline: standard CD5
        ni_base, nj_base = 0, 0
        for cid in f_citers:
            cr = citer_refs.get(cid, set())
            if cr & f_refs:
                nj_base += 1
            else:
                ni_base += 1
        # nk: papers citing refs but NOT focal
        all_ref_citers = set()
        for rid in f_refs:
            all_ref_citers.update(citers.get(rid, set()))
        nk_base = len(all_ref_citers - f_citers)
        cd5_base = compute_cd5(ni_base, nj_base, nk_base)

        # Edge-removal: ignore edges to hot-spot refs
        hotspot_in_refs = f_refs & hotspot_ids
        ni_new, nj_new = 0, 0
        for cid in f_citers:
            cr = citer_refs.get(cid, set())
            effective_refs = cr - hotspot_ids  # remove hot-spot edges
            if effective_refs & f_refs:
                nj_new += 1
            else:
                ni_new += 1
        nk_new = nk_base  # nk unchanged (ref citers don't depend on citer's edges)
        cd5_new = compute_cd5(ni_new, nj_new, nk_new)

        results.append({
            "paper_id": int(pid),
            "year": int(row["year"]),
            "citation_count": int(row["citation_count"]),
            "reference_count": int(row["reference_count"]),
            "disruption_score_sci": float(row["disruption_score"]),
            "baseline_ni": ni_base, "baseline_nj": nj_base, "baseline_nk": nk_base,
            "baseline_cd5": round(cd5_base, 8),
            "new_ni": ni_new, "new_nj": nj_new, "new_nk": nk_new,
            "new_cd5": round(cd5_new, 8),
            "cd5_delta": round(cd5_new - cd5_base, 8),
            "hotspot_refs_in_focal_refs": len(hotspot_in_refs),
            "n_refs": len(f_refs),
            "n_citers": len(f_citers),
        })

        if (i + 1) % 100 == 0:
            print(f"  {i+1}/{len(focal)} ({time.time()-t0:.1f}s)")

    print(f"  Done in {time.time()-t0:.1f}s")

    # Summary
    baseline_cd5s = [r["baseline_cd5"] for r in results]
    new_cd5s = [r["new_cd5"] for r in results]
    deltas = [r["cd5_delta"] for r in results]
    corr = np.corrcoef(baseline_cd5s, new_cd5s)[0, 1]
    baseline_ranks = np.argsort(np.argsort(baseline_cd5s))
    new_ranks = np.argsort(np.argsort(new_cd5s))
    rank_corr = np.corrcoef(baseline_ranks, new_ranks)[0, 1]
    big_rank_change = np.mean(np.abs(baseline_ranks - new_ranks) > len(results) * 0.1)

    print(f"\n=== Summary ===")
    print(f"  N focal: {len(results)}")
    print(f"  Baseline CD5: mean={np.mean(baseline_cd5s):.6f}, std={np.std(baseline_cd5s):.6f}")
    print(f"  New CD5: mean={np.mean(new_cd5s):.6f}, std={np.std(new_cd5s):.6f}")
    print(f"  CD5 delta: mean={np.mean(deltas):.8f}, std={np.std(deltas):.6f}")
    print(f"  Corr(baseline, new): {corr:.6f}")
    print(f"  Rank corr: {rank_corr:.6f}")
    print(f"  Pct significant rank change: {big_rank_change:.2%}")
    n_affected = sum(1 for r in results if abs(r["cd5_delta"]) > 1e-10)
    print(f"  Papers with CD5 change: {n_affected}/{len(results)}")

    # Top movers
    sorted_by_delta = sorted(results, key=lambda r: abs(r["cd5_delta"]), reverse=True)
    print(f"\n  Top 10 papers by |CD5 change|:")
    for r in sorted_by_delta[:10]:
        print(f"    id={r['paper_id']}, base={r['baseline_cd5']:.6f}, "
              f"new={r['new_cd5']:.6f}, delta={r['cd5_delta']:.6f}, "
              f"hotspots_in_refs={r['hotspot_refs_in_focal_refs']}")

    gold = {
        "paper_id": "deng2023_enhancing_disruption",
        "title": "Enhancing the robustness of the disruption metric against noise",
        "venue": "Scientometrics", "year": 2023,
        "task_type": "component",
        "data_source": "SciSciNet (substitute for APS data)",
        "pre_computed_date": "2026-06-17",
        "methodology": (
            "Remove edges from citing papers to hot-spot papers (top-k% most cited references), "
            "recompute CD5 = (ni-nj)/(ni+nj+nk). Tests whether edge removal changes disruption rankings."
        ),
        "parameters": {"n_focal": args.n_focal, "top_pct": args.top_pct, "n_shards": args.n_shards},
        "summary": {
            "n_focal": len(results),
            "baseline_cd5_mean": round(float(np.mean(baseline_cd5s)), 8),
            "baseline_cd5_std": round(float(np.std(baseline_cd5s)), 8),
            "new_cd5_mean": round(float(np.mean(new_cd5s)), 8),
            "new_cd5_std": round(float(np.std(new_cd5s)), 8),
            "cd5_delta_mean": round(float(np.mean(deltas)), 8),
            "cd5_delta_std": round(float(np.std(deltas)), 8),
            "correlation_baseline_new": round(float(corr), 6),
            "rank_correlation": round(float(rank_corr), 6),
            "pct_significant_rank_change": round(float(big_rank_change), 4),
            "n_papers_with_cd5_change": n_affected,
            "mean_hotspot_refs_per_paper": round(float(np.mean([r["hotspot_refs_in_focal_refs"] for r in results])), 2),
            "n_hotspot_papers_total": len(hotspot_ids),
        },
        "per_paper_results": results,
    }

    gold_path = OUTPUT_DIR / "gold_values.json"
    with open(gold_path, "w") as f:
        json.dump(gold, f, indent=2, default=str)
    print(f"\nGold saved to {gold_path}")
    print("Done.")


if __name__ == "__main__":
    main()
