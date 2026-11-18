# Fluxo de desenvolvimento (Superpowers, em versão enxuta)

- Tarefa nova com mais de um arquivo ou decisão de design: `brainstorming` curto (no máximo 3 perguntas, e só se a resposta mudar o que será feito) → `writing-plans` → executar.
- Bug ou teste falhando: `systematic-debugging` antes de propor correção.
- Código novo: teste primeiro quando o comportamento é claro (`test-driven-development`); os testes vão em `tests/` (unittest; o PT-BR em `tests/test_ptbr.py`).
- Antes de dizer "pronto": `python3 -m unittest discover -s tests` verde (o hook de Stop também roda a suíte quando há .py alterado).
- Tarefas independentes: subagentes em paralelo (`dispatching-parallel-agents`); revisão de mudança grande: agente `revisor`.
- **Exceção, produção de conteúdo**: em `/clip-br`, rotinas e qualquer rodada de produção, não use brainstorming, planos nem perguntas. Siga o comando.
- Fim de sessão de desenvolvimento: atualize `docs/contexto/HANDOFF.md` (estado, próximos passos) em poucas linhas.
