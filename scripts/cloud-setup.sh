#!/usr/bin/env bash
# Setup script for a Claude Code cloud environment (claude.ai/code -> environment -> Setup script).
# Installs what the clipper needs on a fresh Ubuntu image and pre-downloads the Parakeet speech model, so each
# routine run starts ready. The environment caches the result for several days.
# Network the environment needs (Custom access, or Full while testing): pypi.org, files.pythonhosted.org,
# huggingface.co and its CDN (*.hf.co), *.twitch.tv, *.ttvnw.net, *.cloudfront.net (Twitch VOD files),
# api.telegram.org. YouTube usually blocks datacenter IPs: leave YouTube sources to the PC.
set -euo pipefail

SUDO=""
if [ "$(id -u)" != "0" ] && command -v sudo >/dev/null 2>&1 && sudo -n true 2>/dev/null; then SUDO=sudo; fi

if ! command -v ffmpeg >/dev/null 2>&1; then
  $SUDO apt-get update -y
  $SUDO apt-get install -y ffmpeg fonts-dejavu-core
fi

PKGS=(yt-dlp "onnx-asr[cpu,hub]==0.12.0" numpy pillow pyyaml)
python3 -m pip install --quiet --upgrade --break-system-packages "${PKGS[@]}" \
  || python3 -m pip install --quiet --upgrade "${PKGS[@]}"

# Pre-download Parakeet TDT 0.6B v3 (multilingual, Portuguese included) and the Silero VAD.
python3 - <<'PY'
import onnx_asr
onnx_asr.load_model("nemo-parakeet-tdt-0.6b-v3", quantization="int8", providers=["CPUExecutionProvider"])
onnx_asr.load_vad("silero", providers=["CPUExecutionProvider"])
print("parakeet ready")
PY

ffmpeg -version | head -1
yt-dlp --version
