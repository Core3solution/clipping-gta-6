# Encerramento de 18/11/2026: auditoria, consolidação e retomada

Escrito no PC (WSL2) às ~00h de 19/11, depois de encerradas as sessões do dia. **Fonte oficial do estado do projeto a partir de agora** (junto com o `HANDOFF.md`). Nada foi implementado nesta auditoria: as melhorias abaixo são **pendências à espera de aprovação**.

Marcação: **[F]** fato verificado por arquivo ou comando; **[H]** hipótese, não medida.

## 1. O que aconteceu em 18/11 (quatro frentes)

| Frente | Máquina | Sessão | Resultado real |
| --- | --- | --- | --- |
| Produção Davy Jones (+ coleta Paulinho live 1 e Alanzoka) | Notebook Windows | 3 operações de dia | 26 blocos capturados e transcritos; **10 vídeos renderizados e aprovados no QA automático/IA**. Não revisados pelo usuário, não publicados, não enviados ao Telegram [F: OPERACOES-2026-11-18.md] |
| Chat 01: desenvolvimento | PC, worktree `../clipping-gta-6-dev`, branch `dev/fase02` | 1 | `clipper import`, checagens `hook_fit`/`cut_edges`/`end_scene`, `clipper qa`. 229 testes verdes. **Nada testado com material real** [F] |
| Chat 02: Paulinho, live 2 (`X2rtbJJEvVE`) | PC | 1 | Captura ao vivo com script próprio; 21 jobs transcritos e analisados; catálogo e 4 candidatos (A–D). **0 vídeos editados** [F: `jobs/curadoria-paulinho.md`] |
| Chat 03: recuperação de gravações | PC, `COLETA/` | 1 | Paulinho live 1 baixada **de novo** (12,4 GB) e picos de volume; Alanzoka: 9 trechos + catálogo de 22 momentos. **0 vídeos** [F: `COLETA/LEIAME-RETOMADA.md`] |
| Chat 04: laboratório Editonny | PC, `~/Projetos/editonny-lab/` | 1 | Editonny instalado isolado; cartão de 5 shorts do Alanzoka aprovado; 5 versões verticais e o workspace + transcrição do V3. **0 vídeos cortados ou renderizados** [F: pasta `renders/` vazia] |

**Vídeos finalizados no dia: 10 (Davy Jones), todos aguardando a revisão do usuário.** Material preparado, mas não finalizado: 5 verticais do Alanzoka (Editonny) e 4 candidatos do Paulinho live 2.

## 2. Matriz de estado

| Item | Existe | Funciona | Testado | Situação |
| --- | --- | --- | --- | --- |
| Pipeline `clipper` (captura VOD, transcrição, candidatos, render) | Sim | Sim | Suíte + produção real no notebook | **Em produção** |
| `scripts/operacao.sh` (filas captura × análise) | Sim | Sim | Produção real (notebook) | Em produção |
| `clipper import` (MP4 local → blocos) | Sim, só em `dev/fase02` | Em teste sintético | Unitários + arquivo sintético de 3 min | **Incompleto: falta material real** |
| `check` determinístico e `clipper qa` | Sim, só em `dev/fase02` | Em teste sintético | Unitários; `qa` num render real | Incompleto: falta produção real; limiar de cena 0,4 pode dar falso positivo |
| `scripts/captura_youtube.sh` + `blocos_youtube.py` | Sim (commit hoje) | Sim, com falhas | Uso real por ~3 h (Paulinho live 2) | **Experimental**: lacunas por TLS/DNS, sem supervisor externo |
| `scripts/coleta/` (Twitch fMP4, refs YouTube, catálogo) | Sim | Sim | Uso real no notebook | Experimental, sem testes |
| `COLETA/_scripts/` | Sim, fora do git | Parcial | Alanzoka: recriados e **não reexecutados**; Paulinho: transcrição não concluiu nem um bloco | Experimental, caminhos fixos de `/home/gustavo` |
| Laboratório Editonny | Sim, fora do repo | `doctor` ok, smoke sintético ok | Nenhum vídeo real até o fim | **Experimental** |
| `telegram.py` | Sim | Desconhecido | Só unitários; sem bot criado | Incompleto |
| Nuvem com o PC desligado (`NUVEM.md`) | Só doc | Não | Não | **Ideia** |
| Sinal de chat, download seletivo, legendas animadas, YuNet, transcrição na GPU, resumo compacto para curadoria | Não | — | — | **Ideias** (AUDITORIA §7) |

