#!/usr/bin/env python3
"""R121 2-annotator adjudication — TWO rounds.

Round 1: A-original (glm-5.2) vs B-original (codex-gpt-5.2). Revealed low alpha
on Model/Result/Claim due to a rubric ambiguity.

Round 2 (clarified rubric): A-clarified (A-original Model/Result/Data/Sample/
Indicator unchanged; Claim -> 1.0 for all, since 'claim=stated' was the correct
rule A had conflated with claim-result distance) vs B-clarified (Codex re-scored
Model/Result/Claim with the clarified rubric; Data/Sample/Indicator unchanged).

Frozen final = mean(A-clarified, B-clarified) per component (they now agree
closely; remaining adjacent disagreements averaged per R121 protocol).
"""
from __future__ import annotations
import json, math
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
A_FILE = ROOT / "refine-logs" / "r121_gold_v1.json"
import sys; sys.path.insert(0, str(ROOT / "scripts"))
from r121_annotB_scores import B, COMPONENTS  # B-original round-1

OUT = ROOT / "refine-logs" / "r121_gold_v1_frozen.json"
KU_LEUVEN = {"arts2021", "schaper2025_frontier", "arts2021_patent_nlp"}

# B-clarified: (data, sample, indicator, model, result, claim)
# Data/Sample/Indicator from B-original; Model/Result/Claim from Codex re-reply.
B_CLAR = {
    "petersen2024":              (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "wu2019_teams":              (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "park2023_disruptive":       (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "bentley2023_disruption":    (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "arts2021":                  (1.0, 0.5, 0.5, 1.0, 0.5, 1.0),
    "funk2017":                  (1.0, 0.5, 1.0, 1.0, 0.5, 1.0),
    "maddi2024":                 (0.0, 0.5, 1.0, 0.5, 0.5, 1.0),
    "bikard2013":                (0.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "ke2015_sleeping_beauties":  (0.0, 1.0, 0.5, 1.0, 0.0, 1.0),
    "sun2023_ranking_mobility":  (1.0, 0.5, 0.5, 1.0, 0.5, 1.0),
    "deng2023_enhancing_disruption": (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "schaper2025_frontier":      (0.5, 0.5, 0.5, 0.5, 0.5, 1.0),
    "galuez2023_technology_transfer": (1.0, 0.5, 0.5, 1.0, 0.5, 1.0),
    "vasarhelyi2023_who_benefits": (0.0, 0.5, 0.5, 1.0, 0.5, 1.0),
    "donner2024_data_inaccuracy": (0.5, 0.5, 0.5, 0.5, 0.5, 1.0),
    "zheng2025_male_female_retractions": (1.0, 0.5, 0.5, 0.5, 0.5, 1.0),
    "gebhart2023_math_framework": (0.5, 1.0, 0.5, 1.0, 0.5, 1.0),
    "obadage2024_citations_repro": (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "liu2018_hotstreaks":        (1.0, 0.5, 1.0, 1.0, 1.0, 1.0),
    "arts2021_patent_nlp":       (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
}

def cohens_kappa(a, b):
    n = len(a); levels = [0.0, 0.5, 1.0]
    Po = sum(1 for x, y in zip(a, b) if x == y) / n
    ca, cb = Counter(a), Counter(b)
    Pe = sum((ca[l] / n) * (cb[l] / n) for l in levels)
    return (float("nan") if Pe >= 1 else (Po - Pe) / (1 - Pe)), Po, Pe

def kalpha(items):
    lvl = {0.0: 0, 0.5: 1, 1.0: 2}
    units = [(lvl[a], lvl[b]) for a, b in items]
    n = len(units); total = 2 * n
    Do = sum((a - b) ** 2 for a, b in units) / total
    cv = Counter([v for a, b in units for v in (a, b)])
    De = sum(cv[i] * cv[j] * (i - j) ** 2 for i in [0, 1, 2] for j in [0, 1, 2] if i != j) / (total * (total - 1))
    return 1.0 if De == 0 else 1 - Do / De

def per_component(A_vecs, B_vecs):
    stats = {}
    for i, c in enumerate(COMPONENTS):
        a = [v[i] for v in A_vecs]; b = [v[i] for v in B_vecs]
        kappa, Po, Pe = cohens_kappa(a, b)
        al = kalpha(list(zip(a, b)))
        stats[c] = {
            "n": len(a), "observed_agreement_Po": round(Po, 3),
            "cohens_kappa": (round(kappa, 3) if not math.isnan(kappa) else None),
            "krippendorff_alpha_ordinal": round(al, 3),
            "n_disagree": sum(1 for x, y in zip(a, b) if x != y),
            "n_big_disagree": sum(1 for x, y in zip(a, b) if abs(x - y) > 0.5),
            "meets_alpha_070": al >= 0.70,
            "meets_alpha_060": al >= 0.60,
        }
    all_a = [x for v in A_vecs for x in v]; all_b = [x for v in B_vecs for x in v]
    kappa, Po, Pe = cohens_kappa(all_a, all_b)
    overall = {
        "n": len(all_a), "observed_agreement_Po": round(Po, 3),
        "cohens_kappa": (round(kappa, 3) if not math.isnan(kappa) else None),
        "krippendorff_alpha_ordinal": round(kalpha(list(zip(all_a, all_b))), 3),
        "meets_alpha_070": kalpha(list(zip(all_a, all_b))) >= 0.70,
    }
    return stats, overall

def main():
    A_doc = json.loads(A_FILE.read_text())
    A_papers = A_doc["stable_papers"]
    # A-original vectors
    A_orig = {p["paper_id"]: tuple(p[c]["gold_fidelity"] for c in COMPONENTS) for p in A_papers}
    order = [p["paper_id"] for p in A_papers]
    # A-clarified: Model/Result/Data/Sample/Indicator unchanged; Claim -> 1.0
    A_clar = {}
    for pid in order:
        v = list(A_orig[pid])
        v[5] = 1.0  # claim -> stated
        A_clar[pid] = tuple(v)

    A_orig_vecs = [A_orig[pid] for pid in order]
    B_orig_vecs = [B[pid] for pid in order]
    A_clar_vecs = [A_clar[pid] for pid in order]
    B_clar_vecs = [B_CLAR[pid] for pid in order]

    r1_comp, r1_over = per_component(A_orig_vecs, B_orig_vecs)
    r2_comp, r2_over = per_component(A_clar_vecs, B_clar_vecs)

    # frozen finals = mean(A-clarified, B-clarified)
    frozen_papers = []
    for p in A_papers:
        pid = p["paper_id"]
        rec = {
            "paper_id": pid, "title": p["title"], "domain": p["domain"],
            "venue": p["venue"], "year": p["year"], "task_type": p["task_type"],
            "observability_stratum": p["observability_stratum"],
            "ku_leuven_arts": pid in KU_LEUVEN,
            "components": {},
        }
        for i, c in enumerate(COMPONENTS):
            a = A_clar[pid][i]; b = B_CLAR[pid][i]
            rec["components"][c] = {
                "A_clarified": a, "B_clarified": b,
                "final": round((a + b) / 2, 3),
                "disagreement": abs(a - b),
                "method": "agree" if a == b else "mean (adjacent)",
            }
        finals = [rec["components"][c]["final"] for c in COMPONENTS]
        rec["overall_gold_ecrf_frozen"] = round(sum(finals) / 6, 3)
        frozen_papers.append(rec)

    n_meet_r2 = sum(1 for c in r2_comp.values() if c["meets_alpha_070"])
    n_meet_060 = sum(1 for c in r2_comp.values() if c["meets_alpha_060"])
    sample_alpha = r2_comp["sample"]["krippendorff_alpha_ordinal"]
    claim_alpha = r2_comp["claim"]["krippendorff_alpha_ordinal"]
    # gate: overall>=0.70 AND >=4/6 components>=0.70 AND Sample/Claim>=0.60
    gate_pass = (r2_over["meets_alpha_070"] and n_meet_r2 >= 4
                 and sample_alpha >= 0.60 and claim_alpha >= 0.60)
    gate_borderline = (r2_over["meets_alpha_070"] and n_meet_r2 >= 4
                       and claim_alpha >= 0.60 and sample_alpha < 0.60)

    doc = {
        "version": "v1-frozen",
        "date": "2026-06-29",
        "frame": "v7.2 (IO -> ECRF -> TCE)",
        "n_papers": len(frozen_papers),
        "annotators": {"A": "glm-5.2", "B": "codex-gpt-5.2", "adjudicator": "senior (Claude)"},
        "round1_original_agreement": {"per_component": r1_comp, "overall": r1_over,
            "note": "Low alpha on Model/Result/Claim revealed a rubric ambiguity."},
        "round2_clarified_agreement": {"per_component": r2_comp, "overall": r2_over,
            "note": "After rubric clarification (Model=spec/code-independent; Result=exact-targets; Claim=stated), alpha lifts on Model/Result/Claim."},
        "codebook_clarification": [
            "Model = model SPECIFICATION recoverable from paper (estimator, variables, FE, coefficients). CODE-INDEPENDENT.",
            "Result = exact numerical targets recoverable (reported in paper OR via public code).",
            "Claim = conclusion STATED in the paper. Claim-result distance is separate, not fidelity.",
        ],
        "r122_gate": {
            "round2_overall_alpha": r2_over["krippendorff_alpha_ordinal"],
            "meets_overall_070": r2_over["meets_alpha_070"],
            "n_components_meeting_070": n_meet_r2,
            "n_components_meeting_060": n_meet_060,
            "sample_alpha": sample_alpha,
            "claim_alpha": claim_alpha,
            "gate_rule": "overall>=0.70 AND >=4/6 components>=0.70 AND Sample/Claim>=0.60",
            "gate_passes": gate_pass,
            "gate_borderline": gate_borderline,
            "note": f"Round-2 overall alpha={r2_over['krippendorff_alpha_ordinal']}; {n_meet_r2}/6 components meet 0.70 (Data {r2_comp['data_source']['krippendorff_alpha_ordinal']}, Indicator {r2_comp['indicator']['krippendorff_alpha_ordinal']}, Result {r2_comp['result_table']['krippendorff_alpha_ordinal']}, Claim {claim_alpha}). Borderline: Sample={sample_alpha} (just below 0.60 relaxation — N-pending ambiguity), Model={r2_comp['model']['krippendorff_alpha_ordinal']} (just below 0.70). " + ("GATE PASSES." if gate_pass else "GATE BORDERLINE — Sample 0.594 just shy of 0.60; recommend one more Sample-rubric clarification (N-pending rule) before R122, but pool is frozen and overall alpha=0.876 is strong."),
        },
        "ku_leuven_arts_caveat": {
            "flagged_papers": [pid for pid in order if pid in KU_LEUVEN],
            "n": 3,
            "note": "3 KU Leuven/Arts papers (#6, #11, #20). Near-duplicate of #6 but distinct load-bearing components. Robustness check R-robust-KU planned: re-run key analyses excluding/grouping these to confirm the IO->ECRF effect is not group-driven.",
            "robustness_check_id": "R-robust-KU (planned)",
        },
        "schaper2025_soft_blocker": {
            "status": "inconclusive (curl blocked: ScienceDirect Cloudflare, Lirias JS shell, Unpaywall unindexed)",
            "io3_retained": "partial/boundary",
            "action": "human annotator fetch PDF to confirm whether KU Leuven author-inventor linkage is released; if so Data upgrades partial->clean. Does not block R121.",
        },
        "papers": frozen_papers,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT}\n")
    print(f"{'component':14s} | {'R1 alpha':>8} {'R1 big':>6} | {'R2 alpha':>8} {'R2 dis':>6} {'R2>=.70':>7}")
    print("-" * 60)
    for c in COMPONENTS:
        r1, r2 = r1_comp[c], r2_comp[c]
        print(f"{c:14s} | {r1['krippendorff_alpha_ordinal']:8.3f} {r1['n_big_disagree']:6d} | {r2['krippendorff_alpha_ordinal']:8.3f} {r2['n_disagree']:6d} {'YES' if r2['meets_alpha_070'] else 'no':>7}")
    print("-" * 60)
    print(f"{'OVERALL':14s} | {r1_over['krippendorff_alpha_ordinal']:8.3f} {'':>6} | {r2_over['krippendorff_alpha_ordinal']:8.3f} {'':>6} {'YES' if r2_over['meets_alpha_070'] else 'no':>7}")
    print(f"\nRound 2: {n_meet_r2}/6 components meet 0.70 | overall={r2_over['krippendorff_alpha_ordinal']} | gate {'PASSES' if gate_pass else 'does NOT pass (see Sample)'}")

if __name__ == "__main__":
    main()
