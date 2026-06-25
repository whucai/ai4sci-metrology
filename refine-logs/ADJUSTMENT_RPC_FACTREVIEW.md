# Idea Adjustment Memo: Integrating RPC-Bench & FactReview

**Date:** 2026-06-25
**Basis:** RPC-Bench (arXiv:2601.14289, 2026-04-30) + FactReview (arXiv:2604.04074, 2026-05-27)
**Affects:** v7.2 (UTD) and v8 (Scientometrics) framings; novelty section, Study 3 design, positioning

---

## 1. Threat Assessment

### RPC-Bench — LOW threat, use as motivation
- 15K human-verified QA pairs from review–rebuttal exchanges of CS papers; taxonomy of 9 categories across Concept/Method/Experiment/Claim-Verification.
- **Comprehension only.** No code execution, no reproduction, no IO manipulation, no component decomposition, no fidelity metric.
- GPT-5 only 37.46% Informativeness. → Use this number as motivation: "even frontier models cannot precisely understand papers, let alone verify their computational claims — motivating a reconstruction-level instrument."
- No structural overlap with ECRF. Cite as the *comprehension ceiling* that ECRF must clear.

### FactReview — HIGH threat, closest prior work
What it already does (overlaps ECRF):
- Extracts claims (empirical/methodological/theoretical) from manuscript.
- Three evidence sources: manuscript (MinerU) + related work (Semantic Scholar + RefCopilot) + **code execution** (Docker, Run-Review-Fix loop, K=3 wrapper-only repairs).
- 4 claim statuses: Supported / Partially-supported / In-conflict / Inconclusive.
- 35 ML papers, 463 benchmark major claims, 84.4% coverage.
- **Removing execution evidence changes 17% of claim statuses** — larger than any other single source.
- Evidence-aware rubric, reviews 4.86/5; reviewer time −58%, coverage 87%→99%.
- Explicitly: "LLM reviewers should audit empirical claims, not make accept-reject decisions."

**Implication:** The v8 novelty claim ("no prior work combines agent-reproduces-paper + evidence-chain-component-fidelity + reproduction-as-measurement-instrument") is **now partially breached** — FactReview does (a) agent executes paper code + (partial b) claim-level verification. Must re-derive novelty against FactReview explicitly.

---

## 2. Re-derived Novelty (4 defensible differentiators)

The contribution must be **structural, not "deeper"**. Four axes where ECRF differs from FactReview:

| Axis | FactReview (claim-level) | ECRF (component-level) |
|------|--------------------------|------------------------|
| **D1 Unit of analysis** | The *claim* (Supported/Partial/Conflict/Inconclusive) | The **evidence-chain component** (Data→Sample→Indicator→Model→Result→Claim), per-component fidelity |
| **D2 IO as causal variable** | Code availability = **binary**; ablation is *post-hoc removal* (observational) | IO = **3-level manipulated treatment** (IO₁ narrative / IO₂ structured-docs-no-code / IO₃ executable); causal identification |
| **D3 Trust inflation** | No concept; "Partial" flags overbroad scope only | **Primary DV**: gap between result-level verdict and component-level verdict (RIB / FRR) |
| **D4 Scientometric link** | None | **Study 4**: correlate ECRF with citations, CD-disruption, altmetrics, team size — a field instrument |

Plus **B₁–B₄ structural break taxonomy** (Substitution / Circularity / Shopping / Assertion) vs FactReview's *pipeline* failures (env/runtime/metric/alignment). FactReview executes *released* code, so it structurally cannot detect B₁ (agent substitutes data/sample) — its agent never chooses data. ECRF's reproduction-from-paper setting *is* where B₁ lives.

**Key reframing:** FactReview's 17%-status-change ablation is **correlational** (remove a source, watch verdicts move). ECRF's IO manipulation is **causal** (randomized IO levels → measured per-component fidelity). The 17% number *supports* the ECRF premise (evidence regime changes conclusions) and ECRF generalizes it from "binary code on/off" to "a 3-level causal IO ladder with component-resolved effects."

---

## 3. Reposition: FactReview as Baseline, not Competitor

The strongest move: **turn the closest competitor into a baseline in Study 3.**

Study 3 originally has 3 regimes (R₁ result-level / R₂ aggregate / R₃ component audit). ReSpecify:
- **R₁** = result-only reproduction verdict (binary "did the numbers match").
- **R₂** = **FactReview-style claim-level execution audit** (manuscript + lit + code execution, claim verdicts). *This is the strong baseline.*
- **R₃** = ECRF component-level audit (decompose each claim into 6 components, score per-component fidelity, detect B₁–B₄).

