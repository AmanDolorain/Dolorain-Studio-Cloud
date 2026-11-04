# Dolorain Studio — ComfyUI Native Architecture Research and Migration Contract
Date: 2026-11-04
Status: RESEARCH / DESIGN ONLY; NOT IMPLEMENTED OR HARDWARE-VALIDATED.
Branch: fix/native-node-behavior-20261104. Do not merge until real acceptance tests pass.

## Verified upstream resources
- ComfyUI Core (GPL-3.0): https://github.com/Comfy-Org/ComfyUI
- ComfyUI Frontend (GPL-3.0, Vue/TypeScript and LiteGraph integration): https://github.com/Comfy-Org/ComfyUI_frontend
- Interface guide: https://docs.comfy.org/interface/overview
- Backend routes: https://docs.comfy.org/development/comfyui-server/comms_routes
- Websocket messages: https://docs.comfy.org/development/comfyui-server/comms_messages
- JS extension registration: https://docs.comfy.org/custom-nodes/js/javascript_overview
- Official sidebar tabs: https://docs.comfy.org/custom-nodes/js/javascript_sidebar_tabs
- Official bottom panel: https://docs.comfy.org/custom-nodes/js/javascript_bottom_panel_tabs
- Official topbar menus: https://docs.comfy.org/custom-nodes/js/javascript_topbar_menu
- Template browser: https://docs.comfy.org/interface/features/template
- Nodes 2.0 compatibility notes: https://docs.comfy.org/interface/nodes-2
- Manager: https://github.com/Comfy-Org/ComfyUI-Manager

## Upstream facilities to REUSE, not rebuild
1. One native frontend app, one graph and tab/workspace state.
2. Built-in native Canvas/LiteGraph or supported Nodes 2.0 rendering; graph serializer, move/resize/drag/select, group/subgraph, link typing and layout.
3. Native node definitions via /object_info; actual custom widgets and web extensions provided by the installed node's package.
4. Missing-node handling via native frontend, preserving serialized node IDs, titles, sizes, sockets, links and optional properties. Do not claim unavailable custom widgets work.
5. Validation errors from POST /prompt (error and node_errors); execution errors/progress from /ws; native queue/history/interrupt/logs UI.
6. Native left sidebar: Assets, Nodes, Models, Workflows, Templates; native Queue and console/logs.
7. Manager using the upstream supported integration (core --enable-manager with manager_requirements as appropriate to the pinned core); install/upgrade/disable/install missing nodes are explicit user actions, never automatic on opening JSON.
8. Workflow templates native browser and model-missing prompts, not a separately invented picker.
9. Settings, shortcuts, theme, search preview, plugin hooks, context menu and window management.
10. Official extension APIs: app.registerExtension; registerSidebarTab, bottomPanelTabs, menuCommands, command IDs. Add Dolorain-specific features there, don't replace ComfyUI's app.

## Evidence from THIS repository (reviewed 2026-11-04)
- studio/index.html contains a hand-written .world / .node / .nodeFields HTML+SVG graph renderer, custom fields and footer.
- studio/backend/server.py serves that HTML as the legacy dashboard; independent validation / status / workspace APIs.
- deploy/runpod/cloud/studio.html renders ANOTHER independent header, then waits for /_studio/ready and embeds native frontend through an iframe. It hides Dashboard under three dots.
- deploy/runpod/cloud/app.py runs the GPU preflight and ComfyUI separately; telemetry reads nvidia-smi and /proc/meminfo; legacy Box dashboard is proxied under /_studio/dashboard.
- Existing test_workflow_drop.py checks HTML strings, not actual real-browser behavior.
- In user's RTX3090 RunPod screenshot: CUDA13.2 preflight passed with driver 595.91.07; /system_stats unresponsive, editor header blank, legacy renderer displayed 'Setting 1' fields; separate GPU statuses diverged. ComfyUI startup root cause has not been established.
- /proc/meminfo may expose host RAM instead of Pod/cgroup limit; do not label it pod RAM without checking cgroup.

