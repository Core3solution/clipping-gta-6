# Decisões técnicas e estado de validação

Atualizado em 18/11/2026 (fim do dia, notebook).

## O que foi implementado e o que foi testado

| Item | Implementado | Testado |
| --- | --- | --- |
| Perfil `gta-br` (PT-BR, palavras de empolgação, exemplos de ganchos, VODs, encoder) | Sim | Carregamento e exemplos validados pela suíte de testes |
| Ganchos, aberturas, enchimentos ("então galera") e títulos em português | Sim | Testes unitários. Inglês continua igual |
| Censura configurável (palavrões em PT mascarados, ofensas removidas, listas `extra`/`allow`) | Sim | Testes unitários |
| Crédito "Corte de <canal>" e link da Twitch com minuto (`?t=1h2m5s`) | Sim | Testes unitários |
| Telegram: envio de MP4 com legenda, botões, descrição; aprovação; pedidos por link | Sim | Contra um servidor falso local. **Falta o teste real com o seu bot** |
| VODs: encerrados e blocos novos de lives em andamento (Twitch), estado persistente, retentativas | Sim | Com yt-dlp simulado. **Falta o teste real contra a Twitch** |
| NVENC automático na RTX 3060, `libx264 veryfast` na nuvem | Sim | Seleção testada. NVENC real confirmado no PC em 18/11 (encode 1080x1920 com `h264_nvenc`) |
| Zoom suave com `perspective` (técnica do Editonny) | Sim | Renderizado com FFmpeg nesta sessão |
| `/clip-br`: modo manual e automático, dois modelos de edição, textos PT-BR | Sim (roteiro) | **Falta a primeira produção real** |
| Transcrição em português (Parakeet v3) | Já existia | **Falta testar com áudio real em PT-BR** |
| Rotina na nuvem com o PC desligado | Documentado (`NUVEM.md`) | **Não testado** |
| Motor no Windows nativo (travas, PIDs, parada graciosa, hooks) | Sim (18/11) | Suíte verde no Windows (196 testes); gravação ao vivo testada só pelos testes com ffmpeg real. Linux: pelo CI após o push |
| VOD da Kick por segmentos HLS (`vods.py`), `vod_from`, `--no-analyze` | Sim (18/11) | **Real:** 26 blocos de 30 min do Davy Jones, 1080p60 sem recodificar |
| Primeira produção (`/clip-br` com curadoria, render, QA) | Sim (18/11) | **Real:** 10 vídeos aprovados pelo `qa-video` (27 renders). Telegram ainda não |
| Transcrição em português (Parakeet v3) | Já existia | **Real:** 26 blocos em PT-BR; legendas conferidas pelo QA |
| Importação de MP4 local (`clipper import`) | Sim (18/11, PC) | Testes automáticos (identidade, cortes reais, retomada, sem duplicar, A/V, autorização, CLI) e arquivo sintético de 3 min 1080p60. **Falta com as gravações reais** |

A suíte completa (187 testes: 158 originais, 21 do PT-BR, 8 da estrutura de desenvolvimento) passa no PC (18/11, nenhum pulado) e no CI do GitHub (2 pulados lá, por falta de yt-dlp). Os testes que dependem de rede ou GPU são simulados.

## Decisões

