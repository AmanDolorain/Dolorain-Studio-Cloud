#!/usr/bin/env bash
set -Eeuo pipefail
# Manual check only; confirms filenames, not license, correct size or hashes.
root=/workspace/dolorain/models
manifest=/opt/dolorain/src/config/h3-models.tsv
missing=0
while IFS="$(printf '\t')" read -r folder filename || [[ -n "$folder" ]]; do
  [[ -z "$folder" || "$folder" == \#* ]] && continue
  if [[ ! -s "$root/$folder/$filename" ]]; then
    echo "[MISSING] $folder/$filename"
    missing=1
  fi
done < "$manifest"
[[ "$missing" == 0 ]] || exit 1
echo "[OK] Expected model filenames present; model weights still need checksum and execution validation."
