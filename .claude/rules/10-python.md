---
paths:
  - "clipper/**/*.py"
  - "tests/**/*.py"
---
# Código Python do clipper

- Python ≥ 3.10, só biblioteca padrão + dependências já declaradas (numpy, pyyaml, pillow, onnx-asr). Ferramentas externas via subprocess (ffmpeg, ffprobe, yt-dlp).
- Siga o estilo do arquivo que está editando: docstrings curtas dizendo o porquê, funções pequenas, sem classes desnecessárias, linhas até ~120 colunas.
- Configuração nova entra no YAML (`watchlist.yaml` ou `profiles/<nome>/profile.yaml`) com valor padrão que mantém o comportamento antigo.
- Estado entre execuções: `clipper/state.py` (JSON atômico em `state/`). Rede: `urllib` (sem `requests`).
- Testes: `unittest`, sem rede e sem GPU (use `mock` e servidores HTTP locais, como em `tests/test_ptbr.py`). Mídia de teste gerada com `ffmpeg -f lavfi`.
