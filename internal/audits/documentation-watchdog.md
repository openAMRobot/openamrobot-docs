# Documentation Watchdog

## Purpose

The watchdog is a read-only audit that detects source-repository commits and identifies documentation sections that may deserve review. It complements, rather than replaces, the MkDocs build and repository-quality workflows.

## Current behavior

- Reads the existing `REPOSITORIES` mapping from `hooks/page_context.py` using Python's AST parser; it does not import or execute the hook.
- Queries GitHub's REST API for commits after the previous successful watchdog run. On the first run, it inspects the previous seven days unless a start time is supplied.
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

Open **Actions → Documentation watchdog → Run workflow**. Optionally provide an ISO-8601 `since` time. Without it, the script uses the prior successful watchdog run's start time. The first run falls back to the previous seven days. The report is attached to the completed workflow run as an artifact named `documentation-watchdog-<run id>`.

The schedule is Thursday at 13:00 UTC. GitHub cron is UTC-based and does not follow daylight saving time, so this is not a fixed 14:00 Europe/Berlin schedule year-round.

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
- The workflow uses GitHub Actions' standard floating action tags already common in this repository; action pinning should follow the organization's policy in a separate reviewed change.
- The initial implementation should be reviewed in a branch before enabling the schedule on the default branch.
