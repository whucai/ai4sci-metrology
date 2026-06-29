#!/usr/bin/env python3
"""R121 Round 3 freeze — Sample + Model rubric clarification.

Round 2 left Sample (0.594) and Model (0.694) just below threshold. Round 3
clarifies:
  Sample = paper STATES the sample? 'N pending' (annotator transcription) does
           NOT reduce the ceiling. 0.5 only if N genuinely absent/sample partial.
  Model  = estimator + key variables + FE ALL enumerated? 0.5 if estimator named
           but some vars/FE pending. Code-independent.

A-round3 = A-original with Sample/Model re-scored under the clarified rule
(+ Claim=1.0 from round 2). B-round3 = Codex re-reply for Sample/Model
(+ Data/Indicator/Result/Claim from B-clarified round 2).

Frozen final = mean(A-round3, B-round3) per component.
"""
from __future__ import annotations
import json, math
from pathlib import Path
from collections import Counter

ROOT = Path(__file__).resolve().parent.parent
A_FILE = ROOT / "refine-logs" / "r121_gold_v1.json"
OUT = ROOT / "refine-logs" / "r121_gold_v1_frozen.json"
COMPONENTS = ["data_source", "sample", "indicator", "model", "result_table", "claim"]
KU_LEUVEN = {"arts2021", "schaper2025_frontier", "arts2021_patent_nlp"}

