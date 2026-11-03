# Release blockers for Dolorain Studio Cloud v1.0

The repository is **not yet a complete, tested H3 Ref2V workflow**.

- Obtain and inspect the exact exported ComfyUI workflow JSON (node IDs, links, model loader types, audio/video paths).
- Identify H3 Connector published source and pin it. Do not silently replace it with an unrelated package.
- Verify official model download locations, licenses, expected sizes and hashes. Avoid committing signed URLs or access tokens.
- Confirm the MiniMax H3 ComfyUI implementation and supported model-specific offloading, attention and VAE tiling. The GPU policy is not a chunking implementation.
- Verify provider base image, Python/CUDA/PyTorch, startup lifecycle, persistence, proxy authentication, Jupyter and SSH settings.
- Run tests in an isolated environment, then smoke-test on rented GPU with measured peak VRAM and generation output.
- Pin a release tag for new templates so changes to main cannot unexpectedly break launches.

## What is now automated
- Shared GitHub bootstrap for either provider
- ComfyUI foundation
- Three pinned, user-owned H3 custom-node repositories
- Expected H3 model directory checks
- Optional, untested memory-mode launch policy

## Not automated
- Model weights
- Missing H3 Connector
- Full workflow JSON
- Authenticated web access
- Actual H3 model-specific chunking/offload
