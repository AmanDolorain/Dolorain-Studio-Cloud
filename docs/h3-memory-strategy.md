# H3 memory strategy (planning, not an implemented H3 chunker)

## Automatic without extra workflow nodes
The launcher can select a conservative ComfyUI memory mode from the GPU's detected total and free VRAM. 24 GB cards start with `--lowvram`; 32/48 GB cards with `--normalvram`, plus a reserve. These are launch-time choices and do not alter the workflow graph.

## Model-specific capabilities to verify before implementing
- ComfyUI's native model offload behavior and compatibility with the exact MiniMax H3 Ref2V loader.
- Attention implementations supported by the installed torch/CUDA/model (SageAttention only when verified).
- Temporal chunking, VAE tiling and decoding only if the H3 implementation exposes compatible options.
- Whether mixed CPU/GPU staging improves throughput or merely adds PCIe transfer overhead.

Do not insert arbitrary chunking between diffusion steps or assume it preserves temporal attention. Model weights and intermediate activations may require simultaneous GPU residency.

## Security and integration
The adaptive launcher binds ComfyUI to localhost by default. Provider proxy/authentication must be configured separately before external access. It is opt-in; existing provider services should not be launched twice.

## Current status
GPU policy is a standalone script, not yet connected to the platform launchers. No GPU test or H3 generation test has been performed.
