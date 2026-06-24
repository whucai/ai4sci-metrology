# R100 Report — Mini Study 2, IO₁ (2026-06-24)

**Design**: 5 papers × IO₁ × 2 models (qwen3-32b, deepseek-v4-pro) = 10 runs.
**Runner**: `scripts/run_v72_pilot.py` · **Image**: `sciscigpt-ds:0.1` (no-network, jail) · **Scorer**: rules-based v0 ECRF.
**Models**: qwen3-32b → qwen3.6-27b-fp8 on h100-1/2/3 (3-node LiteLLM failover); deepseek-v4-pro → DeepSeek API. R101/R102 remain blocked.

---

## 1. Run success rate — 10/10

All 10 runs: status `DONE`, container exit 0, **network blocked on all 10**, no sibling-folder leakage, LLM finish=stop. No routing/isolation/package failures.

## 2. Per-paper × per-model ECRF (v0)

| Paper | qwen3-32b | deepseek-v4-pro |
|-------|----------|-----------------|
| petersen2024 | 0.667 | 0.667 |
| arts2021 | 0.583 | 0.583 |
| funk2017 | 0.917 | 0.917 |
| maddi2024 | 0.917 | 1.000 |
| bikard2013 | 0.833 | 0.833 |

**No model differentiation at IO₁** — both models score near-identically. Expected: IO₁ is text-understanding, which both models do well. Differentiation should appear at IO₂/IO₃ (code reconstruction under real data).

## 3. Component-level score distribution (10 runs)

| Component | Mean | Pattern |
|-----------|------|---------|
| Data Source | 1.00 | always identified from text |
| Indicator | 1.00 | formula always described |
| Claim | 0.95 | conclusion nearly always stated |
| Model | 0.85 | spec mostly correct |
| Sample | 0.60 | moderate (N/window often vague) |
| **Result** | **0.35** | **LOW — 6/10 scored 0.0 (no real data)** |

## 4. IO₁ low-fidelity baseline — **partially confirmed**

- **Result component = 0.35 mean** (6/10 at 0.0) — this IS the expected low-fidelity signal: with no data, the agent cannot produce real numbers.
- **Overall ECRF = 0.79 mean** — **inflated, NOT low**. Cause: v0 scorer keyword-matches "agent mentioned the concept in code," crediting Data_Source/Indicator/Claim = 1.0 even when nothing executed. The low-fidelity signal is in Result/Sample, not the overall score.
- **Implication for R103**: Gate 1 (IO₁ < IO₃ monotonicity) cannot be judged on overall v0 ECRF — it's ceiling-inflated. Must either (a) re-weight Result/Sample, or (b) add an execution-evidence gate, before R101/R102.

## 5. Result-level vs component-level disagreement — **6/10 runs** ⚠

| Run | Indicator/Model/Claim mean | Result | Disagreement |
|-----|---------------------------|--------|--------------|
| petersen × qwen | 1.00 | 0.0 | ⚠ components OK, result failed |
| petersen × deepseek | 1.00 | 0.0 | ⚠ |
| arts × qwen | 0.67 | 0.0 | ⚠ |
| arts × deepseek | 0.83 | 0.0 | ⚠ |
| bikard × qwen | 1.00 | 0.0 | ⚠ |
| bikard × deepseek | 1.00 | 0.0 | ⚠ |
| funk × qwen | 1.00 | 0.5 | ✓ consistent |
| funk × deepseek | 1.00 | 1.0 | ✓ |
| maddi × qwen | 0.83 | 1.0 | ✓ |
| maddi × deepseek | 1.00 | 1.0 | ✓ |

**This is the theory's core pattern in miniature**: the agent understands the paper (Indicator/Model/Claim pass) and may even produce direction-correct numbers from synthetic data, but the **Result component fails** (no real data → wrong/absent numbers). A result-level evaluator would trust the run; component-level audit catches the gap. This is the trust-inflation mechanism (P3) operating at IO₁.

## 6. B₁–B₄ candidate evidence breaks (detection rules fired; need R132 adjudication)

| Break | Count | Notes |
|-------|-------|-------|
| B₂ Circularity (paper_reported hard-coded) | 7/10 | agents label paper numbers `PAPER_REPORTED` — common, mostly legitimate comparison, but flags B₂ for semantic review |
| B₄ Assertion (claim with no result support) | 6/10 | the disagreement cases: claim stated but Result=0 |
| B₃ Shopping (multiple variants/scenarios) | 5/10 | agents try several specs — needs justification check |
| B₁ Substitution (synthetic/placeholder data) | 3/10 | petersen/bikard/funk agents synthesized data to produce numbers — **the strongest break candidate** |

All are **candidates** — R132 (Layer 2 human adjudication) required to confirm. The detection rules are firing, which is the feasibility signal R103 Gate 4 needs.

## 7. Routing / isolation / leakage / scorer issues

- **Routing**: ✅ qwen3-32b via 3-node failover (h100-1/2/3), deepseek via API. No failures. (Note: can call vLLM directly via OpenAI client next time, skipping LiteLLM.)
- **Isolation**: ✅ network blocked 10/10, no sibling leakage, no lingering containers.
- **Scorer**: ⚠ **v0 ECRF over-credits** non-Result components via keyword match → overall ECRF ceiling-inflated at IO₁. Not a hard failure but blocks R103 Gate-1 interpretation. **Must fix before R101/R102.**

---

## Readiness for R101/R102

**Not yet.** Two blockers:
1. **Scorer v0 → v1**: re-weight so Result/Sample drive the overall ECRF (or add execution-evidence gate). Otherwise IO₁<IO₂<IO₃ monotonicity is untestable.
2. **B-candidate adjudication (R132 lite)**: at least spot-confirm the 3 B₁ (synthetic-substitution) candidates before scaling.

R101/R102 remain blocked per your instruction. Recommend: build ECRF v1 scorer on the existing 10 R100 outputs (no new runs needed), re-score, then decide on R101.
