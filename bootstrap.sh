#!/usr/bin/env bash
set -Eeuo pipefail
# One small bootstrap for Vast.ai and RunPod startup-script fields.
# GitHub repository is public. Do not put secrets in this file.
ROOT="${DSC_ROOT:-/workspace}"
DEST="${DSC_SOURCE_DIR:-$ROOT/Dolorain-Studio-Cloud}"
mkdir -p "$ROOT"
command -v git >/dev/null || { echo "git required in base image"; exit 1; }
if [[ ! -d "$DEST/.git" ]]; then
  [[ ! -e "$DEST" ]] || { echo "Refusing to overwrite $DEST"; exit 1; }
  git clone https://github.com/AmanDolorain/Dolorain-Studio-Cloud.git "$DEST"
else
  echo "Existing setup repository detected; not auto-updating."
fi
cd "$DEST"
bash setup.sh
if [[ "${DSC_INSTALL_H3_NODES:-1}" == "1" ]]; then
  bash scripts/install-custom-nodes.sh
fi
echo "Foundation installed. H3 models, connector and GPU inference still require validation."
