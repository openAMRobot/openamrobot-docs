# Documentation Watchdog implementation bundle

This bundle adds a read-only weekly/manual source-to-documentation audit to `openAMRobot/openamrobot-docs`.

## Files

- `scripts/documentation_watchdog.py` — audit implementation.
- `.github/workflows/documentation-watchdog.yml` — scheduled and manual workflow.
- `tests/test_documentation_watchdog.py` — standard-library unit tests.
- `internal/audits/documentation-watchdog.md` — usage and interpretation guide.

## Install into the repository

From the root of the existing documentation checkout, copy these four paths into the same relative locations. They are new files and do not replace the existing MkDocs hook or workflows.

Then run:

```bash
python -m unittest discover -s tests -v
python -m py_compile scripts/documentation_watchdog.py
```

The script needs a GitHub token to query workflow run history and source commits. Do not hard-code or commit a token. The workflow uses `secrets.GITHUB_TOKEN` with read-only `contents` and `actions` permissions.

Before merging, review the new workflow and follow the organization's action-pinning policy if required. Run the workflow manually first and inspect its report artifact before relying on the weekly schedule.
