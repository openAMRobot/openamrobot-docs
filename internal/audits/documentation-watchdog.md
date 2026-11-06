# Documentation Watchdog

## Purpose

The watchdog is a read-only audit that detects source-repository commits and identifies documentation sections that may deserve review. It complements, rather than replaces, the MkDocs build and repository-quality workflows.

## Current behavior

- Reads the existing `REPOSITORIES` mapping from `hooks/page_context.py` using Python's AST parser; it does not import or execute the hook.
- Queries GitHub's REST API for commits after the selected audit-window start. The workflow is currently manual-only; it does not run on a schedule and provides no automatic scheduled coverage. A manual run with an explicit `--since` uses that timestamp. Without `--since`, it inspects the previous `initial_days` (seven by default).
- Collects commit messages, commit links, and changed file paths.
- Lists Markdown pages beneath documentation prefixes owned by each changed source repository.
- Writes Markdown and JSON reports. The workflow uploads them as a 90-day artifact.
- Reports API errors as incomplete checks.

## How to run manually

Requires Python 3.10+ and a GitHub token with read access to the documentation repository's Actions workflow runs and public source repositories. Set `GITHUB_TOKEN` in the environment; never paste tokens into a command committed to the repository.

```bash
GITHUB_TOKEN=... python scripts/documentation_watchdog.py \
  --repo-root . \
  --output-dir /tmp/documentation-watchdog
```

For a specific audit window:

```bash
GITHUB_TOKEN=... python scripts/documentation_watchdog.py \
  --repo-root . \
  --output-dir /tmp/documentation-watchdog \
  --since 2026-10-17T00:00:00Z
```

Outputs:

- `documentation-watchdog.md` — human-readable report.
- `documentation-watchdog.json` — structured report for later tooling.

## How to run in GitHub Actions

Open **Actions → Documentation watchdog → Run workflow**. The workflow is **manual-only**: there is no `schedule` trigger and no automatic recurring audit. Optionally provide an ISO-8601 `since` time. With an explicit value, the manual run audits from that timestamp; without one, it inspects the previous `initial_days` (seven by default). A manual run does not advance or establish scheduled coverage. The report is attached to the completed workflow run as an artifact named `documentation-watchdog-<run id>`.

**Future proposal only:** a Thursday 13:00 UTC cadence has been discussed, but it is not active. Any schedule requires separate project-owner approval of cadence, coverage semantics, report ownership and review.

## How to interpret the report

- **Source changed** means GitHub returned commits in the selected time window.
- **Documentation review candidate** means the source repository owns the listed documentation section according to the existing path-prefix mapping.
- A candidate is not a confirmed documentation defect. The current mapping is repository-level, not source-file-level, so a change to one source file may list multiple pages.
- **Audit incomplete** means a repository could not be checked; it must not be interpreted as “no changes.”

## Safety boundary

The script does not edit documentation, commit or push changes, or open pull requests. It does not assert technical correctness, safety, or physical acceptance. A maintainer must inspect the source diff and relevant documentation before deciding whether an update is needed.

## Limitations and follow-up

- The report uses broad ownership prefixes from the current MkDocs hook.
- GitHub's commit detail API can truncate changed-file lists for very large commits; the report flags this when visible.
- The first-run fallback only covers the configured number of days (seven by default).
- The watchdog workflow pins all three GitHub Actions dependencies to commit SHAs. Keep those pins updated through reviewed dependency changes.
- The workflow must remain manual-only until the project owner separately approves scheduled operation, including cadence, coverage semantics, report ownership and review.
