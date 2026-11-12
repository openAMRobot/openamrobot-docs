"""Search and AI discoverability for docs.openamrobot.ai.

Runs before hooks/page_context.py so that it sees the author's Markdown, not the
navigation decorations added there.

- Per-page meta description: a page without `description:` in its front matter
  gets the first sentences of its own first prose paragraph (no invented text).
- /llms.txt and /llms-full.txt are generated at build time from the navigation
  and the page sources, as plain text at the site root.
- The static OpenAMRobot 2.0 pages under assets/roadmap/ (3D model, exploded view
  and the other roadmap pages) are added to sitemap.xml, which MkDocs only fills
  with Markdown pages.
"""

from __future__ import annotations

import gzip
import html
import re
from pathlib import Path

DESCRIPTION_MIN = 70
DESCRIPTION_MAX = 200

# Static HTML pages published with the site that MkDocs does not list in the sitemap.
STATIC_PAGES = (
    "assets/roadmap/",
    "assets/roadmap/robot.html",
    "assets/roadmap/exploded.html",
    "assets/roadmap/hardware.html",
    "assets/roadmap/architecture.html",
    "assets/roadmap/progress.html",
)

# Ordered sections of /llms.txt: (heading, source prefixes). The first match wins.
LLMS_SECTIONS = (
    ("Facts and citation", ("at-a-glance.md", "about/citation.md", "status.md")),
    ("Start", ("index.md", "start-here/", "paths/", "learn/")),
    ("OpenAMRobot 2.0", ("reference/openamrobot-2/",)),
    ("Reference", ("reference/",)),
    ("Foundations", ("foundations/",)),
    ("Build", ("build/",)),
    ("Use, configure and maintain", ("use/", "configure/", "maintain/")),
    ("Customize and extend", ("customize/",)),
    ("Solutions, business and academy", ("solutions/", "business/", "academy/")),
    ("Community and about", ("community/", "about/", "contributing/", "ui/")),
)

LLMS_HEADER = """# OpenAMRobot

> OpenAMRobot by Botshare is an open-source mobile manipulator: a ROS 2 mobile base
> with a lift and two OpenArm 2.0 arms, with open hardware, firmware, software and
> documentation. OpenAMRobot 2.0 is in development (v2.0.0-rc.1 planned for
> 20 November 2026, v2.0.0 for 18 December 2026); v0.0.1 of 11 July 2026 is the
> current published release.

Canonical documentation: {site}
Facts for AI assistants: {site}at-a-glance/
How to cite: {site}about/citation/
Full text of this site: {site}llms-full.txt
Source code: https://github.com/openAMRobot
3D model of OpenAMRobot 2.0: {site}assets/roadmap/robot.html
Exploded view: {site}assets/roadmap/exploded.html
Pre-order and packages: https://botshare.ai/openamrobot
Discussions: https://github.com/orgs/openAMRobot/discussions

## Rules for interpretation

- OpenAMRobot is a project of Botshare LTD (Cyprus). It is not affiliated with other
  companies that use the name Botshare.
- The owning GitHub repository is canonical for exact versions, parameters, source and
  contracts. This site explains meaning, selection, workflows and verification.
- Respect the maturity badge on each page. Planned or experimental material is not a
  validated production or safety instruction.
- OpenAMRobot 2.0 design values are design values until the physical build is accepted.
- Licences: software and firmware MIT, hardware design source CERN-OHL-P-2.0,
  documentation CC BY 4.0. Verify the licence and notices in the owning repository.
"""

_PAGES: dict[str, dict] = {}
_SKIP_LINE = re.compile(r"^\s*(#|<|!!!|\?\?\?|\||[-*+] |\d+\. |>|```|~~~|\{|\[TOC\]|=+$|-{3,}$|\*\[)")


