"""Import a local video (a finished live saved to disk) as live-vod jobs, like `vods fetch` does for Twitch and Kick.

The file is cut into chunks without re-encoding by one pass of FFmpeg's segment muxer; its CSV segment list gives
each chunk's real start in the source, so offsets and `recorded_at` stay true even though cuts land on keyframes.
The original is only read. The import is keyed by the file's full SHA-256, so a rerun (or the same file under another
name) never creates a chunk twice, and a run killed halfway resumes where it stopped (progress in
state/imports.json).

Being in live.yaml says what to capture, not that clips may be published: publishing permission is kept apart in
profiles/<profile>/authorizations.yaml and copied into each job's `authorization`."""
import hashlib
import json
import subprocess
from pathlib import Path

import yaml

from . import config, state
from .live import slug

STATE = "imports"
STATUSES = ("autorizado", "pendente", "negado")


def probe(path):
    """ffprobe JSON (format + streams) of a media file."""
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries",
                          "format=duration,start_time:stream=codec_type,start_time,duration", "-of", "json",
                          str(path)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def fingerprint(path):
    """{sha256, size, duration, start_time} of a file. The full SHA-256 is cached per path + size + mtime, so a
    resumed import of a 10 GB file doesn't read it all again."""
    path = Path(path).resolve()
    st = path.stat()
    key = f"{path}|{st.st_size}|{st.st_mtime_ns}"
    data = state.load(STATE)
    cached = (data.get("fingerprints") or {}).get(key)
    if cached:
        return cached
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for block in iter(lambda: f.read(8 << 20), b""):
            h.update(block)
    fmt = probe(path).get("format") or {}
    fp = {"sha256": h.hexdigest(), "size": st.st_size, "duration": float(fmt.get("duration") or 0),
          "start_time": float(fmt.get("start_time") or 0)}
    data = state.load(STATE)
    data.setdefault("fingerprints", {})[key] = fp
    state.save(STATE, data)
    return fp


def authorization(streamer, profile=None):
    """Publishing permission for a streamer from profiles/<profile>/authorizations.yaml; anyone not listed (or with
    an unknown status) is `pendente`."""
    f = config.profile_file("authorizations.yaml", profile)
    entries = (yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else None) or {}
    e = entries.get(slug(streamer)) or {}
    status = e.get("status") if e.get("status") in STATUSES else "pendente"
    return {"status": status, "evidence": str(e.get("evidencia") or ""), "date": str(e.get("data") or "")}
