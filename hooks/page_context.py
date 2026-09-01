"""Generate navigation context and page metadata from the MkDocs tree."""

from __future__ import annotations

from html import escape
from pathlib import Path
import subprocess
from urllib.parse import quote


PATHS = {
    "foundations/": ("Beginner", "Builder"),
    "build/": ("Builder", "Integrator"),
    "use/": ("Domain Expert",),
    "configure/": ("Integrator",),
    "customize/": ("Developer", "Integrator"),
    "maintain/": ("Domain Expert", "Integrator"),
    "reference/": ("Developer", "Integrator"),
    "solutions/": ("Integrator", "Entrepreneur"),
    "business/": ("Entrepreneur",),
    "academy/": ("Domain Expert", "Beginner", "Builder", "Developer"),
}

REPOSITORIES = {
    "build/": "openamr-platform-hw",
    "configure/": "openamr-platform-sw",
    "foundations/": "openamr-platform-sw",
    "maintain/": "openamr-platform-sw",
    "use/": "openamrobot-ui",
    "customize/firmware/": "openamr-platform-fw",
    "customize/hardware/": "openamr-platform-hw",
    "customize/software/": "openamr-platform-sw",
    "customize/integration/": "openamrobot-interfaces",
    "reference/openamr-platform-fw/": "openamr-platform-fw",
    "reference/openamr-platform-hw/": "openamr-platform-hw",
    "reference/openamr-platform-sw/": "openamr-platform-sw",
    "reference/openamrobot-interfaces/": "openamrobot-interfaces",
    "reference/openamrobot-ui/": "openamrobot-ui",
    "reference/openamrobot-manifest/": "openamrobot-manifest",
    "reference/openamrobot-release/": "openamrobot-release",
}

RELATED = {
    "foundations/navigation/slam-and-mapping.md": (
        "use/mapping/creating-a-map.md",
        "maintain/faults/navigation-faults.md",
    ),
    "use/mapping/creating-a-map.md": (
        "foundations/navigation/slam-and-mapping.md",
        "maintain/faults/navigation-faults.md",
    ),
    "maintain/faults/navigation-faults.md": (
        "foundations/navigation/slam-and-mapping.md",
        "use/mapping/creating-a-map.md",
    ),
    "configure/navigation-tuning/costmaps.md": (
        "foundations/navigation/obstacle-avoidance.md",
        "reference/openamr-platform-sw/configuration.md",
    ),
    "customize/device-packages/adding-a-sensor.md": (
        "configure/sensors/adding-a-sensor-config.md",
        "reference/openamrobot-interfaces/overview.md",
    ),
}

_NAV = None


def on_nav(nav, config, files, **kwargs):
    global _NAV
    _NAV = nav
    return nav


def _page_map(nav):
    pages = {}

    def visit(items):
        for item in items:
            if getattr(item, "is_page", False):
                pages[item.file.src_uri] = item
            elif getattr(item, "children", None):
                visit(item.children)

    visit(nav.items)
    return pages


def _paths_for(source):
    if source.startswith("paths/") and source != "paths/index.md":
        return (source.split("/", 1)[1].removesuffix(".md").replace("-", " ").title(),)
    for prefix, labels in PATHS.items():
        if source.startswith(prefix):
            return labels
    return ()


def _repo_for(source):
    for prefix in sorted(REPOSITORIES, key=len, reverse=True):
        if source.startswith(prefix):
            return REPOSITORIES[prefix]
    return None


def _siblings(page):
    if not getattr(page.parent, "is_section", False):
        return None, None
    children = [
        item
        for item in getattr(page.parent, "children", [])
        if getattr(item, "is_page", False) and not item.file.src_uri.endswith("/index.md")
    ]
    if page not in children:
        return None, None
    index = children.index(page)
    return (children[index - 1] if index else None, children[index + 1] if index + 1 < len(children) else None)


