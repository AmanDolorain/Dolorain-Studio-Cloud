#!/usr/bin/env bash
set -Eeuo pipefail
# Dolorain Studio Cloud - shared installer for Vast.ai and RunPod.
# Run as a normal shell script on a compatible Linux GPU container.
export DEBIAN_FRONTEND=noninteractive
ROOT="${DSC_ROOT:-/workspace}"
COMFY="${DSC_COMFY_DIR:-$ROOT/ComfyUI}"
mkdir -p "$ROOT"
command -v git >/dev/null || { echo "ERROR: git is required in the Docker image"; exit 1; }
command -v python3 >/dev/null || { echo "ERROR: python3 is required in the Docker image"; exit 1; }
if [ ! -d "$COMFY/.git" ]; then
  if [ -e "$COMFY" ]; then echo "ERROR: $COMFY exists but is not a Git checkout; refusing to overwrite"; exit 1; fi
  git clone --depth 1 https://github.com/comfyanonymous/ComfyUI.git "$COMFY"
else
  echo "Existing ComfyUI detected; not auto-updating."
fi
cd "$COMFY"
if [ "${DSC_INSTALL_REQUIREMENTS:-1}" = "1" ]; then
  python3 -m pip install -r requirements.txt
fi
mkdir -p models/diffusion_models models/text_encoders models/vae models/loras input output custom_nodes
cat <<'MSG'
Dolorain Studio Cloud setup completed.
H3 model weights are NOT included or downloaded automatically.
Put your licensed model files in the corresponding ComfyUI/models folders.
This installer does not configure public access, authentication, or SSH.
MSG
