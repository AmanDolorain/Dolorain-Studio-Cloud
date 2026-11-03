#!/usr/bin/env bash
set -u
echo "Dolorain Studio Cloud environment check"
echo "OS: $(uname -s) / $(uname -m)"
for cmd in bash git curl python3 nvidia-smi; do
  if command -v "$cmd" >/dev/null 2>&1; then echo "OK: $cmd"; else echo "MISSING: $cmd"; fi
done
if command -v python3 >/dev/null 2>&1; then
  python3 - <<'PY'
try:
    import torch
    print("PyTorch:", torch.__version__)
    print("CUDA available:", torch.cuda.is_available())
    if torch.cuda.is_available():
        print("GPU:", torch.cuda.get_device_name(0))
except ImportError:
    print("PyTorch not installed")
PY
fi
