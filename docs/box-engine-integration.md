# Dolorain Box Engine — Independent Transport (2026-11-04)

## Architecture and invariant

\`\`\`text
Dolorain Studio
    |
    v
Studio Adapter (knows workflows, nodes and graph links)
    |
    v
Independent Box Engine (ONLY opaque payloads, byte sizes, route labels)
    |                 |                   |
    +-- bounded RAM --+-- opt-in spill ---+-- opt-in fair scheduler
    |
    +-- opt-in PyTorch CUDA transfer adapter (no model or workflow knowledge)
    |
    v
Consumer callback / completion acknowledgement
\`\`\`

Only the Studio adapter parses workflow JSON. **Box Engine does not parse graphs, model names, node types, tensor semantics, prompts, or H3 parameters.** Runtime model selection and model-specific GPU offloading remain outside Box Engine.

## Implemented in GitHub source

- \`pipeline/bounded_flow.py\`: bounded in-flight item and byte credits with producer backpressure; credits released when consumer callback returns, with error propagation.
- \`pipeline/box_engine.py\`: explicit \`transfer()\`, \`transfer_scheduled()\`, \`transfer_spilled()\`, \`transfer_gpu()\`; all optional, none auto-intercept running jobs.
- \`pipeline/fair_scheduler.py\`: route FIFO + round-robin within each priority, bounded higher-priority bursts, bounded queue credits and failure propagation. Priority does not promise real-time scheduling.
- \`pipeline/disk_spill.py\`: opt-in, temporary, private directory for bytes-only payloads; configured quota and minimum free-space reserve, chunked reads, and cleanup on successful or failed delivery. Not a durable queue.
- \`pipeline/gpu_transfer.py\`: PyTorch CUDA tensor copy adapter using **existing PyTorch only**, explicit device, copy-size and free-VRAM safety checks, CUDA stream synchronization and completion events. Output is consumed before acknowledgement. Does not change diffusion scheduling.
- \`pipeline/gpu_smoke.py\`: **manual**, small host-to-device-to-host exact-data test. Skips when CUDA or PyTorch is absent. Run from repository root using \`python pipeline/gpu_smoke.py\`.
- \`studio/backend/box_adapter.py\`: Studio-only workflow validation and GPU policy observations.
- \`studio/backend/server.py\`: optional read-only Box API; queued inference is unchanged.
- \`studio/tests/test_box_engine.py\` and \`studio/tests/test_box_runtime_extensions.py\`: CPU/fake-CUDA contract tests.

## Tests and validation distinction

Earlier foundation reported 24 local Python unit tests passing. **The newest combined integration and newly committed extension-test suite have not been executed against the exact final GitHub commit in this assistant turn**; code presence does not prove test success. Neither a real NVIDIA RTX GPU nor a Vast.ai/RunPod deployment was available to execute the CUDA smoke test. Do not label GPU integration production-tested.

Recommended checks from repository root:

\`\`\`bash
python -m unittest discover -s studio/tests -p 'test_*.py' -v
python pipeline/gpu_smoke.py
\`\`\`

The second command should run only on an owner-approved GPU instance, after checking the instance is idle. Running it uses a small amount of VRAM and time. The script installs nothing.

## Not completed / production blockers

1. **Real RTX GPU smoke test** and peak-VRAM/RAM measurement; demonstrate exact round-trip bytes and safe event acknowledgment on actual CUDA/PyTorch.
2. **H3 generation-path opt-in integration**: Box Engine CUDA transfers are explicit utility APIs, **not plugged into the running H3 diffusion backend**. Safe offload/tiling must be implemented at supported boundaries and quality-benchmarked separately.
3. **Windows app deployment**: updating GitHub source does **not** modify the user's existing Windows Studio installation. Target-machine regression and packaging tests remain.
4. **Cloud launcher/front-end wiring**: current Vast.ai and RunPod launch scripts are unchanged. A headless engine is expected; secure proxy and auth need separate testing.
5. Robust multi-process/remote spill and device-memory ownership are not implemented. Temporary disk spill is local-only, explicitly opt-in and cleans up on normal termination.

## Data safety

No automatic model download, pip installation, third-party hosted service, public bridge endpoint, background GPU process or secret is added. Explicit disk spill should be used only in an authorized scratch directory because it writes unencrypted raw bytes; never spill secrets or private prompts without a dedicated security design. Disk quotas are a per-manager limit; external processes may also consume disk. Existing H3 inference remains untouched until validated and explicitly enabled.
