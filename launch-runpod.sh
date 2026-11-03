#!/usr/bin/env bash
set -Eeuo pipefail
# For RunPod container start command / startup script.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
bash "$SCRIPT_DIR/setup.sh"
if [ "${DSC_START_COMFY:-0}" = "1" ]; then
  cd "${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}"
  exec python3 main.py --listen 0.0.0.0 --port "${DSC_COMFY_PORT:-8188}"
fi
echo "RunPod setup finished. Start ComfyUI via your image's service, or set DSC_START_COMFY=1."
