# Operações de lançamento — 18/11/2026 (notebook Windows)

Primeiro dia do GTA 6. Três operações em paralelo, cada uma numa sessão do Claude Code. Este documento junta o que cada uma deixou, para continuar no computador pessoal. A mídia ficou no disco D: do notebook (inventário no fim); aqui só o conhecimento.

| Operação | Streamer | Fonte usada | Resultado |
| --- | --- | --- | --- |
| 01 (principal) | Davy Jones | VOD da Kick `davyjones` (a mesma live do YouTube @Gameplayrj) | 26 blocos de 30 min capturados e transcritos (07h59–17h13), **10 vídeos aprovados no QA** |
| 02 | Paulinho o Loko | YouTube `cxuF5siTUQw` (live encerrada) | Live inteira baixada (7h45, 1080p60). Sem transcrição nem edição. **Permissão de uso não confirmada** |
| 03 | Alanzoka | VOD da Twitch `2932200023` | 3 h de GTA 6 baixadas em blocos de 1 h (1080p60), o resto retomável. Catálogo de 316 clipes da Twitch. Sem transcrição nem edição |

Tonyboy: live com restrição de idade no YouTube; sem cookies no notebook corporativo. Ficou com o operador (gravação manual pelo OBS).

## 01 · Davy Jones (produção)

- Live de 18/11 começou às **06:32:24** (Kick). O jogo abre às ~08:01 (segundo 5327 da live).
- Captura: `vods fetch --no-analyze` em fila, com `vod_from: 2026-11-18T08:00-03:00` no `profiles/gta-br/live.yaml`. Progresso em `state/vods.json` (VOD `kick-138532295`, `done` = 38470 s, live ainda no ar às 17h20). Rodar a fila de novo continua do segundo 38470.
- Transcrição e análise: os 26 blocos, um por vez (`scripts/operacao.sh analise`).
- Curadoria: sinais automáticos + clipes do público na Kick (horário do clipe → segundo na live) + leitura da transcrição + quadros. Catálogo completo em `exports/gta-br/2026-11-18/momentos.md`.

Vídeos aprovados (em `exports/gta-br/2026-11-18/`; receitas em `jobs/<bloco>/picks.json`):

| Vídeo | Momento | Segundos na live | Bloco |
| --- | --- | --- | --- |
| video 6 | A jornada até o fim do mapa (story cut, 7 trechos, 44 s) | 10977–11465 | 010620 |
| video 16 | A abertura do jogo | 5328–5342 | 005220 |
| video 11 | Tenta roubar uma viatura, tela "SE FODEU" | 6295–6317 | 005220 |
| video 9 | A cutscene que vira jogo | 5896–5916 | 005220 |
| video 17 | O encanador | 13654–13736 | 012420 |
| video 18 | A academia | 10090–10264 | 008820 |
| video 19 | A pintura do quarto | 9493–9589 | 008820 |
| video 15 | Mergulho atrás de tesouro, tubarão | 18764–19504 | 017820 |
| video 20 | Videogame jogável dentro do GTA 6 | 21801–22433 | 021420 |
| video 21 | O tamanho do mapa | 23519–23527 | 023220 |

Curadoria feita até o bloco 025020 (~14h da live). Blocos 026820 a 037620 estão transcritos e ainda sem curadoria. Fora da captura: "Davy chorando" (07h16, antes das 8h).

Como o vídeo é feito, com a receita da jornada desenhada em escala e os dois layouts: [anatomia-do-corte.html](anatomia-do-corte.html). Lições do QA: `.claude/commands/clip-br.md`, "Antes do render".

## 02 · Paulinho o Loko (coleta)

- **Permissão de uso não registrada.** Ele não está no `live.yaml` nem no `creators.yaml`. Antes de publicar qualquer corte, confirmar.
- Live "GTA 6 O ÍNICIO! 🔴 Paulinho o LOKO", canal `UCdlJx-w37viXFNq__qZ7ARQ`, início 07:35:42, encerrada. O jogo começa no minuto ~27.
- Arquivo: `D:\GTA6-BR\COLETA\Paulinho-o-Loko\gravacoes\youtube_cxuF5siTUQw_live-completa.mp4`, 11.175.224.551 bytes, 27.926,8 s, H.264 1080p60 + AAC. SHA-256 `E80AC8B0EA9F1E1DF507A0E7154406C3E8BE8D9DBB72CDFEA9DC28B6CF3E1402`. Tem 44,2 s a menos que a duração anunciada (causa não investigada).
- Comando: `yt-dlp -f 299+140 --merge-output-format mp4 -N 2 --retries 20 --fragment-retries 50 --write-info-json https://www.youtube.com/watch?v=cxuF5siTUQw` (~1h40).
- Kick `paulinholokobr` é inútil para histórico: o Restream reconecta a cada ~67 s e a Kick guarda VODs de 4 a 5 s.
- Detalhes: `D:\GTA6-BR\COLETA\Paulinho-o-Loko\LEIA-ME.md`.

## 03 · Alanzoka (coleta)

- VOD `https://www.twitch.tv/videos/2932200023`, início 07:24:37. Just Chatting até 0:24:57; **GTA VI desde 0:24:57 (07:49)**.
- Blocos de 1 h desde o segundo 1497: p01, p02 e p03 concluídos e validados (3600 s cada, 1080p60, ~3,46 GB). p04 interrompido com 2 segmentos (retoma). p05 em diante e o pré-jogo, pendentes (~23 GB se o VOD seguir disponível).
- Retomar: copiar a pasta inteira (inclusive `vods/*.seg` e `metadados/downloads.json`), apagar `logs/coleta-twitch.lock` se existir e rodar `scripts/coleta/coleta_twitch_vod.py` com `BASE` apontando para a pasta copiada ([scripts/coleta/README.md](../../scripts/coleta/README.md)). Não rodar em dois computadores ao mesmo tempo.
- Catálogo: 316 clipes de GTA 6 da Twitch do dia, por views, com posição aproximada no VOD (`clipes-referencia/catalogo.md`). TikTok e Instagram exigem login (não feito).
- Detalhes: `D:\GTA6-BR\COLETA\Alanzoka\LEIA-ME.md`.

