#!/usr/bin/env bash
set -Eeuo pipefail
ROOT="${COMFYUI_DIR:-/workspace/ComfyUI}"
"${PYTHON:-python3}" -c 'import torch; print("PyTorch:",torch.__version__); print("CUDA available:",torch.cuda.is_available()); print("CUDA runtime:",torch.version.cuda)'
test -f "$ROOT/main.py" && echo "ComfyUI found"
for file in 01_Character_Sheet_Designer.json 02_H3_Video_Generation.json; do
  if [[ -f "$ROOT/user/default/workflows/$file" ]]; then echo "Found workflow: $file"; else echo "MISSING workflow: $file"; fi
done
command -v gcc || echo "WARNING: gcc not found"
