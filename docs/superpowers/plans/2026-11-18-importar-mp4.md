# Importar MP4 local — plano de implementação

> **For agentic workers:** REQUIRED SUB-SKILL: Use subagent-driven-development (recommended) or executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** `python -m clipper --profile gta-br import <arquivo> ...` turns a local video into 30-min `live-vod-*` jobs, resumable, without touching the original.

**Architecture:** new module `clipper/imports.py` (identity, authorization, split, import orchestration); one `import` subcommand in `clipper/__main__.py`; state in `state/imports.json` via `clipper/state.py`; job layout identical to `vods.make_job`.

**Tech Stack:** Python 3.12 stdlib, ffmpeg/ffprobe via subprocess, pyyaml (already declared), unittest.

**Spec:** `docs/superpowers/specs/2026-11-18-importar-mp4-design.md`

## Global Constraints

- No new dependency. Network not used. Tests: unittest, media from `ffmpeg -f lavfi`, `CLIPPER_STATE_DIR` + patched `JOBS`.
- Original file opened read-only; never moved, renamed or rewritten.
- Job id: `live-vod-{slug(streamer)}-{vod}-{int(offset):06d}`; `slug` from `clipper.live`.
- A/V thresholds: start diff > 0.1 s or end diff > 0.5 s → `av.ok = false`.
- Authorization statuses: `autorizado`, `pendente`, `negado`; missing → `pendente`.
- English behaviour and other profiles unchanged; full suite stays green.
- Work only in the worktree `/home/gustavo/Projetos/clipping-gta-6-dev`, its own `.venv`.

## Review Focus

1. Re-running after a crash in the middle of moving blocks → no duplicate job, missing blocks created. (Task 3 test `test_resume_after_partial_move`)
2. Re-running a completed import → nothing new, returns `already_imported`. (Task 3)
3. Same file under another path/name → recognised by SHA-256, not re-imported. (Task 3)
4. `--from` beyond the duration → clear error, no staging left behind. (Task 3)
5. Source with audio missing → blocks still created, `av.ok` false with reason `no audio`. (Task 2)

---

### Task 1: identity and authorization

**Files:** Create `clipper/imports.py`, `profiles/gta-br/authorizations.yaml`; Test `tests/test_ptbr.py` (class `ImportTests`).

**Interfaces — Produces:**
- `fingerprint(path: Path) -> dict` → `{"sha256": str, "size": int, "duration": float, "start_time": float}`; cached in state `imports["fingerprints"]["<abs path>|<size>|<mtime_ns>"] = sha256`.
- `authorization(streamer: str, profile: str | None = None) -> dict` → `{"status", "evidence", "date"}` read from `config.profile_file("authorizations.yaml")` by `slug(streamer)`.

- [ ] Test `test_fingerprint_is_full_sha256_and_cached`: sha equals `hashlib.sha256(file bytes)`; second call with `hashlib.sha256` patched to raise still returns the same dict (cache hit); touching the file (new mtime) recomputes.
- [ ] Test `test_authorization_is_separate_from_live_yaml`: streamer absent → `pendente`; entry `{status: autorizado, evidencia: x, data: y}` → returned; `live.yaml` not read (patch `live.load_streams` to raise).
- [ ] Run: `.venv/bin/python -m unittest tests.test_ptbr.ImportTests -v` → FAIL (module missing).
- [ ] Implement both (sha in 8 MB reads; state key `"imports"`).
- [ ] Run → PASS. Commit.

### Task 2: split and A/V check

**Interfaces — Produces:**
- `av_check(path: Path) -> dict` → `{"ok": bool, "video": [start, end], "audio": [start, end], "reason": str}`.
- `split(src: Path, staging: Path, chunk_s: int, from_s: float, duration: float) -> list[dict]` → `[{"file": Path, "start": float, "end": float}]`, source-timeline seconds, blocks before `from_s` dropped. Writes marker `staging/"segmented"` only after ffmpeg exits 0; if the marker exists, re-reads `list.csv` without running ffmpeg.

- [ ] Test `test_split_uses_real_cut_times`: lavfi 50 s, GOP 2 s, chunk 12, from 7 → starts within 2 s after 7, 19, 31, 43; contiguous (`end[i] == start[i+1]`); every `av_check(...)["ok"]`.
- [ ] Test `test_split_reuses_finished_staging`: second call with `subprocess.run` patched to raise returns the same list.
- [ ] Test `test_av_check_flags_missing_audio`: video-only lavfi file → `ok` False, `reason == "no audio"`.
- [ ] Run → FAIL. Implement (ffmpeg `-map 0:v:0 -map 0:a:0? -c copy -f segment -segment_times ... -segment_format mp4 -reset_timestamps 1 -segment_list list.csv`; offsets minus source `start_time`). Run → PASS. Commit.

### Task 3: import orchestration, CLI, docs

**Interfaces — Consumes:** Tasks 1–2. **Produces:** `import_file(path, streamer, url, started_at=None, vod=None, from_s=0.0, chunk_minutes=30, cfg=None, analyze=True) -> dict` → `{"imported": [job ids], "skipped": [job ids], "warnings": [str], "already_imported": bool, "sha256": str}`; CLI `import`.

`job.json`: `id, url, title, channel, duration, offset, live: true, vod, recorded_at, profile, source_file, source_sha256, av, authorization`; plus `source.info.json` and `live_ready` (as `vods.make_job`). State `imports[sha256] = {file, size, duration, streamer, vod, from, chunk, blocks: {"<offset6>": job_id}, complete}`.

- [ ] Test `test_import_creates_jobs_and_preserves_original`: 50 s file, chunk minutes patched small via `chunk_s` → jobs exist with `live_ready`, offsets match split, `recorded_at = started_at + offset`, `authorization.status == "pendente"`, original sha and path unchanged, staging dir removed.
- [ ] Test `test_reimport_and_renamed_copy_are_skipped`: second call and a call on a copy under another name → `already_imported` True, no new jobs.
- [ ] Test `test_resume_after_partial_move`: make `os.replace` fail on the 2nd block → error; rerun → all blocks present once, state complete.
- [ ] Test `test_from_beyond_duration_is_an_error`: raises `SystemExit`, no `.import-*` dir left.
- [ ] Run → FAIL. Implement; wire `import` subcommand (`file`, `--streamer` required, `--url`, `--started-at` ISO, `--vod`, `--from` seconds, `--chunk-minutes`, `--no-analyze`), print JSON like `vods`.
- [ ] Full suite: `.venv/bin/python -m unittest discover -s tests` → OK.
- [ ] Real check (not a test): import a 2–3 min lavfi file through the CLI in the worktree; `ffprobe` one block.
- [ ] Docs: `docs/pt-br/OPERACAO.md` (command), `DECISOES.md` (decisions 21–23), `AGENTS.md` mention; commit.
