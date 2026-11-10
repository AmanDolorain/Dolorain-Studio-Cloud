#!/usr/bin/env bash
set -Eeuo pipefail
cd "${COMFYUI_DIR:-/workspace/ComfyUI}"
exec "${PYTHON:-python3}" main.py --listen 0.0.0.0 --port "${COMFYUI_PORT:-8188}"
