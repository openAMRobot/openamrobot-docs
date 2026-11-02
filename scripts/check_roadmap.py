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
  private audit repository, or a private term from ROADMAP_PRIVATE_TERMS);
- the top navigation of a page does not list the six pages in order;
- the shared model (model/model.js, model/base_glb.js, model/exploded.json)
  is inconsistent: an exploded.json id that model.js does not define, an
  invalid stage, a component without a source or with a non-public link, a
  GLB node without id, class or source, or a page over its size budget;
- robot.html or exploded.html carry a second three.js (an inline copy of the
  three.js core, or a three.js script other than model/three-r160.min.js and,
  on robot.html only, the store addons model/three-r160-store.min.js), robot
  geometry or robot materials of their own (anything but one call of
  OAMR_MODEL.build), or a renderer look other than model/look.js (calibration,
  light-look fallback and its frame probe included), or robot.html does not
  start with the Follow preset, Frames and Labels off and High quality on, or
  tints one arm, or model/model.js draws a light strip (an led material or a
  cyan emissive colour) on the robot, or the robot page store video, pictures,
  thumbnails or contact sheet are missing, over their size limits, not
  labelled as simulation visualization, or push its first load over budget; or
  model/finish.json names an unknown material class or part;
- the exploded view lacks a control (explode robot, open the base, cutaway,
  tour, pause, stop, record), its opened-base offsets, labels, view settings
  or tour keyframes name unknown ids, the tour is not 40 to 50 s, or a tour
  video or poster is missing, over 15 MB, or loads before it is played.

