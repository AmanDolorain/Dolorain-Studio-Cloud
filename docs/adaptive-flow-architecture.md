# Dolorain Adaptive Flow Pipeline (DAFP)

Status: **CPU diagnostic prototype wired to Dolorain Studio's Box Engine drawer**. GPU scheduling and MiniMax H3 execution **remain unintegrated**.

## Intent
Two cooperating layers:
1. Node/data flow: bounded CPU-memory queues, spill to SSD, backpressure, and release of references when downstream confirms consumption.
2. GPU flow: inspect actual available VRAM; schedule transfers with a safety reserve; optionally overlap transfers and compute where the backend supports it.

## What this cannot do
- Lengthening or looping a pipe does not increase VRAM.
- Buffering full tensors in RAM or disk does not make a 48 GB peak GPU operation fit a 24 GB GPU without genuine tiling, offload, quantization or model-specific partitioning.
- A diffusion step may need complete latent state; arbitrary frame-by-frame streaming can break attention and temporal consistency.
- CUDA operations and dependent ComfyUI nodes cannot be made fully asynchronous just by adding a queue.
- Larger queues increase memory usage and latency; the goal is **bounded** flow, not filling an unlimited pipe.

## Proposed stages
Input node -> bounded staging queue -> optional disk spill -> GPU admission controller -> supported transfer/compute -> output queue -> downstream node.

Backpressure: producer blocks when queue is full; no silent data loss. Consumer releases buffer ownership only after work is complete. GPU admission should use real free VRAM and a configurable safety reserve; capacity is not simply total VRAM.

## Integration plan
1. Collect baseline peak VRAM, RAM, transfer time, and generation time on 24 GB and 48 GB hardware.
2. Validate model-specific supported offloading and chunking (H3 implementation first).
3. Wrap only safe input/output stages with bounded streaming queues.
4. Add explicit synchronization and error propagation.
5. Test output equivalence, deterministic seeds where applicable, and failure recovery.
6. Enable as an opt-in experimental ComfyUI custom node, never default on an untested GPU instance.

## Safety
Do not automatically grow queues to the size of incoming data. Use a bounded RAM budget and optional disk spill with capacity checks. A producer can be blocked by backpressure; this is intentional and safer than OOM.
