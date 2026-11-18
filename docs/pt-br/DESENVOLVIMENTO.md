# Como desenvolvemos (Claude Code + VS Code + GitHub)

## Instalar uma vez

1. WSL2 e ferramentas: [WINDOWS-WSL.md](WINDOWS-WSL.md).
2. No Ubuntu, dentro do projeto: `scripts/devkit/install-local.sh --rtk` (venv, dependências, RTK edição oss, testes). Depois `rtk init -g` se quiser a compressão de saída em todos os projetos.
3. VS Code no Windows com a extensão **WSL**: no Ubuntu, `code .` abre o projeto. Aceite as extensões recomendadas (Claude Code, Python, Ruff, YAML, GitHub, GitLens).
4. Claude Code: `claude --model sonnet`. Na primeira vez, aceite confiar na pasta e aprove o MCP `context7` quando ele pedir.

**Não instale os plugins Superpowers ou Ponytail no Claude Code.** As skills já vêm no repositório (`.claude/skills/`), o que garante que funcionem também na nuvem. Instalar o plugin duplicaria tudo.

## O que já funciona sozinho

| Peça | Quando age |
| --- | --- |
| Hook `session_context.py` | Toda sessão começa com branch, últimos commits e "Próximos passos" do `HANDOFF.md` |
| Hook `guard.py` | Bloqueia segredos, escrita no `.env`, `git add` de mídia ou `jobs/`/`exports/`, e pergunta antes de commit/push na `main` |
| Hook `verify_on_stop.py` | Ao fim de cada resposta, se algum .py mudou, roda os testes e devolve falhas ao Claude |
| Regras `.claude/rules/` | Princípios, fluxo, contexto e segurança sempre; Python, docs e produção só quando esses arquivos são tocados |
| Skills | O Claude escolhe pelo assunto: `systematic-debugging` em bug, `writing-plans` em tarefa grande, `ponytail` para manter a mudança pequena, `verification-before-completion` antes de dizer "pronto" |
| Subagentes | `explorador` (buscas, Haiku), `revisor` (revisão independente), `depurador` (causa raiz), `qa-video` (confere os vídeos renderizados) |

## Ciclo de uma tarefa

1. Peça em linguagem natural ("adicione sinal de chat da Twitch ao mapa de empolgação").
2. Tarefa grande: o Claude faz poucas perguntas, escreve um plano e executa. Tarefa pequena: executa direto.
3. Antes do commit, peça "revise com o agente revisor".
4. Commit numa branch (`ptbr-<assunto>`), push, Pull Request no GitHub. O CI roda os testes.
5. Ao terminar a sessão: "atualize o HANDOFF".

## Atalhos no VS Code (Terminal > Executar tarefa)

Testes (todos), Testes PT-BR, Telegram: status, Telegram: ler aprovações, VODs: o que baixaria, Atualizar skills de terceiros.

## Reaproveitar em outro projeto

`scripts/devkit/export.sh /caminho/do/projeto` copia skills, hooks, agentes genéricos, regras gerais, VS Code, templates do GitHub e o esqueleto de contexto, sem sobrescrever nada. Depois, ajuste as regras e crie um `CLAUDE.md` curto. As skills de terceiros se atualizam com `scripts/devkit/sync-skills.sh` (commits fixados no script).
