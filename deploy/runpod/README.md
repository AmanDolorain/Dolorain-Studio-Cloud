# Dolorain Studio — Own CUDA 13.2 RunPod Template (candidate)

**Status: source template prepared; image NOT built or published; GPU compatibility NOT certified.**

Branding: black-and-white **D** at [studio/brand/d-logo.svg](../../studio/brand/d-logo.svg). The Studio header uses this asset. It is original SVG artwork, not a third-party font/logo. For the RunPod template icon, use the raw URL of this SVG if accepted; otherwise export it to PNG (not yet produced/published).

## Product layers

1. **Owned**: Dolorain Studio interface, Studio Adapter, Independent Box Engine, deployment scripts and branding.
2. **Temporary third-party runtime**: NVIDIA CUDA, PyTorch and a pinned headless ComfyUI inference compatibility engine. Studio hosts the native editor and installed developer extensions through its browser endpoint.
3. **Persistent user data**: H3 weight files and license-verified assets, inputs, outputs and workflows under `/workspace/dolorain/`. None are bundled into the image.

Our long-term engine must replace the temporary inference backend *only* after MiniMax H3 loaders, text/audio/video VAEs, diffusion/sampling, GPU memory, video output and workflow equivalence tests pass. The inference backend is not our original code; own packaging is not the same as owning every component.

## Verified upstream references / proposed pins

- Base: `nvidia/cuda:13.2.1-cudnn-runtime-ubuntu24.04` (published NVIDIA image).
- PyTorch: `torch==2.13.0`, `torchvision==0.28.0`, CUDA 13.2 wheels (Python 3.12 x86_64).
- Temporary ComfyUI checkout: `56f179f6c50dad0c4c860ae4da427415c8e86415`.
- Three user-owned H3 controller repositories pinned in `config/custom-nodes.tsv`. **H3 Connector and full H3 model-loader compatibility are not yet proven**.
- Host driver policy: require NVIDIA Linux driver **595.45.04 or newer**, deliberately strict relative to CUDA minor-version compatibility. At cheaper GPUs, check the **host driver before renting**.

The Dockerfile deliberately installs only ComfyUI's core requirements and three known, pinned user-owned node repositories. This is a compatibility-stage **minimum candidate**, not a complete audited dependency lock: transitive Python versions and Docker base digest still need a full successful image build, license review, pinning and SBOM before production.

## One-click manual GitHub image build

This repository includes [**Build Dolorain CUDA 13.2 image**](../../.github/workflows/build-dolorain-cuda132.yml), a **workflow_dispatch-only** GitHub Actions workflow. In GitHub, open **Actions → Dolorain CUDA 13.2 image - manual build → Run workflow**. It runs source tests and then attempts to publish the image to GHCR. Check the workflow logs for a real PASS before entering an image name in RunPod.

Requested candidate image name after a **successful** build: `ghcr.io/amandolorain/dolorain-studio:cuda13.2-candidate`. This URL does **not** assert that the image already exists. Make GHCR package public or configure registry credentials for RunPod. Avoid reusing this mutable candidate tag for production; use a release-specific immutable digest after GPU validation.

## Build/publish first — do not rent a GPU yet

From an authorized Docker build machine (or manually triggered GitHub Actions workflow), build at repository root:

```bash
docker build -f deploy/runpod/Dockerfile -t dolorain-studio:cuda13.2 .
```

Do not treat this command as having run: **this GitHub source commit does not publish a container registry image.**

Optional registry publication, after build/test and your authorization:

```bash
docker tag dolorain-studio:cuda13.2 ghcr.io/amandolorain/dolorain-studio:cuda13.2-test
docker push ghcr.io/amandolorain/dolorain-studio:cuda13.2-test
```

The registry package must be made visible to RunPod, or authenticated pull must be configured. No image is assumed to exist at those tags.

## RunPod template

The browser services are Dolorain Studio on HTTP 8765 and JupyterLab on HTTP 8888. The engine stays on loopback. See [current access settings and diagnostics](WEB-ACCESS.md). Use the image entrypoint and mount the persistent volume at `/workspace`.

## Safe test sequence

1. Confirm provider instance price including **GPU, disk, internet and idle persistent storage fees**, and **host driver >=595.45.04**.
2. Build/publish image without renting an A40, if your build service supports it.
3. Boot cheap candidate Pod; read `preflight.py` result and GPU compute architecture, PyTorch/CUDA integrity, startup logs.
4. Run `python -m unittest discover -s /opt/dolorain/src/studio/tests -p 'test_*.py' -v`.
5. Run `python /opt/dolorain/src/pipeline/gpu_smoke.py` (small GPU copy; not H3 generation).
6. Check existing persistent model filenames with `bash /opt/dolorain/src/deploy/runpod/check-required-models.sh`. Check SHA256 separately; filename alone proves nothing.
7. Inspect `/object_info` for required H3 node types; only then attempt a **small, paid H3 video** after validating an authorized GPU budget and licenses.
8. Stop/delete Pod after work; check lingering disk/volume charges.

## Explicit limitations

No A40/3090/A30/4090 CUDA 13.2 device test was performed. The image was not built or published. The H3 Connector is not installed because its source is not verified. Model weights are not downloaded. CUDA 13.2 compatibility for H3/SageAttention is not established. Template configuration in RunPod's account has **not** been created.

No new installs or model downloads occur on every Pod startup; package installation occurs **once per Docker image build**. Persistent GPU data stays outside the image.
