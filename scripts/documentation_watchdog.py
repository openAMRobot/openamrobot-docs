#!/usr/bin/env python3
"""Read-only audit of source-repository changes that may affect OpenAMRobot docs.

Uses only the Python standard library. It reads the existing REPOSITORIES mapping
from hooks/page_context.py, queries GitHub's REST API, and writes Markdown + JSON
reports to a caller-selected output directory. It never edits documentation or
source repositories.
"""
from __future__ import annotations

import argparse
import ast
import json
import os
import sys
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any
from urllib.error import HTTPError, URLError
from urllib.parse import urlencode
from urllib.request import Request, urlopen

API_ROOT = "https://api.github.com"
OWNER = "openAMRobot"
WORKFLOW_FILE = "documentation-watchdog.yml"
USER_AGENT = "openamrobot-documentation-watchdog/1.0"


class AuditError(RuntimeError):
    """Raised when a required GitHub API operation fails."""


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def isoformat(value: datetime) -> str:
    return value.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_time(value: str) -> datetime:
    parsed = datetime.fromisoformat(value.replace("Z", "+00:00"))
    if parsed.tzinfo is None:
        parsed = parsed.replace(tzinfo=timezone.utc)
    return parsed.astimezone(timezone.utc)


def request_json(url: str, token: str | None = None, retries: int = 3) -> tuple[Any, dict[str, str]]:
    headers = {
        "Accept": "application/vnd.github+json",
        "X-GitHub-Api-Version": "2022-11-28",
        "User-Agent": USER_AGENT,
    }
    if token:
        headers["Authorization"] = f"Bearer {token}"
    last_error: Exception | None = None
    for attempt in range(retries):
        request = Request(url, headers=headers)
        try:
            with urlopen(request, timeout=30) as response:
                payload = json.loads(response.read().decode("utf-8"))
                return payload, {key.lower(): value for key, value in response.headers.items()}
        except HTTPError as exc:
            body = exc.read().decode("utf-8", errors="replace")[:500]
            last_error = AuditError(f"GitHub API returned HTTP {exc.code} for {url}: {body}")
            if exc.code not in (403, 429, 500, 502, 503, 504):
                break
            retry_after = exc.headers.get("Retry-After")
            if retry_after and attempt + 1 < retries:
                time.sleep(min(int(retry_after), 20))
            elif attempt + 1 < retries:
                time.sleep(2 ** attempt)
        except (URLError, TimeoutError, json.JSONDecodeError) as exc:
            last_error = exc
            if attempt + 1 < retries:
                time.sleep(2 ** attempt)
    raise AuditError(str(last_error or "GitHub API request failed"))


def load_repository_mapping(repo_root: Path) -> dict[str, list[str]]:
    """Read REPOSITORIES from the MkDocs hook without importing/executing it."""
    hook = repo_root / "hooks" / "page_context.py"
    if not hook.is_file():
        raise AuditError(f"Cannot find existing repository mapping: {hook}")
    tree = ast.parse(hook.read_text(encoding="utf-8"), filename=str(hook))
    mapping_node = next(
        (node.value for node in tree.body if isinstance(node, ast.Assign)
         and any(isinstance(target, ast.Name) and target.id == "REPOSITORIES" for target in node.targets)),
        None,
    )
    if mapping_node is None:
        raise AuditError("REPOSITORIES mapping was not found in hooks/page_context.py")
    raw = ast.literal_eval(mapping_node)
    if not isinstance(raw, dict):
        raise AuditError("REPOSITORIES mapping is not a dictionary")
    by_repo: dict[str, list[str]] = {}
    for doc_prefix, repo in raw.items():
        if not isinstance(doc_prefix, str) or not isinstance(repo, str):
            raise AuditError("Unexpected entry in REPOSITORIES mapping")
        by_repo.setdefault(repo, []).append(doc_prefix)
    return {repo: sorted(set(prefixes)) for repo, prefixes in sorted(by_repo.items())}


def previous_successful_run(owner: str, repo: str, current_run_id: str | None, token: str) -> datetime | None:
    """Return the start time of the most recent successful prior watchdog run."""
    url = f"{API_ROOT}/repos/{owner}/{repo}/actions/workflows/{WORKFLOW_FILE}/runs?" + urlencode(
        {"status": "success", "per_page": 20}
    )
    payload, _ = request_json(url, token)
    runs = payload.get("workflow_runs", []) if isinstance(payload, dict) else []
    for run in runs:
        if str(run.get("id")) == str(current_run_id):
            continue
        started = run.get("run_started_at") or run.get("created_at")
        if started:
            return parse_time(started)
    return None


