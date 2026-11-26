"""Render a DORA 4+1 report from a redacted, timestamped evidence snapshot."""

from __future__ import annotations

import argparse
import json
import math
import re
import statistics
from datetime import UTC, datetime
from pathlib import Path
from typing import Any

FAILED_DEPLOYMENT_STATUSES = {"build_failed", "update_failed", "pre_deploy_failed"}
SUCCESSFUL_DEPLOYMENT_STATUSES = {"live", "deactivated"}


def parse_time(value: Any, label: str) -> datetime:
    if not isinstance(value, str):
        raise TypeError(f"{label} must be an ISO-8601 timestamp")
    normalized = value.replace("Z", "+00:00")
    fractional = re.search(r"\.(\d+)(?=[+-]\d{2}:\d{2}$)", normalized)
    if fractional:
        micros = fractional.group(1)[:6].ljust(6, "0")
        normalized = normalized[:fractional.start(1)] + micros + normalized[fractional.end(1):]
    try:
        parsed = datetime.fromisoformat(normalized)
    except ValueError as exc:
        raise ValueError(f"{label} must be an ISO-8601 timestamp") from exc
    if parsed.tzinfo is None:
        raise ValueError(f"{label} must include a timezone")
    return parsed.astimezone(UTC)


def summarize(values: list[float]) -> dict[str, float | int] | None:
    if not values:
        return None
    ordered = sorted(values)
    p90_index = math.ceil(0.9 * len(ordered)) - 1
    return {
        "n": len(ordered),
        "median": statistics.median(ordered),
        "p90": ordered[p90_index],
        "minimum": ordered[0],
        "maximum": ordered[-1],
    }


