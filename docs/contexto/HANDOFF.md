# Passagem de contexto entre sessões

Atualize ao fim de cada sessão de desenvolvimento, em poucas linhas. O hook de início de sessão mostra a seção "Próximos passos".

## Estado atual (18/11/2026)

- Branch `ptbr-operacao-lancamento`: perfil gta-br, PT-BR, Telegram, VODs, NVENC, zoom suave, `/clip-br`, estrutura de desenvolvimento (skills, agentes, hooks, regras).
- PC instalado (WSL2, Ubuntu 26.04): `.venv` com `uv sync --locked --python 3.12`; yt-dlp, deno, uv e RTK (oss) em `~/.local/bin`; modelo Parakeet v3 baixado. Hooks usam o `.venv`.
- Suíte verde no PC (187 testes, nenhum pulado) e no CI do GitHub (`5f20eba`; 2 pulados lá, sem yt-dlp). O CI agora instala ffmpeg (os testes de zoom e de VODs do gta-br precisam dele). NVENC real confirmado na RTX 3060. YouTube e Twitch acessíveis pelo yt-dlp (sem download).
- Branch no GitHub (`origin/ptbr-operacao-lancamento`), sincronizada; `main` intocada (`bde4393`). Nada de PR aberto.
- Skills (19), `/clip-br` e os 4 subagentes já carregam no Claude Code (subagentes só após recarregar a sessão).
- **Não feito, por decisão do usuário (18/11):** Telegram, primeira produção, nuvem, modo lançamento. Nenhuma implementação nova foi iniciada.
- **Notebook Windows (18/11, nativo, sem WSL/admin):** i7-1360P, 16 GB, Intel Iris Xe (sem NVENC; QSV existe mas não ganha do libx264). Em `~/.local/bin` (no PATH do usuário): ffmpeg/ffprobe 8.1 (BtbN), uv 0.13.9, yt-dlp e deno (`uv tool`). `.venv` com Python 3.12 pelo `uv.lock`. Hooks agora rodam no Windows (antes o `python3` era o atalho da Store e nenhum hook executava). Suíte no Windows: estrutura verde; **motor com 31 falhas** (`fcntl` em `live.py`, sinais, `/proc`, `os.kill(pid,0)` que mata o processo no Windows, agendador só launchd/systemd). Diagnóstico completo aguardando aprovação para o porte.
- Influenciadores em avaliação (autorização de uso pendente; só metadados): Davy Jones (YouTube @Gameplayrj, kick.com/davyjones), Alanzoka (twitch.tv/alanzoka), Tonyboy (YouTube @tonyboyoficial, live com restrição de idade). Radar: categoria GTA VI da Kick.

## Pendências que dependem do usuário

- Nomes e plataformas (Twitch/YouTube/Kick) dos **3 influenciadores autorizados**; hoje `profiles/gta-br/live.yaml` está vazio e `creators.yaml` só tem a Rockstar.
- Bot do Telegram: criar no @BotFather, `cp .env.example .env` e preencher o token (o Claude não lê nem edita o `.env`).
- Escolher o 1º vídeo (link de autorizado; o Launch Trailer oficial `youtu.be/rz1B4B2yBZY` é a opção sem risco de direitos).
- Opcional: Demucs (separação de voz na GPU, ~2–3 GB); sem ele, `separate_voices: false`. Memória do WSL é 7,7 GB (`.wslconfig` se ficar lento).

## Operação de 18/11 (notebook, tarde)

- Motor portado para Windows (suíte verde no Windows; Linux não verificado aqui, falta o CI após push). Commits locais `1df3396`, `c003fff`, `35422e0`, `9829f96`.
- Davy Jones: histórico pela Kick desde 07h59 em blocos de 30 min (`jobs/live-vod-davyjones-kick-kick-138532295-*`, no D:), captura e análise em filas (`docs/pt-br/OPERACAO.md`). Catálogo e sinais do público em `exports/gta-br/2026-11-18/momentos.md`.
- Tonyboy: gravação manual (OBS) pelo operador; live com restrição de idade, sem cookies no notebook. Alanzoka: à noite (Twitch, `live add twitch:alanzoka` + `vod_from`).
- Atenção: duas filas de análise ao mesmo tempo esgotam a RAM (16 GB, ~3 GB livres com o VS Code aberto) e incham o `pagefile.sys` no C:. Uma fila só.

## Próximos passos

0. Ao chegar em casa: push (com aprovação) para o CI validar Linux; sincronizar `D:\GTA6-BR` com a nuvem escolhida; compilação de primeiras reações (Davy + Tonyboy + Alanzoka) com `clipper find`.
1. Telegram: `telegram chat-id` → `TELEGRAM_CHAT_ID` → `telegram notify "teste"`.
2. Primeiro vídeo: `/clip-br <link>`; avaliar a edição com o agente `qa-video` e com o usuário.
3. Nuvem com o PC desligado (docs/pt-br/NUVEM.md): 1 bloco de VOD, depois rotina de hora em hora.
4. Modo lançamento e primeiras reações dos 3 autorizados: `brainstorming` curto → `writing-plans` → TDD.
5. Depois: legendas animadas e callouts do Editonny, SFX do woven-sfx, sinal de chat da Twitch.

## Como operar o PC (WSL)

- Python: `.venv` (o hook põe no PATH); testes `.venv/bin/python -m unittest discover -s tests`. Se `rtk`/`uv`/`yt-dlp` não forem achados, reabra o VS Code (`~/.profile` põe `~/.local/bin` no PATH).
- Push: `git -c credential.helper= -c "credential.helper=/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe" push origin ptbr-operacao-lancamento` (sempre com aprovação do usuário). O git do WSL não tem identidade: commits saem como `Claude <noreply@anthropic.com>`.
- CI: `curl -s 'https://api.github.com/repos/Core3solution/clipping-gta-6/actions/runs?branch=ptbr-operacao-lancamento&per_page=1'`.

## Decisões recentes

Ver `docs/pt-br/DECISOES.md` e `docs/pt-br/ECOSSISTEMA.md`.
