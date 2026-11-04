"""Isolated Box Engine transport and Studio adapter tests; no GPU needed."""
import json
import sys
import time
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'pipeline'))
sys.path.insert(0, str(HERE / 'backend'))
from bounded_flow import BoundedFlow
from box_engine import BoxEngine, Packet
import box_adapter


class BoxEngineTests(unittest.TestCase):
    def test_h3_workflow_is_only_seen_by_adapter(self):
        workflow = json.loads((HERE / 'H3_Workflow_Fast_FaceDetail5.json').read_text(encoding='utf-8'))
        result = box_adapter.inspect_workflow(workflow)
        self.assertEqual(result['node_count'], 22)
        self.assertEqual(result['link_count'], 29)
        self.assertEqual(result['checked_routes'], 29)
        self.assertTrue(result['valid_structure'])
        self.assertEqual(result['mode'], 'metadata_only')
        self.assertFalse(BoxEngine().status()['model_aware'])  # no model identity used by engine

    def test_broken_link_is_adapter_responsibility(self):
        graph = {'nodes': [{'id': 1}], 'links': [[5, 1, 0, 999, 0, 'whatever']]}
        original = json.dumps(graph)
        result = box_adapter.inspect_workflow(graph)
        self.assertEqual(result['warning_count'], 1)
        self.assertFalse(result['valid_structure'])
        self.assertEqual(json.dumps(graph), original)

    def test_box_accepts_arbitrary_binary_without_inspection(self):
        packets = [Packet(bytes([i])*4, 4, route='dest') for i in range(12)]
        delivered = []
        stats = BoxEngine(queue_items=2, memory_budget_bytes=8).transfer(
            packets, lambda packet: (time.sleep(0.001), delivered.append(packet.payload)))
        self.assertEqual(delivered, [p.payload for p in packets])
        self.assertEqual(stats.produced, 12)
        self.assertEqual(stats.consumed, 12)
        self.assertLessEqual(stats.peak_reserved_bytes, 8)
        self.assertLessEqual(stats.peak_reserved_items, 2)
        self.assertGreater(stats.backpressure_waits, 0)

    def test_oversized_packet_is_rejected(self):
        with self.assertRaisesRegex(RuntimeError, 'Flow producer failed'):
            BoxEngine(memory_budget_bytes=4).transfer([Packet(b'x'*5, 5)], lambda packet: None)

    def test_consumer_failure_stops_and_propagates(self):
        with self.assertRaisesRegex(RuntimeError, 'Flow consumer failed'):
            BoxEngine(queue_items=1, memory_budget_bytes=8).transfer(
                (Packet(b'x', 1) for _ in range(100)), lambda p: 1/0)

    def test_status_has_no_ai_dependency(self):
        result = BoxEngine().status()
        self.assertFalse(result['model_aware'])
        self.assertFalse(result['workflow_aware'])
        self.assertEqual(result['execution_hook'], 'adapter_required')
        self.assertEqual(result['mode'], 'independent_transport')

    def test_gpu_plan_is_outside_engine(self):
        with patch.object(box_adapter, 'probe', return_value={
            'name': 'test GPU', 'total_gb': 24, 'free_gb': 20}):
            status = box_adapter.status()
        self.assertEqual(status['gpu_plan']['status'], 'ready')
        self.assertEqual(status['gpu_plan_mode'], 'observe_only')

    def test_packet_types_not_assumed(self):
        packets = [Packet({'data': 'anything'}, 1), Packet([4, 5], 2)]
        recorded = []
        BoxEngine(queue_items=1, memory_budget_bytes=3).transfer(packets, recorded.append)
        self.assertEqual(recorded, packets)

    def test_bounded_flow_legacy_api_compatible(self):
        target = []
        stats = BoundedFlow(max_items=2).run(range(4), target.append)
        self.assertEqual(target, [0, 1, 2, 3])
        self.assertEqual(stats.consumed, 4)

if __name__ == '__main__':
    unittest.main()
