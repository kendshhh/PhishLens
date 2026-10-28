# Issue and pull request labels

Apply labels when opening every issue and pull request, including drafts.
Use the existing repository labels consistently:

- Type: `bug` for fixes, `documentation` for documentation, and `enhancement` for feature, CI, tooling, maintenance and test improvements. Multiple types are appropriate when the scope warrants them.
- Area: add each relevant `area: devops`, `area: frontend`, `area: backend`, `area: database`, `area: api`, `area: ai`, `area: integration` or `area: testing` label.
- Sprint: add the sprint owning the work (`sprint-1` or `sprint-2`). Preserve the original sprint and add the current sprint plus `carryover` when explicitly replanned.
- Priority: use the issue's agreed `priority:P0` or `priority:P1`; do not infer urgency from a PR's existence.

PRs should use the applicable type, area and sprint labels from their linked issue, adjusted to their actual scope. Labels describe work; they do not establish acceptance, review or delivery.

Before finishing issue or PR creation, verify that labels were saved. When auditing the repository, include open and closed issues and PRs, and preserve existing labels unless their meaning is demonstrably wrong.
