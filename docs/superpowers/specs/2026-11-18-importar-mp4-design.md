# Importar MP4 local: design curto

Aprovado pelo usuário em 18/11/2026. Etapa 1 da [auditoria](../../pt-br/AUDITORIA-2026-11-18.md).

**Por quê:** as gravações do Paulinho o Loko (MP4 de 7h45 do YouTube) e do Alanzoka (blocos de 1 h da Twitch) estão em arquivos locais, e o pipeline só aceita URL. Sem importar, elas não entram na fila de transcrição nem no `/clip-br`.

**Objetivo:** `clipper import <arquivo>` corta o vídeo em blocos de 30 min sem recodificar. Cada bloco vira um job `jobs/live-vod-<streamer>-<vod>-<segundo>/`, igual aos do `vods.py`, que a fila `scripts/operacao.sh analise` e o `live jobs` já reconhecem.

**Fora do escopo:** chat (etapa 4), mudanças no render e qualquer publicação.

**Não pode acontecer:**
- Alterar ou mover o arquivo original.
- Criar o mesmo bloco duas vezes.
- Gravar offset errado (o horário real do momento na live).
- Bloco com áudio fora de sincronia passar sem aviso.
- Tratar a presença no `live.yaml` como autorização para publicar.

## Abordagens consideradas

| Abordagem | Troca | Escolha |
| --- | --- | --- |
| **Uma passada do segment muxer** (`-c copy -f segment -segment_times`, lista CSV com início e fim reais) | Corta em keyframe; a lista CSV dá o tempo absoluto de cada bloco. Determinística: rodar de novo gera os mesmos blocos. | **Sim** (testado num spike: offsets absolutos, A/V alinhados) |
| `-ss`/`-t` por bloco com `-c copy` | Retomar é trivial, mas o corte cai no keyframe anterior: blocos sobrepostos e áudio começando antes do vídeo | Não |
| Recodificar cada bloco | Corte exato, mas lento (7h45 de 1080p60) e perde qualidade | Não |

## Design

- **Identidade:** SHA-256 completo + tamanho + duração (ffprobe). O hash fica em cache por caminho + tamanho + `mtime_ns` em `state/imports.json`, para não ser recalculado ao retomar.
- **Retomar sem duplicar:** a chave da importação é o SHA-256. O id do job é determinístico (`vod` + segundo de início). Bloco já registrado ou com `source.mp4` no lugar é pulado. A segmentação vai para `jobs/.import-<sha12>/` e só vale com o marcador `segmented`; se faltar, refaz do zero (é cópia, leva minutos). Cada bloco é movido com `os.replace` (mesmo disco, sem cópia extra), e o estado é salvo depois de cada bloco.
- **Timestamps:** `offset` = início do bloco na lista CSV menos o `start_time` da fonte. `recorded_at` = `--started-at` + `offset`. `--from` (início da gameplay) entra como primeiro ponto de corte, e o trecho anterior é descartado.
- **Sincronia A/V:** por bloco, ffprobe dos streams. Diferença de início > 0,1 s ou de fim > 0,5 s marca `av.ok = false` no `job.json` e entra nos avisos da saída. A fonte também é checada.
- **Autorização:** registro próprio em `profiles/<perfil>/authorizations.yaml` (`status: autorizado | pendente | negado`, `evidencia`, `data`). O `job.json` recebe `authorization`. Quem não está no arquivo fica `pendente`. A importação nunca é bloqueada; publicar continua sendo decisão humana.
- **Original preservado:** só leitura. O teste confere que o SHA-256 e o arquivo continuam iguais.

Decisões minhas (o builder pode ajustar): `vod` padrão = 12 primeiros caracteres do SHA-256; o último bloco fica mesmo se for curto; a análise roda por padrão, como no `vods fetch` (`--no-analyze` para a fila).
