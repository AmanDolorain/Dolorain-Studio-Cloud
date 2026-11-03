# Experimental adaptive flow

This is a **CPU-only proof of concept** for bounded producer/consumer flow. It does not install as a ComfyUI node, access CUDA, or alter MiniMax H3 generation.

See [architecture](../docs/adaptive-flow-architecture.md).

Do not use the prototype for production or untrusted inputs. Its first revision assumes consumers do not raise exceptions. GPU-aware scheduling and ComfyUI integration will require separate testing.
