"""Optional PyTorch CUDA buffer-transfer adapter for the independent Box Engine.

CUDA/Torch is imported only when explicitly creating this adapter. It never
loads model weights, inspects workflows, replaces H3 operators or installs deps.
Each transfer waits for its own completion event BEFORE returning buffer credit.
"""
from __future__ import annotations

from dataclasses import dataclass
import importlib
import time
from typing import Any, Callable, Iterable

from box_engine import BoxEngine, Packet


@dataclass
class TensorCopy:
    tensor: Any
    direction: str
    size_bytes: int
    milliseconds: float
    synchronized: bool
    free_cuda_bytes_before: int | None = None
    free_cuda_bytes_after: int | None = None


class TorchCudaAdapter:
    def __init__(self, device: str = 'cuda:0', *, reserve_bytes: int = 512 * 1024 * 1024,
                 max_copy_bytes: int = 1024 * 1024 * 1024,
                 queue_items: int = 2, memory_budget_bytes: int = 1024 * 1024 * 1024,
                 torch_module: Any = None):
        if not isinstance(device, str) or not device.startswith('cuda:') or not device[5:].isdigit():
            raise ValueError('Explicit CUDA device such as cuda:0 is required')
        if type(reserve_bytes) is not int or reserve_bytes < 0:
            raise ValueError('reserve_bytes must be non-negative')
        if type(max_copy_bytes) is not int or max_copy_bytes < 1:
            raise ValueError('max_copy_bytes must be positive')
        self.torch = torch_module if torch_module is not None else importlib.import_module('torch')
        if not self.torch.cuda.is_available():
            raise RuntimeError('CUDA is unavailable. No GPU transfer was attempted.')
        self.device, self.reserve_bytes, self.max_copy_bytes = device, reserve_bytes, max_copy_bytes
        self.box = BoxEngine(queue_items, memory_budget_bytes)

    @staticmethod
    def _nbytes(tensor: Any) -> int:
        return int(tensor.numel()) * int(tensor.element_size())

    def copy_tensor(self, tensor: Any, destination: str) -> TensorCopy:
        """One explicit CPU<->CUDA copy; event synchronization is mandatory.

        Caller controls source tensor lifetime; output may be consumed after
        return. No automatic deep-model offloading or GPU scheduler changes.
        """
        torch = self.torch
        if not isinstance(tensor, torch.Tensor) or tensor.layout != torch.strided:
            raise TypeError('Expected a dense PyTorch Tensor')
        source = tensor.device.type
        if destination not in ('cpu', self.device):
            raise ValueError('Destination must be cpu or configured CUDA device')
        if source == 'cpu' and destination != self.device:
            raise ValueError('For CPU source, destination must be CUDA')
        if source == 'cuda' and destination != 'cpu':
            raise ValueError('For CUDA source, destination must be CPU')
        if source not in ('cpu', 'cuda'):
            raise ValueError('Only CPU and CUDA sources supported')
        if source == 'cuda' and str(tensor.device) != self.device:
            raise ValueError('Source CUDA device does not match configured device')
        size = self._nbytes(tensor)
        if size > self.max_copy_bytes:
            raise ValueError('Tensor exceeds maximum allowed transfer size')
        before = self.torch.cuda.mem_get_info(self.device)[0]
        if destination == self.device and before - size < self.reserve_bytes:
            raise MemoryError('Not enough free GPU memory above safety reserve')
        start = time.monotonic()
        stream = torch.cuda.Stream(device=self.device)
        # GPU inputs may still be in-flight on the caller's current stream.
        if source == 'cuda':
            stream.wait_stream(torch.cuda.current_stream(self.device))
        with torch.cuda.stream(stream):
            output = tensor.to(destination, non_blocking=True)
            event = torch.cuda.Event()
            event.record(stream)
        event.synchronize()  # Never ACK an asynchronous copy before completion.
        after = self.torch.cuda.mem_get_info(self.device)[0]
        return TensorCopy(output, f'{source}_to_{"cuda" if destination == self.device else "cpu"}',
                          size, (time.monotonic() - start) * 1000, True, before, after)

    def transfer_tensors(self, tensors: Iterable[Any], destination: str,
                         on_complete: Callable[[TensorCopy], None]):
        """Opt-in transfer with Box Engine credits; no default H3 integration."""
        def packets():
            for tensor in tensors:
                yield Packet(tensor, self._nbytes(tensor))
        def consume(packet: Packet):
            completed = self.copy_tensor(packet.payload, destination)
            on_complete(completed)  # Must finish using result before returning/ACK.
        return self.box.transfer(packets(), consume)
