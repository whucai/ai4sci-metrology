# Refine-Logs Manifest (2026-06-24)

## Experiment planning (v7.2 Evidence-Chain Theory)
- EXPERIMENT_PLAN.md — claim-driven plan (anti-claims, simplicity/frontier checks, 3 studies)
- EXPERIMENT_PLAN_20260624.md — timestamped source
- EXPERIMENT_TRACKER.md — C0/S1/P1/S2/S3/R milestones; MUST=32 (8 done + 24 TODO); R097 gap-found
- PILOT_PAPERS.md — rev2 Top-5 (Petersen/Arts/funk2017/maddi/bikard) + 6 backups
- PRE_RUN_VALIDATION.md — R095 codebook, R096 IO package, R097 isolation gap+fix, R098 gold-chain template
- FINAL_PROPOSAL.md — v7.1 proposal

## Phase-0 pre-run products (2026-06-24)
- PRE_RUN_VALIDATION.md — R095 codebook, R096 IO package, R097 spec, R098 template
- GOLD_CHAIN_R098.md — 5-paper gold-chain draft (9 fields each)
- R097_ISOLATION_REPORT.md — 7/7 gates PASS, final IO feasibility table
- src/sciscigpt_local/isolated_executor.py — container --network none executor
- scripts/test_r097_isolation.py — isolation gate test

## R097b + R098 completion (2026-06-24)
- docker/sciscigpt-ds/Dockerfile + requirements.txt — sciscigpt-ds:0.1 (digest 2ec5ab91...)
- docker/sciscigpt-ds/build.log
- R098_ADJUDICATION.md — MinerU adjudication of 6 numeric details
- R097b_R098_FINAL_REPORT.md — final image test + IO feasibility + gold-chain changes + R100 readiness
- MinerU outputs: /tmp/mineru_out/{funk2017,maddi2024,bikard2013}

## R100 (mini Study 2 IO1) — 2026-06-24
- scripts/run_v72_pilot.py — v7.2 runner (IO1 prompt -> isolated exec -> ECRF v0 score)
- refine-logs/r100/ — 10 run JSONs + LLM responses
- R100_REPORT.md — 7-point report; 10/10 success, 6/10 result-vs-component disagreement, B-candidates, scorer caveat

## R100b (ECRF v1 rescoring, no new runs) — 2026-06-24
- scripts/ecrf_v1_scorer.py — v1 weights + 5 execution-evidence gates + refined B2 + R132-lite B1
- refine-logs/r100/r100b_v1_rescore.json — v0/v1 comparison
- R100B_REPORT.md — v0=0.792 -> v1=0.490 (IO1 now LOW); 3/3 B1 CONFIRMED; R101 may start

## R101 (mini Study 2 IO2) — 2026-06-24
- scripts/run_v72_pilot.py — extended for IO2 (docs+raw_data into workdir, IO2 prompt)
- scripts/r101_analysis.py — IO2 v1 scoring + IO1 comparison + result-line classifier
- refine-logs/r101/ — 10 IO2 run JSONs + responses + r101_v1_rescore.json
- R101_REPORT.md — 10/10 isolated; overall 0.483 (flat vs IO1); Result UP; gate-c no misfire; scorer fixes needed before R102
