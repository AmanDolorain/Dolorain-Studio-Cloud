#!/usr/bin/env bash
set -Eeuo pipefail
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
MODEL_DIR="${DSC_COMFY_DIR:-${DSC_ROOT:-/workspace}/ComfyUI}/models"
manifest="$REPO_DIR/config/h3-models.tsv"
missing=0
while IFS=$'\t' read -r folder filename; do
  [[ -z "$folder" || "$folder" == \#* ]] && continue
  if [[ -s "$MODEL_DIR/$folder/$filename" ]]; then
    printf 'OK      %s/%s\n' "$folder" "$filename"
  else
    printf 'MISSING %s/%s\n' "$folder" "$filename"
    missing=$((missing+1))
  fi
done < "$manifest"
if (( missing > 0 )); then
  printf '%d model file(s) missing or empty.\n' "$missing"
  exit 1
fi
echo "All expected H3 model files exist (integrity not yet verified)."
