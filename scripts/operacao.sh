#!/bin/sh
# Operação em duas filas independentes (Git Bash no Windows, ou Linux):
#   sh scripts/operacao.sh captura   baixa os blocos novos dos VODs do live.yaml, sem analisar, a cada 5 min
#   sh scripts/operacao.sh analise   transcreve e pontua um bloco por vez, na ordem em que chegam
# A captura nunca espera a análise. Ambas retomam de onde pararam (state/vods.json; candidates.json por bloco).
cd "$(dirname "$0")/.." || exit 1
export CLIPPER_PROFILE="${CLIPPER_PROFILE:-gta-br}" PATH="$HOME/.local/bin:$PATH" PYTHONUTF8=1  # Windows: cp1252 has no "→"
PY=.venv/bin/python; [ -x "$PY" ] || PY=.venv/Scripts/python.exe; [ -x "$PY" ] || PY=python3
mkdir -p logs
case "$1" in
  captura)
    while :; do
      echo "== $(date '+%F %T') captura" >> logs/captura.log
      "$PY" -m clipper vods fetch --no-analyze --max-chunks 20 >> logs/captura.log 2>&1
      sleep "${INTERVALO:-300}"
    done ;;
  analise)
    while :; do
      job=$(ls -d jobs/live-vod-* 2>/dev/null | while read -r j; do
              [ -f "$j/source.mp4" ] && [ -f "$j/live_ready" ] && [ ! -f "$j/candidates.json" ] && echo "$j"
            done | head -1)
      if [ -n "$job" ]; then
        echo "== $(date '+%F %T') analise $job" >> logs/analise.log
        "$PY" -m clipper analyze "$(basename "$job")" >> logs/analise.log 2>&1 || sleep 60
      else
        sleep 60
      fi
    done ;;
  *) echo "uso: sh scripts/operacao.sh captura|analise" >&2; exit 2 ;;
esac
