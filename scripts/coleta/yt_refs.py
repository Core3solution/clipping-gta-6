"""Catalogo de referencias YouTube (Alanzoka x GTA 6): lista candidatos e enriquece com yt-dlp (data, views, duracao)."""
import json, subprocess, sys, os
M = r"D:\GTA6-BR\COLETA\Alanzoka\metadados"
SRC = [("canal_videos", "https://www.youtube.com/@alanzoka/videos", 40),
       ("canal_shorts", "https://www.youtube.com/@alanzoka/shorts", 40),
       ("canal_lives", "https://www.youtube.com/@alanzoka/streams", 15),
       ("busca_gameplay", "ytsearch40:alanzoka gta 6 gameplay vice city", 40),
       ("busca_cortes", "ytsearch40:alanzoka gta 6 cortes", 40),
       ("busca_shorts", "ytsearch30:alanzoka gta 6 shorts", 30)]
seen, urls = {}, []
for name, u, n in SRC:
    r = subprocess.run(["yt-dlp", "-J", "--flat-playlist", "--no-warnings", "--playlist-end", str(n), u],
                       capture_output=True, text=True, encoding="utf-8")
    try:
        es = json.loads(r.stdout).get("entries", [])
    except Exception:
        es = []
    for e in es:
        if e and e.get("id") and e["id"] not in seen:
            seen[e["id"]] = name
            urls.append(e["id"])
    print(name, len(es), flush=True)
out = os.path.join(M, "ref_youtube_enriquecido.jsonl")
done = set()
if os.path.exists(out):
    done = {json.loads(l)["id"] for l in open(out, encoding="utf-8")}
fmt = "%(.{id,title,channel,uploader_id,upload_date,timestamp,view_count,duration,live_status,was_live,webpage_url})j"
with open(out, "a", encoding="utf-8") as f:
    for vid in urls:
        if vid in done:
            continue
        r = subprocess.run(["yt-dlp", "--skip-download", "--no-warnings", "--print", fmt, "--socket-timeout", "20",
                            f"https://www.youtube.com/watch?v={vid}"], capture_output=True, text=True, encoding="utf-8")
        for line in r.stdout.splitlines():
            try:
                d = json.loads(line); d["fonte_busca"] = seen[vid]; f.write(json.dumps(d, ensure_ascii=False) + "\n"); f.flush()
            except Exception:
                pass
print("ok", len(urls))