def compute(snapshot: dict[str, Any]) -> dict[str, Any]:
    if not isinstance(snapshot, dict) or snapshot.get("schema_version") != 1:
        if not isinstance(snapshot, dict):
            raise TypeError("DORA evidence must be an object")
        raise ValueError("Unsupported DORA evidence schema")
    window = snapshot.get("window_utc")
    if not isinstance(window, dict):
        raise TypeError("window_utc is required")
    start = parse_time(window.get("start"), "window start")
    end = parse_time(window.get("end"), "window end")
    days = (end - start).total_seconds() / 86400
    if days <= 0 or days > 90:
        raise ValueError("window must be positive and no longer than 90 days")

    ci_runs = snapshot.get("ci_runs")
    prs = snapshot.get("merged_pull_requests")
    deployments = snapshot.get("production_deployments")
    if not all(isinstance(items, list) for items in (ci_runs, prs, deployments)):
        raise TypeError("CI, PR, and deployment evidence must be arrays")

    ci_seconds: list[float] = []
    ci_success = ci_failure = ci_cancelled = 0
    for run in ci_runs:
        if not isinstance(run, dict):
            raise TypeError("CI run record must be an object")
        started_value = run.get("started_at_utc")
        finished_value = run.get("finished_at_utc")
        if started_value and finished_value:
            started = parse_time(started_value, "CI run start")
            finished = parse_time(finished_value, "CI run finish")
            duration = (finished - started).total_seconds()
            if duration < 0:
                raise ValueError("CI run duration cannot be negative")
            ci_seconds.append(duration)
        conclusion = run.get("conclusion")
        if conclusion == "success":
            ci_success += 1
        elif conclusion == "failure":
            ci_failure += 1
        elif conclusion == "cancelled":
            ci_cancelled += 1

    pr_by_sha: dict[str, datetime] = {}
    for pr in prs:
        if not isinstance(pr, dict):
            raise TypeError("merged PR record must be an object")
        sha = pr.get("merge_sha")
        if not isinstance(sha, str) or not sha:
            raise ValueError("merged PR must include merge_sha")
        merged = parse_time(pr.get("merged_at_utc"), "PR merge time")
        if sha in pr_by_sha and pr_by_sha[sha] != merged:
            raise ValueError("a merge SHA maps to conflicting PR merge times")
        pr_by_sha[sha] = merged

    successful_deploys: list[dict[str, Any]] = []
    failed_attempts = 0
    for deploy in deployments:
        if not isinstance(deploy, dict):
            raise TypeError("deployment record must be an object")
        status = deploy.get("status")
        if status in SUCCESSFUL_DEPLOYMENT_STATUSES:
            if not deploy.get("finished_at_utc"):
                raise ValueError("successful deployment must include finished_at_utc")
            successful_deploys.append(deploy)
        elif status in FAILED_DEPLOYMENT_STATUSES:
            failed_attempts += 1

    earliest_by_sha: dict[str, datetime] = {}
    for deploy in successful_deploys:
        sha = deploy.get("sha")
        if sha not in pr_by_sha:
            continue
        finish = parse_time(deploy.get("finished_at_utc"), "deployment finish")
        if finish < pr_by_sha[sha]:
            continue
        prior = earliest_by_sha.get(sha)
        if prior is None or finish < prior:
            earliest_by_sha[sha] = finish
    lead_minutes = [
        (finish - pr_by_sha[sha]).total_seconds() / 60
        for sha, finish in earliest_by_sha.items()
    ]

    recovery_events = snapshot.get("recovery_events")
    rework_classifications = snapshot.get("deployment_classifications")
    recovery_minutes: list[float] = []
    if recovery_events is not None:
        if not isinstance(recovery_events, list):
            raise TypeError("recovery_events must be null or an array")
        for event in recovery_events:
            started = parse_time(event.get("failure_started_at_utc"), "incident start")
            recovered = parse_time(event.get("service_restored_at_utc"), "incident recovery")
            duration = (recovered - started).total_seconds() / 60
            if duration < 0:
                raise ValueError("recovery duration cannot be negative")
            recovery_minutes.append(duration)

    rework_rate = None
    if rework_classifications is not None:
        if not isinstance(rework_classifications, list):
            raise TypeError("deployment_classifications must be null or an array")
        if rework_classifications:
            if len(rework_classifications) != len(successful_deploys):
                raise ValueError("every successful deployment must be classified before computing rework")
            allowed = {"planned", "unplanned_rework"}
            classes = [item.get("classification") if isinstance(item, dict) else None
                       for item in rework_classifications]
            if any(value not in allowed for value in classes):
                raise ValueError("deployment classifications must be planned or unplanned_rework")
            rework_rate = 100 * classes.count("unplanned_rework") / len(classes)

    return {
        "period_start": start,
        "period_end": end,
        "window_days": days,
        "ci": {
            "duration_seconds": summarize(ci_seconds),
            "runs": len(ci_runs), "success": ci_success, "failure": ci_failure,
            "cancelled": ci_cancelled,
            "duration_samples": len(ci_seconds),
            "success_rate_percent": 100 * ci_success / len(ci_runs) if ci_runs else None,
        },
        "deployment_frequency": {
            "successful_deployments": len(successful_deploys),
            "per_day": len(successful_deploys) / days,
            "per_week": len(successful_deploys) * 7 / days,
            "attempts": len(deployments),
            "failed_attempts": failed_attempts,
        },
        "change_lead_time_minutes": summarize(lead_minutes),
        "matched_change_count": len(lead_minutes),
        "eligible_merge_count": len(prs),
        "matched_merge_shas": len(earliest_by_sha),
        "unmatched_successful_deploys": max(0, len(successful_deploys) - len(earliest_by_sha)),
        "change_fail_rate_percent": None,
        "recovery_time_minutes": summarize(recovery_minutes) if recovery_events is not None else None,
        "rework_rate_percent": rework_rate,
    }


def fmt_duration(summary: dict[str, Any] | None, unit: str) -> str:
    if summary is None:
        return "not measured"
    return (f"median {summary['median']:.2f} {unit}; p90 {summary['p90']:.2f} {unit}; "
            f"range {summary['minimum']:.2f}–{summary['maximum']:.2f} {unit} (n={summary['n']})")