## 3. Auditoria técnica

### 3.1 Arquitetura e pastas
- O núcleo (`clipper/`, 6.373 linhas em `dev/fase02`) é coeso e coberto por testes [F]. Os módulos do upstream que o gta-br não usa (`dub`, `tts`, `voice_setup`, `speakers`, ~800 linhas) ficam: a regra é não mudar o comportamento original.
- **Crescimento fora do núcleo** é onde está a complexidade: `scripts/coleta/` (3), `scripts/` (captura YouTube, 2), `COLETA/_scripts/` (8), `editonny-lab/producao/` (6). São 19 scripts soltos, sem testes, vários com caminhos absolutos [F].
- **Funções duplicadas** [F]:

| Função | Implementações hoje |
| --- | --- |
| Captura ao vivo | `live.py` · `scripts/captura_youtube.sh` (o `live.record()` falha sem formato muxado no YouTube) |
| VOD da Twitch | `vods.py` · `scripts/coleta/coleta_twitch_vod.py` (segmentos fMP4) · `COLETA/_scripts/alanzoka_fila.py` (usa o anterior) |
| Arquivo local → transcrição | `clipper import` (dev) · `paulinho_transcreve.py` · `alanzoka_audio_transcreve.py` |
| Layout vertical facecam + jogo | `render.py` (`split`) · `editonny-lab/producao/vertical.py` |
| Achar a facecam | `clipper frame` (manual) · `editonny-lab/producao/camloc.py` (modelo, normal e espelhado) |
| QA do vídeo | `clipper qa` (dev) · `quality_gate.py` do Editonny · agente `qa-video` |

### 3.2 Dependências e stack
- Python 3.12 + uv (lockfile), FFmpeg, yt-dlp, Parakeet v3 (`onnx-asr`, CPU). Stack adequada e gratuita [F].
- O Editonny traz outra stack inteira (Node 24, Chrome headless/HyperFrames, Whisper large-v3-turbo, Tesseract): 4,5 GB, isolada fora do repo [F]. Não entra no `pyproject`.

### 3.3 GPU, CPU, RAM e disco
| Recurso | Fato | Pendência |
| --- | --- | --- |
| Transcrição | Parakeet só CPU: ~15–20 min por bloco de 30 min no notebook [F]. Whisper do Editonny: 190 s de áudio em 498 s na CPU [F] | Medir `onnxruntime-gpu` (Parakeet CUDA) e faster-whisper CUDA num bloco real antes de escolher [H: 10× mais rápido] |
| Render | NVENC já usado no encode; filtros (blur 1080×1920) na CPU [F]. Editonny renderiza com CPU + Chrome, sem NVENC [F] | Blur em baixa resolução; NVDEC [H] |
| RAM | WSL enxerga 7,7 GiB dos 16 GB; sem `.wslconfig` [F]. Com 4 sessões e transcrições juntas, carga 20–28 em 12 threads [F: LEIAME-RETOMADA] | `.wslconfig memory=12GB` (adiado pelo usuário) |
| Disco PC | C: ~275 GB livres; projeto usa 6,5 GB `jobs/` + 16 GB `COLETA/` + 2,1 GB `exports/` + 4,5 GB lab [F]. O VHDX do WSL não encolhe sozinho | Download seletivo [H] |
| Notebook | ~53 GB no D:; duas transcrições juntas esgotam a RAM [F] | Uma análise por vez (já é regra) |

