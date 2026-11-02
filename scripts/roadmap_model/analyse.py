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

from frames import FACTS, HERE, MODEL, REPO, datums, glb_nodes, load_yaml, sensor_frames

OWN = {"mech": "fridayali", "elec": "evans-kwashie", "lead": "BotshareAI", "nav": "skunal3318", "manip": "Brinex45",
       "perc": "vineethmanthena", "tech": "panthera-momagdii"}


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


def build_scene(G, P, chest, lift, head_pitch=30):
    """Parts of the robot (the page scene) except the arms."""
    parts = []
    for k, n in G.items():
        env = n["extras"].get("class") == "envelope"  # envelopes are boxes by definition: exact tests on their bounds
        parts.append(Part(k, n["v"], n["f"], "base", boxes=[(n["v"].min(0), n["v"].max(0))] if env else None))
    t, L, Wc, RET, HEAD = .304, .24, .06, .53, .012
    c = t + RET
    i = RET - HEAD - .012
    MOUNT_X, PX, PY, PL = .18, .12, .06, .34
    def add(pid, vf, g, exact=True):
        v = np.asarray(vf[0])
        parts.append(Part(pid, v, vf[1], g, boxes=[(v.min(0), v.max(0))] if (exact and len(v) == 8) else None))
    add("lift_base_plate", box_mesh([.36, .23, .01], [0, 0, t - .005]), "col")
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
                ("getac_portrait_ghost", "*"), ("rear_estop_clear_ghost", "*"), ("k1k2_option_b", "*"), ("tz_receiver", "*"), ("estop", "front_panel"),
                ("reset_button", "front_panel"), ("feedthru", "side_panel"), ("rz_disc", "rear_panel"), ("rz_sb50", "rear_panel"), ("fasteners", "*"),
                ("harness_fittings", "*"), ("shims", "*"), ("us_locknut", "*"), ("lift_bolt_keepout", "*"),
                ("lift_sensor_bracket", "lift_sensor_bracket"), ("flag_rod", "lift_flag"), ("rear_estop_housing", "second_estop"),
                ("bay_plate", "lidar_support"), ("lift_base_plate", "lift_node"), ("lift_column_stage", "lift_column"), ("lift_column_head", "lift_column"),
                ("lift_column_head", "arm_profile"), ("rear_estop", "lift_column")]

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
    # bp050: front lift-plate bolts and the LiDAR support
    lsup = G["lidar_support"]["v"]
    for bp, pts in summ["bolts"].items():
        for (x, y) in pts:
            if x > .135:
                near = lsup[(np.abs(lsup[:, 0] - x) < .03)]
                dy = np.min(np.abs(np.abs(near[:, 1]) - abs(y))) if len(near) else 1
                gap = (abs(y) - .085) * 1000 - 8
                frame_below = "none (cover sheet only; centre bracket ends at x 0.135)"
                issue("major", "MEC-019 front deck bolts / frame", bp, "front bolt at x %.3f, y %+.3f: frame below: %s" % (x, y, frame_below),
                      "B7: bolts go through the deck into the frame below", "M-01 rev19.7 / B7; CAD v0.2 centre bracket x +-0.135",
                      "add a cross member or two standoff tubes from the base sheet under the front bolt row (both bp000 and bp050 rows), or turn the pattern (300 along y) and re-check",
                      OWN["mech"], "load path")
                break
        if bp == "bp050":
            x, y = max(pts)
            issue("major" if (abs(y) - .085 - .008) < .005 else "minor", "MEC-019 bp050 front bolts / LiDAR support MMP.07", "bp050",
                  "bolt axis y %.3f vs support edge 0.085: washer clearance %.1f mm" % (abs(y), (abs(y) - .085 - .008) * 1000),
                  ">= 5 mm tool and washer clearance", "B7 pattern 190 x 300; CAD v0.2 MMP.07", "shift the support or the pattern; check the nut access from the bay", OWN["mech"], "interference")

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
    gp = geos.get("getac_portrait_ghost")
    if gp:
        for other in ("head_light", "arm_profile", "head_camera", "head_camera_bracket"):
            r = pair(gp, geos[other])
            if r and r[1] > .0005:
                issue("major", "getac pocket portrait / %s" % other, "portrait, L1000", "overlap %.1f mm" % (r[1] * 1000), "overlap <= 0.5 mm",
                      "design_intent/getac_pocket_portrait.step; datums head_light_gap_below_tablet", "raise the pivot or move the light bar below the portrait sweep (needs about 16 mm more)", OWN["mech"], "interference")

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
    for tr, nm in ((0.0, "L1000"), (.35, "L1350")):
        tot, mom, unplaced = 0, np.zeros(3), []
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

    # ---- TZBOT receiver
    rx = names.get("tz_receiver")
    if rx:
        g = geos["tz_receiver"]
        bottom = g.lo[2]
        metal = []
        for k in ("base_plate", "castor_front_left", "castor_front_right", "hub_motor_wheel_left", "hub_motor_wheel_right", "lidar_support", "bay_plate", "front_panel"):
            if k in geos:
                r = pair(g, geos[k], .02)
                if r:
                    metal.append((k, round(r[0] * 1000, 1), round(r[1] * 1000, 1)))
        issue("major", "TZBOT receiver WCM-500-24 / floor clearance", "position not documented (drawn provisional under the front bay)",
              "receiver 65 mm tall vs base sheet bottom 52 mm: recess of at least %.0f mm into the base needed for a %.0f mm floor gap" % ((.065 + bottom - .052) * 1000, bottom * 1000),
              "floor gap 0 to 50 mm; no metal within 20 mm", "B5; CAD v0.2 base sheet 52.0 / 54.0 mm", "cut the steel base sheet (280 x 250 mm with the 20 mm metal-free border) and give the receiver its own bracket; pick the zone with the battery and bay layout", OWN["mech"], "tzbot")
        for k, dmin, dep in metal:
            issue("major", "TZBOT receiver / %s (metal within 20 mm)" % k, "provisional receiver position", "clearance %.1f mm, overlap %.1f mm" % (dmin, dep),
                  ">= 20 mm metal-free", "B5 TZBOT WCM-500-24", "cut-out or relocate", OWN["mech"], "tzbot")

    # ---- services and fits from the build summary
    nof = summ["nofit"]
    if nof:
        issue("blocker", "Front bay and rear zone layout / %s" % ", ".join(nof), "proposed layout (packer, 3 mm gaps, 10 mm around converters)",
              "no space for %s after the front bay and both rear side pockets" % ", ".join(nof), "every onboard part placed",
              "parts.yaml catalogue outlines (verify), CAD v0.2 free space", "two-level bay plate or a DIN carrier on the centre-bracket rear wall; re-check with real datasheet outlines; the BMS/PDB layout from the hardware owner is due",
              OWN["elec"], "layout")
    over = [k for k, v in summ["packed"].items() if k.startswith("bay_") and v[0][0] < 0]
    if over:
        issue("major", "Front bay overflow / %s" % ", ".join(over), "proposed layout", "%d front-bay parts only fit in the rear side pockets" % len(over),
              "front bay holds the listed parts (E2)", "packer result (build_summary.json)", "adopt the 28 Oct alternative (DIN parts in the side pockets) or enlarge the bay", OWN["elec"], "layout")
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
    # the MEC-005 single plate
    issue("major", "MEC-005 single removable plate / LiDAR support MMP.07 and electronics bracket MMP.04.00.00.002", "front bay",
          "both stand on the base sheet in the bay: a one-piece plate must pass under the LiDAR support (3 mm) or be two wing plates",
          "one removable flat plate (E1)", "CAD v0.2", "mount the LiDAR support on the plate and shorten the 17.5 mm spacer to 14.5 mm to keep the 222.05 mm scan plane, or split MEC-005", OWN["mech"], "layout")
    issue("major", "Jetson Orin NX with fan on the IMU bracket MMP.04.00.00.002", "CAD v0.2", "compute (with fan) shares the electronics bracket with the EV_ICM-42688-P",
          "nothing heavy or vibrating on the IMU bracket (E2)", "CAD v0.2 compute node on the bracket top", "move the IMU to its own sub-plate on elastomer mounts or move the Jetson; the bay has no 90 mm wide free spot", OWN["mech"], "layout")
    issue("minor", "Battery assembly removal path", "cover off", "cells lift out vertically through the cover opening; 26 mm above the cells, nothing on top (B5)",
          "removable without removing the arms", "B5; lift base plate at x -0.12 to 0.24 (rear edge 17 mm ahead of the cells)", "keep the cover split behind the lift plate", OWN["mech"], "services")
    issue("minor", "Disconnect handle access", "rear panel", "BS-6004B drawn at the rear panel centre above the rear TF-Luna", "reachable from outside", "proposed position", "confirm the panel cut-out", OWN["elec"], "services")
    issue("minor", "Front bay plate removal with the cover off", "cover off", "plate lifts out after the 8 M4 screws; the lift-plate nuts below the deck need the bay keep-outs", "removable with the cover off", "proposed", "keep the keep-outs free of parts", OWN["mech"], "services")
    # service loop
    sd = summ["seed"][0] if summ.get("seed") else {}
    if sd:
        issue("minor" if sd["service_loop_length"] >= sd["service_loop_need"] else "major", "Upper-body service loop length", "L1000 to L1350",
              "loop %.0f mm vs %.0f mm needed at L1350" % (sd["service_loop_length"] * 1000, sd["service_loop_need"] * 1000), "covers the 350 mm stroke plus bend allowance", "harness route", "size the sleeve at build", OWN["elec"], "harness")
    # rod outside the plate (B8) and second E-stop position (B8)
    rodv = names["flag_rod"].world(base_cfg)
    issue("major", "Flag rod LFT-004 / adapter plate MEC-004 footprint", "all lift positions", "rod y %.0f to %.0f mm vs plate edge 50 mm: %.0f to %.0f mm outside" % (rodv[:, 1].min() * 1000, rodv[:, 1].max() * 1000, rodv[:, 1].min() * 1000 - 50, rodv[:, 1].max() * 1000 - 50),
          "inside the plate footprint", "datums.yaml lift_flag_rod_offset_from_face; B8", "rod mount bracket of design_intent/adapter_post (keeps the rod inside) or a 130 mm wide plate", OWN["mech"], "interference")
    issue("major", "Second E-stop at 40 mm below the column top / right gripper", "arm workspace", "hit in the 29 Oct simulation; clear position 180 mm below the top edge (ghost drawn)",
          "no arm contact", "B8; datums second_estop_below_profile_top", "move to the 180 mm position at M-09; housing flange needs >= 50 mm below the top (design intent)", OWN["mech"], "arm reach")
    issue("major", "Getac ZX80 at shoulder height / arms", "arm workspace", "hit in 23 of 154 simulation frames (29 Oct)", "no arm contact", "B8", "M-09 position; MoveIt collision object", OWN["mech"], "arm reach")
    issue("minor", "Left tote wall / sensors S1, S2", "visualization", "3.2 mm overlap", "none", "B8 (visualization only)", "fix the tote model", OWN["tech"], "interference")
    issue("minor", "Hub motor wheel radius 0.100 vs base_link 0.098", "all", "wheel envelope reaches 2 mm below the floor", "wheel radius = base_link height", "datums drive_wheel_radius / base_link_height_above_floor", "decide the rounding to 0.1 (open)", OWN["mech"], "geometry")

    # ---- write
    order = {"blocker": 0, "major": 1, "minor": 2}
    issues.sort(key=lambda r: (order[r["severity"]], r["kind"], r["parts"]))
    for i, r in enumerate(issues):
        r["id"] = "GI-%03d" % (i + 1)
    keys = ["id", "severity", "kind", "parts", "configuration", "measured", "limit", "source", "suggested_fix", "owner"]
    with open(os.path.join(MODEL, "geometry_issues.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in issues:
            w.writerow({k: r[k] for k in keys})
    out = {"self_check": check, "frames": frames, "heights": heights, "mass": res, "stability": stab, "loads": loads, "views": views,
           "sweep": {"%s|%s|%s" % k: v[:20] for k, v in sweep.items()}, "sweep_steps_per_arm": nsteps,
           "counts": {s: sum(1 for r in issues if r["severity"] == s) for s in order}, "steel_chassis_kg": round(steel, 2)}
    json.dump(out, open(os.path.join(HERE, "analysis_summary.json"), "w"), indent=1, default=str)
    print(json.dumps(out["counts"]), json.dumps({k: (round(v["mass"], 1), v["com"]) for k, v in res.items()}), json.dumps(stab))


if __name__ == "__main__":
    main()
