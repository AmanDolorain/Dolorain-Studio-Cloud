# Dolorain Studio — Workflow Editor Source

The source of the Dolorain Studio v2.9.4 editor is in this directory. The workflow Rename/Open/Delete changes are included.

## Main files
- `index.html` — Studio and Graph UI, workflow tabs, shortcuts, fullscreen, rename/open/delete.
- `canvas_size.js`, `node_fields.js`, `manager_catalog.js` — UI support modules (catalog is a static browser catalog, not installed node packages).
- `backend/server.py` — local-only bridge for an **already running** compatible ComfyUI engine.
- `backend/start_studio.py` and `start-local.bat` — launcher for the **full Windows distribution**, not source-only checkout. This launcher may provision Python packages if the bundled engine is offline.
- `H3_Workflow_Fast_FaceDetail5.json` — example workflow.
- `tests/test_bridge.py` — backend workflow prompt tests.

## Use already installed ComfyUI and dependencies

1. Start the compatible engine you **already have**. Do not re-download models or custom nodes just because this UI source exists.
2. With Python 3 available, from repository root run:

```bash
python studio/backend/server.py --comfy http://127.0.0.1:8188
```

Change `8188` only when the existing engine uses a different **locally forwarded** port. Then browse to `http://127.0.0.1:8765`. The bridge itself uses standard Python libraries and does not install packages.
3. Confirm that needed model and custom node types are actually installed in the engine before generating. Existing model directory names alone do not prove the models are present.

Note: `start-local.bat` from the full Windows ZIP expects `engine/ComfyUI` and verified CPU wheels; they are intentionally *not* committed here. It can create a virtualenv and install dependencies. **Do not run it when you only want to reuse an existing environment.**

## Workflow controls

The active tab name supports double-click rename. The workflow chooser opened with `W` also supports double-click rename, a play icon to open, and a trash icon to delete with confirmation. Use the app's own Save command after edits. Fullscreen can be enabled through the file menu. Both views edit the same canonical graph.

## Scope and verification

This repository contains Studio frontend and local bridge **source**, not a portable installer. Windows testing, GPU H3 generation, provider startup wiring and standalone non-ComfyUI inference are not verified by this source-only update. Do not expose the bridge to the public internet without a separate access-controlled deployment.

## Independent Box Engine drawer (experimental)

The bottom Box Engine panel is a read-only view of the **independent transport**, with queue capacity and byte budget. `GET /api/box/status` observes transport configuration and separate GPU launch-policy recommendations. `POST /api/box/inspect` sends the current workflow to `studio/backend/box_adapter.py`, **never** to the Box Engine. The adapter validates Studio graph references and sends only opaque route IDs to the transport.

`pipeline/box_engine.py` knows no model names, node types or workflow format. Its data-transfer API works on opaque packets with explicit sizes and acknowledgement-based release. Real GPU execution is **not** yet routed through it. No AI model, pip package, or weight file is downloaded automatically.

The source checkout expects `pipeline/` next to `studio/`. Older standalone Windows distributions need their own incremental deployment of these source changes; GitHub edits do not update an existing local install.
