# Economia de contexto e de uso

- Leia por partes: `Grep`/`Glob` primeiro, depois `Read` com `offset`/`limit`. Não leia arquivos inteiros de 500+ linhas sem precisar (`clipper/render.py`, `tests/test_core.py`).
- Nunca leia mídia, `uv.lock`, `research/gaming-shorts-titles.json` nem `jobs/*/transcript.json` inteiros. Transcrição: Grep por `"s": 843.` e leia ao redor.
- Varredura ampla do repositório ou da web: delegue ao agente `explorador` (modelo menor) e receba só a conclusão.
- Saída de comando longa: filtre (`| tail -20`, `--quiet`). Com RTK instalado no PC, a filtragem é automática.
- Modelo: Sonnet para o dia a dia e para produção; Opus só para arquitetura ou depuração difícil.
- Respostas curtas e diretas; sem repetir código que acabou de ser escrito.
