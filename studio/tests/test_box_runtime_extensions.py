"""CPU + fake-CUDA opt-in integration tests. No model downloads or GPU required."""
from __future__ import annotations

import os
import tempfile
import unittest
from pathlib import Path
import sys
from types import SimpleNamespace

ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(ROOT / 'pipeline'))
from box_engine import BoxEngine, Packet
from disk_spill import DiskSpill
from fair_scheduler import FairScheduler, Scheduled
from gpu_transfer import TorchCudaAdapter


class DiskAndSchedulingTests(unittest.TestCase):
    def test_disk_spill_streams_and_cleans(self):
        with tempfile.TemporaryDirectory() as root:
            delivered = []
            engine = BoxEngine(queue_items=2, memory_budget_bytes=4)
            def receive(packet):
                self.assertEqual(packet.route, 'opaque-route')
                self.assertEqual(packet.size_bytes, 12)
                delivered.append(b''.join(packet.payload.iter_chunks(3)))
            stats = engine.transfer_spilled(
                [Packet(b'hello world!', 12, route='opaque-route')],
                receive, directory=root, max_disk_bytes=32, min_free_bytes=0)
            self.assertEqual(delivered, [b'hello world!'])
            self.assertEqual(stats.consumed, 1)
            self.assertLessEqual(stats.peak_reserved_bytes, 4)
            self.assertEqual(os.listdir(root), [])

    def test_disk_spill_failure_still_cleans(self):
        with tempfile.TemporaryDirectory() as root:
            def fail(_packet):
                raise ValueError('test failure')
            with self.assertRaisesRegex(RuntimeError, 'Flow consumer failed'):
                BoxEngine(queue_items=1, memory_budget_bytes=4).transfer_spilled(
                    [Packet(b'hello', 5)], fail, directory=root,
                    max_disk_bytes=32, min_free_bytes=0)
            self.assertEqual(os.listdir(root), [])

    def test_disk_quota_enforced(self):
        with tempfile.TemporaryDirectory() as root:
            with DiskSpill(root, max_disk_bytes=3, min_free_bytes=0) as spool:
                with self.assertRaises(ValueError):
                    spool.put(b'large')
                self.assertEqual(spool.used_bytes, 0)
            self.assertEqual(os.listdir(root), [])

    def test_wrong_spill_size_rejected(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaisesRegex(RuntimeError, 'Flow producer failed'):
                BoxEngine().transfer_spilled(
                    [Packet(b'x' * 9, 8)], lambda p: None, directory=root,
                    max_disk_bytes=20, min_free_bytes=0)
            self.assertEqual(os.listdir(root), [])

    def test_invalid_spill_root_never_created(self):
        with tempfile.TemporaryDirectory() as root:
            with self.assertRaises(ValueError):
                DiskSpill(Path(root) / 'not-approved', 8)

    def test_scheduler_no_losses_bounds_and_route_order(self):
        engine = BoxEngine(queue_items=3, memory_budget_bytes=10)
        data = [Scheduled(i, 2, route='R'+str(i % 2), priority=i % 3)
                for i in range(40)]
        received = []
        stats = engine.transfer_scheduled(data, received.append, urgent_burst=2)
        self.assertEqual(sorted(x.payload for x in received), list(range(40)))
        self.assertEqual(stats.consumed, 40)
        self.assertLessEqual(stats.peak_reserved_items, 3)
        self.assertLessEqual(stats.peak_reserved_bytes, 10)
        # Within one route and priority, FIFO order is never re-ordered.
        for route in ('R0', 'R1'):
            for priority in (0, 1, 2):
                original = [x.payload for x in data if x.route == route and x.priority == priority]
                actual = [x.payload for x in received if x.route == route and x.priority == priority]
                self.assertEqual(original, actual)

    def test_scheduler_rejects_unknown_priorities(self):
        with self.assertRaisesRegex(RuntimeError, 'Scheduled producer failed'):
            FairScheduler().run([Scheduled(b'x', 1, priority=999)], lambda item: None)

    def test_scheduler_propagates_consumer_failures(self):
        with self.assertRaisesRegex(RuntimeError, 'Scheduled consumer failed'):
            FairScheduler().run([Scheduled(1, 1)], lambda item: 1/0)

    def test_model_agnostic_engine_status(self):
        state = BoxEngine().status()
        self.assertFalse(state['model_aware'])
        self.assertFalse(state['workflow_aware'])
        self.assertFalse(state['gpu_execution_interception'])
        self.assertEqual(state['optional_features']['disk_spill'], 'opt_in')


class FakeDevice:
    def __init__(self, name):
        self.type = 'cuda' if name.startswith('cuda') else name
        self.name = name
    def __str__(self):
        return self.name


class FakeTensor:
    def __init__(self, data, device='cpu'):
        self.data = data
        self.device = FakeDevice(device)
        self.layout = 'strided'
    def numel(self):
        return len(self.data)
    def element_size(self):
        return 4
    def to(self, device, non_blocking=False):
        return FakeTensor(self.data[:], device)


class FakeStream:
    def wait_stream(self, other):
        pass


class FakeEvent:
    synchronized = False
    def record(self, stream):
        self.stream = stream
    def synchronize(self):
        self.synchronized = True


class FakeStreamContext:
    def __enter__(self):
        return self
    def __exit__(self, *args):
        return False


class FakeCuda:
    def __init__(self):
        self.events = []
    def is_available(self):
        return True
    def mem_get_info(self, device):
        return (12 * 1024**3, 24 * 1024**3)
    def Stream(self, device=None):
        return FakeStream()
    def stream(self, stream):
        return FakeStreamContext()
    def current_stream(self, device):
        return FakeStream()
    def Event(self):
        event = FakeEvent()
        self.events.append(event)
        return event


class GpuContractTests(unittest.TestCase):
    def fake_torch(self):
        fake = SimpleNamespace()
        fake.Tensor = FakeTensor
        fake.strided = 'strided'
        fake.cuda = FakeCuda()
        return fake

    def test_cuda_completion_before_ack_and_copy(self):
        fake = self.fake_torch()
        outputs = []
        engine = BoxEngine(queue_items=1, memory_budget_bytes=128)
        stats = engine.transfer_gpu(
            [FakeTensor([1, 2, 3])], 'cuda:0',
            lambda out: outputs.append(out),
            device='cuda:0', torch_module=fake, reserve_bytes=0,
            max_copy_bytes=128)
        self.assertEqual(stats.consumed, 1)
        self.assertEqual(outputs[0].tensor.data, [1, 2, 3])
        self.assertTrue(outputs[0].synchronized)
        self.assertTrue(all(event.synchronized for event in fake.cuda.events))
        self.assertEqual(stats.peak_reserved_bytes, 12)

    def test_oversized_gpu_copy_rejected(self):
        fake = self.fake_torch()
        adapter = TorchCudaAdapter(torch_module=fake, max_copy_bytes=4)
        with self.assertRaisesRegex(ValueError, 'maximum allowed'):
            adapter.copy_tensor(FakeTensor([1, 2]), 'cuda:0')

    def test_gpu_adapter_unavailable_without_cuda(self):
        fake = self.fake_torch()
        fake.cuda.is_available = lambda: False
        with self.assertRaisesRegex(RuntimeError, 'CUDA is unavailable'):
            TorchCudaAdapter(torch_module=fake)


if __name__ == '__main__':
    unittest.main()
