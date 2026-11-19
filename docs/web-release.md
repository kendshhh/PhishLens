# Web release configuration and acceptance

The project owner selected PR #244's web frontend for Sprint 4 on November 19,
2026. Chrome tests keep their historical scope. Sign-in on the web is a follow-up
to #247, whose original scope explicitly excluded hosted Auth and deployment.

## Build

Node 22 or later is required. `npm run web:build` needs no dependencies, secrets
or configuration. By default accounts are disabled and local paste-and-check works.
The web build reports an **Uncertain** result when its optional local LLM judge
is unavailable; it must not claim the email is safe. Do not treat this as evidence
that the model has met a phishing-detection quality threshold.

Account-enabled builds take these public settings only:

| Variable | Meaning |
| --- | --- |
| PHISHLENS_WEB_ENV | production (default), staging, or local-only development |
| PHISHLENS_WEB_API_ORIGIN | The matching fixed Render service origin; loopback HTTP only in development |
| PHISHLENS_WEB_AUTH_URL | Verified HTTPS Neon database Auth URL; omitted means accounts disabled |
| PHISHLENS_WEB_BACKEND_SHA | Full approved backend SHA; mandatory when accounts are enabled |

These variables contain **no** database URL, key, password, token or credential.
Never substitute a production target for an unavailable staging target. Build
identity is in `web/dist/build-info.json`: source SHA, dirty flag, public settings
and SHA-256 of the packaged files. Its expected backend SHA is an assertion to
verify during acceptance, not proof of what Render is serving.

Vercel uses the generated Build Output API v3 directory `.vercel/output` (see
[Vercel's specification](https://vercel.com/docs/build-output-api)). The build
sets CSP to self and the single configured Auth origin. The browser calls the
same web origin; fixed rewrites forward only saved-analysis routes and the four
`/backend/{health,ready,version,model-info}` checks to the selected Render service.
API responses are not cacheable. Cookies are removed from API proxy requests and
responses; the API client sends bearer tokens and requires Neon report mode.
This removes the need for a separate Render CORS change for the web client.
Neon Auth remains a direct credentialed request and still needs the exact web
origin on its trusted-origin list. Confirm cookie behavior in the target browser.

`npm run web:serve` previews the generated files, CSP and fixed proxy on loopback
port 4173. A local development build emits no Vercel deployable output. Unit
tests use loopback substitutes and cannot establish hosted rewrite behavior.

## Account safety

An account-enabled client sends `X-Require-Auth-Mode: neon` on every CRUD request.
This backend rejects demo-mode mismatches before its report database dependency.
Deploy a compatible backend before enabling accounts. The backend verifies JWT
signatures, issuer, audience, expiry and the signed verified/active claims and
selects records by the server-owned subject mapping. It does not recheck provider
revocation or changed account status after JWT issuance; a captured token can
remain valid until expiry. That limitation remains a release decision.

Only a boolean failed-sign-out marker goes into persistent web storage, never
credentials or report bodies. With blocked/read-only storage, automatic session
restoration is disabled and explicit sign-in is required on each page load.
The pasted draft/result use tab session storage with a memory fallback.

## Hosted gate (not established by a build or local tests)

The existing designated operator must confirm the exact frontend domain, backend
SHA, isolated database mapping, rotated credential, migration/seed baseline,
effective Auth mode and Auth URL, trusted web origin, idle test window and cleanup
ownership before any shared request or change. Chrome-origin authorization is
not web-origin authorization. Use the previously approved bounded synthetic
account/report operations only after the target and operations are reconfirmed.

Record the frontend source and artifact manifest, backend `/version` and model
hash, real sign-up/verification and browser cookie/session behavior, persistent
save/reload/update, duplicate replay/conflict, per-user GET/PATCH/DELETE 404s,
controlled failure behavior, and exact cleanup. Keep credentials, OTPs, tokens,
connection strings and private email content out of the evidence.

Actual deployment/recovery timings, audience presentation and participant records
are separate requirements. Do not replace them with a local substitute or mark
the release gate Done while they are missing.