def pages_for_prefixes(repo_root: Path, prefixes: list[str]) -> list[str]:
    docs = repo_root / "docs"
    found: set[str] = set()
    for prefix in prefixes:
        target = docs / prefix
        if target.is_file():
            found.add(target.relative_to(repo_root).as_posix())
        elif target.is_dir():
            found.update(path.relative_to(repo_root).as_posix() for path in target.rglob("*.md"))
    return sorted(found)


def github_paginated(url: str, token: str) -> list[Any]:
    items: list[Any] = []
    next_url: str | None = url
    while next_url:
        payload, headers = request_json(next_url, token)
        if not isinstance(payload, list):
            raise AuditError(f"Expected a list response from {next_url}")
        items.extend(payload)
        link = headers.get("link", "")
        next_url = None
        for part in link.split(","):
            if 'rel="next"' in part:
                start = part.find("<")
                end = part.find(">", start + 1)
                if start >= 0 and end > start:
                    next_url = part[start + 1:end]
                break
    return items


def commits_since(repo: str, since: datetime, token: str) -> list[dict[str, Any]]:
    query = urlencode({"since": isoformat(since), "per_page": 100})
    commits = github_paginated(f"{API_ROOT}/repos/{OWNER}/{repo}/commits?{query}", token)
    result: list[dict[str, Any]] = []
    for commit in commits:
        sha = commit.get("sha", "")
        if not sha:
            continue
        detail, _ = request_json(f"{API_ROOT}/repos/{OWNER}/{repo}/commits/{sha}", token)
        files = detail.get("files", []) if isinstance(detail, dict) else []
        result.append({
            "sha": sha,
            "short_sha": sha[:12],
            "message": (detail.get("commit", {}).get("message", "").splitlines() or [""])[0],
            "date": detail.get("commit", {}).get("author", {}).get("date") or commit.get("commit", {}).get("author", {}).get("date", ""),
            "url": detail.get("html_url", commit.get("html_url", "")),
            "files": sorted({item.get("filename", "") for item in files if item.get("filename")}),
            "files_truncated": len(files) >= 300,
        })
    return result


def markdown_report(report: dict[str, Any]) -> str:
    lines = [
        "# OpenAMRobot Documentation Watchdog",
        "",
        f"- **Generated:** {report['generated_at']}",
        f"- **Audit window starts:** {report['since']}",
        f"- **Window basis:** {report['window_basis']}",
        f"- **Repositories checked:** {report['repositories_checked']}",
        f"- **Repositories with errors:** {report['repositories_with_errors']}",
        "",
        "> This is a read-only review aid. A source change is not proof that documentation is incorrect.",
        "",
        "## Summary",
        "",
        f"- Source commits found: **{report['total_commits']}**",
        f"- Potential documentation review candidates: **{report['total_candidate_pages']}**",
        f"- Failed repository checks: **{report['repositories_with_errors']}**",
        "",
    ]
    for item in report["repositories"]:
        lines.extend([f"## `{item['repository']}`", ""])
        if item.get("error"):
            lines.extend([f"**AUDIT INCOMPLETE:** {item['error']}", ""])
            continue
        lines.extend([
            f"- Current default-branch HEAD: `{item.get('head_sha') or 'not returned'}`",
            f"- Commits in audit window: {len(item['commits'])}",
            f"- Documentation sections owned by this repository: {', '.join(f'`{p}`' for p in item['doc_prefixes']) or 'none found'}",
            "",
        ])
        if item["commits"]:
            lines.extend(["### Source changes", ""])
            for commit in item["commits"]:
                label = f"[`{commit['short_sha']}`]({commit['url']})" if commit.get("url") else f"`{commit['short_sha']}`"
                lines.append(f"- {label} — {commit['message']} ({commit['date']})")
                if commit["files"]:
                    for path in commit["files"]:
                        lines.append(f"  - Changed path: `{path}`")
                else:
                    lines.append("  - Changed paths unavailable in the API response.")
                if commit.get("files_truncated"):
                    lines.append("  - **Note:** GitHub may have truncated the file list for this commit.")
            lines.append("")
            lines.extend(["### Documentation review candidates", ""])
            if item["candidate_pages"]:
                lines.extend(f"- `{path}`" for path in item["candidate_pages"])
                lines.append("")
                lines.append("These pages are candidates because their owning repository changed; the current mapping is repository-level, not source-file-level.")
            else:
                lines.append("No existing Markdown pages were found under the mapped documentation prefixes.")
            lines.append("")
        else:
            lines.extend(["No commits were returned for this repository in the audit window.", ""])
    lines.extend([
        "## Interpretation and limitations",
        "",
        "1. **Source changed** means GitHub returned commits in the audit window.",
        "2. **Review candidate** means a documentation section is mapped to that source repository; it does not mean the page is stale.",
        "3. The current `REPOSITORIES` map is broad. File-level source-to-page relationships are not implemented yet.",
        "4. An API failure is reported as an incomplete audit, never as proof that no changes occurred.",
        "5. The audit does not edit files, commit changes, or open pull requests.",
        "",
    ])
    return "\n".join(lines)


