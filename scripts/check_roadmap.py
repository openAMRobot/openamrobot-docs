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
ROBOT_FIRST_LOAD_MAX_BYTES = 4093278 + 100 * 1024  # #58 first load (page, scripts, finish.json) plus 100 KB
TOUR_SECONDS = (40.0, 50.0)
EXPLODED_FIRST_LOAD_MAX_BYTES = 4 * 1000 * 1000  # page, scripts, exploded.json and video posters; not the videos
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


def model_components(js):
    """COMPONENTS registry of model/model.js (the JSON between its markers)."""
    m = re.search(r"/\*COMPONENTS-JSON\*/(.*?)/\*COMPONENTS-JSON-END\*/", js, flags=re.S)
    if not m:
        raise ValueError("model.js has no COMPONENTS-JSON block")
    return json.loads(m.group(1))


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
    first = size + os.path.getsize(os.path.join(mdir, "exploded.json"))
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


# P-03 rev20.0 item 24, layout update of 28 Oct 2026: the second E-stop (formerly the chest E-stop) on the rear
# face of the static DOLD lift profile, close to its upper edge; the moving chest bottom up: head light, then
# the Getac, the head light top edge 30 mm below the Getac bottom edge.
CHEST_ORDER = ["head_light", "getac_tablet"]
CHEST_IDS = ["second_estop"] + CHEST_ORDER
LIGHT_TABLET_GAP = 0.03
# P-03 rev20.0 item 24, 28 Oct 2026 correction: Getac ZX80 234 x 149.8 x 17.6 mm mounted landscape (x depth 17.6,
# y across 234, z height 149.8); Falcon FLDL-i150x15-W housing 158 x 17 x 20 mm
CHEST_SIZES = {"getac_tablet": [0.0176, 0.234, 0.1498], "head_light": [0.02, 0.158, 0.017]}
# the replaced Getac ZX10 (275 x 192 x 17.9 mm) must not come back in the model or the robot and exploded pages
CHEST_RETIRED = [r"ZX10", r"275 x 192", r"0\.275, 0\.192", r"17\.9 mm", r"(?i)portrait", r"chest_estop"]
# head camera (P-03 rev20.0 items 15, 17 and 18, 28 Oct 2026): lens 42 mm ahead of the shoulder, baseline hp30
HEAD_PITCH_BASELINE = 30
ZED_X = 0.222


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
        for pat in CHEST_RETIRED:
            if re.search(pat, text):
                err(name, "names a replaced chest layout item (%s): the tablet is the Getac ZX80 mounted landscape and "
                    "the second E-stop (second_estop) is on the static lift profile (P-03 rev20.0 item 24)" % pat)
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
    se = chest.get("second_estop") or {}
    if not 0.02 <= se.get("below_top", -1) <= 0.06:  # centre 20 to 60 mm below the static profile top
        err("model.js", "M.CHEST second_estop below_top %s: the second E-stop sits close to the static profile upper edge" % se.get("below_top"))
    if len(re.findall(r"part\('second_estop', R\.col\)", js)) != 1 or re.search(r"part\('second_estop'\)", js):
        err("model.js", "the second E-stop must be built exactly once, in the static lift group (part('second_estop', R.col))")
    fm = re.search(r"function chestItems\s*\(", js)
    body = function_body(js, fm.end()) if fm else ""
    if fm and not ("-D.COL.L / 2" in body and "rotation.z = Math.PI" in body):
        err("model.js", "chestItems must put the second E-stop on the rear face of the static profile (x -COL.L/2), facing rearward")
    for fn in ("columnFittings", "chassisFittings"):
        fm2 = re.search(r"function %s\s*\(" % fn, js)
        if fm2 and re.search(r"\bmats\.(red|yellow)\b", function_body(js, fm2.end())):
            err("model.js", "%s draws an E-stop (red or yellow); E-stops come from the GLB and chestItems" % fn)
    if not fm:
        err("model.js", "chestItems not found")
    elif re.search(r"emissive|Light\(", body):
        err("model.js", "chestItems gives the head light a glow or a light source")
    # Build option chestPlaceholders: on (default) all three items, off the second E-stop only. The exploded
    # view keeps it on; the robot page store scene turns it off until work package M-09 sets the positions.
    fm = re.search(r"function chestItems\s*\(THREE, R, mov, mats, (\w+)\)\s*\{", js)
    if not fm:
        err("model.js", "chestItems takes no chestPlaceholders flag (THREE, R, mov, mats, all)")
    else:
        b = function_body(js, fm.end() - 1)
        cut = re.search(r"if \(!%s\) return out;" % fm.group(1), b)
        pos = {cid: b.find("part('%s'" % cid) for cid in CHEST_IDS}
        if not cut or not (0 <= pos["second_estop"] < cut.start() < min(pos["getac_tablet"], pos["head_light"])):
            err("model.js", "chestItems must draw the second E-stop first and stop before the Getac and head light "
                "when chestPlaceholders is off")
    if "chestItems(THREE, R, mov, mats, o.chestPlaceholders !== false)" not in js:
        err("model.js", "M.build does not pass chestPlaceholders (default on) to chestItems")
    builds = {page: re.findall(r"MODEL\.build\(\w+,\s*(\{[^}]*\})\)", html[page]) for page in ("robot.html", "exploded.html")}
    off = lambda a: re.search(r"chestPlaceholders\s*:\s*(!1|false)\b", a) is not None
    if not builds["exploded.html"] or any(off(a) or "chestPlaceholders" in a for a in builds["exploded.html"]):
        err("exploded.html", "the exploded view must build the model with all three chest items (chestPlaceholders on)")
    if len(builds["robot.html"]) != 1 or not off(builds["robot.html"][0]):
        err("robot.html", "the store scene must build the model with chestPlaceholders off (second E-stop only, no tablet "
            "or head light until work package M-09)")
    if "not shown in this store scene until work package M-09" not in html["robot.html"]:
        err("robot.html", "the page does not state that the Getac and head light are not shown until work package M-09")
    # Head camera baseline hp30 and lens 42 mm ahead of the shoulder (P-03 rev20.0 items 15, 17 and 18)
    pitch = lambda a: (re.search(r"headPitch\s*:\s*(\d+)", a) or [None, None])[1]
    for page in ("robot.html", "exploded.html"):
        if not builds[page] or any(pitch(a) != str(HEAD_PITCH_BASELINE) for a in builds[page]):
            err(page, "the shared model must be built with headPitch %d (hp30 baseline)" % HEAD_PITCH_BASELINE)
    if "o.headPitch === undefined ? %d : o.headPitch" % HEAD_PITCH_BASELINE not in js:
        err("model.js", "M.build default head pitch is not the hp30 baseline")
    zm = re.search(r"ZED_X:\s*([\d.]+)", js)
    if not zm or abs(float(zm.group(1)) - ZED_X) > 1e-6:
        err("model.js", "M.DIMS.ZED_X %s, expected %.3f (lens 42 mm ahead of the shoulder)" % (zm and zm.group(1), ZED_X))
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
    first = len(h.encode("utf-8")) + os.path.getsize(os.path.join(root, "model", "finish.json"))
    for src in re.findall(r'<script src="([^"]+)"', h) + re.findall(r'<video\b[^>]*\bposter="([^"]+)"', h):
        first += os.path.getsize(os.path.join(root, src)) if os.path.isfile(os.path.join(root, src)) else 0
    for tag in re.findall(r"<img\b[^>]*>", strip_scripts(h)):
        m = re.search(r'src="([^"]+)"', tag)
        if m and 'loading="lazy"' not in tag and not m.group(1).startswith("data:") and os.path.isfile(os.path.join(root, m.group(1))):
            first += os.path.getsize(os.path.join(root, m.group(1)))
    if first > ROBOT_FIRST_LOAD_MAX_BYTES:
        err("robot.html", "first load %d bytes, over %d (#58 plus 100 KB)" % (first, ROBOT_FIRST_LOAD_MAX_BYTES))


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
    check_shared(args.dir, html, err)
    check_no_light_strips(args.dir, err)
    check_no_duplicate_fittings(args.dir, html, err)
    with open(os.path.join(args.dir, "model", "model.js"), encoding="utf-8") as f:
        check_chest_and_riser(args.dir, html, err, model_components(f.read()))
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

    if errors:
        print("Roadmap check failed:")
        for e in errors:
            print("  ERROR: " + e)
        sys.exit(1)
    print("Roadmap check passed: %d pages, snapshot %s." % (len(PAGES), next(iter(alld))))


if __name__ == "__main__":
    main()