def render(snapshot: dict[str, Any]) -> str:
    metrics = compute(snapshot)
    ci = metrics["ci"]
    frequency = metrics["deployment_frequency"]
    urls = snapshot.get("source_urls", {})
    start = metrics["period_start"].strftime("%Y-%m-%d %H:%M UTC")
    end = metrics["period_end"].strftime("%Y-%m-%d %H:%M UTC")
    recovery = metrics["recovery_time_minutes"]
    recovery_text = fmt_duration(recovery, "min") if recovery else "not measured (no qualifying production recovery records)"
    lead = fmt_duration(metrics["change_lead_time_minutes"], "min")
    rework = "not measured (deployments lack reviewed planned/unplanned classifications)"
    if metrics["rework_rate_percent"] is not None:
        rework = f"{metrics['rework_rate_percent']:.2f}%"
    deployment_proxy = f"{frequency['failed_attempts']}/{frequency['attempts']} failed Render deployment attempts"
    success_rate = (f"{ci['success_rate_percent']:.2f}%" if ci["success_rate_percent"] is not None
                    else "not measured")
    pipeline_time = fmt_duration(ci["duration_seconds"], "s")
    return f"""# PhishLens DORA delivery report — {metrics['period_end'].strftime('%Y-%m-%d')}

**Snapshot:** `{snapshot.get('current_main_sha', 'unknown')}`<br>
**Window:** {start} through {end} ({metrics['window_days']:.2f} days)<br>
**Collected:** {snapshot.get('collected_at_utc', 'unknown')}

This report contains the four DORA delivery metrics and the current fifth metric,
deployment rework rate. It also reports CI wall time as an internal pipeline
measure. DORA metric names and definitions follow the [current DORA guide](https://dora.dev/guides/dora-metrics/);
the course's “time to restore” is represented by failed-deployment recovery time.

| Metric | Result | Denominator and method |
|---|---|---|
| Change lead time | {lead} | {metrics['matched_change_count']} unique merged PR SHAs matched exactly to the first successful Render deployment after merge, out of {metrics['eligible_merge_count']} merged PRs in the window. Uses merge-to-live as a reproducible proxy for commit-to-production; records without an exact SHA match are excluded. |
| Deployment frequency | {frequency['successful_deployments']} successful Render deploy records; {frequency['per_day']:.2f}/day ({frequency['per_week']:.2f}/week) | {frequency['successful_deployments']} records with `live` or `deactivated` status divided by {metrics['window_days']:.2f} days. This is the complete set assembled from the retained Nov 14 inventory and the current Render inventory. |
| Change fail rate | **Not measured** | Current source does not link production incidents or failed changes to the corresponding release SHA. Diagnostic only: {deployment_proxy}; this deploy-attempt proxy is not the DORA change fail rate. |
| Failed-deployment recovery time | {recovery_text} | Recovery requires timestamps from production failure detection to verified service restoration. The available source contains no qualifying production recovery event; this is not zero. |
| Deployment rework rate | {rework} | Requires each successful production deployment to be classified as planned or unplanned rework. No reviewed classification ledger is available; this is not zero. |
| CI workflow wall time (supplemental) | {pipeline_time} | {ci['duration_samples']} timed main-push CI runs; outcomes across {ci['runs']} completed runs: {ci['success']} success, {ci['failure']} failure, {ci['cancelled']} cancelled; successful-run share {success_rate}. From run start to completion, excluding queue before start and environment wait outside the workflow run. |

## Optimization result

No current like-for-like before/after pipeline optimization is established. The
latest reusable comparison remains the October 21 staging-cache trial: two
samples per condition; the whole staging job averaged 40.5 seconds before and
44.0 seconds with cache. That experiment did not demonstrate an end-to-end gain.
The October 28 extension-cache trial also did not show a job-time improvement.
See [optimization evidence](optimizations.md). Keep this criterion open until a
specific workflow change is compared with the same event, checks, runner, and
queue/approval treatment over adequate samples.

## Sources and limits

- GitHub main CI runs: [{urls.get('ci_runs', 'source URL missing')}]({urls.get('ci_runs', 'source URL missing')})
- Merged PR metadata: [{urls.get('merged_pull_requests', 'source URL missing')}]({urls.get('merged_pull_requests', 'source URL missing')})
- Render production deploy inventory: [{urls.get('production_deploys', 'source URL missing')}]({urls.get('production_deploys', 'source URL missing')})
- Retained Render inventory through Nov 14: `{urls.get('historical_render_inventory', 'source file missing')}`
- DORA definitions: [DORA software delivery metrics](https://dora.dev/guides/dora-metrics/)

Render deployments with `deactivated` status were previously live and later
superseded. Deployment frequency counts successful deploy records, including
repeat deploys of the same SHA; change lead time deduplicates by merged SHA.
Current production is on `{snapshot.get('production_sha', 'not included in this snapshot')}`;
the report's deploy history does not imply that the current main commit has been
released. No production user data or inference telemetry is included.
"""


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("snapshot", type=Path)
    parser.add_argument("output", type=Path)
    args = parser.parse_args()
    try:
        snapshot = json.loads(args.snapshot.read_text(encoding="utf-8-sig"))
        report = render(snapshot)
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(report, encoding="utf-8")
    except (OSError, json.JSONDecodeError, TypeError, ValueError) as exc:
        parser.exit(1, f"Invalid or unreadable DORA evidence; report was not written: {exc}\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
