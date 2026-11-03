#!/usr/bin/env bash
set -Eeuo pipefail
# Launch only if the selected image does not already run ComfyUI.
ROOT="${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}"
REPO="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
[[ -f "$ROOT/main.py" ]] || { echo "ComfyUI missing at $ROOT"; exit 1; }
mapfile -t flags < <(python3 "$REPO/pipeline/gpu_policy.py" 2>"$ROOT/dsc-gpu-policy.log")
# Process substitution does not propagate producer errors: check the output.
[[ "${#flags[@]}" -ge 2 ]] || { cat "$ROOT/dsc-gpu-policy.log"; echo "GPU policy failed; refusing to launch"; exit 1; }
cat "$ROOT/dsc-gpu-policy.log"
cd "$ROOT"
exec python3 main.py --listen 127.0.0.1 --port "${DSC_COMFY_PORT:-8188}" "${flags[@]}"
