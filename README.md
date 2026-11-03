# Dolorain Studio Cloud

Shared ComfyUI bootstrap for **Vast.ai** and **RunPod**.

**Status: foundation only, not yet GPU-tested.** MiniMax H3 custom nodes, model downloads, authentication and port mapping are not configured yet.

## Files
- `setup.sh` — shared ComfyUI setup; keeps existing Git checkout and creates model directories.
- `launch-vast.sh` — Vast.ai wrapper.
- `launch-runpod.sh` — RunPod wrapper.
- `config/comfyui.env.example` — optional configuration example without secrets.

## Minimal on-start bootstrap (either provider)

Paste in the provider's **startup script** field, **not Docker Options**, only after checking your Docker image includes bash, curl, git, Python 3, and compatible CUDA/PyTorch:

```bash
#!/usr/bin/env bash
set -e
curl -fsSL https://raw.githubusercontent.com/AmanDolorain/Dolorain-Studio-Cloud/main/setup.sh -o /tmp/dsc-setup.sh
bash /tmp/dsc-setup.sh
```

This installs ComfyUI foundations but **does not automatically start ComfyUI**, expose ports, or enable authentication. The selected image's existing startup service may handle those tasks.

## H3 model directories
- `models/diffusion_models/` — diffusion
- `models/text_encoders/` — text encoder
- `models/vae/` — video/audio VAE
- `models/loras/` — Turbo LoRA

No model weights are downloaded or committed. Existing model files are preserved. Do not commit passwords, API tokens or model weights. Public access to ComfyUI requires appropriate access controls.

## Next
Confirm exact RunPod and Vast.ai Docker images, then implement and test H3 node installation, model retrieval, startup, and secure port access.