### 3.4 Recuperação após falhas
- **Bom:** `vods.py` retoma por `state/vods.json`; Alanzoka retoma por `downloads.json`; `clipper import` retoma sem duplicar (dev) [F].
- **Fraco** [F]:
  - a captura do YouTube não tem supervisor: uma falha de DNS derrubou captura e loop de blocos por ~8 min sem ninguém notar;
  - tarefas em segundo plano morrem com a sessão do Claude (usar `setsid nohup`);
  - o scratchpad em `/tmp` foi apagado num reinício e scripts tiveram de ser recriados;
  - **o cartão aprovado do Editonny só existe no log da sessão do Claude** (`~/.claude/projects/.../3dd77db1-....jsonl`). Se o log sumir, o `mkconf.py` quebra.

### 3.5 Tokens
- O maior gasto é por desenho: transcrição palavra por palavra lida com Grep/Read e QA por quadros via IA (27 renders para 10 vídeos) [F: AUDITORIA]. `dev/fase02` já ataca o QA (checagens antes do render).
- Quatro sessões grandes em paralelo (logs de 2 a 10 MB cada) [F].
- O hook do RTK reescreve comandos `Bash`; no modo automático isso fez várias chamadas voltarem para reenvio nesta sessão [F]. Custa turnos.
- O `verify_on_stop` roda a suíte inteira (~90 s) em cada parada com `.py` alterado, inclusive em sessões de produção que só mexem em scripts [F].

### 3.6 Skills, hooks, agentes, Superpowers e Ponytail
| Item | Uso medido nos logs do PC (18/11) [F] |
| --- | --- |
| Superpowers | Só o Chat 01 (dev) usou: worktrees, brainstorming, writing-plans, TDD, receiving-code-review. As 4 sessões de operação: 0 (correto: a regra 02 dispensa em produção) |
| Ponytail | `ponytail-review` 1× (Chat 01) |
| Agentes | `revisor` 2× (dev e sessão anterior); `qa-video` usado no notebook; `explorador` e `depurador`: 0 |
| Hooks | `guard`, `session_context`, `verify_on_stop` ativos. O `session_context` injeta os "Próximos passos" do HANDOFF: se o HANDOFF estiver velho, a sessão começa errada |
- **Ponytail na prática:** o núcleo segue o princípio (mudanças aditivas, sem dependência nova). Fora dele não: 19 scripts ad hoc e uma segunda stack de edição inteira (Editonny) cresceram sem passar pela pergunta "o `clipper` já faz isso?".

### 3.7 Segurança, licenças e direitos
- Nenhum segredo, cookie ou mídia no git [F: varredura dos arquivos deste commit; `.gitignore` cobre `.env`, `jobs/`, `exports/`, `logs/`; `COLETA/` está em `.git/info/exclude`].
- Base AGPL-3.0; Editonny MIT (lab fora do repo; crédito no `THIRD_PARTY.md` só se portar código); Clipador de Live sem licença: **não copiar** [F].
- `COLETA/_scripts/clipes_twitch_gql.py` usa o Client-ID público do site da Twitch (o mesmo do yt-dlp). Não é segredo, mas é uso não oficial da API.
- **Autorização de publicação:** `profiles/gta-br/authorizations.yaml` (dev) está vazio. Pela regra, **todos os streamers estão "pendente"**, inclusive o Davy Jones dos 10 vídeos [F].
- **Música:** o Paulinho disse na live que um vídeo dele caiu por música do jogo. Todo corte precisa de checagem da rádio do jogo (Content ID) antes de publicar.

## 4. Inteligência e contexto

