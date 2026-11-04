"""Independent Dolorain Box Engine transport: no workflow or model knowledge.

Only opaque envelopes, byte sizes, queue capacity, and consumer acknowledgement.
No GPU policy, ML framework, specific node types, network or installs.
"""
from __future__ import annotations

from dataclasses import dataclass
from typing import Any, Callable, Iterable

from bounded_flow import BoundedFlow, FlowStats


@dataclass(frozen=True)
class Packet:
    payload: Any
    size_bytes: int
    route: str = ''  # Opaque destination identifier; interpretation belongs to adapter.


class BoxEngine:
    def __init__(self, queue_items: int = 2, memory_budget_bytes: int = 8 * 1024 * 1024):
        self.flow = BoundedFlow[Packet](queue_items, memory_budget_bytes)

    def transfer(self, packets: Iterable[Packet], deliver: Callable[[Packet], None]) -> FlowStats:
        """Deliver packets with bounded credits; release on callback completion.

        For GPU buffers, an adapter MUST wait for its device completion event
        inside deliver() before returning. The engine never assumes that a
        returned async GPU launch has finished.
        """
        def size(packet: Packet) -> int:
            if not isinstance(packet, Packet):
                raise TypeError('Box Engine accepts Packet envelopes only')
            return packet.size_bytes
        return self.flow.run(packets, deliver, size_of=size)

    def inspect_routes(self, routes: Iterable[dict]) -> dict:
        """Exercise metadata through the same bounded transport, without data movement.

        This is a diagnostic path, NOT evidence of GPU-ready execution.
        """
        checked = 0
        def metadata_packets():
            for route in routes:
                if not isinstance(route, dict) or not isinstance(route.get('route'), str):
                    raise ValueError('Expected opaque route descriptors')
                yield Packet(route, 1, route['route'])
        def observe(_packet: Packet) -> None:
            nonlocal checked
            checked += 1
        s = self.transfer(metadata_packets(), observe)
        return {
            'mode': 'metadata_only', 'checked_routes': checked,
            'queue_capacity': self.flow.max_items,
            'memory_budget_bytes': self.flow.max_bytes,
            'peak_reserved_items': s.peak_reserved_items,
            'peak_reserved_bytes': s.peak_reserved_bytes,
            'backpressure_waits': s.backpressure_waits,
        }

    def status(self) -> dict:
        return {
            'name': 'Dolorain Box Engine', 'mode': 'independent_transport',
            'workflow_aware': False, 'model_aware': False,
            'queue_capacity': self.flow.max_items,
            'memory_budget_bytes': self.flow.max_bytes,
            'execution_hook': 'adapter_required',
        }