def _title(page):
    if page.title:
        return page.title
    return Path(page.file.src_uri).stem.replace("-", " ").title()


def _link(page, label=None):
    return f'<a href="/{escape(page.url)}">{escape(label or _title(page))}</a>'


def _last_updated(source):
    result = subprocess.run(
        ["git", "log", "-1", "--format=%cs", "--", str(Path("docs") / source)],
        check=False,
        capture_output=True,
        text=True,
    )
    return result.stdout.strip()


def on_page_markdown(markdown, page, config, files, **kwargs):
    markdown = markdown.replace(
        "https://avatars.githubusercontent.com/u/175850144?v=4",
        "/assets/openamrobot-logo.jpg",
    )
    source = page.file.src_uri
    for css_class, status in (
        ("oamr-status--stable", "Stable"),
        ("oamr-status--beta", "Beta"),
        ("oamr-status--experimental", "Experimental"),
        ("oamr-status--planned", "Planned"),
    ):
        if css_class in markdown:
            page.meta.setdefault("capability_status", status)
            break
    if source in {"index.md", "404.md"}:
        return markdown

    pages = _page_map(_NAV)
    previous, following = _siblings(page)
    parent = getattr(page, "parent", None)
    if not getattr(parent, "is_section", False):
        parent = None
    parent_page = next((item for item in getattr(parent, "children", []) if getattr(item, "is_page", False)), None)

    crumbs = ['<a href="/">Home</a>']
    if parent_page and parent_page != page:
        crumbs.append(_link(parent_page, parent.title))
    crumbs.append(f'<span aria-current="page">{escape(_title(page))}</span>')

    labels = _paths_for(source)
    path_html = "".join(f"<span>{escape(label)}</span>" for label in labels)
    top = (
        '<nav class="oamr-breadcrumbs" aria-label="Breadcrumb"><ol>'
        + "".join(f"<li>{crumb}</li>" for crumb in crumbs)
        + "</ol></nav>"
        + (f'<div class="oamr-track-labels" aria-label="Recommended paths">{path_html}</div>' if path_html else "")
    )

    related_pages = [pages[path] for path in RELATED.get(source, ()) if path in pages]
    links = []
    if parent_page and parent_page != page:
        links.append(("Parent", _link(parent_page, parent.title)))
    if previous:
        links.append(("Previous", _link(previous)))
    if following:
        links.append(("Next", _link(following)))
    if related_pages:
        links.append(("Related", " · ".join(_link(item) for item in related_pages)))

    repo = _repo_for(source)
    if repo:
        url = f"https://github.com/openAMRobot/{repo}"
        links.append(("Owning repository", f'<a href="{url}">{repo}</a>'))

    issue_title = quote(f"Docs feedback: {_title(page)}")
    issue_body = quote(f"Page: {config.site_url}{page.url}\n\nWhat should be improved?\n")
    feedback = f"https://github.com/openAMRobot/openamrobot-docs/issues/new?title={issue_title}&body={issue_body}"
    updated = _last_updated(source)
    rows = "".join(f"<dt>{escape(label)}</dt><dd>{value}</dd>" for label, value in links)
    bottom = (
        '<aside class="oamr-page-context" aria-label="Page connections">'
        '<h2>Continue and connect</h2><dl>' + rows + "</dl>"
        + (f'<p class="oamr-page-updated">Last updated {escape(updated)}</p>' if updated else "")
        + f'<p class="oamr-page-actions"><a href="{feedback}">Report a documentation problem</a>'
        ' · <a href="mailto:info@botshare.ai">Contact OpenAMRobot</a></p></aside>'
    )
    return f"{top}\n\n{markdown}\n\n{bottom}"


def on_page_context(context, page, config, nav, **kwargs):
    description = page.meta.get("description") or f"Learn about {_title(page)} in the OpenAMRobot documentation hub."
    page.meta["description"] = description
    context["page_description"] = description
    return context
