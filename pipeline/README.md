# Independent Box Engine

The transport layer is model- and workflow-agnostic:
- `box_engine.py` accepts `Packet(payload, size_bytes, route)` envelopes and a consumer callback.
- `bounded_flow.py` applies item/byte budgets, backpressure and consumer acknowledgement. The opaque contents are never interpreted.
- `gpu_policy.py` is a separate **planning** utility; it does not control the Box Engine.

**Only** `studio/backend/box_adapter.py` knows Studio workflow nodes and links. It translates node/link metadata into opaque route identifiers; no model identity or node-type details enter the Box Engine. The Studio drawer and bridge provide read-only diagnostics and planning.

No external runtime dependencies or models are installed. H3 generation, GPU scheduling and provider scripts are unchanged. The CPU transport is functional, but the GPU data path is **not integrated**.

Details: [Box Engine status](../docs/box-engine-integration.md).
