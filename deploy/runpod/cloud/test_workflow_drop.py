"""Source regression checks for the Studio native JSON workflow importer.

These are intentionally static checks; an end-to-end drag/drop browser
acceptance test is still required on the candidate RunPod image.
"""
from pathlib import Path
import unittest

STUDIO = Path(__file__).with_name("studio.html").read_text(encoding="utf-8")


class NativeWorkflowDropContract(unittest.TestCase):
    def test_external_json_is_intercepted_before_browser_navigation(self):
        self.assertIn("attachJsonDrop(document)", STUDIO)
        self.assertIn("attachJsonDrop(win.document)", STUDIO)
        self.assertIn("event.preventDefault()", STUDIO)
        self.assertIn("event.stopImmediatePropagation()", STUDIO)


    def test_one_header_with_dashboard_and_native_editor(self):
        self.assertIn('id="dashboardSwitch"', STUDIO)
        self.assertIn('id="editorSwitch"', STUDIO)
        self.assertIn('id="dashboardCanvas"', STUDIO)
        self.assertIn('id="canvas"', STUDIO)
        self.assertIn('function switchView(view)', STUDIO)
        self.assertIn("style.textContent='body>header", STUDIO)
        self.assertNotIn('>Studio dashboard</a>', STUDIO)

    def test_approved_theme_and_native_workflow_camera(self):
        self.assertIn('body.dark', STUDIO)
        self.assertIn('#18a957', STUDIO)
        self.assertIn('ds.scale=0.6', STUDIO)
        self.assertIn('frameWorkflowAtSixtyPercent()', STUDIO)
        self.assertIn("node.color='#991b1b'", STUDIO)

    def test_native_import_keeps_workflow_tabs_and_missing_nodes(self):
        self.assertIn("nativeApp.handleFile(file,'file_drop')", STUDIO)
        self.assertIn("enableMissingNodeAppearance()", STUDIO)
        self.assertIn("n.has_errors&&n.last_serialization", STUDIO)
        self.assertIn('data-dolorain-missing', STUDIO)
        self.assertNotIn("new FileReader(", STUDIO)


if __name__ == "__main__":
    unittest.main()
