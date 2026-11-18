# Passagem de contexto entre sessões

Atualize ao fim de cada sessão de desenvolvimento, em poucas linhas. O hook de início de sessão mostra a seção "Próximos passos".

## Estado atual (18/11/2026)

- Branch `ptbr-operacao-lancamento`: perfil gta-br, PT-BR, Telegram, VODs, NVENC, zoom suave, `/clip-br`, estrutura de desenvolvimento (skills, agentes, hooks, regras).
- PC instalado (WSL2, Ubuntu 26.04): `.venv` com `uv sync --locked --python 3.12`; yt-dlp, deno, uv e RTK (oss) em `~/.local/bin`; modelo Parakeet v3 baixado. Hooks usam o `.venv`.
- Suíte verde no PC (187 testes, nenhum pulado). NVENC real confirmado na RTX 3060. YouTube e Twitch acessíveis pelo yt-dlp (sem download). Telegram e produção real ainda não testados.
- Branch commitada localmente, **push pendente**: o GitHub recusou (403) a conta salva no Windows, sem escrita em `Core3solution/clipping-gta-6`. `main` intocada. Subagentes do projeto apareceram no Claude Code após recarregar.
- Sem `.env`, sem streamers cadastrados (`profiles/gta-br/live.yaml` vazio) e sem "modo lançamento" no código. Demucs não instalado (use `separate_voices: false`).
- Shell: se `rtk`/`uv`/`yt-dlp` não forem achados, reabra o VS Code (`~/.profile` põe `~/.local/bin` no PATH).

## Próximos passos

1. Validar skills e agentes numa sessão nova (`/clip-br` listado, agentes `revisor`/`qa-video` invocáveis).
2. Telegram: bot no @BotFather, `cp .env.example .env` (o usuário preenche), `telegram chat-id`, `telegram notify "teste"`.
3. Primeiro vídeo real: `/clip-br <link de GTA 6>`; avaliar a edição com o agente `qa-video` e o usuário.
4. Nuvem com o PC desligado (docs/pt-br/NUVEM.md): 1 bloco de VOD, depois rotina de hora em hora.
5. Modo lançamento: pedir ao usuário os 3 influenciadores autorizados (`live add`/`creators add`), planejar com `writing-plans`.
6. Depois: legendas animadas e callouts do Editonny, SFX do woven-sfx, sinal de chat da Twitch.

## Decisões recentes

Ver `docs/pt-br/DECISOES.md` e `docs/pt-br/ECOSSISTEMA.md`.