Usage: python3 scripts/check_roadmap.py [--dir docs/assets/roadmap] [--today]
"""
import argparse
import base64
import csv
import datetime as dt
import hashlib
import json
import os
import re
import struct
import sys
from html.parser import HTMLParser

PAGES = ["index.html", "robot.html", "exploded.html", "hardware.html", "architecture.html", "progress.html"]
NAV = [("index.html", "Overview"), ("robot.html", "Robot"), ("exploded.html", "Exploded view"), ("hardware.html", "Hardware"),
       ("architecture.html", "Architecture"), ("progress.html", "Progress")]
STAGES_NOTE = "Subsystem grouping for orientation. Not an assembly instruction; the 2.0 assembly guide is in preparation."
GEOMETRY = {"cad", "envelope", "primitive", "none"}
GLB_CLASSES = {"chassis", "component", "envelope"}
PUBLIC_LINK = re.compile(r"^https://github\.com/openAMRobot/(?:openamr-platform-hw|openamr-platform-sw|openamr-upperbody-hw)/(?:blob|tree)/main/\S+$")
EXPLODED_MAX_BYTES = 350 * 1024
EXPLODED_CONTROLS = ["b-asm", "b-explode", "b-open", "b-cut", "b-reset", "b-nums", "b-hq", "b-tour", "b-pause", "b-stop", "b-rec"]
MEDIA = ["media/openamrobot-2-tour-1080p.mp4", "media/openamrobot-2-tour-1080x1350.mp4"]
MEDIA_MAX_BYTES = 15 * 1024 * 1024
# robot.html: offline-rendered store video and pictures (simulation visualization)
STORE_VIDEO = "media/openamrobot-2-store-1080p.mp4"
STORE_POSTER = "media/openamrobot-2-store-1080p-poster.png"
STORE_PICTURES = [("01_aisle_follow", (1920, 1080)), ("02_pick_side", (1920, 1080)), ("03_place_tote", (1920, 1080)),
                  ("04_front_low", (1920, 1080)), ("05_store_overview", (1920, 1080)), ("06_dock", (1920, 1080)),
                  ("02_pick_side_1080x1350", (1080, 1350)), ("04_front_low_1080x1350", (1080, 1350))]
STORE_SHEET = "media/store/contact_sheet.jpg"
PICTURE_MAX_BYTES = 1000 * 1000
THUMB_MAX_BYTES = 120 * 1000
# payload budget of the 2 Nov 2026 update: default view at most 15 MB, High quality at most 40 MB
ROBOT_FIRST_LOAD_MAX_BYTES = 15 * 1000 * 1000  # page, scripts, finish.json, placement.json
TOUR_SECONDS = (40.0, 50.0)
EXPLODED_FIRST_LOAD_MAX_BYTES = 15 * 1000 * 1000  # page, scripts, exploded.json, placement.json and video posters; not the videos
ROBOT_MAX_BYTES = 600 * 1024  # robot.html without a bundled three.js
THREE_CORE = "model/three-r160.min.js"
THREE_ADDONS = {"robot.html": ["model/three-r160-store.min.js"], "exploded.html": []}
# three.js core text: none of it may appear in a page's inline scripts or in the addon file
THREE_CORE_MARKS = ["__THREE__", "isWebGLRenderer", "THREE.WebGLRenderer:"]
# robot construction outside model/model.js: model internals called from a page, or code that only the
# robot builder has (OpenArm link meshes, robot page fittings, the robot materials)
ROBOT_MARKS = [r"\b(?:OAMR_)?MODEL\.(?:base|upperBody|armGeometries|armRig|arm|materials|classMaterial|texture)\(", r"\bBASE_GLB\b",
               r"OPENARM\.meshes", r"HEXALIFT V4", r'fillText\("AMRobot"', r"makeScale\(\w+\.scale\[0\]",
               r"vertexColors:\s*(?:!0|true)", r"emissive:\s*(?:732282|2776023)\b", r"\b(?:13225426|10133671|14146270|329224)\b"]
# renderer look outside model/look.js
LOOK_MARKS = [r"\.toneMapping\s*=", r"\.toneMappingExposure\s*=", r"\.outputColorSpace\s*=", r"\.shadowMap\.type\s*=",
              r"\bRoomEnvironment\b", r"\bPMREMGenerator\b"]
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


PLACEMENT = None  # model/placement.json (generated by scripts/roadmap_model/build.py), loaded by main()


def model_components(js):
    """COMPONENTS registry of model/model.js (the JSON between its markers) plus the components of
    model/placement.json, which model.js appends at load."""
    m = re.search(r"/\*COMPONENTS-JSON\*/(.*?)/\*COMPONENTS-JSON-END\*/", js, flags=re.S)
    if not m:
        raise ValueError("model.js has no COMPONENTS-JSON block")
    comps = json.loads(m.group(1))
    if PLACEMENT and "M.PLACE.components" in js:
        comps = comps + PLACEMENT.get("components", [])
    return comps


def glb_nodes(payload, prims=False):
    """Nodes of the base GLB in model/base_glb.js (base64 with a '.' every 16 characters); with prims,
    each node carries _prims, the primitive count of its mesh."""
    m = re.search(r'window\.BASE_GLB="([^"]+)"', payload)
    if not m:
        raise ValueError("base_glb.js does not set window.BASE_GLB")
    raw = base64.b64decode(m.group(1).replace(".", ""))
    if raw[:4] != b"glTF":
        raise ValueError("BASE_GLB is not a binary glTF")
    n = struct.unpack("<I", raw[12:16])[0]
    doc = json.loads(raw[20:20 + n])
    nodes = [x for x in doc["nodes"] if "mesh" in x]
    if prims:
        for x in nodes:
            x["_prims"] = len(doc["meshes"][x["mesh"]]["primitives"])
    return nodes


def check_model(root, html, err):
    """Shared model: registry, GLB nodes, exploded offsets and stages, sizes."""
    mdir = os.path.join(root, "model")
    try:
        with open(os.path.join(mdir, "model.js"), encoding="utf-8") as f:
            js = f.read()
        comps = model_components(js)
        with open(os.path.join(mdir, "base_glb.js"), encoding="utf-8") as f:
            nodes = glb_nodes(f.read())
        with open(os.path.join(mdir, "exploded.json"), encoding="utf-8") as f:
            ex = json.load(f)
    except (OSError, ValueError, KeyError) as e:
        err("model", str(e))
        return
    ids = [c.get("id") for c in comps]
    if len(set(ids)) != len(ids):
        err("model.js", "duplicate component ids")
    glb = {}
    for n in nodes:
        x = n.get("extras") or {}
        for k in ("id", "class", "source"):
            if not str(x.get(k, "")).strip():
                err("base_glb.js", "GLB node %s has no %s" % (n.get("name"), k))
        if x.get("class") not in GLB_CLASSES:
            err("base_glb.js", "GLB node %s has class %s" % (n.get("name"), x.get("class")))
        glb[x.get("id")] = x
    used = set()
    for c in comps:
        cid = c.get("id")
        for k in ("name", "purpose", "source", "link"):
            if not str(c.get(k, "")).strip():
                err("model.js", "component %s has no %s" % (cid, k))
        if c.get("geometry") not in GEOMETRY:
            err("model.js", "component %s has geometry %s" % (cid, c.get("geometry")))
        if not PUBLIC_LINK.match(c.get("link", "")):
            err("model.js", "component %s links %s, not a public openAMRobot GitHub file" % (cid, c.get("link")))
        if c.get("provisional") and c.get("geometry") != "envelope":
            err("model.js", "component %s is provisional but not an envelope" % cid)
        for nid in c.get("nodes", []):
            used.add(nid)
            if nid not in glb:
                err("model.js", "component %s names GLB node %s, which base_glb.js does not have" % (cid, nid))
            elif bool(glb[nid].get("provisional")) != bool(c.get("provisional")):
                err("model.js", "component %s and GLB node %s disagree on provisional" % (cid, nid))
            elif bool(glb[nid].get("placeholder")) != bool(c.get("placeholder")):
                err("model.js", "component %s and GLB node %s disagree on placeholder" % (cid, nid))
        for pid in c.get("parts", []):
            if PLACEMENT and pid in PLACEMENT.get("geometry", {}):
                continue
            if "'%s'" % pid not in js and not (pid.startswith("openarm_") and "'openarm_' + side" in js):
                err("model.js", "component %s names part %s, which model.js does not build" % (cid, pid))
        if c.get("geometry") == "none" and (c.get("nodes") or c.get("parts")):
            err("model.js", "component %s is not drawn but names geometry" % cid)
        if c.get("geometry") != "none" and not (c.get("nodes") or c.get("parts")):
            err("model.js", "component %s is drawn but names no geometry" % cid)
    for nid in sorted(set(glb) - used):
        err("model.js", "GLB node %s belongs to no component" % nid)
    stages = ex.get("stages", [])
    if [s.get("n") for s in stages] != list(range(1, len(stages) + 1)) or not stages:
        err("exploded.json", "stages must be numbered 1 to n")
    if ex.get("stages_note") != STAGES_NOTE or STAGES_NOTE not in html:
        err("exploded.json", "the stages note must read: " + STAGES_NOTE)
    byid = {c.get("id"): c for c in comps}
    for cid, e in ex.get("components", {}).items():
        if cid not in byid:
            err("exploded.json", "component %s is not defined in model.js" % cid)
            continue
        if e.get("stage") not in range(1, len(stages) + 1):
            err("exploded.json", "component %s has invalid stage %s" % (cid, e.get("stage")))
        geo = set(byid[cid].get("nodes", []) + byid[cid].get("parts", []))
        for pid, off in e.get("offsets", {}).items():
            if pid not in geo:
                err("exploded.json", "offset %s is not a node or part of %s" % (pid, cid))
            if not (isinstance(off, list) and len(off) == 3 and all(isinstance(v, (int, float)) for v in off)):
                err("exploded.json", "offset %s of %s is not [x, y, z]" % (pid, cid))
        if byid[cid].get("geometry") != "none" and set(e.get("offsets", {})) != geo:
            err("exploded.json", "component %s: offsets must cover exactly its nodes or parts" % cid)
        for pid, off in e.get("open", {}).items():
            if pid not in geo:
                err("exploded.json", "open offset %s is not a node or part of %s" % (pid, cid))
            if not (isinstance(off, list) and len(off) == 3 and all(isinstance(v, (int, float)) for v in off)):
                err("exploded.json", "open offset %s of %s is not [x, y, z]" % (pid, cid))
    for cid in byid:
        if cid not in ex.get("components", {}):
            err("exploded.json", "component %s has no entry (stage and offsets)" % cid)
    check_views(root, html, ex, byid, glb, err)
    with open(os.path.join(mdir, "base_glb.js"), encoding="utf-8") as f:
        prims = {(n.get("extras") or {}).get("id"): n.get("_prims", 0) for n in glb_nodes(f.read(), prims=True)}
    check_finish(root, err, comps, prims)
    # budgets: the page itself, and its first load (page, local scripts, exploded.json; videos load on demand)
    size = len(html.encode("utf-8"))
    if size > EXPLODED_MAX_BYTES:
        err("exploded.html", "%d bytes, over %d" % (size, EXPLODED_MAX_BYTES))
    first = size + os.path.getsize(os.path.join(mdir, "exploded.json")) + os.path.getsize(os.path.join(mdir, "placement.json"))
    for src in re.findall(r'<script src="([^"]+)"', html) + re.findall(r'<video\b[^>]*\bposter="([^"]+)"', html):
        first += os.path.getsize(os.path.join(root, src))
    if first > EXPLODED_FIRST_LOAD_MAX_BYTES:
        err("exploded.html", "first load %d bytes, over %d" % (first, EXPLODED_FIRST_LOAD_MAX_BYTES))


def check_views(root, html, ex, byid, glb, err):
    """Opened base, cutaway, labels, the guided tour and its videos."""
    allg = set(glb)
    for c in byid.values():
        allg.update(c.get("parts", []))
    for cid, name in ex.get("labels", {}).items():
        if cid not in byid or not str(name).strip():
            err("exploded.json", "label %s names no component" % cid)
    views = ex.get("views", {})
    for v in ("open_base", "cutaway"):
        if v not in views:
            err("exploded.json", "views.%s is missing" % v)
        for pid, op in views.get(v, {}).get("opacity", {}).items():
            if pid not in allg or not (isinstance(op, (int, float)) and 0 <= op <= 1):
                err("exploded.json", "views.%s opacity %s: unknown part or not 0 to 1" % (v, pid))
    for cid in views.get("open_base", {}).get("frame", []):
        if cid not in byid:
            err("exploded.json", "views.open_base frame names unknown component %s" % cid)
    for st in ex.get("stages", []):
        fr = st.get("frame", "base")
        if fr not in ("base", "robot") and not (isinstance(fr, list) and all(c in byid for c in fr)):
            err("exploded.json", "stage %s frames %s" % (st.get("n"), fr))
    tour = ex.get("tour") or {}
    keys = tour.get("keys", [])
    if tour.get("fps") != 30 or len(keys) < 2:
        err("exploded.json", "tour needs fps 30 and at least two keyframes")
    else:
        ts = [k.get("t") for k in keys]
        if ts[0] != 0 or any(b <= a for a, b in zip(ts, ts[1:])):
            err("exploded.json", "tour keyframe times must start at 0 and increase")
        if not TOUR_SECONDS[0] <= ts[-1] <= TOUR_SECONDS[1]:
            err("exploded.json", "tour lasts %s s, not %s to %s s" % (ts[-1], TOUR_SECONDS[0], TOUR_SECONDS[1]))
        if not keys[0].get("caption"):
            err("exploded.json", "the first tour keyframe has no caption")
        for k in keys:
            fr = k.get("frame", "robot")
            ids = ([] if fr in ("robot", "base") else fr if isinstance(fr, list) else [fr]) + k.get("labels", []) + k.get("focus", [])
            for cid in ids:
                if cid not in byid:
                    err("exploded.json", "tour keyframe at %s s names unknown component %s" % (k.get("t"), cid))
            for w in ("r", "b", "c"):
                if not 0 <= k.get(w, 0) <= 1:
                    err("exploded.json", "tour keyframe at %s s: %s outside 0 to 1" % (k.get("t"), w))
    for cid in EXPLODED_CONTROLS:
        if not re.search(r'<button id="%s"' % cid, html):
            err("exploded.html", "control %s is missing" % cid)
    for path in MEDIA:
        full = os.path.join(root, path)
        poster = full[:-4] + "-poster.png"
        if not os.path.isfile(full):
            err("exploded.html", "tour video %s is missing" % path)
            continue
        if os.path.getsize(full) > MEDIA_MAX_BYTES:
            err("exploded.html", "%s is %d bytes, over %d" % (path, os.path.getsize(full), MEDIA_MAX_BYTES))
        if not os.path.isfile(poster):
            err("exploded.html", "poster %s is missing" % os.path.relpath(poster, root))
        if 'href="%s"' % path not in html:
            err("exploded.html", "no download link to %s" % path)
    for v in re.findall(r"<video\b[^>]*>", html):
        if 'preload="none"' not in v:
            err("exploded.html", "a video loads before it is played (preload must be none)")
    if 'src="%s"' % MEDIA[0] not in html:
        err("exploded.html", "the 16:9 tour video is not shown on the page")


def check_shared(root, html, err):
    """robot.html and exploded.html: one three.js, the robot only from model/model.js, the look from model/look.js."""
    for p in ("robot.html", "exploded.html"):
        h = html[p]
        srcs = re.findall(r'<script src="([^"]+)"', h)
        threes = [x for x in srcs if "three" in os.path.basename(x).lower()]
        if threes != [THREE_CORE] + THREE_ADDONS[p]:
            err(p, "three.js scripts %s, expected %s" % (threes, [THREE_CORE] + THREE_ADDONS[p]))
        for need in ("model/model.js", "model/look.js"):
            if srcs.count(need) != 1:
                err(p, "must load %s once" % need)
        inline = "".join(re.findall(r"<script(?![^>]*\bsrc=)[^>]*>(.*?)</script>", h, flags=re.S))
        for mark in THREE_CORE_MARKS:
            if mark in inline:
                err(p, "an inline script carries three.js core code (%s); use %s" % (mark, THREE_CORE))
        if len(re.findall(r"OAMR_MODEL\.build\(|\bMODEL\.build\(", inline)) != 1:
            err(p, "must build the robot with exactly one call of OAMR_MODEL.build")
        for rx in ROBOT_MARKS:
            m = re.search(rx, inline)
            if m:
                err(p, "robot geometry or materials defined in the page (%s); they belong in model/model.js" % m.group(0))
        for rx in LOOK_MARKS:
            m = re.search(rx, inline)
            if m:
                err(p, "renderer look set in the page (%s); it belongs in model/look.js" % m.group(0))
        if not re.search(r"(?:OAMR_)?LOOK\.apply\(", inline) or not re.search(r"(?:OAMR_)?LOOK\.environment\(", inline):
            err(p, "must take tone mapping, colour output, shadows and environment from model/look.js")
        for call in ("CAL", "robotEnv(", "lightLook(", "startProbe(", "forced("):
            if call not in inline:
                err(p, "must use the calibrated look and the light-look fallback of model/look.js (%s)" % call.rstrip("("))
    # robot.html page defaults: view preset Follow, Frames and Labels off, High quality on; one arm material
    h = html["robot.html"]
    for what, rx in [("view preset Follow selected", r'<button data-view="follow" class="on">'),
                     ("view preset Follow at start", r'view:"follow",'), ("Follow applied at start", r'P2\("follow"\)'),
                     ("Frames off", r'<button id="b-frames" aria-pressed="false">'), ("Frames off at start", r'\bvar fs=!1;'),
                     ("Labels off", r'<button id="b-labels" aria-pressed="false">'), ("Labels off at start", r'\bvr=!1,'),
                     ("High quality on", r'<button id="b-q" class="on">'), ("High quality on at start", r'\bhq:!Mr,')]:
        if not re.search(rx, h):
            err("robot.html", "page default not as required: %s" % what)
    if len(re.findall(r'<button data-view="[a-z]+" class="on">', h)) != 1:
        err("robot.html", "exactly one view preset must be selected")
    if re.search(r"armHi|=e===s\?\w+:kc", h):
        err("robot.html", "the arms must share the as-delivered arm material (no working-arm tint)")
    for f in [THREE_CORE] + THREE_ADDONS["robot.html"]:
        if not os.path.isfile(os.path.join(root, f)):
            err("model", "%s is missing" % f)
    try:
        with open(os.path.join(root, THREE_ADDONS["robot.html"][0]), encoding="utf-8") as f:
            addons = f.read()
        for mark in THREE_CORE_MARKS:
            if mark in addons:
                err(THREE_ADDONS["robot.html"][0], "carries three.js core code (%s)" % mark)
    except OSError:
        pass
    size = len(html["robot.html"].encode("utf-8"))
    if size > ROBOT_MAX_BYTES:
        err("robot.html", "%d bytes, over %d" % (size, ROBOT_MAX_BYTES))


def emissive_cyan(v):
    """True for an emissive colour (integer, 0x hex or #hex) that reads cyan: green and blue well above red."""
    v = v.strip().lower()
    n = int(v, 16) if v.startswith(("0x", "#")) and len(v.lstrip("#0x")) else int(v) if v.isdigit() else None
    if n is None:
        return False
    r, g, b = n >> 16 & 255, n >> 8 & 255, n & 255
    return g > 90 and b > 90 and min(g, b) > r + 50


def check_no_light_strips(root, err):
    """The robot carries no status light strips: model/model.js (the only robot builder) may not define an
    led material or any material with a cyan emissive colour."""
    try:
        with open(os.path.join(root, "model", "model.js"), encoding="utf-8") as f:
            js = f.read()
    except OSError:
        return
    if re.search(r"\bmats\.led\b|\bled\s*:\s*new\b", js):
        err("model.js", "an led material is defined or used on the robot; the robot has no light strips")
    for m in re.finditer(r"emissive\s*:\s*(0x[0-9a-fA-F]+|#[0-9a-fA-F]{6}|\d+)", js):
        if emissive_cyan(m.group(1)):
            err("model.js", "cyan emissive colour %s on the robot; the robot has no light strips" % m.group(1))


def function_body(src, start):
    """Text of the brace block that opens at the first '{' after index start."""
    i = src.index("{", start)
    depth = 0
    for j in range(i, len(src)):
        depth += {"{": 1, "}": -1}.get(src[j], 0)
        if depth == 0:
            return src[i:j + 1]
    return src[i:]


def check_no_duplicate_fittings(root, html, err):
    """The base E-stop and RESET come from the GLB only (nodes estop and reset_button): the robot page fittings
    (model/model.js chassisFittings) draw neither again, and robot.html buildTotes draws no tote rails on the
    cover (not in the BOM or the CAD); the totes are their own groups."""
    try:
        with open(os.path.join(root, "model", "model.js"), encoding="utf-8") as f:
            js = f.read()
    except OSError:
        return
    m = re.search(r"function chassisFittings\s*\(", js)
    if not m:
        err("model.js", "chassisFittings not found")
    else:
        body = function_body(js, m.end())
        for mat in ("red", "yellow", "resetLit"):
            if re.search(r"\bmats\.%s\b" % mat, body):
                err("model.js", "chassisFittings draws a base E-stop or RESET (mats.%s); they come from the GLB" % mat)
    if re.search(r"\bresetLit\b", js):
        err("model.js", "resetLit material defined; the RESET button comes from the GLB")
    m = re.search(r"\bbuildTotes\(\)\s*\{", html["robot.html"])
    if not m:
        err("robot.html", "buildTotes not found")
    else:
        body = function_body(html["robot.html"], m.start())
        if re.search(r"\(this\.g,", body) or "aluDark" in body:
            err("robot.html", "buildTotes adds geometry outside the totes (tote rails on the cover); not in the BOM or the CAD")


# Owner corrections of 2 Nov 2026 (Alex; to be entered in P-03 and M-01): the second E-stop (formerly the chest E-stop)
# on top of the adapter plate behind the post, button up (A5); the moving chest bottom up: head light, then the Getac,
# the head light top edge 10 mm below the Getac bottom edge (A3).
CHEST_ORDER = ["head_light", "getac_tablet"]
CHEST_IDS = ["second_estop"] + CHEST_ORDER
LIGHT_TABLET_GAP = 0.01
# A3 (2 Nov 2026): Getac ZX80 portrait is the decided default (x depth 17.6, y across 149.8, z height 234); the landscape
# default (y 234, z 149.8) fails. Falcon FLDL-i150x15-W housing 158 x 17 x 20 mm
CHEST_SIZES = {"getac_tablet": [0.0176, 0.1498, 0.234], "head_light": [0.02, 0.158, 0.017]}
GETAC_LANDSCAPE = [0.0176, 0.234, 0.1498]
# the replaced Getac ZX10 (275 x 192 x 17.9 mm) must not come back in the model or the robot and exploded pages
CHEST_RETIRED = [r"ZX10", r"275 x 192", r"0\.275, 0\.192", r"17\.9 mm", r"(?i)landscape (?:default|position)", r"getac_second_position_ghost",
                 r"(?i)portrait second position", r"chest_estop", r"(?i)chest E-stop", r"estop_p[1-4]_ghost"]
# head camera (P-03 rev20.0 items 15, 17 and 18, 28 Oct 2026): lens 42 mm ahead of the shoulder, baseline hp30
HEAD_PITCH_BASELINE = 30
LIFT_PARTS = {"lift_stop_sensors": "LFT-001", "lift_sensor_brackets": "LFT-003", "flag_rod": "LFT-004",
              "rod_corner_bracket": "LFT-005", "lift_flag": "LFT-006"}
LIFT_SENSOR_Z = [0.12, 0.295, 0.47]  # above the column base, P-03 rev20.0 item 24
ZED_X = 0.237   # A4 (2 Nov 2026): lens 57 mm ahead of the shoulder


def getac_default_errors(size):
    """A3 (2 Nov 2026): the drawn Getac must be portrait (149.8 across, 234 tall); a landscape default fails."""
    if size == GETAC_LANDSCAPE:
        return ["the Getac is drawn landscape; portrait is the decided default (A3, 2 Nov 2026)"]
    if size != CHEST_SIZES["getac_tablet"]:
        return ["the Getac size %s is not the portrait %s (A3)" % (size, CHEST_SIZES["getac_tablet"])]
    return []


def retired_chest_hits(text):
    """Patterns of CHEST_RETIRED found in a text: a landscape default, the portrait ghost and the old E-stop ghosts are
    retired (A3, A5, 2 Nov 2026); the portrait default is decided."""
    return [pat for pat in CHEST_RETIRED if re.search(pat, text)]


def check_chest_and_riser(root, html, err, comps):
    """Second E-stop and chest equipment (P-03 rev20.0 item 24, layout update of 28 Oct 2026): the three
    registry entries exist and are placeholders, the OpenArm kit button (ARM-008) is gone, the second E-stop is
    built once on the static lift profile (rear face, facing rearward, near its upper edge), M.CHEST lists the
    moving chest bottom up with the head light 30 mm under the Getac, no red or yellow button in the robot page
    fittings, and the head light has no glow or light source. Head camera: hp30 baseline and the 42 mm lens
    position. Tote riser (robot.html): one riser group per tote that follows the riser value and is hidden at 0."""
    try:
        with open(os.path.join(root, "model", "model.js"), encoding="utf-8") as f:
            js = f.read()
    except OSError:
        return
    byid = {c.get("id"): c for c in comps}
    if "arm_kit_estop" in byid:
        err("model.js", "arm_kit_estop (ARM-008, withdrawn) is still in the registry; the second E-stop is second_estop")
    for cid in CHEST_IDS:
        c = byid.get(cid)
        if not c:
            err("model.js", "chest item %s is missing from the registry" % cid)
        elif not c.get("placeholder"):
            err("model.js", "chest item %s is not marked placeholder" % cid)
    try:
        with open(os.path.join(root, "model", "exploded.json"), encoding="utf-8") as f:
            xj = f.read()
    except OSError:
        xj = ""
    for name, text in (("model.js", js), ("exploded.json", xj), ("robot.html", html["robot.html"]),
                       ("exploded.html", html["exploded.html"])):
        for pat in retired_chest_hits(text):
            if pat:
                err(name, "names a replaced chest layout item (%s): the tablet is the Getac ZX80 in portrait (A3) and "
                    "the second E-stop (second_estop) is on the adapter plate (A5, 2 Nov 2026)" % pat)
    m = re.search(r"/\*CHEST-JSON\*/(.*?)/\*CHEST-JSON-END\*/", js, flags=re.S)
    chest = json.loads(m.group(1)) if m else {}
    if chest.get("order") != CHEST_ORDER:
        err("model.js", "M.CHEST order %s, expected %s (moving chest, bottom up)" % (chest.get("order"), CHEST_ORDER))
    drawn = chest.get("drawn", {})
    for cid in CHEST_ORDER:
        geo = (byid.get(cid) or {}).get("geometry")
        if cid not in drawn or geo in (None, "none"):
            err("model.js", "chest item %s is not drawn (M.CHEST drawn and a registry geometry)" % cid)
    for cid, size in CHEST_SIZES.items():  # placeholder sizes from their sources, x depth, y across, z height (m)
        if (drawn.get(cid) or {}).get("size") != size:
            err("model.js", "chest item %s size %s, expected %s from its source" % (cid, (drawn.get(cid) or {}).get("size"), size))
    stack = [(cid, drawn[cid]["z"] - drawn[cid]["size"][2] / 2, drawn[cid]["z"] + drawn[cid]["size"][2] / 2)
             for cid in CHEST_ORDER if cid in drawn and "size" in drawn[cid]]
    if len(stack) == 2:
        gap = stack[1][1] - stack[0][2]
        if abs(gap - LIGHT_TABLET_GAP) > 0.0005:
            err("model.js", "head light top edge %.4f m below the Getac bottom edge, expected %.3f m" % (gap, LIGHT_TABLET_GAP))
    for cid, bottom, top in stack:
        if bottom < 0.01 or top > 0.35:  # arm profile from 10 to 350 mm above the column top
            err("model.js", "chest item %s leaves the arm-profile height (%.4f to %.4f m)" % (cid, bottom, top))
    for e_ in getac_default_errors((drawn.get("getac_tablet") or {}).get("size")):
        err("model.js", e_)
    se = chest.get("second_estop") or {}
    # A5 (2 Nov 2026): built exactly once, on the adapter plate top in the moving group, button up
    if se.get("position") != "adapter_top" or not 0.03 <= se.get("panel_above_plate", -1) <= 0.07:
        err("model.js", "M.CHEST second_estop must be position adapter_top with the panel 30 to 70 mm above the plate (A5)")
    if len(re.findall(r"part\('second_estop'", js)) != 1 or not re.search(r"part\('second_estop', mov\)", js):
        err("model.js", "the second E-stop must be built exactly once, on the adapter plate in the moving group (part('second_estop', mov))")
    fm = re.search(r"function chestItems\s*\(", js)
    body = function_body(js, fm.end()) if fm else ""
    if fm and "rotation.y = -Math.PI / 2" not in body:
        err("model.js", "chestItems must turn the second E-stop button up (rotation.y = -Math.PI / 2)")
    for fn in ("columnFittings", "chassisFittings"):
        fm2 = re.search(r"function %s\s*\(" % fn, js)
        if fm2 and re.search(r"\bmats\.(red|yellow)\b", function_body(js, fm2.end())):
            err("model.js", "%s draws an E-stop (red or yellow); E-stops come from the GLB and chestItems" % fn)
    if not fm:
        err("model.js", "chestItems not found")
    elif re.search(r"emissive|Light\(", body):
        err("model.js", "chestItems gives the head light a glow or a light source")
    # One robot on both pages: the same M.build, chestItems and liftSensors without page options; only
    # fittings (robot page scene items that are not registry parts) may differ.
    if re.search(r"chestPlaceholders|function chestItems\s*\([^)]*,\s*all\)|if \(!all\) return out;", js):
        err("model.js", "chestItems has a page option again; both pages draw the same robot")
    if "chestItems(THREE, R, mov, mats).forEach" not in js or "liftSensors(THREE, R, mov, mats).forEach" not in js:
        err("model.js", "M.build does not draw the chest items and the lift stop sensor set on every build")
    builds = {page: re.findall(r"MODEL\.build\(\w+,\s*(\{[^}]*\})\)", html[page]) for page in ("robot.html", "exploded.html")}
    keys = lambda a: set(re.findall(r"(\w+)\s*:", a))
    for page, allowed in (("robot.html", {"fittings", "headPitch"}), ("exploded.html", {"headPitch"})):
        if len(builds[page]) != 1 or not keys(builds[page][0]) <= allowed:
            err(page, "builds the shared model with options %s; only %s are allowed (one robot on both pages)"
                % (builds[page], sorted(allowed)))
    # Lift stop sensor set (P-03 rev20.0 item 24, LIFT-SNS-01 rev 1, BOM Issue 7.14 LFT-001 to LFT-006): the flag
    # faces S1, S2 and S3 at L1000, L1175 and L1350, the 2 mm gap and the 9 mm rod offset.
    lm = re.search(r"/\*LIFT-JSON\*/(.*?)/\*LIFT-JSON-END\*/", js, flags=re.S)
    ls = json.loads(lm.group(1)) if lm else {}
    for cid, bom in LIFT_PARTS.items():
        c = byid.get(cid)
        if not c or c.get("bom") != bom or not c.get("placeholder"):
            err("model.js", "lift sensor part %s (%s) missing, with another BOM ID or not a placeholder" % (cid, bom))
    if ls.get("z") != LIFT_SENSOR_Z or ls.get("flag_below_plate") != 0.41 or ls.get("gap") != 0.002 \
            or ls.get("flag") != [0.002, 0.045, 0.02] or (ls.get("rod") or {}).get("len") != 0.43:
        err("model.js", "M.LIFT_SENSE differs from LIFT-SNS-01 rev 1 (sensors z 120/295/470, flag 410 mm below the plate, 2 mm gap, 45 x 20 x 2 flag, 430 mm rod)")
    else:
        dm = re.search(r"STOPS:\s*\{L1000:\s*([\d.]+),\s*L1175:\s*([\d.]+),\s*L1350:\s*([\d.]+)\}", js)
        stops = [float(v) for v in dm.groups()] if dm else []
        for k, (dz, stop) in enumerate(zip(ls["z"], stops)):
            # plate underside = base-plate top + retracted column + lift travel; flag centre 410 mm below it
            flag = 0.53 + (stop - stops[0]) - ls["flag_below_plate"]
            if abs(flag - dz) > 1e-6:
                err("model.js", "at %s the flag centre is %.3f m above the column base, the sensor S%d is at %.3f m" % (ls["stops"][k], flag, k + 1, dz))
        s_out = ls["axis_off"] + ls["sensor"]["d"] / 2
        if abs(ls["rod"]["off"] - s_out - 0.009) > 1e-6:
            err("model.js", "the flag rod is %.4f m beside the sensors, LIFT-SNS-01 gives 9 mm" % (ls["rod"]["off"] - s_out))
    if not re.search(r"part\('lift_stop_sensors', R\.col\)", js) or not re.search(r"part\('flag_rod', mov\)", js) \
            or not re.search(r"part\('lift_flag', mov\)", js):
        err("model.js", "the sensors must be in the static lift group and the rod and flag in the moving group")
    # Head camera baseline hp30 and lens 42 mm ahead of the shoulder (P-03 rev20.0 items 15, 17 and 18)
    pitch = lambda a: (re.search(r"headPitch\s*:\s*(\d+)", a) or [None, None])[1]
    for page in ("robot.html", "exploded.html"):
        if not builds[page] or any(pitch(a) != str(HEAD_PITCH_BASELINE) for a in builds[page]):
            err(page, "the shared model must be built with headPitch %d (hp30 baseline)" % HEAD_PITCH_BASELINE)
    if "o.headPitch === undefined ? %d : o.headPitch" % HEAD_PITCH_BASELINE not in js:
        err("model.js", "M.build default head pitch is not the hp30 baseline")
    zm = re.search(r"ZED_X:\s*([\d.]+)", js)
    if not zm or abs(float(zm.group(1)) - ZED_X) > 1e-6:
        err("model.js", "M.DIMS.ZED_X %s, expected %.3f (lens 57 mm ahead of the shoulder, A4)" % (zm and zm.group(1), ZED_X))
    h = html["robot.html"]
    for need, what in (('this.hp=%d,' % HEAD_PITCH_BASELINE, "initial head pitch state"),
                       ('id="hp" min="15" max="35" step="5" value="%d"' % HEAD_PITCH_BASELINE, "head pitch slider value"),
                       ('N0("hp-v").textContent="%d\\xB0"' % HEAD_PITCH_BASELINE, "head pitch readout"),
                       ('<b>hp%d</b> <span class="kind k-dec">default</span>' % HEAD_PITCH_BASELINE, "configuration table default")):
        if need not in h:
            err("robot.html", "%s is not hp%d" % (what, HEAD_PITCH_BASELINE))
    for bad in ("default hp25", "<b>hp25</b>", "head_pitch hp25,", "22 mm ahead", "0.202, 0, 0.389"):
        if bad in h:
            err("robot.html", "still states the former head camera baseline (%s)" % bad)
    h = html["robot.html"]
    bm = re.search(r"\bbuildTotes\(\)\s*\{", h)
    body = function_body(h, bm.start()) if bm else ""
    if "tote_riser_" not in body or "riserFit(" not in body:
        err("robot.html", "buildTotes draws no tote riser (one riser group per tote, fitted to the riser value)")
    sm = re.search(r"\bsetRiser\(\w+\)\s*\{", h)
    if not sm or "riserFit(" not in function_body(h, sm.start()):
        err("robot.html", "setRiser does not refit the tote risers to the riser value")
    fm = re.search(r"\briserFit\((\w+),(\w+)\)\s*\{", h)
    if not fm or not re.search(r"\.visible=%s>" % fm.group(2), function_body(h, fm.start())):
        err("robot.html", "riserFit does not hide the riser at riser 0")


SYNC_FILES = ["model/model.js", "model/exploded.json", "robot.html", "exploded.html"]


def check_sync_audit(root, err, comps):
    """One robot on both pages: scripts/sync_audit.json (written by scripts/audit_sync.js) must be current (its
    sha256 fingerprint matches the files it read), cover every registry part and report no mismatch between the
    robot page and the exploded view (drawn on both, exploded.json stage and offset, mesh count, transforms)."""
    path = os.path.join(root, "..", "..", "..", "scripts", "sync_audit.json")
    try:
        with open(path, encoding="utf-8") as f:
            a = json.load(f)
    except (OSError, ValueError):
        err("sync_audit.json", "missing; run node scripts/audit_sync.js")
        return
    for f in SYNC_FILES:
        with open(os.path.join(root, f), "rb") as fh:
            if hashlib.sha256(fh.read()).hexdigest() != a.get("fingerprint", {}).get(f):
                err("sync_audit.json", "older than %s; rerun node scripts/audit_sync.js" % f)
    seen = {r.get("part") for r in a.get("rows", [])}
    for c in comps:
        for pid in c.get("nodes") or c.get("parts") or []:
            if pid not in seen:
                err("sync_audit.json", "registry part %s (%s) is not in the audit" % (pid, c.get("id")))
    for m in a.get("mismatches", []):
        err("sync_audit.json", "robot page and exploded view differ: %s" % m)
    if a.get("errors"):
        err("sync_audit.json", "page errors during the audit: %s" % a["errors"])


# Known contacts: overlaps in the model that are recorded as issues and accepted for now (warn only). Each entry
# names the two parts, the overlap the model must show (mm, within 0.1 mm), the geometry_issues.csv row that records
# it (by its parts text; IDs are assigned by analyse.py) and the marker drawn in the model. When the overlap changes (fixed or worse) the check fails until the entry
# and the issue row are updated.
KNOWN_CONTACTS = [
    {"a": "tz_receiver", "b": "floor transmitter (52 mm, not drawn)", "transmitter_h_mm": 52.0, "overlap_mm": 2.0,
     "issue": "TZBOT receiver / floor transmitter WCM-500-24 (charging gap)", "kind": "reserved for 3.0", "severity": "minor",
     "owner": "fridayali", "limit": "gap 10 to 30 mm",
     "note": "receiver reserved at the rear, not installed in 2.0; charging gap to be solved in release 3.0 (TZBOT WCM-500-24 manual V2.5: air gap 20 +-10 mm)"},
]


def check_known_contacts(root, err):
    """Each declared known contact: the receiver bottom (first primitive of tz_receiver) against the 52 mm floor transmitter
    gives the declared overlap, and its geometry_issues.csv row is present with the declared kind, severity, owner and limit."""
    try:
        P = json.load(open(os.path.join(root, "model", "placement.json"), encoding="utf-8"))
        rows = {r["parts"]: r for r in csv.DictReader(open(os.path.join(root, "model", "geometry_issues.csv"), encoding="utf-8"))}
    except OSError as e:
        err("known contacts", "cannot read the model files: %s" % e)
        return
    G = P.get("geometry", {})
    for kc in KNOWN_CONTACTS:
        if kc["a"] not in G:
            err("known contacts", "%s: part missing in placement.json" % kc["a"])
            continue
        q = G[kc["a"]]["prims"][0]
        bottom = (float(q["p"][2]) - float(q["s"][2]) / 2) * 1000
        ov = kc["transmitter_h_mm"] - bottom
        if abs(ov - kc["overlap_mm"]) > 0.1:
            err("known contacts", "%s / %s overlap %.1f mm, declared %.1f mm: update KNOWN_CONTACTS and %s" % (kc["a"], kc["b"], ov, kc["overlap_mm"], kc["issue"]))
        r = rows.get(kc["issue"])
        if not r:
            err("known contacts", "%s: row missing in geometry_issues.csv" % kc["issue"])
            continue
        for key in ("kind", "severity", "owner"):
            if r[key] != kc[key]:
                err("known contacts", "%s: %s is %r, declared %r" % (kc["issue"], key, r[key], kc[key]))
        if ("gap -%g mm" % kc["overlap_mm"]) not in r["measured"] or kc["limit"] not in r["limit"] or "release 3.0" not in r["suggested_fix"]:
            err("known contacts", "%s: the row does not state gap -%g mm, the limit %r and the release 3.0 note" % (kc["issue"], kc["overlap_mm"], kc["limit"]))


# STATE.md (repository state record): every figure it states about the roadmap model is read from the generated files,
# so that it cannot go stale. Each pattern must be present once; its numbers must equal the generated ones.
STATE_FIGURES = [
    ("snapshot", r"Roadmap pages \(`docs/assets/roadmap/`\): snapshot (%s)" % DATE),
    ("sync_audit", r"`scripts/sync_audit\.json` regenerated by the Playwright visual audit: (\d+) parts, (\d+) mismatches"),
    ("bom", r"BOM Issue 7\.14 \((\d+) records, (\d+) onboard by the model rule\)"),
    ("issues", r"Geometry and hardware issues \(`geometry_issues\.csv`\): (\d+) blockers?, (\d+) majors?, (\d+) minors?"),
    ("parity", r"Roadmap vs combined model \(`parity_report\.csv`\): (\d+) mapped items, (\d+) matched, (\d+) out of tolerance, (\d+) pending"),
]


def state_figures(root):
    """The figures of STATE_FIGURES from the generated files under docs/assets/roadmap and scripts/."""
    repo = os.path.abspath(os.path.join(root, "..", "..", ".."))
    out = {}
    try:
        a = json.load(open(os.path.join(repo, "scripts", "sync_audit.json"), encoding="utf-8"))
        out["sync_audit"] = (str(len(a.get("rows", []))), str(len(a.get("mismatches", []))))
    except (OSError, ValueError):
        pass
    try:
        rows = list(csv.DictReader(open(os.path.join(root, "model", "bom_coverage.csv"), encoding="utf-8")))
        out["bom"] = (str(len(rows)), str(sum(1 for r in rows if r["onboard"] == "y")))
    except OSError:
        pass
    try:
        rows = list(csv.DictReader(open(os.path.join(root, "model", "geometry_issues.csv"), encoding="utf-8")))
        out["issues"] = tuple(str(sum(1 for r in rows if r["severity"] == s)) for s in ("blocker", "major", "minor"))
    except OSError:
        pass
    try:
        p = json.load(open(os.path.join(repo, "scripts", "roadmap_model", "parity_summary.json"), encoding="utf-8"))
        out["parity"] = (str(p["mapped_items"]), str(p["matched"]), str(p["out_of_tolerance"]), str(p["pending"]))
    except (OSError, ValueError, KeyError):
        pass
    return out


def state_errors(state_text, figures, snapshot):
    """Disagreements between STATE.md and the generated figures (empty list: STATE.md is current)."""
    out = []
    want = dict(figures)
    if snapshot:
        want["snapshot"] = (snapshot,)
    for key, pat in STATE_FIGURES:
        found = re.findall(pat, state_text)
        if len(found) != 1:
            out.append("STATE.md must state the %s figure once (pattern %s), found %d" % (key, pat, len(found)))
            continue
        got = found[0] if isinstance(found[0], tuple) else (found[0],)
        if key in want and tuple(got) != tuple(want[key]):
            out.append("STATE.md %s figure %s, the generated files give %s" % (key, ", ".join(got), ", ".join(want[key])))
        elif key not in want:
            out.append("STATE.md %s figure cannot be checked: its generated file is missing" % key)
    return out


def check_finish(root, err, comps, glb_prims):
    """model/finish.json: classes of known parts, primitives that exist, known texture names."""
    try:
        with open(os.path.join(root, "model", "finish.json"), encoding="utf-8") as f:
            fin = json.load(f)
    except (OSError, ValueError) as e:
        err("finish.json", str(e))
        return
    classes = fin.get("classes", {})
    parts = set(glb_prims)
    for c in comps:
        parts.update(c.get("parts", []))
    for pid in list(fin.get("parts", {})) + list(fin.get("class_of", {})):
        if pid not in parts:
            err("finish.json", "part %s is neither a GLB node nor a part of model.js" % pid)
    for pid, cl in fin.get("class_of", {}).items():
        for key, name in ({"*": cl} if isinstance(cl, str) else cl).items():
            if name not in classes:
                err("finish.json", "part %s names unknown class %s" % (pid, name))
            if key not in ("*", "lens") and pid in glb_prims and not (key.isdigit() and int(key) < glb_prims[pid]):
                err("finish.json", "part %s has no primitive %s" % (pid, key))
    for name, c in classes.items():
        if c.get("keep"):
            continue
        for k in ("roughness", "metalness"):
            if not isinstance(c.get(k), (int, float)) or not 0 <= c[k] <= 1:
                err("finish.json", "class %s: %s not 0 to 1" % (name, k))
        for k in ("specular", "env_scale"):
            if k in c and (not isinstance(c[k], (int, float)) or not 0 <= c[k] <= 1):
                err("finish.json", "class %s: %s not 0 to 1" % (name, k))
        for k in ("normal_map", "roughness_map"):
            if k in c and c[k] not in ("orange_peel", "layer_lines", "brushed"):
                err("finish.json", "class %s: unknown texture %s" % (name, c[k]))
        if ("normal_map" in c or "roughness_map" in c) and not c.get("tile_m"):
            err("finish.json", "class %s has a texture but no tile_m" % name)


def jpeg_size(path):
    """(width, height) of a baseline or progressive JPEG, from its SOF segment."""
    with open(path, "rb") as f:
        d = f.read()
    if d[:2] != b"\xff\xd8":
        return None
    i = 2
    while i + 9 < len(d):
        if d[i] != 0xFF:
            return None
        m, n = d[i + 1], struct.unpack(">H", d[i + 2:i + 4])[0]
        if m in (0xC0, 0xC1, 0xC2):
            h, w = struct.unpack(">HH", d[i + 5:i + 9])
            return w, h
        i += 2 + n
    return None


def check_store_media(root, html, err):
    """robot.html: the store video (poster, preload none, download link), the pictures and their lazy
    thumbnails, all labelled as simulation visualization, within their size limits and the first-load budget."""
    h = html["robot.html"]
    full = os.path.join(root, STORE_VIDEO)
    if not os.path.isfile(full):
        err("robot.html", "store video %s is missing" % STORE_VIDEO)
    elif os.path.getsize(full) > MEDIA_MAX_BYTES:
        err("robot.html", "%s is %d bytes, over %d" % (STORE_VIDEO, os.path.getsize(full), MEDIA_MAX_BYTES))
    poster = os.path.join(root, STORE_POSTER)
    if not os.path.isfile(poster) or os.path.getsize(poster) > PICTURE_MAX_BYTES:
        err("robot.html", "poster %s is missing or over %d bytes" % (STORE_POSTER, PICTURE_MAX_BYTES))
    if 'src="%s"' % STORE_VIDEO not in h or 'href="%s" download' % STORE_VIDEO not in h:
        err("robot.html", "the store video is not shown with a download link")
    for v in re.findall(r"<video\b[^>]*>", h):
        if 'preload="none"' not in v or "poster=" not in v:
            err("robot.html", "a video loads before it is played or has no poster")
    if "Simulation visualization" not in h or "Not footage of the real robot" not in h:
        err("robot.html", "the store video and pictures must be labelled as simulation visualization, not real-robot footage")
    for name, (w, hh) in STORE_PICTURES:
        pic, th = "media/store/%s.jpg" % name, "media/store/thumbs/%s.jpg" % name
        fp = os.path.join(root, pic)
        if not os.path.isfile(fp):
            err("robot.html", "picture %s is missing" % pic)
            continue
        if os.path.getsize(fp) > PICTURE_MAX_BYTES:
            err("robot.html", "%s is %d bytes, over %d" % (pic, os.path.getsize(fp), PICTURE_MAX_BYTES))
        if jpeg_size(fp) != (w, hh):
            err("robot.html", "%s is %s, not %d x %d" % (pic, jpeg_size(fp), w, hh))
        ft = os.path.join(root, th)
        if not os.path.isfile(ft) or os.path.getsize(ft) > THUMB_MAX_BYTES:
            err("robot.html", "thumbnail %s is missing or over %d bytes" % (th, THUMB_MAX_BYTES))
        if not re.search(r'<a href="%s"><img data-src="%s"[^>]*loading="lazy"' % (re.escape(pic), re.escape(th)), h):
            err("robot.html", "%s is not linked from a lazy-loaded thumbnail" % pic)
    sheet = os.path.join(root, STORE_SHEET)
    if not os.path.isfile(sheet) or os.path.getsize(sheet) > PICTURE_MAX_BYTES:
        err("robot.html", "contact sheet %s is missing or over %d bytes" % (STORE_SHEET, PICTURE_MAX_BYTES))
    # first load: page, scripts, finish.json, images that are not lazy, video posters (thumbnails carry data-src and
    # get their src from an IntersectionObserver when the grid comes near the viewport)
    first = len(h.encode("utf-8")) + os.path.getsize(os.path.join(root, "model", "finish.json")) + os.path.getsize(os.path.join(root, "model", "placement.json"))
    for src in re.findall(r'<script src="([^"]+)"', h) + re.findall(r'<video\b[^>]*\bposter="([^"]+)"', h):
        first += os.path.getsize(os.path.join(root, src)) if os.path.isfile(os.path.join(root, src)) else 0
    for tag in re.findall(r"<img\b[^>]*>", strip_scripts(h)):
        m = re.search(r'src="([^"]+)"', tag)
        if m and 'loading="lazy"' not in tag and not m.group(1).startswith("data:") and os.path.isfile(os.path.join(root, m.group(1))):
            first += os.path.getsize(os.path.join(root, m.group(1)))
    if first > ROBOT_FIRST_LOAD_MAX_BYTES:
        err("robot.html", "first load %d bytes, over %d (15 MB default-view budget)" % (first, ROBOT_FIRST_LOAD_MAX_BYTES))


def mp4_seconds(path):
    """Duration of an MP4 file from its mvhd box (seconds)."""
    with open(path, "rb") as f:
        d = f.read()
    i = d.find(b"mvhd")
    if i < 0:
        return None
    if d[i + 4] == 1:
        ts, du = struct.unpack(">IQ", d[i + 24:i + 36])
    else:
        ts, du = struct.unpack(">II", d[i + 16:i + 24])
    return du / ts


def check_store_video_text(root, html, err):
    """robot.html: the text under the store video states the duration of the file and a speed that matches the
    simulated time over that duration (the caption of the render carries the same speed)."""
    full = os.path.join(root, STORE_VIDEO)
    if not os.path.isfile(full):
        return
    m = re.search(r"no audio, ([\d.]+) s, ([\d.]+) MB; played at ([\d.]+)x speed \(([\d.]+) s of simulated time in ([\d.]+) s of video\)",
                  html["robot.html"])
    if not m:
        err("robot.html", "the store video text does not state duration, size and speed")
        return
    dur = mp4_seconds(full)
    stated, mb, speed, sim, vid = (float(v) for v in m.groups())
    if dur is None or abs(stated - dur) > 0.1 or abs(vid - dur) > 0.1:
        err("robot.html", "store video text says %.1f s, the file lasts %s s" % (stated, dur))
    if abs(mb - os.path.getsize(full) / 1e6) > 0.05:
        err("robot.html", "store video text says %.1f MB, the file is %d bytes" % (mb, os.path.getsize(full)))
    if dur and abs(sim / dur - speed) > 0.05 * speed:
        err("robot.html", "store video text says %gx speed, %.1f s of sim time in %.1f s is %.2fx" % (speed, sim, dur, sim / dur))


def check_nav(p, html, err):
    m = re.search(r'<nav class="rm-nav"[^>]*>.*?</nav>', html, flags=re.S)
    if not m:
        err(p, "no roadmap navigation")
        return
    links = re.findall(r'<li><a href="([^"]+)"( aria-current="page")?>([^<]+)</a></li>', m.group(0))
    if [(h, txt) for h, _, txt in links] != NAV:
        err(p, "navigation lists %s, expected %s" % ([txt for _, _, txt in links], [txt for _, txt in NAV]))
    current = [h for h, cur, _ in links if cur]
    if current != [p]:
        err(p, "navigation marks %s as the current page" % current)


def private_terms():
    raw = os.environ.get("ROADMAP_PRIVATE_TERMS", "")
    return [t.strip() for t in raw.split(",") if t.strip()]



# ---------------------------------------------------------------- sensor poses (review of ef90d7f, 2 Nov 2026)
# Drawn sensor pose against its source frame, in x, y and z within 1 mm and in orientation within 0.2 deg. The drawn
# pose of a base sensor is recovered from its drawn mesh (GLB node, base_footprint) by a least-squares rigid fit
# (Horn's quaternion method) to its reference body, the same mesh in the sensor frame (source_snapshot.json
# sensor_bodies, written by build.py and checked there against the platform-sw visual STL of the sensor). The
# intended offset between the drawn body and the frame (where the frame sits on the body) is declared once below,
# with its source, and applied: the drawn body reference point must sit at the frame origin plus that offset.
WHEEL_COMPRESSION_M = 0.002  # intended tyre compression (owner decision of 2 Nov 2026, B1)
SENSOR_POSE_TOL_M = 0.001
SENSOR_POSE_TOL_DEG = 0.2
SENSOR_FIT_RMS_MAX_M = 0.0002  # the drawn mesh must be the reference body moved rigidly
# frame: (body reference point, offset of that point from the frame origin in the sensor frame [m], source)
SENSOR_BODY_OFFSETS = {
    "imu_link": ("board centre", (0.0, -0.0151, -0.0008), "ICM-42688-P die is the frame; 6DOF IMU 14 Click outline 25.4 x 42.9 mm (platform-sw meshes/PROVENANCE.yaml components.imu, imu.stl)"),
    "lidar_link": ("housing centre", (0.0, 0.0, -0.0099), "frame on the scan plane, 222.05 mm above the floor (RPLIDAR S3, sensor_frames.yaml lidar_link; lidar.stl)"),
    "base_camera_link": ("housing centre", (-0.0122, 0.0, 0.0), "frame on the front glass (Gemini 336L, PROVENANCE.yaml components.base_camera; base_camera.stl)"),
    "tof_front": ("housing centre", (-0.00675, 0.0, 0.0), "frame on the lens face (TF-Luna datasheet A05 outline 35 x 21.25 x 13.5 mm; tof.stl)"),
    "tof_rear": ("housing centre", (-0.00675, 0.0, 0.0), "frame on the lens face (TF-Luna datasheet A05; tof.stl)"),
    "us_front_left": ("housing centre", (-0.0160, 0.0, 0.0), "frame on the transducer face; body through the panel hole (MB7060 datasheet 11838ab, PROVENANCE.yaml components.ultrasonic; ultrasonic.stl)"),
    "us_front_right": ("housing centre", (-0.0160, 0.0, 0.0), "as us_front_left"),
    "us_rear_left": ("housing centre", (-0.0160, 0.0, 0.0), "as us_front_left"),
    "us_rear_right": ("housing centre", (-0.0160, 0.0, 0.0), "as us_front_left"),
    "lift_stop_sensor_l1000_link": ("sensor body centre", (0.024, 0.0, 0.0), "frame on the sensing face; SICK IME12-04BNSZC0S body 48 mm (LIFT-SNS-01 rev 1; combined_robot.urdf visual origin)"),
    "lift_stop_sensor_l1175_link": ("sensor body centre", (0.024, 0.0, 0.0), "as lift_stop_sensor_l1000_link"),
    "lift_stop_sensor_l1350_link": ("sensor body centre", (0.024, 0.0, 0.0), "as lift_stop_sensor_l1000_link"),
    "head_camera_link": ("housing centre", (-0.013, 0.0, 0.0), "frame on the left lens line; ZED Mini body 26.5 mm deep (datums head_camera_size; combined_robot.urdf visual origin)"),
}


def _rpy(r, p, y):
    import math
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return [[cy * cp, cy * sp * sr - sy * cr, cy * sp * cr + sy * sr],
            [sy * cp, sy * sp * sr + cy * cr, sy * sp * cr - cy * sr],
            [-sp, cp * sr, cp * cr]]


def _mul(A, B):
    return [[sum(A[i][k] * B[k][j] for k in range(3)) for j in range(3)] for i in range(3)]


def _mv(A, v):
    return [sum(A[i][k] * v[k] for k in range(3)) for i in range(3)]


def _tr(A):
    return [[A[j][i] for j in range(3)] for i in range(3)]


def _angle_deg(A, B):
    import math
    M = _mul(_tr(A), B)
    c = max(-1.0, min(1.0, (M[0][0] + M[1][1] + M[2][2] - 1) / 2))
    return math.degrees(math.acos(c))


def _euler_zyx(Rm):
    import math
    return (math.atan2(Rm[2][1], Rm[2][2]), -math.asin(max(-1.0, min(1.0, Rm[2][0]))), math.atan2(Rm[1][0], Rm[0][0]))


def _jacobi_max_eigvec(N):
    """Eigenvector of the largest eigenvalue of a symmetric 4x4 matrix (cyclic Jacobi)."""
    import math
    A = [row[:] for row in N]
    V = [[1.0 if i == j else 0.0 for j in range(4)] for i in range(4)]
    for _ in range(60):
        off = sum(A[i][j] ** 2 for i in range(4) for j in range(4) if i != j)
        if off < 1e-30:
            break
        for p in range(3):
            for q in range(p + 1, 4):
                if abs(A[p][q]) < 1e-300:
                    continue
                th = (A[q][q] - A[p][p]) / (2 * A[p][q])
                t = (1.0 if th >= 0 else -1.0) / (abs(th) + math.sqrt(th * th + 1))
                c = 1 / math.sqrt(t * t + 1)
                s_ = t * c
                for k in range(4):
                    akp, akq = A[k][p], A[k][q]
                    A[k][p], A[k][q] = c * akp - s_ * akq, s_ * akp + c * akq
                for k in range(4):
                    apk, aqk = A[p][k], A[q][k]
                    A[p][k], A[q][k] = c * apk - s_ * aqk, s_ * apk + c * aqk
                for k in range(4):
                    vkp, vkq = V[k][p], V[k][q]
                    V[k][p], V[k][q] = c * vkp - s_ * vkq, s_ * vkp + c * vkq
    i = max(range(4), key=lambda k: A[k][k])
    return [V[k][i] for k in range(4)]


def rigid_fit(local, world):
    """Rotation R and translation t with world ~ R local + t (Horn 1987, unit quaternions); returns (R, t, rms)."""
    import math
    n = len(local)
    ca = [sum(p[i] for p in local) / n for i in range(3)]
    cb = [sum(p[i] for p in world) / n for i in range(3)]
    S = [[0.0] * 3 for _ in range(3)]
    for a, b in zip(local, world):
        a = [a[i] - ca[i] for i in range(3)]
        b = [b[i] - cb[i] for i in range(3)]
        for i in range(3):
            for j in range(3):
                S[i][j] += a[i] * b[j]
    (sxx, sxy, sxz), (syx, syy, syz), (szx, szy, szz) = S
    N = [[sxx + syy + szz, syz - szy, szx - sxz, sxy - syx],
         [syz - szy, sxx - syy - szz, sxy + syx, szx + sxz],
         [szx - sxz, sxy + syx, -sxx + syy - szz, syz + szy],
         [sxy - syx, szx + sxz, syz + szy, -sxx - syy + szz]]
    w, x, y, z = _jacobi_max_eigvec(N)
    R = [[w * w + x * x - y * y - z * z, 2 * (x * y - w * z), 2 * (x * z + w * y)],
         [2 * (x * y + w * z), w * w - x * x + y * y - z * z, 2 * (y * z - w * x)],
         [2 * (x * z - w * y), 2 * (y * z + w * x), w * w - x * x - y * y + z * z]]
    rc = _mv(R, ca)
    t = [cb[i] - rc[i] for i in range(3)]
    rms = math.sqrt(sum(sum((_mv(R, a)[i] + t[i] - b[i]) ** 2 for i in range(3)) for a, b in zip(local, world)) / n)
    return R, t, rms


def glb_vertices(payload, blz):
    """Vertices of every GLB node (base_footprint, metres) from model/base_glb.js."""
    m = re.search(r'window\.BASE_GLB="([^"]+)"', payload)
    raw = base64.b64decode(m.group(1).replace(".", ""))
    jl = struct.unpack("<I", raw[12:16])[0]
    doc = json.loads(raw[20:20 + jl])
    b0 = 28 + jl
    out = {}
    for n in doc["nodes"]:
        if "mesh" not in n:
            continue
        vs = []
        for pr in doc["meshes"][n["mesh"]]["primitives"]:
            a = doc["accessors"][pr["attributes"]["POSITION"]]
            bv = doc["bufferViews"][a["bufferView"]]
            o = b0 + bv.get("byteOffset", 0) + a.get("byteOffset", 0)
            for k in range(a["count"]):
                x, y, z = struct.unpack_from("<fff", raw, o + 12 * k)
                vs.append([x, y, z + blz])
        out[(n.get("extras") or {}).get("id", n.get("name"))] = vs
    return out


def urdf_frames(path, joints=None):
    """World (base_footprint) pose (R, t) of every link of an expanded URDF; joints: prismatic joint positions."""
    import xml.etree.ElementTree as ET
    root = ET.parse(path).getroot()
    J = {j.find("child").get("link"): j for j in root.findall("joint")}
    vis = {}
    for l in root.findall("link"):
        v = l.find("visual/origin")
        vis[l.get("name")] = [float(x) for x in v.get("xyz", "0 0 0").split()] if v is not None else [0.0, 0.0, 0.0]
    cache = {}

    def world(link):
        if link in cache:
            return cache[link]
        if link not in J:
            cache[link] = ([[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]], [0.0, 0.0, 0.0])
            return cache[link]
        j = J[link]
        Rp, tp = world(j.find("parent").get("link"))
        o = j.find("origin")
        xyz = [float(x) for x in o.get("xyz", "0 0 0").split()] if o is not None else [0.0] * 3
        rpy = [float(x) for x in o.get("rpy", "0 0 0").split()] if o is not None else [0.0] * 3
        R = _mul(Rp, _rpy(*rpy))
        t = [a + b for a, b in zip(_mv(Rp, xyz), tp)]
        if j.get("type") == "prismatic":
            ax = [float(x) for x in j.find("axis").get("xyz").split()]
            q = (joints or {}).get(j.get("name"), 0.0)
            t = [a + b for a, b in zip(t, _mv(R, [c * q for c in ax]))]
        cache[link] = (R, t)
        return cache[link]
    return {name: world(name) for name in vis}, vis


def upper_body_sensor_poses(js, urdf_path):
    """Drawn pose (R, t, body reference point) of the upper-body sensors from model.js values (LIFT-JSON, M.DIMS,
    the hp30 baseline) and their source frames from the committed combined model (bp000, L1000)."""
    import math
    try:
        frames, _ = urdf_frames(urdf_path)
    except (OSError, Exception):  # noqa: BLE001 - reported below as a missing source
        return {"_error": "combined_robot.urdf missing or unreadable"}
    lift = json.loads(re.search(r"/\*LIFT-JSON\*/(.*?)/\*LIFT-JSON-END\*/", js).group(1))
    dims = re.search(r"M\.DIMS = \{(.*?)\};", js, re.S).group(1)
    num = lambda key: float(re.search(r"\b%s: ([-\d.]+)" % key, dims).group(1))
    bp = float(re.search(r"BP: \{bp000: ([\d.]+)", dims).group(1))
    top = num("PLATE_TOP")
    I = [[1.0, 0, 0], [0, 1.0, 0], [0, 0, 1.0]]
    out = {}
    s = lift["sensor"]
    ys = num("W") / 2 + lift["axis_off"] if re.search(r"\bW: ", dims) else 0.03 + lift["axis_off"]
    for k, dz in zip(("l1000", "l1175", "l1350"), lift["z"]):
        body = [bp + lift["face_x"] + s["len"] / 2, ys, top + dz]
        out["lift_stop_sensor_%s_link" % k] = {"drawn_body": body, "drawn_R": I, "source": frames.get("lift_stop_sensor_%s_link" % k)}
    hp = math.radians(HEAD_PITCH_BASELINE)
    Rz = _rpy(0, hp, 0)
    lens = [bp + num("ZED_X"), 0.0, top + float(re.search(r"RETRACTED: ([\d.]+)", dims).group(1)) + num("MOUNT_ABOVE_COL") + num("ZED_ABOVE_SH")]
    src = frames.get("head_camera_link")
    if src:   # A4 (2 Nov 2026): lens 57 mm ahead of J1_A; the combined model keeps 42 mm until the P-03 entry (+15 mm along x)
        src = dict(src) if isinstance(src, dict) else src
        try:
            src["t"] = [src["t"][0] + 0.015, src["t"][1], src["t"][2]]
        except (TypeError, KeyError, IndexError):
            src = (src[0], [src[1][0] + 0.015, src[1][1], src[1][2]]) if isinstance(src, tuple) else src
    out["head_camera_link"] = {"drawn_body": [a + b for a, b in zip(lens, _mv(Rz, [-0.013, 0, 0]))], "drawn_R": Rz, "source": src}
    return out


def sensor_pose_errors(snap, verts, upper=None):
    """Errors of the sensor pose check (empty list: every drawn sensor sits at its source frame within 1 mm and 0.2 deg)."""
    out = []
    bodies = snap.get("sensor_bodies") or {}
    rpys = snap.get("sensor_frames_rpy") or {}
    tol, tdeg = SENSOR_POSE_TOL_M, SENSOR_POSE_TOL_DEG
    for frame, node in snap["frame_nodes"].items():
        b = bodies.get(frame)
        if frame not in SENSOR_BODY_OFFSETS:
            out.append("sensor %s: no declared body offset (SENSOR_BODY_OFFSETS)" % frame)
            continue
        if not b or frame not in rpys:
            out.append("sensor %s: no reference body or orientation in source_snapshot.json (rerun build.py)" % frame)
            continue
        if node not in verts:
            out.append("sensor %s: GLB node %s missing" % (frame, node))
            continue
        local = [[c / 1000.0 for c in p] for p in b["ref_local_mm"]]
        world = verts[node]
        if len(local) != len(world):
            out.append("sensor %s: drawn mesh %s has %d vertices, reference body %d (rerun build.py)" % (frame, node, len(world), len(local)))
            continue
        R, t, rms = rigid_fit(local, world)
        src_t = snap["sensor_frames"][frame]
        src_R = _rpy(*rpys[frame])
        if rms > SENSOR_FIT_RMS_MAX_M:
            out.append("sensor %s: drawn mesh %s is not its reference body moved rigidly (fit rms %.2f mm)" % (frame, node, rms * 1000))
        d = [t[i] - src_t[i] for i in range(3)]
        for i, ax in enumerate("xyz"):
            if abs(d[i]) > tol:
                out.append("sensor %s: drawn frame %s %.4f, sensor_frames.yaml %.4f (%.1f mm off, limit 1 mm)" % (frame, ax, t[i], src_t[i], d[i] * 1000))
        a = _angle_deg(src_R, R)
        if a > tdeg:
            dr = [x - y for x, y in zip(_euler_zyx(R), rpys[frame])]
            out.append("sensor %s: drawn orientation %.2f deg from sensor_frames.yaml (roll/pitch/yaw %+.2f/%+.2f/%+.2f deg, limit 0.2 deg)" % (
                frame, a, *[__import__("math").degrees((x + 3.141592653589793) % 6.283185307179586 - 3.141592653589793) for x in dr]))
        name, off, _ = SENSOR_BODY_OFFSETS[frame]
        drawn_ref = [a_ + b_ for a_, b_ in zip(_mv(R, off), t)]
        want_ref = [a_ + b_ for a_, b_ in zip(_mv(src_R, off), src_t)]
        dd = [drawn_ref[i] - want_ref[i] for i in range(3)]
        if any(abs(x) > tol for x in dd):
            out.append("sensor %s: drawn %s (%.4f, %.4f, %.4f) is not at the frame plus its declared offset (%.4f, %.4f, %.4f)" % (frame, name, *drawn_ref, *want_ref))
        c = [x / 1000.0 for x in b["centre_local_mm"]]
        if any(abs(c[i] - off[i]) > tol for i in range(3)):
            out.append("sensor %s: reference body centre %s mm in the frame, declared offset %s m (SENSOR_BODY_OFFSETS)" % (frame, b["centre_local_mm"], off))
    for frame, e in (upper or {}).items():
        if frame == "_error":
            out.append("upper-body sensors: %s" % e)
            continue
        src = e["source"]
        if src is None:
            out.append("sensor %s: not in combined_robot.urdf" % frame)
            continue
        name, off, _ = SENSOR_BODY_OFFSETS[frame]
        src_R, src_t = src
        want = [a_ + b_ for a_, b_ in zip(_mv(src_R, off), src_t)]
        for i, ax in enumerate("xyz"):
            if abs(e["drawn_body"][i] - want[i]) > tol:
                out.append("sensor %s: drawn %s %s %.4f, combined model frame plus offset %.4f (%.1f mm off, limit 1 mm)" % (
                    frame, name, ax, e["drawn_body"][i], want[i], (e["drawn_body"][i] - want[i]) * 1000))
        a = _angle_deg(src_R, e["drawn_R"])
        if a > tdeg:
            out.append("sensor %s: drawn orientation %.2f deg from the combined model (limit 0.2 deg)" % (frame, a))
    return out


# ---------------------------------------------------------------- 2 Nov 2026 model checks (section G1)
PARTNER_TERMS = re.compile(r"\b(?:PAIA|Enactic|Reazon)\b", re.I)
SOURCE_SNAPSHOT = "model/source_snapshot.json"  # written by scripts/roadmap_model/build.py


def check_model_sources(root, html, err):
    """BOM coverage, one model source for both 3D pages, sensor and upper-body positions against the source snapshot
    (sensor_frames.yaml, datums.yaml, section B), the design heights, cable endpoints, partner terms."""
    mdir = os.path.join(root, "model")
    # robot.html and exploded.html load the same model files
    srcs = {}
    for p in ("robot.html", "exploded.html"):
        srcs[p] = {s for s in re.findall(r'<script src="([^"]+)"', html[p]) if s.startswith("model/") and "store" not in s}
    if srcs["robot.html"] != srcs["exploded.html"]:
        err("model", "robot.html and exploded.html load different model sources: %s / %s" % (sorted(srcs["robot.html"]), sorted(srcs["exploded.html"])))
    # partner terms and em dashes in the visible text and scripts (fonts and base64 stripped)
    for p, h in html.items():
        t = re.sub(r"[A-Za-z0-9+/=.]{60,}", "", re.sub(r"data:[^)\"']+", "", h))
        m = PARTNER_TERMS.search(t)
        if m:
            err(p, "names %s (Use Case 1 partner and upstream cooperation are not published)" % m.group(0))
        if "\u2014" in t:
            err(p, "contains an em dash")
    try:
        snap = json.load(open(os.path.join(root, SOURCE_SNAPSHOT), encoding="utf-8"))
        place = json.load(open(os.path.join(mdir, "placement.json"), encoding="utf-8"))
        with open(os.path.join(mdir, "base_glb.js"), encoding="utf-8") as f:
            payload = f.read()
        with open(os.path.join(mdir, "model.js"), encoding="utf-8") as f:
            js = f.read()
    except (OSError, ValueError) as e:
        err("model", "source snapshot: %s" % e)
        return
    # GLB node boxes (base_footprint)
    m = re.search(r'window\.BASE_GLB="([^"]+)"', payload)
    raw = base64.b64decode(m.group(1).replace(".", ""))
    jl = struct.unpack("<I", raw[12:16])[0]
    doc = json.loads(raw[20:20 + jl])
    blz = snap["base_link_z"]
    boxes = {}
    for n in doc["nodes"]:
        if "mesh" not in n:
            continue
        lo, hi = [9] * 3, [-9] * 3
        for pr in doc["meshes"][n["mesh"]]["primitives"]:
            a = doc["accessors"][pr["attributes"]["POSITION"]]
            lo = [min(x, y) for x, y in zip(lo, a["min"])]
            hi = [max(x, y) for x, y in zip(hi, a["max"])]
        boxes[(n.get("extras") or {}).get("id", n.get("name"))] = ([lo[0], lo[1], lo[2] + blz], [hi[0], hi[1], hi[2] + blz])
    # B1 (2 Nov 2026): rubber drive wheels r 0.100 on the axle at 0.098: wheel-to-floor overlap up to 2 mm is an intended contact
    for node in ("hub_motor_wheel_left", "hub_motor_wheel_right"):
        if node in boxes and boxes[node][0][2] < -WHEEL_COMPRESSION_M - 1e-4:
            err("model", "%s reaches %.1f mm below the floor: more than the intended %.0f mm tyre compression" % (node, -boxes[node][0][2] * 1000, WHEEL_COMPRESSION_M * 1000))
    tol = 0.001
    for e in sensor_pose_errors(snap, glb_vertices(payload, blz), upper_body_sensor_poses(js, os.path.join(mdir, "combined_robot.urdf"))):
        err("model", e)
    # upper body: model.js values against datums.yaml (snapshot)
    chest = json.loads(re.search(r"/\*CHEST-JSON\*/(.*?)/\*CHEST-JSON-END\*/", js).group(1))
    lift = json.loads(re.search(r"/\*LIFT-JSON\*/(.*?)/\*LIFT-JSON-END\*/", js).group(1))
    dm = snap["datums"]
    oc = snap.get("owner_corrections") or {}   # A3 / A4 / A5 of 2 Nov 2026 (to be entered in P-03 and M-01) override these datums
    pairs = [("lift_stop_sensor_z_l1000", lift["z"][0]), ("lift_stop_sensor_z_l1175", lift["z"][1]), ("lift_stop_sensor_z_l1350", lift["z"][2]),
             ("lift_stop_sensor_face_x", lift["face_x"]), ("lift_flag_below_plate", lift["flag_below_plate"]), ("lift_flag_gap", lift["gap"]),
             ("lift_flag_rod_length", lift["rod"]["len"]), ("lift_flag_rod_offset_from_face", lift["rod"]["off"])]
    for k, v in pairs:
        if k in dm and abs(float(dm[k]) - float(v)) > tol:
            err("model", "upper-body item %s: model %.4f, datums.yaml %.4f (more than 1 mm)" % (k, v, dm[k]))
    gs, hs = chest["drawn"]["getac_tablet"]["size"], chest["drawn"]["head_light"]["size"]
    if oc:
        want_z = float(dm["getac_tablet_z_above_column_top"]) - oc["getac_lower_by"]
        if abs(chest["drawn"]["getac_tablet"]["z"] - want_z) > tol:
            err("model", "Getac centre %.4f above the column top, A3 gives %.4f (datum minus 40 mm)" % (chest["drawn"]["getac_tablet"]["z"], want_z))
        if any(abs(a - b) > tol for a, b in zip(oc["getac_size"], gs)):
            err("model", "Getac size %s, A3 gives the portrait %s" % (gs, oc["getac_size"]))
        if abs(chest["gap_light_tablet"] - oc["light_gap"]) > tol:
            err("model", "head light gap %.3f, A3 gives %.3f" % (chest["gap_light_tablet"], oc["light_gap"]))
    else:
        err("model", "source_snapshot.json has no owner_corrections (rerun build.py)")
    if "head_light_size" in dm and any(abs(a - b) > tol for a, b in zip(dm["head_light_size"], hs)):
        err("model", "upper-body item head_light_size: model %s, datums.yaml %s" % (hs, dm["head_light_size"]))
    light_z = chest["drawn"]["getac_tablet"]["z"] - gs[2] / 2 - chest["gap_light_tablet"] - hs[2] / 2
    if abs(light_z - chest["drawn"]["head_light"]["z"]) > tol:
        err("model", "head light height %.4f is not %.0f mm below the Getac (%.4f)" % (chest["drawn"]["head_light"]["z"], chest["gap_light_tablet"] * 1000, light_z))
    # design heights (section B)
    dims = re.search(r"M\.DIMS = \{(.*?)\};", js, re.S).group(1)
    num = lambda key: float(re.search(r"\b%s: ([-\d.]+)" % key, dims).group(1))
    top = num("PLATE_TOP") + float(re.search(r"RETRACTED: ([\d.]+)", dims).group(1))
    sh = top + num("MOUNT_ABOVE_COL")
    checks = [("us_* z", snap["sensor_frames"]["us_front_left"][2], .0914), ("imu_link z", snap["sensor_frames"]["imu_link"][2], .21904),
              ("LiDAR scan plane", num("LIDAR_Z"), .22205), ("shoulder L1000", sh, 1.0), ("shoulder L1175", sh + .175, 1.175),
              ("shoulder L1350", sh + .35, 1.35), ("head lens L1000", sh + num("ZED_ABOVE_SH"), 1.223), ("head lens ahead of J1_A", num("ZED_X") - num("MOUNT_X"), (snap.get("owner_corrections") or {}).get("zed_ahead_of_j1a", .057))]
    for name, got, want in checks:
        if abs(got - want) > 0.0005:
            err("model", "%s is %.5f m, design value %.5f m" % (name, got, want))
    # BOM coverage: every onboard BOM 7.14 line, model quantity equals BOM quantity when drawn
    parts = embedded(html["hardware.html"], "PARTS")
    bom = {k: v for k, v in parts.items() if re.match(r"^[A-Z]+(?:-[A-Z0-9]+)+$", k)}
    try:
        with open(os.path.join(mdir, "bom_coverage.csv"), encoding="utf-8") as f:
            cov = {r["id"]: r for r in csv.DictReader(f)}
    except OSError:
        err("model", "bom_coverage.csv missing")
        return
    for k, v in bom.items():
        r = cov.get(k)
        if not r:
            err("bom_coverage.csv", "BOM 7.14 line %s is missing" % k)
            continue
        if r["onboard"] == "y" and r["drawn"] == "y" and r["model_qty"] != v.get("Qty", "") and str(v.get("Qty", "")).strip().isdigit():
            err("bom_coverage.csv", "%s: model quantity %s, BOM quantity %s" % (k, r["model_qty"], v.get("Qty")))
        if r["onboard"] == "y" and r["drawn"] == "n" and not r["reason_not_drawn"]:
            err("bom_coverage.csv", "%s is onboard, not drawn and gives no reason" % k)
    for k in cov:
        if k not in bom:
            err("bom_coverage.csv", "%s is not a BOM 7.14 line" % k)
    # base GLB nodes moved by the default front bay option (placement.json front_bay.relocate, model.js M.setFrontBay)
    fbay = place.get("front_bay") or {}
    for k, r in ((fbay.get("relocate") or {}).get(fbay.get("default")) or {}).items():
        if k in boxes:
            lo, hi = boxes[k]
            e = [(hi[i] - lo[i]) / 2 for i in range(3)]
            if abs(abs(r["yaw"]) - 1.5708) < 0.01:
                e = [e[1], e[0], e[2]]
            c = [r["p"][0], r["p"][1], r["p"][2] + blz]
            boxes[k] = ([c[i] - e[i] for i in range(3)], [c[i] + e[i] for i in range(3)])
    # cable endpoints attach to drawn parts
    drawn = set(boxes)
    for c in model_components(js):
        drawn.update(c.get("nodes", []) + c.get("parts", []) + [c["id"]])
    drawn.update(["openarm_left", "openarm_right"])
    with open(os.path.join(mdir, "cable_list.csv"), encoding="utf-8") as f:
        for r in csv.DictReader(f):
            if not r["route_length_m"]:
                continue
            for end in ("from_part", "to_part"):
                if r[end] not in drawn:
                    err("cable_list.csv", "%s %s %s is not a drawn part" % (r["id"], end, r[end]))
            for end, xyz in (("from_part", r["from_xyz"]), ("to_part", r["to_xyz"])):
                b = boxes.get(r[end])
                if b and xyz:
                    p = json.loads(xyz)
                    if not all(b[0][i] - .015 <= p[i] <= b[1][i] + .015 for i in range(3)):
                        err("cable_list.csv", "%s %s end %s is more than 15 mm from %s" % (r["id"], end, p, r[end]))

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dir", default=os.path.join(os.path.dirname(__file__), "..", "docs", "assets", "roadmap"))
    ap.add_argument("--today", action="store_true", help="require the snapshot date to be today's date")
    args = ap.parse_args()
    errors = []

    def err(page, msg):
        errors.append("%s: %s" % (page, msg))

    global PLACEMENT
    try:
        with open(os.path.join(args.dir, "model", "placement.json"), encoding="utf-8") as f:
            PLACEMENT = json.load(f)
    except (OSError, ValueError) as e:
        err("model", "placement.json: %s" % e)
    html, trees = {}, {}
    for p in PAGES:
        try:
            with open(os.path.join(args.dir, p), encoding="utf-8") as f:
                html[p] = f.read()
        except OSError:
            print("Roadmap check failed:\n  ERROR: %s: page missing" % p)
            sys.exit(1)
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

    # 1b. navigation and the shared model of the robot and exploded-view pages
    for p in PAGES:
        check_nav(p, html[p], err)
    check_model(args.dir, html["exploded.html"], err)
    check_model_sources(args.dir, html, err)
    check_shared(args.dir, html, err)
    check_no_light_strips(args.dir, err)
    check_no_duplicate_fittings(args.dir, html, err)
    check_store_video_text(args.dir, html, err)
    with open(os.path.join(args.dir, "model", "model.js"), encoding="utf-8") as f:
        comps = model_components(f.read())
    check_chest_and_riser(args.dir, html, err, comps)
    check_sync_audit(args.dir, err, comps)
    check_store_media(args.dir, html, err)

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
    texts = dict(html)
    for name in ("model/model.js", "model/look.js", "model/finish.json", "model/exploded.json"):  # shared model text
        try:
            with open(os.path.join(args.dir, name), encoding="utf-8") as f:
                texts[name] = f.read()
        except OSError:
            err(name, "missing")
    for p, t in texts.items():
        if p == "robot.html":  # the minified store application and mesh data are not page content
            t = re.sub(r"<script>window\.OPENARM=.*?</script>", "", t, flags=re.S)
            t = re.sub(r"<script>\(\(\)=>\{var jn=window\.THREE.*?</script>", "", t, flags=re.S)
        t = re.sub(r"url\(data:[^)]*\)", "", t)
        for label, rx in FORBIDDEN + [("private term", r) for _, r in priv]:
            for m in rx.finditer(t):
                ctx = t[max(0, m.start() - 40):m.end() + 40].replace("\n", " ")
                err(p, "%s: ...%s..." % (label, ctx if label != "private term" else hashlib.sha256(m.group(0).encode()).hexdigest()[:12]))
                break

    # 5b. every external link of the six pages (outside scripts) opens in a new tab: target="_blank" rel="noopener"
    for p in PAGES:
        t = re.sub(r"<script\b.*?</script>", "", html[p], flags=re.S)
        for a_ in re.findall(r"<a\s[^>]*>", t):
            if 'href="http' in a_ and ('target="_blank"' not in a_ or 'rel="noopener"' not in a_):
                err(p, "external link without target=\"_blank\" rel=\"noopener\": %s" % a_[:120])
                break

    # 6. known contacts (declared overlaps, warn only in the model, recorded as issues)
    check_known_contacts(args.dir, err)

    # 7. STATE.md figures (read from the generated files)
    try:
        with open(os.path.join(args.dir, "..", "..", "..", "STATE.md"), encoding="utf-8") as f:
            for e in state_errors(f.read(), state_figures(args.dir), next(iter(alld)) if len(alld) == 1 else None):
                err("STATE.md", e)
    except OSError:
        err("STATE.md", "missing")

    if errors:
        print("Roadmap check failed:")
        for e in errors:
            print("  ERROR: " + e)
        sys.exit(1)
    print("Roadmap check passed: %d pages, snapshot %s." % (len(PAGES), next(iter(alld))))


if __name__ == "__main__":
    main()
