# Dolorain Studio — MiniMax H3 on Vast.ai

This repository is intended for the **original ComfyUI**, not a custom frontend or a custom Docker image.

## Deployment
Start a Vast.ai instance with a suitable prebuilt PyTorch/CUDA environment and persistent storage if required. Check the base image's Python, CUDA, and PyTorch compatibility before installing dependencies.

Clone this repository and run:

```bash
git clone https://github.com/AmanDolorain/Dolorain-Studio-Cloud.git
cd Dolorain-Studio-Cloud
bash scripts/setup.sh
bash scripts/verify.sh
bash scripts/start.sh
```

For subsequent changes, use `git pull --ff-only` followed by `bash scripts/setup.sh`. Restart ComfyUI after changing custom nodes or Python dependencies.

## Models
Download model weights directly on Vast.ai into the appropriate `ComfyUI/models/` subdirectories. Do not commit model weights or credentials.

## Workflows
The two original H3 workflow JSON files must be copied into `workflows/` before this repository is considered deployable. They are **not yet included in this initial source reset**.

## Status
This is a source reset and setup scaffold, **not a validated GPU-ready release**. Verify the workflow JSON files, model filenames, node compatibility, and GPU generation before production use.
