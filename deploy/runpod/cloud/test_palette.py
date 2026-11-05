"""Regression for the GPU-preflight-pass / ComfyUI-never-started theme error."""
import json
import tempfile
import unittest
from pathlib import Path

from palette import install


class DolorainPaletteTests(unittest.TestCase):
    def test_installs_both_palettes_and_native_preferences(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            install(root)
            path = root / "default" / "comfy.settings.json"
            settings = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(settings["Comfy.ColorPalette"], "dolorain-light")
            self.assertFalse(settings["Comfy.Minimap.Visible"])
            self.assertTrue(settings["Comfy.NodeSearchBoxImpl.NodePreview"])
            palettes = settings["Comfy.CustomColorPalettes"]
            for mode in ("light", "dark"):
                palette = palettes["dolorain-" + mode]
                self.assertEqual(palette["colors"]["theme"]["ring"], "#18a957")

    def test_existing_dark_mode_stays_dark_and_old_accent_is_refreshed(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            path = root / "default" / "comfy.settings.json"
            path.parent.mkdir(parents=True)
            path.write_text(json.dumps({"Comfy.ColorPalette": "dolorain-dark",
                "Comfy.CustomColorPalettes": {"dolorain-dark": {"colors": {"theme": {"ring": "#ffffff"}}}}}))
            install(root)
            settings = json.loads(path.read_text(encoding="utf-8"))
            self.assertEqual(settings["Comfy.ColorPalette"], "dolorain-dark")
            self.assertEqual(settings["Comfy.CustomColorPalettes"]["dolorain-dark"]["colors"]["theme"]["ring"], "#18a957")


if __name__ == "__main__":
    unittest.main()
