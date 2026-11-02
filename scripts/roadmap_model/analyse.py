#!/usr/bin/env python3
"""Geometry and hardware analysis of the OpenAMRobot 2.0 roadmap model (section G2 of the 2 Nov 2026 update).

Rebuilds the scene of model/model.js in Python (base GLB, upper-body primitives, chest and lift-sensor items,
model/placement.json, OpenArm 2.0 kinematics from model/openarm.js), checks it against a dump of the page
scene (scene_dump.js, same part boxes within 0.5 mm), then analyses:
  interference (all part pairs, lift L1000 / L1175 / L1350, bp000 / bp050, hp15 to hp35, both Getac positions,
  arms in the upstream home pose), arm reach (joint by joint through the URDF limits, 10 deg steps, L1000 and
  L1350), sensor views (Gemini 336L and ZED Mini frustums, LiDAR scan plane +-5 mm), mass and stability, the
  the reserved TZBOT receiver position, service access and the K1/K2 fit.
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

from frames import FACTS, HERE, MODEL, REPO, datums, glb_nodes, load_yaml, sensor_frames, tzbot_layout

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
        env = n["extras"].get("class") == "envelope"  # envelopes are boxes by definition: exact tests on their bounds
        v = relocated(n["v"], k, P, opt)
        parts.append(Part(k, v, n["f"], "base", boxes=[(v.min(0), v.max(0))] if env else None))
    t, L, Wc, RET, HEAD = .304, .24, .06, .53, .012
    c = t + RET
    i = RET - HEAD - .012
    MOUNT_X, PX, PY, PL = .18, .12, .06, .34
    def add(pid, vf, g, exact=True):
        v = np.asarray(vf[0])
        parts.append(Part(pid, v, vf[1], g, boxes=[(v.min(0), v.max(0))] if (exact and len(v) == 8) else None))
    add("lift_column", box_mesh([L, Wc, i + .012], [0, 0, t + (i + .012) / 2]), "col")
    add("lift_column_stage", box_mesh([L - .016, Wc - .012, .44], [0, 0, c - HEAD - .22]), "mov")
    add("lift_column_head", box_mesh([.25, .072, HEAD], [0, 0, c - HEAD / 2]), "mov")
    d, p = -L / 2, MOUNT_X + PX / 2
    add("adapter_plate", box_mesh([p - d, .1, .01], [(d + p) / 2, 0, c + .005]), "mov")
    f = c + .01
    add("arm_profile", box_mesh([PX, PY, PL], [MOUNT_X, 0, f + PL / 2]), "mov")
    m = c + .166 + .223
    y = f + PL
    ZED_X = .222
    add("head_camera_bracket", box_mesh([.03, .03, m - y], [ZED_X - .03, 0, (y + m) / 2]), "mov")
    Rz = rpy_matrix([0, math.radians(head_pitch), 0])
    v, ff = box_mesh([.0265, .1245, .0305], np.array([0, 0, 0]))
    v = (v + [-.013, 0, 0]) @ Rz.T + [ZED_X, 0, m]
    add("head_camera", (v, ff), "mov", exact=False)
    # chest: second E-stop (copy of the GLB estop node), Getac, head light
    e = chest["second_estop"]
    ev = G["estop"]["v"] - [0, 0, FACTS["base_link_z"]]
    ax = e["glb_axis"]
    ev = ev + [e["panel_ahead"] - ax[0], -ax[1], -ax[2]]
    if e.get("position") == "P2":  # arm-post rear face, moving group (proposed, 2 Nov 2026)
        ev = ev @ rpy_matrix([0, 0, math.pi]).T + [MOUNT_X - PX / 2, 0, c + .01 + PL - e["post_below_top"]]
        add("second_estop", (ev, G["estop"]["f"]), "mov", exact=False)
    else:
        ev = ev @ rpy_matrix([0, 0, math.pi]).T + [-L / 2, 0, c - HEAD - .006 - e["below_top"]]
        add("second_estop", (ev, G["estop"]["f"]), "col", exact=False)
    C = chest["drawn"]
    fr = MOUNT_X + PX / 2
    ts = C["getac_tablet"]["size"]
    add("getac_tablet", box_mesh(ts, [fr + ts[0] / 2, 0, c + C["getac_tablet"]["z"]]), "mov")
    hs = C["head_light"]["size"]
    add("head_light", box_mesh(hs, [fr + hs[0] / 2, 0, c + C["head_light"]["z"]]), "mov")
    # lift sensors
    y0 = Wc / 2
    s = lift["sensor"]
    ys = y0 + lift["axis_off"]
    for k, dz in enumerate(lift["z"]):
        add("lift_stop_sensor_%d" % (k + 1), cyl_mesh(s["d"] / 2, s["len"], [lift["face_x"] + s["len"] / 2, ys, t + dz], "x"), "col")
        b = lift["bracket"]
        bx = lift["face_x"] + s["len"] - b["at"]
        add("lift_sensor_bracket_%d" % (k + 1), box_mesh([b["leg"], b["t"], lift["bracket_h"]], [bx - b["leg"] / 2, y0 + b["t"] / 2, t + dz]), "col")
        add("lift_sensor_bracket_leg_%d" % (k + 1), box_mesh([b["t"], b["leg"], lift["bracket_h"]], [bx - b["t"] / 2, y0 + b["leg"] / 2, t + dz]), "col")
    r = lift["rod"]
    rx = lift["face_x"] - lift["gap"] - lift["flag"][0] - r["w"] / 2
    ry = y0 + r["off"] + r["w"] / 2
    add("flag_rod", box_mesh([r["w"], r["w"], r["len"]], [rx, ry, c - r["len"] / 2]), "mov")
    fl = lift["flag"]
    add("lift_flag", box_mesh(fl, [lift["face_x"] - lift["gap"] - fl[0] / 2, y0 + lift["flag_off"] + fl[1] / 2, c - lift["flag_below_plate"]]), "mov")
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
    return parts


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
                ("lift_column", "rear_estop"), ("lift_column_head", "adapter_plate"), ("adapter_plate", "arm_profile"), ("adapter_plate", "flag_rod"),
                ("arm_profile", "head_camera_bracket"), ("head_camera_bracket", "head_camera"), ("arm_profile", "getac"), ("arm_profile", "head_light"),
                ("arm_profile", "fasteners"), ("adapter_plate", "fasteners"), ("lift_sensor", "lift_stop"), ("lift_sensor", "fasteners"),
                ("lift_stop", "lift_sensor"), ("harness", "*"), ("service_loop", "*"), ("keepout", "*"), ("can_term", "*"), ("lidar", "lidar_"),
                ("camera_mount", "base_camera"), ("ultrasonic", "ultrasonic"), ("tof", "tof"), ("ultrasonic", "us_locknut"), ("compute", "electronics_bracket"),
                ("controller_plate", "*"), ("base_controller", "controller_plate"), ("imu", "electronics_bracket"), ("motor_driver", "driver_mount"),
                ("battery", "battery_tray"), ("hub_motor", "motor_brackets"), ("castor", "shims"), ("getac", "getac_"), ("head_light", "getac_pocket"),
                ("getac_second_position_ghost", "*"), ("rear_estop_clear_ghost", "*"), ("k1k2_option_b", "*"), ("tz_receiver", "*"), ("estop", "front_panel"),
                ("reset_button", "front_panel"), ("feedthru", "side_panel"), ("rz_disc", "rear_panel"), ("rz_sb50", "rear_panel"), ("fasteners", "*"),
                ("harness_fittings", "*"), ("shims", "*"), ("us_locknut", "*"), ("lift_bolt_keepout", "*"),
                ("lift_sensor_bracket", "lift_sensor_bracket"), ("flag_rod", "lift_flag"), ("rear_estop_housing", "second_estop"),
                ("bay_plate", "lidar_support"), ("lift_base_plate", "lift_node"), ("lift_column_stage", "lift_column"), ("lift_column_head", "lift_column"),
                ("lift_column_head", "arm_profile"), ("rear_estop", "lift_column"),
                # 2 Nov 2026: plate on the arch, E-stop P2 on the post, reserved receiver (its warning is an issue below), ghosts, bay plate
                ("lift_base_plate", "centre_bracket"), ("second_estop", "arm_profile"), ("rear_estop_housing", "arm_profile"), ("rear_estop_housing", "second_estop"),
                ("estop_p", "*"), ("tz_", "*"), ("base_cutout", "*"), ("bay_plate", "lidar_support"), ("bay_plate", "electronics_bracket"),
                ("bay_plate", "compute"), ("bay_plate", "base_controller"), ("lift_node", "lift_column"),
                ("bay_", "electronics_bracket"), ("compute", "electronics_bracket"), ("base_controller", "controller_plate")]  # bracket shortening: own issue

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
        issue(sev, "%s / %s" % (a, b), "L1000, bp000, hp30, landscape", ("overlap %.1f mm" if k == "overlap" else "clearance %.1f mm") % (val * 1000),
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
    gp = geos.get("getac_second_position_ghost")
    if gp:
        for other in ("head_light", "arm_profile", "head_camera", "head_camera_bracket"):
            r = pair(gp, geos[other])
            if r and r[1] > .0005:
                issue("major", "getac pocket portrait / %s" % other, "portrait, L1000", "overlap %.1f mm" % (r[1] * 1000), "overlap <= 0.5 mm",
                      "design_intent/getac_pocket_portrait.step; datums head_light_gap_below_tablet", "move the pivot hub further above the tablet centre", OWN["mech"], "interference")
            elif r and r[0] < .005:
                issue("major", "getac pocket portrait / %s" % other, "portrait, L1000", "clearance %.1f mm" % (r[0] * 1000), "clearance >= 5 mm",
                      "design_intent/getac_pocket_portrait.step", "move the pivot hub further above the tablet centre", OWN["mech"], "interference")

    # ---- arm reach sweep
    sweep = {}
    targets = {k: geos[k] for k in ("getac_tablet", "head_light", "head_camera", "head_camera_bracket", "second_estop", "flag_rod", "arm_profile", "getac_pocket", "lift_flag") if k in geos}
    for tr, nm in ((0.0, "L1000"), (.35, "L1350")):
        cfg = {"bp": "bp000", "travel": tr}
        tg = {k: Geo(names[k], cfg, .004) for k in targets}
        for side in ("left", "right"):
            home = [0.0] * 7
            parts0, a = arm_parts(side, home, .6, up["col_top"] + .166 + tr, .06)
            for j in range(7):
                lo, hi = a["joints"][j]["lo"], a["joints"][j]["hi"]
                for q in np.arange(lo, hi + 1e-6, math.radians(10)):
                    qq = list(home)
                    qq[j] = q
                    ps, _ = arm_parts(side, qq, .6, up["col_top"] + .166 + tr, .06)
                    for lp in ps:
                        if lp.id.endswith("_base"):
                            continue
                        lg = Geo(lp, {"bp": "bp000", "travel": 0}, .006)
                        for k, g in tg.items():
                            if k == "arm_profile" and lp.id.endswith(("link1",)):
                                continue
                            r = pair(lg, g, .002)
                            if r and (r[1] > .001 or r[0] < .0015):
                                key = (nm, side, k)
                                sweep.setdefault(key, []).append((j + 1, round(math.degrees(q)), lp.id))
    nsteps = sum(int((a["joints"][j]["hi"] - a["joints"][j]["lo"]) / math.radians(10)) + 1 for j in range(7))
    for (nm, side, k), lst in sorted(sweep.items()):
        js = sorted({x[0] for x in lst})
        issue("major" if k in ("getac_tablet", "head_light", "head_camera", "second_estop", "getac_pocket") else "minor",
              "OpenArm %s / %s" % (side, k), "%s, single-joint sweep from the upstream home pose (all joints 0), 10 deg steps" % nm,
              "%d of %d sweep poses hit (joints %s)" % (len({(x[0], x[1]) for x in lst}), nsteps, ", ".join("J%d" % j for j in js)),
              "no contact inside the joint limits, or a software keep-out", "openarm_description 14ff67b limits; datums.yaml positions; B8 (29 Oct simulation)",
              "add a MoveIt collision object and joint-limit keep-out for this item; for the Getac and E-stop see M-09", OWN["manip"], "arm reach")

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
    cov = list(csv.DictReader(open(os.path.join(MODEL, "bom_coverage.csv"))))
    mass_items = []
    for r in cov:
        try:
            m = float(r["mass_kg"])
        except ValueError:
            continue
        if r["onboard"] == "y" and m > 0:
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
                    pts.append(w.mean(0))
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
    issue("minor" if margin_ok else "major", "Lift base plate MEC-019 on the centre-frame arch: load path", w,
          "worst case: bolt %.2f, rivet-nut pull-through %.2f, plate %.2f (%.0f MPa), arch top sheet %.2f (%.0f MPa) utilisation; per rear bolt %.0f N tension, %.0f N shear; column tilt %.2f deg" % (
              mu["bolt_utilisation"], mu["rivet_nut_pull_through_utilisation"], mu["plate_utilisation"], wc["plate_stress_MPa"], mu["arch_sheet_utilisation"],
              wc["arch_sheet_stress_MPa"], max(wc["bolt_tension_per_bolt_N"].values()), wc["bolt_shear_per_bolt_N"], plate["max_column_tilt_deg"]),
          "utilisation <= 0.67 (factor 1.5 on unfactored loads) for every element", "lift_plate_check.py; EN 485-2, EN 10025-2, EN 1993-1-8; CAD MMP.04.00.00.000",
          "load path into the arch with margin: GI-026 / GI-027 (front deck bolts without a frame) closed" if margin_ok else
          "add a doubler under the arch top between the rear rivet nuts and the rear wall, or use the outer 190 x 300 rivet-nut pattern as well (wider plate)",
          OWN["mech"], "load path")

    # ---- TZBOT WCM-500-24 receiver: reserved position at the rear under the battery (release 3.0, Alex, 2 Nov 2026). One warning:
    # receiver top vs the cells and the tray, metal within 20 mm, charging gap with a 52 mm floor transmitter. Recorded, not fixed.
    TZ = FACTS["tzbot_receiver"]
    TZL = tzbot_layout()
    tzout = {}
    if "tz_receiver" in geos:
        lo, hi = TZL["lo"], TZL["hi"]
        rv, rf = box_mesh(hi - lo, (lo + hi) / 2)
        RXG = Geo(Part("tz_receiver_body", rv, rf, "base", boxes=[(lo, hi)]), base_cfg, .002)
        def sd(k):
            r = pair(RXG, geos[k], 0.5)
            return None if r is None else round((-r[1] if r[1] > 0 else r[0]) * 1000, 1)
        named = [("battery cells", "battery"), ("battery tray MEC-007", "battery_tray"), ("base sheet MEC-001", "base_plate"),
                 ("castor rear left", "castor_rear_left"), ("castor rear right", "castor_rear_right")]
        meas = [{"part": n, "id": k, "distance_mm": sd(k)} for n, k in named if k in geos]
        if "base_plate" in geos:  # the receiver passes through the 2 mm sheet (no cut-out drawn): overlap = sheet thickness inside the receiver height
            bs = FACTS["base_sheet"]
            for m_ in meas:
                if m_["id"] == "base_plate":
                    m_["distance_mm"] = round(-(min(hi[2], bs["top"]) - max(lo[2], bs["bottom"])) * 1000, 1)
        others = []
        skip = ("tz_", "battery", "battery_tray", "base_plate", "castor_rear", "keepout", "lift_bolt", "harness", "service_loop", "estop_p", "getac_second", "k1k2_option", "can_term")
        for k, gg in geos.items():
            if k.startswith(skip) or k.endswith("_optb"):
                continue
            r = pair(RXG, gg, TZ["metal_clear"])
            if r:
                others.append({"part": k, "id": k, "distance_mm": round((-r[1] if r[1] > 0 else r[0]) * 1000, 1)})
        top_cells = next((m_["distance_mm"] for m_ in meas if m_["id"] == "battery"), None)
        top_tray = next((m_["distance_mm"] for m_ in meas if m_["id"] == "battery_tray"), None)
        tx_h = FACTS["tzbot_transmitter"]["size"][2]
        gap = lo[2] - tx_h
        tzout = {"status": TZ["status"], "decided": TZ["decided"], "lo": lo.round(4).tolist(), "hi": hi.round(4).tolist(), "battery": TZL["battery"],
                 "receiver_top_mm": round(hi[2] * 1000, 1), "receiver_bottom_mm": round(lo[2] * 1000, 1), "vs_cells_mm": top_cells, "vs_tray_mm": top_tray,
                 "metal": meas + others, "gap_mm": round(gap * 1000, 1), "air_gap_mm": [TZ["air_gap"][0] * 1000, TZ["air_gap"][1] * 1000],
                 "transmitter_height_mm": round(tx_h * 1000, 1)}
        within = [m_ for m_ in meas + others if m_["distance_mm"] is not None and m_["distance_mm"] < TZ["metal_clear"] * 1000]
        fmt = lambda v: "overlap %.1f mm" % -v if v < 0 else "clearance %.1f mm" % v
        issue("minor", "TZBOT WCM-500-24 receiver (reserved, rear under the battery)", "reserved position, release 3.0, not installed in 2.0 (owner decision, 2 Nov 2026)",
              "receiver top %.0f mm vs battery cells: %s, vs battery tray: %s; metal within 20 mm: %s; rear castors: %s (outside 20 mm); charging gap with a %.0f mm floor transmitter: %.0f mm (receiver bottom %.0f mm)" % (
                  hi[2] * 1000, fmt(top_cells), fmt(top_tray) if top_tray is not None else "n/a",
                  "; ".join("%s %s" % (m_["part"], fmt(m_["distance_mm"])) for m_ in within) or "none",
                  fmt(min(m_["distance_mm"] for m_ in meas if m_["id"].startswith("castor_rear"))),
                  tx_h * 1000, gap * 1000, lo[2] * 1000),
              "no overlap with the cells or the tray, no metal within 20 mm, air gap %.0f to %.0f mm (TZBOT WCM-500-24 manual V2.5)" % (TZ["air_gap"][0] * 1000, TZ["air_gap"][1] * 1000),
              TZ["source"] + "; reserved position, owner decision of 2 Nov 2026", "known, to be solved in release 3.0", OWN["mech"], "reserved for 3.0")

    # ---- services and fits from the build summary
    nof = summ["nofit"]
    fbs = summ.get("front_bay", {})
    fbd = summ.get("front_bay_default", "A")
    nof_fb = (fbs.get(fbd) or {}).get("fit", {}).get("not_placed", [])
    if nof or nof_fb:
        dims = {it["id"]: it["dims"] for it in load_yaml(os.path.join(HERE, "parts.yaml"))["packed"]}
        issue("blocker", "Rear zone layout (B5) / %s" % ", ".join(nof + nof_fb), "B5 rear zone with the design-intent battery tray MEC-007 and the real side-pocket section; overflow under the arch tried",
              "no space for %s: behind the cells 66 mm deep with the tray rear wall (70 mm without it) for the 70 mm deep FB-A / FB-B; side pockets 71 mm wide (with the tray wall) and 117 mm tall only between z 74 and 191 mm, 140 mm long, for the BMS %s mm" % (
                  ", ".join(nof + nof_fb), "x".join("%g" % d for d in dims.get("rz_bms", []))),
              "every onboard part placed with >= 5 mm clearance", "parts.yaml catalogue outlines (verify), B5, CAD v0.2 side panel flanges, design_intent/battery_tray.py",
              "FB-A and FB-B on the rear panel inner face above the disconnect (vertical, 70 mm deep into the zone is then not needed) or a lower-profile fuse block; a BMS no larger than 140 x 70 x 115 mm for the pocket, or fix the Daly order code and its outline; then update B5",
              OWN["elec"], "layout")
    for k, o in summ["k1k2_options"].items():
        if k == "A":
            issue("minor", "K1/K2 option A GX11CAC fit", "rear zone", "fits: %s" % o["fits"], "fits the rear zone", "packer", "decision 2 Nov", OWN["elec"], "fit")
        else:
            issue("major" if not o["fits"] else "minor", "K1/K2 option B %s fit" % o["part"], "rear zone (with the rest of the layout)",
                  "fits: %s (%s)" % (o["fits"], ", ".join(o.get("nofit", [])) or "all placed"), "fits the rear zone", "packer with catalogue outline %s mm" % "x".join(map(str, o["dims"])),
                  "if option B is chosen, mount K1/K2 on the rear panel or the centre-bracket rear wall", OWN["elec"], "fit")
    # side pockets vs the side panel return flanges
    issue("major", "Rear side pockets / side panel return flanges", "rear zone", "pocket 91 mm wide only between z 74 and 191 mm; 36 mm at the flange heights (inner flange at y 0.193)",
          "B5 / platform-sw #95: 140 x 91 x 210 mm free each side", "CAD v0.2 side panel MMP.00.00.00.003 (GLB)", "keep tall parts (BMS, K1/K2) inside y 0.193 or between the flanges; update B5", OWN["mech"], "layout")
    jet_fixed = fbd == "A"
    issue("major", "Jetson Orin NX with fan on the IMU bracket MMP.04.00.00.002", "CAD v0.2", "compute (with fan) shares the electronics bracket with the EV_ICM-42688-P",
          "nothing heavy or vibrating on the IMU bracket (E2)", "CAD v0.2 compute node on the bracket top",
          "front bay option A (proposed) moves the Jetson to the upper shelf; owner to adopt the option in CAD" if jet_fixed else "move the IMU to its own sub-plate or move the Jetson", OWN["mech"], "layout")
    issue("minor", "Battery assembly removal path", "cover off", "cells lift out vertically through the cover opening; 26 mm above the cells, nothing on top (B5)",
          "removable without removing the arms", "B5; lift base plate at x -0.12 to 0.24 (rear edge 17 mm ahead of the cells)", "keep the cover split behind the lift plate", OWN["mech"], "services")
    issue("minor", "Disconnect handle access", "rear panel", "BS-6004B drawn at the rear panel centre above the rear TF-Luna", "reachable from outside", "proposed position", "confirm the panel cut-out", OWN["elec"], "services")
    issue("minor", "Front bay plates removal with the cover off", "cover off, option A", "shelf lifts off its 4 standoffs, then the lower plate off its rivet nuts",
          "removable with the cover off; every fuse and connector reachable", "front_bay.py", "keep the connectors facing up", OWN["mech"], "services")
    issue("minor", "Lift base plate removal and cover opening", "cover off", "the cover opening (x -0.146 to 0.156, y -0.113 to 0.107) must be extended forward to x 0.260 for the plate front (0.250) and the column at bp050 (front 0.230)",
          "cover clears the plate and the column", "CAD v0.2 cover MMP.01.00.00.001; B3", "extend the cover opening to x 0.260 (owner to confirm in CAD)", OWN["mech"], "services")
    # service loop
    sd = summ["seed"][0] if summ.get("seed") else {}
    if sd:
        issue("minor" if sd["service_loop_length"] >= sd["service_loop_need"] else "major", "Upper-body service loop length", "L1000 to L1350",
              "loop %.0f mm vs %.0f mm needed at L1350" % (sd["service_loop_length"] * 1000, sd["service_loop_need"] * 1000), "covers the 350 mm stroke plus bend allowance", "harness route", "size the sleeve at build", OWN["elec"], "harness")
    # rod outside the plate (B8) and second E-stop position (B8)
    rodv = names["flag_rod"].world(base_cfg)
    issue("major", "Flag rod LFT-004 / adapter plate MEC-004 footprint", "all lift positions", "rod y %.0f to %.0f mm vs plate edge 50 mm: %.0f to %.0f mm outside" % (rodv[:, 1].min() * 1000, rodv[:, 1].max() * 1000, rodv[:, 1].min() * 1000 - 50, rodv[:, 1].max() * 1000 - 50),
          "inside the plate footprint", "datums.yaml lift_flag_rod_offset_from_face; B8", "rod mount bracket of design_intent/adapter_post (keeps the rod inside) or a 130 mm wide plate", OWN["mech"], "interference")
    ep = json.load(open(os.path.join(HERE, "estop_positions.json")))
    p2 = ep["positions"]["P2"]
    hits = {k: sum(v["reach_study_hits"].values()) for k, v in p2["stops"].items()}
    issue("major", "Second E-stop P2 (proposed) / arm reach envelope", "L1000 / L1175 / L1350, arm-post rear face, 55 mm below the post top",
          "actuator centre %s m; single-joint sweep clear; reach study %s of about %d valid random poses per arm and stop come within 5 mm" % (
              " / ".join("%.3f" % v["actuator_centre_m"] for v in p2["stops"].values()), " / ".join(str(v) for v in hits.values()), ep["n_per_arm"] * 0.92),
          "0.90 to 1.50 m at every stop, no arm contact (owner, 2 Nov 2026)", "estop_positions.py; design_intent/rear_estop_housing.py",
          "P-03 entry for P2 (then datums second_estop_below_profile_top and its parent link change); add the housing as a MoveIt collision object on arm_profile_link", OWN["manip"], "arm reach")
    issue("major", "Getac ZX80 at shoulder height / arms", "arm workspace", "hit in 23 of 154 simulation frames (29 Oct)", "no arm contact", "B8", "M-09 position; MoveIt collision object", OWN["mech"], "arm reach")
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
    gpo = {}
    if gp:
        for other in ("head_light", "arm_profile", "head_camera", "head_camera_bracket"):
            r = pair(gp, geos[other], .05)
            gpo[other] = None if r is None else {"clearance_mm": round(r[0] * 1000, 1), "overlap_mm": round(r[1] * 1000, 1)}
    out = {"self_check": check, "closed_issues": closed_out, "frames": frames, "heights": heights, "mass": res, "stability": stab, "loads": loads, "views": views,
           "intended_contacts": intended, "tzbot": tzout, "lift_base_plate": plate, "estop_positions": ep, "front_bay": {k: v.get("fit") for k, v in fbs.items()},
           "front_bay_default": fbd, "getac_portrait": gpo, "mass_items": placed_mass,
           "sweep": {"%s|%s|%s" % k: v[:20] for k, v in sweep.items()}, "sweep_steps_per_arm": nsteps,
           "counts": {s: sum(1 for r in issues if r["severity"] == s) for s in order}, "steel_chassis_kg": round(steel, 2)}
    json.dump(out, open(os.path.join(HERE, "analysis_summary.json"), "w"), indent=1, default=str)
    print(json.dumps(out["counts"]), json.dumps({k: (round(v["mass"], 1), v["com"]) for k, v in res.items()}), json.dumps(stab))


if __name__ == "__main__":
    main()
