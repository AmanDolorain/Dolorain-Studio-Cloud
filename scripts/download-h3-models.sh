#!/usr/bin/env bash
set -Eeuo pipefail
# Download only from URLs explicitly supplied by the operator.
# Usage: DSC_MODEL_URLS_FILE=/path/to/model-urls.tsv bash scripts/download-h3-models.sh
# File format: directory<TAB>filename<TAB>https-url (one per line).
: "${DSC_MODEL_URLS_FILE:?Set DSC_MODEL_URLS_FILE to a local TSV file of authorized model URLs}"
[[ -f "$DSC_MODEL_URLS_FILE" ]] || { echo "URL manifest missing"; exit 1; }
command -v curl >/dev/null || { echo "curl required"; exit 1; }
BASE="${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}/models"
while IFS=$'\t' read -r dir name url; do
  [[ -z "$dir" || "$dir" == \#* ]] && continue
  case "$dir" in diffusion_models|text_encoders|vae|loras) ;; *) echo "Invalid model directory"; exit 1;; esac
  [[ "$name" =~ ^[a-zA-Z0-9._-]+$ ]] || { echo "Invalid model filename"; exit 1; }
  [[ "$url" == https://* ]] || { echo "Only HTTPS model URLs allowed"; exit 1; }
  mkdir -p "$BASE/$dir"
  dest="$BASE/$dir/$name"
  if [[ -s "$dest" ]]; then echo "SKIP existing: $dir/$name"; continue; fi
  echo "Downloading: $dir/$name"
  # Partial downloads are never mistaken for complete weights.
  rm -f "$dest.part"
  curl --fail --location --retry 3 --connect-timeout 30 --output "$dest.part" "$url"
  [[ -s "$dest.part" ]] || { echo "Empty download: $name"; exit 1; }
  mv "$dest.part" "$dest"
done < "$DSC_MODEL_URLS_FILE"
echo "Downloads finished. Verify hashes against publisher checksums where available."
