"""Recover footage without a recorder running: finished Twitch VODs and the new part of lives still running.

Twitch keeps a live's VOD growing while the stream is on (when the streamer has VODs enabled), so a run every hour
can download only the minutes it hasn't seen yet. Each chunk becomes a normal live job (`jobs/live-vod-...`) with
`live_ready`, so `clipper live jobs`, `/clip-daily live` and `clipper live done` handle it exactly like a chunk from
the recorder. This is what lets the operation work from a cloud routine or with the PC switched off during the live.

Progress per VOD (seconds already turned into jobs, failures) is kept in state/vods.json, so a fresh clone or a
crashed run picks up where the last one stopped, and no second of footage is fetched twice.

Streams come from the profile's live.yaml (`twitch:name`); Kick and YouTube lives are recovered later through their
uploads (`creators.yaml` + `clipper daily`)."""
import json
import re
import subprocess
from datetime import datetime, timezone
from pathlib import Path

from . import config, state
from .config import JOBS
from .live import load_streams, slug, topic_only
from .sources import topic_evidence

STATE = "vods"
EDGE_S = 120          # a live VOD's last 2 minutes may still be incomplete on Twitch's side
MAX_ATTEMPTS = 3      # a chunk that fails this often is skipped (and reported) instead of blocking the queue


def settings(cfg):
    v = cfg.get("vods") or {}
    return {"chunk": int(v.get("chunk_minutes", 30)) * 60, "max": int(v.get("max_chunks_per_run", 4)),
            "lookback_h": float(v.get("lookback_hours", 48)), "min": int(v.get("min_chunk_minutes", 10)) * 60}


def ytdlp_json(url, flat=False, limit=None):
    cmd = ["yt-dlp", "-J", "--no-warnings", "--skip-download"]
    if flat:
        cmd += ["--flat-playlist"] + (["-I", f"1:{limit}"] if limit else [])
    res = subprocess.run(cmd + [url], capture_output=True, text=True, timeout=180)
    if res.returncode != 0:
        raise RuntimeError((res.stderr.strip().splitlines() or ["yt-dlp failed"])[-1])
    return json.loads(res.stdout)


def download(url, start, end, dest):
    """Only [start, end] of the VOD, at up to 1080p, into dest (mp4)."""
    dest = Path(dest)
    cmd = ["yt-dlp", "--no-warnings", "--no-part", "-f", "best[height<=1080]/best", "--download-sections",
           f"*{int(start)}-{int(end)}", "--merge-output-format", "mp4", "-o", str(dest.with_suffix(".%(ext)s")), url]
    subprocess.run(cmd, check=True, capture_output=True, text=True, timeout=3600)
    got = next(iter(sorted(dest.parent.glob(dest.stem + ".*"))), None)
    if not got:
        raise RuntimeError("download produced no file")
    if got.suffix != ".mp4":
        subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(got), "-c", "copy", "-movflags", "+faststart",
                        str(dest)], check=True)
        got.unlink()
    return dest


def twitch_name(url):
    m = re.search(r"twitch\.tv/([^/?#]+)", url or "")
    return m.group(1).lower() if m and m.group(1) != "videos" else None


def recent_vods(name, limit=5):
    """[{id, url}] newest first for a Twitch channel's past broadcasts (live ones included)."""
    data = ytdlp_json(f"https://www.twitch.tv/{name}/videos?filter=archives&sort=time", flat=True, limit=limit)
    out = []
    for e in data.get("entries") or []:
        vid = str(e.get("id") or "").lstrip("v")
        if vid.isdigit():
            out.append({"id": vid, "url": f"https://www.twitch.tv/videos/{vid}"})
    return out


def plan_chunks(duration, done, live, s):
    """[(start, end)] still to fetch for one VOD, given how far it was already fetched (`done` seconds)."""
    usable = max(0.0, float(duration) - (EDGE_S if live else 0))
    out, t = [], float(done)
    while usable - t >= s["chunk"]:
        out.append((t, t + s["chunk"]))
        t += s["chunk"]
    if usable - t >= s["min"] and not live:  # a finished VOD's tail
        out.append((t, usable))
    elif live and usable - t >= s["min"] and not out:
        out.append((t, usable))  # a live VOD with less than a full chunk new: take what's there once it's worth it
    return out


