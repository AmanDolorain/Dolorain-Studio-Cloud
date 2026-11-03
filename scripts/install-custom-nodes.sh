#!/usr/bin/env bash
set -Eeuo pipefail
# Install only explicitly listed trusted git repositories.
# Format: folder<TAB>https-git-url<TAB>commit-or-tag
ROOT="${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}"
MANIFEST="${DSC_NODES_MANIFEST:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)/config/custom-nodes.tsv}"
[[ -d "$ROOT/custom_nodes" ]] || { echo "ComfyUI missing at $ROOT"; exit 1; }
[[ -f "$MANIFEST" ]] || { echo "Manifest missing: $MANIFEST"; exit 1; }
while IFS=$'\t' read -r name url ref; do
  [[ -z "$name" || "$name" == \#* ]] && continue
  [[ "$name" =~ ^[a-zA-Z0-9._-]+$ ]] || { echo "Invalid node folder: $name"; exit 1; }
  [[ "$url" == https://github.com/* ]] || { echo "Only GitHub HTTPS repositories accepted"; exit 1; }
  [[ -n "$ref" ]] || { echo "Pin a commit or tag for $name"; exit 1; }
  dest="$ROOT/custom_nodes/$name"
  if [[ -e "$dest" && ! -d "$dest/.git" ]]; then echo "Refusing to overwrite $dest"; exit 1; fi
  if [[ ! -d "$dest/.git" ]]; then git clone "$url" "$dest"; fi
  actual="$(git -C "$dest" remote get-url origin)"
  [[ "$actual" == "$url" ]] || { echo "Origin mismatch for $name"; exit 1; }
  git -C "$dest" fetch --depth 1 origin "$ref"
  git -C "$dest" checkout --detach FETCH_HEAD
  if [[ -f "$dest/requirements.txt" ]]; then python3 -m pip install -r "$dest/requirements.txt"; fi
  echo "Installed $name at $(git -C "$dest" rev-parse --short HEAD)"
done < "$MANIFEST"
echo "Custom node manifest processed."
