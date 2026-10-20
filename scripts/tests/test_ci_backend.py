"""Regression tests for CI target safety and disappearing/skipped DB tests."""

import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts.ci_backend import REQUIRED_DATABASE_TESTS, check_environment, verify_report


class BackendGateTests(unittest.TestCase):
    def environment(self):
        return {"DATABASE_URL": "postgresql+psycopg://phishlens:ci-only-password@localhost:5432/phishlens_dev",
                "RUN_DATABASE_TESTS": "1", "AI_MODE": "mock"}

    def test_explicit_disposable_target(self):
        check_environment(self.environment())

    def test_rejects_unsafe_or_implicit_configuration(self):
        for key, value in [
            ("DATABASE_URL", ""),
            ("DATABASE_URL", self.environment()["DATABASE_URL"].replace("localhost", "db.neon.tech")),
            ("DATABASE_URL", self.environment()["DATABASE_URL"] + "?host=db.neon.tech"),
            ("DATABASE_URL", self.environment()["DATABASE_URL"].replace("phishlens_dev", "production")),
            ("DATABASE_URL", "postgresql://user:private@localhost:5432/phishlens_dev"),
            ("DATABASE_URL", "postgresql+psycopg://[broken"),
            ("RUN_DATABASE_TESTS", "0"), ("AI_MODE", "gemini"), ("AI_MODE", "local"),
        ]:
            with self.subTest(key=key, value=value):
                env = self.environment() | {key: value}
                with self.assertRaises(ValueError):
                    check_environment(env)

    def report(self, directory, cases):
        path = Path(directory) / "pytest.xml"
        path.write_text("<testsuites><testsuite>" + cases + "</testsuite></testsuites>", encoding="utf-8")
        return path

    def cases(self, status=""):
        return "".join(f'<testcase classname="{module}" name="{name}">{status}</testcase>'
                       for module, name in sorted(REQUIRED_DATABASE_TESTS))

    def test_required_database_tests_pass(self):
        with tempfile.TemporaryDirectory() as directory:
            result = verify_report(self.report(directory, self.cases()))
        self.assertEqual(result["required_database_tests_passed"], 2)
        self.assertIn("not established", result["crud_acceptance"])

    def test_missing_skipped_failed_or_client_only_tests_fail(self):
        for cases in ["", '<testcase classname="client" name="crud"/>',
                      self.cases('<skipped message="opt-in missing"/>'),
                      self.cases('<failure message="assertion"/>'), self.cases('<error/>')]:
            with (self.subTest(cases=cases), tempfile.TemporaryDirectory() as directory,
                  self.assertRaises(ValueError)):
                verify_report(self.report(directory, cases))

    def test_main_rejects_cloud_before_running_pytest(self):
        from scripts.ci_backend import main
        with patch.dict("os.environ", {}, clear=True), patch("sys.argv", ["ci_backend.py"]), \
                patch("scripts.ci_backend.subprocess.run") as run:
            self.assertEqual(main(), 1)
        run.assert_not_called()


if __name__ == "__main__":
    unittest.main()
