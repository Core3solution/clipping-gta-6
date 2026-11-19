# Passagem de contexto entre sessões

Atualize ao fim de cada sessão de desenvolvimento, em poucas linhas. O hook de início de sessão mostra a seção "Próximos passos".

## Estado atual (19/11/2026, 00h, encerramento do dia 18 no PC)

- **Fonte oficial:** [docs/pt-br/ENCERRAMENTO-2026-11-18.md](../pt-br/ENCERRAMENTO-2026-11-18.md) (o que existe, o que funciona, o que foi testado, pendências, onde está cada material e retomada por máquina).
- Branches no GitHub: `main` intocada (`bde4393`); `ptbr-operacao-lancamento` (operação, 196 testes verdes, CI verde em `edaed40`); `dev/fase02` (desenvolvimento, 229 testes verdes, enviada em 18/11, **não mesclada**). Nada de PR.
- **Vídeos finalizados: 10 do Davy Jones** (notebook, `exports/gta-br/2026-11-18/`), aprovados só no QA automático. Não revisados pelo usuário, não publicados.
- Preparado, sem vídeo final: 5 versões verticais do Alanzoka no Editonny (PC) e 4 candidatos do Paulinho live 2 (PC, `jobs/curadoria-paulinho.md`).
- `dev/fase02` tem `clipper import`, `check` (`hook_fit`, `cut_edges`, `end_scene`) e `clipper qa`: **nada testado com material real**.
- `scripts/captura_youtube.sh` + `blocos_youtube.py`: experimentais, usados ao vivo no Paulinho live 2 (lacunas por TLS/DNS).
- Mídia não vai ao GitHub. Cada máquina tem material exclusivo (tabela na seção 8 do ENCERRAMENTO).

## Pendências que dependem do usuário

- **Autorização de publicação** de Davy Jones, Paulinho, Alanzoka e Tonyboy (nenhuma registrada).
- Revisar os 10 vídeos do Davy (música do jogo, cenas) antes de publicar.
- Aprovar ou não o merge da `dev/fase02` na `ptbr` (libera o `clipper import`).
- Aprovar as melhorias da auditoria (seção 6 do ENCERRAMENTO). Nenhuma entra sem aprovação.
- Bot do Telegram (`.env`, o Claude não lê nem edita).

## Próximos passos (19/11: produzir, não desenvolver)

1. **Notebook:** revisar os 10 vídeos do Davy; curadoria dos blocos 026820–037620 com `/clip-br`; retomar a captura se o VOD seguir disponível.
2. **PC:** salvar o cartão aprovado do Editonny num arquivo em `producao/` e retomar o Alanzoka pelo `~/Projetos/editonny-lab/producao/RETOMAR.md` (V3 primeiro).
3. **PC:** Paulinho live 2, candidatos A–D, só render depois de checar a música; publicação só com autorização.
4. Paulinho live 1 e trechos do Alanzoka pelo `clipper import`, só depois do merge aprovado.

## Como operar

- **PC (WSL):** testes `.venv/bin/python -m unittest discover -s tests`. Se `rtk`/`uv`/`yt-dlp` não forem achados, reabra o VS Code. Push: `git -c credential.helper= -c "credential.helper=/mnt/c/Program\ Files/Git/mingw64/bin/git-credential-manager.exe" push origin <branch>` (sempre com aprovação). O git do WSL não tem identidade: commits saem como `Claude <noreply@anthropic.com>`.
- **Worktree de desenvolvimento:** `~/Projetos/clipping-gta-6-dev` (branch `dev/fase02`, `.venv` próprio). Não usar para captura.
- **Notebook Windows:** testes `.venv/Scripts/python.exe -m unittest discover -s tests` (com `~/.local/bin` no PATH). Filas: [docs/pt-br/OPERACAO.md](../pt-br/OPERACAO.md). Commit com `git -c user.name=Claude -c user.email=noreply@anthropic.com commit ...` (decisão 20).
- CI: `curl -s 'https://api.github.com/repos/Core3solution/clipping-gta-6/actions/runs?branch=ptbr-operacao-lancamento&per_page=1'`.

## Decisões recentes

Ver `docs/pt-br/DECISOES.md` (13 a 20: notebook, 18/11; 21 a 24: `dev/fase02`) e `docs/pt-br/ECOSSISTEMA.md`.
