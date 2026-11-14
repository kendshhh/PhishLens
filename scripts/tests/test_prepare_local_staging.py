import importlib.util
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch
from zipfile import ZipFile

SCRIPT = Path(__file__).resolve().parents[1] / "prepare_local_staging.py"
spec = importlib.util.spec_from_file_location("prepare_local_staging", SCRIPT)
preview = importlib.util.module_from_spec(spec)
spec.loader.exec_module(preview)


class LocalStagingTests(unittest.TestCase):
    def test_default_refresh_removes_previously_included_models(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "output/staging-local/extension"

            def package(command, **_kwargs):
                archive = root / "output/extension/PhishLens-Extension.zip"
                archive.parent.mkdir(parents=True, exist_ok=True)
                with ZipFile(archive, "w") as output:
                    output.writestr("manifest.json", json.dumps({"action": {}}))
                    output.writestr("popup.html", '<header class="app-header">Preview</header>')
                    output.writestr("js/popup.js", "// Synthetic controller\n")
                    output.writestr("js/config.js", "// Replaced by preview configuration\n")
                    if "--include-models" in command:
                        output.writestr("models/judge/weights.bin", b"synthetic weights")

            with patch.object(preview, "ROOT", root), patch.object(preview, "TARGET", target), \
                    patch.object(preview.subprocess, "run", side_effect=package):
                with patch("sys.argv", [str(SCRIPT), "--include-models"]):
                    preview.main()
                weights = target / "models/judge/weights.bin"
                self.assertTrue(weights.is_file())
                with patch("sys.argv", [str(SCRIPT)]):
                    preview.main()
                self.assertFalse(weights.exists())
                metadata = json.loads((target / "local-preview.json").read_text(encoding="utf-8"))
                self.assertFalse(metadata["includes_local_judge_weights"])
                self.assertEqual((target / "popup.html").read_text(encoding="utf-8").count("STAGING · LOCAL UI PREVIEW"), 1)
                self.assertEqual(json.loads((target / "manifest.json").read_text(encoding="utf-8"))["host_permissions"],
                                 [preview.ORIGIN + "/*"])
                with patch("sys.argv", [str(SCRIPT), "--include-models"]):
                    preview.main()
                self.assertTrue(weights.is_file())
                self.assertTrue(json.loads((target / "local-preview.json").read_text(encoding="utf-8"))[
                    "includes_local_judge_weights"])

    def test_preview_outside_output_is_rejected_without_removing_files(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            target = root / "unrelated"
            target.mkdir()
            retained = target / "keep.bin"
            retained.write_bytes(b"keep")
            with patch.object(preview, "ROOT", root), patch.object(preview, "TARGET", target), \
                    patch.object(preview.subprocess, "run"), patch("sys.argv", [str(SCRIPT)]), \
                    self.assertRaisesRegex(ValueError, "escapes the output directory"):
                preview.main()
            self.assertEqual(retained.read_bytes(), b"keep")


if __name__ == "__main__":
    unittest.main()
