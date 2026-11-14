# Deterministic AI development evaluation — 2026-11-14

- Workspace base commit: `8c02a7c86e8b2052d127b5a6a0422a5a80ffa9ea`; the
  worktree was dirty and the evaluation changes were not committed, so this is
  a local run rather than a commit-pinned CI artifact.
- Provider/model: deterministic TF-IDF, model SHA
  `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c`.
- Cohort: 40 synthetic development cases, `synthetic-v1`, hash
  `a755533aa841bc695574196b3147f2c3b408129872a62204c1f4c5f149ab226f`.
- Completion: 40 attempts, 40 responses, 0 inference errors, 0 provider calls,
  0 model downloads.
- Results: binary accuracy **0.65**; phishing recall **0.1875 (3/16)**;
  legitimate false-positive rate **0.0625 (1/16)**. All 8 spam examples were
  predicted as legitimate; this evaluation does not claim three-class accuracy.
- Outcome: the run completed, but the low phishing recall is a product-quality
  concern. There is no AI-owner-approved quality threshold, so do not interpret
  the workflow's completion status as model acceptance. This cohort is
  synthetic and development-only, not held out or representative of production.

The raw local JSONL is ignored under `output/ai-evaluation/`; the deterministic
run is reproducible with the command documented in
[`ai-evaluation.md`](../ai-evaluation.md).
