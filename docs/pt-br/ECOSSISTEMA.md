# Ecossistema de ferramentas (catálogo resumido)

Levantado em 17/11/2026 a partir dos 9 repositórios públicos de soumatheusgomes e das ferramentas que eles citam (~50). A lista de repositórios favoritados não pôde ser lida (o GitHub bloqueia leitura automática da página de estrelas). Custo de tudo marcado "agora": R$ 0.

Legenda do momento: **agora** (instalado neste repositório), **PC** (instalação opcional na sua máquina), **depois** (fase seguinte), **não** (redundante, pago ou incompatível).

## 1. Desenvolvimento da ferramenta

| Ferramenta | Licença | Para que serve | Momento | Como está no projeto |
| --- | --- | --- | --- | --- |
| Superpowers (obra) | MIT | Fluxo de engenharia: brainstorming, planos, TDD, depuração sistemática, verificação, subagentes, revisão, worktrees | agora | 14 skills copiadas em `.claude/skills/` (funcionam no PC e na nuvem) |
| Ponytail | MIT | Menor mudança completa, revisão de excesso, dívida técnica | agora | 5 skills em `.claude/skills/` (sem os hooks em Node) |
| Agentville | Apache-2.0 | Hooks, agentes e regras de um harness completo | agora (adaptado) | Ideias reescritas em Python: `guard.py`, `verify_on_stop.py`, agentes `revisor`/`depurador`/`explorador` |
| Vibe Coding Toolkit | MIT | Guias, prompts e templates (CLAUDE→AGENTS, handoff, regras) | agora (adaptado) | `CLAUDE.md`, `docs/contexto/HANDOFF.md`, regras. Templates JS/Next ignorados |
| curso-vibecoding | sem licença | Prompts PT-BR (bug, segurança, arquitetura, lentidão) | referência | Usar como inspiração de pedido; não copiado |
| Context7 | MIT (serviço grátis com limite) | Documentação atual de bibliotecas via MCP | agora | `.mcp.json` (aprovar no primeiro uso) |
| uv | MIT/Apache | Ambiente Python com lockfile | agora | Já usado pelo upstream (`uv.lock`) |
| skill-creator (anthropics/skills) | Apache-2.0 | Criar skills | não | Redundante com `writing-skills` |
| trailofbits/skills (modern-python etc.) | a confirmar | Boas práticas Python, segurança | depois | Conferir licença antes |
| Plugins oficiais (code-review, pr-review-toolkit, hookify, commit-commands) | — | Revisão e commits | não | Redundantes com Superpowers + agente `revisor` |
| aia-harness | MIT | Gera uma estrutura `.claude` inteira | não | Já temos a nossa, mais enxuta |
| Graphify | Apache-2.0 | Grafo do código | depois | Repositório pequeno; sem ganho agora |
| Harness2, agent-browser, Chrome DevTools MCP, github-project-skill | vários | Pesquisa, navegador, CI | não | Fora do escopo ou share-alike |

## 2. Operação de produção de conteúdo

| Ferramenta | Licença | Para que serve | Momento |
| --- | --- | --- | --- |
| clipping-gta-6 | AGPL-3.0 | Base: gravação, transcrição, sinais, curadoria via Claude, render | agora |
| Editonny | MIT | Zoom suave (já portado); próximos: legendas animadas, callouts, SFX gerados, facecam YuNet, checagens de qualidade | agora/depois |
| woven-sfx | MIT + sons CC0 | Biblioteca de efeitos sonoros livres | depois (próximo) |
| browser-use/video-use | MIT | Padrões de skill de edição (transcrição condensada, imagem de linha do tempo, autoavaliação) | depois (o ASR dele é pago: não usar) |
| HyperFrames (HeyGen) | Apache-2.0 | Motion graphics HTML→MP4 | depois, só no PC (Node + Chrome), telemetria desligada |
| faster-whisper | MIT | ASR na RTX 3060, comparação com Parakeet | depois (PC) |
| onnx-asr / Parakeet v3 | MIT | ASR atual, CPU, inclui português | agora |
| WhisperX | BSD-2 | Alinhamento fino e diarização | depois, se necessário |
| YuNet / MediaPipe | MIT / Apache | Detecção de rosto para facecam | depois |
| Kokoro TTS | a confirmar | Narração local | depois (avaliar PT-BR) |
| Remotion | licença própria | Vídeo em React | não (HyperFrames cobre) |
| ElevenLabs, OpenRouter, Pexels, Fish Audio | pagos | Voz, imagens, música | não |

## 3. Infraestrutura e automação

| Ferramenta | Para que serve | Momento |
| --- | --- | --- |
| Rotinas do Claude Code | Rodar `/clip-br` de hora em hora sem o PC | agora (teste em `docs/pt-br/NUVEM.md`) |
| Bot do Telegram (Bot API) | Entrega e aprovação | agora |
| GitHub Actions | CI da suíte de testes (main e `ptbr-*`) | agora |
| Oracle Always Free (A1 ARM) + `tools/ORACLE/server-setup.sh` | Máquina persistente grátis, com cartão e risco de capacidade | depois; não usar `oracle.js` nem `SERVER/server-setup.sh` sem editar |
| ofelia | Cron para containers em VPS | depois, se houver VPS |
| n8n (setups do Matheus) | Orquestração visual com filas | não agora (script + rotina bastam) |
| Firecrawl, Traefik, ZAPBOX | Raspagem, proxy, WhatsApp | não |
| Grok Bot | Computador persistente pago | só se as opções gratuitas falharem |

## 4. Economia de contexto e de uso

| Ferramenta ou prática | Efeito | Momento |
| --- | --- | --- |
| Regras com `paths` (`.claude/rules/`) | Instruções de Python, docs e produção só carregam quando relevantes | agora |
| `CLAUDE.md` curto + `HANDOFF.md` lido pelo hook de início | Cada sessão começa orientada sem reler o repositório | agora |
| Agente `explorador` com modelo Haiku | Buscas amplas fora do contexto principal e mais baratas | agora |
| Hook de Stop com cache | Testes só rodam quando .py mudou | agora |
| RTK edição oss | Comprime a saída de git, testes e ferramentas antes de chegar ao Claude | PC (`install-local.sh --rtk`, depois `rtk init -g`) |
| Caveman | Respostas comprimidas | depois (sobreposição com Ponytail; modo "ultra" arriscado) |
| Sonnet como padrão | Mesma qualidade de curadoria com menos uso que Opus | agora |
| Memória automática do Claude Code | Notas pessoais por projeto na sua máquina | automática (local) |
| Memória em Obsidian | — | não |