## Target architecture
One browser application and one stable Dolorain header:
  [ D | Dolorain Studio | GPU VRAM RAM Load Temp | elapsed | Studio/Workflow | generate | diagnostics | theme ]
  [ ONE workspace, switching between Dashboard and NATIVE ComfyUI Editor ]
The native ComfyUI frontend owns canvas, workflow tabs, node widgets, missing-node UX, manager, search, validation, queue, history, shortcuts, and console. The Dolorain header is a thin supported extension/shell with no second independent graph or duplicate state. Dashboard contains monitoring, model & cloud controls and diagnostics only, never an editable shadow graph.

Build a supported frontend integration, NOT overlay CSS selectors for undocumented .lg-node shape, NOT a separate DOM/SVG node renderer, NOT a second isolated ComfyUI app/frame with conflicting auth/websocket. Preserve native ComfyUI controls, show/hide only the main content views. Respect both classic LiteGraph and Vue Nodes 2.0 without coupling to private DOM.

## Manager / models
- Do not auto-install arbitrary custom nodes or download models upon importing JSON. Provide official missing-node discovery and user-confirmed install.
- Ship base ComfyUI and optional manager in a pinned, license-compliant version after compatibility review; distinguish Manager from individual H3 / Pixaroma custom nodes.
- Installed-node presentation MUST preserve all original JS widgets (video/audio selection, player, prompt resizing, input conversion).
- Absent custom node: retain graph metadata and explicit missing/error state; execute is blocked with native actionable validation.

## GPU / engine
- Independent states: GPU detected, CUDA preflight, ComfyUI process alive, /system_stats ready, execution queue; don't conflate Box transport health with inference availability.
- Record complete ComfyUI process errors and return code. Preflight PASS does NOT mean backend READY.
- Verify actual ComfyUI CLI args against pinned commit using its --help; do not assume --models-directory is supported.
- RAM utilization uses correct cgroup memory.* or explicit host RAM label.
- Avoid exposing unauthenticated Jupyter and manager endpoints on public proxies except a deliberately temporary controlled test.

## Engineering and release gates — ALL required
A. Static unit and integration tests for the verified pinned ComfyUI CLI, license notices, status API, websocket proxy, model paths, extension boot, failed preflight/failed ComfyUI error report.
B. End-to-end browser acceptance on exact release image: same header Dashboard↔Editor; toolbar no duplicate header; GPU and engine consistent; persistence; native template/node/model/queue/logs panels.
C. Import H3 and SparkVSR JSON via Edge drag/drop: new native tab, no page navigation, positions/links unchanged; missing nodes explicitly marked and reported, not generic working widgets.
D. Install exact matching custom-node versions and check real Video upload/player, Audio upload/player, prompts, dropdowns, settings, combo widgets, resizing, serializing, linking, input conversion, search hover preview, groups, multi-tabs.
E. Trigger controlled validation error and execution exception; confirm native per-node error and diagnostics, queue/history, cancel/interrupt.
F. Run one small paid generation on compatible GPU only after UI tests and user budget authorization.
G. No main merge and no candidate tag overwrite until A-F pass. Build/push to separate isolated test tag. Recheck GPL-3.0 obligations and license notices for distribution.

## Implementation sequence (one coherent migration, not a series of visual patches)
1. Freeze and document current UI behavior; retain old code for rollback but remove legacy graph editor from user-facing Cloud workspace.
2. Establish pinned core+frontend+Manager compatibility; verify actual CLI flags and startup log/error capture, websocket and native routes first.
3. Integrate Dolorain thin native frontend extension (header, view switch, safe telemetry, dashboard panel), keeping ComfyUI's original DOM, canvas, tabs and sidebar.
4. Integrate existing Box dashboard as a non-graph workspace; do not let it be a second source of queue/node/gpu truth.
5. Add full native E2E browser suite plus smoke checks; user reviews UI in GPU test; only then merge.

**This document records research/architecture only. No claim of completed implementation or tested build.**
