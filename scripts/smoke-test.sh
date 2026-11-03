#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}"
[[ -f "$ROOT/main.py" ]] || { echo "FAIL: ComfyUI main.py missing"; exit 1; }
[[ -d "$ROOT/models" ]] || { echo "FAIL: models folder missing"; exit 1; }
echo "PASS: ComfyUI directory structure"
python3 - <<'PY'
import importlib.util
for name in ("torch", "safetensors", "yaml"):
    print(("OK" if importlib.util.find_spec(name) else "MISSING") + ": " + name)
PY
if command -v nvidia-smi >/dev/null 2>&1; then
  nvidia-smi --query-gpu=name,memory.total --format=csv,noheader || true
else
  echo "GPU test skipped (no nvidia-smi)."
fi
echo "This is a structural check, not a MiniMax H3 generation test."
