"""Hosted acceptance must identify the requested staging commit and data."""
import copy
import io
import json
import unittest
from unittest.mock import patch

from scripts.secretary.preview import smoke

SHA = "a" * 40


class HostedIdentityTests(unittest.TestCase):
    def responses(self):
        return [
            {"status": "ok", "service": "phishlens-api"},
            {"status": "ready", "database": "connected"},
            {"commit": SHA, "environment": "staging"},
            {"items": [{"subject": "Synthetic account notice"}]},
        ]

    def verify(self, payloads):
        responses = [io.BytesIO(json.dumps(value).encode()) for value in payloads]
        with patch("urllib.request.urlopen", side_effect=responses), patch(
            "scripts.secretary.preview.time.monotonic", side_effect=[0, 181]
        ):
            return smoke("https://staging.invalid", SHA)

    def test_exact_staging_commit_and_seed_pass(self):
        evidence = self.verify(self.responses())
        self.assertEqual(evidence["version"], SHA)
        self.assertEqual(evidence["history"], "passed")

    def test_wrong_commit_fails(self):
        values = self.responses()
        values[2]["commit"] = "b" * 40
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_production_environment_fails(self):
        values = self.responses()
        values[2]["environment"] = "production"
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_missing_synthetic_history_fails(self):
        values = self.responses()
        values[3]["items"] = []
        with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
            self.verify(values)

    def test_unhealthy_or_unready_service_fails(self):
        for index in (0, 1):
            with self.subTest(index=index):
                values = copy.deepcopy(self.responses())
                values[index]["status"] = "unavailable"
                with self.assertRaisesRegex(RuntimeError, "Staging smoke failed"):
                    self.verify(values)


if __name__ == "__main__":
    unittest.main()
