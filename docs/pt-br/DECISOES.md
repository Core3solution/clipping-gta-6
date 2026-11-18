# Decisões técnicas e estado de validação

Atualizado em 17/11/2026.

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

A suíte completa (158 testes originais + 21 novos) passa. Os testes que dependem de rede ou GPU foram simulados. Esta sessão de desenvolvimento não alcança Twitch, YouTube, Telegram nem PyPI.

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
