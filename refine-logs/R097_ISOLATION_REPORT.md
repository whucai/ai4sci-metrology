# Phase-0 Completion Report — R095–R099 (2026-06-24)

**Status**: R095/R096/R097/R099 complete and approved; R098 draft complete, pending adjudication. **R100–R102 NOT launched** — awaiting user decision.

---

## Final IO package feasibility table (R096 + R098 combined)

| Paper | Stratum | Task | Domain | IO₁ | IO₂ | IO₃ | Constructability | Boundary? |
|-------|---------|------|--------|-----|-----|-----|-------------------|-----------|
| Petersen2024 | Low | STRICT | SoS | ✓ | ✓ | ✓ (SciSciNet + R002 reproduce.py) | Clean | No |
| Arts2021 | Medium | METHOD | IS/Innov | ✓ | ✓ | ✓ (USPTO + R003 ref code) | Clean | No |
| **funk2017** | Med-High | STRICT | Mgmt | ✓ | ✓ | ✓ (**Dataverse + cdindex.info code**) | **Cleanest IO₃** | No |
| maddi2024 | Medium | STRICT-DS | SoS | ✓ | ✓ | ⚠️ (WoS ok; Publons drift) | Partial IO₃ | Soft |
| bikard2013 | High | DATA-SUB | Mgmt | ✓ | ✓ | ✗ (no code/data) | **IO₃→IO₂ collapse** | **Yes (by design)** |

**Conclusion**: 3 clean IO₃, 1 partial, 1 boundary — exactly the design intent (only 1 boundary case). The IO gradient (IO₁<IO₂<IO₃) is testable on 4 papers with constructable IO₃; bikard2013 is the diagnostic boundary case.

---

## R097 isolation test results — 7/7 gates PASS

**Approach**: Docker container, `--network none`, `--user uid:gid`, `--read-only` rootfs, tmpfs `/tmp`, only the per-run workdir bind-mounted rw. Model/control plane (LLM that *generates* code) runs **outside** the container; only *execution* is isolated. No home dirs, caches, benchmark pool, or cross-condition artifacts mounted. (`src/sciscigpt_local/isolated_executor.py`, test: `scripts/test_r097_isolation.py`)

| Gate | Property | Result |
|------|----------|--------|
| G-A | Network egress blocked | PASS — socket to 1.1.1.1:53 → OSError |
| G-E | Container exec succeeded | PASS — exit 0 |
| G-B | Host home unreachable | PASS — `/home/*` glob = [] |
| G-C | Sibling IO folder unreachable | PASS — `sibling_exists=False` |
| G-D | Workspace writable | PASS — wrote/`_wtest.txt` |
| G-F1 | Basic numeric exec | PASS — `1+1=2` |
| G-F2 | No lingering container | PASS — `docker ps` empty after run |

**Fix applied during testing**: `tempfile.mkdtemp` creates `0700` workdirs; container run as host uid with `--cap-drop=ALL` (no `DAC_OVERRIDE`) couldn't traverse it → "Permission denied". Resolved by `chmod 0755` workdir + `--user uid:gid`. This is the standard bind-mount pattern and is now in the executor.

**Implication**: anti-claim A4 (prompt-engineering / harness-leakage artifact) is now physically blocked at execution time. The IO₁ "no web" condition is enforced, not just promised.

---

## R098 gold-chain status

`refine-logs/GOLD_CHAIN_R098.md` — all 5 papers, 9 fields each, filled:
- **Petersen2024 / Arts2021**: reused from C0 (R002/R003), consistency-checked against v7.2 template — all 9 fields map.
- **funk2017 / maddi2024 / bikard2013**: read this pass; fields 1–9 filled with quoted line numbers.

**Pending adjudication** (6 numeric details, none block the IO design):
- funk2017: exact N (Table 1)
- maddi2024: time window + regression coefficients
- bikard2013: fixed-effects coefficients

**Tool for adjudication**: MinerU on the source PDFs — gives cleaner extraction than the current `.md` files for pinning exact table values. (`minerU` recommended by user 2026-06-24.)

---

## Decision gate before R100–R102

R095–R099 are complete to the draft/adjudication level. The IO manipulation is now physically enforceable (R097) and the pilot set is clean (R099/R098). Remaining before launch:

1. **Adjudication pass on R098** — confirm 6 numeric details via MinerU (can run in parallel with R100 prep, does not block the IO gradient itself).
2. **Build the data-science Docker image** for R100 (`python:3.11-slim` proves isolation; real runs need numpy/pandas/statsmodels/scikit-learn + the cdindex code for funk2017, USPTO loader for Arts2021, etc.).
3. **User greenlight** to launch R100–R102.

**My recommendation**: proceed to (1) and (2) now; launch R100–R102 once the data-science image is built and you confirm. The highest-risk assumption (IO₂ cleanly isolates docs from code) is now testable on a clean pilot set under enforced isolation.
