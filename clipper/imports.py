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
import os
import shutil
import subprocess
from datetime import datetime
from pathlib import Path

import yaml

from . import config, state
from .config import JOBS
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


def _num(x):
    """ffprobe number, or None for a missing value or "N/A"."""
    try:
        return float(x)
    except (TypeError, ValueError):
        return None


def av_check(path, max_start_s=0.1, max_end_s=0.5):
    """Whether audio and video of a chunk start and end together: {ok, video: [start, end], audio: [...], reason,
    audio_tracks}. Only the first stream of each kind counts (it is the one the chunks keep); MKV gives no
    per-stream duration, so the container's is used there."""
    info = probe(path)
    fmt_dur = _num((info.get("format") or {}).get("duration")) or 0.0
    spans, tracks = {}, 0
    for s in info.get("streams") or []:
        kind = s.get("codec_type")
        tracks += kind == "audio"
        if kind in ("video", "audio") and kind not in spans:
            start = _num(s.get("start_time")) or 0.0
            dur = _num(s.get("duration"))
            spans[kind] = [round(start, 3), round(start + (fmt_dur if dur is None else dur), 3)]
    out = {"ok": False, "video": spans.get("video"), "audio": spans.get("audio"), "reason": "", "audio_tracks": tracks}
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


def split(src, staging, chunk_s, from_s, duration, min_tail_s=None):
    """Cut `src` into chunks of `chunk_s` seconds from `from_s` (the part before it is dropped), copying the streams.
    Returns [{file, start, end}] in seconds from the start of the file (the segment list is already relative to it,
    whatever the source's first timestamp). A tail shorter than `min_tail_s` (default: 60 s, or half a chunk) joins
    the last chunk. blocks.json in `staging` marks a finished split: a rerun reuses it; a staging folder without it
    (a killed run) is split again from scratch."""
    min_tail_s = min(60.0, chunk_s / 2) if min_tail_s is None else min_tail_s
    staging = Path(staging)
    done = staging / "blocks.json"
    if done.exists():
        return [dict(b, file=staging / b["file"]) for b in json.loads(done.read_text(encoding="utf-8"))]
    if staging.exists():
        shutil.rmtree(staging)
    staging.mkdir(parents=True)
    marks, t = ([from_s] if from_s > 0 else []), from_s + chunk_s
    while t <= duration - min_tail_s:
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
    blocks = []
    for row in (staging / "list.csv").read_text(encoding="utf-8").splitlines():
        name, a, b = row.rsplit(",", 2)
        start, end = round(float(a), 3), round(float(b), 3)
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


def job_id(streamer, vod, offset):
    return f"live-vod-{slug(streamer)}-{vod}-{int(offset):06d}"


