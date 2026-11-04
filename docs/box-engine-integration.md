# Independent Dolorain Box Engine — architecture and status (2026-11-04)

## Boundary

```text
Dolorain Studio workflow (nodes, types, model-specific controls)
     |
     v
studio/backend/box_adapter.py   [workflow-aware, graph diagnostics]
     |
     | opaque Packet(payload, size_bytes, route)
     v
pipeline/box_engine.py          [model-agnostic, workflow-agnostic]
     |
     v
pipeline/bounded_flow.py        [bounded transport, producer backpressure]
     |
     v
consumer callback / future GPU adapter
```

**Box Engine is not an AI model.** It must never choose a model, inspect node types, validate sockets, parse workflow JSON, or alter execution graphs. The Studio adapter alone knows node IDs and graph links and passes opaque route descriptors to the transport.

## Implemented now

- Reuses the existing Python standard-library BoundedFlow; no Hugging Face weights, new pip packages, vendor frameworks or model downloads.
- Bounded item count and byte credits; credits include queued and consumer-held packets until callback returns.
- Producer backpressure, error propagation, cancellation signaling and draining queued credits on failure.
- Opaque Packet payload with caller-supplied byte length and opaque route.
- Studio-only structural node/link checks; Box Engine handles **only** opaque route metadata.
- Bottom Studio Box Engine panel displays queue and byte budget, GPU policy observation and Studio adapter diagnostics.
- `GET /api/box/status` and `POST /api/box/inspect` are still read-only.
- The previous node-aware functions and Hugging Face model metadata have been removed from Box Engine.
- Python unit tests: 14 passed locally, covering CPU transport, bounds, errors, adapter validation and legacy bridge prompt translation.
- Node.js syntax check passed for the frontend JavaScript. GPU production and on-device browser tests were **not** performed.

## Not implemented (do not claim otherwise)

- No automated GPU tensor scheduling, memory relocation, offload, VAE tiling or temporal chunking.
- No actual GPU buffer adapter with completion-event acknowledgement.
- No disk spill, persisted job queue, distributed transport, cross-process shared memory or multi-consumer routing yet.
- No general byte-size inference for arbitrary payloads; the adapter must supply accurate `size_bytes`.
- No changes to H3 generation path, cloud startup behavior or installed dependencies.
- No automatic connection suggestions or AI graph inference.
- Existing GPU policy is displayed by Studio adapter only, not applied by Box Engine.
- A third-party inference engine is still used headlessly in the backend.

## Next safe milestone

Build a **separate, opt-in** backend adapter for one safe supported data-buffer boundary. It must know the actual buffer size, wait for asynchronous device completion before reporting ACK, measure peak VRAM/RAM/time, and pass equivalence tests on 24/32 GB GPUs. Never interpose generic queues into H3 diffusion internal operations without model-specific evidence.
