# Checagens determinísticas antes e depois do render — plano

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** catch by script, before rendering, the defects the `qa-video` agent caught after 27 renders on 18/11; after rendering, measure the MP4 by script so the agent only looks at one contact sheet per video.

**Architecture:** pre-render checks join `hooks.check_picks` (same report shape, counted by `has_fails`), plus one video check in `clipper check` (scene change at the end). Post-render: new `clipper/qa.py` + `clipper qa <mp4...>` (ffmpeg filters, JSON verdict, contact sheet). `/clip-br` and the `qa-video` agent run `qa` first.

**Tech Stack:** stdlib, Pillow (already declared), ffmpeg filters `scdet`, `blackdetect`, `freezedetect`, `silencedetect`, `ebur128`.

**Spec:** user decision of 18/11 (AUDITORIA-2026-11-18.md §2–3, §7 etapa 2); QA lessons in `docs/pt-br/anatomia-do-corte.html` ("O que o QA pegou").

## Approaches

| Option | Trade-off | Pick |
| --- | --- | --- |
| Extend `check` (pre) + new `qa` command (post), our code, ideas from Editonny `verify_cut`/`quality_gate` | Small, fits `/clip-br`, no dependency | **Yes** |
| Run Editonny's `quality_gate.py` on our MP4s | Needs its project layout (`edl.json`, `project.json`), OCR, its venv | No (the full Editonny test is a separate step) |
| Keep the LLM QA only | What cost 27 renders and the tokens | No |

## Global Constraints

- Report shape unchanged for existing keys; new keys: `hook_fit`, `cut_edges`, `end_scene` (fails, counted by `has_fails`), `cut_notes` (notes).
- English profiles: same checks apply (they are language-independent); existing tests stay green.
- Thresholds: hook > 3 lines at its style = fail; start/end inside a word (word straddles the cut by > 0.08 s) = fail; scene change score ≥ 0.4 in the last 0.6 s before an end = fail; black ≥ 0.1 s, freeze ≥ 2 s, silence ≥ 1.5 s at −45 dB, integrated loudness outside −14 ± 1.5 LUFS, true peak > −1.0 dBTP, size ≠ 1080×1920, no audio = fail.

## Review Focus

1. Story cut (`segments`) from several jobs → edges checked per segment against that segment's own words.
2. A hook whose text fits only because of `*markup*` → measured after stripping markup, as rendered.
3. Clip ending exactly on the job's last frame → scene check reads within the file, no ffmpeg error.
4. MP4 with no audio stream → `qa` fails with "no audio", does not crash.
5. A pick without transcript (`--job` missing) → edge checks skipped silently, as today's `edit` notes.

---

### Task 1: hook fits the banner (pre)

- Produces: `captions.hook_lines(text: str, style: str) -> list[str]` (the wrap `render_hook` uses, without the `[:3]` cut); `render_hook` uses it. `hooks.check_hook_fit(pick) -> list[str]`.
- [ ] Test: a 60-char `bold` hook → fail naming the hook and the line count; a 20-char one → none; `render_hook` output unchanged for a short hook (pixel-equal PNG before/after the refactor).
- [ ] Implement, wire into `check_picks` (`entry["hook_fit"]`) and `has_fails`. Commit.

### Task 2: cuts on word edges (pre)

- Produces: `hooks.check_cut_edges(pick, words, load=None) -> (fails: list[str], notes: list[str])`, source-second words per segment.
- [ ] Test: start at 10.20 with word 10.00–10.50 → fail "starts inside \"palavra\""; end inside a word → fail; end 0.1 s after a word with no `.?!` and the next word 0.15 s later → note "ends mid-sentence"; clean cut → nothing; multi-job segments use `load(job)`.
- [ ] Implement, wire (`cut_edges` fails, `cut_notes` notes). Commit.

### Task 3: scene change at the end (pre, needs the video)

- Produces: `analyze.scene_cuts(video: Path, start: float, end: float) -> list[float]` (seconds of `scdet` cuts); `__main__` check adds `end_scene` when a cut falls in the last 0.6 s of the clip (or of each segment).
- [ ] Test: lavfi file switching from `color=red` to `color=blue` at 5.0 s; pick ending at 5.3 → fail; ending at 4.5 → none.
- [ ] Implement. Commit.

### Task 4: `clipper qa` (post)

- Produces: `qa.check(mp4: Path) -> dict` → `{"ok", "fails": [str], "measures": {...}, "sheet": str}`; CLI `qa FILE...` prints JSON, exits 1 if any fails; sheet `<name>.sheet.jpg` with 6 frames.
- [ ] Tests (lavfi): clean 1080×1920 clip with tone at −14 LUFS → ok; 0.5 s black inserted → fail "black"; no audio → fail "no audio"; 720p → fail size.
- [ ] Implement. Commit.

### Task 5: production flow uses it

- [ ] `.claude/commands/clip-br.md` §4–5: `check` must be clean of fails before render; after render `clipper qa` on the new MP4s; `qa-video` only for MP4s that passed, looking at the sheet. Same in `.claude/agents/qa-video.md`.
- [ ] Full suite green; `DECISOES.md`, `OPERACAO.md`. Commit.
