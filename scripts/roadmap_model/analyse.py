#!/usr/bin/env python3
"""Geometry and hardware analysis of the OpenAMRobot 2.0 roadmap model (section G2 of the 2 Nov 2026 update).

Rebuilds the scene of model/model.js in Python (base GLB, upper-body primitives, chest and lift-sensor items,
model/placement.json, OpenArm 2.0 kinematics from model/openarm.js), checks it against a dump of the page
scene (scene_dump.js, same part boxes within 0.5 mm), then analyses:
  interference (all part pairs, lift L1000 / L1175 / L1350, bp000 / bp050, hp15 to hp35, both Getac positions,
  arms in the upstream home pose), arm reach (joint by joint through the URDF limits, 10 deg steps, L1000 and
  L1350), sensor views (Gemini 336L and ZED Mini frustums, LiDAR scan plane +-5 mm), mass and stability, the
  TZBOT receiver, service access and the K1/K2 fit.
Writes model/geometry_issues.csv and scripts/roadmap_model/analysis_summary.json.
Usage: python3 scripts/roadmap_model/analyse.py [--dump scene_dump.json]
"""
import argparse
import base64
import csv
import json
import math
import os
import re

import numpy as np
from scipy.spatial import cKDTree

from frames import FACTS, HERE, MODEL, REPO, datums, glb_nodes, lift_rear_layout, load_yaml, sensor_frames, tzbot_layout

OWN = {"mech": "fridayali", "elec": "evans-kwashie", "lead": "BotshareAI", "nav": "skunal3318", "manip": "Brinex45",
       "perc": "vineethmanthena", "tech": "panthera-momagdii"}


def issue_key(r):
    """Registry key of an issue: kind|parts, with the part lists that change from run to run stripped."""
    p = re.sub(r" \(nearest [^)]*\)", "", r["parts"])
    for pre in ("Front bay and rear zone layout /", "Front bay overflow /", "Rear zone layout (B5) /"):
        if p.startswith(pre):
            p = pre[:-2]
    return "%s|%s" % (r["kind"], p)


# ---------------------------------------------------------------- primitives
def box_mesh(s, p, rot=None):
    sx, sy, sz = np.array(s) / 2
    v = np.array([[x, y, z] for x in (-sx, sx) for y in (-sy, sy) for z in (-sz, sz)])
    f = np.array([[0, 1, 3], [0, 3, 2], [4, 6, 7], [4, 7, 5], [0, 4, 5], [0, 5, 1], [2, 3, 7], [2, 7, 6], [0, 2, 6], [0, 6, 4], [1, 5, 7], [1, 7, 3]])
    if rot is not None:
        v = v @ rot.T
    return v + p, f


def cyl_mesh(r, h, p, ax, n=16):
    a = np.linspace(0, 2 * np.pi, n, endpoint=False)
    ring = np.stack([r * np.cos(a), r * np.sin(a)], 1)
    v = np.vstack([np.c_[ring, np.full(n, -h / 2)], np.c_[ring, np.full(n, h / 2)], [[0, 0, -h / 2], [0, 0, h / 2]]])
    f = []
    for i in range(n):
        j = (i + 1) % n
        f += [[i, j, n + j], [i, n + j, n + i], [2 * n, j, i], [2 * n + 1, n + i, n + j]]
    if ax == "x":
        v = v[:, [2, 1, 0]]
    elif ax == "y":
        v = v[:, [0, 2, 1]]
    return v + p, np.array(f)


def tube_mesh(pts, r):
    vs, fs, off = [], [], 0
    for a, b in zip(pts[:-1], pts[1:]):
        a, b = np.array(a), np.array(b)
        d = b - a
        L = np.linalg.norm(d)
        if L < 1e-6:
            continue
        v, f = cyl_mesh(r, L, [0, 0, 0], "z", 8)
        z = d / L
        x = np.cross(z, [0, 0, 1] if abs(z[2]) < .9 else [1, 0, 0])
        x /= np.linalg.norm(x)
        y = np.cross(z, x)
        v = v @ np.stack([x, y, z], 1).T + (a + b) / 2
        vs.append(v)
        fs.append(f + off)
        off += len(v)
    return np.vstack(vs), np.vstack(fs)


def rpy_matrix(e):  # three.js Euler order 'ZYX' : Rz * Ry * Rx
    rx, ry, rz = e
    cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
    return np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])


def axis_angle(ax, q):
    ax = np.array(ax, float) / np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    return np.eye(3) + math.sin(q) * K + (1 - math.cos(q)) * K @ K


def T(Rm=None, p=(0, 0, 0)):
    M = np.eye(4)
    if Rm is not None:
        M[:3, :3] = Rm
    M[:3, 3] = p
    return M


class Part:
    def __init__(self, pid, v, f, group, cid=None, boxes=None):
        self.id, self.v0, self.f, self.group, self.cid = pid, np.asarray(v, float), np.asarray(f), group, cid or pid
        self.boxes = boxes  # axis-aligned boxes [(lo, hi)] when the part is made of them only (exact tests)

    def world(self, cfg):
        v = self.v0.copy()
        if self.group in ("col", "mov"):
            v[:, 0] += FACTS["lift_plate"]["col_axis_x"][cfg["bp"]]
        if self.group == "mov":
            v[:, 2] += cfg["travel"]
        return v


# ---------------------------------------------------------------- scene
def model_js():
    s = open(os.path.join(MODEL, "model.js"), encoding="utf-8").read()
    chest = json.loads(re.search(r"/\*CHEST-JSON\*/(.*?)/\*CHEST-JSON-END\*/", s).group(1))
    lift = json.loads(re.search(r"/\*LIFT-JSON\*/(.*?)/\*LIFT-JSON-END\*/", s).group(1))
    comps = json.loads(re.search(r"/\*COMPONENTS-JSON\*/(.*?)/\*COMPONENTS-JSON-END\*/", s, re.S).group(1))
    return chest, lift, comps


def relocated(v, k, P, option=None):
    """Base GLB node vertices moved by a front bay option (model.js M.setFrontBay): yaw about the node centre, then translation."""
    F = P.get("front_bay") or {}
    r = ((F.get("relocate") or {}).get(option or F.get("default")) or {}).get(k)
    if not r:
        return v
    c = np.array(F["glb_centre"][k]) + [0, 0, FACTS["base_link_z"]]
    Rz = rpy_matrix([0, 0, r["yaw"]])
    return (v - c) @ Rz.T + np.array(r["p"]) + [0, 0, FACTS["base_link_z"]]


def build_scene(G, P, chest, lift, head_pitch=30, option=None):
    """Parts of the robot (the page scene) except the arms; the front bay option shown (default: the proposed one)."""
    parts = []
    opt = option or (P.get("front_bay") or {}).get("default")
    for k, n in G.items():
        if k in (P.get("hide_glb") or []):
            continue   # replaced GLB nodes (A1: the single-row battery envelope), hidden on both pages
        env = n["extras"].get("class") == "envelope"  # envelopes are boxes by definition: exact tests on their bounds
        v = relocated(n["v"], k, P, opt)
        parts.append(Part(k, v, n["f"], "base", boxes=[(v.min(0), v.max(0))] if env else None))
    t, L, Wc, RET = .304, .24, .06, .53
    COLF = FACTS["column"]   # DOLD STEP (owner, 8 Nov 2026): foot, static profile to 503 + 2 mm cover, inner stage 209.5 x 53.3 x 470
    c = t + RET
    MOUNT_X, PX, PY, PL = .18, .12, .06, .34
    def add(pid, vf, g, exact=True):
        v = np.asarray(vf[0])
        parts.append(Part(pid, v, vf[1], g, boxes=[(v.min(0), v.max(0))] if (exact and len(v) == 8) else None))
    add("lift_column_foot", box_mesh(COLF["foot"], [0, 0, t + COLF["foot"][2] / 2]), "col")
    add("lift_column", box_mesh([L, Wc, COLF["static_top"] - COLF["static_bottom"]], [0, 0, t + (COLF["static_top"] + COLF["static_bottom"]) / 2]), "col")
    add("lift_column_stage", box_mesh(COLF["inner"], [0, 0, c - COLF["inner"][2] / 2]), "mov")
    d, p = lift["plate_rear_x"], MOUNT_X + PX / 2   # A6: one-piece plate with the rear extension
    add("adapter_plate", box_mesh([p - d, .1, .01], [(d + p) / 2, 0, c + .005]), "mov")
    f = c + .01
    add("arm_profile", box_mesh([PX, PY, PL], [MOUNT_X, 0, f + PL / 2]), "mov")
    m = c + .166 + .223
    y = f + PL
    ZED_X = .18 + FACTS["zed_ahead_of_j1a"]  # owner decision 8 Nov 2026: lens 60 mm ahead of J1_A
    add("head_camera_bracket", box_mesh([.03, .03, m - y], [ZED_X - .03, 0, (y + m) / 2]), "mov")
    Rz = rpy_matrix([0, math.radians(head_pitch), 0])
    v, ff = box_mesh([.0265, .1245, .0305], np.array([0, 0, 0]))
    v = (v + [-.013, 0, 0]) @ Rz.T + [ZED_X, 0, m]
    add("head_camera", (v, ff), "mov", exact=False)
    # chest: second E-stop (copy of the GLB estop node), Getac, head light
    e = chest["second_estop"]
    ev = G["estop"]["v"] - [0, 0, FACTS["base_link_z"]]
    ax = e["glb_axis"]
    ev = ev - [ax[0], ax[1], ax[2]]   # panel face at the origin, button axis +x
    # A5 (2 Nov 2026): on the adapter plate top behind the post, above the column axis, button up (pitch -pi/2), moving group
    ev = ev @ rpy_matrix([0, -math.pi / 2, 0]).T + [0, 0, c + .01 + e["panel_above_plate"]]
    add("second_estop", (ev, G["estop"]["f"]), "mov", exact=False)
    C = chest["drawn"]
    fr = MOUNT_X + PX / 2
    ts = C["getac_tablet"]["size"]
    add("getac_tablet", box_mesh(ts, [fr + ts[0] / 2, 0, c + C["getac_tablet"]["z"]]), "mov")
    hs = C["head_light"]["size"]
    add("head_light", box_mesh(hs, [fr + hs[0] / 2, 0, c + C["head_light"]["z"]]), "mov")
    # lift sensors (A6: rear face of the static column, axes along y; the same values as model.js liftSensors)
    s = lift["sensor"]
    b = lift["bracket"]
    for k, dz in enumerate(lift["z"]):
        add("lift_stop_sensor_%d" % (k + 1), cyl_mesh(s["d"] / 2, s["len"], [lift["axis_x"], lift["face_y"] - s["len"] / 2, t + dz], "y"), "col")
        add("lift_sensor_bracket_%d" % (k + 1), box_mesh([b["t"], b["leg"], lift["bracket_h"]], [lift["rear_x"] - b["t"] / 2, -b["leg"] / 2, t + dz]), "col")
        add("lift_sensor_bracket_leg_%d" % (k + 1), box_mesh([b["leg"], b["t"], lift["bracket_h"]], [lift["rear_x"] - b["leg"] / 2, -b["t"] / 2, t + dz]), "col")
    r = lift["rod"]
    rx, ry = sum(lift["rod_x"]) / 2, sum(lift["rod_y"]) / 2
    add("flag_rod", box_mesh([r["w"], r["w"], r["len"]], [rx, ry, c - r["len"] / 2]), "mov")
    cl = lift["corner_x"][1] - lift["corner_x"][0]
    add("rod_corner_bracket", box_mesh([cl, r["w"], cl], [sum(lift["corner_x"]) / 2, ry, c - cl / 2]), "mov")
    fl = lift["flag"]
    add("lift_flag", box_mesh(fl, [sum(lift["flag_x"]) / 2, sum(lift["flag_y"]) / 2, c - lift["flag_below_plate"]]), "mov")
    # placement parts
    info = {}
    for cc in P["components"]:
        for pp in cc["parts"]:
            info[pp] = cc["id"]
    for pid, e in P["geometry"].items():
        if e.get("option") and e["option"] != opt:
            continue
        vs, fs, off, bx, allbox = [], [], 0, [], True
        for q in e["prims"]:
            if q["t"] == "box" and not q.get("r"):
                bx.append((np.array(q["p"]) - np.array(q["s"]) / 2, np.array(q["p"]) + np.array(q["s"]) / 2))
            else:
                allbox = False
            if q["t"] == "box":
                v, ff = box_mesh(q["s"], q["p"], rpy_matrix(q["r"]) if q.get("r") else None)
            elif q["t"] == "cyl":
                v, ff = cyl_mesh(q["r"], q["h"], q["p"], q["ax"])
            elif q["t"] == "tube":
                v, ff = tube_mesh(q["pts"], q["r"])
            else:
                v, ff = np.array(q["v"]).reshape(-1, 3), np.array(q["f"]).reshape(-1, 3)
            vs.append(v)
            fs.append(ff + off)
            off += len(v)
        parts.append(Part(pid, np.vstack(vs), np.vstack(fs), e["group"], info.get(pid), boxes=bx if (allbox and bx) else None))
    # lift energy chain links: model.js chainLinks + M.setChain draw them at build time for the lift travel 0 (L1000);
    # add the same link boxes here so the Python scene equals the page scene (self-check). The chain changes shape with
    # the travel; its clearance over the stroke is checked by harness.py energy_chain() at the three lift stops.
    E = P.get("energy_chain")
    ch = next((q for q in parts if E and q.id == E.get("part")), None)
    if ch is not None:
        vs, fs, off = [ch.v0], [ch.f], len(ch.v0)
        for v, ff in chain_link_meshes(E, 0.0):
            vs.append(v)
            fs.append(ff + off)
            off += len(v)
        ch.v0, ch.f, ch.boxes = np.vstack(vs), np.vstack(fs), None
    return parts


