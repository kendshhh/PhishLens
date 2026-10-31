"""Keep hosted preview archives bound to their configured staging origin."""

import base64
import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import Mock
from zipfile import ZipFile

from scripts.secretary.preview import package

CONFIG = {
    "staging_origin": "https://phishlens-staging.onrender.com",
    "production_origin": "https://phishlens-api-ocvt.onrender.com",
}
SHA = "a" * 40


class PreviewPackageOriginTests(unittest.TestCase):
    def build_archive(self, worker):
        api = Mock()
        files = {
            "manifest.json": json.dumps({
                "manifest_version": 3,
                "background": {"service_worker": "background.js", "type": "module"},
            }).encode(),
            "popup.html": b"<html><body><main></main></body></html>",
            "background.js": worker.encode(),
            "js/popup.js": b"import { API_BASE_URL } from './config.js';\n",
        }

        def read(path):
            relative = path.split("contents/extension/", 1)[1].split("?", 1)[0]
            data = files.get(relative, f"fixture:{relative}".encode())
            return {
                "encoding": "base64",
                "size": len(data),
                "content": base64.b64encode(data).decode(),
            }

        api.request.side_effect = read
        directory = tempfile.TemporaryDirectory()
        self.addCleanup(directory.cleanup)
        output = Path(directory.name) / "staging.zip"
        package(api, SHA, 99, CONFIG, output)
        return output

    def assert_staging_archive(self, output, expected_worker):
        with ZipFile(output) as archive:
            self.assertIsNone(archive.testzip())
            worker = archive.read("background.js")
            popup = archive.read("js/popup.js")
            self.assertIn(expected_worker, worker.decode())
            for data in (worker, popup):
                self.assertNotIn(b"127.0.0.1", data)
                self.assertNotIn(b"localhost", data)
                self.assertNotIn(CONFIG["production_origin"].encode(), data)
            self.assertEqual(
                archive.read("js/config.js"),
                ("export const API_BASE_URL = " + json.dumps(CONFIG["staging_origin"]) + ";\n").encode(),
            )
            self.assertEqual(
                json.loads(archive.read("manifest.json"))["host_permissions"],
                [CONFIG["staging_origin"] + "/*"],
            )

    def test_api_worker_uses_shared_config_and_staging_archive(self):
        output = self.build_archive(
            'import { API_BASE_URL } from "./js/config.js";\n'
            'fetch(`${API_BASE_URL}/analyses`);\n'
        )
        self.assert_staging_archive(output, "API_BASE_URL")

    def test_local_scanner_archive_includes_models_and_staging_report_config(self):
        output = self.build_archive(
            "import { analyzeWithReview } from './ai/live-workflow.mjs';\n"
        )
        self.assert_staging_archive(output, "live-workflow.mjs")
        with ZipFile(output) as archive:
            names = set(archive.namelist())
            for asset in (
                "ai/live-workflow.mjs",
                "ai/local-analyzer.mjs",
                "ai/tfidf_v12a.json",
                "vendor/ml/ort-wasm-simd-threaded.jsep.wasm",
            ):
                self.assertIn(asset, names)


if __name__ == "__main__":
    unittest.main()

