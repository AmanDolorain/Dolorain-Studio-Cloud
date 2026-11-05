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

## Approved Dolorain visual and behavior contract (2026-11-04)
This section captures visible screenshots, current/project context and earlier design decisions available in the conversation. It does not claim exhaustive access to all earlier chat transcripts.
### Canvas layout and camera
- Keep the accepted white Dolorain node skin: readable compact nodes, light grey headers, ports, wiring, subtle dotted background and dashed workflow/group boundaries. Do not substitute the stock ComfyUI aesthetic.
- At first opening/import, frame the leftmost workflow content at the left and follow its layout toward the right, rather than auto-centering the graph arbitrarily.
- Default initial zoom exactly 60%, with visible plus/minus and percentage readout. Save and restore per-workflow viewport when available; never recenter while the user is editing.
- Keep a visible workflow-bounded rectangular space based on native graph node/group positions; allow boundary resizing/expansion up/down/left/right while allowing normal native zoom/pan without clipping or modifying connections.
- Preserve native node and group size/position and metadata; boundary is a presentation overlay, not a second graph or executable graph replacement.
### Unified user interface
- One permanent Dolorain header for BOTH dashboard and editor; switch only lower workspace. Keep D logo, GPU/VRAM/RAM/Load/Temp, elapsed time, original studio/editor icons, diagnostics and theme; do not hide dashboard in three dots.
- Separate detected GPU, CUDA preflight, ComfyUI backend, Box engine transport, generation status. Use container-cgroup RAM or explicitly identify host RAM.
- Keep native ComfyUI sidebar (templates/models/nodes/workflows), native workflow tabs, queue/history/settings/shortcuts, validation errors and console/logs reachable and visibly distinguishable.
### Node style vs native behavior
- Change appearance only: every installed node retains original developer-defined widgets, prompt input, audio/video player and uploader, image previews, sockets, dropdowns, conversion, resizing, connections, name edits and serialization.
- Missing custom nodes must preserve original JSON identities, links, dimensions/ports and be visibly RED with an actionable native missing/error indication. Do not render fictional functional fields named Setting 1, Setting 2, etc.
- Maintain a distinct node manager including search, original previews, explicit install/update/disable and missing-node resolution; never auto-install packages.
- For classic canvas-rendered nodes, pure CSS cannot recolor the drawings. Evaluate native palettes, LiteGraph style constants and supported extension hooks against the PINNED frontend version. Do not replace canvas rendering with homemade HTML nodes.
### Required E2E acceptance
- H3 and SparkVSR JSON import into native tabs, zoom begins at 60%, first node visible left, bounded workflow frame extends right and can be resized without modifying graph.
- Verify unified header and GPU readings on dashboard and editor, no menu-hidden dashboard, no empty canvas if engine healthy; diagnose startup failures separately.
- Missing packages: red nodes + errors + preserved links; with installed packages: real video/audio/prompt widgets and previews, correct settings and behavior.
- Check native error panel, execution failure, manager missing-node flow, sidebar templates, queue, history, console, custom-node search preview, saving and reload.
- Do not merge failed test build; require browser and RTX 3090 checks before release.

## Final native-canvas feature decisions — user acceptance 2026-11-04
These decisions override conflicting earlier proposals in this research document. They are REQUIREMENTS, not implemented features.

### KEEP: ComfyUI behavior
- Native node graph movement/drag, sizing/resizing, grouping, typed connections, zoom, pan, multi-selection, copy/paste and undo/redo.
- Native input/output sockets, dropdowns, editable widgets, text inputs, image/video/audio elements and developer-provided custom-node extensions. Never substitute fictional `Setting 1` fields.
- Native Node Library with built-in and installed custom nodes, node search, add-node actions and working hover previews.
- Native Model Library, workflow JSON drag/drop/import/save/open/tabs, queue/run/interrupt, progress indication, execution history and per-node highlighting/animating active execution and completed/error states.
- Native error dialogs, missing-node identification, validation errors, detailed execution logs and diagnostics.
- Real ComfyUI Manager workflows for explicit install/update/disable/find-missing; installed node pack detection must be distinct from available nodes.
- Native extension integration opportunities: sidebar, bottom panel, topbar, commands, contextual node actions and shortcuts.

### REMOVE / DO NOT SHOW
- The bottom-right or bottom canvas minimap / graph overview map. Do not install/show it, and do not replace it with a different minimap.
- A second HTML/SVG shadow node canvas; a second header; generic generated replacement widgets; dashboard hidden under 3 dots.

### KEEP: Dolorain visual language
- User-approved compact WHITE/GRAY Dolorain node shapes, visual proportions, title bands, text sizes, socket colors, workflow-background dots, groups, style, theme and positioning.
- One permanent Dolorain header with D logo, correct GPU name, VRAM, RAM, GPU utilization, temperature, elapsed generation timer, dashboard/editor switches and diagnostics.
- 60% initial display zoom. Workflow starts near left edge and extends to the right. Visible bounded/resizable workflow space; allow free native zoom and pan without losing graph content.
- Native execution highlighting must be visible within Dolorain skin: node active/running transitions, completed state, errors in red, connection/progress feedback. The styling can change but source of state and sequencing must be real ComfyUI events.
- For a missing custom node, preserve as much type/title/size/ports/connections and JSON-saved visual metadata as genuinely available; RED/error indicator plus actionable missing node list. Original third-party custom widget functionality cannot exist until its plugin is installed; never promise pixel-perfect preview if its implementation is absent.

### Release gates
- Demonstrate live native node-progress highlighting over consecutive execution steps.
- Demonstrate missing nodes in RED and native errors, and no fabricated settings.
- Demonstrate zoom at 60%, left-to-right initial placement and boundary resizing, and absence of minimap.
- Demonstrate same header in Dashboard and Editor, same telemetry values, native manager/library/templates/logs/queue.
- The last docker test build failed; it was removed by the user. Do NOT merge PR or publish as release until compatibility, startup, browser and GPU generation testing succeeds.
