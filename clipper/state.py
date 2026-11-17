"""Small JSON state that must survive between runs: which VOD seconds were already clipped, which MP4s went to
Telegram, the reviewer's approvals and links sent from the phone.

It lives in `state/` at the repo root (or $CLIPPER_STATE_DIR). Locally that folder just stays on disk; in a cloud
routine, where every run starts from a fresh clone, the run commits it back (see docs/pt-br/NUVEM.md). Files are
written atomically (temp file + rename), so a run killed mid-write never leaves a broken file behind."""
import json
import os
import tempfile
from pathlib import Path

from .config import ROOT


def state_dir():
    d = Path(os.environ.get("CLIPPER_STATE_DIR") or ROOT / "state")
    d.mkdir(parents=True, exist_ok=True)
    return d


def load(name, default=None):
    """state/<name>.json, or `default` (a fresh {} if not given) when missing or unreadable."""
    f = state_dir() / f"{name}.json"
    try:
        return json.loads(f.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {} if default is None else default


def save(name, data):
    d = state_dir()
    fd, tmp = tempfile.mkstemp(dir=d, prefix=f".{name}.", suffix=".tmp")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False, sort_keys=True)
        os.replace(tmp, d / f"{name}.json")
    finally:
        if os.path.exists(tmp):
            os.unlink(tmp)
    return d / f"{name}.json"
