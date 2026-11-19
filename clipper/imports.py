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
import shutil
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


def av_check(path, max_start_s=0.1, max_end_s=0.5):
    """Whether audio and video of a chunk start and end together: {ok, video: [start, end], audio: [...], reason}."""
    spans = {}
    for s in probe(path).get("streams") or []:
        if s.get("codec_type") in ("video", "audio") and s["codec_type"] not in spans:
            start = float(s.get("start_time") or 0)
            spans[s["codec_type"]] = [round(start, 3), round(start + float(s.get("duration") or 0), 3)]
    out = {"ok": False, "video": spans.get("video"), "audio": spans.get("audio"), "reason": ""}
    if not spans.get("video") or not spans.get("audio"):
        out["reason"] = "no audio" if spans.get("video") else "no video"
        return out
    (v0, v1), (a0, a1) = spans["video"], spans["audio"]
    if abs(v0 - a0) > max_start_s:
        out["reason"] = f"audio starts {a0 - v0:+.2f} s from the video"
    elif abs(v1 - a1) > max_end_s:
        out["reason"] = f"audio ends {a1 - v1:+.2f} s from the video"
    else:
        out["ok"] = True
    return out


def split(src, staging, chunk_s, from_s, duration):
    """Cut `src` into chunks of `chunk_s` seconds from `from_s` (the part before it is dropped), copying the streams.
    Returns [{file, start, end}] in seconds of the source. blocks.json in `staging` marks a finished split: a rerun
    reuses it; a staging folder without it (a killed run) is split again from scratch."""
    staging = Path(staging)
    done = staging / "blocks.json"
    if done.exists():
        return [dict(b, file=staging / b["file"]) for b in json.loads(done.read_text(encoding="utf-8"))]
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    marks, t = ([from_s] if from_s > 0 else []), from_s + chunk_s
    while t < duration:
        marks.append(t)
        t += chunk_s
    cmd = ["ffmpeg", "-y", "-loglevel", "error", "-i", str(src), "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
           "-f", "segment", "-segment_format", "mp4", "-segment_format_options", "movflags=+faststart",
           "-reset_timestamps", "1", "-segment_list", str(staging / "list.csv"), "-segment_list_type", "csv"]
    if marks:
        cmd += ["-segment_times", ",".join(f"{m:.3f}" for m in marks)]
    else:
        cmd += ["-segment_time", str(chunk_s)]
    subprocess.run(cmd + [str(staging / "b%04d.mp4")], check=True)
    origin = float((probe(src).get("format") or {}).get("start_time") or 0)
    blocks = []
    for row in (staging / "list.csv").read_text(encoding="utf-8").splitlines():
        name, a, b = row.rsplit(",", 2)
        start, end = round(float(a) - origin, 3), round(float(b) - origin, 3)
        if start < from_s - 0.001:  # the pre-game part before --from
            (staging / name).unlink(missing_ok=True)
            continue
        blocks.append({"file": name, "start": start, "end": end})
    done.write_text(json.dumps(blocks), encoding="utf-8")
    return [dict(b, file=staging / b["file"]) for b in blocks]


def authorization(streamer, profile=None):
    """Publishing permission for a streamer from profiles/<profile>/authorizations.yaml; anyone not listed (or with
    an unknown status) is `pendente`."""
    f = config.profile_file("authorizations.yaml", profile)
    entries = (yaml.safe_load(f.read_text(encoding="utf-8")) if f.exists() else None) or {}
    e = entries.get(slug(streamer)) or {}
    status = e.get("status") if e.get("status") in STATUSES else "pendente"
    return {"status": status, "evidence": str(e.get("evidencia") or ""), "date": str(e.get("data") or "")}