| Pergunta | Resposta |
| --- | --- |
| Instruções conflitantes? | **Sim, 4** [F]: (1) o HANDOFF da `ptbr` manda "implementar a importação de MP4", que já existe na `dev/fase02`; (2) `DECISOES.md` nº 8 diz "Editonny só técnicas isoladas", mas o usuário decidiu testar o Editonny completo (AUDITORIA, decisões do usuário) e ele foi instalado; (3) a AUDITORIA diz "Editonny não está instalado" e "0 chamadas de skill", ambos superados no mesmo dia; (4) três jeitos de rodar os testes (`uv run`, `python3`, `.venv/bin/python`) entre AGENTS.md, regra 02 e HANDOFF |
| Documentos redundantes ou velhos? | Dois HANDOFFs divergentes (um por branch). `anatomia-do-corte.html` diz 24 blocos; o certo é 26. Estado de retomada espalhado em 5 arquivos, 3 deles fora do git (`COLETA/LEIAME-RETOMADA.md`, `jobs/OPERACAO-PAULINHO-ENCERRAMENTO.md`, `editonny-lab/producao/RETOMAR.md`) |
| Os agentes usam as skills? | Em desenvolvimento, sim (Chat 01). Em produção, não, e é o esperado |
| Existe fonte oficial? | Agora: `HANDOFF.md` + este documento + `DECISOES.md`. Os arquivos fora do git são detalhes locais |
| Sessões duplicando trabalho? | **Sim** [F]: a live 1 do Paulinho (`cxuF5siTUQw`) foi baixada duas vezes (notebook 11,2 GB, SHA-256 conhecido; PC 12,4 GB, formato diferente); transcrição por blocos implementada 3 vezes; detecção de facecam e layout vertical em paralelo ao `clipper` |
| Decisões sem evidência? | Poucas, e marcadas: ganhos de GPU, falsos positivos do limiar de cena e o "melhor" do YuNet são [H]. As candidatas do Paulinho têm tempo com ±20 s de incerteza (dito no arquivo) |
| Dá para retomar em outro computador sem as conversas? | **Código e decisões, sim** (GitHub). **Não** para: o cartão aprovado do Editonny (só no log da sessão), as curadorias do Paulinho e do Alanzoka (fora do git, só no PC) e a mídia (cada máquina tem a sua). Ver §7 |

## 5. Diagnóstico por componente

| Componente | Classe | Motivo |
| --- | --- | --- |
| `clipper/` núcleo (vods, analyze, candidates, hooks, simulate, state) | **Manter** | Em produção, testado |
| `captions.py` / `render.py` (visual) | **Otimizar** | Legenda estática, gancho de 88 px no vídeo todo, jogo em 32% da altura no `fit` [F: AUDITORIA §3] |
| `transcribe.py` | **Investigar** | CPU-only; medir GPU antes de mudar |
| `live.py` | **Otimizar** | Falha no YouTube sem formato muxado; absorver a captura separada de vídeo+áudio |
| Módulos upstream não usados (`dub`, `tts`, `voice_setup`, `speakers`) | **Manter** | Regra de preservar o original |
| `telegram.py` | **Investigar** | Nunca testado com bot real |
| `imports.py`, `qa.py`, checagens (dev) | **Manter** e **Investigar** | Testar com o Paulinho e o Alanzoka antes de mesclar |
| `scripts/operacao.sh` | **Manter** | Em uso |
| `scripts/captura_youtube.sh`, `blocos_youtube.py` | **Otimizar** | Supervisor externo; o `900` fixo no `blocos_youtube.py` presume blocos de 15 min (quebra se `MINUTOS` mudar); limiar do watchdog |
| `scripts/coleta/coleta_twitch_vod.py` | **Substituir** (depois) | Duplica o `vods.py`; portar a técnica fMP4 para lá |
| `scripts/coleta/catalogo_clipes.py`, `yt_refs.py` | **Manter** | Pequenos, úteis |
| `scripts/devkit/`, `scripts/cloud-setup.sh` | **Investigar** | Sem uso registrado em 18/11 |
| `COLETA/_scripts/paulinho_transcreve.py`, `alanzoka_audio_transcreve.py` | **Substituir** | Pelo `clipper import` + `analyze` |
| `COLETA/_scripts/paulinho_rms.sh` + `paulinho_picos_volume.py` | **Investigar** | Base pronta da "triagem por áudio" (etapa 5 da AUDITORIA) |
| `COLETA/_scripts/clipes_twitch_gql.py` | **Otimizar** | Generalizar o canal (hoje fixo em `alanzoka`) e levar para `scripts/coleta/` |
| `COLETA/_scripts/alanzoka_fila.py`, `alanzoka_gera_catalogo.py`, `paulinho_valida.sh` | **Manter local** | Uso único; não vão ao git |
| Laboratório Editonny | **Investigar** | Decidir só depois de um vídeo pronto comparado com o do `clipper` |
| `producao/vertical.py`, `camloc.py` | **Investigar** | Candidatos a portar para o `clipper` (layout empilhado + facecam automática) |
| Clipador de Live | **Remover** (não instalar) | Sem licença |
| Superpowers, Ponytail, agentes | **Manter** | Custo baixo; usados no dev |
| Hook `verify_on_stop` | **Otimizar** | Rodar só quando `clipper/` ou `tests/` mudarem |
| Hook RTK no modo automático | **Investigar** | Reenvios de chamadas |
| HANDOFF duplicado por branch | **Otimizar** | Unificar ao mesclar `dev/fase02` |
| `DECISOES.md` nº 8, AUDITORIA, anatomia | **Otimizar** | Atualizar os trechos superados (§4) |

