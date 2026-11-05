"""Studio के दोनों iframe और सक्रिय वर्कफ़्लो के बीच अनुबंध की जाँच।"""
from pathlib import Path
import unittest

STUDIO = Path(__file__).with_name("studio.html").read_text(encoding="utf-8")


class WorkflowViews(unittest.TestCase):
    def test_shell_drop_reaches_the_visible_editor(self):
        self.assertIn("nativeApp.handleFile(file,'file_drop')", STUDIO)
        self.assertIn("editor.importWorkflows(files)", STUDIO)
        self.assertIn("event.preventDefault()", STUDIO)

    def test_preview_waits_for_the_native_frontend(self):
        self.assertIn("nativePreviewFrame.contentWindow.app", STUDIO)
        self.assertIn("tabsRestored", STUDIO)
        self.assertNotIn("win.Function(", STUDIO)

    def test_preview_uses_active_workflow(self):
        self.assertIn("frame.contentWindow.nativeWorkflowSnapshot()", STUDIO)
        self.assertNotIn("fetch('/_studio/workflow'", STUDIO)
        self.assertIn("frame.hidden=false;nativePreviewFrame.hidden=true", STUDIO)

    def test_missing_node_style_is_not_written_to_workflow_colors(self):
        self.assertIn("node.strokeStyles.error", STUDIO)
        self.assertIn(".lg-node[data-dolorain-missing] .lg-node-header", STUDIO)
        self.assertNotIn("node.color=", STUDIO)
