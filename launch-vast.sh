#!/usr/bin/env bash
set -Eeuo pipefail
# Paste the small bootstrap below into Vast.ai On-start Script, or run this file manually.
# Use a suitable GPU Docker image with git, python3 and PyTorch/CUDA.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/setup.sh"
if [ "${DSC_START_COMFY:-0}" = "1" ]; then
  cd "${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}"
  exec python3 main.py --listen 0.0.0.0 --port "${DSC_COMFY_PORT:-8188}"
fi
echo "Vast.ai setup finished. Start ComfyUI via your image's service, or set DSC_START_COMFY=1."