## 6. Pendências (nada implementado; aguardam aprovação)

| P | Pendência | Impacto | Esforço | Evidência |
| --- | --- | --- | --- | --- |
| **P0** | **Autorizações**: registrar em `authorizations.yaml` Davy, Paulinho, Alanzoka e Tonyboy (usuário) | Bloqueia toda publicação | Baixo | Arquivo vazio [F] |
| **P0** | Revisar os 10 vídeos do Davy e checar música do jogo | Única produção pronta | Baixo | OPERACOES [F] |
| **P0** | Salvar o cartão aprovado do Editonny num arquivo em `producao/` (sair do log da sessão) | Evita perder a aprovação | Baixo | RETOMAR.md §1 [F] |
| P1 | Decidir quando mesclar `dev/fase02` → `ptbr` (merge simples; conflito trivial só no HANDOFF) | Libera `import`, `check` e `qa` na produção | Baixo | 229 testes [F] |
| P1 | Testar `clipper import` com Paulinho live 1 e Alanzoka | Destrava 2 streamers | Médio | Sem teste real [F] |
| P1 | Recuperar as lacunas do Paulinho live 2 pelo VOD | Completa o material | Médio | Tabela em `jobs/OPERACAO-PAULINHO-ENCERRAMENTO.md` |
| P1 | Escolher uma cópia da live 1 do Paulinho (notebook ou PC) e apagar a outra **com aprovação** | 11–12 GB | Baixo | Duas cópias [F] |
| P2 | Benchmark de transcrição CPU × GPU num bloco real | Tempo 10× [H] | Médio | AUDITORIA §5 |
| P2 | Supervisor da captura do YouTube e `900` derivado de `MINUTOS` | Menos lacunas | Baixo | Falhas 5 e 6 do encerramento do Paulinho |
| P2 | Visual: legendas animadas, gancho menor e por tempo, layout empilhado com facecam automática | Qualidade | Alto | AUDITORIA §3; Editonny |
| P2 | `verify_on_stop` restrito a `clipper/`/`tests/` | Tempo e tokens | Baixo | §3.5 |
| P2 | Corrigir os 4 conflitos de instrução (§4) | Contexto | Baixo | §4 |
| P3 | Portar a técnica fMP4 da Twitch para o `vods.py`; triagem por áudio + download seletivo; sinal de chat | Disco e escala | Alto | AUDITORIA §4 e §7 |
| P3 | Telegram real; depois nuvem | Operação sem PC | Médio | Sem bot [F] |
| P3 | `.wslconfig memory=12GB` | RAM | Baixo | Adiado pelo usuário |

## 7. Proposta de arquitetura mais enxuta (não implementada)

Um caminho só, com o `clipper` como dono de cada etapa. Os scripts soltos viram subcomandos ou são apagados quando o subcomando existir e estiver testado.

```
ENTRADA     vods.py (Kick/Twitch, + técnica fMP4)  ·  live.py (+ vídeo e áudio separados do YouTube)  ·  clipper import (MP4 local)
              ↓  todos geram jobs live-vod-* no mesmo formato, com estado em state/
TRIAGEM     sinais + picos de volume (ideia do paulinho_rms) + clipes do público → janelas
TRANSCRIÇÃO Parakeet (GPU opcional, depois do benchmark)
CURADORIA   Claude, com resumo compacto por candidato
CHECAGEM    clipper check (hook_fit, cut_edges, end_scene)
RENDER      clipper render (layouts do clipper; técnicas do Editonny portadas só se vencerem a comparação)
QA          clipper qa → qa-video só na folha de contato
ENTREGA     telegram.py → aprovação humana → publicação manual
```

