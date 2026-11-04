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

    def test_native_import_keeps_workflow_tabs_and_missing_nodes(self):
        self.assertIn("nativeApp.handleFile(file,'file_drop')", STUDIO)
        self.assertIn("enableMissingNodeAppearance()", STUDIO)
        self.assertIn("n.has_errors&&n.last_serialization", STUDIO)
        self.assertIn('data-dolorain-missing', STUDIO)
        self.assertNotIn("new FileReader(", STUDIO)


if __name__ == "__main__":
    unittest.main()
