"""Manual GPU verification on a *running* CUDA machine. No installs/downloads.

Run from repo root: python pipeline/gpu_smoke.py
Does not load models, submit workflows or alter any active GPU service.
"""
from __future__ import annotations

import json
import sys
from gpu_transfer import TorchCudaAdapter


def main() -> int:
    try:
        import torch
    except ImportError:
        print(json.dumps({'status': 'SKIPPED', 'reason': 'Existing torch unavailable; no packages installed'}))
        return 2
    if not torch.cuda.is_available():
        print(json.dumps({'status': 'SKIPPED', 'reason': 'CUDA GPU unavailable'}))
        return 2
    try:
        adapter = TorchCudaAdapter(device='cuda:0', reserve_bytes=512 * 1024 * 1024,
                                   max_copy_bytes=4 * 1024 * 1024,
                                   memory_budget_bytes=4 * 1024 * 1024)
        src = torch.arange(1024, dtype=torch.float32)
        gpu_copies = []
        result = adapter.transfer_tensors([src], 'cuda:0', gpu_copies.append)
        back = adapter.copy_tensor(gpu_copies[0].tensor, 'cpu')
        if not torch.equal(src, back.tensor):
            raise RuntimeError('Transferred bytes differ from source')
        print(json.dumps({'status': 'PASS', 'packets': result.consumed,
                          'bytes': back.size_bytes,
                          'h2d_ms': round(gpu_copies[0].milliseconds, 3),
                          'd2h_ms': round(back.milliseconds, 3),
                          'synchronized': gpu_copies[0].synchronized and back.synchronized}))
        return 0
    except Exception as exc:
        print(json.dumps({'status': 'FAILED', 'reason': type(exc).__name__ + ': ' + str(exc)[:200]}))
        return 1


if __name__ == '__main__':
    sys.exit(main())
