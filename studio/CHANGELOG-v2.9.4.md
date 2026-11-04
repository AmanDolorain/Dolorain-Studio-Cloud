# Dolorain Studio — v2.9.4 (04 November 2026)

Base: full Windows v2.9, plus v2.9.1, v2.9.2 and v2.9.3 incremental updates.

## Improvements
- Preserved v2.9.3's behavior: widgets for wired **inputs** remain hidden; they return when their incoming wire is disconnected. The source Controller stays editable. Connected inputs use their wire, not obsolete target widget values, at ComfyUI queue time.
- Wire coordinates are drawn **after** the node widgets mount, so wires use the final node geometry.
- Node and Group names may be changed via title click, **F2** after selecting, or **right-click title → Rename**. Saves/exports retain custom titles. No extra permanent toolbar button.
- Freshly added nodes now save named widget values as well as positional values, preventing misalignment between the displayed widget and the value submitted to ComfyUI.
- Checkbox programmatic updates set the checked state instead of assigning only `.value`.
- Bridge: a muted/disconnected source on an *optional* input is omitted rather than rejecting the whole graph; required inputs remain validated.
- Kept the existing single footer, colors, toolbar icons, H3 graph, pan/zoom/Fit, Studio/Subgraph views and file workflows unchanged.

## Install
**Already using v2.9.3:** Close the Studio launcher. Extract `Dolorain-Studio-v2.9.4-Update-from-v2.9.3.zip` over the folder *above* your existing `Dolorain-Studio/` directory, and allow replacement. Re-launch `start-local.bat` and hard refresh Edge with Ctrl+Shift+R. Existing workflow JSON and engine models are not replaced.

**Fresh install:** Use `Dolorain-Studio-v2.9.4-Windows-Full.zip`; extract it, install prerequisites stated in README.md, and run `start-local.bat`. GPU model weights/custom packs are not bundled.

## Validation
- Chromium headless UI checks: 22 original nodes, 29 links, wired field hiding, H3 Controller edit/preset, disconnect/reconnect, F2/context rename, single footer, both views, theme toggle, Fit; no JS page errors.
- Five backend unit tests passed (`python -m pytest -q tests/test_bridge.py`). JS syntax checked with Node.js.
- Not exercised here: Windows launcher/setup and ComfyUI GPU/H3 generation on a connected instance. Live engine validation remains necessary.
