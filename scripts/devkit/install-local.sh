#!/usr/bin/env bash
# One-time setup of this project on the PC (Ubuntu under WSL2, or Linux/macOS). Free tools only.
#   scripts/devkit/install-local.sh          # venv + Python deps + checks + tests
#   scripts/devkit/install-local.sh --rtk    # also RTK (Apache-2.0 "oss" edition): compresses command output for Claude
set -euo pipefail
ROOT="$(cd "$(dirname "$0")/../.." && pwd)"; cd "$ROOT"
WANT_RTK=0; for a in "$@"; do [ "$a" = "--rtk" ] && WANT_RTK=1; done

say() { printf '\n== %s\n' "$*"; }
say "Ferramentas do sistema"
for t in git python3 ffmpeg ffprobe; do command -v "$t" >/dev/null || { echo "falta $t: sudo apt install -y git python3-venv ffmpeg"; exit 1; }; done
python3 -c 'import sys; assert sys.version_info >= (3, 10), "Python >= 3.10"'
ffmpeg -hide_banner -encoders 2>/dev/null | grep -q h264_nvenc && echo "NVENC disponível no FFmpeg" || echo "NVENC não listado: render usa libx264 (funciona, mais lento)"
command -v nvidia-smi >/dev/null && nvidia-smi -L || echo "GPU NVIDIA não visível (ok para testes)"

say "Ambiente Python (.venv)"
export PATH="$HOME/.local/bin:$PATH"
if command -v uv >/dev/null; then
  # Same lockfile and Python as CI; yt-dlp and deno (YouTube JS runtime) as isolated tools in ~/.local/bin.
  uv sync --locked --python 3.12
  uv tool install --upgrade "yt-dlp[default]"
  uv tool install --upgrade deno
  . .venv/bin/activate
else
  [ -d .venv ] || python3 -m venv .venv
  . .venv/bin/activate
  pip install --quiet --upgrade pip
  pip install --quiet -U yt-dlp "onnx-asr[cpu,hub]==0.12.0" numpy pillow pyyaml
fi

say "Configuração"
[ -f .env ] || { cp .env.example .env; echo "criado .env a partir de .env.example: preencha o Telegram (docs/pt-br/TELEGRAM.md)"; }

if [ "$WANT_RTK" = 1 ]; then
  say "RTK (edição oss, Apache-2.0)"
  if ! command -v rtk >/dev/null; then
    curl -fsSL https://raw.githubusercontent.com/rtk-ai/rtk/refs/heads/master/install.sh | RTK_EDITION=oss sh
  fi
  echo "Para ligar o RTK no Claude Code (todos os projetos): rtk init -g   |   ver economia: rtk gain"
fi

say "Testes"
python3 -m unittest discover -s tests 2>&1 | tail -3
say "Pronto. Abra o Claude Code aqui: claude --model sonnet"
