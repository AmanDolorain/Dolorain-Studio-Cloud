# Dolorain Box Engine — integration status (2026-11-04)

## Connected in this repository

- `studio/index.html` shows an optional bottom **Box Engine** drawer without exposing the original engine's canvas.
- `studio/backend/server.py` routes `GET /api/box/status` and `POST /api/box/inspect` to `pipeline/box_engine.py` when the repository's `pipeline/` folder is present.
- `pipeline/box_engine.py` reuses existing `BoundedFlow` CPU worker queue for a read-only structural check of workflow node IDs and links. It reads `gpu_policy.probe/plan` for planning information only.
- No extra pip dependencies or model downloads; no change to queued generations, launch flags, or GPU memory behavior.
- The provided H3 graph was checked: 22 nodes, 29 links, 0 structural warnings. Studio backend API tests and Python unit tests passed in a local test environment. Chromium browsing was blocked by this environment's navigation policy; end-to-end UI and GPU testing remains outstanding.

## Still missing

1. Identify and verify the exact Hugging Face model discussed for connection intelligence; its name is not recorded in the current GitHub repo. `DSC_BOX_CONNECTION_MODEL` is metadata-only; no model is downloaded, loaded, or run.
2. Map the model's actual inputs/outputs to Studio connection suggestions; add opt-in human approval before editing links.
3. H3-specific supported CPU/GPU offload, VAE tiling, temporal chunking, scheduling and memory benchmarks on 24/32/48 GB GPU hardware.
4. Connect the Studio frontend to Vast.ai/RunPod launchers without exposing the original UI. Current provider setup scripts were left untouched.
5. Full Windows deployment compatibility and browser UI tests; the source checkout needs `pipeline/` alongside `studio/`.

## Guardrails

Box Engine is observe-only. The GPU policy's calculated flags are not applied. Never claim CPU queues increase GPU VRAM or that structural validation proves a workflow can execute. Keep the existing backend headless and private; use authenticated proxy or SSH tunnel for remote access. Do not commit models, passwords, or tokens.