O Editonny fica como laboratório de referência até a comparação lado a lado. Uma stack só em produção.

## 8. Onde está cada material

| Material | Notebook Windows (`D:\GTA6-BR`) | PC (WSL) | GitHub |
| --- | --- | --- | --- |
| Código, docs, decisões, `state/vods.json` | clone | clone | **Sim** (`ptbr-operacao-lancamento`) |
| `clipper import`, `check`, `qa` | — | worktree `../clipping-gta-6-dev` | **Sim** (`dev/fase02`, desde hoje) |
| Davy Jones: 26 blocos (32 GB), 10 vídeos, variantes, `momentos.md` | **Só aqui** | — | Não |
| Paulinho live 1 `cxuF5siTUQw` | Sim (11,2 GB, SHA-256 no OPERACOES) | Sim (12,4 GB, outra cópia) + picos de volume | Não |
| Paulinho live 2 `X2rtbJJEvVE`: 21 jobs, brutos, curadoria (A–D), encerramento | — | **Só aqui** (`jobs/`, 6,5 GB) | Não |
| Alanzoka: blocos p01–p03 (9,7 GB) + catálogo de 316 clipes | **Só aqui** | — | Não |
| Alanzoka: 9 trechos, catálogo de 22 momentos, transcrições, 72 clipes GQL | — | **Só aqui** (`COLETA/`, 3,6 GB) | Não |
| Editonny: lab, 5 verticais, workspace V3, cartão aprovado | — | **Só aqui** (lab 4,5 GB; `exports/editonny` 2,1 GB; cartão no log da sessão) | Não |
| Modelos (Parakeet, Whisper), caches, `.venv` | próprios | próprios | Não (baixam de novo) |

## 9. Retomada

Prioridade de 19/11: **produzir vídeos**, não ferramentas. Nenhuma pendência da §6 entra sem aprovação.

### Notebook Windows (primeiro)
1. `git pull` na `ptbr-operacao-lancamento`. Testes: `.venv/Scripts/python.exe -m unittest discover -s tests`.
2. Revisar os 10 vídeos do Davy em `exports/gta-br/2026-11-18/` e decidir publicar ou refazer (música do jogo; autorização do Davy).
3. Produção: curadoria dos blocos `026820`–`037620` do Davy com `/clip-br` (já transcritos). Se o VOD da Kick ainda existir, `sh scripts/operacao.sh captura` continua do segundo 38470.
4. Commit com `git -c user.name=Claude -c user.email=noreply@anthropic.com commit ...` (decisão 20); push só com aprovação.

### PC Ubuntu/WSL (depois)
1. `git pull`. Testes: `.venv/bin/python -m unittest discover -s tests`. Push pelo GCM (comando no HANDOFF).
2. **Alanzoka no Editonny:** seguir `~/Projetos/editonny-lab/producao/RETOMAR.md`, começando pelo V3 (já transcrito). Antes, salvar o cartão aprovado num arquivo (P0).
3. **Paulinho live 2:** os candidatos A–D estão em `jobs/curadoria-paulinho.md`; render só depois de checar a música do jogo. Publicação só com autorização.
4. **Paulinho live 1 / Alanzoka trechos:** só depois de aprovar o merge da `dev/fase02` (P1), usar `clipper import`. Até lá, nada de novos scripts.
5. Não rodar duas transcrições ao mesmo tempo (RAM de 7,7 GiB no WSL).

### Para levar mídia entre as máquinas
Inventário e regras: [OPERACOES-2026-11-18.md](OPERACOES-2026-11-18.md), seção "Inventário". `jobs/` e `exports/` na raiz do projeto. Conferir o SHA-256 da live 1 do Paulinho depois de copiar. Nunca subir mídia, cookies ou `.env` ao GitHub.
