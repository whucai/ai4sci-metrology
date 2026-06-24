# R101 Report — Mini Study 2, IO₂ (2026-06-24)

**Design**: 5 papers × IO₂ × 2 models = 10 runs. IO₂ = paper + structured docs (data dictionary/sample notes/indicator defs) + controlled raw data (where available) + **no executable code**. Image `sciscigpt-ds:0.1`, no-network jail, sibling-isolation. ECRF v1 scorer. R102 remains blocked.

## 1. Run status — 10/10

All 10 runs: status DONE, exit 0, **network blocked on all 10**, **no leakage** (files_written only `_audit_*`). No routing/isolation failures.

## 2. ECRF v1 scores (IO₂)

| Paper | qwen3-32b | deepseek |
|-------|-----------|----------|
| petersen2024 | 0.450 | 0.450 |
| arts2021 | 0.475 | 0.400 |
| funk2017 | **0.600** | 0.500 |
| maddi2024 | 0.500 | 0.500 |
| bikard2013 | 0.450 | 0.500 |

## 3. IO₁ vs IO₂ comparison

| Metric | IO₁ | IO₂ | Δ |
|--------|-----|-----|---|
| **overall mean** | 0.490 | **0.483** | **−0.008** ❌ criterion FAIL |
| Result component | 0.35 | **0.40** | **+0.05** ✅ criterion PASS |
| data_source | 1.00 | 0.75 | −0.25 |
| sample | 0.60 | 0.45 | −0.15 |
| indicator | 1.00 | 1.00 | 0 |
| model | 0.85 | 0.90 | +0.05 |
| claim | 0.95 | 1.00 | +0.05 |

Per-paper IO₂ mean: petersen 0.45 · arts 0.44 · funk 0.55 · maddi 0.50 · bikard 0.48.
Per-model IO₂ mean: qwen3-32b 0.495 · deepseek 0.470.

**The headline criterion (IO₂ overall > IO₁ 0.490) FAILS** (0.483 < 0.490, essentially flat). But the **Result component improved** (the real fidelity signal) and Model/Claim ticked up. The overall is dragged down by data_source/sample *dropping* — a scorer artifact (see §5).

## 4. Result-line classification

Only **1 PAPER_REPORTED** line detected across all 10 runs; 0 COMPUTED / 0 DATA_SUB / 0 SYNTHETIC lines. **The classifier is too strict** — it requires a line containing "result" + "=" + a 2+ decimal number. Agents print results in table format or with other labels, so the regex misses them. This is a **scorer limitation, not a real absence of results**. The gate-(c) code-keyword detection (which doesn't depend on output lines) still works. The classifier needs loosening before R102.

## 5. Synthetic gate (c) vs DATA_SUB — **no misfire** ✅

| Run | data provided? | synth in code? | gate (c) fired? |
|-----|----------------|----------------|-----------------|
| petersen × qwen | ✅ | ❌ | ❌ (correct — used real data) |
| petersen × deepseek | ✅ | ❌ | ❌ |
| bikard × qwen | ✅ | ❌ | ❌ |
| funk × qwen | ✅ | ❌ | ❌ |
| arts × both | ✅ | ✅ | ✅ (agent synthesized despite data) |
| bikard × deepseek | ✅ | ✅ | ✅ |
| funk × deepseek | ✅ | ✅ | ✅ |
| maddi × both | ❌ (no Publons) | ✅ | ✅ |

**Gate (c) does NOT misfire on legitimate DATA_SUB.** The 4 runs where the agent used the provided real SciSciNet/patent data were correctly *not* penalized. The 6 runs where the agent synthesized (4 ignored provided data; 2 had no data) were correctly capped. This is the key design validation: the gate distinguishes substitute-real-data from synthetic-toy-data.

## 6. B₁–B₄ candidates (IO₂, refined rules)

| Break | Count |
|-------|-------|
| B₁ Substitution | 6 |
| B₄ Assertion | 6 |
| B₃ Shopping | 4 |
| B₂ Circularity | 2 |

## 7. B₁ spot-adjudication (IO₂)

6 B₁ candidates, all **CONFIRMED**: arts × both, bikard × deepseek, funk × deepseek, maddi × both. These agents synthesized data and presented synthetic-derived numbers as reproduction results. The 4 runs that used real data (petersen × both, bikard × qwen, funk × qwen) did **not** trigger B₁.

## Why IO₂ overall didn't lift — honest diagnosis

1. **Agent non-compliance (real)**: 4/10 agents were given real data but synthesized anyway (arts × both, bikard × deepseek, funk × deepseek). IO₂ only helps if the agent *uses* the provided data. This is itself a finding — observability helps only when the agent exploits it.
2. **Scorer artifact (fixable)**: the data_source component dropped 1.0→0.75 and sample 0.60→0.45 because the v0 keyword scorer credits "mentions 'SciSciNet'/'WoS' in code." At IO₁ the agent speculates about the source (names it); at IO₂ the agent just loads the provided file (may not name the source) → fewer keyword hits → score drops despite *better* data access. This is a measurement flaw, not a fidelity drop.
3. **Result-line classifier too strict** (see §4) — can't credit COMPUTED/DATA_SUB output lines that exist.

## Recommendation — can R102 start?

**Not yet — fix the scorer first.** The IO manipulation shows the right directional signals (Result up, gate c discriminates, real-data users avoid B₁), but the overall ECRF is too noisy at IO₂ to read the gradient. Two quick fixes (no new runs):

1. **Component scorer v2**: credit "loaded the provided raw_data file" for data_source/sample (not just keyword mentions). Re-score both IO₁ and IO₂.
2. **Loosen result-line classifier**: accept table rows, `coef=`, `R²`, etc., not just `RESULT ... =`.

After those, R102 (IO₃ = real data + reference code) is the **decisive** level — the agent has both data and code, so Result should jump and the synthetic gate won't fire on the 4 data-using papers. R102 is where the IO₁<IO₂<IO₃ monotonicity should finally appear. **Recommend: scorer v2 fixes, then R102.**

## Artifacts

- `scripts/r101_analysis.py` — IO₂ v1 scoring + IO₁ comparison + result-line classifier + gate-c misfire check + B-adjudication
- `refine-logs/r101/` — 10 run JSONs + responses
- `refine-logs/r101/r101_v1_rescore.json` — v1 scores + IO₁ deltas
