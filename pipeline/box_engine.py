"""Dolorain Studio Box Engine: read-only workflow connection diagnostics.

Uses the existing bounded CPU pipeline and GPU launch policy, but never runs,
modifies, schedules, or chunks GPU workloads. No dependencies or downloads.
"""
from __future__ import annotations

import os
from collections import Counter

from bounded_flow import BoundedFlow
from gpu_policy import plan, probe

MAX_NODES = 20000
MAX_LINKS = 50000


def status() -> dict:
    gpu = probe()
    model_id = os.environ.get('DSC_BOX_CONNECTION_MODEL', '').strip() or None
    return {
        'name': 'Dolorain Box Engine',
        'mode': 'observe_only',
        'pipeline': 'bounded_cpu_diagnostics',
        'gpu': gpu,
        'gpu_plan': plan(gpu),
        'hf_model': model_id,
        'hf_model_state': 'configured_not_loaded' if model_id else 'not_configured',
        'stages': [
            {'id': 'input', 'label': 'Workflow inputs', 'state': 'available'},
            {'id': 'queue', 'label': 'Bounded CPU queue', 'state': 'available'},
            {'id': 'gpu', 'label': 'GPU admission', 'state': 'planning_only'},
            {'id': 'output', 'label': 'Results', 'state': 'diagnostics_only'},
        ],
    }


def inspect_workflow(workflow: dict, max_items: int = 2) -> dict:
    if not isinstance(workflow, dict):
        raise ValueError('Expected a workflow object')
    nodes, links = workflow.get('nodes'), workflow.get('links')
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise ValueError('Expected workflow nodes and links lists')
    if len(nodes) > MAX_NODES or len(links) > MAX_LINKS:
        raise ValueError('Workflow too large for Box Engine diagnostics')
    if isinstance(max_items, bool) or not isinstance(max_items, int) or not 1 <= max_items <= 16:
        raise ValueError('Queue capacity must be between 1 and 16')

    ids = set()
    errors = []
    for node in nodes:
        if not isinstance(node, dict) or not isinstance(node.get('id'), (int, str)):
            errors.append('Invalid node record or ID')
            continue
        if node['id'] in ids:
            errors.append('Duplicate node ID: ' + str(node['id']))
        ids.add(node['id'])

    type_counts = Counter()
    connected_nodes = set()
    seen_links = set()

    def handle(link):
        if not isinstance(link, list) or len(link) < 6:
            errors.append('Malformed connection record')
            return
        link_id, src, src_slot, dst, dst_slot, kind = link[:6]
        if link_id in seen_links:
            errors.append('Duplicate connection ID: ' + str(link_id))
        seen_links.add(link_id)
        if src not in ids or dst not in ids:
            errors.append('Connection ' + str(link_id) + ' references a missing node')
        else:
            connected_nodes.add(src)
            connected_nodes.add(dst)
        if not isinstance(src_slot, int) or not isinstance(dst_slot, int) or src_slot < 0 or dst_slot < 0:
            errors.append('Connection ' + str(link_id) + ' has invalid slot indexes')
        type_counts[str(kind)] += 1

    stats = BoundedFlow(max_items=max_items).run(links, handle)
    return {
        'mode': 'observe_only',
        'node_count': len(nodes),
        'link_count': len(links),
        'connected_nodes': len(connected_nodes),
        'isolated_nodes': max(0, len(ids) - len(connected_nodes)),
        'checked_connections': stats.consumed,
        'queue_capacity': max_items,
        'connection_types': dict(type_counts.most_common(12)),
        'warnings': errors[:25],
        'warning_count': len(errors),
        'valid_structure': len(errors) == 0,
        'note': 'Diagnostic only: does not validate model execution or alter GPU scheduling.',
    }
