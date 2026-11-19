# Operação contínua (notebook Windows, 18/11/2026)

Duas filas independentes, para a captura nunca esperar a edição. Rodam no Git Bash do Windows ou no Linux.

```bash
sh scripts/operacao.sh captura   # baixa os blocos novos dos VODs do live.yaml (sem analisar), a cada 5 min
sh scripts/operacao.sh analise   # transcreve e pontua um bloco por vez, na ordem em que chegam
```

Logs em `logs/captura.log` e `logs/analise.log`. As duas retomam de onde pararam: a captura pelo `state/vods.json`, a análise pelo `candidates.json` de cada bloco. Para parar, feche o terminal ou encerre o processo; nada se perde.

## De onde vem cada transmissão

| Fonte | Como | Testado |
| --- | --- | --- |
| Kick (live em andamento ou encerrada) | VOD em HLS que cresce durante a live; segmentos baixados em paralelo e juntados sem recodificar (~5x o tempo real no notebook, 1080p60) | Sim, Davy Jones 18/11 |
| Twitch | VOD que cresce durante a live (yt-dlp por trecho) | Com yt-dlp simulado; real ainda não |
| YouTube ao vivo | **Não dá para baixar um trecho enquanto a live está no ar** ("cannot be partially downloaded"). Use a mesma live na Kick, ou o upload depois que ela terminar | Testado 18/11 |
| Live com restrição de idade (Tonyboy) | Exige login; sem cookies do notebook corporativo. Gravação manual pelo OBS | Pendente |

No `live.yaml`, `vod_from` evita baixar a parte antes do jogo, e `channel` é o nome nos créditos. Um streamer que transmite em duas plataformas entra só por uma.

### Vídeo que já está no disco (importar MP4)

Para uma live salva num arquivo (download do YouTube, blocos da Twitch, gravação local):

```bash
.venv/bin/python -m clipper --profile gta-br import "/caminho/live.mp4" --streamer "Paulinho o Loko" \
  --url "https://www.youtube.com/watch?v=cxuF5siTUQw" --vod cxuF5siTUQw \
  --started-at 2026-11-18T07:35:42-03:00 --from 1620 --no-analyze
```

- Corta em blocos de 30 min sem recodificar (`jobs/live-vod-<streamer>-<vod>-<segundo>/`), prontos para `sh scripts/operacao.sh analise` e o `/clip-br`. Sem `--no-analyze`, transcreve cada bloco logo depois de cortar.
- `--from` pula o pré-jogo (segundos). `--started-at` é o início da live: dá o horário real de cada bloco (`recorded_at`).
- **O original nunca é alterado.** O arquivo é reconhecido pelo SHA-256 completo: rodar de novo, ou importar uma cópia com outro nome, não cria bloco repetido. Se cair no meio, rode o mesmo comando: continua de onde parou.
- Cada bloco tem a checagem de sincronia de áudio e vídeo em `job.json` (`av`). Problemas aparecem em `warnings` na saída.
- Espaço: os blocos ocupam o mesmo tanto que o original (11 GB do Paulinho = +11 GB). Sem espaço livre, recusa antes de começar.
- Arquivo do Windows: `C:\Users\...` vira `/mnt/c/Users/...` no WSL. Fonte com várias trilhas de áudio (OBS): só a primeira entra, com aviso.
- `--started-at` precisa do fuso (`-03:00` ou `Z`). O mesmo arquivo não pode ser reimportado com outro `--from` ou `--chunk-minutes`: os blocos se sobreporiam.
- Se cair durante o corte, a próxima execução refaz o corte (é cópia, leva minutos); se cair depois, continua do bloco seguinte. Se a análise de um bloco falhar, `sh scripts/operacao.sh analise` pega o bloco depois. Não rode duas importações do mesmo arquivo ao mesmo tempo.
- **Autorização para publicar** fica em `profiles/gta-br/authorizations.yaml`, separada do `live.yaml`. Quem não está lá sai como `pendente` no `job.json` e nos avisos.
- Testado: suíte automática (10 testes) e um arquivo sintético de 3 min em 1080p60 pela CLI (18/11). **Ainda não testado com as gravações reais** do Paulinho e do Alanzoka.

## Armazenamento

`jobs/` e `exports/` do projeto são junções para `D:\GTA6-BR\` (disco local de 673 GB; o C: tem pouco espaço). Para recriar num notebook novo, sem admin:

```bat
mklink /J jobs D:\GTA6-BR\jobs
mklink /J exports D:\GTA6-BR\exports
```

| Pasta conceitual | Onde fica (sem cópias) |
| --- | --- |
| 01 Gravações | `jobs/live-vod-<stream>-<vod>-<segundo>/source.mp4` (um bloco de 30 min; o número é o segundo desde o início da live) |
| 02 Transcrições | `jobs/<bloco>/transcript.json` |
| 03 Momentos selecionados | `jobs/<bloco>/candidates.md` (automático) e `jobs/<bloco>/picks.json` (curadoria); catálogo editorial do dia em `exports/gta-br/<data>/momentos.md` |
| 04 Vídeos editados | `exports/gta-br/<data>/video N/` (MP4, `titles and description.md`) |
| 05 Aprovados | `state/telegram.json` (decisão do Telegram, sem copiar o vídeo) |
| 06 Publicados | ainda manual (registrar no `upload.json` do vídeo) |
| 07 Compilações | `exports/gta-br/<data>/video N/` de picks com `segments` de vários blocos ou streamers (créditos de todos na descrição) |

Nunca apague gravações originais sem aprovação. Mídia, cookies e `.env` nunca vão para o GitHub (o hook `guard.py` bloqueia).

## Continuar em outro computador

- **Código, docs e estado** (`state/*.json`, pequeno): pelo GitHub, neste branch.
- **Mídia** (`D:\GTA6-BR`): ainda local. Próximo passo, no computador pessoal: sincronizar a pasta com uma nuvem gratuita (ex.: rclone para o Google Drive da CORE 3). O notebook corporativo não acessa o Drive.
- Em outro computador, com o `state/vods.json` do GitHub, a captura continua do bloco seguinte, sem baixar de novo o que já existe.

## Recursos do notebook

i7-1360P, 16 GB, Intel Iris Xe (sem NVENC; render em `libx264 veryfast`). Começamos com uma captura e uma análise por vez. Antes de aumentar, confira CPU, RAM e disco. Em 18/11, com o VS Code e o navegador abertos, a RAM livre ficou perto de 3 GB.
