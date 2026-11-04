# Dolorain Studio Cloud

**Dolorain Studio** is the primary workflow editor interface. This repository contains the Studio editor source under [`studio/`](studio/) and the existing Vast.ai / RunPod GPU setup scripts.

## Studio workflow editor

- Studio View and editable Node Graph View use the same workflow.
- Includes the H3 example graph, canvas controls, workflow tabs, fullscreen and keyboard shortcuts.
- Workflow names can be renamed from the open tab or workflow chooser; the chooser includes Open (play) and Delete (trash) controls.
- See [Studio source and instructions](studio/README.md).

**Important:** The visible ComfyUI canvas is not required. For now, inference still relies on an existing compatible **headless ComfyUI backend**, which supports custom nodes and GPU execution. A fully ComfyUI-free inference engine has **not** been built or verified.

## Reuse existing installations before downloading

Use the already installed compatible ComfyUI backend, Python packages, custom nodes, and model weights where available. The Studio source does not bundle models, a virtual environment, or the third-party ComfyUI distribution.

For a live local API connection, start an existing ComfyUI instance first and launch the bridge with the correct *local loopback* port, for example:

```bash
python studio/backend/server.py --comfy http://127.0.0.1:8188
```

Run the above from the repository root, with a compatible Python installation. Then open `http://127.0.0.1:8765`. The bridge itself uses Python's standard library. For cloud machines, use SSH port forwarding or another appropriate access-controlled tunnel. Do not expose the loopback-only bridge publicly.

**Avoid accidental installs:** `studio/start-local.bat` is the Windows full-distribution launcher, **not** the reuse-only launcher. Its `install()` routine can create a virtual environment and install requirements when the bundled engine is offline. It requires the separate full Windows distribution with `engine/` and wheels. Do not run it from the source-only checkout expecting a working inference engine. Existing cloud `setup.sh` also performs dependency installation by default; inspect its flags before running.

## Existing Vast.ai / RunPod setup (legacy backend)

- `setup.sh` — shared ComfyUI foundation; reuses an existing Git checkout (but may still install Python requirements).
- `launch-vast.sh` and `launch-runpod.sh` — provider wrappers.
- `config/`, `scripts/`, `pipeline/` — prior GPU setup and experiments.

Those existing files are preserved for compatibility and have **not** been switched automatically to the new Studio UI. The new frontend-to-cloud integration still requires target-GPU validation.

## Status

- Studio editor source committed and backend's five Python unit tests pass in the staging environment.
- Workflow rename/open/delete and fullscreen UI behavior have browser-based test evidence from the staged editor.
- Windows target-machine installation, full H3 GPU video generation, and cross-provider launch integration are **not yet verified**.
- No model weights, passwords, user workflows, generated videos, wheel bundles or large vendor dependencies are committed.

## Box Engine (experimental Studio connection)

The bottom **Box Engine** drawer is wired to the existing `pipeline/bounded_flow.py` CPU pipeline and `pipeline/gpu_policy.py` GPU **planning** policy through `pipeline/box_engine.py` and Studio bridge endpoints. It can inspect workflow connections and report VRAM planning status. It **does not** alter generation scheduling, run H3 tensor chunking, or auto-download Hugging Face models.

See [Box Engine integration status](docs/box-engine-integration.md). The previously discussed Hugging Face connection model is **not identified/connected** yet.
