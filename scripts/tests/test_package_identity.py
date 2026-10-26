"""Exercise package provenance against real clean, dirty and exported checkouts."""

import json
import os
import shutil
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

from scripts.verify_extension_package import verify

SOURCE_ROOT = Path(__file__).resolve().parents[2]


class PackageIdentityTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.environment = os.environ.copy()
        for variable in ("SOURCE_COMMIT", "GITHUB_SHA", "GIT_DIR", "GIT_WORK_TREE",
                         "GIT_INDEX_FILE"):
            self.environment.pop(variable, None)
        self.copy_inputs(self.root)
        (self.root / ".gitignore").write_text("output/\nexports/\n", encoding="utf-8")
        (self.root / "no-hooks").mkdir()
        self.git("init")
        self.git("add", "extension", "scripts", ".gitignore")
        self.git("commit", "-m", "Synthetic package fixture")
        self.revision = self.git("rev-parse", "HEAD").strip()

    def copy_inputs(self, destination):
        shutil.copytree(SOURCE_ROOT / "extension", destination / "extension")
        (destination / "scripts").mkdir(parents=True)
        for name in ("package_extension.py", "validate_extension.py"):
            shutil.copyfile(SOURCE_ROOT / "scripts" / name, destination / "scripts" / name)

    def git(self, *arguments):
        result = subprocess.run(
            ["git", "-c", "user.name=Synthetic package fixture",
             "-c", "user.email=package@example.invalid", "-c", "commit.gpgsign=false",
             "-c", f"core.hooksPath={self.root / 'no-hooks'}", *arguments],
            cwd=self.root, env=self.environment, capture_output=True, text=True, check=True,
        )
        return result.stdout

    def package(self, root=None, **environment):
        root = root or self.root
        result = subprocess.run(
            [sys.executable, str(root / "scripts/package_extension.py")],
            cwd=root, env={**self.environment, **environment},
            capture_output=True, text=True, check=False,
        )
        self.assertEqual(result.returncode, 0, result.stderr)
        evidence_path = root / "output/extension/evidence.json"
        evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
        return evidence, evidence_path

    def assert_rejected(self, evidence_path, source=None):
        with self.assertRaises(ValueError):
            verify(evidence_path.with_name("PhishLens-Extension.zip"),
                   evidence_path, source or self.revision)

    def test_clean_checkout_has_verifiable_identity(self):
        evidence, path = self.package()
        self.assertEqual(evidence["source_commit"], self.revision)
        self.assertEqual(evidence["tested_commit"], self.revision)
        self.assertIs(evidence["runtime_or_packaging_changes"], False)
        self.assertEqual(verify(path.with_name("PhishLens-Extension.zip"), path,
                                self.revision)["files_verified"], 10)

    def test_staged_and_unstaged_runtime_changes_are_dirty(self):
        asset = self.root / "extension/popup.css"
        asset.write_text(asset.read_text(encoding="utf-8") + "\n/* changed */\n",
                         encoding="utf-8")
        for staged in (False, True):
            with self.subTest(staged=staged):
                if staged:
                    self.git("add", "extension/popup.css")
                evidence, path = self.package()
                self.assertIs(evidence["runtime_or_packaging_changes"], True)
                self.assert_rejected(path)

    def test_untracked_required_inputs_cannot_be_clean(self):
        for name in ("extension/popup.css", "scripts/validate_extension.py"):
            with self.subTest(input=name):
                self.git("rm", "--cached", name)
                evidence, path = self.package()
                self.assertIsNone(evidence["runtime_or_packaging_changes"])
                self.assert_rejected(path)
                self.git("add", name)

    def test_ignored_nested_export_does_not_inherit_parent_identity(self):
        export = self.root / "exports/copy"
        self.copy_inputs(export)
        (export / "extension/popup.css").write_text("/* modified export */\n",
                                                    encoding="utf-8")
        evidence, path = self.package(export)
        self.assertIsNone(evidence["source_commit"])
        self.assertIsNone(evidence["tested_commit"])
        self.assertIsNone(evidence["runtime_or_packaging_changes"])
        self.assert_rejected(path)

    def test_ci_variables_cannot_make_nested_export_clean(self):
        export = self.root / "exports/copy"
        self.copy_inputs(export)
        evidence, path = self.package(export, SOURCE_COMMIT=self.revision,
                                      GITHUB_SHA=self.revision)
        self.assertIsNone(evidence["runtime_or_packaging_changes"])
        self.assert_rejected(path)

    def test_ci_source_head_and_tested_merge_identity_remain_distinct(self):
        source_head = "a" * 40
        evidence, path = self.package(SOURCE_COMMIT=source_head, GITHUB_SHA=self.revision)
        self.assertEqual(evidence["source_commit"], source_head)
        self.assertEqual(evidence["tested_commit"], self.revision)
        self.assertIs(evidence["runtime_or_packaging_changes"], False)
        self.assertEqual(verify(path.with_name("PhishLens-Extension.zip"), path,
                                source_head)["files_verified"], 10)
