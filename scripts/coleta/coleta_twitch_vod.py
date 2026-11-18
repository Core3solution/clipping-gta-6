"""Coleta Alanzoka (Twitch VOD em andamento) em blocos de 1 h, sem recodificar. Um processo, sequencial.
Estado em metadados/downloads.json; log em logs/coleta-twitch.log. Re-executar retoma de onde parou.
Cópia da operação 03 de 18/11/2026 (scripts/coleta/README.md). Para outro streamer/VOD, ajuste BASE, VOD_ID e GTA_START."""
import json, os, re, shutil, subprocess, sys, time, datetime, urllib.request
from concurrent.futures import ThreadPoolExecutor
from urllib.parse import urljoin

WORKERS = 3

BASE = r"D:\GTA6-BR\COLETA\Alanzoka"
VOD_ID = "2932200023"
URL = f"https://www.twitch.tv/videos/{VOD_ID}"
FFMPEG = "ffmpeg"    # no PATH (em 18/11 era o caminho absoluto do notebook)
FFPROBE = "ffprobe"
GTA_START = 1497          # capitulo "Grand Theft Auto VI" (s desde o inicio do VOD)
CHUNK = 3600
STATE = os.path.join(BASE, "metadados", "downloads.json")
LOG = os.path.join(BASE, "logs", "coleta-twitch.log")
LOCK = os.path.join(BASE, "logs", "coleta-twitch.lock")
OUTDIR = os.path.join(BASE, "vods")


def log(msg):
    line = f"{datetime.datetime.now():%Y-%m-%d %H:%M:%S} {msg}"
    print(line, flush=True)
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def load():
    try:
        return json.load(open(STATE, encoding="utf-8"))
    except Exception:
        return {"vod": URL, "itens": {}}


def save(st):
    tmp = STATE + ".tmp"
    json.dump(st, open(tmp, "w", encoding="utf-8"), ensure_ascii=False, indent=1)
    os.replace(tmp, STATE)


def info():
    r = subprocess.run(["yt-dlp", "-J", "--no-warnings", "--skip-download", URL], capture_output=True, text=True, encoding="utf-8")
    j = json.loads(r.stdout)
    fm = [f for f in j["formats"] if f.get("format_id") == "1080p60"] or [f for f in j["formats"] if f.get("height") == 1080]
    return float(j["duration"]), j.get("live_status") == "is_live", fm[-1]["url"]


INIT = [None]  # init segment do fMP4 (#EXT-X-MAP)
UA = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64)"}


def get(url, tries=4):
    for i in range(tries):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=UA), timeout=60) as r:
                return r.read()
        except OSError:
            if i == tries - 1:
                raise
            time.sleep(3 * (i + 1))


def segments(m3u8):
    out, t, dur = [], 0.0, None
    for ln in (x.strip() for x in get(m3u8).decode().splitlines()):
        if ln.startswith("#EXT-X-MAP:"):
            INIT[0] = urljoin(m3u8, re.search(r'URI="([^"]+)"', ln).group(1))
        elif ln.startswith("#EXTINF:"):
            dur = float(ln[8:].split(",")[0])
        elif ln and not ln.startswith("#") and dur is not None:
            out.append((t, dur, urljoin(m3u8, ln)))
            t, dur = t + dur, None
    return out


def fetch_range(m3u8, a, b, dest):
    """Segmentos que cobrem [a,b) baixados em paralelo (retomavel) e juntados sem recodificar."""
    segs = [s for s in segments(m3u8) if a <= s[0] < b]  # por inicio do segmento: blocos sem sobreposicao nem lacuna
    if not segs:
        raise RuntimeError("sem segmentos no intervalo")
    tmp = dest + ".seg"
    os.makedirs(tmp, exist_ok=True)

    def one(item):
        i, (_, _, u) = item
        f = os.path.join(tmp, f"{i:05d}.m4s")
        if not os.path.exists(f):
            open(f + ".part", "wb").write(get(u))
            os.replace(f + ".part", f)
        return f
    with ThreadPoolExecutor(WORKERS) as ex:
        files = list(ex.map(one, enumerate(segs)))
    joined = os.path.join(tmp, "joined.mp4")
    with open(joined, "wb") as out:
        if INIT[0]:
            out.write(get(INIT[0]))
        for f in files:
            with open(f, "rb") as src:
                shutil.copyfileobj(src, out)
    r = subprocess.run([FFMPEG, "-y", "-loglevel", "error", "-i", joined, "-map", "0:v:0", "-map", "0:a:0?", "-c", "copy",
                        "-movflags", "+faststart", dest + ".part.mp4"], capture_output=True, text=True)
    if r.returncode:
        raise RuntimeError("remux: " + r.stderr.strip()[-200:])
    os.replace(dest + ".part.mp4", dest)
    shutil.rmtree(tmp)
    return segs[0][0], segs[-1][0] + segs[-1][1]


