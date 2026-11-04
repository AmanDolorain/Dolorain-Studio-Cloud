# Dolorain Native Inference Engine — replacement gates

Goal: Dolorain Studio, workflow engine and Box Engine all controlled by the product owner, with no visible ComfyUI canvas. **This is a roadmap, not a completed native H3 implementation.**

## What we own today
- Studio interface, branding, workflows and graph editor.
- Independent Box Engine queue, scheduler, disk spill and optional CUDA copy utilities.
- Studio Adapter and deployment scripts.

## Temporary dependencies to eliminate later
- Headless ComfyUI inference runtime, node execution protocol and H3 loaders.
- ComfyUI-facing custom nodes (migration or native replacement needed).

## Dependencies that will legitimately remain
- NVIDIA driver, CUDA/cuDNN, GPU framework or separately maintained custom kernels and third-party model weights under their licenses.
- Owning the app does not mean inventing a GPU driver, reimplementing all CUDA mathematics or owning external model IP.

## Minimum native H3 runtime milestones
1. Record the exact currently working H3 workflow graph and model names, licenses, hashes, tensor formats and device memory peaks.
2. Build a versioned Dolorain API + typed node registry, not tied to ComfyUI's node format; canonical workflow conversion with import/export tests.
3. Implement and test model loading (text encoder, diffusion, audio/video VAEs, Turbo LoRA) without relying on ComfyUI internals.
4. Implement scheduler, noise, conditioning, audio/video timing, sampling, reference media and output encoding compatible with current H3 baseline.
5. Integrate the separate Box Engine only at measured safe data boundaries with correct GPU event ownership and no temporal consistency regressions.
6. Verify deterministic where supported, face consistency, motion, output quality, speed, peak VRAM and OOM recovery on A40 and RTX 3090; extend to RTX 4090/A30.
7. Compare functionality and speed side-by-side, then remove ComfyUI packages and the temporary adapter from *new* Docker image builds; retain rollback path.

**Exit criterion:** a complete H3 Ref2V workflow runs through the Dolorain runtime on an approved GPU, with correct references/audio/seed/export and measured results at least equivalent to the baseline.

Do not declare the native engine complete or remove the temporary runtime before these gates pass. A clean template includes only demonstrated dependencies, not an untested arbitrary strip-down that silently removes required functionality.
