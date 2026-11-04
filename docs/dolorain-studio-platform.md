# Dolorain Studio: product architecture proposal

## Product principle
**No ComfyUI canvas in the user-facing application.** Use a purpose-built, responsive UI with fixed sections: Inputs, Models, Generation, Output. Automatically group compatible controls, with rounded section cards, strong contrast, consistent spacing and keyboard navigation. No manual node placement, color adjustment, or group sizing required.

## Architecture choices
**Phase 1 (recommended):** Dolorain Studio frontend -> typed workflow schema -> adapter -> headless ComfyUI execution backend. ComfyUI is installed only as a runtime dependency on the GPU machine, not presented as the UI. Existing ComfyUI custom nodes can run unchanged when compatible with that backend.

**Phase 2 (optional):** Replace ComfyUI backend with custom inference adapters. This requires porting custom nodes and verifying MiniMax H3 loaders, scheduling, VAE, attention, audio/video, and model lifecycle. It is not drop-in compatible with ComfyUI GitHub nodes.

## Default workspace
- Left navigation: Projects, Templates, Models, Runs, Settings
- Top: workflow name, GPU/VRAM indicator, run/stop, save
- Main: four ordered, automatically arranged rounded panels
  - Inputs: reference images, video, audio, prompt
  - Models: diffusion, text encoder, video/audio VAE, LoRA
  - Generation: resolution, FPS, length, seed, scheduler, sampling
  - Output: preview, progress, history, export
- Optional advanced graph view: read-only or auto-layout; no need to drag nodes
- Narrow screens: sections stack vertically; no giant infinite canvas

## Workflow engine
Versioned JSON workflow schema independent of frontend layout. Adapter translates to actual ComfyUI graph and validates required nodes before run. Backpressure and GPU memory policy are backend concerns, not visual graph decorations.

## Current status (2026-11-04)
The Dolorain Studio frontend, Studio Adapter and independent Box Engine exist as source code. A CUDA 13.2 **candidate** RunPod Dockerfile and a monochrome D brand asset also exist. The H3 inference path still uses a headless third-party backend. A fully native H3 inference service has not been implemented or GPU-tested. See [native-engine replacement gates](OWN_ENGINE_ROADMAP.md) and [RunPod template candidate](../deploy/runpod/README.md).
