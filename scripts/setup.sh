#!/usr/bin/env bash
set -Eeuo pipefail
export DEBIAN_FRONTEND=noninteractive
ROOT="${COMFYUI_DIR:-/workspace/ComfyUI}"
if [[ "${EUID}" -eq 0 ]]; then
  apt-get update
  apt-get install -y --no-install-recommends git git-lfs build-essential ffmpeg curl ca-certificates libgl1 libglib2.0-0 python3-venv python3-pip
fi
if [[ ! -f "$ROOT/main.py" ]]; then
  mkdir -p "$(dirname "$ROOT")"
  git clone https://github.com/comfyanonymous/ComfyUI.git "$ROOT"
fi
cd "$ROOT"
PYTHON="${PYTHON:-python3}"
"$PYTHON" -m pip install -r requirements.txt
"$PYTHON" -m pip install huggingface_hub hf_xet
mkdir -p custom_nodes user/default/workflows models input output
while IFS=' ' read -r name url; do
  [[ -z "$name" || "$name" == \#* ]] && continue
  if [[ -d "custom_nodes/$name/.git" ]]; then
    git -C "custom_nodes/$name" pull --ff-only
  elif [[ ! -e "custom_nodes/$name" ]]; then
    git clone --depth 1 "$url" "custom_nodes/$name"
  fi
  if [[ -f "custom_nodes/$name/requirements.txt" ]]; then
    "$PYTHON" -m pip install -r "custom_nodes/$name/requirements.txt"
  fi
done < "$(dirname "$(realpath "$0")")/../config/custom_nodes.txt"
cp "$(dirname "$(realpath "$0")")/../workflows/"*.json user/default/workflows/ 2>/dev/null || true
echo "Setup complete. Verify CUDA and workflows before GPU generation."