def probe(path):
    r = subprocess.run([FFPROBE, "-v", "error", "-select_streams", "v:0", "-show_entries",
                        "stream=width,height,r_frame_rate,codec_name:format=duration,size", "-of", "json", path],
                       capture_output=True, text=True)
    j = json.loads(r.stdout)
    s = j["streams"][0]
    return {"w": s["width"], "h": s["height"], "fps": s["r_frame_rate"], "codec": s["codec_name"],
            "dur": float(j["format"]["duration"]), "bytes": int(j["format"]["size"])}


def hms(s):
    return f"{int(s)//3600:02d}{int(s)%3600//60:02d}{int(s)%60:02d}"


def do_chunk(st, m3u8, a, b, label):
    name = f"twitch_v{VOD_ID}_{label}_{hms(a)}-{hms(b)}.mp4"
    dest = os.path.join(OUTDIR, name)
    it = st["itens"].setdefault(name, {})
    if it.get("status") in ("concluido", "suspeito"):
        return
    it.update(status="iniciado", inicio=a, fim=b, started=str(datetime.datetime.now()))
    save(st)
    log(f"INICIADO {name} [{a}-{b}s]")
    try:
        real = fetch_range(m3u8, a, b, dest)
        it["cobertura_real_s"] = [round(real[0], 1), round(real[1], 1)]
    except Exception as e:
        it.update(status="interrompido", erro=str(e)[:300])
        save(st)
        log(f"INTERROMPIDO {name}: {it['erro']}")
        return
    try:
        p = probe(dest)
    except Exception as e:
        it.update(status="interrompido", erro=f"ffprobe: {e}")
        save(st)
        log(f"INTERROMPIDO (ffprobe) {name}")
        return
    rs, re_ = it["cobertura_real_s"]; ok = abs(p["dur"] - (re_ - rs)) <= 5 and p["h"] == 1080
    it.update(status="concluido" if ok else "suspeito", ffprobe=p, ended=str(datetime.datetime.now()))
    save(st)
    log(f"{'CONCLUIDO' if ok else 'SUSPEITO'} {name} {p['w']}x{p['h']}@{p['fps']} {p['codec']} {p['dur']:.0f}s {p['bytes']/1e9:.2f}GB")


def main():
    if os.path.exists(LOCK):
        try:
            pid = int(open(LOCK).read())
            if subprocess.run(["tasklist", "/FI", f"PID eq {pid}"], capture_output=True, text=True).stdout.count(str(pid)):
                print("ja em execucao, pid", pid)
                return
        except Exception:
            pass
    open(LOCK, "w").write(str(os.getpid()))
    st = load()
    try:
        while True:
            dur, live, m3u8 = info()
            log(f"VOD duracao {dur:.0f}s live={live}")
            t, n = GTA_START, 1
            while t < dur:
                end = t + CHUNK
                if end <= dur - 20:                       # bloco cheio ja disponivel
                    do_chunk(st, m3u8, t, end, f"gta6_p{n:02d}")
                elif not live:                            # live encerrada: ultimo bloco parcial
                    do_chunk(st, m3u8, t, int(dur), f"gta6_p{n:02d}")
                t += CHUNK; n += 1
            if dur > GTA_START + 60:
                do_chunk(st, m3u8, 0, GTA_START, "pre-gta_just-chatting")
            pend = [k for k, v in st["itens"].items() if v.get("status") in ("interrompido", "suspeito")]
            if not live and not pend:
                log("FIM: VOD encerrado e tudo concluido")
                break
            time.sleep(600 if live else 120)
    finally:
        try: os.remove(LOCK)
        except OSError: pass


if __name__ == "__main__":
    main()
