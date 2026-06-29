# Round 2 — Revised design responding to Round 1

Thank you. The "different object" critique is correct and decisive; I accept it and the R₂₊ point. Below is the revised design. Please judge whether it rescues the contribution and then deliver the two follow-ups at the end.

## Accepted fixes

### A. Same-object regimes (fixes the baseline-alignment flaw)
All regimes now score the **same agent reproduction trace** (the agent's own code, data the agent chose, outputs it produced) at a given IO level:
- **R₁** = result-level: do the agent's reproduced numbers match the paper's reported numbers (within tolerance)?
- **R₂** = FactReview-style claim-level audit applied to the **agent's trace** (claim extraction → literature grounding → execute the agent's code under K=3 wrapper repair → 4-status verdict), with **no component-provenance scoring**.
- **R₂₊** = R₂ + two bolt-on checks reviewers would call trivial: (i) data/sample provenance check (did the agent use the paper's data file / sample spec?), (ii) hard-coded-paper-number scanner (M₂). This is the "FactReview extended by 2 checks" baseline.
- **R₃** = ECRF component-level audit of the **same trace**: decompose each claim into Data→Sample→Indicator→Model→Result→Claim, score each component's reconstruction fidelity, task-contingent pass.
- **Prior-art calibration cell (separate)**: original FactReview on the released repo, reported as "how the published system behaves on these papers," NOT as a head-to-head baseline against R₃. (This is what the 35-paper calibration reproduces.)

Killer claim becomes: **R₂="Supported" (agent's numbers match + claim well-formed) but R₃=M₁/M₂ (agent substituted data / hard-coded outputs) — on the same trace.** Now both audit the agent's reconstruction, so the contrast is fair: R₂ says "result valid," R₃ says "process invalid." That IS trust inflation.

### B. R₂₊ and the D1 fallback (pre-registered)
Hypothesis: FRR(R₂) > FRR(R₂₊) > FRR(R₃).
- If R₃ beats R₂₊ on FRR → D1 (component unit) stands.
- If R₂₊ ≈ R₃ (the two bolt-on checks catch most M₁/M₂) → D1's FRR advantage collapses; we reframe D1's contribution as **the continuous per-component fidelity score** that enables (a) Study 2's Component×IO sensitivity (R₂₊ produces binary flags, not per-component scores) and (b) Study 4's scientometric correlation (needs a continuous variable). R₃ then wins not on FRR but on being a *measurement instrument* rather than a *detector*. Pre-registered fallback.

### C. Killer experiment hardened
- Report the full denominator: all R₂="Supported" cases, all R₃-invalid cases, all M₁/M₂ candidates, and a random sample of unflagged cases (recall estimation).
- Two adjudicators **blinded to hypothesis and to R₂/R₃ labels**; resolve by discussion; record agreement.
- Target 5–8 confirmed cases across ≥2 papers and ≥2 modes; report **rate + bootstrap CI**, not just "≥3 examples."
- Pre-register the case-definition rule before unblinding.

### D. Study 2 causality — wording downgraded
Reframed as a **controlled input-sensitivity intervention**. Causal language limited to "the within-paper randomized artifact package changes agent behavior under this harness." No claim that "observability determines reproducibility" in the wild. The Component×IO interaction is the mechanism evidence, not a population causal effect.

### E. Study 4 — demoted to exploratory ecological validation
Moved to appendix for NeurIPS/ICML; a modest exploratory study for Scientometrics. Claim licensed: "ECRF is associated with impact indicators," NOT "reproducibility predicts impact." All confounds (selection, fame, data-availability, age, team resources, venue, openness) stated. No GPU spent on Study 4 until Studies 2–3 land.

### F. Reliability gates before main claims
Freeze R121 Layer-1 gold chains (20/20, 2 annotators, α gate per component, adjudication log) BEFORE full Study 2. Report inter-annotator reliability **by component**. Add one repeat seed on 6 stratified papers (36 runs) for ICC/metric stability. Frontier subset 6×3×2 = 36 runs.

## Push-back / questions for you

1. **Does the same-object fix + R₂₊ + fallback rescue the contribution to the 7/10 path?** Or is there a remaining structural flaw you'd still attack?
2. **Is the D1 fallback (continuous per-component score enabling Study 2 + 4, vs R₂₊'s binary flags) a defensible contribution if FRR(R₂₊)≈FRR(R₃)?** Or would you still call that incremental over R₂₊?
3. The killer argument now hinges on: the agent, reconstructing from the paper (IO₁/IO₂, no released code), substitutes data and coincidentally hits the number. **Is this realistic in 120 runs, or will agents that substitute data rarely produce matching numbers** (making M₁ cases rare and the killer hard to populate)? This is an empirical-risk question — your prior on how often M₁ produces coincidentally-correct numbers?
4. **Minimal paper outline** (sections + figure plan) for the revised design, NeurIPS D&B frame.
5. **Revised results-to-claims matrix** that includes R₂₊ as a column (S2 IO × S3 FRR ladder incl. R₂₊ × S4).

Please be specific.
