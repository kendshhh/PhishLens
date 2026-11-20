# Staging acceptance — 2026-11-15 (application SHA `8c4795f`)

> Historical acceptance for the exact application SHA below. Current service
> identity and release status are in [PIPELINE.md](../../PIPELINE.md); this
> record does not establish acceptance of current `main`, current staging or
> production.

## Source and target

- GitHub repository: `kendshhh/PhishLens` (public; public visibility is intended).
- GitHub `main` at acceptance time: `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` (PR #215). PR #224 later advanced `main` to `c568b7a39a7abf3a99ed7aa318d490397d21bd30` by changing browser-acceptance checks and adding evidence; PR #221 advanced it to `bfa0d61040ea671a81317102f2de536cf86a9844` with a documentation audit; and PR #226 advanced it to `56fba3952b588d289cf539623f9b4149b03258fc` with the hosted-staging URL identity fix. The November 15 record covers exact deployed application SHA `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f`, before that fix, not a deployment of current `main`.
- Render service: `phishlens-staging` (`srv-db92irlg1s2s739404i0`), linked to `main`, auto-deploy off.
- Render deployment: `dep-dbsfqtbbc2fs73bes84g`, status `live`, finished `2026-11-15T00:33:10Z`, exact SHA matched.
- Staging database endpoint `ep-soft-fog-b3orfa8a` maps in Neon project `patient-bird-25428852` to branch `pr-58-staging` (`br-delicate-paper-b381z98i`) and database `phishlens_dev`. The runtime role is `phishlens_staging_app`; migrations use the separate `neondb_owner` role. No connection string or password was read or recorded.
- On the tested `8c4795f` source, the startup guard pinned the host and checked parsed URL host, database path, and username fields, but did not reject `user` or `dbname` query overrides honored by PostgreSQL. The November 15 deployment, mapping, and CRUD results remain point-in-time observations; connection URLs were not read, and the run did not test crafted overrides. PR [#226](https://github.com/kendshhh/PhishLens/pull/226) later fixed the guard: hosted runtime and migration URLs now allow only `sslmode` and `channel_binding`, and psycopg's effective role, database, host, and port are checked before DNS resolution or migration. Its offline regression tests passed (11 tests; Ruff and diff checks passed), with no database connection. [Issue #227](https://github.com/kendshhh/PhishLens/issues/227) tracked that now-merged fix; the original reproduction is documented in [PR #222's review](https://github.com/kendshhh/PhishLens/pull/222#pullrequestreview-5909501325). `/ready` remains connectivity evidence only, not database identity evidence.

## Read-only preflight

All four checks were made after the exact-SHA deployment became live:

| Endpoint | Observed result |
| --- | --- |
| `/version` | HTTP 200; `environment=staging`; exact SHA `8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f` |
| `/health` | HTTP 200; `status=ok` |
| `/ready` | HTTP 200; `status=ready`, database `connected` |
| `/model-info` | HTTP 200; `provider_mode=tfidf`; model SHA-256 `a2f13c256dd46c3267263f8de8f4f822206c5b0ceda96658713e2523a7f9559c` |

## Synthetic feature acceptance and cleanup

Ran the guarded staging CRUD verifier against the exact SHA:

```text
node scripts/verify_crud.mjs --base-url https://phishlens-staging.onrender.com --environment staging --expected-sha 8c4795f5a4ef4e55c44ff44e98ffd6413cb21c6f --allow-writes
```

The run passed create, read, update, clear, delete, and post-delete checks. It created synthetic record `d5c7f840-e329-4055-af2c-abcb3296c066` and reported `cleanedUp=true`. Analysis used the non-paid TF-IDF provider. No Gemini request or production write was made.

This is one backend staging CRUD acceptance run. It does not establish production behavior, installed-Chrome acceptance, held-out model quality, load behavior, or an approved release. The November 14 staging record documents an earlier PR #61 feature-branch run; that evidence does not claim staging deployed later `main` commits `c568b7a`, `bfa0d61`, or `56fba395`.