def run_audit(args: argparse.Namespace) -> dict[str, Any]:
    repo_root = Path(args.repo_root).resolve()
    token = args.token or os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
    if not token:
        raise AuditError("Set GITHUB_TOKEN (or pass --token) to query commits and previous workflow runs reliably.")
    mapping = load_repository_mapping(repo_root)
    owner = os.environ.get("GITHUB_REPOSITORY", f"{OWNER}/openamrobot-docs").split("/", 1)[0]
    docs_repo = os.environ.get("GITHUB_REPOSITORY", f"{OWNER}/openamrobot-docs").split("/", 1)[-1]
    current_run_id = os.environ.get("GITHUB_RUN_ID")

    if args.since:
        since = parse_time(args.since)
        window_basis = "explicit --since / workflow input"
    else:
        since = previous_successful_run(owner, docs_repo, current_run_id, token)
        if since:
            window_basis = "start time of the previous successful watchdog run"
        else:
            since = utc_now() - timedelta(days=args.initial_days)
            window_basis = f"first-run fallback: previous {args.initial_days} days (no earlier successful watchdog run found)"

    results: list[dict[str, Any]] = []
    for repo, prefixes in mapping.items():
        item: dict[str, Any] = {
            "repository": repo,
            "doc_prefixes": prefixes,
            "candidate_pages": pages_for_prefixes(repo_root, prefixes),
            "commits": [],
            "head_sha": None,
            "error": None,
        }
        try:
            commits = commits_since(repo, since, token)
            item["commits"] = commits
            branch_data, _ = request_json(f"{API_ROOT}/repos/{OWNER}/{repo}", token)
            default_branch = branch_data.get("default_branch") if isinstance(branch_data, dict) else None
            if default_branch:
                ref_data, _ = request_json(f"{API_ROOT}/repos/{OWNER}/{repo}/commits/{default_branch}", token)
                item["head_sha"] = ref_data.get("sha") if isinstance(ref_data, dict) else None
        except AuditError as exc:
            item["error"] = str(exc)
        results.append(item)

    errors = sum(bool(item["error"]) for item in results)
    return {
        "generated_at": isoformat(utc_now()),
        "since": isoformat(since),
        "window_basis": window_basis,
        "repositories_checked": len(results),
        "repositories_with_errors": errors,
        "total_commits": sum(len(item["commits"]) for item in results),
        "total_candidate_pages": len({page for item in results if item["commits"] for page in item["candidate_pages"]}),
        "repositories": results,
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", default=".", help="Documentation repository checkout (default: current directory)")
    parser.add_argument("--output-dir", required=True, help="Directory for Markdown and JSON report outputs")
    parser.add_argument("--since", help="ISO-8601 audit-window start; defaults to previous successful run or first-run fallback")
    parser.add_argument("--initial-days", type=int, default=7, help="First-run fallback window in days (default: 7)")
    parser.add_argument("--token", help="GitHub token; otherwise uses GITHUB_TOKEN or GH_TOKEN")
    args = parser.parse_args(argv)
    if args.initial_days < 1:
        parser.error("--initial-days must be at least 1")
    try:
        report = run_audit(args)
        output = Path(args.output_dir)
        output.mkdir(parents=True, exist_ok=True)
        (output / "documentation-watchdog.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
        (output / "documentation-watchdog.md").write_text(markdown_report(report), encoding="utf-8")
        print(f"Markdown report: {output / 'documentation-watchdog.md'}")
        print(f"JSON report:     {output / 'documentation-watchdog.json'}")
        print(f"Repositories: {report['repositories_checked']}; errors: {report['repositories_with_errors']}; commits: {report['total_commits']}")
        return 1 if report["repositories_with_errors"] else 0
    except AuditError as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
