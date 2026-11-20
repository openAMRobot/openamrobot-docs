#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Extract the headless quick-start commands of the digital twin page and write them as one script.

A fenced ``bash`` block counts when the line directly before its opening fence is the marker
``<!-- quickstart:headless -->``. Blocks are kept in page order. The written script runs with
``set -eo pipefail``, so the first failing command fails the run. A page with no marked block,
a marker not followed by a bash fence, or an unclosed fence is an error: a quick start that
executes nothing must not pass.

Usage:
  digital_twin_quickstart.py [--page PATH] --list
  digital_twin_quickstart.py [--page PATH] --write OUT.sh
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

MARKER = "<!-- quickstart:headless -->"
DEFAULT_PAGE = Path(__file__).resolve().parent.parent / "docs/reference/openamrobot-2/digital-twin/install-and-run.md"
HEADER = (
    "#!/usr/bin/env bash\n"
    "# Generated from {page} by scripts/digital_twin_quickstart.py. Do not edit: edit the page.\n"
    "set -eo pipefail\n"
)


class QuickstartError(ValueError):
    pass


def extract(text: str) -> list[tuple[int, str]]:
    """Return (line number of the opening fence, block body) for every marked bash block."""
    lines = text.splitlines()
    blocks: list[tuple[int, str]] = []
    i = 0
    while i < len(lines):
        if lines[i].strip() == MARKER:
            if i + 1 >= len(lines) or lines[i + 1].strip() != "```bash":
                raise QuickstartError(f"line {i + 1}: marker not followed by a ```bash fence")
            start = i + 1
            body: list[str] = []
            j = start + 1
            while j < len(lines) and lines[j].strip() != "```":
                body.append(lines[j])
                j += 1
            if j >= len(lines):
                raise QuickstartError(f"line {start + 1}: fence not closed")
            if not any(line.strip() for line in body):
                raise QuickstartError(f"line {start + 1}: empty block")
            blocks.append((start + 1, "\n".join(body)))
            i = j + 1
            continue
        i += 1
    if not blocks:
        raise QuickstartError("no block marked " + MARKER)
    return blocks


def script(page: Path, blocks: list[tuple[int, str]]) -> str:
    parts = [HEADER.format(page=page.name)]
    for n, (line, body) in enumerate(blocks, 1):
        parts.append(f'\necho "=== quick start block {n} of {len(blocks)} (page line {line}) ==="\n{body}\n')
    parts.append(f'\necho "=== quick start: all {len(blocks)} blocks passed ==="\n')
    return "".join(parts)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--page", type=Path, default=DEFAULT_PAGE)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--list", action="store_true", help="print the line and first command of each block")
    group.add_argument("--write", type=Path, help="write the script to this path")
    args = parser.parse_args(argv)
    try:
        blocks = extract(args.page.read_text(encoding="utf-8"))
    except (OSError, QuickstartError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 1
    if args.list:
        for line, body in blocks:
            print(f"line {line}: {body.splitlines()[0]}")
        print(f"{len(blocks)} blocks")
    else:
        args.write.write_text(script(args.page, blocks), encoding="utf-8")
        print(f"wrote {len(blocks)} blocks to {args.write}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
