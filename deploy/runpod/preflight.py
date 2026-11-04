#!/usr/bin/env python3
"""Read-only CUDA/PyTorch/driver check. No network operations."""
from __future__ import annotations
import subprocess


def main():
    import torch
    if torch.version.cuda != "13.2":
        raise SystemExit("[FAILED] Expected PyTorch CUDA 13.2, got " + str(torch.version.cuda))
    raw = subprocess.check_output(
        ["nvidia-smi", "--query-gpu=driver_version", "--format=csv,noheader,nounits"],
        text=True, timeout=8
    ).strip().splitlines()[0]
    driver = tuple(int(x) for x in raw.split(".")[:3])
    if driver < (595, 45, 4):
        raise SystemExit("[FAILED] Driver " + raw + " below conservative CUDA 13.2 GA target 595.45.04")
    if not torch.cuda.is_available():
        raise SystemExit("[FAILED] CUDA device not available")
    name = torch.cuda.get_device_name(0)
    major, minor = torch.cuda.get_device_capability(0)
    arch = "sm_" + str(major) + str(minor)
    # Compatible CUDA kernels can run even without an exact architecture entry.
    try:
        sample = torch.ones((2, 2), device="cuda:0")
        value = (sample @ sample + 1)[0, 0].item()
        torch.cuda.synchronize(0)
        if value != 3.0:
            raise RuntimeError(f"unexpected probe result {value}")
    except RuntimeError as exc:
        raise SystemExit(
            f"[FAILED] CUDA execution on {name} ({arch}), driver {raw}, "
            f"torch {torch.__version__}, compiled architectures {torch.cuda.get_arch_list()}: {exc}"
        ) from exc
    print("[OK] Dolorain CUDA 13.2 GPU " + name + " architecture " + arch + " driver " + raw, flush=True)


if __name__ == "__main__":
    main()
