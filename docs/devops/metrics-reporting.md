# Replay consultation metrics offline

For the current PhishLens DORA 4+1 snapshot, see
[the 2026-11-25 report](dora-report-2026-11-25.md) and its redacted source
metadata. Reproduce it from the repository root with GitHub CLI and the
authenticated Render CLI:

```powershell
./scripts/collect_dora_evidence.ps1 -OutputPath docs/devops/evidence/dora-source-2026-11-25.json
python -m scripts.report_dora_metrics docs/devops/evidence/dora-source-2026-11-25.json docs/devops/dora-report-2026-11-25.md
```

The DORA report keeps change-failure rate, failed-deployment recovery time,
deployment rework, and comparable optimization explicitly unmeasured when the
required linked evidence is absent. It does not infer them from CI failures or
from zero observed incidents.

Related: #40 and #41, verified Week 2 DevOps metrics/reporting responsibilities.
This command works independently of PR #55 and does not contact GitHub, Render,
the database or an AI provider. It creates a summary from existing observer data.

Download metrics.json from the production observer's
Veriqo-Production-Evidence artifact, retain the originating run link, then run
from the repository root:

```powershell
python scripts/report_devops_metrics.py path/to/metrics.json output/consultation-metrics.md
```

The output directory must already exist. Keep the original JSON alongside the
report; do not replace it with rounded presentation values. The command refuses
to overwrite its input. Missing metrics stay 'not measured'; zero is preserved.
Invalid/nonfinite/negative values fail instead of producing a credible-looking
report. Source workflow links are limited to canonical GitHub Actions run URLs;
raw observer error/log fields are never copied into the summary.

The period is shown in UTC to match the source evidence. Use local dates when
recording the actual consultation. Sample counts, separate pending/cancelled
outcomes and bounded deployment meanings remain visible. A currently-live
deployment count is not all successful deliveries in the period. Recovery still
requires real incident/restoration timestamps. This utility does not collect new
measurements, demonstrate an optimization, certify production health or replace
deployment/browser acceptance.

Before presenting, attach the source observer run/artifact, identify the actual
pipeline change and link its PR, explain differences in coverage between samples,
and supply actual recovery/process evidence where available. Owner: Kendra.
Actual team feedback and completed rehearsal cannot be generated from metrics.

## Validation

Eight focused tests cover missing versus zero, unit conversion/sample retention,
pending/deployment scope, invalid numbers/shapes, unsafe source links, sensitive
field exclusion and ordered reporting periods. Changed-file Ruff passed.

Replayed the retained week1-production-2026-10-19.json: 47 PR duration samples
average 1.72 minutes, 18 main samples average 0.85 minutes, and latest-outcome
success rate is 87.88%. These are rounded historical evidence, not a current
measurement. The generated example is output/devops/week1-consultation-report.md
and is excluded from source control. GitHub CI must validate the new branch.
