#!/usr/bin/env python3
"""SessionStart: a few lines of orientation, so each session starts knowing where the work stopped without
re-reading the repo. Stdout becomes context. Kept under ~25 lines on purpose (context costs tokens every session)."""
import os
import re
import shlex
import subprocess
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])


def git(*args):
    try:
        return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=5).stdout.strip()
    except (OSError, subprocess.SubprocessError):
        return ""


def section(md, title, max_lines=8):
    m = re.search(rf"^## {re.escape(title)}\s*\n(.*?)(?=^## |\Z)", md, re.M | re.S)
    lines = [ln for ln in (m.group(1).strip().splitlines() if m else []) if ln.strip()]
    return lines[:max_lines]


def use_venv():
    """On the PC the deps live in .venv (uv sync), not in system python3: put it first on PATH for this session's
    Bash commands, so `python3 -m clipper` works as the commands and docs write it. The cloud has no .venv."""
    venv, env_file = ROOT / ".venv" / "bin", os.environ.get("CLAUDE_ENV_FILE")
    if not (venv.is_dir() and env_file):
        return
    line = f'export VIRTUAL_ENV={shlex.quote(str(venv.parent))} PATH={shlex.quote(str(venv))}:"$PATH"\n'
    try:
        if line not in (Path(env_file).read_text(encoding="utf-8") if Path(env_file).exists() else ""):
            with open(env_file, "a", encoding="utf-8") as f:
                f.write(line)
    except OSError:
        pass  # orientation below still prints


def main():
    use_venv()
    out = [f"Projeto: {ROOT.name}. Branch: {git('branch', '--show-current') or '?'}."]
    changed = [ln for ln in git("status", "--porcelain").splitlines() if ln.strip()]
    if changed:
        out.append(f"Alterações não commitadas: {len(changed)} arquivo(s).")
    last = git("log", "-3", "--format=%h %s")
    if last:
        out.append("Últimos commits:\n" + "\n".join("  " + ln[:110] for ln in last.splitlines()))
    handoff = ROOT / "docs" / "contexto" / "HANDOFF.md"
    if handoff.exists():
        nxt = section(handoff.read_text(encoding="utf-8"), "Próximos passos")
        if nxt:
            out.append("Próximos passos (docs/contexto/HANDOFF.md):\n" + "\n".join("  " + ln for ln in nxt))
    if os.environ.get("CLAUDE_CODE_REMOTE") == "true":
        out.append("Sessão na nuvem: disco efêmero; ao terminar, commit só de state/ e do código "
                   "(nunca .env, jobs/, exports/).")
    print("\n".join(out))


if __name__ == "__main__":
    main()
