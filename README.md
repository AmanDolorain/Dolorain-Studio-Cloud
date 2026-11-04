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

## Independent Box Engine (opt-in extensions)

The Studio adapter alone knows workflow nodes and links. The independent, model-agnostic Box Engine handles opaque payloads with bounded CPU credits. **Fair route scheduling**, **temporary disk spill**, and **PyTorch CUDA tensor transfer with event synchronization** are available as explicit opt-in APIs in `pipeline/`. They are not wired into H3 generation; inference remains unchanged.

No models or third-party packages are downloaded automatically. Actual RTX GPU tests, H3-specific offload/quality comparison, Windows deployment and cloud-launch integration remain outstanding.

See [implementation and remaining validation](docs/box-engine-integration.md).

## RunPod CUDA 13.2 template

Open HTTP 8765 for Dolorain Studio and HTTP 8888 for JupyterLab. Keep the existing template credentials. Studio can open JupyterLab using the optional single-login setting. Studio hosts the native node editor and its developer extensions. **Logs · Diagnostics** provides a copyable execution and layer report. The existing dashboard is accessible from the Studio header.

Build the image from this revision before deploying a fresh Pod. The image build includes a CPU boot check for both browser services. Live hardware and H3 generation require a separate test. See the [RunPod access guide](deploy/runpod/WEB-ACCESS.md).
