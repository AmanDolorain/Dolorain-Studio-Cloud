# Dual-view workflow editor specification

## Core requirement
Dolorain Studio has **two synchronized views of one workflow**, not two independently maintained graphs:
- **Studio View:** approachable input/model/generation/output controls.
- **Node Graph View:** full, editable nodes, sockets and connections, including advanced nodes. No opaque group hiding the real execution graph.

## Data model
Persist a canonical, versioned graph with stable node IDs, typed ports, directed links, model settings and UI metadata. Both views edit the same state through validated graph operations. Never silently discard unsupported nodes or unknown widget values. Serialize and import ComfyUI workflow JSON with explicit losslessness checks; distinguish UI workflow format from API prompt format.

## Graph ergonomics
- Automatic layout by stage with adjustable grid and zoom-to-fit
- Rounded, collapsible stage backgrounds; default stage order: Inputs -> Models -> Generation -> Output
- Group resizing and node alignment automatically recomputed when content changes
- Strong contrast and readable edge routing; connection tracing/highlight
- Search node, find upstream/downstream dependencies, jump to error
- Manual override for positioning and wiring; auto-layout is optional and reversible
- Undo/redo and validation before execution
- Status per node: pending, executing, succeeded, failed; expose error stack and run logs
- Large workflow performance: viewport virtualization, not hiding or deleting nodes

## Execution
A backend adapter converts the canonical graph into the compatible execution format. Initially use headless ComfyUI to preserve ComfyUI node compatibility. A truly ComfyUI-free backend requires separately implementing and testing the node execution protocol and model loaders.

## Safeguards
Do not run graphs with invalid required inputs or incompatible ports. Changing a connection updates the shared graph and invalidates stale results. Imported graphs must preserve unknown/custom node information or show an explicit incompatibility report.

## Status
Product specification only. The editor, graph synchronization, importer, backend adapter and actual UI are **not implemented yet**.
