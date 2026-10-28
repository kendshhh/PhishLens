"""Create a consultation summary from an exported observer metrics.json."""

import argparse
import datetime as dt
import json
import math
import re
from pathlib import Path


def number(value, label):
    if value is None:
        return "not measured"
    if isinstance(value, bool) or not isinstance(value, (int, float)):
        raise TypeError(f"{label} must be a nonnegative finite number or null")
    try:
        finite = math.isfinite(value)
    except OverflowError as error:
        raise ValueError(f"{label} is too large") from error
    if not finite or value < 0:
        raise ValueError(f"{label} must be a nonnegative finite number or null")
    return f"{value:.2f}" if isinstance(value, float) else str(value)


def minutes(value, label):
    number(value, label)
    return "not measured" if value is None else f"{value / 60:.2f}"


def render(data):
    if not isinstance(data, dict):
        raise TypeError("Observer evidence must be a JSON object")
    pipeline = data.get("pipeline", {})
    deployments = data.get("deployments", {})
    if not isinstance(pipeline, dict) or not isinstance(deployments, dict):
        raise TypeError("Pipeline and deployment evidence must be objects")
    rate = pipeline.get("success_rate_percent")
    number(rate, "success rate")
    if rate is not None and rate > 100:
        raise ValueError("Success rate must be between 0 and 100")
    period = "not measured"
    start, end = data.get("period_start"), data.get("period_end")
    if start is not None or end is not None:
        start, end = dt.datetime.fromisoformat(start), dt.datetime.fromisoformat(end)
        if start.tzinfo is None or end.tzinfo is None or end < start:
            raise ValueError("Reporting period must have ordered timezone-aware timestamps")
        period = f"{start.astimezone(dt.UTC).isoformat()} to {end.astimezone(dt.UTC).isoformat()}"
    rows = [
        ("Average PR pipeline (minutes)", minutes(pipeline.get("average_pr_pipeline_seconds"), "PR duration")),
        ("PR duration samples", number(pipeline.get("pr_duration_samples"), "PR samples")),
        ("Average main pipeline (minutes)", minutes(pipeline.get("average_main_pipeline_seconds"), "main duration")),
        ("Main duration samples", number(pipeline.get("main_duration_samples"), "main samples")),
        ("Latest-outcome CI success rate (%)", number(rate, "success rate")),
        ("Successful workflows", number(pipeline.get("successes"), "successes")),
        ("Failed workflows", number(pipeline.get("failures"), "failures")),
        ("Cancelled workflows (separate)", number(pipeline.get("cancelled"), "cancelled")),
        ("Pending workflows (separate)", number(pipeline.get("pending"), "pending")),
        ("Observed currently-live deployments", number(deployments.get("observed_live_deployments"), "deployments")),
        ("Failed deployments in snapshot", number(deployments.get("failed_deployments"), "failed deployments")),
        ("Average merge-to-Render-live (minutes)", minutes(deployments.get("average_merge_to_render_live_seconds"), "lead time")),
        ("Merge-to-live samples", number(deployments.get("merge_to_live_samples"), "lead samples")),
        ("Recovery time", "not measured; record actual incident/restoration timestamps separately"),
    ]
    lines = ["# DevOps consultation metrics", "", f"Reporting period (UTC): {period}",
             "", "| Metric | Recorded value |", "|---|---|"]
    lines += [f"| {label} | {value} |" for label, value in rows]
    lines += ["", "CI success rate excludes pending/cancelled/other outcomes. Durations include",
              "queue and approval time when included by the source observer; they are not job",
              "execution benchmarks. Current live-deployment counts are not lifetime successful",
              "delivery totals. Render-live timestamps do not independently prove application availability.",
              "", "Missing values are not zero. No optimization gain or completed recovery is inferred.",
              "This summary does not certify production health or deployment acceptance.",
              "", "## Source workflows", ""]
    sources = data.get("workflow_sources", [])
    if not isinstance(sources, list):
        raise TypeError("Workflow sources must be a list")
    for source in sources:
        # Only emit canonical run URLs; never copy observer errors, logs or arbitrary text.
        if not isinstance(source, str) or not re.fullmatch(
            r"https://github\.com/[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+/actions/runs/[0-9]+", source
        ):
            raise ValueError("Workflow source must be a canonical GitHub run URL")
        lines.append(f"- [Workflow run {source.rsplit('/', 1)[1]}]({source})")
    if not sources:
        lines.append("Sources unavailable; attach the originating observer run/artifact before presenting.")
    return "\n".join(lines) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    if args.input.resolve() == args.output.resolve():
        parser.error("Output must not overwrite source evidence")
    try:
        result = render(json.loads(args.input.read_text(encoding="utf-8-sig")))
        args.output.write_text(result, encoding="utf-8")
    except (OSError, ValueError, TypeError):
        parser.exit(1, "Invalid or unreadable metrics evidence; output could not be generated.\n")
    print(f"Report written: {args.output}")


if __name__ == "__main__":
    main()

