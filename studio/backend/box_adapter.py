"""Studio-only adapter; Box Engine itself never receives workflow JSON.

This adapter translates node/connection records into opaque routing metadata,
and is the ONLY layer allowed to understand workflow identifiers.
"""
from __future__ import annotations

from collections import Counter

from box_engine import BoxEngine
from gpu_policy import probe, plan

MAX_NODES, MAX_LINKS = 20000, 50000


def status() -> dict:
    engine = BoxEngine()
    gpu = probe()
    return {**engine.status(), 'gpu': gpu, 'gpu_plan': plan(gpu),
            'gpu_plan_mode': 'observe_only',
            'stages': [
                {'id': 'adapter', 'label': 'Studio adapter', 'state': 'available'},
                {'id': 'transport', 'label': 'Bounded transport', 'state': 'available'},
                {'id': 'gpu', 'label': 'GPU integration', 'state': 'not_connected'},
            ]}


def inspect_workflow(workflow: dict) -> dict:
    if not isinstance(workflow, dict):
        raise ValueError('Expected a Studio workflow object')
    nodes, links = workflow.get('nodes'), workflow.get('links')
    if not isinstance(nodes, list) or not isinstance(links, list):
        raise ValueError('Expected nodes and links lists')
    if len(nodes) > MAX_NODES or len(links) > MAX_LINKS:
        raise ValueError('Workflow too large for Studio adapter')
    node_ids, warnings = set(), []
    for node in nodes:
        if not isinstance(node, dict) or type(node.get('id')) not in (str, int):
            warnings.append('Invalid node ID')
            continue
        nid = node['id']
        if nid in node_ids:
            warnings.append('Duplicate node ID: ' + str(nid))
        node_ids.add(nid)

    seen, connected, type_counts, routes = set(), set(), Counter(), []
    for link in links:
        if not isinstance(link, list) or len(link) < 6:
            warnings.append('Malformed connection record')
            continue
        ident, start, output_slot, end, input_slot, port_kind = link[:6]
        if type(ident) not in (int, str) or type(start) not in (int, str) or type(end) not in (int, str):
            warnings.append('Connection has invalid identifiers')
            continue
        if ident in seen:
            warnings.append('Duplicate connection ID: ' + str(ident))
        seen.add(ident)
        if start not in node_ids or end not in node_ids:
            warnings.append('Connection ' + str(ident) + ' references a missing node')
        else:
            connected.update((start, end))
        if any(type(slot) is not int or slot < 0 for slot in (output_slot, input_slot)):
            warnings.append('Connection ' + str(ident) + ' has invalid slot indexes')
        type_counts[str(port_kind)] += 1
        # Opaque route descriptor; NO node types, port names or model metadata.
        routes.append({'route': str(ident)})

    check = BoxEngine().inspect_routes(routes)
    return {**check, 'node_count': len(nodes), 'link_count': len(links),
            'connected_nodes': len(connected),
            'isolated_nodes': max(0, len(node_ids) - len(connected)),
            'checked_connections': check['checked_routes'],
            'connection_types': dict(type_counts.most_common(12)),
            'warnings': warnings[:25], 'warning_count': len(warnings),
            'valid_structure': not warnings,
            'note': 'Studio adapter checked connections. Box Engine handled opaque metadata only; GPU execution was not changed.'}