def chain_link_meshes(E, T):
    """Link boxes of the lift energy chain for the lift travel T, as model.js M.setChain places them (col group frame)."""
    zc = (E["fixed_z"] + E["moving_z0"] + T + math.pi * E["R"] - E["length"]) / 2
    a, b = E["fixed_z"] - zc, math.pi * E["R"]
    out = []
    for i in range(int(round(E["length"] / E["pitch"]))):
        s = (i + .5) * E["pitch"]
        if s < a:
            y, z, th = E["y_fixed"], E["fixed_z"] - s, -math.pi / 2
        elif s < a + b:
            th = math.pi + (s - a) / E["R"]
            y, z = E["R"] * math.cos(th), zc + E["R"] * math.sin(th)
            th += math.pi / 2
        else:
            y, z, th = E["y_moving"], zc + s - a - b, math.pi / 2
        out.append(box_mesh([E["outer_w"], E["pitch"] * .92, E["outer_h"]], [E["x"], y, z], rpy_matrix([th, 0, 0])))
    return out


def arm_parts(side, q, grip, sh, bpx):
    """OpenArm links in the robot frame (the same forward kinematics as M.poseArm in model.js)."""
    s = open(os.path.join(MODEL, "openarm.js"), encoding="utf-8").read()
    A = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
    a, meshes = A["arms"][side], A["meshes"]

    def mesh(vis, M):
        if not vis or vis["key"] not in meshes:
            return None
        e = meshes[vis["key"]]
        pos = np.frombuffer(base64.b64decode(e["pos"]), dtype="<i2").reshape(-1, 3) * e["q"]
        V = (pos * vis["scale"]) @ rpy_matrix(vis["rpy"]).T + vis["xyz"]
        V = V @ M[:3, :3].T + M[:3, 3]
        return V, np.arange(len(V)).reshape(-1, 3)

    l = T(None, [bpx, 0, sh]) @ T(rpy_matrix(a["mount"]["rpy"]), [.18, a["mount"]["xyz"][1], 0])
    out = []
    m0 = mesh(a["base_visual"], l)
    if m0:
        out.append(Part("arm_%s_base" % side, m0[0], m0[1], "world"))
    for i, j in enumerate(a["joints"]):
        l = l @ T(rpy_matrix(j["rpy"]), j["xyz"]) @ T(axis_angle(j["axis"], q[i]))
        mm = mesh(j["visual"], l)
        if mm:
            out.append(Part("arm_%s_link%d" % (side, i + 1), mm[0], mm[1], "world"))
    for k, fg in enumerate(a["fingers"]):
        lim = fg["lo"] if abs(fg["lo"]) > abs(fg["hi"]) else fg["hi"]
        M = l @ T(rpy_matrix(fg["rpy"]), fg["xyz"]) @ T(axis_angle(fg["axis"], lim * grip))
        mm = mesh(fg["visual"], M)
        if mm:
            out.append(Part("arm_%s_finger%d" % (side, k + 1), mm[0], mm[1], "world"))
    return out, a


# ---------------------------------------------------------------- geometry tests
def surface_samples(v, f, step):
    tri = v[f]
    e = np.maximum.reduce([np.linalg.norm(tri[:, 1] - tri[:, 0], axis=1), np.linalg.norm(tri[:, 2] - tri[:, 0], axis=1),
                           np.linalg.norm(tri[:, 2] - tri[:, 1], axis=1)])
    n = np.ceil(e / step).astype(int).clip(1, 60)
    out = [v]
    for k in np.unique(n):
        if k < 2:
            continue
        sel = tri[n == k]
        a, b = np.meshgrid(np.arange(k + 1), np.arange(k + 1))
        mk = (a + b) <= k
        a, b = a[mk] / k, b[mk] / k
        out.append((sel[:, None, 0] + a[None, :, None] * (sel[:, None, 1] - sel[:, None, 0]) + b[None, :, None] * (sel[:, None, 2] - sel[:, None, 0])).reshape(-1, 3))
    return np.vstack(out)


