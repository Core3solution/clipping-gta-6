# AGENTS.md

Python clipper for GTA 6 shorts (`clipper/`); see README.md for the commands and what each one does.

## Commands
- Install: `uv sync` (Python deps from `pyproject.toml` / `uv.lock`); system tools (ffmpeg, yt-dlp, whisper.cpp, demucs): `uv run python -m clipper setup --install`
- Test: `uv run python -m unittest discover -s tests`
- Build/lint: none configured

## Rules
- CI lives in `.github/workflows/ci.yml` and must stay green.
- Never commit with `--no-verify`.
- Never commit `.env`, `jobs/`, `exports/` or `logs/` (secrets and large media; already in `.gitignore`).

## Operação GTA 6 Brasil (branch ptbr-operacao-lancamento)
- Profile `gta-br` (`--profile gta-br` or `CLIPPER_PROFILE=gta-br`); the production command is `/clip-br` (`.claude/commands/clip-br.md`).
- Docs for the operator are in Portuguese in `docs/pt-br/` (start at `docs/pt-br/README.md`; decisions and what is tested vs not in `docs/pt-br/DECISOES.md`).
- New modules: `clipper/telegram.py` (delivery/approval), `clipper/vods.py` (VOD chunks), `clipper/state.py` (state/ JSON). Tests: `tests/test_ptbr.py`.
- Never publish to a social network; never commit `.env`, `jobs/`, `exports/`. Secrets only via env/.env (TELEGRAM_BOT_TOKEN, TELEGRAM_CHAT_ID).
- Keep changes minimal and additive: English behaviour and the original profiles must stay unchanged (the full suite must stay green).
