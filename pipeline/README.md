# Experimental adaptive flow

The original `bounded_flow.py` remains a **CPU-only bounded producer/consumer proof of concept**; `gpu_policy.py` remains a **launch-flag recommendation**, not GPU scheduling or tensor chunking.

The new `box_engine.py` makes both components visible to Dolorain Studio via the local backend bridge:
- `GET /api/box/status` reads the current GPU probe and suggested launch policy, without applying it.
- `POST /api/box/inspect` analyzes the Studio workflow's node IDs and connection records using the bounded CPU queue, returning counts and structural warnings. It does not submit a GPU prompt.
- The Studio bottom **Box Engine** drawer is opt-in, collapsed by default.

No H3-specific offload, temporal chunking, model recommendation, AI inference, or ComfyUI GPU data-path changes are implemented. Do not turn planning output into live GPU flags without hardware tests.

See [Box Engine integration status](../docs/box-engine-integration.md) and [adaptive architecture](../docs/adaptive-flow-architecture.md).
