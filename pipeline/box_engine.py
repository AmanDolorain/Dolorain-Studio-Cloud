"""Independent Dolorain Box Engine: opaque, bounded data transport.

No model, workflow, node-graph or inference scheduling knowledge.
Optional components are imported ONLY on explicit invocation:
  - route-fair priority scheduling (CPU only)
  - private bounded disk spill for bytes-like buffers
  - CUDA tensor adapter with completion event synchronization
None of these intercept a running inference process automatically.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from bounded_flow import BoundedFlow, FlowStats


@dataclass(frozen=True)
class Packet:
    payload: Any
    size_bytes: int
    route: str = ''  # Opaque routing identifier, assigned by application adapter.


class BoxEngine:
    def __init__(self, queue_items: int = 2, memory_budget_bytes: int = 8 * 1024 * 1024):
        self.flow = BoundedFlow[Packet](queue_items, memory_budget_bytes)

    def transfer(self, packets: Iterable[Packet], deliver: Callable[[Packet], None]) -> FlowStats:
        """Synchronously deliver opaque packets with bounded in-flight credits.

        For asynchronous consumers, deliver() MUST await underlying completion
        before returning. This includes CUDA events and disk/network transfers.
        """
        def size(packet: Packet) -> int:
            if not isinstance(packet, Packet):
                raise TypeError('Box Engine accepts Packet envelopes only')
            return packet.size_bytes
        return self.flow.run(packets, deliver, size_of=size)

    def transfer_scheduled(self, packets: Iterable[Any], deliver: Callable[[Any], None],
                           urgent_burst: int = 3):
        """Opt-in per-route fair priority delivery; packets are opaque Scheduled envelopes."""
        from fair_scheduler import FairScheduler
        return FairScheduler(self.flow.max_items, self.flow.max_bytes, urgent_burst).run(packets, deliver)

    def transfer_spilled(self, packets: Iterable[Packet], deliver: Callable[[Packet], None],
                         *, directory: str, max_disk_bytes: int,
                         min_free_bytes: int = 256 * 1024 * 1024):
        """Opt-in bounded disk spill of raw bytes, with automatic cleanup.

        The downstream callback gets Packet(payload=SpillRef, route=..., size_bytes=...).
        It must consume SpillRef.iter_chunks() before returning. A spill handle
        becomes invalid immediately after callback returns. Disk bytes are
        accounted separately; queued Packet.size_bytes=1 is a METADATA unit.
        A caller must not keep its own large payload objects alive indefinitely.
        """
        from disk_spill import DiskSpill

        with DiskSpill(directory, max_disk_bytes, min_free_bytes) as spool:
            def staged():
                for packet in packets:
                    if not isinstance(packet, Packet):
                        raise TypeError('Expected Packet envelopes for spill')
                    if not isinstance(packet.payload, (bytes, bytearray, memoryview)):
                        raise TypeError('Spill supports only bytes-like payloads')
                    payload = packet.payload
                    real_bytes = memoryview(payload).nbytes
                    if packet.size_bytes != real_bytes:
                        raise ValueError('Declared packet size differs from actual bytes')
                    route = packet.route
                    ref = spool.put(payload)
                    del packet, payload
                    # Queue contains only metadata, not the original bytes.
                    yield Packet(ref, 1, route)

            def delivered(packet: Packet) -> None:
                ref = packet.payload
                try:
                    deliver(Packet(ref, ref.size_bytes, packet.route))
                finally:
                    spool.release(ref)  # ACK, or failure cleanup.

            return self.transfer(staged(), delivered)

    def transfer_gpu(self, tensors: Iterable[Any], destination: str,
                     on_complete: Callable[[Any], None], *,
                     device: str = 'cuda:0',
                     reserve_bytes: int = 512 * 1024 * 1024,
                     max_copy_bytes: int = 1024 * 1024 * 1024,
                     torch_module: Any = None):
        """Opt-in CUDA copy via a separate adapter. Never modifies running H3 jobs."""
        from gpu_transfer import TorchCudaAdapter
        adapter = TorchCudaAdapter(
            device=device, reserve_bytes=reserve_bytes, max_copy_bytes=max_copy_bytes,
            queue_items=self.flow.max_items, memory_budget_bytes=self.flow.max_bytes,
            torch_module=torch_module)
        return adapter.transfer_tensors(tensors, destination, on_complete)

    def inspect_routes(self, routes: Iterable[dict]) -> dict:
        """Metadata-only diagnostic. Does not move real payloads or schedule GPU."""
        checked = 0
        def metadata_packets():
            for route in routes:
                if not isinstance(route, dict) or not isinstance(route.get('route'), str):
                    raise ValueError('Expected opaque route descriptor')
                yield Packet(route, 1, route['route'])
        def observe(_packet: Packet) -> None:
            nonlocal checked
            checked += 1
        stats = self.transfer(metadata_packets(), observe)
        return {
            'mode': 'metadata_only', 'checked_routes': checked,
            'queue_capacity': self.flow.max_items,
            'memory_budget_bytes': self.flow.max_bytes,
            'peak_reserved_items': stats.peak_reserved_items,
            'peak_reserved_bytes': stats.peak_reserved_bytes,
            'backpressure_waits': stats.backpressure_waits,
        }

    def status(self) -> dict:
        return {
            'name': 'Dolorain Box Engine', 'mode': 'independent_transport',
            'workflow_aware': False, 'model_aware': False,
            'queue_capacity': self.flow.max_items,
            'memory_budget_bytes': self.flow.max_bytes,
            'execution_hook': 'adapter_required',
            'optional_features': {
                'fair_scheduler': 'opt_in',
                'disk_spill': 'opt_in',
                'cuda_transfer': 'opt_in_requires_existing_torch_cuda',
            },
            'gpu_execution_interception': False,
        }