1. **Base:** clipping-gta-6 (AGPL-3.0). As mudanças ficam num branch próprio, sem reescrever o que já existe.
2. **Curadoria pelo próprio Claude Code** (assinatura Max), como o projeto original já faz. Nenhuma API de LLM paga.
3. **Português como camada, não como fork:** os padrões de gancho reconhecem inglês **e** português ao mesmo tempo, e o perfil escolhe o idioma dos textos.
4. **VODs em vez de gravação contínua na nuvem:** a Twitch mantém o VOD crescendo durante a live, então uma execução por hora recupera só a parte nova. Os blocos viram jobs `live-vod-*` e entram no mesmo fluxo dos blocos gravados (`live jobs`, `live done`).
5. **Estado em `state/` (JSON, escrita atômica):** sobrevive a clone novo (commit no fim de cada rotina) e a falhas no meio de uma execução, sem baixar nem enviar nada duas vezes.
6. **Telegram só por HTTPS da Bot API, sem bibliotecas novas:** nada de processo sempre ligado. Os toques e pedidos são lidos a cada rodada.
7. **Nada é publicado automaticamente.** Aprovar só registra a decisão.
8. **Editonny:** só técnicas isoladas, com crédito (`THIRD_PARTY.md`). O fluxo dele exige humano no meio e o caminho de HyperFrames precisa de Chromium e npm.
9. **Ambiente do PC com uv (18/11/2026):** `.venv` por `uv sync --locked --python 3.12` (mesmo lockfile e Python do CI); yt-dlp e deno (runtime JS que o YouTube exige) como `uv tool` em `~/.local/bin`. O python3 do sistema não tem as dependências, então o hook de início de sessão põe o `.venv` no PATH do Claude (via `CLAUDE_ENV_FILE`) e o hook de Stop testa com `.venv/bin/python`. Na nuvem não há `.venv` e nada muda.
10. **CI instala ffmpeg (18/11/2026):** dois testes do gta-br (zoom `perspective` e blocos de VOD, que usam `ffprobe` em `make_job`) precisam de ffmpeg real; sem ele o CI falhava. Preferimos instalar no CI a pular os testes, para o CI validar o fluxo que a nuvem vai usar.
11. **Git no WSL (18/11/2026):** sem identidade configurada; os commits saem como `Claude <noreply@anthropic.com>` (como os do patch), para não expor e-mail pessoal. Push só com aprovação do usuário, pelo Git Credential Manager do Windows passado no próprio comando.
12. **RTK e Context7 (18/11/2026):** RTK edição oss com hook **global** (`~/.claude/settings.json`, caminho absoluto), porque na nuvem não há `rtk` e um hook no projeto quebraria lá. Context7 aprovado só localmente (`.claude/settings.local.json`, fora do git).

