# Native-only cleanup — 2026-11-05

## Protected references
- Source: `fix/native-node-behavior-20261104`
- Immutable-by-policy backup branch: `backup/pre-native-cleanup-20261105`
- Working branch: `cleanup/native-editor-only-20261105`
- Do not modify `main` or delete the backup.

## Keep
- `deploy/runpod/cloud/studio.html` native editor shell and `deploy/runpod/cloud/app.py` proxy/telemetry/diagnostics.
- `START-DOLORAIN-LOCAL.bat` and `scripts/Start-Dolorain-Local.ps1`, adjusted to discover the existing local ComfyUI venv instead of removed Easy Install.
- `pipeline/` Box Engine and GPU policy, `studio/backend/box_adapter.py`, H3 workflow JSON, branding, cloud scripts, security, tests and diagnostics.

## Legacy to remove AFTER dependencies are migrated
- `studio/index.html` handmade HTML/SVG graph, `studio/canvas_size.js`, `studio/node_fields.js`, `studio/manager_catalog.js`.
- `studio/backend/server.py` and its workflow bridge endpoints after extracting any still-used helpers (notably `jupyter_proxy_url`) and replacing the legacy `/_studio/dashboard/` routing in cloud app.
- `studio/start-local.bat`, `studio/backend/start_studio.py`, and `deploy/windows/Open-Dolorain-Studio.cmd` if confirmed not needed by any remaining launcher.
- Legacy-only tests and docs after equivalent native acceptance tests exist.

## Blocking issue
The Windows native preview currently displays 'ComfyUI starting... Checking native engine' despite backend port 8188 responding. Diagnose native frontend proxy, iframe and ready behavior before deleting the legacy fallback. Preserve Logs and Box diagnostics; do not claim the native UI is verified.

## Acceptance
Native editor must load on Windows with existing CPU ComfyUI and no downloads; cloud compatibility must remain intact. Confirm workflow JSON import, genuine node widgets, missing nodes, manager, logs, dashboard and Box diagnostics. Only then delete legacy code, run tests and request review for merge.
