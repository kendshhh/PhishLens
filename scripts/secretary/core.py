"""Pure reporting policy. PR content is data, never instructions or executable code."""
import hashlib
import json
import re

MARKER = "<!-- veriqo-secretary:v1 -->"
RULES = {
    "R1 Persistent CRUD": ("backend/app/routers/history", "backend/models", "extension/js/history"),
    "R2 Backend AI processing": ("backend/ai/", "scripts/benchmark_ai", "docs/ai"),
    "R3 Backend API": ("backend/app/", "docs/api"),
    "R4 Real-data frontend": ("extension/",),
    "R5 Related tables": ("backend/models", "backend/migrations/", "scripts/seed"),
    "R6 Configuration/secrets": (".github/", ".env", "backend/core/", "scripts/"),
    "R7 Failure handling": ("backend/ai/", "backend/app/", "extension/background", "extension/js/api"),
}


def safe(value, limit=1200):
    """Prevent mentions/HTML/markdown injection; redact common credential formats."""
    value = str(value)[:limit]
    value = re.sub(r"(?i)(?:AIza[\w-]{20,}|gh[pousr]_[\w]{15,}|sk-[\w-]{15,})", "[REDACTED]", value)
    value = re.sub(r"(?i)(?:postgres(?:ql)?|https?)://[^\s/@]+:[^\s/@]+@[^\s]+", "[REDACTED URL]", value)
    value = value.replace("@", "@\u200b").replace("<", "&lt;").replace(">", "&gt;")
    return re.sub(r"([\\`*_[\]#|!])", r"\\\1", value).replace("\n", " ").replace("\r", " ")


def application_change(files):
    return any(f["filename"].startswith(("backend/", "extension/")) or
               f["filename"] in {"requirements.txt", "package.json", "package-lock.json"} or
               f["filename"].startswith("scripts/start_staging") for f in files)


