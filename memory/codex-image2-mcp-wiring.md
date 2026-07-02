---
name: codex-image2-mcp-wiring
description: codex-image2 MCP bridge registered + how to drive native gpt-image-2 figure generation without session restart
metadata:
  node_type: memory
  type: reference
  originSessionId: current
---

**codex-image2 MCP = native gpt-image-2 raster generation bridge** (for paper figures). Registered + connected 2026-07-02.

**Wiring:**
- Bridge: `~/.claude/mcp-servers/codex-image2/server.py` (copied from ARIS repo `~/下载/Auto-claude-code-research-in-sleep/mcp-servers/codex-image2/server.py`). It is a stdio MCP server that wraps `codex debug app-server send-message-v2 <prompt>`.
- Registered via: `claude mcp add codex-image2 -s user -- python3 /home/caile/.claude/mcp-servers/codex-image2/server.py` → wrote to `~/.claude.json` (user scope, non-overwriting; codex + zotero MCPs untouched). `claude mcp list` shows `codex-image2 ✔ Connected`.
- Verify: `codex --version` (0.142.0), `codex features list` → `image_generation` = stable/true, `codex debug app-server send-message-v2 "ping"` responds.
- Exposed MCP tools (after a session restart): `mcp__codex-image2__generate_start`, `mcp__codex-image2__generate_status`.

**Driving WITHOUT a session restart (the trick used 2026-07-02):** the `mcp__codex-image2__*` tools only load at session start, but you can import the bridge module and call its sync fn directly:
```python
import importlib.util
spec = importlib.util.spec_from_file_location("c2", "/home/caile/.claude/mcp-servers/codex-image2/server.py")
m = importlib.util.module_from_spec(spec); spec.loader.exec_module(m)
result, err = m.run_codex_image(prompt, cwd=Path("<repo>"),
    output_path=Path("<repo>/figures/ai_generated/figure_v1.png"),  # MUST be under cwd/figures/ai_generated/
    system="...", model=None,
    reference_image_paths=["<abs path to condition sketch>"],
    timeout_sec=900, run_log_path=Path(".../step3_run.log"))
```
Caveats: (1) `output_path` MUST be under `cwd/figures/ai_generated/` (the bridge's `validate_output_path` rejects other dirs — fast fail, no gen). (2) the bridge reconfigures stdout/stdin to binary on import, so write results to a file, don't rely on print. (3) the bridge rejects shell/Python/SVG/HTML fallbacks — only native `imageGeneration` items are materialized (`nativeToolConfirmed=true`).

**Figure pipeline (paper-illustration-image2 skill, 3 steps):** (1) Codex reads paper + A/B debate → layout JSON (every element: position, text+line-breaks, colors, connects_to); (1.5) optional logo/asset library (skip for abstract diagrams); (2) Codex Python sketch from JSON (matplotlib, the condition image); (3) `run_codex_image` with sketch as `reference_image_paths` + layout brief → native raster. Helper: `python3 .aris/tools/paper_illustration_image2.py {preflight,finalize,verify}`.

**Artifacts (2026-07-02 run):** refine-logs/figures/fig1_layout.json + fig1_sketch.png (steps 1-2) → figures/ai_generated/figure_v1.png + figure_final.png + latex_include.tex + verify.json (step 3, native, 96s, imageCount=2). Pipeline doc: refine-logs/figures/FIGURE_PIPELINE.md.

To remove the MCP: `claude mcp remove codex-image2 -s user`.

Related: [[study2-euc-mechanism-2026-07-02]], [[git-sync-policy]]
