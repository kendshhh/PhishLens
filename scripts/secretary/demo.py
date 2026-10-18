"""Offline demonstration artifacts. These are explicitly synthetic, not hosted verification."""
import base64
import json
from pathlib import Path

from .core import render
from .preview import package

ROOT = Path(__file__).resolve().parents[2]


def main():
    config = json.loads((ROOT / ".github/secretary.json").read_text())
    sha = "0" * 40
    snapshot = {"pr": {"number": 0, "title": "OFFLINE EXAMPLE — history rendering", "body": "Related to #23",
        "draft": False, "user": {"login": "synthetic-teammate"}, "head": {"sha": sha, "repo": {"full_name": "kendshhh/PhishLens"}},
        "base": {"ref": "main", "repo": {"full_name": "kendshhh/PhishLens"}}},
        "files": [{"filename": "extension/js/history.js", "status": "modified", "patch": "@@ -1 +1 @@\n-old\n+new"}],
        "jobs": {n: {"conclusion": "success"} for n in config["required_ci_jobs"]},
        "preview": {"state": "waiting", "current": False}, "config": config, "gaps": []}
    output = ROOT / "output/secretary-demo"
    output.mkdir(parents=True, exist_ok=True)
    report = "# Offline example — synthetic evidence only\n\nNo real PR, deployment, visual test or human approval is represented below.\n\n" + render(snapshot, {"status": "disabled"}, "OFFLINE EXAMPLE")
    (output / "example-report.md").write_text(report, encoding="utf-8")

    class LocalAssets:
        def request(self, path):
            asset = path.split("contents/extension/", 1)[1].split("?", 1)[0]
            data = (ROOT / "extension" / asset).read_bytes()
            return {"encoding": "base64", "size": len(data), "content": base64.b64encode(data).decode()}

    package(LocalAssets(), sha, 0, config, output / "Veriqo-OFFLINE-DEMO-Extension.zip")
    print("Created output/secretary-demo/example-report.md and Veriqo-OFFLINE-DEMO-Extension.zip")
    print("Offline demonstration only. The zero SHA is not a deployed version; do not use for PR acceptance.")


if __name__ == "__main__":
    main()
