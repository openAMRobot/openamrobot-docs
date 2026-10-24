#!/usr/bin/env python3
"""Check the generated OpenAMRobot 2.0 roadmap pages in docs/assets/roadmap/.

The pages are generated HTML with embedded data (PARTS, PK, RQ). This check
parses them and fails when:

- an embedded array does not parse or disagrees with the page around it
  (BOM row count, package boxes, traceability rows, action plan size);
- a status count strip (legend buttons with counts) disagrees with the items
  it counts;
- an in-page or cross-page anchor link does not resolve;
- the snapshot dates disagree (with --today: are not today's date);
- a forbidden term appears (em dash, prices, contact details, supplier or
  distributor names, quote numbers, personal first names, links into the
  private audit repository, or a private term from ROADMAP_PRIVATE_TERMS).

Usage: python3 scripts/check_roadmap.py [--dir docs/assets/roadmap] [--today]
"""
import argparse
import datetime as dt
import hashlib
import json
import os
import re
import sys
from html.parser import HTMLParser

PAGES = ["index.html", "robot.html", "hardware.html", "architecture.html", "progress.html"]
STATUS = {"st-mat": "MERGED AND TESTED", "st-mun": "MERGED UNTESTED", "st-rev": "IN REVIEW",
          "st-prog": "IN PROGRESS", "st-doc": "DOCUMENTED ONLY", "st-not": "NOT STARTED", "st-blk": "BLOCKED"}
VOID = {"area", "base", "br", "col", "embed", "hr", "img", "input", "link", "meta", "source", "track", "wbr"}
DATE = r"\d{1,2} (?:Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec) \d{4}"

# Supplier and distributor names (manufacturers may be named; sellers may not).
SELLERS = ["Digi-?Key", "Mouser", "OpenELAB", "Farnell", "element14", "RS Components", "Conrad", "Reichelt",
           "AliExpress", "Amazon", "Arrow Electronics", "TME", "Botland", "Robotshop", "Eckstein", "Berrybase"]
