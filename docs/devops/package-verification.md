# Verify a downloaded production package

Keep the ZIP and its evidence.json sidecar from the same CI artifact together.
Use the full expected PR head (or main source commit) from GitHub:

```powershell
python scripts/verify_extension_package.py output/extension/PhishLens-Extension.zip output/extension/evidence.json --expected-source FULL_SOURCE_SHA
```

The command rejects abbreviated source IDs, a missing tested revision, a different source, modified/unknown packaging inputs,
archive/file digest mismatches, extra/duplicate archive entries, a version mismatch
and unexpected production or optional host permissions. Its fixed runtime inventory
cannot be expanded by editing the sidecar. It reads the ZIP without extraction.
This command handles production packages from #55, not staging package evidence.

The evidence is unsigned: matching hashes prove consistency with the sidecar,
not independent authenticity of the publisher. Obtain both files from the trusted
Actions run. Source and tested merge commits can differ on pull requests.
Passing integrity checks does not establish installed Chrome acceptance.

The packager uses local Git identity only when its project root is the Git
worktree root and every approved runtime/packaging input is tracked there.
An exported copy nested inside another repository records unknown local
identity/input status, even if CI identity variables are supplied; the verifier
rejects that package. Staged or unstaged input changes are marked modified.
Untracked required inputs have unknown status and cannot be labelled clean.
Build verifiable packages from the intended clean checkout.

## Local continuation validation — October 21, 2026

Fifteen synthetic regression tests cover a valid pair, stale source,
altered archive bytes, an extra file with a recomputed archive digest, incorrect
file digest, modified/unknown inputs, wildcard/optional host permissions, version
drift, malformed evidence, missing tested revision, abbreviated source, an expanded
sidecar inventory and a corrupt ZIP with a clean nonzero CLI exit.
The existing local package identifies source 149808e and modified inputs; it must
not be presented as the latest #55 artifact. No remote artifact was replaced.

The CI follow-up verifies the production artifact immediately after packaging and
before uploading it. Existing staging test discovery executes these regression
tests alongside all existing deployment guards. Latest-head GitHub results remain
necessary; this local verification does not satisfy hosted staging approval.
