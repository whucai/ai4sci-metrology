# Figure 1 Pipeline — codex-image2 native raster (toolchain wiring)

**Date**: 2026-07-02

## Status
- ✅ Step 1 — Codex (gpt-5.5) read R125 reports + multi-agent A/B debate → layout JSON (`fig1_layout.json`).
- ✅ Step 1.5 — no logo/asset library (abstract mechanism diagram).
- ✅ Step 2 — Codex Python sketch from JSON → `fig1_sketch.png` (the condition image).
- ✅ Toolchain — `codex-image2` MCP **registered + connected** (user scope).
- ⏳ Step 3 — native gpt-image-2 raster generation: **requires session restart** to load `mcp__codex-image2__generate_start` / `generate_status`, then run with `fig1_sketch.png` + `fig1_layout.json` as condition.

## Toolchain verification (2026-07-02)
- `codex` CLI: `/home/caile/.nvm/versions/node/v20.14.0/bin/codex`, version `codex-cli 0.142.0`.
- `codex features list`: `image_generation` = **stable / true** (native image gen available).
- `codex debug app-server send-message-v2 "ping"`: responds (app-server path live).
- Bridge installed: `~/.claude/mcp-servers/codex-image2/server.py` (from ARIS repo `mcp-servers/codex-image2/server.py`).
- Registered via: `claude mcp add codex-image2 -s user -- python3 /home/caile/.claude/mcp-servers/codex-image2/server.py` → written to `~/.claude.json` (user config; non-overwriting — `codex` and `zotero` MCPs untouched).
- `claude mcp list`: `codex-image2 … ✔ Connected`.
- Exposed tools (after restart): `mcp__codex-image2__generate_start`, `mcp__codex-image2__generate_status`.

## Step 3 plan (after session restart)
Call `mcp__codex-image2__generate_start` with:
- `prompt`: a text brief referencing the layout JSON (IO→uptake→ECRF mechanism, 3 columns, gate bar, 3 counterexample callouts) + instruction "use the provided sketch as the visual condition; preserve the layout, colors, and labels; render as a clean publication figure".
- `cwd`: `/mnt/mydisk/PycharmProjects/ai4sci-metrology`
- `outputPath`: `figures/ai_generated/figure_v1.png`
- attach `fig1_sketch.png` as the condition image + `fig1_layout.json` as the layout spec.
Then poll `mcp__codex-image2__generate_status` until `done=true`. The bridge rejects shell/Python fallbacks — only native `imageGeneration` output is accepted.

## To remove the server (if ever needed)
`claude mcp remove codex-image2 -s user`
