import json, datetime as dt, re, os
B = r"D:\GTA6-BR\COLETA\Alanzoka"; M = B + r"\metadados"; C = B + r"\clipes-referencia"
TZ = dt.timezone(dt.timedelta(hours=-3))
S0 = dt.datetime(2026, 11, 18, 10, 24, 37, tzinfo=dt.timezone.utc).timestamp()   # inicio do VOD Twitch 2932200023
G0 = S0 + 1497                                                                     # inicio do capitulo GTA VI
loc = lambda t: dt.datetime.fromtimestamp(t, TZ).strftime("%d/%m %H:%M")
hms = lambda s: f"{int(s)//3600}:{int(s)%3600//60:02d}:{int(s)%60:02d}"
fdur = lambda s: f"{int(s)//60}:{int(s)%60:02d}" if s else "?"

tw = json.load(open(M + r"\twitch_clips_24h.json", encoding="utf-8-sig"))["entries"]
tw7 = json.load(open(M + r"\twitch_clips_7d.json", encoding="utf-8-sig"))["entries"]
ids = {e["id"] for e in tw}
tw += [e for e in tw7 if e["id"] not in ids]
T = []
for e in tw:
    ts = e.get("timestamp")
    if not ts or ts < G0:
        continue                                           # so GTA 6 (apos o inicio do capitulo); sem outros jogos
    T.append({"plataforma": "twitch", "titulo": e["title"], "link": e["url"], "views": e.get("view_count"),
              "duracao_s": e.get("duration"), "criado_em": loc(ts), "timestamp": ts,
              "offset_vod_aprox_s": round(ts - S0), "vod": "twitch.tv/videos/2932200023"})
T.sort(key=lambda x: -(x["views"] or 0))

Y = []
p = M + r"\ref_youtube_enriquecido.jsonl"
for l in open(p, encoding="utf-8"):
    d = json.loads(l)
    txt = (d.get("title") or "").lower()
    if not re.search(r"gta ?(6|vi)\b|grand theft auto (6|vi)\b", txt):
        continue
    if "alanzoka" not in txt and (d.get("channel") or "").lower() != "alanzoka" and "alanzoka" not in (d.get("uploader_id") or "").lower():
        continue
    ts = d.get("timestamp")
    ud = d.get("upload_date")
    Y.append({"plataforma": "youtube", "titulo": d["title"], "canal": d.get("channel"), "link": d["webpage_url"],
              "views": d.get("view_count"), "duracao_s": d.get("duration"), "data": ud, "criado_em": loc(ts) if ts else None,
              "origem": "oficial" if (d.get("uploader_id") or "").lower() == "@alanzoka" else "terceiro (corte/reupload)",
              "live": d.get("was_live") or d.get("live_status")})
Y.sort(key=lambda x: -(x["views"] or 0))
pos = [y for y in Y if (y["data"] or "0") >= "20261118"]
pre = [y for y in Y if (y["data"] or "0") < "20261118"]

json.dump({"gerado_em": str(dt.datetime.now()), "twitch_clips": T, "youtube_lancamento": pos, "youtube_pre_lancamento": pre},
          open(C + r"\catalogo.json", "w", encoding="utf-8"), ensure_ascii=False, indent=1)

o = [f"# Catálogo de referências Alanzoka × GTA 6\n\nGerado em {dt.datetime.now():%d/%m/%Y %H:%M}. Ordenado por popularidade (views). Sem curadoria editorial. "
     f"Horários em Brasília. Início da gameplay GTA VI: **18/11 07:49** (VOD Twitch 2932200023, 00:24:57).\n",
     f"## Twitch — clipes de GTA 6 (hoje) — {len(T)}\n", "| # | Views | Dur | Criado | ~VOD | Título | Link |", "|--|--|--|--|--|--|--|"]
for i, x in enumerate(T, 1):
    o.append(f"| {i} | {x['views']} | {fdur(x['duracao_s'])} | {x['criado_em']} | {hms(x['offset_vod_aprox_s'])} | {x['titulo'].replace('|','/')} | {x['link']} |")
for tit, L in ((f"## YouTube — pós-lançamento (18/11) — {len(pos)}", pos), (f"## YouTube — pré-lançamento (trailers, reações) — {len(pre)}", pre)):
    o += ["", tit, "", "| # | Views | Dur | Data | Origem | Título | Link |", "|--|--|--|--|--|--|--|"]
    for i, x in enumerate(L, 1):
        o.append(f"| {i} | {x['views']} | {fdur(x['duracao_s'])} | {x['data']} | {x['origem']} ({x['canal']}) | {x['titulo'].replace('|','/')} | {x['link']} |")
o += ["", "## Sem dados", "- Kick: canal sem clipes retornados pelo yt-dlp.", "- TikTok: yt-dlp não extrai o perfil sem cookies/ID.", "- Instagram: exige login (não contornado)."]
open(C + r"\catalogo.md", "w", encoding="utf-8").write("\n".join(o))
print(len(T), len(pos), len(pre))