Hypotheses become:
- **H3 (trust inflation):** TIR(R₁) > 0 — result-level verdicts inflate trust.
- **H4 (audit correction):** TIR(R₂) > TIR(R₃) — *even execution-based claim audit (FactReview-style) inflates trust relative to component audit.* This is the killer claim: it shows FactReview's own paradigm has a measurable blind spot that ECRF closes.

**Killer empirical result to pursue:** find papers where FactReview would label a claim "Supported" (numbers reproduce) but ECRF's component audit reveals B₁ (data/sample substitution: agent hit similar numbers via a different data path) or B₂ (paper values hard-coded as outputs). These are *trust-inflation cases invisible to FactReview by construction*. Even N=3–5 such cases, adjudicated by humans, constitute the decisive demonstration.

---

## 4. Concrete Study Adjustments

### Study 1 (construct validation) — unchanged
ECRF dimensionality via M0/M1 re-analysis. Add: contrast ECRF component scores vs FactReview claim verdicts on the same papers to validate that component-level scores carry information claim-level verdicts do not.

### Study 2 (IO → ECRF causal test) — sharpen vs FactReview
- Keep 20 papers × 3 IO × 2 models = 120 runs.
- **New framing:** "FactReview can only ablate evidence sources post-hoc; we causally manipulate IO levels." The IO₃ cell *includes* executable code (FactReview's regime); IO₁/IO₂ are regimes FactReview cannot study because it has no IO variable. This is methodologically prior to FactReview.
- Add a FactReview-style claim-verdict pass on IO₃ runs as a within-study baseline: show that claim-level verdicts (FactReview-style) and component-level scores (ECRF) disagree on a measurable subset → that disagreement *is* the trust-inflation signal.

### Study 3 (MAIN: trust inflation + audit correction) — reSpecified as above
- R₂ becomes the FactReview-style baseline (not a strawman — implement the actual manuscript+lit+execution+claim-verdict pipeline).
- Primary result: TIR(R₂) > TIR(R₃), with human-adjudicated B₁–B₄ cases that are invisible at R₂.
- 4 evidence break types require 3-layer evidence (automated rule → audit trace → human adjudication) — unchanged.

### Study 4 (scientometric capstone, v8) — unchanged in design, strengthened by FactReview's absence
No prior execution-audit work (incl. FactReview) links verification outcomes to scientometric impact. Study 4 remains the field-facing contribution only ECRF can do.

---

## 5. Positioning Paragraph (drop-in for Related Work / Intro)

> Closest prior work is FactReview (Yue et al., 2026), which executes released code under a bounded repair budget to assign claim-level verdicts (Supported / Partially-supported / In-conflict / Inconclusive) and shows that removing execution evidence changes 17% of verdicts. We build on this premise but make three structural moves FactReview cannot: (i) we shift the unit of analysis from the *claim* to the *evidence-chain component* (Data→Sample→Indicator→Model→Result→Claim), yielding a per-component fidelity score that localizes *where* reconstruction breaks; (ii) we treat information observability not as a binary code-availability flag but as a three-level causal treatment (narrative / structured-docs / executable), enabling causal identification of the observability–fidelity relationship; and (iii) we introduce trust inflation — the gap between result-level and component-level validity — as the primary dependent variable, and show that even execution-based claim audit (FactReview-style) inflates trust relative to component audit. RPC-Bench (Chen et al., 2026) establishes the comprehension ceiling (GPT-5 37.46% Informativeness) that motivates a reconstruction-level instrument. Unlike both, ECRF is positioned not as a reviewing tool but as a **measurement instrument** producing a new scientometric variable — execution-level reproducibility fidelity — correlated with citations, disruption, and team size (Study 4).

---

## 6. Action Items

- [ ] Ingest RPC-Bench + FactReview into research-wiki; add `contradicts`/`addresses_gap` edges from both to ECRF node. Re-run novelty assertion with both included.
- [ ] Update `idea-stage/IDEA_REPORT.md` (v8 on `worktree-scientometrics-pivot`) §Related Work + §Novelty with the 4-differentiator table.
- [ ] Update `refine-logs/FINAL_PROPOSAL.md` (v8) §Study 3: reSpecify R₂ as FactReview-style baseline; add H4 restatement.
- [ ] Update `refine-logs/EXPERIMENT_PLAN.md` (v8) Block for Study 3: add FactReview-style claim-verdict pipeline as R₂ implementation.
- [ ] Add a memory note: "FactReview is the closest prior work; novelty now rests on D1–D4, not on 'no prior execution audit'."
- [ ] Decision needed: apply adjustment to v7.2 (UTD, on dev/master) or v8 (Scientometrics, on worktree-scientometrics-pivot) or both.
