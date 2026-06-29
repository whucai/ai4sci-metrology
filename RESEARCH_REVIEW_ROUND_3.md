# Round 3 — Lock the killer-case operationalization + final TODO

Converging. Two last asks.

## My operationalization of the killer panel (given your prior that M₁-exact-match is rare)

The "R₂/R₂₊ = Supported but R₃ = process-invalid" panel is defined as **process-invalid supported cases**, split into two reported strata (NOT collapsed to "wrong data, right number"):

- **Stratum S-exact**: agent's reproduced number matches the paper's reported value within tolerance (exact/numeric), AND R₃ flags a component invalid (M₁ data/sample substitution, or M₂ hard-coded output). This is the hardest, most vivid case — expected rare.
- **Stratum S-directional**: agent's reproduced *direction / sign / qualitative claim* matches the paper (e.g., "X positively predicts Y", "disruption declined"), AND R₃ flags a component invalid. Coarse/directional claims are legitimate scientific claims; reproducing the direction via the wrong process is still trust inflation. Expected more populous (your 10–25% prior).

Both strata count toward the killer. Headline metric: **P(R₂/R₂₊ = Supported | R₃ = process-invalid)**, reported overall and split by S-exact vs S-directional, with bootstrap CI and the full denominator. M₂ (hard-coded) expected to populate S-exact; M₁ (substitution) expected to populate S-directional more than S-exact.

Selection: from the full 120 runs, take ALL R₂/R₂₊-Supported-and-R₃-invalid candidates + a random sample of R₃-valid cases (recall anchor) + all M₁/M₂ automated-flagged cases. Blinded adjudication. Pre-registered case-definition rule before unblinding.

## Question 1
Is this operationalization sound? Specifically: is counting **directional/coarse claims** as legitimate "Supported" verdicts defensible, or will a reviewer say "you're watering down the killer by counting weak directional matches"? Where would you draw the line on what R₂ may call "Supported" so that R₂ is a fair (not strawman) baseline?

## Question 2
Given everything, give me the **final prioritized TODO list** in execution order, each item with: what it unblocks, compute cost, and whether it's MUST / SHOULD / NICE. Stop-the-presses items first. I want to hand this to the executor and go.

## Question 3 (optional)
One-line: is there anything left that would make you, as reviewer 2, sink the paper regardless of empirical outcomes? (A structural flaw I haven't addressed.) If not, we're done.
