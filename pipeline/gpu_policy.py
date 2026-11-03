"""GPU-aware ComfyUI launch policy. Standard library only; no custom nodes.

This configures documented ComfyUI low-VRAM mode and reserve-VRAM. It does NOT
chunk MiniMax H3 tensors or guarantee that a model fits.
"""
import json
import os
import subprocess
import sys

def probe():
    try:
        raw = subprocess.check_output(
            ["nvidia-smi", "--query-gpu=memory.total,memory.free,name",
             "--format=csv,noheader,nounits"], text=True, timeout=8
        ).strip().splitlines()[0]
        total, free, name = [v.strip() for v in raw.split(",", 2)]
        return {"total_gb": int(total)/1024, "free_gb": int(free)/1024, "name": name}
    except (OSError, ValueError, subprocess.SubprocessError, IndexError):
        return None

def plan(gpu):
    if gpu is None:
        return {"status": "unknown", "flags": [], "reason": "GPU probe unavailable"}
    total, free = gpu["total_gb"], gpu["free_gb"]
    # Conservative policy, not a performance claim.
    reserve = 2.0 if total <= 26 else 3.0
    if free < reserve + 4:
        return {"status": "insufficient_free_vram", "flags": [],
                "reason": "Free VRAM too low for automatic launch"}
    flags = ["--reserve-vram", str(reserve)]
    if total <= 26:
        flags.append("--lowvram")
    else:
        flags.append("--normalvram")
    return {"status": "ready", "flags": flags,
            "reason": "Conservative launch flags; H3 fit still unverified"}

if __name__ == "__main__":
    gpu = probe()
    result = plan(gpu)
    print(json.dumps({"gpu": gpu, **result}, indent=2), file=sys.stderr)
    if result["status"] != "ready":
        sys.exit(2)
    # Output only shell-safe flag tokens, one per line.
    print("\n".join(result["flags"]))
