"""Transforma os blocos .ts fechados de scripts/captura_youtube.sh em jobs e analisa um por vez.
uso: CLIPPER_PROFILE=gta-br .venv/bin/python scripts/blocos_youtube.py PASTA_RAW URL TITULO NOME CANAL [MIN_SEGUNDOS]
Um bloco está fechado quando existe outro .ts mais novo na pasta (em PASTA-recup: quando para de crescer por 2 min). Blocos menores que MIN_SEGUNDOS ficam na pasta."""
import subprocess, sys, time
from pathlib import Path
ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT))
from clipper import live

raw, url, title, name, channel = Path(sys.argv[1]), *sys.argv[2:6]
min_s = int(sys.argv[6]) if len(sys.argv) > 6 else 120
dur = lambda p: float(subprocess.run(["ffprobe", "-v", "error", "-show_entries", "format=duration", "-of", "csv=p=0", str(p)],
                                     capture_output=True, text=True).stdout.strip() or 0)
while True:
    recup = Path(str(raw) + "-recup")  # lacunas puxadas da janela HLS: fechadas quando param de crescer
    segs = sorted(raw.glob("*.ts"))[:-1]  # o último ainda está sendo gravado
    segs += [f for f in sorted(recup.glob("*.ts")) if time.time() - f.stat().st_mtime > 120]
    for seg in segs:
        if dur(seg) < min_s:
            continue
        session, idx = seg.stem.split("-")
        jid = live.make_job(seg, name, url, title, int(session) + int(idx) * 900, channel)
        subprocess.run([sys.executable, "-m", "clipper", "analyze", jid, "--fast"], cwd=ROOT,
                       stdout=open(ROOT / "logs" / f"analise-{jid}.log", "w"), stderr=subprocess.STDOUT)
        print(f"{time.strftime('%T')} analisado {jid}", flush=True)
    time.sleep(30)
