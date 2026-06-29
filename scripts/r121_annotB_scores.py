#!/usr/bin/env python3
"""R121 annotator B (Codex/GPT-5.2) scores — transcribed from Codex reply.
Component order: data_source, sample, indicator, model, result_table, claim.
Verifies totals: 57x1.0, 59x0.5, 4x0.0 (120 total)."""
B = {
    "petersen2024":              (1.0, 1.0, 1.0, 0.5, 0.5, 1.0),
    "wu2019_teams":              (1.0, 1.0, 1.0, 0.5, 0.5, 1.0),
    "park2023_disruptive":       (1.0, 1.0, 1.0, 0.5, 0.5, 1.0),
    "bentley2023_disruption":    (1.0, 1.0, 1.0, 0.5, 0.5, 1.0),
    "arts2021":                  (1.0, 0.5, 0.5, 0.5, 0.5, 1.0),
    "funk2017":                  (1.0, 0.5, 1.0, 0.5, 0.5, 1.0),
    "maddi2024":                 (0.0, 0.5, 1.0, 0.5, 0.5, 1.0),
    "bikard2013":                (0.0, 1.0, 0.5, 0.5, 0.5, 1.0),
    "ke2015_sleeping_beauties":  (0.0, 1.0, 0.5, 0.5, 0.5, 1.0),
    "sun2023_ranking_mobility":  (1.0, 0.5, 0.5, 0.5, 0.5, 1.0),
    "deng2023_enhancing_disruption": (1.0, 1.0, 0.5, 0.5, 0.5, 1.0),
    "schaper2025_frontier":      (0.5, 0.5, 0.5, 0.5, 0.5, 1.0),
    "galuez2023_technology_transfer": (1.0, 0.5, 0.5, 0.5, 0.5, 1.0),
    "vasarhelyi2023_who_benefits": (0.0, 0.5, 0.5, 0.5, 0.5, 1.0),
    "donner2024_data_inaccuracy": (0.5, 0.5, 0.5, 0.5, 0.5, 1.0),
    "zheng2025_male_female_retractions": (1.0, 0.5, 0.5, 0.5, 0.5, 1.0),
    "gebhart2023_math_framework": (0.5, 1.0, 0.5, 0.5, 0.5, 1.0),
    "obadage2024_citations_repro": (1.0, 1.0, 1.0, 1.0, 0.5, 1.0),
    "liu2018_hotstreaks":        (1.0, 0.5, 1.0, 1.0, 1.0, 1.0),
    "arts2021_patent_nlp":       (1.0, 1.0, 1.0, 1.0, 1.0, 1.0),
}
COMPONENTS = ["data_source", "sample", "indicator", "model", "result_table", "claim"]

if __name__ == "__main__":
    from collections import Counter
    c = Counter()
    for v in B.values():
        for s in v:
            c[s] += 1
    print("B totals:", dict(c), "sum", sum(c.values()))
    assert c[1.0] == 57 and c[0.5] == 59 and c[0.0] == 4, "B totals mismatch"
    print("OK — matches Codex reported 57/59/4")