def import_file(path, streamer, url="", started_at=None, vod=None, from_s=0.0, chunk_minutes=30, cfg=None,
                analyze=True, title=None):
    """Turn a local video into live-vod jobs (one per chunk). Safe to rerun: finished imports are recognised by the
    file's SHA-256, chunks already made are skipped, and an interrupted run continues from its staging folder."""
    src = Path(path).resolve()
    if not src.is_file():
        raise SystemExit(f"arquivo não encontrado: {src} (no WSL, C:\\... é /mnt/c/...)")
    started = None
    if started_at:
        when = datetime.fromisoformat(started_at.replace("Z", "+00:00"))
        if when.tzinfo is None:
            raise SystemExit(f"--started-at {started_at} precisa do fuso, ex.: 2026-11-18T07:35:42-03:00")
        started = when.timestamp()
    fp = fingerprint(src)
    sha = fp["sha256"]
    if from_s >= fp["duration"]:
        raise SystemExit(f"--from {from_s:.0f} s passa do fim do vídeo ({fp['duration']:.0f} s)")
    staging = JOBS / f".import-{sha[:12]}"
    data = state.load(STATE)
    rec = data.get(sha) or {}
    if rec and (rec.get("from"), rec.get("chunk_minutes")) != (from_s, chunk_minutes):
        raise SystemExit(f"este arquivo já foi importado com --from {rec.get('from')} e --chunk-minutes "
                         f"{rec.get('chunk_minutes')}; com outros valores os blocos se sobreporiam")
    if rec.get("complete"):
        shutil.rmtree(staging, ignore_errors=True)  # left behind by a run killed right after finishing
        return {"imported": [], "skipped": sorted(rec["blocks"].values()), "warnings": [], "already_imported": True,
                "sha256": sha}
    if not (staging / "blocks.json").exists():
        JOBS.mkdir(parents=True, exist_ok=True)
        free = shutil.disk_usage(JOBS).free
        if free < fp["size"] * 1.05:
            raise SystemExit(f"espaço insuficiente em {JOBS}: {free / 1e9:.1f} GB livres, os blocos ocupam "
                             f"{fp['size'] / 1e9:.1f} GB")
    vod = vod or rec.get("vod") or sha[:12]
    rec.update(file=str(src), size=fp["size"], duration=fp["duration"], streamer=streamer, vod=vod, url=url,
               started_at=started_at, chunk_minutes=chunk_minutes, **{"from": from_s})
    rec.setdefault("blocks", {})
    data[sha] = rec
    state.save(STATE, data)
    auth = authorization(streamer, config.PROFILE)
    warnings = []
    if auth["status"] != "autorizado":
        warnings.append(f"{streamer}: publicação {auth['status']} (profiles/{config.PROFILE}/authorizations.yaml)")
    whole = av_check(src)
    if not whole["ok"]:
        warnings.append(f"fonte: {whole['reason']}")
    if whole["audio_tracks"] > 1:
        warnings.append(f"fonte: {whole['audio_tracks']} trilhas de áudio; só a primeira entra nos blocos")
    blocks = split(src, staging, chunk_minutes * 60, from_s, fp["duration"])
    if not blocks:
        raise SystemExit("nenhum bloco gerado (sem keyframe depois de --from?)")
    for b in blocks:  # every id first: a clash must stop the import before any chunk moves
        meta_file = JOBS / job_id(streamer, vod, b["start"]) / "job.json"
        if meta_file.exists() and json.loads(meta_file.read_text(encoding="utf-8")).get("source_sha256") != sha:
            raise SystemExit(f"{meta_file.parent.name} já existe e veio de outro arquivo; use outro --vod")
    imported, skipped = [], []
    for b in blocks:
        key, jid = f"{int(b['start']):06d}", job_id(streamer, vod, b["start"])
        job = JOBS / jid
        dest, meta_file = job / "source.mp4", job / "job.json"
        if rec["blocks"].get(key) == jid and dest.exists():
            Path(b["file"]).unlink(missing_ok=True)
            skipped.append(jid)
            continue
        job.mkdir(parents=True, exist_ok=True)
        if not dest.exists():  # a run killed after the move but before saving progress already put it there
            os.replace(b["file"], dest)
        av = av_check(dest)
        if not av["ok"]:
            warnings.append(f"{jid}: {av['reason']}")
        meta = {"id": jid, "url": url, "title": title or src.stem, "channel": streamer,
                "duration": round(b["end"] - b["start"]), "offset": b["start"], "live": True, "vod": vod,
                "recorded_at": started + b["start"] if started is not None else None, "profile": config.PROFILE,
                "source_file": str(src), "source_sha256": sha, "av": av, "authorization": auth}
        meta_file.write_text(json.dumps(meta, indent=2, ensure_ascii=False), encoding="utf-8")
        (job / "source.info.json").write_text(json.dumps({"title": meta["title"], "channel": streamer,
                                                          "is_live": False}), encoding="utf-8")
        (job / "live_ready").write_text(datetime.now().isoformat())
        rec["blocks"][key] = jid
        state.save(STATE, data)
        imported.append(jid)
        if analyze:
            from .analyze import analyze as run_analysis
            run_analysis(job, cfg)
    rec["complete"] = True
    state.save(STATE, data)
    shutil.rmtree(staging, ignore_errors=True)
    return {"imported": imported, "skipped": skipped, "warnings": warnings, "already_imported": False,
            "sha256": sha}