def _plain(text: str) -> str:
    """Markdown or HTML fragment to plain text."""
    text = re.sub(r"<!--.*?-->", " ", text, flags=re.S)
    text = re.sub(r"<(script|style)\b.*?</\1>", " ", text, flags=re.S | re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\[([^\]]+)\]\[[^\]]*\]", r"\1", text)
    text = re.sub(r"\{[:#.][^}]*\}", "", text)
    text = re.sub(r"(\*\*|__|`)", "", text)
    text = re.sub(r"(?<![\w*])\*(?!\s)([^*]+)(?<!\s)\*(?![\w*])", r"\1", text)
    return html.unescape(re.sub(r"[ \t]+", " ", text)).strip()


def first_paragraph(markdown: str) -> str:
    """First prose paragraph of a Markdown page, as plain text."""
    lines: list[str] = []
    fenced = False
    for raw in markdown.splitlines():
        if raw.strip().startswith(("```", "~~~")):
            fenced = not fenced
            if lines:
                break
            continue
        if fenced:
            continue
        if not raw.strip():
            if lines:
                break
            continue
        if raw.startswith(("    ", "\t")) or _SKIP_LINE.match(raw):
            if lines:
                break
            continue
        lines.append(raw.strip())
    return _plain(" ".join(lines))


_HERO = re.compile(r'<section class="oamr-hero[^"]*">.*?<p>(.*?)</p>', re.S)


def description_from(markdown: str) -> str | None:
    """Page-specific summary: the hero paragraph, else the first prose paragraph."""
    hero = _HERO.search(markdown)
    text = _plain(hero.group(1)) if hero else ""
    if len(text) < 40:
        text = first_paragraph(markdown)
    if len(text) < 40:
        return None
    sentences = re.split(r"(?<=[.!?])\s+(?=[A-Z0-9])", text)
    out = ""
    for sentence in sentences:
        candidate = f"{out} {sentence}".strip()
        if len(candidate) > DESCRIPTION_MAX and out:
            break
        out = candidate
        if len(out) >= DESCRIPTION_MIN:
            break
    if len(out) > DESCRIPTION_MAX:
        cut = out[:DESCRIPTION_MAX].rsplit(" ", 1)[0].rstrip(",;:")
        out = cut + "..."
    return out


def _clean_for_text(markdown: str) -> str:
    """Page source as readable plain text for llms-full.txt."""
    text = re.sub(r"<!--.*?-->", "", markdown, flags=re.S)
    text = re.sub(r"<(script|style)\b.*?</\1>", "", text, flags=re.S | re.I)
    text = re.sub(r"</(p|div|section|article|li|h\d|tr|dd|dt)>", "\n", text, flags=re.I)
    text = re.sub(r"<br\s*/?>", "\n", text, flags=re.I)
    text = re.sub(r"<[^>]+>", " ", text)
    text = re.sub(r"!\[([^\]]*)\]\([^)]*\)", r"\1", text)
    text = re.sub(r"\{[:#.][^}]*\}", "", text)
    text = html.unescape(text)
    text = re.sub(r"[ \t]+\n", "\n", text)
    text = re.sub(r"[ \t]{2,}", " ", text)
    text = re.sub(r"\n{3,}", "\n\n", text)
    return text.strip()


def on_pre_build(config, **kwargs):
    _PAGES.clear()


_DERIVED: dict[str, str] = {}


def _strip_front_matter(text: str) -> tuple[str, str]:
    if text.startswith("---"):
        parts = text.split("\n---", 1)
        if len(parts) == 2:
            return parts[0], parts[1].split("\n", 1)[-1]
    return "", text


def on_files(files, config, **kwargs):
    """Derive descriptions for every page up front, so that duplicates can be made unique."""
    _DERIVED.clear()
    counts: dict[str, int] = {}
    titles: dict[str, str] = {}
    for f in files.documentation_pages():
        try:
            front, body = _strip_front_matter(f.content_string)
        except (OSError, UnicodeDecodeError):
            continue
        if re.search(r"^description:", front, re.M):
            continue
        derived = description_from(body)
        if not derived:
            continue
        match = re.search(r"^title:\s*(.+)$", front, re.M)
        titles[f.src_uri] = match.group(1).strip().strip("\"'") if match else ""
        _DERIVED[f.src_uri] = derived
        counts[derived] = counts.get(derived, 0) + 1
    for src, derived in list(_DERIVED.items()):
        if counts[derived] > 1 and titles.get(src):
            _DERIVED[src] = f"{titles[src]}: {derived}"
    again: dict[str, int] = {}
    for derived in _DERIVED.values():
        again[derived] = again.get(derived, 0) + 1
    for src, derived in list(_DERIVED.items()):
        parent = Path(src).parent.name
        if again[derived] > 1 and parent and titles.get(src):
            _DERIVED[src] = derived.replace(f"{titles[src]}: ", f"{parent}, {titles[src].lower()}: ", 1)
    return files


