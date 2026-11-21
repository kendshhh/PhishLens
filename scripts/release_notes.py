"""Extract the versioned candidate section for publication after release gates pass."""

from __future__ import annotations

import argparse
import re
from pathlib import Path


def extract_notes(changelog: str, version: str) -> str:
    if not re.fullmatch(r"(0|[1-9]\d*)\.(0|[1-9]\d*)\.(0|[1-9]\d*)", version or ""):
        raise ValueError("Release notes require a semantic version X.Y.Z")
    lines = changelog.splitlines()
    heading = f"## [{version}] - Candidate, not released"
    try:
        start = lines.index(heading)
    except ValueError as exc:
        raise ValueError("Changelog has no matching unreleased candidate section") from exc
    end = next((index for index in range(start + 1, len(lines))
                if lines[index].startswith("## [")), len(lines))
    body = "\n".join(lines[start + 1:end]).strip()
    if not body:
        raise ValueError("Candidate changelog section is empty")
    return f"# PhishLens v{version}\n\n{body}\n"


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--changelog", type=Path, default=Path("CHANGELOG.md"))
    parser.add_argument("--version", required=True)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    try:
        notes = extract_notes(args.changelog.read_text(encoding="utf-8"), args.version)
        args.output.write_text(notes, encoding="utf-8")
    except (OSError, ValueError) as exc:
        parser.exit(1, f"Release notes rejected: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
