#!/usr/bin/env python3
"""SessionStart: a few lines of orientation, so each session starts knowing where the work stopped without
re-reading the repo. Stdout becomes context. Kept under ~25 lines on purpose (context costs tokens every session)."""
import os
import re
import shlex
import subprocess
import sys
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


def bash_path(p):
    """C:\\x\\y -> /c/x/y: Git Bash splits PATH on ':', so a Windows drive path would break it."""
    s = str(p).replace("\\", "/")
    return f"/{s[0].lower()}{s[2:]}" if re.match(r"^[A-Za-z]:/", s) else s


def use_venv():
    """On the PC the deps live in .venv (uv sync), not in system python3: put it first on PATH for this session's
    Bash commands, so `python3 -m clipper` works as the commands and docs write it. The cloud has no .venv.
    Windows venvs have Scripts/python.exe and no python3 (python3 is the Store stub), hence the function."""
    win = os.name == "nt"
    venv, env_file = ROOT / ".venv" / ("Scripts" if win else "bin"), os.environ.get("CLAUDE_ENV_FILE")
    if not (venv.is_dir() and env_file):
        return
    line = f'export VIRTUAL_ENV={shlex.quote(str(venv.parent))} PATH={shlex.quote(bash_path(venv))}:"$PATH"\n'
    if win:
        line = line[:-1] + '; python3() { python "$@"; }\n'
    try:
        if line not in (Path(env_file).read_text(encoding="utf-8") if Path(env_file).exists() else ""):
            with open(env_file, "a", encoding="utf-8") as f:
                f.write(line)
    except OSError:
        pass  # orientation below still prints


def main():
    sys.stdout.reconfigure(encoding="utf-8")  # Windows consoles default to cp1252, which has no "→"
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