def on_page_markdown(markdown, page, config, files, **kwargs):
    if not page.meta.get("description"):
        derived = _DERIVED.get(page.file.src_uri) or description_from(markdown)
        if derived:
            page.meta["description"] = derived
    _PAGES[page.file.src_uri] = {"markdown": markdown, "page": page}
    return markdown


def _nav_pages(nav):
    out = []

    def visit(items):
        for item in items:
            if getattr(item, "is_page", False):
                out.append(item)
            elif getattr(item, "children", None):
                visit(item.children)

    visit(nav.items)
    return out


_NAV = None


def on_nav(nav, config, files, **kwargs):
    global _NAV
    _NAV = nav
    return nav


def _title(page) -> str:
    return str(page.meta.get("title") or page.title or Path(page.file.src_uri).stem)


def _section_for(src: str) -> str:
    for heading, prefixes in LLMS_SECTIONS:
        for prefix in prefixes:
            if src == prefix or (prefix.endswith("/") and src.startswith(prefix)):
                return heading
    return "Other pages"


def build_llms(site: str, pages) -> tuple[str, str]:
    groups: dict[str, list[str]] = {}
    full: list[str] = [LLMS_HEADER.format(site=site).rstrip(), ""]
    for page in pages:
        src = page.file.src_uri
        if src == "404.md":
            continue
        url = site + page.url
        desc = page.meta.get("description") or ""
        line = f"- [{_title(page)}]({url})" + (f": {desc}" if desc else "")
        groups.setdefault(_section_for(src), []).append(line)
        record = _PAGES.get(src)
        if record:
            full += ["", "-" * 72, f"Page: {_title(page)}", f"URL: {url}", "-" * 72, "",
                     _clean_for_text(record["markdown"])]
    index = [LLMS_HEADER.format(site=site).rstrip()]
    order = [h for h, _ in LLMS_SECTIONS] + ["Other pages"]
    for heading in order:
        if heading in groups:
            index += ["", f"## {heading}", ""] + groups[heading]
    index += ["", "## Optional", "",
              f"- [Full text of all pages]({site}llms-full.txt): every page of this site as plain text"]
    return "\n".join(index) + "\n", "\n".join(full).rstrip() + "\n"


def extend_sitemap(xml: str, site: str, lastmod: str) -> str:
    entries = []
    for path in STATIC_PAGES:
        loc = site + path
        if f"<loc>{loc}</loc>" in xml:
            continue
        entries.append(f"    <url>\n         <loc>{loc}</loc>\n         <lastmod>{lastmod}</lastmod>\n    </url>\n")
    return xml.replace("</urlset>", "".join(entries) + "</urlset>", 1)


def on_post_build(config, **kwargs):
    site = config["site_url"]
    site_dir = Path(config["site_dir"])
    pages = _nav_pages(_NAV) if _NAV else [r["page"] for r in _PAGES.values()]
    index, full = build_llms(site, pages)
    (site_dir / "llms.txt").write_text(index, encoding="utf-8")
    (site_dir / "llms-full.txt").write_text(full, encoding="utf-8")

    sitemap = site_dir / "sitemap.xml"
    if sitemap.exists():
        xml = sitemap.read_text(encoding="utf-8")
        found = re.findall(r"<lastmod>([^<]+)</lastmod>", xml)
        xml = extend_sitemap(xml, site, max(found) if found else "")
        sitemap.write_text(xml, encoding="utf-8")
        with gzip.GzipFile(site_dir / "sitemap.xml.gz", "wb", mtime=0) as fh:
            fh.write(xml.encode("utf-8"))