def scan(cfg, now=None):
    """What `fetch` would download: per stream, its recent on-topic VODs and their missing chunks."""
    s = settings(cfg)
    st = state.load(STATE)
    now = now or datetime.now(timezone.utc).timestamp()
    plan, skipped, errors = [], [], []
    for stream in load_streams():
        name = twitch_name(stream.get("url"))
        if not name:
            continue
        try:
            vods = recent_vods(name)
        except (RuntimeError, subprocess.SubprocessError, ValueError) as e:
            errors.append({"stream": stream["name"], "error": str(e)})
            continue
        for v in vods:
            rec = st.get(v["id"], {})
            if rec.get("finished") and rec.get("done", 0) >= rec.get("duration", 0) - 1:
                continue
            try:
                info = ytdlp_json(v["url"])
            except (RuntimeError, subprocess.SubprocessError, ValueError) as e:
                errors.append({"stream": stream["name"], "vod": v["id"], "error": str(e)})
                continue
            started = float(info.get("timestamp") or 0)
            if started and now - started > s["lookback_h"] * 3600:
                continue
            title = info.get("description") or info.get("title") or ""
            if topic_only(stream) and not topic_evidence(title, "", [], cfg):
                skipped.append({"stream": stream["name"], "vod": v["id"], "title": title})
                continue
            live = bool(info.get("is_live") or info.get("live_status") == "is_live")
            dur = float(info.get("duration") or 0)
            for a, b in plan_chunks(dur, rec.get("done", 0), live, s):
                key = f"{int(a)}-{int(b)}"
                if (rec.get("failures") or {}).get(key, 0) >= MAX_ATTEMPTS:
                    continue
                plan.append({"stream": stream["name"], "channel": info.get("uploader") or stream["name"],
                             "vod": v["id"], "url": v["url"], "title": title, "live": live, "duration": dur,
                             "started_at": started, "start": a, "end": b})
    return {"chunks": order(plan), "skipped_off_topic": skipped, "errors": errors}


def order(chunks):
    """Round-robin across streams so every streamer gets clips; within a stream, the newest VOD first and, inside a
    VOD, its chunks in order (each run continues where the last stopped)."""
    by = {}
    for c in sorted(chunks, key=lambda c: (-c["started_at"], c["start"])):
        by.setdefault(c["stream"], []).append(c)
    out, queues = [], list(by.values())
    while any(queues):
        for q in queues:
            if q:
                out.append(q.pop(0))
    return out


def job_id(c):
    return f"live-vod-{slug(c['stream'])}-{c['vod']}-{int(c['start']):06d}"


def make_job(c, src):
    job = JOBS / job_id(c)
    job.mkdir(parents=True, exist_ok=True)
    dur = float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0",
                                str(src)], capture_output=True, text=True).stdout.strip() or 0)
    meta = {"id": job.name, "url": c["url"], "title": c["title"], "channel": c["channel"], "duration": round(dur),
            "offset": float(c["start"]), "live": True, "vod": c["vod"],
            "recorded_at": (c["started_at"] or 0) + float(c["start"]) or None, "profile": config.PROFILE}
    (job / "job.json").write_text(json.dumps(meta, indent=2), encoding="utf-8")
    (job / "source.info.json").write_text(json.dumps({"title": c["title"], "channel": c["channel"],
                                                       "is_live": c["live"]}), encoding="utf-8")
    (job / "live_ready").write_text(datetime.now().isoformat())
    return job


def fetch_chunks(cfg, max_chunks=None, dry_run=False, analyze=True):
    """Download the next chunks, turn each into a live job and (by default) transcribe + score it, so
    `/clip-daily live` finds it ready. Progress is saved after every chunk."""
    s = settings(cfg)
    found = scan(cfg)
    todo = found["chunks"][:max_chunks or s["max"]]
    if dry_run:
        return {"would_fetch": todo, "pending_total": len(found["chunks"]), "errors": found["errors"]}
    st = state.load(STATE)
    done, failed, blocked = [], [], set()
    for c in todo:
        if c["vod"] in blocked:  # chunks of a VOD are sequential: after a failure, retry from there next run
            continue
        rec = st.setdefault(c["vod"], {"stream": c["stream"], "done": 0.0})
        rec.update(duration=c["duration"], finished=not c["live"], title=c["title"])
        job = JOBS / job_id(c)
        src = job / "source.mp4"
        try:
            if not src.exists():  # a crashed run may have left the download complete: don't fetch it twice
                job.mkdir(parents=True, exist_ok=True)
                download(c["url"], c["start"], c["end"], src)
            make_job(c, src)
            if analyze:
                from .analyze import analyze as run_analysis
                run_analysis(job, cfg)
        except (subprocess.SubprocessError, RuntimeError, OSError) as e:
            key = f"{int(c['start'])}-{int(c['end'])}"
            rec.setdefault("failures", {})[key] = rec.get("failures", {}).get(key, 0) + 1
            failed.append({"job": job.name, "error": str(e)[-300:]})
            state.save(STATE, st)
            blocked.add(c["vod"])
            continue
        rec["done"] = max(float(rec.get("done", 0)), float(c["end"]))
        rec["updated_at"] = datetime.now(timezone.utc).isoformat(timespec="seconds")
        state.save(STATE, st)
        done.append(job.name)
    return {"fetched": done, "failed": failed, "pending_after": max(0, len(found["chunks"]) - len(done)),
            "errors": found["errors"], "skipped_off_topic": found["skipped_off_topic"]}


def status():
    return state.load(STATE)