13. **Notebook Windows nativo (18/11/2026):** sem WSL e sem admin. O winget trava e o pip aponta para um espelho corporativo em HTTP (o pip recusa, e não liberamos `--trusted-host`), então ffmpeg 8.1 e uv vieram das releases oficiais no GitHub com SHA-256 conferido, em `~/.local/bin` (PATH do usuário). Os hooks passam por `.claude/hooks/python.sh`, que pula o atalho `python3` da Microsoft Store; no Linux continua chamando `python3`. O guard também cobre o PowerShell e caminhos com `\`.

14. **Histórico de live do YouTube pela Kick (18/11/2026):** o yt-dlp não corta trecho de live do YouTube em andamento ("cannot be partially downloaded"), e o modo "desde o início" só junta o arquivo quando a live termina. Davy Jones transmite a mesma live na Kick, cujo VOD é HLS crescente: baixamos os segmentos de 10 s em paralelo (6 conexões, ~5x o tempo real em 1080p60) e juntamos sem recodificar. Uma plataforma por streamer, para não capturar a mesma live duas vezes.
15. **Captura separada da análise (18/11/2026):** `vods fetch --no-analyze` em loop e uma fila que transcreve um bloco por vez (`scripts/operacao.sh`). A captura nunca espera a transcrição.
16. **Mídia no D: por junções (18/11/2026):** `jobs/` e `exports/` apontam para `D:\GTA6-BR\` (`mklink /J`, sem admin). O código não muda e o C: (pouco espaço, paginação do Windows) fica livre. As pastas conceituais 01–07 são mapeadas sobre a estrutura existente, sem cópias ([OPERACAO.md](OPERACAO.md)).
17. **Modelo Parakeet baixado em partes (18/11/2026):** o download do Hugging Face por uma conexão travou (~0,8 MB/s); baixamos os 4 arquivos com `curl` em 8 faixas paralelas direto no cache do Hugging Face e conferimos o SHA-256. Sem mudança de código.

18. **Três operações separadas (18/11/2026):** Davy Jones na produção (pipeline completo); Paulinho o Loko e Alanzoka só coleta, em `D:\GTA6-BR\COLETA\`, fora do `state/` e do `jobs/` do projeto. Assim, uma coleta sem autorização confirmada nunca entra na produção por engano. Resumo em [OPERACOES-2026-11-18.md](OPERACOES-2026-11-18.md).
19. **Scripts de coleta preservados como estão (18/11/2026):** `scripts/coleta/` guarda os scripts da operação 03 (Twitch por segmentos fMP4, referências do YouTube, catálogo de clipes), só com o ffmpeg vindo do PATH. Não foram integrados ao `clipper` nem testados; a importação de MP4 local e a Twitch por segmentos no `vods.py` ficam como trabalho planejado.
20. **Autoria dos commits do notebook (18/11/2026):** o git do notebook tem identidade pessoal. Seguindo a decisão 11, os commits deste branch são publicados como `Claude <noreply@anthropic.com>`; os 8 commits locais do dia foram reescritos com essa autoria antes do primeiro push, quando ainda não estavam em nenhum outro lugar.

21. **Desenvolvimento em worktree isolada (18/11/2026, PC):** outras sessões capturam e recuperam gravações na pasta principal, usando o `.venv`, o `jobs/` e o `state/` dela. O desenvolvimento roda em `../clipping-gta-6-dev` (branch `dev/fase02`), com `.venv` próprio criado pelo mesmo `uv.lock`. Nada da pasta principal é alterado. Auditoria completa: [AUDITORIA-2026-11-18.md](AUDITORIA-2026-11-18.md).
22. **Importar MP4 por uma passada do segment muxer (18/11/2026):** `-c copy -f segment -segment_times` com a lista CSV dá o início real de cada bloco na fonte (o corte cai no keyframe seguinte à marca). Assim os offsets e o `recorded_at` são exatos, os blocos não se sobrepõem, e a mesma entrada sempre gera os mesmos blocos, o que torna a retomada segura. Descartados: `-ss`/`-t` por bloco (sobreposição e áudio fora de sincronia no início) e recodificar (lento). Identidade pelo SHA-256 completo, guardado em cache por caminho + tamanho + mtime em `state/imports.json`.
23. **Autorização de publicação separada da captura (18/11/2026):** estar no `live.yaml`/`creators.yaml` diz o que capturar, não o que publicar. A autorização fica em `profiles/<perfil>/authorizations.yaml` (`autorizado | pendente | negado`, evidência, data) e vai para o `job.json` de cada bloco importado. A importação nunca é bloqueada; publicar continua sendo decisão humana.

## Repositórios avaliados (resumo)

| Repositório | Licença | Uso |
| --- | --- | --- |
| soumatheusgomes/editonny | MIT | **Agora:** zoom com `perspective` (feito). **Próximos:** legendas animadas (`text_render.py`), callouts do modelo Descoberta (`visuals/highlight.py`, `impact_word.py`), efeitos sonoros gerados por código, detecção automática da facecam (YuNet), filtros contra alucinação da transcrição, checagens do `quality_gate.py`. **Não:** HyperFrames, APIs pagas (ElevenLabs, OpenRouter, Pexels), fluxo com confirmação humana |
| soumatheusgomes/vibe-coding-toolkit | MIT | **Agora:** `CLAUDE.md` apontando para `AGENTS.md`, convenções de trabalho e template de passagem de contexto entre execuções. Plugins Superpowers, Ponytail e Caveman são opcionais no seu Claude Code. **Não:** templates JS/Next, RTK (não sobrevive à nuvem efêmera) |
| soumatheusgomes/agentville | Apache-2.0 | **Depois:** hook `secret-scan` (com padrão para token do Telegram). **Não:** o `settings.json` dele usa `bypassPermissions` |
| soumatheusgomes/tools | Sem licença | Só referência. `ORACLE/server-setup.sh` como inspiração. **Não rodar** `oracle.js` (cria shape pago) nem `SERVER/server-setup.sh` (traz a chave SSH de outra pessoa) |
| soumatheusgomes/n8n-setup e n8n-setup-scale | MIT | Não agora: nenhuma vantagem imediata sobre uma rotina e um script |
| soumatheusgomes/buscandomilhao, framework-5p, curso-vibecoding | Sem licença | Não: são prompts e material de curso, sem componente reutilizável para a operação |

## Próximos passos de qualidade (depois da primeira produção)

1. Legendas animadas do Editonny (palavra ativa em caixa deslizante) como terceiro estilo.
2. Detecção automática da facecam restrita aos cantos (YuNet), para dispensar o `clipper frame`.
3. Sinal de chat da Twitch (picos e "KKKK") no mapa de empolgação.
4. Aprendizado com Aprovar/Rejeitar: ajustar pesos por perfil (`learned-weights.yaml` já é suportado).
