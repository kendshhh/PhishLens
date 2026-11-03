"""Snapshot public benchmark evidence, leaving source mail and runs untouched."""

import argparse
import datetime as dt
import hashlib
import html
import json
from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parents[1]
STUDIES = (
    "academic_pilot_v2", "real_email_v3", "english_real_v4_checkpoint_clean",
    "reviewed_functional_explanations_v6", "real_readiness_v10",
    "compact_classifiers_v11", "tfidf_false_alarm_v12", "tfidf_false_alarm_v12a",
)
PUBLIC_NAMES = (
    "summary.md", "decision_summary.md", "terminology.md", "terminology.html", "Graph.csv",
    "metrics.json", "run_record.json", "verification.json", "final_lock.json",
    "final_verification.json", "integration_verification.json",
    "parity_verification.json", "visual_report.html", "config.yaml",
)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source", type=Path, required=True)
    args = parser.parse_args()
    source = args.source.resolve()
    target = ROOT / "benchmark-records"
    if source == ROOT.resolve():
        parser.error("Source must be the original benchmark checkout")
    records = []

    def copy(relative, destination=None):
        src = source / relative
        if not src.is_file():
            return
        dest = target / (destination or relative)
        dest.parent.mkdir(parents=True, exist_ok=True)
        digest = hashlib.sha256(src.read_bytes()).hexdigest()
        # Never silently replace an existing archive with different evidence.
        if dest.exists() and hashlib.sha256(dest.read_bytes()).hexdigest() != digest:
            raise RuntimeError(f"Existing snapshot differs: {dest.relative_to(target)}")
        shutil.copyfile(src, dest)
        records.append({"file": dest.relative_to(target).as_posix(),
                        "source": str(src), "bytes": src.stat().st_size,
                        "sha256": digest})

    for study in STUDIES:
        base = Path("benchmarks") / study
        copy(base / "config.yaml", Path(study) / "config.yaml")
        for name in PUBLIC_NAMES:
            copy(base / "results" / name, Path(study) / name)
        for chart in (source / base / "results" / "charts").glob("*"):
            if chart.suffix in {".svg", ".png"}:
                copy(chart.relative_to(source), Path(study) / "charts" / chart.name)

    for relative in (
        "output/benchmarks/2026-10-22-comparison/report.md",
        "output/benchmarks/local-20261023/TEAM_HANDOFF.md",
        "output/benchmarks/kaggle-free-20261022/summary.md",
        "output/benchmark-explained-20261029/walkthrough.html",
        "output/benchmark-history-20261027/visual_report.html",
        "output/benchmark-history-20261027/terminology.html",
        "output/benchmark-history-20261027/benchmark_history.csv",
        "output/benchmark-history-20261027/visual_chart_data.json",
    ):
        copy(Path(relative), Path("history") / Path(relative).parent.name / Path(relative).name)
    for chart in (source / "output/benchmark-history-20261027/charts").glob("*"):
        if chart.suffix in {".svg", ".png"}:
            copy(chart.relative_to(source), Path("history/benchmark-history-20261027/charts") / chart.name)

    manifest = {"snapshot_date_manila": "2026-10-29", "source_checkout": str(source),
                "copied_at_utc": dt.datetime.now(dt.UTC).isoformat(),
                "integration_base": "1344fcb061272bac93ced5911f1ab8fbb3b6785d",
                "scope": "Public report snapshot; no raw mail, predictions or private fixtures",
                "files": records}
    (target / "manifest.json").write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    links = []
    for item in records:
        if item["file"].endswith(("summary.md", "decision_summary.md", "visual_report.html", "walkthrough.html", "report.md", "TEAM_HANDOFF.md")):
            name = html.escape(item["file"])
            links.append(f'<li><a href="{name}">{name}</a></li>')
    (target / "index.html").write_text('''<!doctype html><html lang="en"><meta charset="utf-8">
<meta name="viewport" content="width=device-width"><title>PhishLens benchmark records</title>
<style>body{max-width:960px;margin:40px auto;padding:0 24px;font:17px/1.6 system-ui;color:#17233b}
li{margin:12px 0}a{color:#1453ad}code{background:#eef2f8;padding:3px}</style>
<h1>PhishLens benchmark records</h1><p>Snapshot: 29 October 2026. Original outcomes,
setbacks and qualifications are preserved. Different studies used different data;
do not combine them into one accuracy ranking.</p>
<p><strong>Selected for the advisory integration pilot: TF-IDF v12a.</strong>
It passed eight measured scoped checks. The original full benchmark is incomplete.</p>
<p><a href="README.md">Reading guide and source locations</a> ·
<a href="manifest.json">File sizes and SHA-256 inventory</a></p><ul>'''
        + "\n".join(links) + "</ul></html>\n", encoding="utf-8")
    print(f"Preserved {len(records)} public evidence files in {target}")


if __name__ == "__main__":
    main()
