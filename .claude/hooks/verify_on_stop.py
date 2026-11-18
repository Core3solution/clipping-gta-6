#!/usr/bin/env python3
"""Stop hook: when Python files changed since the last green run, run the test suite before Claude ends its turn.
On failure, exit 2 sends the failing tests back to Claude to fix (once: `stop_hook_active` prevents loops).

Cheap by design: skipped when no .py file changed, and the last green state is remembered in .git/, so an unchanged
tree never re-runs. Set CLIPPER_SKIP_VERIFY=1 to turn it off for a session (e.g. a production run in the cloud)."""
import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

ROOT = Path(os.environ.get("CLAUDE_PROJECT_DIR") or Path(__file__).resolve().parents[2])
MARK = ROOT / ".git" / "claude-verified"


def git(*args):
    return subprocess.run(["git", "-C", str(ROOT), *args], capture_output=True, text=True, timeout=10).stdout


def main():
    try:
        event = json.loads(sys.stdin.read() or "{}")
    except ValueError:
        event = {}
    if event.get("stop_hook_active") or os.environ.get("CLIPPER_SKIP_VERIFY") == "1" or not (ROOT / ".git").is_dir():
        return
    py = sorted(ln[3:] for ln in git("status", "--porcelain").splitlines() if ln[3:].endswith(".py"))
    if not py:
        return
    digest = hashlib.sha1((git("diff", "HEAD", "--", *py) + "".join(py)).encode()).hexdigest()
    if MARK.exists() and MARK.read_text().strip() == digest:
        return
    venv_py = ROOT / ".venv" / "bin" / "python"  # PC: deps in .venv (uv sync); cloud: system python3
    py_exe = str(venv_py) if venv_py.exists() else sys.executable
    res = subprocess.run([py_exe, "-m", "unittest", "discover", "-s", "tests"], cwd=ROOT,
                         capture_output=True, text=True, timeout=900)
    if res.returncode == 0:
        MARK.write_text(digest)
        return
    tail = "\n".join(res.stderr.strip().splitlines()[-40:])
    print(f"verify_on_stop: a suíte de testes falhou depois das mudanças em {', '.join(py[:6])}. "
          f"Corrija antes de encerrar (ou explique por que a falha não é sua):\n{tail}", file=sys.stderr)
    sys.exit(2)


if __name__ == "__main__":
    main()
