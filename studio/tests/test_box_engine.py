"""Box Engine diagnostics are read-only and never download or run GPU workloads."""
import json
import sys
import unittest
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(HERE.parent / 'pipeline'))
import box_engine


class BoxEngineTests(unittest.TestCase):
    def test_bounded_analysis_of_saved_h3_workflow(self):
        workflow = json.loads((HERE / 'H3_Workflow_Fast_FaceDetail5.json').read_text(encoding='utf-8'))
        result = box_engine.inspect_workflow(workflow)
        self.assertEqual(result['node_count'], len(workflow['nodes']))
        self.assertEqual(result['checked_connections'], len(workflow['links']))
        self.assertEqual(result['warning_count'], 0)
        self.assertTrue(result['valid_structure'])
        self.assertEqual(result['mode'], 'observe_only')

    def test_dangling_connections_are_reported_not_modified(self):
        graph = {'nodes': [{'id': 1}], 'links': [[10, 1, 0, 99, 0, 'IMAGE']]}
        before = json.dumps(graph)
        result = box_engine.inspect_workflow(graph)
        self.assertFalse(result['valid_structure'])
        self.assertEqual(result['warning_count'], 1)
        self.assertEqual(json.dumps(graph), before)

    def test_invalid_capacity_rejected(self):
        with self.assertRaises(ValueError):
            box_engine.inspect_workflow({'nodes': [], 'links': []}, 0)

    def test_gpu_policy_is_observed_not_applied(self):
        with patch.object(box_engine, 'probe', return_value={
            'name': 'Test GPU', 'total_gb': 24.0, 'free_gb': 20.0
        }):
            result = box_engine.status()
        self.assertEqual(result['mode'], 'observe_only')
        self.assertEqual(result['gpu_plan']['status'], 'ready')
        self.assertEqual(result['gpu_plan']['flags'][-1], '--lowvram')
        self.assertEqual(result['stages'][2]['state'], 'planning_only')

    def test_hf_model_not_downloaded_automatically(self):
        with patch.object(box_engine, 'probe', return_value=None), patch.dict('os.environ', {}, clear=True):
            result = box_engine.status()
        self.assertIsNone(result['hf_model'])
        self.assertEqual(result['hf_model_state'], 'not_configured')


if __name__ == '__main__':
    unittest.main()