def inspect(pr, files, config):
    findings, gaps = [], []
    body = pr.get("body") or ""
    if pr["base"]["ref"] != config["base_branch"]:
        findings.append(("confirmed", "medium", "PR", "Target branch is not the configured main branch."))
    if not re.search(r"(?:#\d+|/issues/\d+)", body):
        findings.append(("confirmed", "medium", "PR description", "Link the relevant issue and acceptance criteria."))
    if len(pr.get("title", "").strip()) < 8 or "Describe the resulting behavior" in body:
        findings.append(("confirmed", "medium", "PR description", "Explain the purpose and resulting behavior instead of leaving template text."))
    if len(files) > config["max_files"] or sum(len(f.get("patch") or "") for f in files) > config["max_diff_chars"]:
        gaps.append("Oversized diff: only the configured first files/characters were inspected. Split the PR or arrange manual review.")
    budget = config["max_diff_chars"]
    for f in files[:config["max_files"]]:
        name = f["filename"]
        if f.get("status") != "removed" and not f.get("patch"):
            gaps.append("Patch unavailable (binary, too large, or API omission): " + safe(name))
        patch = (f.get("patch") or "")[:max(0, budget)]
        budget -= len(patch)
        added = "\n".join(line[1:] for line in patch.splitlines() if line.startswith("+") and not line.startswith("+++"))
        hunk = re.search(r"@@ -\d+(?:,\d+)? \+(\d+)", patch)
        location = name + (":" + hunk[1] + " (first changed hunk)" if hunk else "")
        if (name.startswith(".env") and name != ".env.example") or re.search(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----|AIza[\w-]{20,}|gh[pousr]_[\w]{15,}", added):
            findings.append(("confirmed", "high", location, "Potential credential file/key material. Remove it and check whether rotation is required; values are not reproduced."))
        if name.startswith(".github/workflows/"):
            findings.append(("concern", "medium", location, "Inspect token permissions, event trust boundary, secret access, and required-check changes."))
        if name.startswith("backend/migrations/"):
            findings.append(("concern", "medium", location, "Review backward compatibility and destructive changes. CI uses disposable PostgreSQL; hosted migration needs isolated staging data."))
        if name.endswith(("requirements.txt", "requirements.in", "package.json", "package-lock.json")):
            findings.append(("concern", "medium", name, "Dependency change: review source, lockfile consistency and advisories. No vulnerability scan is implied by this report."))
    names = [f["filename"] for f in files]
    if any(n.startswith("backend/ai/") and not n.endswith("evaluation_cases.py") for n in names):
        findings.append(("concern", "medium", "backend/ai/", "Attach evaluation evidence for behavior/prompt changes; confirm mocked provider, malformed-output, timeout and quota tests. Live provider calls are not run by this agent."))
    requirements = [r for r, prefixes in RULES.items() if any(n.startswith(prefixes) for n in names)]
    return findings[:30], gaps[:30], requirements


def recommendation(pr, jobs, preview, findings, gaps, required, relevant):
    if pr.get("draft"):
        return "BLOCKED", "Draft PR: not ready for formal review or merge."
    if any(kind == "confirmed" and severity == "high" for kind, severity, _, _ in findings):
        return "CHANGES RECOMMENDED", "A confirmed high-severity finding needs correction."
    if pr["head"]["repo"]["full_name"] != pr["base"]["repo"]["full_name"] and relevant:
        return "BLOCKED", "Fork: run ordinary CI without secrets; bring reviewed work to a trusted branch for staging."
    failed = [n for n in required if jobs.get(n, {}).get("conclusion") in {"failure", "cancelled", "timed_out", "action_required", "skipped", "neutral", "stale"}]
    if failed:
        return "CHANGES RECOMMENDED", "Required CI did not pass: " + ", ".join(failed)
    if any(jobs.get(n, {}).get("conclusion") != "success" for n in required):
        return "WAITING FOR CHECKS", "Required CI is pending or missing; no success is inferred."
    if relevant:
        if preview.get("state") in {"failure", "error"}:
            return "BLOCKED", "Staging deployment/smoke failed; inspect linked evidence."
        if not preview.get("current") or preview.get("sha") != pr["head"]["sha"] or preview.get("state") != "success":
            return "WAITING FOR CHECKS", "No successful current staging deployment for this exact head; shared staging may have been replaced."
    if gaps:
        return "BLOCKED", "Review coverage is incomplete; human inspection is required."
    if any(kind == "confirmed" for kind, *_ in findings):
        return "CHANGES RECOMMENDED", "Correct the confirmed description/scope findings. Possible concerns still need human review."
    return "READY FOR KENDRA’S REVIEW", "Configured evidence is available. This is a request for human testing/review, never approval."


def fingerprint(snapshot):
    return hashlib.sha256(json.dumps(snapshot, sort_keys=True, ensure_ascii=True).encode()).hexdigest()


def manual_steps(files):
    names = [f["filename"] for f in files]
    steps = ["Open the linked Actions run and staging deployment. Confirm PR number and full deployed SHA match this report before testing."]
    if any(n.startswith("extension/") for n in names):
        steps += ["Download the staging-extension artifact, extract it, open chrome://extensions, enable Developer mode, and Load unpacked. Check the STAGING banner and SHA.",
                  "Select synthetic text: 'Your account closes today; enter your password at https://example.invalid/verify'. Use Analyze selection. Observe loading followed by a labeled result or a readable provider error; mock output is not AI acceptance.",
                  "Open history: expect Synthetic account notice, phishing, high risk, 93% confidence. Try a disconnected backend for the error state; use an isolated empty test database for the empty state. Select twice rapidly and Clear during loading; older results must not return."]
    if any(n.startswith("backend/") for n in names):
        steps += ["Open staging /docs. Try POST /analyses with synthetic text, then an empty JSON body: expect a structured result (check mode) and HTTP 422 respectively. Record responses without real emails or credentials."]
    if any(n.startswith("backend/migrations/") for n in names):
        steps += ["Inspect the disposable-database migration/seed job and schema relationship tests. Do not test migrations against production. Confirm the Neon staging host privately."]
    steps += ["Compare with the production API /docs and a separately identified production extension profile/build. A website cannot demonstrate context-menu, Chrome storage, permissions, or badge behavior.",
              "Record 'Manual test: SHA, build/run link, browser/version, actions, expected/actual results, evidence, PASS/FAIL' in your own PR comment. Report file/step and synthetic reproduction for problems; then submit a separate formal GitHub review."]
    return steps


def render(snapshot, ai, now):
    pr, config = snapshot["pr"], snapshot["config"]
    files, jobs, preview = snapshot["files"], snapshot["jobs"], snapshot["preview"]
    findings, gaps, requirements = inspect(pr, files, config)
    gaps = gaps + snapshot.get("gaps", [])
    action, reason = recommendation(pr, jobs, preview, findings, gaps, config["required_ci_jobs"], application_change(files))
    sha = pr["head"]["sha"]
    repo = pr["base"]["repo"]["full_name"]
    url = f"https://github.com/{repo}/pull/{pr['number']}"
    lines = [MARKER, f"<!-- evidence:{fingerprint(snapshot)} -->", "## DevOps Secretary — " + action,
             f"PR [#{pr['number']}]({url}) · {safe(pr['title'])} · author {safe(pr['user']['login'])}",
             f"Reviewed head: `{sha}` · report time: {now} · draft: {bool(pr.get('draft'))}",
             "Branch: " + safe(pr["head"].get("ref", "not available")) + " → " + safe(pr["base"]["ref"]),
             "### Summary", f"{len(files)} changed files. Analysis covers bounded patches and available API evidence, not a full security or correctness audit.",
             "Related issues: " + (", ".join(sorted(set(re.findall(r"#\d+", pr.get("body") or "")))) or "not linked"),
             "Course mapping (affected areas, not completion): " + (", ".join(requirements) or "documentation/process only"),
             "### Automated evidence", "| Check | Result | Evidence |", "|---|---|---|"]
    for name in config["required_ci_jobs"]:
        job = jobs.get(name, {})
        link = job.get("html_url") or url + "/checks"
        lines.append(f"| {name} | {safe(job.get('conclusion') or job.get('status') or 'missing')} | [run]({link}) |")
    lines += ["Type checks: not configured in this repository. Dependency compatibility checks are not an advisory audit.",
              "### Proposed version and visual evidence",
              f"Production: {config['production_origin']}/docs · Staging: {config['staging_origin']}/docs",
              f"Preview state: {safe(preview.get('state', 'waiting'))}; current exact SHA: {bool(preview.get('current'))}; deployed SHA: {safe(preview.get('sha', 'not available'))}.",
              f"Deployment/artifact evidence: {preview.get('log_url') or url + '/checks'}",
              "Download **Veriqo-Staging-Extension** from the preview run artifacts. It has a STAGING/PR/SHA banner. The API URL is a working backend, not a browser-extension UI preview.",
              "Before/after screenshots and installed-Chrome verification: not available from this agent; no visual pass is claimed.",
              "### Findings"]
    for kind, severity, location, message in findings:
        lines.append(f"- **{severity.upper()} · {kind}** · {safe(location)}: {safe(message)}")
    if not findings:
        lines.append("No configured heuristic finding. This does not establish absence of defects.")
    lines += ["### AI-assisted explanation", safe(ai.get("summary", "Unavailable or disabled; deterministic evidence remains usable."), 2200),
              "AI status: " + safe(ai.get("status", "unavailable")), "### Deployment, migration and access limits",
              "Shared staging can be replaced by another PR. Recheck its SHA immediately before testing. Hosted PR code receives only isolated non-production runtime credentials; environment approval is a deployment trust gate, not PR approval."]
    lines += ["- " + safe(g) for g in gaps] or []
    lines += ["- Branch protection/admin-only configuration is not inferred from passing jobs. AI quality, persistent CRUD and actual human testing require separate evidence.",
              "### Kendra’s manual test checklist"]
    lines += ["- [ ] " + s for s in manual_steps(files)]
    lines += ["### Recommended next action", "**" + action + "** — " + reason,
              "Automated evidence, this recommendation, your manual test record, and a formal teammate approval are separate. This bot never approves, merges, changes secrets/protection, or rolls back."]
    # Keep Markdown table rows adjacent; separate prose blocks for readable reports.
    output = ""
    previous_table = False
    for line in lines:
        table = line.startswith("|")
        output += ("\n" if table and previous_table else "\n\n") + line
        previous_table = table
    return output.strip()
