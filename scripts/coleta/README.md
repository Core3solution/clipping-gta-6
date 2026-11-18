# Scripts de coleta (operação 03, Alanzoka, 18/11/2026)

Escritos na sessão de coleta do Alanzoka, fora do `clipper`. Preservados aqui como estavam, só com o ffmpeg/ffprobe vindo do PATH. Não fazem parte do pipeline nem têm testes.

| Script | O que faz | Ajustar antes de rodar |
| --- | --- | --- |
| `coleta_twitch_vod.py` | Baixa um VOD da Twitch (inclusive em andamento) em blocos de 1 h, segmento por segmento (fMP4 com init), e junta sem recodificar. Retomável (`*.seg/`, `metadados/downloads.json`), uma instância por vez (lock), segue a live até ela acabar. | `BASE`, `VOD_ID`, `GTA_START`, `CHUNK`. Para retomar a coleta de 18/11, **mantenha** `VOD_ID = "2932200023"`, `GTA_START = 1497` e `CHUNK = 3600`, e apague o `logs/coleta-twitch.lock` antigo |
| `yt_refs.py` | Lista vídeos de um canal do YouTube e de buscas, e enriquece cada um com data, views e duração (`yt-dlp --print`). Retomável. | `M` (pasta de metadados), `SRC` (canal e buscas) |
| `catalogo_clipes.py` | Gera `catalogo.md`/`catalogo.json` a partir dos clipes da Twitch e do JSONL do YouTube, só GTA 6, por views. | `B`, `S0` (início do VOD em UTC), `G0` (início do capítulo GTA VI) |

Rodar no Windows: `set PYTHONIOENCODING=utf-8` e `python -u scripts\coleta\coleta_twitch_vod.py`. Dependências: Python 3.10+, yt-dlp, ffmpeg e ffprobe no PATH.

Por que um script próprio para a Twitch: o `yt-dlp --download-sections` (ffmpeg com `-ss` sobre um HLS de 9 h) não gravou nada em 4 min. A mesma técnica (segmentos em paralelo, junção byte a byte, remux) já está no `clipper/vods.py` para a Kick. Juntar os dois (Twitch com init fMP4 no `vods.py`) é trabalho futuro, ver [docs/pt-br/OPERACOES-2026-11-18.md](../../docs/pt-br/OPERACOES-2026-11-18.md).
