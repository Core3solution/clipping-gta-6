# Passagem de contexto entre sessões

Atualize ao fim de cada sessão de desenvolvimento, em poucas linhas. O hook de início de sessão mostra a seção "Próximos passos".

## Estado atual (18/11/2026, 17h30, fim do dia no notebook)

- Branch `ptbr-operacao-lancamento` no GitHub; `main` intocada (`bde4393`). Nada de PR aberto.
- **Primeiro dia de produção feito no notebook Windows** (nativo, sem WSL nem admin). Resumo das 3 operações, inventário de mídia e pendências: [docs/pt-br/OPERACOES-2026-11-18.md](../pt-br/OPERACOES-2026-11-18.md).
- **Davy Jones:** 26 blocos de 30 min (07h59–17h13) capturados pela Kick e transcritos; **10 vídeos aprovados no QA**, nada publicado e nada enviado ao Telegram. Curadoria feita até o bloco 025020; os blocos 026820–037620 estão transcritos e sem curadoria.
- **Paulinho o Loko:** live inteira do YouTube baixada (7h45). Permissão de uso **não confirmada**.
- **Alanzoka:** 3 h de GTA 6 baixadas do VOD da Twitch; o resto é retomável com `scripts/coleta/coleta_twitch_vod.py`.
- **Tonyboy:** live com restrição de idade; o operador grava pelo OBS.
- A mídia (~53 GB) ficou no D: do notebook e vai à parte. Pelo GitHub vão só o código, a documentação e o `state/vods.json`.
- Motor portado para Windows (suíte verde no Windows, 196 testes). Linux não testado no notebook: conferir o CI depois do push.
- PC (WSL2, Ubuntu 26.04) continua como antes: `.venv` com `uv sync --locked --python 3.12`; yt-dlp, deno, uv e RTK em `~/.local/bin`; NVENC na RTX 3060.

## Pendências que dependem do usuário

- Confirmar a permissão do Paulinho o Loko antes de publicar qualquer corte dele.
- Copiar a mídia do D: do notebook para o PC (inventário no OPERACOES-2026-11-18.md) e escolher a nuvem de armazenamento (Drive da CORE 3 ou outra gratuita).
- Bot do Telegram: criar no @BotFather, `cp .env.example .env` e preencher o token (o Claude não lê nem edita o `.env`).
- Tonyboy: autenticação do YouTube só num dispositivo pessoal, se for necessária.
- Revisar e aprovar os 10 vídeos do Davy Jones antes de publicar (em `exports/gta-br/2026-11-18/`).

## Próximos passos

1. Conferir o CI do push de 18/11 (Linux) e copiar `D:\GTA6-BR` para o PC (`jobs/` e `exports/` na raiz do projeto).
2. Implementar a importação de MP4 local em blocos de 30 min (spec no OPERACOES-2026-11-18.md): destrava Paulinho, Alanzoka e Tonyboy.
3. Curadoria dos blocos 026820–037620 do Davy Jones; retomar a captura (`sh scripts/operacao.sh captura`) se o VOD seguir disponível.
4. Compilação das primeiras reações (âncora do Davy: live 5328–5342,6; depois Alanzoka e Tonyboy) com `clipper find`.
5. Auditoria do Editonny e do vibe-coding-toolkit (lista no OPERACOES-2026-11-18.md); depois legendas animadas e callouts.
6. Telegram, e depois a nuvem com o PC desligado (docs/pt-br/NUVEM.md).

## Como operar

- **PC (WSL):** testes `.venv/bin/python -m unittest discover -s tests`. Se `rtk`/`uv`/`yt-dlp` não forem achados, reabra o VS Code. Push: `git -c credential.helper= -c "credential.helper=/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe" push origin ptbr-operacao-lancamento` (sempre com aprovação). O git do WSL não tem identidade: commits saem como `Claude <noreply@anthropic.com>`.
- **Notebook Windows:** testes `.venv/Scripts/python.exe -m unittest discover -s tests` (com `~/.local/bin` no PATH). Filas: [docs/pt-br/OPERACAO.md](../pt-br/OPERACAO.md). O git do notebook tem identidade pessoal configurada: commit com `git -c user.name=Claude -c user.email=noreply@anthropic.com commit ...` (decisão 11).
- CI: `curl -s 'https://api.github.com/repos/Core3solution/clipping-gta-6/actions/runs?branch=ptbr-operacao-lancamento&per_page=1'`.

## Decisões recentes

Ver `docs/pt-br/DECISOES.md` (13 a 20 são de 18/11, notebook) e `docs/pt-br/ECOSSISTEMA.md`.
