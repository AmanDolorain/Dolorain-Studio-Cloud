# Independent Box Engine (opt-in extensions)

Transport stays model-agnostic; workflow parsing remains solely in Studio's adapter.

| Component | Purpose | Activation |
|---|---|---|
| \`bounded_flow.py\` | Bounded in-flight CPU queue and backpressure | \`BoxEngine.transfer()\` |
| \`box_engine.py\` | Opaque Packet façade and optional integrations | Explicit method invocation |
| \`fair_scheduler.py\` | Priority / route fairness with bounded credits | \`transfer_scheduled()\` |
| \`disk_spill.py\` | Temporary raw bytes spill, quota, free-space reserve, cleanup | \`transfer_spilled(..., directory=..., max_disk_bytes=...)\` |
| \`gpu_transfer.py\` | CUDA/PyTorch tensor copies and event completion | \`transfer_gpu(..., destination=...)\` |
| \`gpu_smoke.py\` | Manual small reversible GPU copy test | \`python pipeline/gpu_smoke.py\` |

**Important:** These utilities are wired to the Box Engine facade, but are **not activated automatically** for H3 or any generation workflow. The Studio bottom drawer still provides diagnostic read-only APIs. No model data or node types reach the transport. A compatible PyTorch already installed in the environment is required only when explicitly invoking the CUDA adapter.

For details, risks and missing hardware tests see [Box Engine integration](../docs/box-engine-integration.md).