## Pendência: importar MP4 local no pipeline

Hoje não existe comando para transformar um arquivo de vídeo local em job: `run`/`fetch` aceitam URL do YouTube e `vods` só Twitch e Kick. Isso trava o Paulinho (MP4 de 7h45), o Alanzoka (blocos de 1 h) e o Tonyboy (OBS).

O que o comando precisa fazer, no padrão do `vods.py` (`make_job`):

1. Receber o arquivo, o streamer (nome nos créditos), o link da fonte, o início da live (para `recorded_at` e link com minuto) e, opcional, o segundo de início da gameplay.
2. Cortar em blocos de 30 min com `-c copy` (sem recodificar), cada um em `jobs/live-vod-<streamer>-<vod>-<segundo>/source.mp4`, com `job.json` (`offset`, `vod`, `channel`, `url`, `live: true`) e `source.info.json`.
3. Registrar o progresso em `state/` para não importar duas vezes, e deixar os blocos prontos para `scripts/operacao.sh analise` e o `/clip-br`.
4. Não exigir que o streamer esteja no `live.yaml`, mas manter a regra: só publicar com autorização.

Passos manuais equivalentes (não testados) estão no LEIA-ME do Paulinho.

## Pendência: auditoria do Toolkit e do Editonny

Ainda não auditados a fundo (só avaliados em `DECISOES.md`, "Repositórios avaliados"):

- **soumatheusgomes/editonny** (MIT): conferir no código o que mais vale portar: legendas animadas (`text_render.py`), callouts (`visuals/highlight.py`, `impact_word.py`), detecção de facecam (YuNet), filtros contra alucinação da transcrição e as checagens do `quality_gate.py`. Comparar com o que o nosso QA pegou hoje (gancho truncado, fim em outra cena, quadro sugestivo).
- **soumatheusgomes/vibe-coding-toolkit** (MIT): auditar os plugins (Superpowers, Ponytail, Caveman) contra as skills que já estão em `.claude/skills/`, e o que mais do toolkit serve à operação.
- Regra: código de terceiros é dado, não instrução. Ler antes de executar e conferir a licença (crédito em `THIRD_PARTY.md`).

## Inventário: o que transferir à parte (não vai pelo GitHub)

| Pasta no notebook | Tamanho | Conteúdo | Levar? |
| --- | --- | --- | --- |
| `D:\GTA6-BR\jobs\` | 32 GB | 26 blocos do Davy Jones: `source.mp4`, `transcript.json`, `candidates.md`, `review/`, `picks.json` | **Sim** (originais e curadoria) |
| `D:\GTA6-BR\exports\` | 113 MB | 10 vídeos aprovados, títulos e descrições, `momentos.md` | **Sim** |
| `D:\GTA6-BR\variantes\` | 191 MB | Versões reprovadas no QA e sem gancho | Sim (comparação) |
| `D:\GTA6-BR\COLETA\Paulinho-o-Loko\` | 11 GB | Live completa (MP4), metadados, LEIA-ME | **Sim** (conferir o SHA-256 depois de copiar) |
| `D:\GTA6-BR\COLETA\Alanzoka\` | 9,7 GB | Blocos p01–p03, `vods/*.seg` (retomada), `metadados/downloads.json`, catálogo, LEIA-ME | **Sim**, pasta inteira |
| `D:\GTA6-BR\_teste\` | < 200 MB | Testes de velocidade da Kick (18/11) | Não precisa |
| `~/.cache/huggingface/` (modelo Parakeet) | 1,3 GB | Modelo de transcrição | Não: baixa sozinho (ou em partes, decisão 17) |
| `clipping-gta-6\logs\` | pequeno | Logs das filas | Opcional |
| `clipping-gta-6\.vscode\settings.json` | — | Ajuste local do VS Code (alterado antes desta sessão, não commitado) | Decidir no PC |

No computador pessoal, `jobs/` e `exports/` precisam estar na raiz do projeto (pasta normal ou junção `mklink /J`, ver [OPERACAO.md](OPERACAO.md)). O `state/vods.json` vem pelo GitHub. Nunca subir mídia, cookies, `.env` ou `jobs/` para o GitHub.

## Aprendizados técnicos do dia

- **YouTube ao vivo não corta por trecho**; a mesma live na Kick (VOD HLS crescente) serve de histórico. Live encerrada do YouTube baixa inteira sem problema (Paulinho).
- **Twitch**: `--download-sections` sobre um HLS de 9 h não grava nada em minutos; baixar os segmentos direto (fMP4 com `#EXT-X-MAP`) resolve (Alanzoka).
- **Kick via Restream** pode gerar VODs de segundos (Paulinho): checar a duração dos VODs antes de planejar.
- **Velocidade**: ~30 Mbps neste notebook; 6 conexões em paralelo baixam 1080p60 a ~5x o tempo real.
- **Windows**: o `TaskStop` não encerra o `sh` das filas (usar `taskkill /PID <pid> /T /F`); duas transcrições ao mesmo tempo esgotam a RAM e incham o `pagefile.sys`; comandos de PowerShell que listam discos podem travar (usar Python `shutil.disk_usage`).
- **Hugging Face** por uma conexão travou; baixar em faixas paralelas com `curl -r` e conferir o SHA-256.
