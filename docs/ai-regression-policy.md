# AI deterministic regression policy (proposal for issue #93)

**Status:** proposed; AI-owner approval is pending. This document does not claim that the proposed thresholds are agreed.

**AI evaluation owner:** Wilberr (`@EnviousCoal`), identified as owner in [issue #92](https://github.com/kendshhh/PhishLens/issues/92).  
**Reviewer:** `@EnviousCoal`; backup: `@xxTrixia`.

## Deterministic development baseline

The development inventory is `synthetic-v1`: 40 fixed synthetic examples (16 phishing, 16 legitimate, 8 spam), SHA-256 `a755533aa841bc695574196b3147f2c3b408129872a62204c1f4c5f149ab226f`. These cases are regression data, not a representative or held-out evaluation set.

The reviewed deterministic gate recorded 87 selected AI contract/failure test instances in [CI run 41216421988](https://github.com/kendshhh/PhishLens/actions/runs/41216421988): 87 passed, zero failed, zero errors and zero skipped. The run made no provider calls and measured no model predictions.

A separate historical CPU benchmark on 2026-10-18 used local DistilBERT `dima806/phishing-email-detection`, revision `310a5602280486e01dd60e37230980cfcc327b41`, against the same synthetic set. It completed 40/40 calls and recorded binary accuracy 0.60, phishing recall 0.75, phishing precision 0.50, and false-positive rate 0.50. This single development run is a reference observation only; it is not a held-out result, a hosted-model baseline, or a suitability claim. Its recorded evidence is [ai-local-2026-10-18.json](devops/evidence/ai-local-2026-10-18.json).

## Proposed blocking threshold

For the deterministic pull-request gate, require every test ID and parameterized case count declared in `scripts/ai_ci_report.py` to be present and not skipped. Allow zero missing required IDs, zero skipped required IDs, zero failed tests, zero test errors, and zero skipped selected tests. Any violation, missing JUnit report, or incomplete report blocks the gate.

The 87/87 observation is a historical run count, not a fixed minimum: the required suite can grow, while the explicit IDs and parameter counts remain the source of coverage requirements. This threshold covers deterministic contract and failure behavior only.

## Model-quality thresholds

No numeric model-quality threshold is proposed here. The synthetic local-model result above is too limited to justify a deployment-quality bar, and it must not be transferred to a hosted provider. Any future numeric blocker needs the owner to approve the model revision, frozen evaluation split, metrics, and allowed regression before results are used for tuning or acceptance. Held-out examples must remain leakage-controlled.

## Approval record

This proposal is awaiting confirmation from `@EnviousCoal`; `@xxTrixia` is the backup reviewer. Once approved, record the decision in the PR review and update this status from proposed to approved.