# First names from internal owner columns; people are named by GitHub handle and role only.
NAMES = ["Alex", "Anushka", "Cuma", "Pragati", "Majd", "Kunal", "Mohamed", "Karthikeyan", "Evans", "Satya", "Anand"]
FORBIDDEN = [
    ("em dash", re.compile("—")),
    ("price", re.compile(r"[€$£]\s?\d|\b(?:USD|EUR|GBP|CHF|INR)\s?\d|\b\d[\d,.]*\s?(?:€|USD|EUR|GBP|CHF|INR)\b")),
    ("e-mail address", re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b")),
    ("phone number", re.compile(r"\+\d{2}[\s\d]{8,}")),
    ("quote number", re.compile(r"\b(?:quote|quotation|offer|angebot)\s*(?:no\.?|number|nr\.?|#)\s*:?\s*[A-Z0-9/-]*\d", re.I)),
    ("supplier or distributor name", re.compile(r"\b(?:%s)\b" % "|".join(SELLERS))),
    ("personal first name", re.compile(r"(?<![@/\w-])(?:%s)\b(?![-\w])" % "|".join(NAMES))),
    ("link into the private audit repository", re.compile(r"github\.com/openAMRobot/audits\b", re.I)),
]


class Node:
    __slots__ = ("tag", "attrs", "parent", "kids", "text")

    def __init__(self, tag, attrs, parent):
        self.tag, self.attrs, self.parent, self.kids, self.text = tag, dict(attrs), parent, [], []

    def cls(self):
        return (self.attrs.get("class") or "").split()

    def walk(self):
        yield self
        for k in self.kids:
            yield from k.walk()

    def ancestors(self):
        p = self.parent
        while p is not None:
            yield p
            p = p.parent

    def textall(self):
        return "".join(n_text for n in self.walk() for n_text in n.text)


class Tree(HTMLParser):
    def __init__(self):
        super().__init__(convert_charrefs=True)
        self.root = Node("#root", {}, None)
        self.stack = [self.root]
        self.ids = set()
        self.hrefs = []

    def _new(self, tag, attrs):
        n = Node(tag, attrs, self.stack[-1])
        self.stack[-1].kids.append(n)
        if "id" in n.attrs:
            self.ids.add(n.attrs["id"])
        for k in ("href", "xlink:href"):
            if k in n.attrs and tag == "a":
                self.hrefs.append(n.attrs[k])
        return n

    def handle_starttag(self, tag, attrs):
        n = self._new(tag, attrs)
        if tag not in VOID:
            self.stack.append(n)

    def handle_startendtag(self, tag, attrs):
        self._new(tag, attrs)

    def handle_endtag(self, tag):
        for i in range(len(self.stack) - 1, 0, -1):
            if self.stack[i].tag == tag:
                del self.stack[i:]
                return

    def handle_data(self, data):
        self.stack[-1].text.append(data)


def strip_scripts(html):
    return re.sub(r"<script\b.*?</script>", "", html, flags=re.S)


def embedded(html, name):
    i = html.find("var %s=" % name)
    if i < 0:
        raise ValueError("embedded array %s not found" % name)
    return json.JSONDecoder().raw_decode(html, i + len("var %s=" % name))[0]


def strip_counts(node):
    """{status: count} and the stated total from a cstrip element."""
    got = {}
    for b in node.kids:
        if b.tag == "button" and b.attrs.get("data-hl") in STATUS:
            num = next((k for k in b.walk() if k.tag == "b"), None)
            got[b.attrs["data-hl"]] = int(num.textall().strip())
    total = re.search(r"(\d+) items", node.attrs.get("aria-label", ""))
    return got, int(total.group(1)) if total else None


def strip_scope(node):
    """Items a count strip counts: its figure when it sits in a figcaption, else the following siblings
    up to the next heading or count strip."""
    if any(a.tag == "figcaption" for a in node.ancestors()):
        fig = next(a for a in node.ancestors() if a.tag == "figure")
        return [fig]
    sib = node.parent.kids
    out = []
    for k in sib[sib.index(node) + 1:]:
        heading = k.tag == "h2" or (k.tag == "h3" and not k.attrs.get("id", "").startswith("ph-"))
        if heading or k.tag == "section" or "cstrip" in k.cls():  # plan phase headings (ph-*) stay in scope
            break
        out.append(k)
    return out


def counted(scope_nodes):
    got = {}
    for s in scope_nodes:
        for k in s.walk():
            st = k.attrs.get("data-st")
            if st not in STATUS:
                continue
            c = k.cls()
            if "chip" in c or "lbar" in c or "badge" in c or "carry" in c:
                continue
            anc = list(k.ancestors())
            if any("cstrip" in a.cls() or "legendbar" in a.cls() or "narrow" in a.cls() for a in anc):
                continue
            inner = anc[:anc.index(s)] if s in anc else []
            if any(a.attrs.get("data-st") in STATUS for a in inner):
                continue  # an item inside a counted item (its own chip row, for example)
            got[st] = got.get(st, 0) + 1
    return got


def private_terms():
    raw = os.environ.get("ROADMAP_PRIVATE_TERMS", "")
    return [t.strip() for t in raw.split(",") if t.strip()]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(__file__), "..", "docs", "assets", "roadmap"))
    ap.add_argument("--today", action="store_true", help="require the snapshot date to be today's date")
    args = ap.parse_args()
    errors = []

    def err(page, msg):
        errors.append("%s: %s" % (page, msg))

    html, trees = {}, {}
    for p in PAGES:
        with open(os.path.join(args.dir, p), encoding="utf-8") as f:
            html[p] = f.read()
        tr = Tree()
        tr.feed(strip_scripts(html[p]))
        trees[p] = tr
    # rows rendered from embedded data at load time
    try:
        trees["progress.html"].ids.update("r-" + r["id"] for r in embedded(html["progress.html"], "RQ"))
    except ValueError:
        pass

    # 1. embedded arrays
    try:
        parts = embedded(html["hardware.html"], "PARTS")
        bom = [k for k in parts if re.match(r"^[A-Z]+(?:-[A-Z0-9]+)+$", k)]
        m = re.search(r"BOM Issue [\d.]+ has (\d+) component rows in (\d+) purchase packages", html["hardware.html"])
        if m and int(m.group(1)) != len(bom):
            err("hardware.html", "page states %s BOM rows, PARTS holds %d" % (m.group(1), len(bom)))
        nodes = set(re.findall(r'id="n-([A-Z0-9-]+)"', html["hardware.html"]))
        for n in sorted(nodes - set(parts)):
            err("hardware.html", "diagram node %s has no PARTS entry" % n)
        if m:
            pk_rows = re.findall(r'<tr id="buy-\d+"', html["hardware.html"])
            if len(pk_rows) != int(m.group(2)):
                err("hardware.html", "page states %s purchase packages, table lists %d" % (m.group(2), len(pk_rows)))
    except ValueError as e:
        err("hardware.html", str(e))
    try:
        pk = embedded(html["architecture.html"], "PK")
        boxes = re.findall(r'data-st="(st-[a-z]+)" data-p="([^"]+)"', html["architecture.html"])
        for st, name in boxes:
            if name not in pk:
                err("architecture.html", "package box %s has no PK entry" % name)
            elif pk[name].get("status") != STATUS[st]:
                err("architecture.html", "package %s: box %s, PK %s" % (name, STATUS[st], pk[name].get("status")))
        for name in pk:
            if name not in {n for _, n in boxes}:
                err("architecture.html", "PK entry %s has no package box" % name)
    except ValueError as e:
        err("architecture.html", str(e))
    try:
        rq = embedded(html["progress.html"], "RQ")
        m = re.search(r"<h2>Traceability: (\d+) rows</h2>", html["progress.html"])
        if not m or int(m.group(1)) != len(rq):
            err("progress.html", "traceability heading does not match %d RQ rows" % len(rq))
        ids = [r["id"] for r in rq]
        if len(set(ids)) != len(ids):
            err("progress.html", "duplicate RQ ids")
        stat = {}
        for r in rq:
            stat[r["status"]] = stat.get(r["status"], 0) + 1
        for s, n in stat.items():
            if not re.search(r"%s:\s*%d\b" % (re.escape(s), n), re.sub(r"<[^>]+>", " ", html["progress.html"])):
                err("progress.html", "traceability summary does not show '%s: %d'" % (s, n))
    except ValueError as e:
        err("progress.html", str(e))
    steps = re.findall(r'<li class="step" id="step-(\d+)"', html["progress.html"])
    m = re.search(r"(\d+) steps; (\d+) on the critical path \(steps ([\d, ]+)\)", html["progress.html"])
    if not m or int(m.group(1)) != len(steps):
        err("progress.html", "action plan size does not match %d steps" % len(steps))
    else:
        crit = re.findall(r'<li class="step" id="step-(\d+)" data-st="[^"]+"><div class="sn num">\d+</div><div><p class="sa"><b>(?:(?!</b>).)*</b> <span class="critb">', html["progress.html"])
        if sorted(int(c) for c in crit) != sorted(int(c) for c in m.group(3).split(",")) or len(crit) != int(m.group(2)):
            err("progress.html", "critical-path step list does not match the critical-path markers")

    # 2. status count strips
    for p, tr in trees.items():
        for n in tr.root.walk():
            if n.tag == "div" and "cstrip" in n.cls():
                want, total = strip_counts(n)
                got = counted(strip_scope(n))
                if want != got:
                    err(p, "count strip '%s' shows %s, items are %s" % (n.attrs.get("aria-label"), want, got))
                if total is not None and total != sum(want.values()):
                    err(p, "count strip '%s' total %d, buttons sum to %d" % (n.attrs.get("aria-label"), total, sum(want.values())))

    # 3. anchors
    for p, tr in trees.items():
        for h in tr.hrefs:
            if h.startswith(("http:", "https:", "mailto:", "data:", "javascript:")):
                continue
            target, _, frag = h.partition("#")
            page = target or p
            if page not in trees:
                if target.endswith(".html") and not os.path.exists(os.path.join(args.dir, target)):
                    err(p, "link to missing page %s" % h)
                continue
            if frag and frag not in trees[page].ids:
                err(p, "anchor %s does not resolve" % h)

    # 4. snapshot dates
    dates = {}
    for p in PAGES:
        t = html[p]
        found = re.findall(r'<span class="snap">Snapshot (%s)</span>' % DATE, t)
        found += re.findall(r'<footer class="rm-foot"><p>Snapshot (%s)\.' % DATE, t)
        found += re.findall(r'<p class="src small mute">(?:(?!</p>).)*? · (%s)</p>' % DATE, t, flags=re.S)
        found += re.findall(r"system map, (%s)" % DATE, t)
        found += re.findall(r"<h2>Data refresh, (%s)</h2>" % DATE, t)
        if len(re.findall(r'<span class="snap">', t)) != 1 or len(re.findall(r'<footer class="rm-foot"><p>Snapshot ', t)) != 1:
            err(p, "expected one snapshot label and one footer")
        dates[p] = set(found)
    alld = set().union(*dates.values())
    if len(alld) != 1:
        for p, d in dates.items():
            if d != alld:
                err(p, "snapshot dates %s differ from the other pages %s" % (sorted(d), sorted(alld)))
        if len(alld) > 1:
            errors.append("snapshot dates disagree: %s" % sorted(alld))
    elif args.today:
        today = dt.date.today()
        snap = dt.datetime.strptime(next(iter(alld)), "%d %b %Y").date()
        if snap != today:
            errors.append("snapshot date %s is not today (%s)" % (snap, today))

    # 5. forbidden terms (visible text and attribute values, scripts included for embedded data)
    priv = [(t, re.compile(re.escape(t), re.I)) for t in private_terms()]
    for p in PAGES:
        t = html[p]
        if p == "robot.html":  # three.js bundle and mesh data are not page content
            t = re.sub(r"<script>window\.OPENARM=.*?</script>", "", t, flags=re.S)
            t = re.sub(r"<script>\(\(\)=>\{var Jh=.*?</script>", "", t, flags=re.S)
        t = re.sub(r"url\(data:[^)]*\)", "", t)
        for label, rx in FORBIDDEN + [("private term", r) for _, r in priv]:
            for m in rx.finditer(t):
                ctx = t[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                err(p, "%s: ...%s..." % (label, ctx if label != "private term" else hashlib.sha256(m.group(0).encode()).hexdigest()[:12]))
                break

    if errors:
        print("Roadmap check failed:")
        for e in errors:
            print("  ERROR: " + e)
        sys.exit(1)
    print("Roadmap check passed: %d pages, snapshot %s." % (len(PAGES), next(iter(alld))))


if __name__ == "__main__":
    main()
