# Arquitetura em uma página

O pipeline é um CLI Python (`python3 -m clipper`) para o trabalho mecânico. O Claude Code faz o julgamento (que momento, que gancho, que layout) seguindo os comandos em `.claude/commands/`.

| Etapa | Módulo | Notas |
| --- | --- | --- |
| Fontes de upload (YouTube) | `sources.py` (`watch`, `fetch`), `__main__.daily` | filtro de tema por perfil |
| Lives ao vivo (PC ligado) | `live.py` | FFmpeg segment muxer, blocos de 30 min → jobs `live-*` |
| VODs encerrados e em andamento (Twitch, Kick) | `vods.py` | blocos → jobs `live-vod-*`; Kick por segmentos HLS em paralelo; `vod_from` no `live.yaml`; progresso em `state/vods.json` |
| Filas da operação (captura × análise) | `scripts/operacao.sh` | captura nunca espera a transcrição; uma análise por vez |
| Coletas fora do pipeline | `scripts/coleta/` | Twitch por segmentos fMP4, referências do YouTube, catálogo de clipes (sem testes) |
| Transcrição | `transcribe.py` | Parakeet v3 (onnx-asr, CPU) ou whisper.cpp |
| Sinais e candidatos | `signals.py`, `analyze.py`, `candidates.py` | volume, saltos, heatmap, palavras de empolgação, ritmo |
| Regras de gancho e título | `hooks.py`, `playbook.py`, `simulate.py` | padrões bilíngues EN/PT |
| Render | `render.py`, `captions.py`, `music.py` | FFmpeg; `encoder_args` (NVENC/x264); zoom `perspective` |
| Entrega e aprovação | `telegram.py` | Bot API via urllib; estado em `state/telegram.json` |
| Estado | `state.py` | JSON atômico em `state/` |
| Configuração | `config.py`, `watchlist.yaml`, `profiles/<perfil>/` | perfil ativo por `--profile` ou `CLIPPER_PROFILE` |

Pastas de dados (fora do git): `jobs/<id>/` (fonte, transcrição, candidatos, picks), `exports/<perfil>/<data>/video N/` (MP4, `upload.json`, títulos).

Fluxo de produção: `/clip-br` → (Telegram poll) → vods fetch / live jobs / daily → curadoria → `picks.json` → check/simulate → render → QA → telegram send.
