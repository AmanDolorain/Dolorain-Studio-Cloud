# Dolorain Studio — MiniMax H3 / Original ComfyUI

## Objective
Run the original ComfyUI on Vast.ai using a compatible prebuilt CUDA/PyTorch environment. A custom Studio UI and a separately maintained Docker image are not required.

## Required Project Files
- `workflows/01_Character_Sheet_Designer.json`
- `workflows/02_H3_Video_Generation.json`
- A reproducible installation manifest for required ComfyUI custom nodes
- Vast.ai setup, update, verification, and startup scripts
- A separate process for downloading model weights directly to Vast.ai; model weights will not be committed to GitHub

## Development and Validation
1. Prepare the replacement project files on the `h3-comfyui-rebuild` branch.
2. Test ComfyUI startup, custom nodes, workflow loading, and H3 video generation on a Vast.ai GPU instance.
3. Replace the `main` branch contents only after user approval.

## Current Status
This document is a preparation plan only. The existing `main` branch has not been modified. Do not assume that the existing Dockerfile can be used as a Vast.ai setup script.