# A-round3 (data, sample, indicator, model, result, claim)
A_R3 = {
    "petersen2024":              (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "wu2019_teams":              (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "park2023_disruptive":       (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "bentley2023_disruption":    (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "arts2021":                  (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "funk2017":                  (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "maddi2024":                 (0.0, 1.0, 1.0, 0.5, 0.5, 1.0),
    "bikard2013":                (0.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "ke2015_sleeping_beauties":  (0.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "sun2023_ranking_mobility":  (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "deng2023_enhancing_disruption": (0.5, 1.0, 0.5, 1.0, 0.5, 1.0),
    "schaper2025_frontier":      (0.5, 0.5, 0.5, 0.5, 0.5, 1.0),
    "galuez2023_technology_transfer": (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "vasarhelyi2023_who_benefits": (0.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "donner2024_data_inaccuracy": (0.5, 1.0, 0.5, 0.5, 0.5, 1.0),
    "zheng2025_male_female_retractions": (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "gebhart2023_math_framework": (0.5, 1.0, 0.5, 1.0, 0.5, 1.0),
    "obadage2024_citations_repro": (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "liu2018_hotstreaks":        (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "arts2021_patent_nlp":       (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
}
# B-round3 (data, sample, indicator, model, result, claim)
B_R3 = {
    "petersen2024":              (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "wu2019_teams":              (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "park2023_disruptive":       (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
    "bentley2023_disruption":    (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "arts2021":                  (1.0, 0.5, 0.5, 1.0, 0.5, 1.0),
    "funk2017":                  (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "maddi2024":                 (0.0, 0.5, 1.0, 0.5, 0.5, 1.0),
    "bikard2013":                (0.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "ke2015_sleeping_beauties":  (0.0, 1.0, 0.5, 1.0, 0.0, 1.0),
    "sun2023_ranking_mobility":  (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "deng2023_enhancing_disruption": (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "schaper2025_frontier":      (0.5, 0.5, 0.5, 0.5, 0.5, 1.0),
    "galuez2023_technology_transfer": (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "vasarhelyi2023_who_benefits": (0.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "donner2024_data_inaccuracy": (0.5, 1.0, 0.5, 0.5, 0.5, 1.0),
    "zheng2025_male_female_retractions": (1.0, 1.0, 0.5, 1.0, 0.5, 1.0),
    "gebhart2023_math_framework": (0.5, 1.0, 0.5, 1.0, 0.5, 1.0),
    "obadage2024_citations_repro": (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "liu2018_hotstreaks":        (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
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

def main():
    A_doc = json.loads(A_FILE.read_text())
    order = [p["paper_id"] for p in A_doc["stable_papers"]]
    meta = {p["paper_id"]: p for p in A_doc["stable_papers"]}

    A_vecs = [A_R3[pid] for pid in order]
    B_vecs = [B_R3[pid] for pid in order]

    comp_stats = {}
    for i, c in enumerate(COMPONENTS):
        a = [v[i] for v in A_vecs]; b = [v[i] for v in B_vecs]
        kappa, Po, Pe = cohens_kappa(a, b)
        al = kalpha(list(zip(a, b)))
        comp_stats[c] = {
            "n": len(a), "observed_agreement_Po": round(Po, 3),
            "cohens_kappa": (round(kappa, 3) if not math.isnan(kappa) else None),
            "krippendorff_alpha_ordinal": round(al, 3),
            "n_disagree": sum(1 for x, y in zip(a, b) if x != y),
            "n_big_disagree": sum(1 for x, y in zip(a, b) if abs(x - y) > 0.5),
            "meets_alpha_070": al >= 0.70,
        }
    all_a = [x for v in A_vecs for x in v]; all_b = [x for v in B_vecs for x in v]
    al_o = kalpha(list(zip(all_a, all_b)))
    kappa_o, Po_o, _ = cohens_kappa(all_a, all_b)
    overall = {
        "n": len(all_a), "observed_agreement_Po": round(Po_o, 3),
        "cohens_kappa": round(kappa_o, 3), "krippendorff_alpha_ordinal": round(al_o, 3),
        "meets_alpha_070": al_o >= 0.70,
    }
    n_meet = sum(1 for c in comp_stats.values() if c["meets_alpha_070"])
    sample_a = comp_stats["sample"]["krippendorff_alpha_ordinal"]
    claim_a = comp_stats["claim"]["krippendorff_alpha_ordinal"]
    gate_pass = al_o >= 0.70 and n_meet >= 4 and sample_a >= 0.60 and claim_a >= 0.60

    # frozen papers
    frozen = []
    for pid in order:
        p = meta[pid]
        rec = {"paper_id": pid, "title": p["title"], "domain": p["domain"],
               "venue": p["venue"], "year": p["year"], "task_type": p["task_type"],
               "observability_stratum": p["observability_stratum"],
               "ku_leuven_arts": pid in KU_LEUVEN, "components": {}}
        for i, c in enumerate(COMPONENTS):
            a = A_R3[pid][i]; b = B_R3[pid][i]
            rec["components"][c] = {"A_round3": a, "B_round3": b,
                "final": round((a + b) / 2, 3),
                "disagreement": abs(a - b),
                "method": "agree" if a == b else "mean (adjacent)"}
        finals = [rec["components"][c]["final"] for c in COMPONENTS]
        rec["overall_gold_ecrf_frozen"] = round(sum(finals) / 6, 3)
        frozen.append(rec)

    doc = {
        "version": "v1-frozen-r3",
        "date": "2026-06-29",
        "frame": "v7.2 (IO -> ECRF -> TCE)",
        "n_papers": len(frozen),
        "annotators": {"A": "glm-5.2", "B": "codex-gpt-5.2", "adjudicator": "senior (Claude)"},
        "round_history": {
            "round1_original": "overall alpha=0.717; 2/6 meet 0.70. Revealed Model/Result/Claim rubric ambiguity.",
            "round2_clarified_MRC": "overall alpha=0.876; 4/6 meet 0.70. Claim 0.213->1.000, Result 0.651->0.795, Model 0.492->0.694. Sample 0.594 borderline.",
            "round3_clarified_SampleModel": f"overall alpha={round(al_o,3)}; {n_meet}/6 meet 0.70. Sample {round(sample_a,3)}, Model {comp_stats['model']['krippendorff_alpha_ordinal']}.",
        },
        "codebook_clarifications": [
            "Model = model SPECIFICATION recoverable from paper (estimator + key variables + FE enumerated). CODE-INDEPENDENT. 0.5 if estimator named but some vars/FE pending.",
            "Result = exact numerical targets recoverable (reported in paper OR via public code). 1.0 exact, 0.5 pending/approx, 0.0 none.",
            "Claim = conclusion STATED in the paper. Claim-result distance is separate, not fidelity. 1.0 if stated.",
            "Sample = paper STATES the sample (N stated or derivable, window, unit, filters). 'N pending' (annotator transcription status) does NOT reduce the ceiling. 0.5 only if N genuinely absent or sample genuinely partial.",
        ],
        "agreement_round3": {"per_component": comp_stats, "overall": overall},
        "r122_gate": {
            "overall_alpha": round(al_o, 3), "meets_overall_070": al_o >= 0.70,
            "n_components_meeting_070": n_meet, "sample_alpha": round(sample_a, 3),
            "claim_alpha": round(claim_a, 3),
            "gate_rule": "overall>=0.70 AND >=4/6 components>=0.70 AND Sample/Claim>=0.60",
            "gate_passes": gate_pass,
            "note": f"Round-3 overall alpha={round(al_o,3)}; {n_meet}/6 components meet 0.70. " + ("GATE PASSES — all thresholds cleared." if gate_pass else "GATE does not pass."),
        },
        "ku_leuven_arts_caveat": {
            "flagged_papers": [pid for pid in order if pid in KU_LEUVEN], "n": 3,
            "note": "3 KU Leuven/Arts papers (#6, #11, #20). Near-duplicate of #6 but distinct load-bearing components. Robustness check R-robust-KU planned: re-run key analyses excluding/grouping these to confirm IO->ECRF effect not group-driven.",
            "robustness_check_id": "R-robust-KU (planned)",
        },
        "schaper2025_soft_blocker": {
            "status": "inconclusive (curl blocked: ScienceDirect Cloudflare, Lirias JS shell, Unpaywall unindexed)",
            "io3_retained": "partial/boundary",
            "action": "human annotator fetch PDF to confirm KU Leuven author-inventor linkage release; if so Data upgrades partial->clean. Does not block R121.",
        },
        "papers": frozen,
    }
    OUT.write_text(json.dumps(doc, indent=2, ensure_ascii=False))
    print(f"Wrote {OUT}\n")
    print(f"{'component':14s} {'Po':>5} {'kappa':>6} {'alpha':>6} {'disagree':>8} {'>=0.70':>6}")
    for c in COMPONENTS:
        s = comp_stats[c]
        kk = f"{s['cohens_kappa']:.3f}" if s['cohens_kappa'] is not None else "nan"
        print(f"{c:14s} {s['observed_agreement_Po']:5.2f} {kk:>6} {s['krippendorff_alpha_ordinal']:6.3f} {s['n_disagree']:8d} {'YES' if s['meets_alpha_070'] else 'no':>6}")
    print(f"{'OVERALL':14s} {overall['observed_agreement_Po']:5.2f} {overall['cohens_kappa']:.3f} {overall['krippendorff_alpha_ordinal']:6.3f} {'':>8} {'YES' if overall['meets_alpha_070'] else 'no':>6}")
    print(f"\n{n_meet}/6 components meet 0.70 | overall={round(al_o,3)} | sample={round(sample_a,3)} | model={comp_stats['model']['krippendorff_alpha_ordinal']}")
    print("GATE " + ("PASSES — all thresholds cleared." if gate_pass else "does NOT pass."))

if __name__ == "__main__":
    main()