def inside(points, v, f):
    """Parity test along +z (works for closed meshes); points: (n, 3)."""
    if len(points) == 0:
        return np.zeros(0, bool)
    tri = v[f]
    res = np.zeros(len(points), int)
    lo, hi = tri.min(1), tri.max(1)
    for s in range(0, len(points), 2000):
        P = points[s:s + 2000]
        m = (P[:, None, 0] >= lo[None, :, 0]) & (P[:, None, 0] <= hi[None, :, 0]) & (P[:, None, 1] >= lo[None, :, 1]) & (P[:, None, 1] <= hi[None, :, 1]) & (P[:, None, 2] <= hi[None, :, 2])
        ii, jj = np.nonzero(m)
        if len(ii) == 0:
            continue
        A, B, C = tri[jj, 0], tri[jj, 1], tri[jj, 2]
        p = P[ii]
        d = (B[:, 1] - C[:, 1]) * (A[:, 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (A[:, 1] - C[:, 1])
        ok = np.abs(d) > 1e-14
        l1 = ((B[:, 1] - C[:, 1]) * (p[:, 0] - C[:, 0]) + (C[:, 0] - B[:, 0]) * (p[:, 1] - C[:, 1])) / np.where(ok, d, 1)
        l2 = ((C[:, 1] - A[:, 1]) * (p[:, 0] - C[:, 0]) + (A[:, 0] - C[:, 0]) * (p[:, 1] - C[:, 1])) / np.where(ok, d, 1)
        l3 = 1 - l1 - l2
        hit = ok & (l1 >= 0) & (l2 >= 0) & (l3 >= 0)
        z = l1 * A[:, 2] + l2 * B[:, 2] + l3 * C[:, 2]
        hit &= z > p[:, 2]
        np.add.at(res, s + ii[hit], 1)
    return res % 2 == 1


class Geo:
    def __init__(self, part, cfg, step):
        self.v = part.world(cfg)
        self.boxes = None
        if part.boxes:
            sh = self.v.min(0) - part.v0.min(0)
            self.boxes = [(lo + sh, hi + sh) for lo, hi in part.boxes]
        self.f = part.f
        self.lo, self.hi = self.v.min(0), self.v.max(0)
        self.step = step
        self._s = None

    @property
    def samples(self):
        if self._s is None:
            self._s = surface_samples(self.v, self.f, self.step)
            self._tree = cKDTree(self._s)
        return self._s

    @property
    def tree(self):
        self.samples
        return self._tree


def pair(a, b, margin=0.005):
    """(min clearance m, penetration depth m) of two parts; None when farther than margin. Exact for two
    box-only parts; otherwise surface samples (2 mm, refined to 0.75 mm near contact) with a parity test."""
    if ((a.lo - margin) > b.hi).any() or ((b.lo - margin) > a.hi).any():
        return None
    if a.boxes and b.boxes:
        dmin, depth = 1.0, 0.0
        for alo, ahi in a.boxes:
            for blo, bhi in b.boxes:
                ov = np.minimum(ahi, bhi) - np.maximum(alo, blo)
                if (ov > 0).all():
                    depth = max(depth, float(ov.min()))
                    dmin = 0.0
                else:
                    gap = np.maximum(0, np.maximum(alo, blo) - np.minimum(ahi, bhi))
                    dmin = min(dmin, float(np.linalg.norm(gap)))
        return (dmin, depth) if (dmin < margin or depth > 0) else None
    lo = np.maximum(a.lo, b.lo) - margin
    hi = np.minimum(a.hi, b.hi) + margin
    sa = a.samples[((a.samples >= lo) & (a.samples <= hi)).all(1)]
    sa = sa[np.random.default_rng(0).permutation(len(sa))] if len(sa) > 4000 else sa
    sb = b.samples[((b.samples >= lo) & (b.samples <= hi)).all(1)]
    if len(sa) == 0 or len(sb) == 0:
        return None
    d, _ = cKDTree(sb).query(sa, distance_upper_bound=margin + .002)
    dmin = float(np.min(d)) if np.isfinite(d).any() else 1.0
    depth = 0.0
    if dmin < 0.0025 and a.step > .001:
        fa, fb = Geo.__new__(Geo), Geo.__new__(Geo)
        for g0, g1 in ((a, fa), (b, fb)):
            g1.v, g1.f, g1.lo, g1.hi, g1.step, g1._s, g1.boxes = g0.v, g0.f, g0.lo, g0.hi, .00075, None, None
        return pair(fa, fb, margin)
    if dmin < 0.0025:
        ins = inside(sa[:4000], b.v, b.f)
        if ins.any():
            dd, _ = cKDTree(sb).query(sa[:4000][ins])
            depth = max(depth, float(dd.max()) - .0006)
        ins2 = inside(sb[:4000], a.v, a.f)
        if ins2.any():
            dd, _ = cKDTree(sa).query(sb[:4000][ins2])
            depth = max(depth, float(dd.max()) - .0006)
    return dmin, depth


# ---------------------------------------------------------------- main
def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump", default=None)
    args = ap.parse_args()
    rev, D = datums()
    SF = sensor_frames()
    G = glb_nodes()
    P = json.load(open(os.path.join(MODEL, "placement.json")))
    chest, lift, reg = model_js()
    summ = json.load(open(os.path.join(HERE, "build_summary.json")))
    issues = []

    def issue(sev, parts, cfg, meas, limit, src, fix, owner, kind):
        issues.append({"severity": sev, "kind": kind, "parts": parts, "configuration": cfg, "measured": meas, "limit": limit,
                       "source": src, "suggested_fix": fix, "owner": owner})

    base_cfg = {"bp": "bp000", "travel": 0.0}
    scene = build_scene(G, P, chest, lift)
    names = {p.id: p for p in scene}
    # ---- self-check against the page dump
    check = {}
    if args.dump and os.path.exists(args.dump):
        dump = json.load(open(args.dump))["parts"]
        dev = []
        for pid, (mn, mx) in dump.items():
            if pid in names and pid not in ("lift_column", "arm_profile"):  # composite groups on the page (static + moving stage, slot strips)
                v = names[pid].world(base_cfg)
                dev.append((pid, float(max(np.abs(v.min(0) - mn).max(), np.abs(v.max(0) - mx).max()))))
        dev.sort(key=lambda x: -x[1])
        check = {"compared": len(dev), "max_dev_mm": round(dev[0][1] * 1000, 3) if dev else None, "worst": dev[:5]}
        print("self-check vs page:", check["compared"], "parts, max deviation %.3f mm" % (check["max_dev_mm"] or 0), dev[:3])

    # ---- frame checks (sensors vs sensor_frames.yaml, upper body vs datums.yaml)
    up = P["upper_body"]
    frames = {}
    for k, nid in [("imu_link", "imu"), ("lidar_link", "lidar"), ("base_camera_link", "base_camera")]:
        lo, hi = names[nid].v0.min(0), names[nid].v0.max(0)
        frames[k] = {"frame": [round(x, 4) for x in SF[k]["xyz"]], "node_box": [lo.round(4).tolist(), hi.round(4).tolist()]}
    heights = {"us_z_mm": round(SF["us_front_left"]["xyz"][2] * 1000, 2), "imu_z_mm": round(SF["imu_link"]["xyz"][2] * 1000, 2),
               "lidar_link_z_mm": round(SF["lidar_link"]["xyz"][2] * 1000, 2), "scan_plane_mm": FACTS["lidar_scan_plane"] * 1000,
               "shoulder_mm": {k: round((up["col_top"] + .166 + tr) * 1000, 1) for k, tr in (("L1000", 0), ("L1175", .175), ("L1350", .35))},
               "head_lens_L1000_mm": round(up["head_lens"][2] * 1000, 1)}

    # ---- interference: all pairs at the base configuration
    declared = [("base_plate", "*"), ("support_", "*"), ("side_panel", "*"), ("front_panel", "*"), ("rear_panel", "*"), ("cover", "*"),
                ("centre_bracket", "*"), ("bay_plate", "bay_"), ("bay_plate", "fasteners"), ("rear_plate", "rz_"), ("lift_base_plate", "lift_column"),
                ("lift_base_plate", "fasteners"), ("lift_column", "lift_column"), ("lift_column", "second_estop"), ("lift_column", "lift_sensor"),
                ("lift_column", "rear_estop"), ("lift_column_stage", "adapter_plate"), ("adapter_plate", "arm_profile"), ("adapter_plate", "flag_rod"), ("rod_corner_bracket", "adapter_plate"), ("rod_corner_bracket", "flag_rod"), ("rod_corner_bracket", "fasteners"), ("battery_series_link", "rz_batcon"),
                ("arm_profile", "head_camera_bracket"), ("head_camera_bracket", "head_camera"), ("arm_profile", "getac"), ("arm_profile", "head_light"),
                ("arm_profile", "fasteners"), ("adapter_plate", "fasteners"), ("lift_sensor", "lift_stop"), ("lift_sensor", "fasteners"),
                ("lift_stop", "lift_sensor"), ("harness", "*"), ("lift_energy_chain", "*"), ("wheel_guard", "side_panel"), ("dp_lift", "*"), ("keepout", "*"), ("can_term", "*"), ("lidar", "lidar_"),
                ("camera_mount", "base_camera"), ("ultrasonic", "ultrasonic"), ("tof", "tof"), ("ultrasonic", "us_locknut"), ("compute", "electronics_bracket"),
                ("controller_plate", "*"), ("base_controller", "controller_plate"), ("imu", "electronics_bracket"), ("motor_driver", "driver_mount"),
                ("battery", "battery_tray"), ("hub_motor", "motor_brackets"), ("castor", "shims"), ("getac", "getac_"), ("head_light", "getac_pocket"),
                ("getac_second_position_ghost", "*"), ("rear_estop_clear_ghost", "*"), ("k1k2_option_b", "*"), ("tz_receiver", "*"), ("tz_receiver_frame", "*"), ("estop", "front_panel"),
                ("reset_button", "front_panel"), ("feedthru", "side_panel"), ("rz_disc", "rear_panel"), ("rz_sb50", "rear_panel"), ("fasteners", "*"),
                ("harness_fittings", "*"), ("shims", "*"), ("us_locknut", "*"), ("lift_bolt_keepout", "*"),
                ("lift_sensor_bracket", "lift_sensor_bracket"), ("flag_rod", "lift_flag"), ("rear_estop_housing", "second_estop"),
                ("bay_plate", "lidar_support"), ("lift_base_plate", "lift_node"), ("lift_column_stage", "lift_column"), ("lift_column_foot", "lift_column"), ("lift_column_foot", "lift_base_plate"), ("lift_column_head", "lift_column"),
                ("lift_column_stage", "arm_profile"), ("rear_estop", "lift_column"),
                # 2 Nov 2026: plate on the arch, E-stop P2 on the post, receiver set, ghosts, raised bay plate (its CAD conflicts are issues below)
                ("lift_base_plate", "centre_bracket"), ("second_estop", "arm_profile"), ("rear_estop_housing", "arm_profile"), ("rear_estop_housing", "second_estop"),
                ("estop_p", "*"), ("tz_", "*"), ("base_cutout", "*"), ("rear_estop_housing", "second_estop"), ("rear_estop_housing", "adapter_plate"),
                ("second_estop", "adapter_plate"), ("battery_cells", "battery_tray"), ("battery_series_link", "battery_"), ("rear_plate", "rz_"), ("battery_cells", "harness"), ("bay_plate", "lidar_support"), ("bay_plate", "electronics_bracket"),
                ("bay_plate", "compute"), ("bay_plate", "base_controller"), ("lift_node", "lift_column"),
                ("bay_", "electronics_bracket"), ("compute", "electronics_bracket"), ("base_controller", "controller_plate"),  # bracket shortening: own issue
                # mounting contacts of the 3 Nov 2026 layout (rear_power.py, front_bay.py side plates, harness.py channels, flag_guide.py)
                ("rp_fbb_shelf", "rz_fbb"), ("rp_fba_shelf", "rz_fba"), ("rp_bus_standoffs", "rz_pwr017_1"), ("rp_bus_standoffs", "rear_plate"),
                ("rp_bms_bracket", "rz_bms"), ("rp_busn_bracket", "rz_pwr017_2"), ("rp_corner_plate_l", "rz_"), ("side_plates", "bay_"),
                ("side_plates", "castor_"), ("ch_branch", "ch_central"), ("ch_branch", "wheel_guard"), ("flag_rod_guide", "flag_rod"),
                ("flag_rod_guide", "lift_column")]

    def is_declared(a, b):
        for x, y in declared:
            for p, q in ((a, b), (b, a)):
                if p.startswith(x) and (y == "*" or q.startswith(y)):
                    return True
        return False

    geos = {p.id: Geo(p, base_cfg, .002) for p in scene}
    ids = sorted(geos)
    hits = []
    for i, a in enumerate(ids):
        for b in ids[i + 1:]:
            if is_declared(a, b):
                continue
            r = pair(geos[a], geos[b])
            if r is None:
                continue
            dmin, depth = r
            if depth > .0005:
                hits.append((a, b, "overlap", depth))
            elif dmin < .005:
                hits.append((a, b, "clearance", dmin))
    # receiver and option-B ghosts reported separately
    pairhits = {}
    for a, b, k, val in hits:
        pairhits[(a, b)] = {"kind": k, "val": val, "cfgs": ["L1000 bp000"]}
    for a, b, k, val in []:
        sev = "major" if (k == "overlap" and val > .002) else "minor"
        if k == "overlap" and any(x.startswith(("lift_", "flag", "adapter", "arm_", "getac", "head_", "second")) for x in (a, b)):
            sev = "major"
        issue(sev, "%s / %s" % (a, b), "L1000, bp000, hp30, portrait", ("overlap %.1f mm" if k == "overlap" else "clearance %.1f mm") % (val * 1000),
              "overlap <= 0.5 mm, clearance >= 5 mm", "roadmap model scene (placement.json, GLB, datums.yaml)",
              "move or resize one part; check against CAD", OWN["mech"], "interference")
    # lift positions and bp050: pairs with moving / lift parts
    for bp in ("bp000", "bp050"):
        for tr, nm in ((0.0, "L1000"), (.175, "L1175"), (.35, "L1350")):
            if bp == "bp000" and tr == 0:
                continue
            cfg = {"bp": bp, "travel": tr}
            gm = {p.id: Geo(p, cfg, .003) for p in scene if p.group in ("col", "mov")}
            gb = {p.id: geos[p.id] for p in scene if p.group == "base"}
            for a in gm:
                for b in list(gb) + [x for x in gm if x > a]:
                    if is_declared(a, b):
                        continue
                    r = pair(gm[a], gm.get(b) or gb[b])
                    if r and (r[1] > .0005 or r[0] < .005):
                        key = (a, b) if (a, b) in pairhits or (b, a) not in pairhits else (b, a)
                        e = pairhits.setdefault(key, {"kind": "overlap" if r[1] > .0005 else "clearance", "val": 0, "cfgs": []})
                        if r[1] > .0005:
                            e["kind"] = "overlap"
                            e["val"] = max(e["val"], r[1])
                        elif e["kind"] == "clearance":
                            e["val"] = min(e["val"] or 1, r[0])
                        e["cfgs"].append("%s %s" % (nm, bp))
    for (a, b), e in sorted(pairhits.items()):
        k, val = e["kind"], e["val"]
        sev = "major" if (k == "overlap" and val > .002) else "minor"
        if k == "overlap" and any(x.startswith(("lift_", "flag", "adapter", "arm_", "getac", "head_", "second")) for x in (a, b)):
            sev = "major"
        cf = e["cfgs"]
        issue(sev, "%s / %s" % (a, b), ", ".join(cf) if len(cf) < 6 else "all lift positions (L1000 / L1175 / L1350) at bp000 and bp050",
              ("overlap %.1f mm" if k == "overlap" else "clearance %.1f mm") % (val * 1000),
              "overlap <= 0.5 mm, clearance >= 5 mm", "roadmap model scene (placement.json, GLB, datums.yaml)",
              "move or resize one part; check against CAD", OWN["mech"], "interference")
    # lift base plate on the arch (B3): the load check follows the mass roll-up below

    # ---- head pitch and Getac positions
    for hp in range(15, 40, 5):
        sc = build_scene(G, P, chest, lift, hp)
        cam = [p for p in sc if p.id == "head_camera"][0]
        gc = Geo(cam, base_cfg, .002)
        for other in ("head_camera_bracket", "arm_profile", "getac_tablet", "getac_pocket"):
            if other in geos:
                r = pair(gc, geos[other])
                if r and r[1] > .0005 and other != "head_camera_bracket":
                    issue("major", "head_camera / %s" % other, "hp%02d" % hp, "overlap %.1f mm" % (r[1] * 1000), "overlap <= 0.5 mm", "datums.yaml head camera", "check the pitch bracket", OWN["mech"], "interference")
    # Getac portrait (A3, decided default) against the post, the light bar, the ZED and the arms in the page pose
    getac_check = {}
    pose = {"left": [.25, -.12, 0, 1.9, 0, -.78, 0]}
    pose["right"] = [-q if i not in (3,) else q for i, q in enumerate(pose["left"])]
    armp = []
    for side in ("left", "right"):
        armp += arm_parts(side, pose[side], .6, up["col_top"] + .166, .06)[0]
    for gid in ("getac_tablet", "getac_pocket"):
        if gid not in geos:
            continue
        for other in ["head_light", "head_camera", "head_camera_bracket", "arm_profile"] + [p_.id for p_ in armp]:
            go = geos.get(other) or Geo([p_ for p_ in armp if p_.id == other][0], {"bp": "bp000", "travel": 0}, .003)
            if (gid, other) in (("getac_pocket", "arm_profile"), ("getac_pocket", "head_light"), ("getac_tablet", "arm_profile")):
                continue   # declared mounting contacts (pocket back plate on the post, light plate under the pocket)
            r = pair(geos[gid], go)
            getac_check["%s / %s" % (gid, other)] = None if r is None else [round(r[0] * 1000, 1), round(r[1] * 1000, 1)]
            if r and (r[1] > .0005 or r[0] < .005):
                issue("major" if r[1] > .0005 else "minor", "Getac ZX80 portrait / %s" % other, "portrait (A3), L1000, arms in the page pose",
                      ("overlap %.1f mm" % (r[1] * 1000)) if r[1] > .0005 else ("clearance %.1f mm" % (r[0] * 1000)), "overlap <= 0.5 mm, clearance >= 5 mm",
                      "owner correction A3 (2 Nov 2026), design_intent/getac_pocket.step", "check at M-09", OWN["mech"], "interference")

    # ---- arm reach sweep (owner correction A5): only physically valid poses. Each joint moves out from the upstream home
    # pose (all joints 0) in 10 deg steps in both directions, inside the URDF joint limits; the motion stops at the first
    # pose with a self-collision (non-adjacent links of the same arm, or the other arm at home) or a contact with the robot
    # body. Only the contacts of that first contact pose are reported: poses beyond it cannot be reached and are not counted.
    sweep, stops = {}, {}
    targets = {k: geos[k] for k in ("getac_tablet", "head_light", "head_camera", "head_camera_bracket", "second_estop", "flag_rod", "arm_profile",
                                    "getac_pocket", "lift_flag", "adapter_plate", "lift_column", "rear_estop_housing", "cover") if k in geos}
    def link_geos(side, q, tr):
        ps, a_ = arm_parts(side, q, .6, up["col_top"] + .166 + tr, .06)
        return [(lp.id, Geo(lp, {"bp": "bp000", "travel": 0}, .006)) for lp in ps if not lp.id.endswith("_base")], a_
    def adjacent(a_, b_):
        ia, ib = a_[1], b_[1]   # list order: link1..link7 (0..6), finger1, finger2 (7, 8); the fingers sit on the gripper on link7
        return abs(ia - ib) <= 1 or (ia >= 6 and ib >= 6)
    nposes = 0
    for tr, nm in ((0.0, "L1000"), (.35, "L1350")):
        cfg = {"bp": "bp000", "travel": tr}
        tg = {k: Geo(names[k], cfg, .004) for k in targets}
        for side in ("left", "right"):
            other = "right" if side == "left" else "left"
            og, _ = link_geos(other, [0.0] * 7, tr)
            home = [0.0] * 7
            hg, a = link_geos(side, home, tr)
            idx = {lid: i_ for i_, (lid, _) in enumerate(hg)}
            def self_pairs(lg):
                out = set()
                for x in range(len(lg)):
                    for y in range(x + 1, len(lg)):
                        if adjacent((lg[x][0], x), (lg[y][0], y)):
                            continue
                        r = pair(lg[x][1], lg[y][1], .001)
                        if r and r[1] > .002:
                            out.add((lg[x][0], lg[y][0]))
                    for oid, o in og:
                        r = pair(lg[x][1], o, .001)
                        if r and r[1] > .002:
                            out.add((lg[x][0], oid))
                return out
            def body_hits(lg):
                out = []
                for lid, g in lg:
                    for k, gt in tg.items():
                        if k == "arm_profile" and lid.endswith("link1"):
                            continue   # the arm mount on the post
                        r = pair(g, gt, .002)
                        if r and (r[1] > .001 or r[0] < .0015):
                            out.append((k, lid))
                return out
            base_self, base_body = self_pairs(hg), {k for k, _ in body_hits(hg)}   # contacts already at home: mounting contacts, not motion results
            for j in range(7):
                lo, hi = a["joints"][j]["lo"], a["joints"][j]["hi"]
                for sgn in (1, -1):
                    q = 0.0
                    while True:
                        q += sgn * math.radians(10)
                        if q > hi + 1e-6 or q < lo - 1e-6:
                            break
                        qq = list(home)
                        qq[j] = q
                        lg, _ = link_geos(side, qq, tr)
                        nposes += 1
                        sp = self_pairs(lg) - base_self
                        bh = [(k, lid) for k, lid in body_hits(lg) if k not in base_body]
                        if bh:
                            for k, lid in bh:
                                sweep.setdefault((nm, side, k), []).append((j + 1, round(math.degrees(q)), lid))
                        if sp or bh:
                            stops[(nm, side, j + 1, sgn)] = {"deg": round(math.degrees(q)), "self": sorted(sp), "body": sorted({k for k, _ in bh})}
                            break
    nsteps = nposes
    for (nm, side, k), lst in sorted(sweep.items()):
        js = sorted({x[0] for x in lst})
        issue("major" if k in ("getac_tablet", "head_light", "head_camera", "second_estop", "getac_pocket") else "minor",
              "OpenArm %s / %s" % (side, k), "%s, valid single-joint motion from the upstream home pose (all joints 0), 10 deg steps, stops at the first contact" % nm,
              "first contact on %s (%s)" % (", ".join("J%d at %+d deg" % (x[0], x[1]) for x in sorted(set((x[0], x[1]) for x in lst))), ", ".join(sorted({x[2] for x in lst}))),
              "no contact inside the joint limits, or a software keep-out", "openarm_description 14ff67b limits; datums.yaml positions; valid poses only (A5)",
              "add a MoveIt collision object and joint-limit keep-out for this item", OWN["manip"], "arm reach")

    # ---- sensor views
    views = {}
    def frustum(origin, fwd, up_, hfov, vfov, rng, skip, res=1.0):
        """Parts the camera sees first (depth buffer on a res-degree grid of directions)."""
        fwd = np.array(fwd) / np.linalg.norm(fwd)
        upv = np.array(up_) - np.dot(up_, fwd) * fwd
        upv /= np.linalg.norm(upv)
        rt = np.cross(fwd, upv)
        best = {}
        for k, g in geos.items():
            if any(k.startswith(s) for s in skip):
                continue
            sm = g.samples
            dd = sm - origin
            z = dd @ fwd
            m = (z > .01) & (np.linalg.norm(dd, axis=1) < rng)
            if not m.any():
                continue
            az = np.degrees(np.arctan2(dd[m] @ rt, z[m]))
            el = np.degrees(np.arctan2(dd[m] @ upv, z[m]))
            ok = (np.abs(az) < hfov / 2) & (np.abs(el) < vfov / 2)
            if not ok.any():
                continue
            r = np.linalg.norm(dd[m][ok], axis=1)
            for i, j, rr in zip(np.floor(az[ok] / res).astype(int), np.floor(el[ok] / res).astype(int), r):
                if rr < best.get((i, j), (9, None))[0]:
                    best[(i, j)] = (rr, k)
        cnt = {}
        for (i, j), (rr, k) in best.items():
            c = cnt.setdefault(k, [0, 9, -9, 9, -9, 9])
            c[0] += 1
            c[1], c[2], c[3], c[4] = min(c[1], i * res), max(c[2], (i + 1) * res), min(c[3], j * res), max(c[4], (j + 1) * res)
            c[5] = min(c[5], rr)
        return sorted(((k, v[0], v[1:5], round(v[5], 3)) for k, v in cnt.items()), key=lambda x: -x[1])
    gm = SF["base_camera_link"]
    pitch = gm["rpy"][1]
    fwd = [math.cos(pitch), 0, -math.sin(pitch)]
    views["gemini_336L_bt10"] = frustum(np.array(gm["xyz"]) + [.004, 0, 0], fwd, [0, 0, 1], 90, 65, 3.0, ("base_camera", "camera_mount", "keepout", "lift_bolt", "tz_receiver"))
    hpp = math.radians(30)
    views["zed_mini_hp30"] = frustum(np.array(up["head_lens"]) + [.002, 0, 0], [math.cos(hpp), 0, -math.sin(hpp)], [0, 0, 1], 90, 60, 3.0,
                                     ("head_camera", "keepout", "lift_bolt", "getac_portrait", "rear_estop_clear", "k1k2_option"))
    for k, lst in views.items():
        for pid, n, ext, rmin in lst:
            sev = "minor"
            if "zed" in k and pid.startswith(("getac", "head_light", "harness", "service")):
                sev = "major"
            issue(sev, "%s view / %s" % (k.split("_")[0], pid), k,
                  "first hit in %d of the 1 deg view cells, azimuth %.0f to %.0f, elevation %.0f to %.0f deg, nearest %.0f mm" % (n, ext[0], ext[1], ext[2], ext[3], rmin * 1000),
                  "no robot part in the view unless declared (arms in the ZED view are expected)", "datasheet FOV (Gemini 336L 90 x 65 deg, ZED Mini 90 x 60 deg, verify), 3 m range",
                  "mask in perception or move the part", OWN["perc"], "sensor view")
    # LiDAR plane +-5 mm: first hit per 1 deg bearing at three heights
    zc = FACTS["lidar_scan_plane"]
    lid = np.array(SF["lidar_link"]["xyz"])
    first = {}
    for k, g in geos.items():
        if k == "lidar" or k.startswith(("keepout", "lift_bolt", "k1k2_option", "rear_estop_clear", "getac_portrait")):
            continue
        sm = g.samples
        m = (np.abs(sm[:, 2] - zc) < .005)
        if not m.any():
            continue
        d2 = sm[m, :2] - lid[:2]
        rr = np.linalg.norm(d2, axis=1)
        ok = rr > .04
        brg = np.floor(np.degrees(np.arctan2(d2[ok, 1], d2[ok, 0]))).astype(int)
        for bb, r0 in zip(brg, rr[ok]):
            if r0 < first.get(bb, (9, None))[0]:
                first[bb] = (r0, k)
    plane = {}
    for bb, (r0, k) in first.items():
        e = plane.setdefault(k, [0, 999, -999, 9])
        e[0] += 1
        e[1], e[2], e[3] = min(e[1], bb), max(e[2], bb + 1), min(e[3], r0)
    views["lidar_plane"] = sorted(([k] + v for k, v in plane.items()), key=lambda x: -x[1])
    # open sector: the front half (+-95 deg); behind that the plane is inside the cover (closed sector, masked by the body filter)
    front = {}
    for bb, (r0, k) in first.items():
        if -95 <= bb < 95:
            e = front.setdefault(k, [0, 999, -999, 9])
            e[0] += 1
            e[1], e[2], e[3] = min(e[1], bb), max(e[2], bb + 1), min(e[3], r0)
    views["lidar_plane_open_sector"] = sorted(([k] + v for k, v in front.items()), key=lambda x: -x[1])
    closed = sorted({k for bb, (r0, k) in first.items() if not -95 <= bb < 95})
    issue("minor", "LiDAR closed rear sector (inside the cover)", "scan plane 222.05 mm", "first hits behind +-95 deg: %s" % ", ".join(closed),
          "masked by the scan body filter", "sensor_frames.yaml lidar_link; B7", "keep the body filter mask for the rear sector", OWN["nav"], "sensor view")
    for k, n, a0, a1, r0 in views["lidar_plane_open_sector"]:
        masked = k.startswith(("support_front", "front_panel", "cover", "lidar_s"))
        issue("minor" if masked else "major", "LiDAR scan plane +-5 mm / %s" % k, "scan plane 222.05 mm, bp000, L1000",
              "first hit in %d of 360 bearings (%d to %d deg, x forward = 0), nearest %.0f mm" % (n, a0, a1, r0 * 1000),
              "only the masked side supports inside the open sector", "sensor_frames.yaml lidar_link; B7 scan body filter", 
              "covered by the scan body filter or outside the open sector: confirm the mask" if masked else "extend the body filter or move the part out of the plane",
              OWN["nav"], "sensor view")

    # ---- mass and stability
    MASS_SAME_PART = {"UI-002": "MEC-012"}   # BOM 7.14 lists the Getac portrait mount twice (MEC-012 adapter, UI-002 mount, same 0.461 kg part)
    cov = list(csv.DictReader(open(os.path.join(MODEL, "bom_coverage.csv"))))
    mass_items = []
    for r in cov:
        try:
            m = float(r["mass_kg"])
        except ValueError:
            continue
        if r["onboard"] == "y" and m > 0:
            if r["id"] in MASS_SAME_PART and any(x[0] == MASS_SAME_PART[r["id"]] for x in mass_items):
                continue   # the same physical part as an earlier BOM line: counted once (8 Nov 2026)
            mass_items.append((r["id"], m, r["model_component"]))
    # MEC-001 from CAD volume
    def vol(v, f):
        tri = v[f]
        return abs(np.einsum("ij,ij->i", tri[:, 0], np.cross(tri[:, 1], tri[:, 2])).sum() / 6)
    steel = 0
    for k in ("base_plate", "front_panel", "rear_panel", "side_panel_left", "side_panel_right", "support_front_left", "support_front_right",
              "support_rear_left", "support_rear_right", "centre_bracket", "cover", "cover_flange_front", "cover_flange_rear"):
        steel += vol(G[k]["v"], G[k]["f"]) * 7850
    mass_items = [x for x in mass_items if x[0] != "MEC-001"] + [("MEC-001", steel, "chassis")]
    # COM: place each mass at its part centroid
    cen = {}
    for p in scene:
        cen[p.id] = p.world(base_cfg).mean(0)
    def part_centre(comp, tr):
        ids = [x.strip() for x in str(comp).split(",")]
        pts = []
        for pid in ids:
            for p in scene:
                if p.id == pid or p.cid == pid or p.id.startswith(pid + "_"):
                    w = p.world({"bp": "bp000", "travel": tr if p.group == "mov" else 0})
                    pts.append((w.min(0) + w.max(0)) / 2)   # box centre (8 Nov 2026: the vertex mean put the cells 66 mm high)
        return np.mean(pts, 0) if pts else None
    res = {}
    placed_mass = {}
    for tr, nm in ((0.0, "L1000"), (.35, "L1350")):
        tot, mom, unplaced = 0, np.zeros(3), []
        placed_mass[nm] = []
        for bid, m, comp in mass_items:
            c = None
            if comp.startswith("inside:"):
                comp = comp[7:]
            if bid == "ARM-001":
                c = np.array([up["shoulder"][0] + .12, 0, up["col_top"] + .166 + tr - .25])
            elif bid == "MEC-018":
                c = np.array([.06, 0, .304 + .53 / 2 + tr * .3])
            elif comp == "harness":
                c = np.array([0, 0, .2])
            elif comp == "chassis":
                c = np.array([0, 0, .15])
            else:
                c = part_centre(comp, tr)
            if c is None:
                unplaced.append(bid)
                c = np.array([0, 0, .2])
            placed_mass[nm].append((bid, float(m), [round(float(x), 4) for x in c], comp))
            tot += m
            mom += m * c
        com = mom / tot
        res[nm] = {"mass": tot, "com": com.round(4).tolist(), "unplaced": unplaced}
    # support polygon: castor contacts and wheel contacts
    wy = FACTS["track"] / 2
    cast = [(.27505, .215), (.27505, -.215), (-.27495, .215), (-.27495, -.215)]
    poly = [(.27505, .215), (.27505, -.215), (-.27495, -.215), (-.27495, .215)]
    stab = {}
    for nm, r in res.items():
        cx, cy, cz = r["com"]
        mx = min(.27505 - cx, cx + .27495)
        my = min(.215 - abs(cy), .215 + abs(cy))
        margin = min(mx, my)
        stab[nm] = {"margin_fore_m": round(.27505 - cx, 4), "margin_aft_m": round(cx + .27495, 4), "margin_lat_m": round(.215 - abs(cy), 4),
                    "a_max_fore": round(9.81 * (.27505 - cx) / cz, 2), "a_max_lat": round(9.81 * (.215 - abs(cy)) / cz, 2), "com_z": cz}
    # rigid castors and wheels, no suspension: statically indeterminate; split by a beam model on x (wheels at x 0)
    loads = {}
    for nm, r in res.items():
        m, cx = r["mass"], r["com"][0]
        # assume 6 supports; drive wheels carry the share given by the lever rule between front and rear castor rows with wheels at the centre
        front = m * max(cx, 0) / .27505 * .5
        rear = m * max(-cx, 0) / .27495 * .5
        wheels = m - front - rear
        loads[nm] = {"drive_pair_kg": round(wheels, 1), "per_drive_wheel_kg": round(wheels / 2, 1), "per_castor_front_kg": round(front / 2, 1),
                     "per_castor_rear_kg": round(rear / 2, 1), "assumption": "rigid castors and wheels on a flat floor share by the lever rule with the drive axle carrying the centre share (upper bound for the drive pair); real split depends on shims MEC-016"}
    stop = 1.5 ** 2 / (2 * min(s["a_max_fore"] for s in stab.values()))
    issue("major" if res["L1350"]["mass"] > FACTS["mass_cap"] else "minor", "Total mass", "L1000 and L1350",
          "%.1f kg (onboard coverage roll-up; MEC-001 from CAD volume, steel)" % res["L1000"]["mass"], "<= 120 kg (B7)", "bom_coverage.csv masses",
          "weigh the parts; replace the estimates", OWN["lead"], "mass")
    for nm, s in stab.items():
        sev = "major" if min(s["a_max_fore"], s["a_max_lat"]) < 2.0 else "minor"
        issue(sev, "Static stability", nm, "COM %s; margins fore %.0f / aft %.0f / lateral %.0f mm; a_max fore %.2f m/s2, lateral %.2f m/s2" % (
            res[nm]["com"], s["margin_fore_m"] * 1000, s["margin_aft_m"] * 1000, s["margin_lat_m"] * 1000, s["a_max_fore"], s["a_max_lat"]),
              "a_max >= deceleration needed (1.5 m/s to 0)", "castor contacts M.DIMS CASTER; COM roll-up",
              "limit deceleration in the controller to below a_max at L1350, or lower the COM", OWN["nav"], "stability")
    a_need = 1.5 ** 2 / (2 * .5)  # stop within 0.5 m
    issue("major" if stab["L1350"]["a_max_fore"] < a_need else "minor", "Stopping from 1.5 m/s", "L1350",
          "a_max fore %.2f m/s2 gives a stopping distance of at least %.2f m without tip-over" % (stab["L1350"]["a_max_fore"], 1.5 ** 2 / (2 * stab["L1350"]["a_max_fore"])),
          "stop from 1.5 m/s within 0.5 m needs %.2f m/s2" % a_need, "software speed ceiling 1.5 m/s (B7)", "cap deceleration and speed with the lift raised; E-stop braking (6 Nm brakes) must not exceed a_max", OWN["nav"], "stability")
    for nm, l in loads.items():
        issue("major" if l["drive_pair_kg"] > FACTS["motor_pair_rating"] else "minor", "Drive wheel load", nm,
              "drive pair %.1f kg (%.1f kg per wheel), castors front %.1f / rear %.1f kg each" % (l["drive_pair_kg"], l["per_drive_wheel_kg"], l["per_castor_front_kg"], l["per_castor_rear_kg"]),
              "ZLTECH rating 120 kg per motor pair", "lever-rule split, rigid supports", "set the castor shims (MEC-016) so the drive wheels keep traction without overload", OWN["mech"], "mass")

    # ---- lift base plate on the arch (B3): load check (lift_plate_check.py)
    import lift_plate_check as LPC
    lp = FACTS["lift_plate"]
    above = {}
    for nm in ("L1000", "L1350"):
        sel = [(m, np.array(c)) for bid, m, c, comp in placed_mass[nm] if c[2] > lp["top"] + 0.001 and bid != "MEC-019"]
        mt = sum(m for m, _ in sel)
        above[nm] = (mt, (sum(m * c for m, c in sel) / mt).tolist())
    arm_m = sum(m for bid, m, c, comp in placed_mass["L1350"] if bid == "ARM-001")
    sh = np.array([up["shoulder"][0], 0, up["col_top"] + .166 + .35])
    sel = [(m, np.array(c)) for bid, m, c, comp in placed_mass["L1350"] if c[2] > lp["top"] + 0.001 and bid not in ("MEC-019", "ARM-001")]
    sel += [(arm_m, sh + [0.606 / 2, 0, 0]), (2 * 4.1, sh + [0.606, 0, 0])]
    m_af = sum(m for m, _ in sel)
    arms_fwd = (m_af, (sum(m * c for m, c in sel) / m_af).tolist())
    decel = stab["L1350"]["a_max_fore"]
    plate = LPC.run(lp, {k: (v[0], v[1]) for k, v in above.items()}, decel, arms_fwd)
    plate["above_plate"] = {k: {"mass_kg": round(v[0], 2), "com_m": [round(x, 4) for x in v[1]]} for k, v in above.items()}
    plate["arms_forward"] = {"mass_kg": round(arms_fwd[0], 2), "com_m": [round(x, 4) for x in arms_fwd[1]], "arm_mass_kg_both": round(arm_m, 2),
                             "payload_kg_each": 4.1, "reach_m": 0.606, "source": "OpenArm 2.0 figures used by the robot page (payload 4.1 kg nominal, 6 kg peak, reach 0.606 m)"}
    plate["decel_m_s2"] = decel
    mu = plate["max_utilisation"]
    margin_ok = max(mu.values()) <= 0.67
    w = plate["worst"]
    wc = [c for c in plate["cases"] if c["case"] + " (" + c["bp"] + ")" == w][0]
    # decided fix (owner decision 8 Nov 2026, from the A7 options of 2 Nov): M8 8.8 through-bolts with nuts and a backing plate under the
    # arch top sheet. Screening: sheet and backing plate as two stacked plates sharing the bending moment by t^3 (no composite action),
    # so the sheet keeps t_s^3 / (t_s^3 + t_b^3) of it; the rivet-nut pull-through no longer applies (nut and backing plate).
    fix = FACTS.get("arch_fix", {"backing_t": 0.005, "backing_material": "S235JR"})
    ts_, tb_ = FACTS["arch"]["sheet"], fix["backing_t"]
    share_s = ts_ ** 3 / (ts_ ** 3 + tb_ ** 3)
    u_sheet_fix = mu["arch_sheet_utilisation"] * share_s
    u_back_fix = mu["arch_sheet_utilisation"] * (1 - share_s) * (ts_ / tb_) ** 2
    plate["decided_fix"] = {"what": "M8 8.8 through-bolts with nuts, %.0f mm %s backing plate under the arch top sheet" % (tb_ * 1000, fix["backing_material"]),
                            "arch_sheet_utilisation": round(u_sheet_fix, 3), "backing_plate_utilisation": round(u_back_fix, 3),
                            "bolt_utilisation": mu["bolt_utilisation"], "method": "two stacked plates, moment shared by t^3 (screening, no composite action)"}
    issue("minor", "Lift base plate MEC-019 on the centre-frame arch: load path", w,
          "worst case: bolt %.2f, rivet-nut pull-through %.2f, plate %.2f (%.0f MPa), arch top sheet %.2f (%.0f MPa) utilisation without the fix; per rear bolt %.0f N tension, %.0f N shear; column tilt %.2f deg; with the decided fix (%s): arch top sheet %.2f, backing plate %.2f, bolt %.2f (screening)" % (
              mu["bolt_utilisation"], mu["rivet_nut_pull_through_utilisation"], mu["plate_utilisation"], wc["plate_stress_MPa"], mu["arch_sheet_utilisation"],
              wc["arch_sheet_stress_MPa"], max(wc["bolt_tension_per_bolt_N"].values()), wc["bolt_shear_per_bolt_N"], plate["max_column_tilt_deg"],
              plate["decided_fix"]["what"], u_sheet_fix, u_back_fix, mu["bolt_utilisation"]),
          "utilisation <= 0.67 (factor 1.5 on unfactored loads) for every element", "lift_plate_check.py; EN 485-2, EN 10025-2, EN 1993-1-8; CAD MMP.04.00.00.000",
          "decided (owner decision 8 Nov 2026, A7 option of 2 Nov): through-bolts with a backing plate under the arch top sheet; CAD pending",
          OWN["mech"], "decided fix, CAD pending")

    # ---- TZBOT WCM-500-24 receiver (B4): position, lowest point, floor gap, cut-out, metal-free zone, EMC distances
    TZ = FACTS["tzbot_receiver"]
    tzout = {}
    if "tz_receiver" in geos:
        # owner decision of 2 Nov 2026: wireless charging prepared in 2.0, receiver at the rear panel on the centre line, installed later
        import rear_layout
        RLa = rear_layout.layout()
        g = geos["tz_receiver"]
        lo, hi = g.lo, g.hi
        tx_h = FACTS["tzbot_transmitter"]["size"][2]
        g0, g1 = TZ["air_gap"]
        gap = lo[2] - tx_h
        tzout["position"] = {"lo": lo.round(4).tolist(), "hi": hi.round(4).tolist(), "x_m": RLa["receiver_x"], "status": TZ["status"],
                             "clearance_to_rear_bodies_mm": RLa["receiver_clearance_mm"], "inside_metal_free_margin_mm": RLa["metal_in_margin_mm"]}
        tzout["floor_gap"] = {"receiver_bottom_mm": round(lo[2] * 1000, 1), "transmitter_height_mm": round(tx_h * 1000, 1), "gap_mm": round(gap * 1000, 1),
                              "manual_air_gap_mm": [g0 * 1000, g1 * 1000], "source": TZ["source"], "status": "prepared, installed later"}
        tzout["rear_layout"] = {k: RLa[k] for k in ("measured", "pocket_free", "pockets", "plate", "margin", "cutout")}
        issue("minor", "TZBOT receiver / floor transmitter WCM-500-24 (charging gap)", "prepared, installed later",
              "gap %.0f mm: receiver bottom %.0f mm, %.0f mm floor transmitter" % (gap * 1000, lo[2] * 1000, tx_h * 1000), "gap %.0f to %.0f mm (20 +-10 mm)" % (g0 * 1000, g1 * 1000),
              TZ["source"] + "; owner correction of 2 Nov 2026 (bottom 2 mm below the base sheet)", "to solve before the receiver is installed (receiver higher, recessed transmitter or a low ramp)",
              OWN["mech"], "to solve before receiver installation")
        for k, v in sorted(RLa["metal_in_margin_mm"].items()):
            issue("minor", "TZBOT receiver / %s (inside the 20 mm metal-free frame)" % k, "prepared, installed later",
                  "%.1f mm from the receiver" % v, ">= 20 mm from the receiver sides (TZBOT manual V2.5, A >= 2 cm; plastic frame, owner decision 8 Nov 2026)", "TZBOT WCM-500-24 manual V2.5; receiver at the rear panel (owner, 2 Nov 2026)",
                  "to solve before the receiver is installed (the 20 mm plastic frame keeps metal out; TF-Luna and its PETG mount are mostly non-metal)",
                  OWN["mech"], "to solve before receiver installation")

    # ---- services and fits from the build summary
    nof = summ["nofit"]
    fbs = summ.get("front_bay", {})
    fbd = summ.get("front_bay_default", "A")
    nof_fb = (fbs.get(fbd) or {}).get("fit", {}).get("not_placed", [])
    if nof or nof_fb:
        dims = {it["id"]: it["dims"] for it in load_yaml(os.path.join(HERE, "parts.yaml"))["packed"]}
        RLb = __import__("rear_layout").layout()
        RLb_step = __import__("rear_layout").gi080_step_result
        pz = RLb["plate"]
        g80 = summ.get("gi080", {})
        tried = "; ".join("option %d (%s): %s" % (st["option"], st["what"], RLb_step(st)) for st in g80.get("steps", []))
        issue("major", "Rear layout (A1) / %s" % ", ".join(nof + nof_fb), "power-electronics plate above the receiver and the pocket rear corners",
              "the automatic packer could not place %s under its rules (single layer plus shelf, 5 mm gaps, nothing above a fuse block, estimated outlines); the free space above the receiver is about %.0f x %.0f x %.0f mm (plate width x plate length x height to the cover; plate underside %.0f mm above the floor, rear flange slope from x -0.315); disconnect and SB50 on the rear panel. Packer attempts (A9 options 1 to 3, independent review options 4 and 5): %s" % (
                  ", ".join(nof + nof_fb), (pz[1][1] - pz[0][1]) * 1000, (pz[1][0] - pz[0][0]) * 1000, (FACTS["cover_underside"] - pz[1][2]) * 1000, pz[0][2] * 1000, tried),
              "every onboard part placed with >= 5 mm clearance and fuse access; nothing on the cells; F0 within about 150 mm of the battery positive; BMS close to the cells",
              "parts.yaml estimated outlines (verify); owner corrections A1 and A9 of 2 Nov 2026; build_summary.json gi080",
              "a manual two-level layout with datasheet outlines follows in the next PR",
              OWN["elec"], "manual layout pending")
    g80m = summ.get("gi080", {})
    if g80m.get("manual") and not (nof or nof_fb):   # rear power module laid out by hand (rear_power.py): what is left to verify
        fit_ = g80m.get("fit", {})
        lv = g80m.get("levels", {})
        issue("minor", "Rear power module layout (rear_power.py) / catalogue outlines", "receiver gap %s mm, plate underside %s mm, main line %s mm, FB-B shelf %s mm" % (
                  lv.get("gap_mm"), lv.get("plate_underside_mm"), lv.get("main_line_mm"), lv.get("fbb_shelf_mm")),
              "every part placed, no clash below 5 mm; closest: %s; %d adaptations of the owner report: %s" % (
                  ", ".join("%s / %s %.1f mm" % (c_["a"], c_["b"], c_["gap_mm"]) for c_ in fit_.get("closest", [])[:4]), len(g80m.get("adaptations", [])),
                  "; ".join("%s: %s" % (a_["part"], a_["model"]) for a_ in g80m.get("adaptations", []))),
              "every part placed with >= 5 mm clearance, fuses reachable, nothing on the cells, F0 within about 150 mm of battery +",
              "rear power owner report rev 2 (evans-kwashie, 2 Nov 2026); owner decision of 3 Nov 2026 (15 mm receiver gap); build_summary.json gi080",
              "verify the Daly, 5007100, 6004, 7748, 5046, GX11CAC and busbar outlines and stud positions on drawings; CAD the shelves and busbars (harness_cad_changes.csv)",
              OWN["elec"], "verify")
        near_ = fit_.get("inside_receiver_metal_free_zone", [])
        if near_:
            issue("minor", "TZBOT receiver / parts inside the metal-free zone (non-metal)", "receiver prepared, installed later; 15 mm gap to the power plate (owner decision 3 Nov 2026)",
                  "inside the zone (20 mm on the sides, 15 mm above): %s; specified non-metallic (G10 plate, POM standoffs, PA66 or PEEK fasteners, plastic part feet)" % ", ".join(
                      "%s %.1f mm" % (n_["part"], n_["gap_mm"]) for n_ in near_),
                  "no metal within 20 mm of the receiver sides (TZBOT manual V2.5, A >= 2 cm; 3D-printed plastic frame, design by the mechanical owner) and 15 mm above (owner decision 8 Nov 2026; TZBOT recommends 20 mm)", "TZBOT manual V2.5; rear_power.py",
                  "warning: confirm with TZBOT that the non-metal parts and the K1/K2 bases at 18 mm are acceptable", OWN["elec"], "verify with supplier")
    fg_ = summ.get("flag_guide")
    if fg_:
        sm_ = fg_["summary"]
        issue("minor", "Flag rod guide / band between the flag and the corner bracket", "L1000 to L1350, every 25 mm",
              "guide z %.0f to %.0f mm in the %.0f to %.0f mm band: %.1f mm below, %.1f mm above; rod engaged at every step: %s (at least %.1f mm below the guide); chain %.1f mm, sensors %.1f mm" % (
                  fg_["z"][0] * 1000, fg_["z"][1] * 1000, fg_["band"][0] * 1000, fg_["band"][1] * 1000, fg_["band_margin_mm"][0], fg_["band_margin_mm"][1],
                  sm_["rod_engaged_all"], sm_["min_rod_below_guide_mm"], sm_.get("min_chain_to_guide_mm", 0), sm_["min_sensors_to_guide_mm"]),
              "flag and corner bracket clear the guide at every position; chain, sensors and cables at least 5 mm",
              "owner decision of 3 Nov 2026; flag_guide.py", "if the tolerance stack exceeds 3 mm, use a 15 mm corner bracket (5 mm more band) or move it to the +y face of the rod", OWN["mech"], "verify")
    # A9 cable rules on the 25 mm² runs (build_summary.json cables_25mm2)
    c25 = summ.get("cables_25mm2", {})
    if c25:
        f0 = c25.get("CBL-P01", {})
        bad = sorted(k for k, v in c25.items() if not v.get("bend_ok"))
        f0_bad = f0 and f0.get("route_m", 0) > 0.165
        if f0_bad or bad:
            meas = []
            if f0:
                meas.append("battery + to F0 (CBL-P01) %.0f mm routed, %.0f mm straight" % (f0["route_m"] * 1000, f0["direct_m"] * 1000))
            for k in bad:
                w = c25[k]["worst_corner"]
                meas.append("%s 90 deg corner has %.0f mm straight cable, %.0f mm needed for R 60 mm" % (k, w["have_mm"], w["need_mm"]) if w else k)
            issue("major", "Rear layout (A9) / 25 mm² cable rules", "rear power-electronics plate and the battery trays",
                  "; ".join(meas), "F0 within about 150 mm cable length of battery +; bend radius >= 60 mm on 25 mm² cables (A9)",
                  "cable_list.csv point-to-point routes in the rear bay (one horizontal leg, one vertical drop); build_summary.json cables_25mm2",
                  "move F0 next to the battery + terminal and space the main-path parts (disconnect, PWR-017, K1/K2) for 60 mm bends, together with the GI-080 layout",
                  OWN["elec"], "layout")
    # K1/K2 are GX11CAC only (P-03 rev20.4, owner 8 Nov 2026); option B is no longer reported (GI-008, GI-009 closed)
    for k, o in summ["k1k2_options"].items():
        if k == "A":
            issue("minor", "K1/K2 option A GX11CAC fit", "rear zone", "fits: %s" % o["fits"], "fits the rear zone", "packer", "decision 2 Nov", OWN["elec"], "fit")
    # side pockets (A1) vs the side panel return flanges
    RLc = __import__("rear_layout").layout()
    if not RLc["pockets"].get("clears_flanges"):
        tr = RLc["trays"][0]
        issue("minor", "Rear side pockets / side panel return flanges", "4 + 4 LF105 upright in the side pockets (A1)",
              "pocket %.0f mm across (CAD) x %.0f mm along; 4 cells %s need y %.3f to %.3f, the flanges at y >= 0.193 (z 51 to 74 and 191 to 214 mm) cross them; %.0f mm free inside the flange line" % (
                  RLc["pocket_free"]["y_mm"], RLc["pocket_free"]["x_beside_support_mm"], RLc["pockets"]["arrangement"], tr["lo"][1], tr["hi"][1], RLc["pocket_free"]["y_inside_flanges_mm"]),
              "cells clear the side-panel flanges", "CAD v0.2 side panel MMP.00.00.00.003 (GLB); rear_layout.py",
              "decided (A9, owner, 2 Nov 2026; to be entered in P-03 and M-01): notch the side-panel return flanges at x -0.275 to -0.133 m; CAD pending", OWN["mech"], "decided fix, CAD pending")
    # the Jetson on the front-bay plate (A2), not on the IMU bracket
    fbfit = (fbs.get(fbd) or {}).get("fit", {})
    jz = ((fbs.get(fbd) or {}).get("placed") or {}).get("compute")
    issue("minor", "Jetson Orin NX on J401 position (A2)", "front bay, %s" % fbfit.get("layout", ""), "Jetson on the %s, not on bracket MMP.04.00.00.002; nothing heavy or vibrating on the IMU bracket" % (
              {"A_lower": "lower plate under the shelf (check the fan inlet and outlet)", "A_upper": "upper shelf", "bay": "single plate"}.get(jz[0] if jz else "", "front bay")),
          "nothing heavy or vibrating on the IMU bracket", "front_bay.py", "check the fan airflow at M-09", OWN["mech"], "layout")
    issue("minor", "Battery assembly removal path", "cover off", "each pocket tray lifts out vertically with its 4 cells; the series link over the centre unbolts first",
          "removable without removing the arms", "A1 side pockets; lift base plate at x -0.080 to 0.250", "keep the cover split behind the lift plate", OWN["mech"], "services")
    issue("minor", "Disconnect handle and SB50 access", "rear panel", "BS-6004B and SB50 on the rear panel above the power plate, left and right of the rear TF-Luna", "reachable from outside", "proposed position (A1)", "confirm the panel cut-outs", OWN["elec"], "services")
    issue("minor", "Front bay plates removal with the cover off", "cover off, one layout (A2)", "shelf lifts off its 4 standoffs, then the lower plate off the base sheet",
          "removable with the cover off; every fuse and connector reachable", "front_bay.py", "keep connectors facing up", OWN["mech"], "services")
    issue("minor", "Lift base plate removal and cover opening", "cover off", "the cover opening (x -0.146 to 0.156, y -0.113 to 0.107) must be extended forward to x 0.260 for the plate front (0.250) and the column at bp050 (front 0.230)",
          "cover clears the plate and the column", "CAD v0.2 cover MMP.01.00.00.001; B3", "extend the cover opening to x 0.260 (owner to confirm in CAD)", OWN["mech"], "services")
    # lift energy chain and blocked harness routes (harness.py, harness_routes.json)
    sd = {}
    for d_ in summ.get("seed", []):
        if "energy_chain" in d_:
            sd = d_
    if sd:
        ch_ = sd["energy_chain"]
        issue("minor" if not sd["chain_clash"] else "major", "Lift energy chain over the stroke", "L1000 to L1350 (every 25 mm)",
              "chain %.3f m, R %.0f mm, stroke %.0f mm; %s" % (ch_["length"], ch_["R"] * 1000, ch_["stroke"] * 1000, "no contact" if not sd["chain_clash"] else "contact: " + ", ".join(sd["chain_clash"])),
              "both runs present, loop clear of the cover, no contact with the column, sensors, flag rod, lift node or DP-LIFT-L/R", "harness_routes.json chain", "confirm the chain order code and bracket CAD", OWN["elec"], "harness")
        for cid in sd.get("harness_blocked", []):
            issue("major", "No compliant harness route: %s" % cid, "rear bay (A9 layout)", "no route between the two terminals keeps the rules (not over a fuse block or component, R >= 60 mm, no detour over 2.5 x)",
                  "every cable on a supported route", "harness_routes.json unrouted", "rear-layout rework with GI-080 (space a cable passage beside FB-A or move the terminal)", OWN["elec"], "harness")
    # A6: flag rod on the one-piece adapter plate (GI-010 closes when the rod is inside the plate footprint); stroke check of the
    # rod and the flag against the column, the lift cable chain (service loop), the second E-stop housing, the rear power
    # electronics and the top cover, at L1000, L1175 and L1350
    rodv = names["flag_rod"].world(base_cfg)
    plv = names["adapter_plate"].world(base_cfg)
    inside = rodv[:, 1].max() <= plv[:, 1].max() + 1e-6 and rodv[:, 1].min() >= plv[:, 1].min() - 1e-6 and rodv[:, 0].min() >= plv[:, 0].min() - 1e-6
    if not inside:
        issue("major", "Flag rod LFT-004 / adapter plate MEC-004 footprint", "all lift positions", "rod x %.0f to %.0f, y %.0f to %.0f mm vs plate x %.0f to %.0f, y +-%.0f mm" % (
            rodv[:, 0].min() * 1000, rodv[:, 0].max() * 1000, rodv[:, 1].min() * 1000, rodv[:, 1].max() * 1000, plv[:, 0].min() * 1000, plv[:, 0].max() * 1000, plv[:, 1].max() * 1000),
            "inside the plate footprint", "A6 (owner correction, 2 Nov 2026)", "extend the plate (frames.lift_rear_layout)", OWN["mech"], "interference")
    LRt = lift_rear_layout()
    stroke = {}
    for tr, nm in ((0.0, "L1000"), (.175, "L1175"), (.35, "L1350")):
        cfg = {"bp": "bp000", "travel": tr}
        gr = {k: Geo(names[k], cfg, .003) for k in ("flag_rod", "lift_flag", "rod_corner_bracket") if k in names}
        res_ = {}
        for other in ("lift_column", "rear_estop_housing", "second_estop", "lift_energy_chain", "cover", "lift_stop_sensors", "lift_sensor_bracket_1", "lift_sensor_bracket_2",
                      "lift_sensor_bracket_3", "lift_stop_sensor_1", "lift_stop_sensor_2", "lift_stop_sensor_3", "lift_node", "rear_plate", "harness_r24_col", "harness_sig_col"):
            if other not in names:
                continue
            go = Geo(names[other], cfg, .003)
            best = None
            for k, g in gr.items():
                r = pair(g, go, .05)
                if r:
                    d_ = -r[1] if r[1] > 0 else r[0]
                    best = d_ if best is None else min(best, d_)
            res_[other] = None if best is None else round(best * 1000, 1)
        stroke[nm] = res_
    cover_top = max(float(v[:, 2].max()) for k, v in ((k, names[k].world(base_cfg)) for k in ("cover",) if k in names))
    rod_bottom = float(rodv[:, 2].min())
    lift_rear_out = {"layout": LRt, "rod_inside_plate": bool(inside), "rod_bottom_L1000_mm": round(rod_bottom * 1000, 1),
                     "rod_bottom_above_cover_L1000_mm": round((rod_bottom - cover_top) * 1000, 1), "clearances_mm": stroke}
    # the E-stop housing and its fasteners stay out of the rod mount area (rod + corner bracket footprint on the plate underside)
    if "rear_estop_housing" in names and "rod_corner_bracket" in names:
        hv = names["rear_estop_housing"].world(base_cfg)
        mv = np.vstack([rodv, names["rod_corner_bracket"].world(base_cfg)])
        gx = max(float(hv[:, 0].min() - mv[:, 0].max()), float(mv[:, 0].min() - hv[:, 0].max()))
        gy = max(float(hv[:, 1].min() - mv[:, 1].max()), float(mv[:, 1].min() - hv[:, 1].max()))
        lift_rear_out["estop_to_rod_mount_mm"] = round(max(gx, gy) * 1000, 1)
        if max(gx, gy) < 0.005:
            issue("major", "Second E-stop housing / flag rod mount (A6)", "adapter plate", "%.1f mm between the housing footprint and the rod mount" % (max(gx, gy) * 1000),
                  ">= 5 mm: the housing fasteners do not share the rod mount area", "A6 (owner correction, 2 Nov 2026)", "move the housing forward on the plate", OWN["mech"], "interference")
    contacts = sorted({(nm, k, v) for nm, d_ in stroke.items() for k, v in d_.items() if v is not None and v < 1.95})
    if contacts:
        issue("major", "Flag rod and flag (A6) / %s" % ", ".join(sorted({k for _, k, _ in contacts})), "L1000 / L1175 / L1350, bp000",
              "; ".join("%s %s %.1f mm" % (nm, k, v) for nm, k, v in contacts), "clearance >= 2 mm (the 2 mm flag gap is the design value)",
              "A6 (owner correction, 2 Nov 2026); frames.lift_rear_layout", "move the part out of the rod and flag path", OWN["mech"], "interference")
    eact = up.get("estop2_actuator_z_stops") or {}
    ep = {"position": "adapter plate top behind the post, centred in y, above the column axis, button up (A5)", "actuator_centre_m": eact,
          "reach_band_m": [0.90, 1.50], "cable": "through the adapter plate into the lift cable chain with the arm cables"}
    hit_e = sorted({k[1] for k in sweep if k[2] == "second_estop"})
    issue("minor" if not hit_e and all(0.90 <= v <= 1.50 for v in eact.values()) else "major", "Second E-stop on the adapter plate (A5)", "L1000 / L1175 / L1350",
          "actuator centre %s m; arm motion in valid poses: %s" % (" / ".join("%.3f" % v for v in eact.values()), "clear" if not hit_e else "hit by the %s arm" % " and ".join(hit_e)),
          "0.90 to 1.50 m at every stop, no arm contact (owner, 2 Nov 2026)", "owner correction A5; design_intent/rear_estop_housing.py",
          "enter the position in P-03 and M-01; tapped holes and a cable hole in MEC-004 (M-09)", OWN["mech"], "arm reach")
    g_hit = sorted({k[1] for k in sweep if k[2] in ("getac_tablet", "getac_pocket")})
    issue("major" if g_hit else "minor", "Getac ZX80 at shoulder height / arms", "portrait (A3), L1000 and L1350",
          "29 Oct simulation (landscape at shoulder height): hit in 23 of 154 frames; rerun with the portrait Getac 40 mm lower: page pose clear, single-joint sweep %s" % ("hit by the %s arm" % " and ".join(g_hit) if g_hit else "clear"),
          "no arm contact", "B8; owner correction A3", "rerun the Gazebo pick cycle with the portrait Getac; MoveIt collision object", OWN["mech"], "arm reach")
    issue("minor", "Left tote wall / sensors S1, S2", "visualization", "3.2 mm overlap", "none", "B8 (visualization only)", "fix the tote model", OWN["tech"], "interference")

    # ---- write
    order = {"blocker": 0, "major": 1, "minor": 2}
    issues.sort(key=lambda r: (order[r["severity"]], r["kind"], r["parts"]))
    # stable issue IDs (issue_ids.yaml, seeded from the IDs published in PR #68): an issue keeps its ID across reruns; new
    # issues get the next free ID; IDs no longer reported are closed with a reason (hardware page)
    reg_path = os.path.join(HERE, "issue_ids.yaml")
    REG = load_yaml(reg_path) if os.path.exists(reg_path) else {}
    ids_reg, closed_reg = dict(REG.get("ids") or {}), dict(REG.get("closed") or {})
    nxt = max([int(v[3:]) for v in list(ids_reg.values()) + list(closed_reg)] + [0]) + 1
    seen, used = set(), set()
    for r in issues:
        k = issue_key(r)
        if k in used:  # same parts in another configuration (for example L1000 and L1350)
            k = "%s|%s" % (k, r["configuration"])
        used.add(k)
        if k not in ids_reg:
            ids_reg[k] = "GI-%03d" % nxt
            nxt += 1
        r["id"] = ids_reg[k]
        assert r["id"] not in seen, "two issues share the ID %s (%s)" % (r["id"], k)
        seen.add(r["id"])
    for k, v in list(ids_reg.items()):
        if v not in seen:
            closed_reg.setdefault(v, {"key": k, "reason": "no longer reported by the analysis"})
            del ids_reg[k]
    for v in list(closed_reg):
        if v in seen:
            del closed_reg[v]
    with open(reg_path, "w") as f:
        f.write("# Stable IDs of geometry_issues.csv (written by analyse.py). key: kind|parts (dynamic part lists stripped).\n")
        f.write("# closed: IDs no longer reported, with the reason. Edit a reason by hand; analyse.py keeps it.\n")
        f.write("ids:\n" + "".join("  %s: %s\n" % (json.dumps(k), v) for k, v in sorted(ids_reg.items(), key=lambda x: x[1])))
        f.write("closed:\n" + "".join("  %s: {key: %s, reason: %s}\n" % (v, json.dumps(c["key"]), json.dumps(c["reason"])) for v, c in sorted(closed_reg.items())))
    closed_out = [{"id": v, "key": c["key"], "reason": c["reason"]} for v, c in sorted(closed_reg.items())]
    keys = ["id", "severity", "kind", "parts", "configuration", "measured", "limit", "source", "suggested_fix", "owner"]
    with open(os.path.join(MODEL, "geometry_issues.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in issues:
            w.writerow({k: r[k] for k in keys})
    wl = min(float(G[k]["v"][:, 2].min()) for k in ("hub_motor_wheel_left", "hub_motor_wheel_right"))
    intended = [{"pair": "hub motor wheels / floor", "overlap_mm": round(-wl * 1000, 2), "limit_mm": FACTS["wheel_compression"] * 1000,
                 "reason": "owner decision 2 Nov 2026 (B1): rubber tyres r 0.100 m on the axle at 0.098 m; 2 mm intended tyre compression under load levels the rigid chassis (no suspension)",
                 "within_limit": -wl <= FACTS["wheel_compression"] + 1e-6}]
    if not intended[0]["within_limit"]:
        issue("major", "Hub motor wheels / floor", "all", "overlap %.1f mm" % (-wl * 1000), "intended contact <= 2 mm (B1)", "base GLB", "check the wheel model", OWN["mech"], "geometry")
    gpo = getac_check
    out = {"self_check": check, "closed_issues": closed_out, "lift_rear": lift_rear_out, "frames": frames, "heights": heights, "mass": res, "stability": stab, "loads": loads, "views": views,
           "intended_contacts": intended, "tzbot": tzout, "lift_base_plate": plate, "estop": ep, "getac_check": getac_check, "front_bay": {k: v.get("fit") for k, v in fbs.items()},
           "front_bay_default": fbd, "getac_portrait": gpo, "mass_items": placed_mass,
           "sweep": {"%s|%s|%s" % k: v[:20] for k, v in sweep.items()}, "sweep_stops": {"%s|%s|J%d|%+d" % k: v for k, v in stops.items()}, "sweep_valid_poses": nsteps,
           "counts": {s: sum(1 for r in issues if r["severity"] == s) for s in order}, "steel_chassis_kg": round(steel, 2)}
    json.dump(out, open(os.path.join(HERE, "analysis_summary.json"), "w"), indent=1, default=str)
    print(json.dumps(out["counts"]), json.dumps({k: (round(v["mass"], 1), v["com"]) for k, v in res.items()}), json.dumps(stab))


if __name__ == "__main__":
    main()
