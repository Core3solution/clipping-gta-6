"""Post-render QA by script: what can be measured on a finished MP4 is measured here, so the QA agent (and the
operator) only look at one contact sheet per video for what needs eyes (framing, what the picture shows).

One FFmpeg pass reads the whole clip with blackdetect, freezedetect, silencedetect and ebur128 (integrated loudness
and true peak); ffprobe checks size and audio. Thresholds follow the platforms' delivery (-14 LUFS, true peak under
-1 dBTP) and the defects the QA agent caught on 18/11. Ideas from Editonny's quality_gate.py (MIT); no code copied."""
import json
import re
import subprocess
from pathlib import Path

SIZE = (1080, 1920)
LUFS, LUFS_TOL, MAX_TP = -14.0, 1.5, -1.0
BLACK_S, FREEZE_S, SILENCE_S, SILENCE_DB = 0.1, 2.0, 1.5, -45
BLACK_FAIL_S = 1.0  # shorter black is a cutscene fade (content): a warning for the eyes, not a re-render
SHEET_FRAMES = 6


def _probe(mp4):
    out = subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration:stream=codec_type,width,height",
                          "-of", "json", str(mp4)], capture_output=True, text=True, check=True).stdout
    return json.loads(out)


def measure(mp4, has_audio=True):
    """{black: [(start, dur)], freeze: [(start, dur)], silence: [(start, dur)], lufs, true_peak} in one pass."""
    vf = f"blackdetect=d={BLACK_S}:pix_th=0.10,freezedetect=n=-60dB:d={FREEZE_S}"
    cmd = ["ffmpeg", "-hide_banner", "-nostats", "-i", str(mp4), "-vf", vf]
    cmd += ["-af", f"silencedetect=n={SILENCE_DB}dB:d={SILENCE_S},ebur128=peak=true"] if has_audio else ["-an"]
    err = subprocess.run(cmd + ["-f", "null", "-"], capture_output=True, text=True).stderr
    f = r"(-?[\d.]+)"
    out = {"black": [(float(a), float(c)) for a, _, c in
                     re.findall(rf"black_start:{f} black_end:{f} black_duration:{f}", err)],
           "freeze": [(float(a), float(b)) for a, b in
                      zip(re.findall(rf"freeze_start: {f}", err), re.findall(rf"freeze_duration: {f}", err))],
           "silence": [(float(a), float(b)) for a, b in
                       zip(re.findall(rf"silence_start: {f}", err), re.findall(rf"silence_duration: {f}", err))],
           "lufs": None, "true_peak": None}
    summary = err[err.rfind("Summary:"):] if "Summary:" in err else ""
    m = re.search(rf"I:\s+{f} LUFS", summary)
    out["lufs"] = float(m.group(1)) if m else None
    m = re.search(rf"Peak:\s+{f} dBFS", summary)
    out["true_peak"] = float(m.group(1)) if m else None
    return out


def contact_sheet(mp4, duration, frames=SHEET_FRAMES):
    """One JPG with `frames` evenly spaced stills (3 per row), next to the MP4: what the QA agent looks at."""
    sheet = Path(mp4).with_suffix(".sheet.jpg")
    rate = frames / max(duration, 0.1)
    subprocess.run(["ffmpeg", "-y", "-loglevel", "error", "-i", str(mp4), "-vf",
                    f"fps={rate:.5f},scale=360:640:force_original_aspect_ratio=decrease,pad=360:640:(ow-iw)/2:(oh-ih)/2,"
                    f"tile=3x{(frames + 2) // 3}", "-frames:v", "1", "-q:v", "4", str(sheet)], check=True)
    return sheet


def check(mp4):
    """{ok, fails, warnings, measures, sheet}. Fails are always defects (re-render). Warnings can be content (a
    cutscene fade, a still map screen, a quiet dive): whoever looks at the contact sheet decides."""
    info = _probe(mp4)
    streams = info.get("streams") or []
    video = next((s for s in streams if s.get("codec_type") == "video"), {})
    has_audio = any(s.get("codec_type") == "audio" for s in streams)
    duration = float((info.get("format") or {}).get("duration") or 0)
    m = measure(mp4, has_audio)
    fails = []
    size = (video.get("width"), video.get("height"))
    if size != SIZE:
        fails.append(f"size {size[0]}x{size[1]}, expected {SIZE[0]}x{SIZE[1]}")
    if not has_audio:
        fails.append("no audio")
    fails += [f"black {d:.2f}s at {s:.1f}s" for s, d in m["black"] if d >= BLACK_FAIL_S]
    warnings = [f"black {d:.2f}s at {s:.1f}s" for s, d in m["black"] if d < BLACK_FAIL_S]
    warnings += [f"still picture {d:.1f}s at {s:.1f}s" for s, d in m["freeze"]]
    warnings += [f"silence {d:.1f}s at {s:.1f}s" for s, d in m["silence"]]
    if has_audio and (m["lufs"] is None or abs(m["lufs"] - LUFS) > LUFS_TOL):
        fails.append(f"loudness {m['lufs']} LUFS, expected {LUFS:.0f} ± {LUFS_TOL}")
    if has_audio and m["true_peak"] is not None and m["true_peak"] > MAX_TP:
        fails.append(f"true peak {m['true_peak']} dBTP, max {MAX_TP}")
    sheet = contact_sheet(mp4, duration)
    return {"ok": not fails, "fails": fails, "warnings": warnings, "measures": dict(m, duration=round(duration, 2)),
            "sheet": str(sheet)}
