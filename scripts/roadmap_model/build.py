#!/usr/bin/env python3
"""Build the placement data of the OpenAMRobot 2.0 roadmap model from its sources.

Reads datums.yaml (openamr-upperbody-sw), sensor_frames.yaml (openamr-platform-sw), facts.yaml (section B
facts of record), parts.yaml (parts table), bom_map.yaml (BOM line coverage), the PARTS list of hardware.html
(BOM Issue 7.14), the base GLB (model/base_glb.js) and the design-intent index (model/design_intent/index.json).
Writes, under docs/assets/roadmap/model/:
  placement.json         parts the model draws on top of the GLB and the upper-body primitives (model.js loads it)
  exploded.json          entries (stage, exploded and opened-base offsets) for every placement part, stage 9 Harness
  bom_coverage.csv       one row per BOM 7.14 line
  fastener_schedule.csv  every fastener of the model (named or proposed), the start of MEC-014
  cable_list.csv         every cable of the harness with route length plus 10 % service margin
  assembly_sequence.csv  proposed assembly order with tool access checks
Next week's update: edit parts.yaml / bom_map.yaml / facts.yaml and rerun
  python3 scripts/roadmap_model/build.py
Sources are read from ../src (override with OAMR_SRC).
"""
import csv
import html as H
import itertools
import json
import math
import os
import re

import numpy as np

import front_bay as FB
from frames import FACTS, HERE, MODEL, REPO, SENSOR_FRAMES, aabb, bl_to_bf, datums, glb_nodes, lift_rear_layout, load_yaml, sensor_frames, tzbot_layout

R = lambda v, n=4: round(float(v), n)
MM = 0.001

DOMAIN_COL = {"BAT": "#c0392b", "SAFE": "#e67e22", "R24": "#f1c40f", "LV": "#27ae60", "SIG": "#2980b9", "MECH": "#7f8c8d"}
BODY_COL = {"BAT": "#3b3f46", "SAFE": "#4a4036", "R24": "#4b4a36", "LV": "#34463b", "SIG": "#1f3b57", "MECH": "#8a939b"}


# ---------------------------------------------------------------- sources
def bom_parts():
    s = open(os.path.join(REPO, "docs/assets/roadmap/hardware.html"), encoding="utf-8").read()
    i = s.index("var PARTS=") + 10
    parts, _ = json.JSONDecoder().raw_decode(s, i)
    return {k: v for k, v in parts.items() if re.match(r"^[A-Z]+(?:-[A-Z0-9]+)+$", k)}


def upper_body(D, rev):
    """Upper-body reference points (base_footprint, bp000, L1000) derived from datums.yaml and B7."""
    f = FACTS
    ax = f["lift_plate"]["col_axis_x"]["bp000"]
    top = f["lift_plate"]["top"] + f["column"]["retracted"]          # column top / carriage reference at L1000
    prof_front = ax + 0.18 + 0.06
    # owner corrections A3 / A4 / A5 (owner, 2 Nov 2026; to be entered in P-03 and M-01): Getac portrait, centre 40 mm lower; light bar
    # top edge 10 mm below the Getac bottom; ZED lens 57 mm ahead of J1_A; second E-stop on the adapter plate behind the post
    gs = FACTS["getac"]["size"]
    g_z = top + D["getac_tablet_z_above_column_top"] - FACTS["getac"]["lower_by"]
    light_top = g_z - gs[2] / 2 - FACTS["getac"]["light_gap"]
    eh = FACTS["second_estop"]["housing"]
    static_top = top - D["lift_static_profile_top_below_column_top"]
    return {
        "datums_revision": rev, "col_axis_x": ax, "col_top": top, "static_top": static_top,
        "shoulder": [ax + 0.18, 0.031, top + 0.166], "prof_front": prof_front,
        "head_lens": [ax + 0.18 + FACTS["zed_ahead_of_j1a"], 0.0, top + 0.166 + 0.223],
        "getac": [prof_front + gs[0] / 2, 0.0, g_z], "getac_size": gs,
        "head_light": [prof_front + D["head_light_size"][0] / 2, 0.0, light_top - D["head_light_size"][2] / 2],
        "estop2": [ax, 0.0, top + 0.010 + eh[2] / 2], "estop2_actuator_z": round(top + 0.010 + eh[2] + 0.007, 4),
        "estop2_actuator_z_stops": {k: round(top + 0.010 + eh[2] + 0.007 + tr, 4) for k, tr in (("L1000", 0.0), ("L1175", 0.175), ("L1350", 0.350))},
        "col_rear_x": ax - 0.12, "col_front_x": ax + 0.12,
        "lift_sensor_z": [FACTS["lift_plate"]["top"] + D["lift_stop_sensor_z_" + k] for k in ("l1000", "l1175", "l1350")],
    }


# ---------------------------------------------------------------- packer
class Grid:
    """Voxel occupancy (5 mm) of a zone; obstacles and placed parts are boxes."""

    def __init__(self, lo, hi, res=0.005):
        self.lo, self.res = np.array(lo, float), res
        self.n = np.ceil((np.array(hi) - self.lo) / res - 1e-6).astype(int)
        self.occ = np.zeros(self.n, bool)

    def idx(self, lo, hi):
        a = np.floor((np.array(lo) - self.lo) / self.res + 1e-3).astype(int)
        b = np.ceil((np.array(hi) - self.lo) / self.res - 1e-3).astype(int)
        return np.clip(a, 0, self.n), np.clip(b, 0, self.n)

    def block(self, lo, hi):
        a, b = self.idx(lo, hi)
        if (b > a).all():
            self.occ[a[0]:b[0], a[1]:b[1], a[2]:b[2]] = True

    def block_points(self, pts):
        k = np.floor((pts - self.lo) / self.res).astype(int)
        m = ((k >= 0) & (k < self.n)).all(1)
        k = k[m]
        self.occ[k[:, 0], k[:, 1], k[:, 2]] = True

    def free(self, lo, hi):
        lo, hi = np.array(lo), np.array(hi)
        if (lo < self.lo - 1e-9).any() or (hi > self.lo + self.n * self.res + 1e-9).any():
            return False
        a, b = self.idx(lo, hi)
        return not self.occ[a[0]:b[0], a[1]:b[1], a[2]:b[2]].any()


def surface_points(v, f, step=0.002):
    """Points on the triangles of a mesh, at most `step` apart (voxelizes sheet-metal parts as shells)."""
    tri = v[f]
    out = [tri.reshape(-1, 3)]
    e = np.maximum(np.linalg.norm(tri[:, 1] - tri[:, 0], axis=1), np.linalg.norm(tri[:, 2] - tri[:, 0], axis=1))
    for n in sorted(set(np.ceil(e / step).astype(int).clip(1, 200))):
        sel = tri[np.ceil(e / step).astype(int).clip(1, 200) == n]
        if n <= 1:
            continue
        a, b = np.meshgrid(np.arange(n + 1), np.arange(n + 1))
        m = (a + b) <= n
        a, b = a[m] / n, b[m] / n
        p = sel[:, None, 0] + a[None, :, None] * (sel[:, None, 1] - sel[:, None, 0]) + b[None, :, None] * (sel[:, None, 2] - sel[:, None, 0])
        out.append(p.reshape(-1, 3))
    return np.vstack(out)


zone_of = {}
TOP_ACCESS = {"rz_fba", "rz_fbb", "rz_f0", "rz_fchg", "rz_pre"}   # fuses: top access with the cover off (A1 service access)


def pack(items, zones, obstacles, ceiling=None, shells=()):
    """Greedy placement on the zone floor: largest first, domain order fore-aft, 10 mm air gap around converters,
    3 mm elsewhere. Returns {id: (centre, size)} and the ids that do not fit."""
    placed, nofit = {}, []
    zone_of.clear()
    grids = {}
    for zn, z in zones.items():
        g = Grid([z["x"][0], z["y"][0], z["z"][0]], [z["x"][1], z["y"][1], z["z"][1]])
        for lo, hi in obstacles:
            g.block(lo, hi)
        for pts in shells:
            g.block_points(pts)
        import rear_layout
        cf = rear_layout.ceiling if zn.startswith("rear") else (ceiling if zn == "front_bay" else None)
        if cf:
            for ix in range(g.n[0]):
                x = g.lo[0] + (ix + .5) * g.res
                c = cf(x)
                kz = int(max(0, math.floor((c - g.lo[2]) / g.res)))
                g.occ[ix, :, kz:] = True
        grids[zn] = g
    order = sorted(items, key=lambda it: -np.prod(it["dims"]))
    order = order + [dict(it, zone=fz, _fallback=True) for it in order for fz in it.get("fallback", [])]
    for it in order:
        if it.get("_fallback"):
            keys = [it["id"]] if int(it.get("qty", 1)) == 1 else ["%s_%d" % (it["id"], i + 1) for i in range(int(it.get("qty", 1)))]
            if not any(k in nofit for k in keys):
                continue
        g = grids[it["zone"]]
        z = zones[it["zone"]]
        gap = (0.010 if it.get("converter") else it.get("gap", 0.003))
        dims = np.array(it["dims"]) * MM
        perms = sorted(set(itertools.permutations(dims)), key=lambda p: (abs(p[2] - dims[2]) > 1e-9, -p[0]))
        fore = {"BAT": 0, "SAFE": 0, "R24": 1, "LV": 1, "SIG": 2}.get(it["domain"], 1)
        xs = np.arange(z["x"][0], z["x"][1], g.res)
        if it["zone"] == "front_bay" and fore == 2:
            xs = xs[::-1]  # signal parts toward the front, power entry toward the rear zone
        ys = np.arange(z["y"][0], z["y"][1], g.res)
        ys = sorted(ys, key=lambda y: -abs(y))  # outboard first
        best = None
        for qty_i in range(int(it.get("qty", 1))):
            best = None
            for p in perms:
                p = np.array(p)
                zs = [z["z"][0]] if (it["zone"] == "front_bay" or z.get("floor_only")) else list(np.arange(z["z"][0], z["z"][1], 0.01))
                for x, zz in ((a, b) for b in zs for a in xs):
                    for y in ys:
                        lo = np.array([x, y, zz])
                        hi = lo + p
                        zlo = np.array([z["x"][0], z["y"][0], z["z"][0]])
                        zhi = np.array([z["x"][1], z["y"][1], z["z"][1]])
                        if (hi > zhi + 1e-6).any():
                            continue
                        gz = 0 if zz <= z["z"][0] + 1e-9 else gap
                        if g.free(np.maximum(lo - [gap, gap, gz], zlo), np.minimum(hi + [gap, gap, gap], zhi)):
                            # service access (A1): nothing above a fuse block or fuse holder, and a fuse part never goes under another part
                            over = lambda a, b: (a[0][0] < b[1][0] and b[0][0] < a[1][0] and a[0][1] < b[1][1] and b[0][1] < a[1][1])
                            blocked = False
                            for k2, (c2, p2) in placed.items():
                                if zone_of.get(k2) != it["zone"]:
                                    continue
                                b2 = (c2 - p2 / 2, c2 + p2 / 2)
                                if over((lo, hi), b2) and ((k2.rsplit("_", 1)[0] in TOP_ACCESS or k2 in TOP_ACCESS) and lo[2] >= b2[1][2] - 1e-6
                                                         or (it["id"] in TOP_ACCESS) and hi[2] <= b2[0][2] + 1e-6):
                                    blocked = True
                                    break
                            if blocked:
                                continue
                            best = (lo + p / 2, p)
                            break
                    if best:
                        break
                if best:
                    break
            key = it["id"] if int(it.get("qty", 1)) == 1 else "%s_%d" % (it["id"], qty_i + 1)
            if it.get("_fallback") and key not in nofit:
                continue
            if best:
                c, p = best
                g.block(c - p / 2, c + p / 2)
                placed[key] = best
                zone_of[key] = it["zone"]
                if key in nofit:
                    nofit.remove(key)
            elif key not in nofit:
                nofit.append(key)
    return placed, nofit


# ---------------------------------------------------------------- geometry helpers
def box(s, p, c, o=None, r=None, hq=False, name=None):
    d = {"t": "box", "s": [R(v) for v in s], "p": [R(v) for v in p], "c": c}
    if o is not None:
        d["o"] = o
    if r is not None:
        d["r"] = [R(v) for v in r]
    if hq:
        d["hq"] = 1
    if name:
        d["n"] = name
    return d


def cyl(r, h, p, ax, c, o=None, hq=False):
    d = {"t": "cyl", "r": R(r, 5), "h": R(h, 5), "p": [R(v) for v in p], "ax": ax, "c": c}
    if o is not None:
        d["o"] = o
    if hq:
        d["hq"] = 1
    return d


def tube(pts, r, c):
    return {"t": "tube", "pts": [[R(v) for v in q] for q in pts], "r": R(r, 5), "c": c}


def plen(pts):
    return float(sum(np.linalg.norm(np.subtract(pts[i + 1], pts[i])) for i in range(len(pts) - 1)))


# ---------------------------------------------------------------- harness graph (base_footprint, bp000, L1000)
def harness_graph(U):
    ax, top = U["col_axis_x"], U["col_top"]
    Z = 0.245
    ZF = 0.278   # front bay trunk: over the option A DIN carrier and shelf parts, under the cover (0.290)
    ZL = 0.205   # front sensor run: below the LiDAR scan plane band (0.217 to 0.227) in the open sector (C3)
    N = {
        # front bay trunk (above the bay parts, under the cover); it drops below the scan plane at x 0.300, behind the open sector
        "FL1": (0.150, 0.150, ZF), "FL2": (0.300, 0.150, ZF), "FR1": (0.150, -0.150, ZF), "FR2": (0.300, -0.150, ZF),
        "FL3": (0.300, 0.150, ZL), "FL4": (0.345, 0.150, ZL), "FR3": (0.300, -0.150, ZL), "FR4": (0.345, -0.150, ZL),
        "FC": (0.150, 0.0, ZF), "FCF": (0.255, 0.0, ZF), "FCL": (0.385, 0.0, ZL), "FCL_L": (0.385, 0.150, ZL), "FCL_R": (0.385, -0.150, ZL),
        # through the centre-bracket walls (grommets) and across the drive section, above the wheels
        "GCF_L": (0.118, 0.150, Z), "GCF_R": (0.118, -0.150, Z), "CL": (0.0, 0.125, Z), "CR": (0.0, -0.125, Z),
        "GCR_L": (-0.118, 0.125, Z), "GCR_R": (-0.118, -0.125, Z), "CC": (0.0, 0.0, 0.250),
        # rear section (A1): trunk over the series-link strip at the arch edge, then over the power plate (cells in the side pockets)
        "RL1": (-0.152, 0.100, 0.278), "RL2": (-0.152, 0.030, 0.278), "RL3": (-0.300, 0.050, 0.275),
        "RR1": (-0.152, -0.100, 0.278), "RR2": (-0.152, -0.030, 0.278), "RR3": (-0.300, -0.050, 0.275), "RB": (-0.310, 0.0, 0.275),
        # up through the deck behind the lift plate, beside the static column, service loop to the carriage
        "D0": (-0.128, -0.050, 0.250), "GD": (-0.128, -0.050, 0.296), "SL0": (ax - 0.135, -0.045, 0.330),
        "SL1": (ax - 0.135, -0.045, top - 0.040), "SLB": (ax - 0.150, -0.045, top - 0.280),
        "SL2": (ax - 0.115, -0.045, top - 0.020),
        # on the carriage (moving): under the adapter plate, up the arm post; MR: through the adapter plate to the second E-stop (A5)
        "M0": (ax - 0.100, -0.040, top - 0.006), "M1": (ax + 0.100, -0.040, top - 0.006),
        "MP": (ax + 0.120, 0.0, top + 0.020), "MJ_L": (ax + 0.150, 0.038, top + 0.166), "MJ_R": (ax + 0.150, -0.038, top + 0.166),
        "MT": (ax + 0.160, 0.0, top + 0.352), "MF": (ax + 0.250, 0.0, top + 0.120),
        "MR0": (ax - 0.040, 0.0, top + 0.016), "MR": (ax - 0.040, 0.0, top - 0.006),
        # static column: lift sensors on the +y face
        "CY_T": (ax - 0.132, -0.030, 0.80), "CY_B": (ax - 0.132, -0.030, 0.330),   # A6: down the rear face of the static column
    }
    group = {k: "base" for k in N}
    for k in ("SL0", "SL1", "SLB", "CY_T", "CY_B"):
        group[k] = "col"
    for k in ("SL2", "M0", "M1", "MP", "MJ_L", "MJ_R", "MT", "MF", "MR0", "MR"):
        group[k] = "mov"
    E = [("FL1", "FL2"), ("FR1", "FR2"), ("FL1", "FC"), ("FR1", "FC"), ("FC", "FCF"), ("FL2", "FL3"), ("FL3", "FL4"), ("FR2", "FR3"), ("FR3", "FR4"),
         ("FL4", "FCL_L"), ("FR4", "FCL_R"), ("FCL_L", "FCL"), ("FCL_R", "FCL"), ("FCF", "FL2"), ("FCF", "FR2"),
         ("FL1", "GCF_L"), ("FR1", "GCF_R"), ("GCF_L", "CL"), ("GCF_R", "CR"), ("CL", "CC"), ("CR", "CC"),
         ("CL", "GCR_L"), ("CR", "GCR_R"), ("GCR_L", "RL1"), ("GCR_R", "RR1"), ("RL1", "RL2"), ("RL2", "RL3"),
         ("RR1", "RR2"), ("RR2", "RR3"), ("RL3", "RB"), ("RR3", "RB"), ("CC", "D0"), ("CR", "D0"), ("D0", "GD"),
         ("GD", "SL0"), ("SL0", "SL1"), ("SL1", "SLB"), ("SLB", "SL2"), ("SL2", "M0"), ("M0", "M1"), ("M1", "MP"),
         ("MP", "MJ_L"), ("MP", "MJ_R"), ("MP", "MT"), ("MP", "MF"), ("M0", "MR"), ("MR", "MR0"), ("GD", "CY_B"),
         ("CY_B", "CY_T")]
    return N, group, E


def route(N, E, a, b):
    import heapq
    adj = {}
    for u, v in E:
        w = float(np.linalg.norm(np.subtract(N[u], N[v])))
        adj.setdefault(u, []).append((v, w))
        adj.setdefault(v, []).append((u, w))
    dist, prev, q = {a: 0}, {}, [(0, a)]
    while q:
        d, u = heapq.heappop(q)
        if u == b:
            break
        for v, w in adj.get(u, []):
            if d + w < dist.get(v, 1e9):
                dist[v], prev[v] = d + w, u
                heapq.heappush(q, (d + w, v))
    path, u = [b], b
    while u != a:
        u = prev[u]
        path.append(u)
    return path[::-1]


def write_lift_json(LR):
    """Write M.LIFT_SENSE in model.js from frames.lift_rear_layout() (A6): the pages and the checker read it."""
    f = FACTS["lift_rear"]
    js_path = os.path.join(MODEL, "model.js")
    js = open(js_path, encoding="utf-8").read()
    L = {"face": "rear", "z": f["sensor_z"], "stops": ["L1000", "L1175", "L1350"], "sensor": f["sensor"], "rear_x": f["column_rear_x"],
         "axis_x": LR["sensor_axis_x"], "face_y": LR["face_y"], "gap": f["gap"], "flag": f["flag"], "flag_x": LR["flag_x"], "flag_y": LR["flag_y"],
         "flag_below_plate": f["flag_below_plate"], "rod": f["rod"], "rod_x": LR["rod_x"], "rod_y": LR["rod_y"], "corner_x": LR["corner_x"],
         "rod_clear": f["rod_clear"], "bracket": {"leg": f["bracket"]["leg"], "t": f["bracket"]["t"], "at": f["bracket"]["axis_from_face"]},
         "bracket_h": f["bracket"]["h"], "plate_rear_x": LR["plate_rear_x"]}
    new = "/*LIFT-JSON*/%s/*LIFT-JSON-END*/" % json.dumps(L)
    js2 = re.sub(r"/\*LIFT-JSON\*/.*?/\*LIFT-JSON-END\*/", lambda m: new, js, flags=re.S)
    if js2 != js:
        open(js_path, "w", encoding="utf-8").write(js2)


# ---------------------------------------------------------------- main build
def main():
    rev, D = datums()
    SF = sensor_frames()
    G = glb_nodes()
    T = load_yaml(os.path.join(HERE, "parts.yaml"))
    for it in T["fixed"]:
        if it["id"] == "lift_node":   # A6: below the L1000 sensor on the rear face of the static column
            it["pos"] = [it["pos"][0], it["pos"][1], FACTS["lift_rear"]["lift_node_z"]]
    TZL = tzbot_layout()
    LR = lift_rear_layout()   # A6: lift stop sensors and flag rod at the rear of the column
    write_lift_json(LR)   # receiver box from facts.yaml (WCM-500-24 manual V2.5, B4 position); the parts table follows it
    for it in T["fixed"]:
        if it["id"] == "tz_receiver":
            it["dims"] = [round(v * 1000, 1) for v in TZL["size"]]
            it["pos"] = [R(v) for v in TZL["centre"]]
    BM = load_yaml(os.path.join(HERE, "bom_map.yaml"))
    BOM = bom_parts()
    U = upper_body(D, rev)
    di_path = os.path.join(MODEL, "design_intent", "index.json")
    DI = json.load(open(di_path)) if os.path.exists(di_path) else []
    if isinstance(DI, dict):
        DI = DI.get("items", list(DI.values()))

    box_of = {k: aabb(v["v"]) for k, v in G.items()}
    comps, geo, exploded, fasteners, cables, issues_seed = [], {}, {}, [], [], []

    def comp(cid, name, bom, qty, cls, purpose, geom_src, pos_src, mass, msrc, stage, parts, group="base", label=None, off=None, opn=None,
             hq=False, link=None, part_number=""):
        c = {"id": cid, "name": name, "qty": qty, "geometry": "envelope" if cls in ("provisional", "envelope", "placeholder") else "primitive",
             "bom": bom, "purpose": purpose, "source": geom_src, "class": cls, "position_source": pos_src, "mass_kg": R(mass, 3),
             "mass_source": msrc, "part_number": part_number,
             "link": link or "https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md",
             "parts": list(parts)}
        if cls == "provisional":
            c["provisional_label"] = label or "Provisional position: no source gives it"
        if cls == "placeholder":
            c["placeholder"] = True
            c["label"] = label or "Placeholder"
        if cls == "proposed":
            c["proposed"] = True
            c["label"] = label or "Proposed by the roadmap model (not a decision)"
        if hq:
            c["hq"] = True
        comps.append(c)
        exploded[cid] = {"stage": stage, "offsets": {p: (off or [0, 0, .2]) for p in parts}, "open": {p: (opn or [0, 0, .12]) for p in parts}}
        for p in parts:
            geo.setdefault(p, {"group": group, "prims": []})
        return c

    SW = "https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/config/sensor_frames.yaml"
    HW = "https://github.com/openAMRobot/openamr-platform-hw/tree/main/mechanical/cad/production_files"

    # ---------------- obstacles (GLB AABBs) for the packer
    obst, shells = [], []
    for k, (lo, hi) in box_of.items():
        if k in ("base_plate", "cover", "cover_flange_front", "cover_flange_rear", "battery"):
            continue
        if G[k]["extras"].get("class") == "chassis" and k not in ("electronics_bracket", "lidar_support", "lidar_spacer", "driver_mount", "controller_plate"):
            shells.append(surface_points(G[k]["v"], G[k]["f"]))
            continue
        obst.append((lo - 0.003, hi + 0.003))
    lp = FACTS["lift_plate"]
    # lift base plate on the arch (B3): the same 4 arch bolts for bp000 and bp050 (the plate carries both column hole sets)
    arch_bolts = [(x, y) for x in lp["arch_bolts"]["x"] for y in lp["arch_bolts"]["y"]]
    bolts = {bp: arch_bolts for bp in lp["col_axis_x"]}
    # rear section (owner correction A1): cells and pocket trays, the receiver 20 mm metal-free margin and the series link strip
    import rear_layout
    RL = rear_layout.layout()
    for t_ in RL["trays"]:
        obst.append((np.array(t_["lo"]) - 0.003, np.array(t_["hi"]) + 0.003))
    obst.append((np.array(RL["margin"][0]), np.array(RL["margin"][1])))
    obst.append((np.array([-0.168, -0.105, RL["link_z"] - 0.012]), np.array([-0.137, 0.105, 0.290])))   # series link strip over the zone
    # A9: two removable trays joined by the keyed main connector PWR-018, the disconnect point of the 8S link over the centre
    cl0 = [c_ for c_ in RL["cells"] if c_["side"] == "left"]
    bc_c = np.array([max(c_["hi"][0] for c_ in cl0) - 0.025, 0.0, RL["link_z"]])
    bc_s = np.array([0.030, 0.060, 0.040])
    obst.append((bc_c - bc_s / 2 - 0.003, bc_c + bc_s / 2 + 0.003))
    # fixed parts of the parts table and the design-intent battery tray are obstacles too
    for it in T["fixed"]:
        if it.get("group", "base") != "base" or "dims" not in it or it["id"] in ("tz_receiver", "fan"):
            continue
        for rp in it.get("repeat", [[0, 0, 0]]):
            c0 = np.add(it["pos"], rp)
            h = np.array(it["dims"]) * MM / 2
            obst.append((c0 - h - .003, c0 + h + .003))
    tray = []
    # front-bay ceiling: cover underside, then the front flange slope
    def ceiling(x):
        return FACTS["cover_underside"] if x < 0.315 else FACTS["cover_underside"] - (x - 0.315) * (0.0628 / 0.0706)

    pz = RL["plate"]
    zones = {"rear_plate": {"x": [pz[0][0], pz[1][0]], "y": [pz[0][1], pz[1][1]], "z": [pz[1][2], FACTS["cover_underside"]]}}
    for s_, nm_ in ((1, "rear_corner_l"), (-1, "rear_corner_r")):   # pocket rear corners behind the cell trays, inside the rear supports
        y_ = sorted([s_ * (RL["margin"][1][1] + 0.002), s_ * 0.1658])
        zones[nm_] = {"x": [-0.366, RL["trays"][0]["lo"][0] - 0.004], "y": y_, "z": [0.057, 0.264]}
    for k in ("compute", "base_controller"):   # moved to the front bay (option A); the old places are free
        obst[:] = [o for o in obst if not (np.allclose(o[0], box_of[k][0] - 0.003) and np.allclose(o[1], box_of[k][1] + 0.003))]
    obst.append((np.array([0.005, -0.035, 0.054]), np.array([0.075, 0.035, 0.294])))     # IMU column: nothing heavy or vibrating above the IMU
    # rear zone (C2): 5 mm clearance to the tray, the cells and each other (10 mm around converters), real pocket section
    items = [dict(it, gap=0.005) for it in T["packed"] if it["zone"] != "front_bay" and it["id"] != "rz_batcon"]   # PWR-018 sits on the link (A9)
    placed, nofit = pack(items, zones, obst, None, shells)
    zo = dict(zone_of)
    print("rear packed:", len(placed), "no fit:", nofit)
    # GI-080 (A9, owner correction of 2 Nov 2026): parts without space are tried in order, the first that fits with fuse and
    # connector access is kept: 1) a second level above the power plate inside the cover height; 2) FB-B moved to the front
    # bay near the motor driver (25 mm² SAFE bus from K2 drawn); 3) the BMS upright on the rear panel inner face above the
    # receiver, outside the 20 mm metal-free margin. Nothing ever goes on top of the cells (the trays are obstacles).
    gi80 = {"first_pass_nofit": list(nofit), "steps": [], "fbb_front": False}
    keyed = lambda nf, it: any(k == it["id"] or k.startswith(it["id"] + "_") for k in nf)

    def plate_obstacles(pl, zo_, zones_=("rear_plate",)):
        ob = list(obst)
        for k_, (c_, p_) in pl.items():
            if zo_.get(k_) in zones_ or zones_ == "*":
                lo_, hi_ = c_ - p_ / 2 - 0.005, c_ + p_ / 2 + 0.005
                if k_ in TOP_ACCESS or k_.rsplit("_", 1)[0] in TOP_ACCESS:
                    hi_ = np.array([hi_[0], hi_[1], 1.0])   # nothing above a fuse
                ob.append((lo_, hi_))
        return ob

    if nofit:   # 1) second level above the power plate: level 1 on the plate, a shelf just above the tallest non-fuse part
        zf1 = dict(zones)
        zf1["rear_plate"] = dict(zones["rear_plate"], floor_only=True)
        pl1, nf1 = pack(items, zf1, obst, None, shells)
        zo1 = dict(zone_of)
        rp_ = [(c_, p_) for k_, (c_, p_) in pl1.items() if zo1.get(k_) == "rear_plate" and not (k_ in TOP_ACCESS or k_.rsplit("_", 1)[0] in TOP_ACCESS)]
        z2 = round(max((c_[2] + p_[2] / 2 for c_, p_ in rp_), default=pz[1][2]) + 0.008, 4)
        zl2 = {"rear_l2": {"x": [pz[0][0], pz[1][0]], "y": [pz[0][1], pz[1][1]], "z": [z2 + 0.003, FACTS["cover_underside"]], "floor_only": True}}
        pl2, nf2 = pack([dict(it, zone="rear_l2", fallback=[]) for it in items if keyed(nf1, it)], zl2, plate_obstacles(pl1, zo1), None, shells)
        gi80["steps"].append({"option": 1, "what": "second level above the power plate: level 1 on the plate, shelf underside %.0f mm above the floor (tallest non-fuse part + 8 mm), %.0f mm to the cover underside; fuse columns kept open" % (
                                  z2 * 1000, (FACTS["cover_underside"] - z2 - 0.003) * 1000), "level1_nofit": nf1, "placed": sorted(pl2), "nofit": nf2})
        if not nf2:
            placed, zo = pl1, zo1
            placed.update(pl2)
            zo.update({k_: "rear_l2" for k_ in pl2})
            nofit = []
    if any(k_.startswith("rz_fbb") for k_ in nofit):   # 2) FB-B to the front bay (trial with the front-bay layout; kept only if it fits)
        fbb_it = dict([it for it in T["packed"] if it["id"] == "rz_fbb"][0], zone="front_bay", top_access=True, priority=0)
        trial_items = [dict(it) for it in T["packed"] if it["zone"] == "front_bay"] + [dict(v, id=k, zone="front_bay") for k, v in FB.CATALOGUE.items()] + [fbb_it]
        FB.TIER["rz_fbb"] = "lower"
        trial = FB.layout(trial_items)
        ok2 = "rz_fbb" in trial["placed"] and not [k_ for k_ in trial["nofit"] if k_ != "rz_fbb"]
        if ok2:
            items = [it for it in items if it["id"] != "rz_fbb"]
            placed, nofit = pack(items, zones, obst, None, shells)
            zo = dict(zone_of)
            gi80["fbb_front"] = True
        else:
            del FB.TIER["rz_fbb"]
        gi80["steps"].append({"option": 2, "what": "FB-B (SAFE-bus fuse block, 70 x 165 x 100 mm, fuses reached from above) to the front bay near the motor driver",
                              "fits": ok2, "front_bay_layout": trial.get("layout", ""), "front_bay_nofit": list(trial["nofit"]), "rear_nofit_after": list(nofit)})
    if any(k_.startswith("rz_bms") for k_ in nofit):   # 3) BMS upright on the rear panel inner face above the receiver
        xr = FACTS["rear_section"]["rear_panel_inner_x"]
        zf = {"rear_panel_face": {"x": [xr + 0.002, xr + 0.002 + 0.045], "y": [-0.200, 0.200], "z": [RL["margin"][1][2], FACTS["cover_underside"]]}}
        pl3, nf3 = pack([dict(it, zone="rear_panel_face", fallback=[]) for it in items if it["id"] == "rz_bms"], zf, plate_obstacles(placed, zo, "*"), None, shells)
        gi80["steps"].append({"option": 3, "what": "BMS upright on the rear panel inner face above the receiver, outside the 20 mm metal-free margin", "placed": sorted(pl3), "nofit": nf3})
        if not nf3:
            placed.update(pl3)
            zo.update({k_: "rear_panel_face" for k_ in pl3})
            nofit = [k_ for k_ in nofit if not k_.startswith("rz_bms")]
    zone_of.clear()
    zone_of.update(zo)
    gi80["final_nofit"] = list(nofit)
    print("GI-080:", json.dumps(gi80["steps"]), "final no fit:", nofit)
    # front bay: one layout (A2); the receiver is at the rear (A1)
    fb_items = [dict(it) for it in T["packed"] if it["zone"] == "front_bay"] + [dict(v, id=k, zone="front_bay") for k, v in FB.CATALOGUE.items()]
    if gi80["fbb_front"]:   # GI-080 option 2 kept: FB-B in the front bay, top access to its fuses
        fb_items.append(dict([it for it in T["packed"] if it["id"] == "rz_fbb"][0], zone="front_bay", top_access=True, priority=0))
    fb_default = "single"   # owner correction A2 (2 Nov 2026): one layout, no options
    FBR = {fb_default: FB.layout([dict(i) for i in fb_items])}
    fb_fit = {k: FB.fit_numbers(v, fb_items) for k, v in FBR.items()}
    print("front bay:", {k: (v["placed"], v["not_placed"]) for k, v in fb_fit.items()})
    items = [dict(it, zone="front_bay") if (gi80["fbb_front"] and it["id"] == "rz_fbb") else dict(it) for it in T["packed"]]

    # ---------------- packed parts (rear zone) and the front bay of both options
    stage_of = {"front_bay": 4, "rear_plate": 3, "rear_corner_l": 3, "rear_corner_r": 3, "rear_l2": 3, "rear_panel_face": 3}
    ZONE_TXT = {"rear_plate": "rear power-electronics plate above the reserved receiver zone (A1)", "rear_l2": "second level above the rear power plate (GI-080 option 1)",
                "rear_panel_face": "rear panel inner face above the receiver, outside its 20 mm metal-free margin (GI-080 option 3)", "rear_corner_l": "left pocket rear corner behind the cells (A1)",
                "rear_corner_r": "right pocket rear corner behind the cells (A1)", "rear_behind": "rear zone behind the cells (B5)", "rear_side_l": "rear zone, left side pocket (B5, real section)",
                "rear_side_r": "rear zone, right side pocket (B5, real section)",
                "arch": "under the arch top above the hub motors (overflow proposal, not B5: the B5 rear zone is too small with the tray and the real pocket section)", "A_lower": "front bay, lower plate on the base sheet (power conversion and safety)",
                "A_upper": "front bay, upper shelf (second tier)", "A_din": "front bay, DIN carrier on the centre-bracket front wall", "bay": "front bay, single plate on the base sheet",
                "strip_l": "front bay, left strip beside the receiver (under the bay plate)", "strip_r": "front bay, right strip beside the receiver (under the bay plate)",
                "B_bay": "front bay option B, single tier above the receiver", "pocket_l": "option B, left rear side pocket", "pocket_r": "option B, right rear side pocket"}
    fb_relocate = {}
    item_by_id = {it["id"]: it for it in fb_items}
    item_by_id["bay_din_pnoz"] = dict(item_by_id["bay_din"], id="bay_din_pnoz", dims=[120.3, 22.5, 98.0])
    item_by_id["bay_din_tb"] = dict(item_by_id["bay_din"], id="bay_din_tb", dims=[31.2, 47.5, 42.5], standoff=None)

    def draw_box_part(k, it, cc, p, option=None):
        prims = geo.setdefault(k, {"group": "base", "prims": []})["prims"]
        if option:
            geo[k]["option"] = option
        prims.append(box(p, cc, BODY_COL[it["domain"]], name=it["id"]))
        prims.append(box([p[0] * .9, p[1] * .9, .0015], [cc[0], cc[1], cc[2] + p[2] / 2 + .00075], DOMAIN_COL[it["domain"]]))
        if it.get("standoff") and p[2] < 0.03:
            for sx in (-1, 1):
                for sy in (-1, 1):
                    prims.append(cyl(.0028, .006, [cc[0] + sx * (p[0] / 2 - .004), cc[1] + sy * (p[1] / 2 - .004), cc[2] - p[2] / 2 + .003], "z", "#b8b8b8", hq=True))

    for it in items:
        q = int(it.get("qty", 1))
        keys = [it["id"]] if q == 1 else ["%s_%d" % (it["id"], i + 1) for i in range(q)]
        bomrow = BOM.get(it["bom"], {})
        pn = it.get("part", bomrow.get("Model / order code", ""))
        for opt in (fb_default,):
            suffix = ""
            if it["zone"] == "front_bay":
                P = FBR[opt]["placed"]
                sub = {"bay_din": ["bay_din_pnoz", "bay_din_tb"]}.get(it["id"], keys)
                got = [k for k in sub if k in P]
                where = {k: (P[k][0], P[k][1], P[k][2]) for k in got}
            else:
                got = [k for k in keys if k in placed]
                where = {k: (zone_of.get(k, it["zone"]), placed[k][0], placed[k][1]) for k in got}
            if not got:
                continue
            zn = where[got[0]][0]
            parts_ = [k + suffix for k in got]
            label = None if not suffix else "Front bay option %s (alternative, hidden by default; switch on the exploded view)" % opt
            c = comp(it["id"] + suffix, it["name"] + ("" if not suffix else " (option %s)" % opt), it["bom"], len(got) if it["id"] != "bay_din" else 1, "proposed",
                     "%s. %s" % (it["name"], "Placed by scripts/roadmap_model/%s with %s air gap." % ("front_bay.py" if it["zone"] == "front_bay" else "build.py", "10 mm" if it.get("converter") else ("5 mm" if it["zone"] != "front_bay" else "3 mm"))),
                     "%s: %s" % (it.get("geom", "proposed size"), "x".join("%g" % d for d in it["dims"]) + " mm"),
                     "proposed in the %s (%s domain)" % (ZONE_TXT.get(zn, zn), it["domain"]),
                     (it.get("mass", 0) * (len(got) if it["id"] != "bay_din" else 1)) if not suffix else 0,
                     "estimate" if "proposed" in it.get("geom", "proposed") else "estimate from the catalogue class",
                     stage_of[it["zone"]], parts_, part_number=pn, label=label,
                     off=[0, 0, .32] if it["zone"] == "front_bay" else [-.25, 0, .3], opn=[0, 0, .16] if it["zone"] == "front_bay" else [-.12, 0, .14])
            for k in got:
                zn_k, cc, p = where[k]
                draw_box_part(k + suffix, item_by_id.get(k, it), cc, p, None)
                if not suffix and it["zone"] == "front_bay" and item_by_id.get(k, it).get("standoff") and p[2] < 0.03:
                    fasteners.append({"joint": "%s to the MEC-005 plate" % it["name"], "part": "%s hex standoff + ISO 7380 screw" % it["standoff"],
                                      "size": "%s x 6" % it["standoff"], "qty": 4, "standard": "DIN 7380 / hex standoff", "material": "A2 / brass",
                                      "class": "proposed", "drawn": "y"})
    # compute and NUCLEO: the base GLB nodes are moved by the option layout (model.js M.setFrontBay)
    for opt in (fb_default,):
        rel = {}
        for k in ("compute", "base_controller"):
            if k in FBR[opt]["placed"]:
                _, cc, p = FBR[opt]["placed"][k]
                lo, hi = box_of[k]
                d0 = hi - lo
                yaw = 0.0 if abs(p[0] - d0[0]) < abs(p[0] - d0[1]) else math.pi / 2
                rel[k] = {"p": [R(cc[0]), R(cc[1]), R(cc[2] - FACTS["base_link_z"])], "yaw": R(yaw, 5),
                          "zone": FBR[opt]["placed"][k][0]}
        fb_relocate[opt] = rel
    fb_glb_centre = {k: [R(v) for v in (box_of[k][0] + box_of[k][1]) / 2 - [0, 0, FACTS["base_link_z"]]] for k in ("compute", "base_controller")}
    # option plates (MEC-005 lower plate, shelf, DIN carrier; option B single plate)
    for opt in (fb_default,):
        suffix = ""
        pl = FBR[opt]["plates"]
        k = "bay_plate" + suffix
        geo[k] = {"group": "base", "prims": [box(np.subtract(q["hi"], q["lo"]), np.add(q["hi"], q["lo"]) / 2, "#b9c2c9" if "DIN" not in q["name"] else "#8e9aa3", name=q["name"]) for q in pl]}
        area = sum((q["hi"][0] - q["lo"][0]) * (q["hi"][1] - q["lo"][1]) * (q["hi"][2] - q["lo"][2]) for q in pl)
        c = comp(k, "Front bay plates: %s" % "; ".join(q["name"] for q in pl), "MEC-005", 1, "proposed",
                 "Front bay, one layout (owner correction A2, 2 Nov 2026): %s, plate on the base sheet (top z %.3f); %s." % (FBR[opt].get("layout", ""), FB.FLOOR, "lower plate, upper shelf on standoffs and DIN carrier on the centre-bracket front wall" if "two-tier" in FBR[opt].get("layout", "") else "single plate"),
                 "proposed outlines (3 mm 5052 sheet; DIN carrier 23 mm)", "front bay (front_bay.py)", area * 2680,
                 "outline x thickness x 2680 kg/m3", 4, [k], off=[0, 0, .28], opn=[0, 0, .14], part_number="MEC-005 (drawing revision TBD)",
                 label=None)
    geo_lookup = {}

    # ---------------- fixed parts
    for it in T["fixed"]:
        reps = it.get("repeat", [[0, 0, 0]])
        parts = [it["id"]] if len(reps) == 1 else ["%s_%d" % (it["id"], i + 1) for i in range(len(reps))]
        grp = it.get("group", "base")
        cls = it.get("cls", "proposed")
        bomrow = BOM.get(it.get("bom", ""), {})
        lab = None
        if cls == "provisional":
            lab = "Provisional: %s" % it["pos_src"]
        c = comp(it["id"], it["name"], it.get("bom", ""), len(parts), cls, it["name"] + ".",
                 "%s%s" % (it.get("geom", ""), (": " + "x".join("%g" % d for d in it["dims"]) + " mm") if "dims" in it else ""),
                 it["pos_src"], it.get("mass", 0) * (1 if it["id"] in ("tz_receiver", "rz_disc") else len(parts)), "estimate",
                 {"base": 3, "col": 7, "mov": 8}[grp] if it["id"] not in ("fan", "feedthru") else 4, parts, group=grp, label=lab,
                 part_number=it.get("part", bomrow.get("Model / order code", "")), hq=it["id"] in ("shims", "us_locknut"),
                 off=[0, 0, -.25] if it["id"] == "tz_receiver" else None)
        if it["id"] == "tz_receiver":
            c["class"] = "reserved, not installed in 2.0"
            c["provisional_label"] = "Reserved, not installed in 2.0 (wireless charging is a release 3.0 item)"
        for k, rp in zip(parts, reps):
            p = np.add(it["pos"], rp)
            if grp in ("col", "mov"):
                p = p - [FACTS["lift_plate"]["col_axis_x"]["bp000"], 0, 0]
            col = "#9aa3ab" if it.get("domain") == "MECH" else BODY_COL.get(it.get("domain", "SIG"))
            o = .45 if cls == "provisional" else None
            if "cyl" in it:
                geo[k]["prims"].append(cyl(it["cyl"]["r"], it["cyl"]["h"], p, it["cyl"]["axis"], "#b0b4b8", hq=True))
            else:
                geo[k]["prims"].append(box(np.array(it["dims"]) * MM, p, col, o=o, hq=it["id"] == "shims"))
    # ---------------- rear section, owner correction A1 (owner, 2 Nov 2026; to be entered in P-03 and M-01): TZBOT receiver zone reserved in the
    # middle (not installed in 2.0, wireless charging is a release 3.0 item), 8 x LF105 in the two side pockets, power electronics above
    TZ = FACTS["tzbot_receiver"]
    mz = RL["margin"]
    geo["tz_metal_free_zone"] = {"group": "base", "prims": [box(np.subtract(mz[1], mz[0]), np.add(mz[0], mz[1]) / 2, "#e74c3c", o=.10, name="metal_free_zone")]}
    comp("tz_metal_free_zone", "TZBOT receiver 20 mm metal-free margin (ghost, at the rear panel)", "", 1, "proposed",
         "The receiver outline plus 20 mm on every side: no metal inside it (TZBOT WCM-500-24 manual V2.5). Reserved for release 3.0.", "receiver outline + 20 mm",
         "receiver at the rear panel on the centre line (owner, 2 Nov 2026)", 0, "no mass", 3, ["tz_metal_free_zone"], label="Keep-out ghost, not a part", off=[0, 0, -.25], opn=[0, 0, -.12])
    cz = RL["cutout"]
    geo["base_cutout"] = {"group": "base", "prims": [box([cz[1][0] - cz[0][0], cz[1][1] - cz[0][1], 0.0022], [(cz[0][0] + cz[1][0]) / 2, 0, 0.053], "#e67e22", o=.35, name="base_sheet_cutout")]}
    comp("base_cutout", "Base-sheet cut-out reserved for the receiver (at the rear panel)", "MEC-001", 1, "proposed",
         "Base sheet MMP.02.00.00.001 cut-out under the reserved receiver zone: receiver outline plus the 20 mm metal-free margin (%.0f x %.0f mm). Reserved for release 3.0; 2.0 may keep the sheet closed." % ((cz[1][0] - cz[0][0]) * 1000, (cz[1][1] - cz[0][1]) * 1000),
         "proposed cut-out %.0f x %.0f mm" % ((cz[1][0] - cz[0][0]) * 1000, (cz[1][1] - cz[0][1]) * 1000), "receiver at the rear panel (owner, 2 Nov 2026)", 0, "material removed (not counted)", 1, ["base_cutout"],
         label="Cut-out ghost (reserved for 3.0)", off=[0, 0, -.2], opn=[0, 0, -.1])
    # cells (PWR-001 / PWR-023) and the two pocket trays (MEC-007); the GLB battery node (single row across) is hidden by model.js
    cell_parts = []
    for side in ("left", "right"):
        k = "battery_cells_" + side
        cell_parts.append(k)
        geo[k] = {"group": "base", "prims": [box(np.subtract(c_["hi"], c_["lo"]), np.add(c_["lo"], c_["hi"]) / 2, "#4f7cac", name="LF105") for c_ in RL["cells"] if c_["side"] == side]}
        for c_ in RL["cells"]:
            if c_["side"] == side:
                geo[k]["prims"].append(box([.014, .014, .004], [c_["lo"][0] + .025, (c_["lo"][1] + c_["hi"][1]) / 2, c_["hi"][2] + .002], "#c0392b", name="terminal_pos"))
                geo[k]["prims"].append(box([.014, .014, .004], [c_["hi"][0] - .025, (c_["lo"][1] + c_["hi"][1]) / 2, c_["hi"][2] + .002], "#2c3e50", name="terminal_neg"))
    Cc = FACTS["cells"]
    comp("battery_cells", "Battery: 8 x EVE LF105 upright, 4 per side pocket (8S)", "PWR-001, PWR-023", 8, "provisional",
         "Eight EVE LF105 cells upright, four in each side pocket beside the reserved charger zone, in series (8S); replaces the single row across the robot (B-02 rev18.10).",
         "cell 200 h x 130 x 38 mm (B5); pocket arrangement %s chosen by rear_layout.py" % RL["pockets"].get("arrangement", ""),
         "A1 side pockets (owner, 2 Nov 2026)%s" % ("" if RL["pockets"].get("clears_flanges") else "; needs the side-panel return flanges notched along the pockets (GI-025)"),
         8 * Cc["mass"], "8 x 1.98 kg (cells only)", 3, cell_parts, label="Provisional: A1 side pockets, to be entered in P-03 and M-01", off=[0, 0, .3], opn=[0, 0, .14])
    tray_parts = []
    for t_ in RL["trays"]:
        k = "battery_tray_" + t_["side"]
        tray_parts.append(k)
        lo_, hi_ = np.array(t_["lo"]), np.array(t_["hi"])
        w_ = Cc["restraint_wall"]
        prims = [box([hi_[0] - lo_[0], hi_[1] - lo_[1], Cc["tray_floor"]], [(lo_[0] + hi_[0]) / 2, (lo_[1] + hi_[1]) / 2, lo_[2] + Cc["tray_floor"] / 2], "#8d9aa5", name="tray_floor")]
        for xx in (lo_[0] + w_ / 2, hi_[0] - w_ / 2):
            prims.append(box([w_, hi_[1] - lo_[1], 0.120], [xx, (lo_[1] + hi_[1]) / 2, lo_[2] + 0.060], "#8d9aa5", name="end_wall"))
        for yy in (lo_[1] + w_ / 2, hi_[1] - w_ / 2):
            prims.append(box([hi_[0] - lo_[0], w_, 0.120], [(lo_[0] + hi_[0]) / 2, yy, lo_[2] + 0.060], "#8d9aa5", name="side_wall"))
        prims.append(box([hi_[0] - lo_[0], 0.020, 0.004], [(lo_[0] + hi_[0]) / 2, (lo_[1] + hi_[1]) / 2, hi_[2] - 0.002], "#5d6d7e", name="restraint_strap"))
        geo[k] = {"group": "base", "prims": prims}
    comp("battery_tray", "Battery pocket trays MEC-007, left and right (design intent)", "MEC-007", 2, "provisional",
         "Two pocket trays (3 mm floor and walls, 120 mm restraint walls, top strap) for 4 cells each; terminals on top, reachable with the cover off.",
         "design_intent/battery_tray.step (two pocket trays, scripts/roadmap_model/design_intent/battery_tray.py)", "A1 side pockets", 1.6, "design-intent estimate", 3, tray_parts,
         label="Design intent, not CAD: owner fridayali", off=[0, 0, .25], opn=[0, 0, .12])
    # series link between the two groups across the charger zone, above the metal-free margin
    cl = [c_ for c_ in RL["cells"] if c_["side"] == "left"]
    cr = [c_ for c_ in RL["cells"] if c_["side"] == "right"]
    xa = max(c_["hi"][0] for c_ in cl) - 0.025
    ya, yb = min(c_["lo"][1] for c_ in cl) + 0.019, max(c_["hi"][1] for c_ in cr) - 0.019
    zt = cl[0]["hi"][2] + 0.004
    geo["battery_series_link"] = {"group": "base", "prims": [tube([[xa, ya, zt], [xa, ya, RL["link_z"]], [xa, yb, RL["link_z"]], [xa, yb, zt]], 0.00525, "#c0392b")]}
    comp("battery_series_link", "Battery series link between the two trays (25 mm²), across the centre zone over the receiver, through the keyed connector PWR-018", "PWR-024", 1, "proposed",
         "Insulated 25 mm² link from the left tray to the right tray, over the reserved charger zone at z %.3f, above the 20 mm metal-free margin (top %.3f); disconnect point: the keyed main connector PWR-018 at the centre (A9)." % (RL["link_z"], RL["margin"][1][2]),
         "tube 10.5 mm", "A1, A9", 0.1, "estimate", 3, ["battery_series_link"], off=[0, 0, .3], opn=[0, 0, .14])
    it_bc = [it for it in T["packed"] if it["id"] == "rz_batcon"][0]
    geo["rz_batcon"] = {"group": "base", "prims": [box(bc_s, bc_c, BODY_COL["BAT"], name="rz_batcon"), box([bc_s[0] * .9, bc_s[1] * .9, .0015], [bc_c[0], bc_c[1], bc_c[2] + bc_s[2] / 2 + .00075], DOMAIN_COL["BAT"])]}
    comp("rz_batcon", "Battery main mating connector (keyed, PWR-018): disconnect point of the 8S link between the two trays", "PWR-018", 1, "proposed",
         "Keyed, touch-protected DC connector on the series link at the centre: the two trays (4 + 4 LF105) come out separately after it is unplugged (A9, replaces the one removable battery assembly of B-02 rev18.10).",
         "%s: %s" % (it_bc.get("geom", "proposed size"), "x".join("%g" % d for d in it_bc["dims"]) + " mm"), "on the series link over the centre, z %.3f (A9)" % bc_c[2],
         it_bc.get("mass", 0.08), "estimate", 3, ["rz_batcon"], part_number=it_bc.get("part", ""), off=[0, 0, .3], opn=[0, 0, .14])
    # A9 assembly checks: cells in from above with the cover off, power plate out without the cells, a disconnect point on the 8S link
    trays_ = RL["trays"]
    plate_ = RL["plate"]
    ov = lambda a, b: all(min(a[1][i], b[1][i]) - max(a[0][i], b[0][i]) > 1e-6 for i in range(2))
    tray_check = {"trays": len(trays_), "connector": "PWR-018 keyed, on the 8S link at x %.3f, z %.3f" % (bc_c[0], bc_c[2]),
                  "plate_overlaps_trays_in_plan": any(ov((plate_[0], plate_[1]), (t_["lo"], t_["hi"])) for t_ in trays_),
                  "plate_tray_gap_mm": round(min(abs(t_["lo"][1]) - plate_[1][1] for t_ in trays_ if t_["lo"][1] > 0) * 1000, 1),
                  "cells_from_above": all(t_["hi"][2] < FACTS["cover_underside"] for t_ in trays_), "link_over_plate": RL["link_z"] > plate_[1][2],
                  "nothing_on_cells": True}
    BM["PWR-001"] = {"by": "battery_cells", "cls": "provisional", "geo": "8 x LF105 200 x 130 x 38 mm (B5)", "pos": "A1 side pockets (owner, 2 Nov 2026)", "mass": 21.5, "msrc": "B5 assembly 20 to 23 kg provisional (midpoint)"}
    BM["PWR-023"] = {"by": "battery_cells", "cls": "provisional", "mqty": 8, "geo": "8 cell boxes", "pos": "A1 side pockets", "mass": 0.0, "msrc": "included in PWR-001"}
    BM["MEC-007"] = {"by": "battery_tray", "cls": "provisional", "mqty": 1}
    # MEC-006: power-electronics mounting plate above the receiver zone (A1)
    pl_ = RL["plate"]
    comp("rear_plate", "Rear power-electronics plate above the reserved receiver zone", "MEC-006", 1, "proposed",
         "3 mm aluminium plate over the charger zone, underside %.0f mm above the floor (20 mm above the receiver top): BMS, F0, K1/K2, precharge, FB-A, FB-B, PWR-017, KCHG, F-CHG." % (pl_[0][2] * 1000),
         "proposed outline (3 mm 5052 sheet)", "A1 rear layout (owner, 2 Nov 2026)", (pl_[1][0] - pl_[0][0]) * (pl_[1][1] - pl_[0][1]) * 0.003 * 2680,
         "outline x 3 mm x 2680 kg/m3", 3, ["rear_plate"], off=[-.25, 0, .25], opn=[-.12, 0, .1], part_number="MEC-006 (drawing revision TBD)")
    geo["rear_plate"]["prims"].append(box(np.subtract(pl_[1], pl_[0]), np.add(pl_[0], pl_[1]) / 2, "#b9c2c9"))

    # K1/K2 option B ghost (TeSys D LC1D80BD) next to the recorded GX11CAC, for the fit report
    k1 = [k for k in placed if k.startswith("rz_k1k2")]
    opt = {"A": {"part": "Gigavac GX11CAC", "dims": [73, 45, 76], "fits": len(k1) == 2},
           "B_tesys": {"part": "Schneider TeSys D LC1D80BD", "dims": [120, 75, 127]},
           "B_siemens": {"part": "Siemens 3RT2 size S3", "dims": [152, 70, 140]}}
    for key in ("B_tesys", "B_siemens"):
        g2 = [dict(i, id="opt_" + key, dims=opt[key]["dims"], qty=2, converter=False, gap=0.005) for i in items if i["id"] == "rz_k1k2"]
        others = [dict({k: v for k, v in i.items() if k != "fallback"}, gap=0.005) for i in items if i["id"] != "rz_k1k2" and i["zone"] != "front_bay"]
        pl2, nf2 = pack(others + g2, zones, obst, None, shells)
        opt[key]["fits"] = not [n for n in nf2 if n.startswith("opt_")]
        opt[key]["nofit"] = nf2
        if key == "B_tesys":
            ghost = [k for k in pl2 if k.startswith("opt_")]
            gparts = []
            for i, kk in enumerate(ghost):
                cc, p = pl2[kk]
                gp = "k1k2_option_b_%d" % (i + 1)
                gparts.append(gp)
                geo[gp] = {"group": "base", "prims": [box(p, cc, "#e67e22", o=.25)]}
            if gparts:
                comp("k1k2_option_b", "K1/K2 option B ghost: TeSys D LC1D80BD (labelled alternative)", "SAF-003", len(gparts), "proposed",
                     "Alternative contactor for the 2 Nov decision, drawn as a ghost where the packer would put it.",
                     "catalogue outline 75 x 127 x 120 mm, verify", "packer, rear zone (option B case)", 0, "not counted (alternative)", 3, gparts,
                     label="Ghost alternative, not fitted", off=[-.25, 0, .3], opn=[-.12, 0, .14], part_number="LC1D80BD")

    # ---------------- design-intent parts (from the CAD fork index), drawn as envelopes of their placement
    di_comp = {}
    for d in DI:
        di_comp[d.get("item")] = d

    def di_mesh(item, variant, pl, colour, opacity=None, group="base"):
        import trimesh
        rec = di_comp[item]
        f = [x for x in rec["files"] if x["variant"] == variant][0]
        m = trimesh.load(os.path.join(MODEL, f["stl"] if f["stl"].startswith("design_intent") else "design_intent/" + f["stl"]))
        v = np.asarray(m.vertices) * MM
        rx, ry, rz = pl["rpy"]
        cx, sx, cy, sy, cz, sz = math.cos(rx), math.sin(rx), math.cos(ry), math.sin(ry), math.cos(rz), math.sin(rz)
        Rm = np.array([[cz, -sz, 0], [sz, cz, 0], [0, 0, 1]]) @ np.array([[cy, 0, sy], [0, 1, 0], [-sy, 0, cy]]) @ np.array([[1, 0, 0], [0, cx, -sx], [0, sx, cx]])
        v = v @ Rm.T + np.array(pl["xyz"])
        if group in ("col", "mov"):
            v = v - [FACTS["lift_plate"]["col_axis_x"]["bp000"], 0, 0]
        d = {"t": "mesh", "v": [R(x, 4) for x in v.reshape(-1)], "f": np.asarray(m.faces).reshape(-1).tolist(), "c": colour}
        if opacity is not None:
            d["o"] = opacity
        return d

    DI_DRAW = [  # item, variant, component id, name, bom, colour, group, stage, ghost
        ("motor_bracket", "motor_bracket", "motor_brackets", "Motor shaft-flat brackets MEC-015 (design intent)", "MEC-015", "#6d7780", "base", 2, False),
        ("rear_estop_housing", "rear_estop_housing", "rear_estop_housing", "Second E-stop housing on the adapter plate behind the post, button up (design intent)", "SAF-001", "#c9b037", "mov", 8, False),
        ("getac_pocket", "getac_pocket", "getac_pocket", "Getac ZX80 pocket, portrait (decided default), back plate and light-bar plate (design intent)", "UI-002, MEC-012", "#5d6d7e", "mov", 8, False),
    ]
    for item, variant, cid, name, bomid, colour, group, stage, ghost in DI_DRAW:
        if item not in di_comp:
            continue
        rec = di_comp[item]
        pls = rec["placement"] if isinstance(rec["placement"], list) else [rec["placement"]]
        if item == "rear_estop_housing":
            pls = [p_ for p_ in pls if p_.get("variant") == variant]
        if item == "getac_pocket":
            pls = pls[:1]
        parts = [cid] if len(pls) == 1 else ["%s_%d" % (cid, i + 1) for i in range(len(pls))]
        f0 = [x for x in rec["files"] if x["variant"] == variant][0]
        comp(cid, name, bomid, len(parts), "proposed" if ghost else "provisional",
             "%s. Method: %s, %s mm. Adjustment: %s." % (name, rec.get("method", ""), rec.get("thickness_mm", ""), rec.get("adjustment", "")),
             "design_intent/%s.step (scripts/roadmap_model/design_intent/%s.py)" % (variant, item),
             "%s (%s)" % (rec.get("configuration", ""), rec.get("placement_note", "")[:160]),
             (f0.get("mass_kg") or rec.get("mass_kg") or 0) * (0 if ghost else len(parts)), "design-intent volume x density", stage, parts, group=group,
             label=("Ghost, not fitted" if ghost else "Design intent, not CAD: owner fridayali"),
             off=[0, 0, .25] if group == "base" else [0, 0, .1], opn=[0, 0, .12] if group == "base" else [0, 0, 0],
             link="https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md")
        for k, pl in zip(parts, pls):
            geo[k]["prims"].append(di_mesh(item, variant, pl, colour, .14 if ghost else None, group))
        if ghost:
            comps[-1]["hq"] = False
    # lift base plate MEC-019 on the arch (B3): drawn from the design-intent STL in the base group (the plate stays when bp changes)
    if "lift_base_plate" in di_comp:
        geo["lift_base_plate"] = {"group": "base", "prims": [di_mesh("lift_base_plate", "lift_base_plate", di_comp["lift_base_plate"]["placement"][0], "#c4ccd2")]}
    # the getac pocket replaces the placeholder mount envelope of parts.yaml
    if "getac_pocket" in di_comp:
        comps[:] = [c for c in comps if c["id"] != "tablet_mount"]
        exploded.pop("tablet_mount", None)
        geo.pop("tablet_mount", None)
        BM["UI-002"] = {"by": "getac_pocket"}
        BM["MEC-012"] = {"by": "getac_pocket"}
    BM["MEC-015"] = {"by": "motor_brackets", "cls": "provisional", "mass": 4 * 0.279, "msrc": "design-intent volume x 7850"}

    # ---------------- CAN terminations (CTL-009, CTL-010)
    # ---------------- harness
    N, NG, E = harness_graph(U)
    fbd = FBR[fb_default]["placed"]

    def top_of(k):
        if k in fbd:
            _, cc, p = fbd[k]
            return [cc[0], cc[1], cc[2] + p[2] / 2]
        if k in placed:
            cc, p = placed[k]
            return [cc[0], cc[1], cc[2] + p[2] / 2]
        if k in box_of:
            lo, hi = box_of[k]
            return [(lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2, hi[2]]
        raise KeyError(k)

    def fixed_pos(k):
        for it in T["fixed"]:
            if it["id"] == k:
                return list(it["pos"])
        raise KeyError(k)

    ax = U["col_axis_x"]
    TERM = {
        "battery+": [RL["trays"][0]["hi"][0] - 0.020, RL["trays"][0]["lo"][1] + 0.020, RL["cells"][0]["hi"][2] + 0.004],
        "battery-": [RL["trays"][1]["hi"][0] - 0.020, RL["trays"][1]["hi"][1] - 0.020, RL["cells"][0]["hi"][2] + 0.004],
        "motor_l": [0.0, 0.090, 0.150], "motor_r": [0.0, -0.090, 0.150],
        "zlac": top_of("motor_driver"), "imu": top_of("imu"), "nucleo": top_of("base_controller"), "jetson": top_of("compute"),
        "lidar": [0.300, 0.0, 0.200], "gemini": [0.372, 0.0, 0.160], "estop": [0.345, 0.130, 0.145], "reset": [0.340, -0.130, 0.145],
        "us_fl": [0.355, 0.130, 0.0914], "us_fr": [0.355, -0.130, 0.0914], "us_rl": [-0.355, 0.130, 0.0914], "us_rr": [-0.355, -0.130, 0.0914],
        "tof_f": [0.385, 0.0, 0.107], "tof_r": [-0.374, 0.0, 0.092],
        "disc": fixed_pos("rz_disc"), "sb50": fixed_pos("rz_sb50"), "rx": [FACTS["tzbot_receiver"]["hi"][0] - 0.015, 0.0, FACTS["tzbot_receiver"]["hi"][2] - 0.005],  # cable exit, receiver rear top
        "lift_node": fixed_pos("lift_node"), "lift_motor": [ax - 0.060, 0.0, 0.330],
        "estop2": [ax - 0.025, 0.0, U["col_top"] + 0.016],
        "arm_l": [U["shoulder"][0] - 0.03, 0.045, U["shoulder"][2]], "arm_r": [U["shoulder"][0] - 0.03, -0.045, U["shoulder"][2]],
        "zed": [U["head_lens"][0] - 0.03, 0.0, U["head_lens"][2] - 0.025],
        "getac": [U["prof_front"] + 0.002, 0.08, U["getac"][2] - U["getac_size"][2] / 2 + 0.01],
        "light": [U["prof_front"] + 0.002, 0.07, U["head_light"][2]],
        "lsens1": [ax + LR["sensor_axis_x"], LR["sensor_y"][0], U["lift_sensor_z"][0]], "lsens2": [ax + LR["sensor_axis_x"], LR["sensor_y"][0], U["lift_sensor_z"][1]],
        "lsens3": [ax + LR["sensor_axis_x"], LR["sensor_y"][0], U["lift_sensor_z"][2]],   # A6: cable at the sensor back end (-y)
    }
    for k in list(placed) + list(fbd):
        TERM[k] = top_of(k)
    if "bay_din_pnoz" in fbd:
        TERM["bay_din"] = top_of("bay_din_pnoz")
    ID_OF_TERM = {"battery+": "battery_cells_left", "battery-": "battery_cells_right", "motor_l": "hub_motor_wheel_left", "motor_r": "hub_motor_wheel_right",
                  "zlac": "motor_driver", "imu": "imu", "nucleo": "base_controller", "jetson": "compute", "lidar": "lidar",
                  "gemini": "base_camera", "estop": "estop", "reset": "reset_button", "us_fl": "ultrasonic_front_left",
                  "us_fr": "ultrasonic_front_right", "us_rl": "ultrasonic_rear_left", "us_rr": "ultrasonic_rear_right",
                  "tof_f": "tof_front", "tof_r": "tof_rear", "disc": "rz_disc", "sb50": "rz_sb50", "rx": "tz_receiver",
                  "lift_node": "lift_node", "lift_motor": "lift_column", "estop2": "second_estop", "arm_l": "openarm_left",
                  "arm_r": "openarm_right", "zed": "head_camera", "getac": "getac_tablet", "light": "head_light",
                  "lsens1": "lift_stop_sensors", "lsens2": "lift_stop_sensors", "lsens3": "lift_stop_sensors"}
    near = lambda p: min(N, key=lambda k: np.linalg.norm(np.subtract(N[k], p)) + (0.5 if NG[k] != "base" and p[2] < 0.3 else 0))
    # cable table: id, from, to, function, domain, gauge/type, OD mm, connector A, connector B, pin/terminal, BOM
    CAB = [
        ("CBL-P01", "battery+", "rz_f0", "Battery + to F0 110 A Class T", "BAT", "25 mm²", 10.5, "M8 lug", "M8 lug (5007100 stud)", "pack + terminal", "WIR-001"),
        ("CBL-P02", "rz_f0", "disc", "F0 to lockable disconnect BS-6004B", "BAT", "25 mm²", 10.5, "M8 lug", "M10 lug", "", "WIR-001"),
        ("CBL-P03", "disc", "rz_pwr017_1", "Disconnect to BAT + bus (PWR-017)", "BAT", "25 mm²", 10.5, "M10 lug", "M8 lug", "BAT +", "WIR-001"),
        ("CBL-P04", "rz_pwr017_1", "rz_k1k2_1", "BAT + bus to K1 (SAFE path)", "SAFE", "25 mm²", 10.5, "M8 lug", "M8 lug", "K1 A1", "WIR-001"),
        ("CBL-P05", "rz_k1k2_1", "rz_k1k2_2", "K1 to K2 in series", "SAFE", "25 mm²", 10.5, "M8 lug", "M8 lug", "", "WIR-001"),
        ("CBL-P06", "rz_k1k2_2", "rz_fbb", "K2 to SAFE bus FB-B", "SAFE", "25 mm²", 10.5, "M8 lug", "M8 stud", "SAFE +", "WIR-001"),
        ("CBL-P07", "rz_fbb", "zlac", "F-TRAC 40 A to ZLAC8015D", "SAFE", "10 mm²", 7.5, "M6 lug", "ZLAC power terminal", "F-TRAC", "WIR-001"),
        ("CBL-P08", "zlac", "motor_l", "ZLAC axis 1 to left hub motor (phases + encoder)", "SAFE", "motor OEM lead", 9.0, "ZLAC motor port", "motor lead", "axis 1", "DRV-001"),
        ("CBL-P09", "zlac", "motor_r", "ZLAC axis 2 to right hub motor (phases + encoder)", "SAFE", "motor OEM lead", 9.0, "ZLAC motor port", "motor lead", "axis 2", "DRV-001"),
        ("CBL-P10", "bay_ddr240", "motor_l", "SAFE 24 V brake release, left (24 V 12.5 W)", "SAFE", "0.75 mm²", 5.0, "DIN terminal", "brake lead", "", "DRV-003"),
        ("CBL-P11", "bay_ddr240", "motor_r", "SAFE 24 V brake release, right", "SAFE", "0.75 mm²", 5.0, "DIN terminal", "brake lead", "", "DRV-003"),
        ("CBL-P12", "rz_fbb", "bay_ddr240", "F-LIFT 15 A to DDR-240B-24 input", "SAFE", "2.5 mm² (E-01; 1.5 in the conflict list)", 4.5, "ring lug", "DIN terminal", "F-LIFT", "WIR-001"),
        ("CBL-P13", "bay_ddr240", "lift_motor", "SAFE 24 V to the DOLD lift via CTL-017 motor stage", "SAFE", "16 AWG Mini-Fit Jr HCS", 6.0, "DIN terminal", "Molex Mini-Fit Jr HCS", "", "CTL-016"),
        ("CBL-P14", "rz_fbb", "arm_l", "F-ARM-L 30 A to the left arm", "SAFE", "6 mm²", 6.5, "ring lug", "arm power connector", "F-ARM-L", "WIR-001"),
        ("CBL-P15", "rz_fbb", "arm_r", "F-ARM-R 30 A to the right arm", "SAFE", "6 mm²", 6.5, "ring lug", "arm power connector", "F-ARM-R", "WIR-001"),
        ("CBL-P16", "rz_fba", "bay_pwr009", "F-J401 10 A to the compute branch protection", "BAT", "2.5 mm²", 4.5, "ring lug", "screw terminal", "F-J401", "WIR-001"),
        ("CBL-P17", "bay_pwr029", "jetson", "Protected 19 to 54 V to the J401", "BAT", "2.5 mm²", 4.5, "screw terminal", "J401 DC input", "", "WIR-001"),
        ("CBL-P18", "rz_fba", "bay_rsd60", "F-5V 5 A to RSD-60G-5 input", "BAT", "1.5 mm²", 3.8, "ring lug", "screw terminal", "F-5V", "WIR-001"),
        ("CBL-P19", "bay_rsd60", "nucleo", "5 V to NUCLEO, RPLIDAR, TF-Luna, IMU (distribution)", "LV", "0.5 mm²", 2.5, "screw terminal", "JST / Dupont", "NUCLEO 5V_EXT", "SNS-003"),
        ("CBL-P20", "rz_fba", "bay_rsd100", "F-24V 7.5 A to RSD-100B-24 input", "BAT", "1.5 mm²", 3.8, "ring lug", "screw terminal", "F-24V", "WIR-001"),
        ("CBL-P21", "bay_rsd100", "bay_fbc", "Regulated 24 V to FB-C", "R24", "1.5 mm²", 3.8, "screw terminal", "FB-C bus stud", "", "WIR-001"),
        ("CBL-P22", "bay_fbc", "bay_usbpd", "F-PANEL 3 A to the USB-PD module", "R24", "0.75 mm²", 3.0, "blade fuse circuit", "screw terminal", "F-PANEL", "WIR-001"),
        ("CBL-P23", "bay_usbpd", "getac", "USB-C PD to the Getac ZX80", "R24", "USB-C PD cable 5 A", 4.5, "USB-C", "USB-C", "", "UI-002"),
        ("CBL-P24", "bay_fbc", "light", "F-PANEL 24 V to the head light, low-side switched by CTL-017", "R24", "SICK DOL-0804-G02MRN", 5.0, "M8 4-pin", "M8 4-pin", "AUX-002", "AUX-003"),
        ("CBL-P25", "bay_fbc", "fan", "F-FAN 2 A to the chassis fan", "R24", "0.5 mm²", 2.5, "blade fuse circuit", "fan lead", "F-FAN", "WIR-001"),
        ("CBL-P26", "bay_fbc", "bay_usbhub", "F-HUB 3 A to the USB hub", "R24", "0.75 mm²", 3.0, "blade fuse circuit", "hub DC jack", "F-HUB", "WIR-001"),
        ("CBL-P27", "rz_fba", "rz_fchg", "BAT bus to F-CHG 30 A MIDI", "BAT", "6 mm²", 6.5, "ring lug", "MIDI stud", "", "WCH-006"),
        ("CBL-P28", "rz_fchg", "rz_kchg", "F-CHG to KCHG relay", "BAT", "6 mm²", 6.5, "ring lug", "relay stud", "", "WCH-006"),
        ("CBL-P29", "rz_kchg", "sb50", "KCHG to SB50 (manual Daly charger)", "BAT", "6 mm²", 6.5, "ring lug", "Anderson SB50", "", "WCH-006"),
        ("CBL-P30", "rz_kchg", "rx", "KCHG to the TZBOT receiver output", "BAT", "6 mm²", 6.5, "ring lug", "receiver output", "", "WCH-006"),
        ("CBL-P31", "rx", "nucleo", "TZBOT start and fault lines", "SIG", "2 x 0.34 mm²", 4.0, "receiver signal", "NUCLEO GPIO", "GPIO to be assigned", "WCH-005"),
        ("CBL-P32", "estop", "bay_din", "Base E-stop 2NC loop into the PNOZ", "SIG", "4 x 0.75 mm²", 5.5, "ZBE-102 screw", "PNOZ S11/S12, S21/S22", "S11-S12, S21-S22", "SNS-003"),
        ("CBL-P33", "estop2", "bay_din", "Second E-stop 2NC loop down the column into the PNOZ (series)", "SIG", "4 x 0.75 mm²", 5.5, "ZBE-102 screw", "PNOZ S11/S12, S21/S22", "series with base E-stop", "SNS-003"),
        ("CBL-P34", "reset", "bay_din", "RESET NO to PNOZ reset, NC to the controller", "SIG", "4 x 0.5 mm²", 5.0, "XB4 screw", "PNOZ S34 / ISO1212", "S33-S34; NC to CTL-004", "SNS-003"),
        ("CBL-P35", "bay_din", "rz_k1k2_1", "PNOZ 13-14 to the K1 coil, 23-24 to the K2 coil, EDM loop", "SIG", "4 x 0.75 mm²", 5.5, "PNOZ terminal", "GX11 coil leads", "13-14 K1, 23-24 K2, Y1-Y2 EDM", "SNS-003"),
        ("CBL-P36", "bay_din", "bay_iso1212", "PNOZ Y32 to the isolated input", "SIG", "2 x 0.5 mm²", 4.0, "PNOZ Y32", "ISO1212 IN", "Y32", "CTL-004"),
        ("CBL-P37", "nucleo", "zlac", "CAN1 FDCAN1 to the ZLAC8015D (500 kbit/s provisional)", "SIG", "2 x 2 x 0.34 mm² STP", 6.0, "SN65HVD230 screw", "ZLAC CAN port", "FDCAN1 via CTL-003", "WIR-002"),
        ("CBL-P38", "bay_can2", "rz_bms", "CAN2 FDCAN2 (PB12 RX, PB6 TX) to the Daly BMS through the isolator, 250 kbit/s", "SIG", "2 x 2 x 0.34 mm² STP", 6.0, "Click screw", "BMS CAN connector", "FDCAN2 PB12/PB6", "CTL-011"),
        ("CBL-P39", "bay_can3", "lift_node", "CAN3 FDCAN3 to the lift node CTL-017", "SIG", "2 x 2 x 0.34 mm² STP", 6.0, "screw", "CTL-017 CAN", "FDCAN3", "CTL-016"),
        ("CBL-P40", "nucleo", "imu", "SPI4 to EV_ICM-42688-P (PE12 SCK, PE13 MISO, PE14 MOSI, PE11 CS; INT1 GPIO TBD; 5 V VIN)", "SIG", "8-way 0.14 mm² ribbon", 3.0, "NUCLEO ST zio CN", "board CN1", "CN1 16 SCLK, 18 SDI, 20 SDO, 4 CS, 3 INT1, 11/13 GND, 19 VIN", "CTL-012"),
        ("CBL-P41", "bay_pwr032", "us_fl", "3.3 V + serial to MB7060 front left", "SIG", "4 x 0.25 mm²", 4.0, "JST", "MB7060 pads", "UART RX", "SNS-003"),
        ("CBL-P42", "bay_pwr032", "us_fr", "3.3 V + serial to MB7060 front right", "SIG", "4 x 0.25 mm²", 4.0, "JST", "MB7060 pads", "UART RX", "SNS-003"),
        ("CBL-P43", "bay_pwr032", "us_rl", "3.3 V + serial to MB7060 rear left", "SIG", "4 x 0.25 mm²", 4.0, "JST", "MB7060 pads", "UART RX", "SNS-003"),
        ("CBL-P44", "bay_pwr032", "us_rr", "3.3 V + serial to MB7060 rear right", "SIG", "4 x 0.25 mm²", 4.0, "JST", "MB7060 pads", "UART RX", "SNS-003"),
        ("CBL-P45", "nucleo", "tof_f", "UART + 5 V to TF-Luna front (pin 5 to 3.3 V)", "SIG", "6 x 0.25 mm²", 4.0, "JST", "TF-Luna 6-pin", "UART", "SNS-003"),
        ("CBL-P46", "nucleo", "tof_r", "UART + 5 V to TF-Luna rear (pin 5 to 3.3 V)", "SIG", "6 x 0.25 mm²", 4.0, "JST", "TF-Luna 6-pin", "UART", "SNS-003"),
        ("CBL-P47", "bay_lidar_uart", "lidar", "USB-UART and 5 V to the RPLIDAR S3", "SIG", "S3 cable + adapter", 4.5, "USB-A", "S3 connector", "", "NAV-003"),
        ("CBL-P48", "bay_usbhub", "gemini", "USB 3 to the Gemini 336L", "SIG", "USB 3 cable", 5.0, "USB-A", "USB-C", "", "CAM-002"),
        ("CBL-P49", "bay_usbhub", "zed", "USB 3 Type-C to the ZED Mini (via the service loop)", "SIG", "ZED USB-C cable", 5.0, "USB-A", "USB-C", "", "ARM-009"),
        ("CBL-P50", "bay_usbcan_1", "arm_l", "USB-CAN-FD left arm", "SIG", "CAN-FD 2 x 2 x 0.25 STP", 5.0, "adapter", "arm CAN", "", "ARM-006"),
        ("CBL-P51", "bay_usbcan_2", "arm_r", "USB-CAN-FD right arm", "SIG", "CAN-FD 2 x 2 x 0.25 STP", 5.0, "adapter", "arm CAN", "", "ARM-006"),
        ("CBL-P52", "bay_usbhub", "arm_l", "Wrist camera left (to the gripper)", "SIG", "matched gripper-camera harness", 4.0, "USB-A", "gripper camera", "", "ARM-010"),
        ("CBL-P53", "bay_usbhub", "arm_r", "Wrist camera right (to the gripper)", "SIG", "matched gripper-camera harness", 4.0, "USB-A", "gripper camera", "", "ARM-010"),
        ("CBL-P54", "lsens1", "lift_node", "Lift stop sensor L1000 (always-on 24 V)", "SIG", "SICK DOL-1204-G02M", 5.0, "M12 4-pin", "CTL-017 input", "", "LFT-002"),
        ("CBL-P55", "lsens2", "lift_node", "Lift stop sensor L1175", "SIG", "SICK DOL-1204-G02M", 5.0, "M12 4-pin", "CTL-017 input", "", "LFT-002"),
        ("CBL-P56", "lsens3", "lift_node", "Lift stop sensor L1350", "SIG", "SICK DOL-1204-G02M", 5.0, "M12 4-pin", "CTL-017 input", "", "LFT-002"),
        ("CBL-P57", "jetson", "nucleo", "USB host to MCU", "SIG", "USB data cable", 4.0, "USB-A", "NUCLEO USB", "", "CTL-008"),
        ("CBL-P58", "jetson", "bay_usbhub", "J401 USB 3 to the hub", "SIG", "USB 3 cable", 5.0, "USB-A", "USB-B", "", "CMP-009"),
        ("CBL-P59", "battery-", "rz_pwr017_2", "Battery - (Daly P- switched) to the BAT - bus; all returns here, no chassis return", "BAT", "25 mm²", 10.5, "M8 lug", "M8 lug", "BAT -", "WIR-001"),
        ("CBL-P60", "rz_bms", "battery+", "BMS sense harness and NTCs", "BAT", "BMS sense harness", 6.0, "BMS connector", "cell taps", "", "PWR-025"),
        ("CBL-P61", "bay_din", "rz_pre", "Precharge relay Kpre drive", "SIG", "2 x 0.5 mm²", 4.0, "terminal", "Kpre coil", "TPL7407L channel", "SAF-004"),
    ]
    BEND25 = {}
    cab_rows, tubes, fittings, unattached = [], {d: {"base": [], "col": [], "mov": []} for d in DOMAIN_COL}, [], []
    for cid, a, b, fn, dom, gauge, od, ca, cb, pin, bomref in CAB:
        if a not in TERM or b not in TERM:
            cab_rows.append({"id": cid, "from": a, "to": b, "function": fn, "domain": dom, "gauge_or_type": gauge, "od_mm": od,
                             "connector_a": ca, "connector_b": cb, "pin_or_terminal": pin, "bom": bomref, "route": "not routed: endpoint not placed",
                             "route_length_m": "", "length_with_margin_m": "", "min_bend_radius_mm": max(60 if gauge == "25 mm²" else 0, round(6 * od)),
                             "mass_kg": 0, "from_part": a, "to_part": b, "from_xyz": "", "to_xyz": ""})
            unattached.append(cid)
            continue
        pa, pb = TERM[a], TERM[b]
        na, nb = near(pa), near(pb)
        local = gauge == "25 mm²" and pa[0] < -0.10 and pb[0] < -0.10
        if local:
            # A9: 25 mm² runs inside the rear bay go point to point (one horizontal leg at the higher terminal, then one vertical drop)
            zt = max(pa[2], pb[2])
            path = []
            pts = [list(pa)] + ([[pa[0], pa[1], zt]] if pa[2] < zt - 1e-6 else []) + [[pb[0], pb[1], zt]] + ([list(pb)] if pb[2] < zt - 1e-6 else [])
            pts = [q for i, q in enumerate(pts) if i == 0 or np.linalg.norm(np.subtract(q, pts[i - 1])) > 1e-6]
        else:
            path = route(N, E, na, nb)
            pts = [pa] + [list(N[k]) for k in path] + [pb]
        if gauge == "25 mm²":
            # bend check: each interior corner needs R*tan(theta/2) of straight cable on both sides (R = 60 mm)
            worst = None
            for i in range(1, len(pts) - 1):
                u, v = np.subtract(pts[i], pts[i - 1]), np.subtract(pts[i + 1], pts[i])
                lu, lv = np.linalg.norm(u), np.linalg.norm(v)
                if lu < 1e-6 or lv < 1e-6:
                    continue
                th = math.acos(max(-1.0, min(1.0, float(np.dot(u, v) / (lu * lv)))))
                if th < math.radians(5):
                    continue
                need = 0.060 * math.tan(th / 2)
                have = min(lu if i == 1 else lu / 2, lv if i == len(pts) - 2 else lv / 2)
                if worst is None or have - need < worst[0]:
                    worst = (have - need, round(math.degrees(th)), round(need * 1000, 1), round(have * 1000, 1))
            BEND25[cid] = {"route_m": R(plen(pts), 3), "direct_m": R(float(np.linalg.norm(np.subtract(pa, pb))), 3), "local": bool(local),
                           "bend_ok": bool(worst is None or worst[0] >= -1e-6),
                           "worst_corner": None if worst is None else {"deg": worst[1], "need_mm": worst[2], "have_mm": worst[3]}}
        groups = ["base" if (a not in ID_OF_TERM or not ID_OF_TERM[a].startswith(("openarm", "head_", "getac", "second", "lift_"))) else
                  ("col" if ID_OF_TERM[a] in ("second_estop", "lift_stop_sensors", "lift_node", "lift_column") else "mov")]
        groups += [NG[k] for k in path]
        bt = ID_OF_TERM.get(b, b)
        groups += ["mov" if bt in ("openarm_left", "openarm_right", "head_camera", "getac_tablet", "head_light") else
                   ("col" if bt in ("second_estop", "lift_stop_sensors", "lift_node", "lift_column") else "base")]
        if local:
            groups = ["base"] * len(pts)
        L = plen(pts)
        # split into groups: a segment belongs to the group of its upper end (base->col segments drawn in col)
        seg = {"base": [], "col": [], "mov": []}
        cur, cg = [pts[0]], groups[0]
        for i in range(1, len(pts)):
            g = groups[i]
            rank = {"base": 0, "col": 1, "mov": 2}
            if g != cg:
                hg = g if rank[g] > rank[cg] else cg
                if len(cur) > 1:
                    seg[cg].append(cur)
                seg[hg].append([cur[-1], pts[i]])
                cur, cg = [pts[i]], g
            else:
                cur.append(pts[i])
        if len(cur) > 1:
            seg[cg].append(cur)
        r = od / 2000
        for g, ss in seg.items():
            for s in ss:
                tubes[dom][g].append({"cid": cid, "pts": s, "r": r})
        mass_per_m = {"25 mm²": 0.26, "10 mm²": 0.11, "6 mm²": 0.07, "2.5 mm²": 0.035, "1.5 mm²": 0.022}.get(gauge, 0.03)
        cab_rows.append({"id": cid, "from": a, "to": b, "function": fn, "domain": dom, "gauge_or_type": gauge, "od_mm": od,
                         "connector_a": ca, "connector_b": cb, "pin_or_terminal": pin, "bom": bomref,
                         "route": " > ".join(path) if path else "direct inside the rear bay (A9)", "route_length_m": R(L, 3), "length_with_margin_m": R(L * 1.1, 3),
                         "min_bend_radius_mm": max(60 if gauge == "25 mm²" else 0, round(6 * od)), "mass_kg": R(L * 1.1 * mass_per_m, 3),
                         "from_part": ID_OF_TERM.get(a, a.rsplit("_", 1)[0] if a.endswith(("_1", "_2")) else a),
                         "to_part": ID_OF_TERM.get(b, b.rsplit("_", 1)[0] if b.endswith(("_1", "_2")) else b),
                         "from_xyz": [R(v) for v in pa], "to_xyz": [R(v) for v in pb]})
    # harness components per domain and group
    for dom, gg in tubes.items():
        if dom == "MECH":
            continue
        parts = []
        for g, tl in gg.items():
            if not tl:
                continue
            k = "harness_%s_%s" % (dom.lower(), g)
            parts.append(k)
            off = np.array([FACTS["lift_plate"]["col_axis_x"]["bp000"], 0, 0]) if g in ("col", "mov") else np.zeros(3)
            geo[k] = {"group": g, "prims": [dict(tube([np.subtract(p, off) for p in t["pts"]], t["r"], DOMAIN_COL[dom]), cid=t["cid"]) for t in tl]}
        if not parts:
            continue
        rows = [c for c in cab_rows if c["domain"] == dom]
        comp("harness_" + dom.lower(), "Harness: " + T["harness_domains"][dom]["label"], ", ".join(sorted({c["bom"] for c in rows})), len(rows), "proposed",
             "%d cables of the %s domain on their routes (cable_list.csv)." % (len(rows), dom), "tubes at the cable outer diameter on the routed path",
             "routed by build.py on the harness graph (bp000, L1000); upper-body cables through the service loop",
             sum(c["mass_kg"] for c in rows), "route length x 1.1 x mass per metre", 9, parts, off=[0, 0, .45], opn=[0, 0, .2])
        for k in parts:
            exploded["harness_" + dom.lower()]["offsets"][k] = [0, 0, .45]
    # fittings: tie points every 150 mm, P-clips at trunk nodes, grommets at wall / deck crossings
    fit = {"base": [], "col": [], "mov": []}
    nodes_used = set()
    for c in cab_rows:
        for k in c["route"].split(" > "):
            nodes_used.add(k)
    for k in sorted(nodes_used):
        if k not in N:
            continue
        p = np.array(N[k])
        g = NG[k]
        off = np.array([FACTS["lift_plate"]["col_axis_x"]["bp000"], 0, 0]) if g in ("col", "mov") else np.zeros(3)
        if k.startswith("G"):
            fit[g].append(cyl(.014, .006, p - off, "z" if k == "GD" else "x", "#222222", hq=True))
            fittings.append(("grommet", k))
        else:
            fit[g].append(box([.012, .016, .016], p - off, "#555555", hq=True))
            fittings.append(("P-clip / tie mount", k))
    fparts = []
    for g, pr in fit.items():
        if pr:
            k = "harness_fittings_" + g
            fparts.append(k)
            geo[k] = {"group": g, "prims": pr}
    comp("harness_fittings", "Harness fittings: P-clips, tie mounts and grommets", "MEC-013", len(fittings), "proposed",
         "Tie mount or P-clip at every trunk node, grommet at the centre-bracket walls and the deck crossing.", "small primitives",
         "harness graph nodes", 0.15, "estimate", 9, fparts, hq=True, off=[0, 0, .45], opn=[0, 0, .2])
    # service loop (upper-body cables, sized for the 350 mm stroke), static column, drawn at L1000
    sl = [N["SL1"], N["SLB"], N["SL2"]]
    loop_len = plen([N["SL1"], N["SLB"], N["SL2"]])
    need = (U["col_top"] + FACTS["column"]["stroke"] - 0.020) - (U["col_top"] - 0.040) + 0.06
    k = "service_loop"
    off = np.array([FACTS["lift_plate"]["col_axis_x"]["bp000"], 0, 0])
    pts = [np.subtract(N["SL1"], off), np.subtract([N["SL1"][0] - .015, N["SL1"][1], N["SLB"][2] + .03], off), np.subtract(N["SLB"], off),
           np.subtract([N["SL2"][0] + .0, N["SL2"][1], N["SLB"][2] + .03], off), np.subtract(N["SL2"], off)]
    geo[k] = {"group": "col", "prims": [tube(pts, .011, "#34495e")]}
    comp("service_loop", "Upper-body service loop (cable sleeve, 22 mm)", "MEC-013", 1, "proposed",
         "All upper-body cables in one sleeve from the static column top to the carriage, a hanging loop sized for the 350 mm stroke.",
         "22 mm braided sleeve tube", "proposed: -y side of the static column, drawn at L1000", 0.25, "estimate", 9, [k], off=[0, -.2, .1], opn=[0, 0, 0])
    issues_seed.append({"service_loop_length": R(plen(pts), 3), "service_loop_need": R(need, 3)})

    # ---------------- CAN terminations
    tparts = []
    for i, (cidr, end) in enumerate([("CAN1", "zlac"), ("CAN1", "nucleo"), ("CAN2", "bay_can2"), ("CAN2", "rz_bms")]):
        if end not in TERM:
            continue
        k = "can_term_%d" % (i + 1)
        tparts.append(k)
        p = np.array(TERM[end]) + [0, 0, .006]
        geo[k] = {"group": "base", "prims": [box([.016, .010, .010], p, "#16a085", hq=True)]}
    comp("can_terms", "CAN1 and CAN2 120 ohm terminations", "CTL-009, CTL-010", len(tparts), "proposed",
         "120 ohm at both physical ends of CAN1 and CAN2 (CAN3 termination is part of CTL-015).", "small primitive",
         "bus ends of the routed CAN cables", 0.016, "estimate", 9, tparts, hq=True, off=[0, 0, .45], opn=[0, 0, .2])

    # ---------------- fasteners (named and proposed); drawn ones load only with High quality
    fx = {"base": [], "col": [], "mov": []}
    def F(joint, part, size, qty, std, mat, cls, drawn="y"):
        fasteners.append({"joint": joint, "part": part, "size": size, "qty": qty, "standard": std, "material": mat, "class": cls, "drawn": drawn})
    # lift base plate on the arch (B3): 4 x M8 class 8.8 from above into the arch rivet nuts; column screwed from below (DIN 7500, flush)
    for (x, y) in arch_bolts:
        fx["base"] += [cyl(.0065, .008, [x, y, lp["top"] + .004], "z", "#2d2d2d", hq=True), cyl(.008, .0016, [x, y, lp["top"] + .0008], "z", "#9a9a9a", hq=True),
                       cyl(.0056, .014, [x, y, FACTS["arch"]["top"] - .002 - .007], "z", "#b0b4b8", hq=True)]
    F("Lift base plate MEC-019 to the centre-frame arch (from above)", "socket head cap screw, class 8.8", "M8 x 20", 4, "ISO 4762", "steel 8.8, zinc flake", "proposed")
    F("Lift base plate MEC-019 to the centre-frame arch (from above)", "washer", "M8", 4, "ISO 7089", "steel 200 HV", "proposed")
    F("Lift base plate MEC-019 to the centre-frame arch", "existing M8 blind rivet nut, round thin, stainless, in the arch top (CAD MMP.04.00.00.000)", "M8", 4, "BOM_specs_MMP.xlsx", "stainless steel", "named")
    for bp, axx in lp["col_axis_x"].items():
        for sx in (-1, 1):
            for sy in (-1, 1):
                x, y = axx + sx * lp["col_screws"][0] / 2, sy * lp["col_screws"][1] / 2
                if bp == "bp000":
                    fx["base"].append(cyl(.0082, .0045, [x, y, lp["top"] - .010 + .00225], "z", "#2d2d2d", hq=True))
    F("DOLD column to the lift base plate (from below, first, on the bench; bp000 hole set)", "countersunk thread-forming screw, flush with the plate underside", "M8 x 30 (>= 20 mm engagement)", 4, "DIN 7500", "steel", "named")
    F("DOLD column to the lift base plate (bp050 hole set, alternative)", "same set at the bp050 holes", "M8 x 30", 4, "DIN 7500", "steel", "named", "n")
    top = U["col_top"]
    ax0 = 0.0
    for dx in (-.03, .03):
        fx["mov"].append(cyl(.0065, .008, [ax0 + .18 + dx, 0, top - .004], "z", "#2d2d2d", hq=True))
    F("HFS6-60120 post to adapter plate (from below, end-tapped)", "socket head cap screw", "M8 x 25", 2, "ISO 4762", "steel 8.8", "proposed")
    for z in (top + .06, top + .16, top + .26):
        fx["mov"].append(box([.006, .016, .010], [ax0 + .18 - .062, 0, z], "#7a7a7a", hq=True))
    F("Rear upright (10 mm) and stiffener to the post", "T-slot nut + socket head cap screw", "M6 x 16", 6, "MISUMI HNTT6 / ISO 4762", "steel", "proposed")
    for s in (-1, 1):
        for dx in (-.03, .03):
            for dz in (-.03, .03):
                fx["mov"].append(cyl(.005, .004, [ax0 + .18 + dx, s * .0325, top + .166 + dz], "y", "#2d2d2d", hq=True))
    F("OpenArm J1_A base to the post side face (1 mm spacer)", "T-slot nut + socket head cap screw", "M6 x 20", 8, "MISUMI HNTT6 / ISO 4762", "steel", "proposed")
    F("J1_A spacer", "1 mm spacer plate", "1 mm", 2, "B7", "aluminium", "named")
    gx = 0.372
    for s in (-1, 1):
        fx["base"].append(cyl(.003, .006, [gx, s * .03, 0.123], "x", "#c9a227", hq=True))
    F("Gemini 336L to PETG mount MEC-009", "heat-set insert", "M4 x 8.1", 2, "brass heat-set insert", "brass", "named")
    F("Gemini 336L to PETG mount MEC-009", "socket head cap screw", "M4 x 8", 2, "ISO 4762", "A2", "proposed")
    F("LIFT-SNS-01 rod corner bracket", "short nut", "M4", 2, "LFT-007", "steel", "named")
    F("LIFT-SNS-01 rod corner bracket", "button head screw", "M4 x 8", 2, "ISO 7380", "steel", "named")
    F("LIFT-SNS-01 rod to adapter plate", "socket head cap screw", "M5 x 20", 1, "ISO 4762", "steel", "named")
    F("LIFT-SNS-01 sensor brackets to the DOLD T-slot", "bracket screw + T-nut", "per BEF-WN-M12", 3, "LFT-007", "steel", "named")
    lz = U["lift_sensor_z"]
    LRf = lift_rear_layout()
    for z in lz:   # A6: bracket screw into the T-slot of the rear face, on the leg on the face
        fx["col"].append(cyl(.003, .004, [FACTS["lift_rear"]["column_rear_x"] - .002, -0.020, z - .008], "x", "#2d2d2d", hq=True))
    F("MB7060 in the 27.5 mm panel hole", "3/4 in NPS lock nut", "3/4 in NPS", 4, "MEC-021", "nylon / steel", "named")
    F("MEC-005 lower plate to the base sheet (rivet nuts)", "ISO 7380 button head screw + rivet nut", "M4 x 8", 6, "ISO 7380", "A2", "proposed")
    for (x, y) in [(0.150, 0.150), (0.240, 0.150), (0.325, 0.150), (0.150, -0.150), (0.240, -0.150), (0.325, -0.150)]:
        fx["base"].append(cyl(.004, .0025, [x, y, FB.FLOOR + .00125], "z", "#9a9a9a", hq=True))
    F("DIN rail to MEC-005", "pan head screw", "M4 x 8", 2, "ISO 7045", "A2", "proposed")
    F("RSD-60G-5, RSD-100B-24 to MEC-005", "socket head cap screw + washer", "M4 x 8", 8, "ISO 4762 / ISO 7089", "A2", "proposed", "n")
    F("FB-A, FB-B, PWR-017 to MEC-006", "socket head cap screw + washer", "M5 x 12", 10, "ISO 4762 / ISO 7089", "A2", "proposed", "n")
    F("K1/K2, F0 holder, BMS to the side pocket plates", "socket head cap screw + washer", "M5 x 12", 10, "ISO 4762 / ISO 7089", "A2", "proposed", "n")
    F("Battery tray MEC-007 to the deck", "socket head cap screw + washer", "M6 x 16", 6, "ISO 4762 / ISO 7089", "steel 8.8", "proposed", "n")
    F("Detachable battery side panels", "quarter-turn fastener", "M5", 8, "DIN 7500-compatible quarter-turn", "steel", "proposed", "n")
    F("PETG sensor mounts (MEC-010, MEC-011) to the panels", "heat-set insert + ISO 7380", "M3 x 6", 12, "brass insert / ISO 7380", "A2", "proposed", "n")
    F("Second E-stop housing P2 to the arm-post rear slots (HFS6)", "ISO 4762 + ISO 7089 + M6 T-slot nut", "M6 x 10", 4, "ISO 4762", "steel", "proposed", "n")
    F("TZBOT receiver bracket WCH-007 to the base sheet (outside the 20 mm zone)", "ISO 7380 + rivet nut, stainless (non-magnetic A4)", "M5 x 10", 4, "ISO 7380", "A4", "proposed", "n")
    F("Ferrite sheet on the receiver top", "adhesive backing (no metal fasteners in the 20 mm zone)", "-", 1, "-", "-", "proposed", "n")
    F("MEC-005 upper shelf on the lower plate (second tier)", "hex standoff M4 x 50 + ISO 7380", "M4", 4, "hex standoff / ISO 7380", "A2", "proposed", "n")
    F("DIN carrier to the centre-bracket front legs", "ISO 4762 + rivet nut", "M5 x 12", 4, "ISO 4762", "A2", "proposed", "n")
    F("Getac pocket and light-bar plate to the post front face", "T-slot nut + ISO 4762", "M6 x 12", 4, "ISO 4762", "steel", "proposed", "n")
    F("MEC-015 motor brackets to the base sheet", "hex bolt + nut + washer", "M8 x 20", 8, "ISO 4017 / ISO 4032 / ISO 7089", "steel 8.8", "proposed", "n")
    F("Harness P-clips", "button head screw + rivet nut", "M4 x 8", len([f for f in fittings if f[0] != "grommet"]), "ISO 7380", "A2", "proposed", "n")
    fparts = []
    for g, pr in fx.items():
        if pr:
            k = "fasteners_" + g
            fparts.append(k)
            geo[k] = {"group": g, "prims": pr}
    comp("fasteners", "Fasteners (named and proposed, see fastener_schedule.csv)", "MEC-014, LFT-007", sum(len(p) for p in fx.values()), "proposed",
         "Drawn fasteners of the named joints (B7, LFT-007, Gemini inserts) and proposed ones; the full list is fastener_schedule.csv.",
         "ISO / DIN standard part envelopes", "joints of the model", 0.6, "estimate", 9, fparts, hq=True, off=[0, 0, .45], opn=[0, 0, .2])

    # ---------------- upper-body parts of the harness, fittings and fasteners move to stage 8 components, so that
    # they hide with the upper body (opened base) and explode with it
    up = {"harness": [], "fasteners": []}
    for c in list(comps):
        if c["id"].startswith(("harness_", "fasteners", "service_loop")) and c["id"] != "harness_upper":
            keep = [p for p in c["parts"] if geo[p]["group"] == "base"]
            moved = [p for p in c["parts"] if geo[p]["group"] != "base"]
            if not moved:
                continue
            up["fasteners" if c["id"] == "fasteners" else "harness"] += moved
            if keep:
                c["parts"] = keep
                exploded[c["id"]]["offsets"] = {p: exploded[c["id"]]["offsets"][p] for p in keep}
                exploded[c["id"]]["open"] = {p: exploded[c["id"]]["open"].get(p, [0, 0, .2]) for p in keep}
            else:
                comps.remove(c)
                exploded.pop(c["id"])
    if up["harness"]:
        rows_up = [r for r in cab_rows if r["route"] and any(k in r["route"] for k in ("SL1", "CS_T", "CY_T"))]
        comp("harness_upper", "Harness on the lift column and carriage (service loop, upper-body cables)", "ARM-009, ARM-010, ARM-006, AUX-003, LFT-002, CTL-016", len(rows_up), "proposed",
             "Upper-body part of the routed cables: service loop down the static column (-y side), the second E-stop loop down the rear face, the lift sensor cables on the +y face, and the carriage runs to the arms, ZED, Getac and head light.",
             "tubes at the cable outer diameter", "routed by build.py (bp000, L1000)", 0.6, "estimate", 8, up["harness"], off=[0, -.25, .1], opn=[0, 0, 0])
    if up["fasteners"]:
        comp("fasteners_upper", "Fasteners of the lift and arm post (named and proposed)", "MEC-014", len(up["fasteners"]), "proposed",
             "Lift sensor bracket screws, post bolts from below, rear upright T-nuts and the J1_A mounting screws.", "ISO / DIN standard part envelopes",
             "joints of the upper body", 0.2, "estimate", 8, up["fasteners"], hq=True, off=[0, 0, .1], opn=[0, 0, 0])

    # ---------------- outputs
    # meta for the registry components of model.js (class, part number, position source, mass) from bom_map.yaml
    js = open(os.path.join(MODEL, "model.js"), encoding="utf-8").read()
    reg = json.loads(re.search(r"/\*COMPONENTS-JSON\*/(.*?)/\*COMPONENTS-JSON-END\*/", js, re.S).group(1))
    meta = {}
    for c in reg:
        hits = [(bid, m) for bid, m in BM.items() if isinstance(m, dict) and c["id"] in [x.strip() for x in str(m.get("by", "")).split(",")]]
        if not hits:
            first = (c.get("bom") or "").split(",")[0].strip()
            hits = [(first, BM[first])] if first in BM else []
        cls = {"cad": "CAD-derived", "envelope": "envelope", "primitive": "primitive", "none": "not drawn"}[c["geometry"]]
        if c.get("provisional"):
            cls = "provisional"
        if c.get("placeholder"):
            cls = "placeholder"
        mm = hits[0][1] if hits else {}
        meta[c["id"]] = {"class": cls, "part_number": BOM.get(hits[0][0], {}).get("Model / order code", "")[:120] if hits else "",
                         "position_source": mm.get("pos", "CAD v0.2 assembly (openamr-platform-hw)" if c["geometry"] == "cad" else ""),
                         "mass_kg": mm.get("mass", ""), "mass_source": mm.get("msrc", "")}
    placement = {"schema": 1, "meta": meta, "frame": "base_footprint (floor under the drive-axle midpoint; x forward, y left, z up)",
                 "about": "Generated by scripts/roadmap_model/build.py. Do not edit by hand.",
                 "sources": {"datums": rev, "facts": FACTS["documents"], "snapshot": FACTS["snapshot"]},
                 "groups": "base: robot root (floor frame); col: lift assembly (x from the column axis); mov: lift stage (x from the column axis, z at L1000)",
                 "legend": {d: T["harness_domains"][d] for d in T["harness_domains"]},
                 "components": comps, "geometry": geo,
                 "hide_glb": ["battery"],   # A1: the single-row battery envelope is replaced by the cells in the side pockets
                 "front_bay": {"default": fb_default, "layout": FBR[fb_default].get("layout", ""), "relocate": fb_relocate, "glb_centre": fb_glb_centre, "relocatable": ["compute", "base_controller"]},
                 "upper_body": {k: (v if not isinstance(v, (list, tuple)) else [R(x) for x in v]) for k, v in U.items() if k != "datums_revision"}}
    json.dump(placement, open(os.path.join(MODEL, "placement.json"), "w"), separators=(",", ":"))
    # exploded.json: merge entries, add stage 9
    xp = os.path.join(MODEL, "exploded.json")
    ex = json.load(open(xp))
    if not any(s["n"] == 9 for s in ex["stages"]):
        ex["stages"].append({"n": 9, "title": "Harness", "text": "Every cable of the harness on its routed path, coloured by domain, with the P-clips, grommets, CAN terminations, the upper-body service loop and the drawn fasteners. Proposed by the roadmap model; cable_list.csv gives each route.", "frame": "base"})
    gen = ex.setdefault("generated", [])
    for cid in gen:
        ex["components"].pop(cid, None)
    ex["components"].update(exploded)
    ex["generated"] = sorted(exploded)
    json.dump(ex, open(xp, "w"), indent=1, ensure_ascii=False)

    # bom_coverage.csv
    comp_by_id = {c["id"]: c for c in comps}
    rows = []
    for bid in sorted(BOM, key=lambda k: (k.split("-")[0], k)):
        b = BOM[bid]
        m = dict(BM.get(bid, {}))
        qty = b.get("Qty", "")
        q = int(qty) if str(qty).strip().isdigit() else None
        by = m.get("by", "")
        if by in comp_by_id or by in [it["id"] for it in T["packed"] + T["fixed"]]:
            c = comp_by_id.get(by)
            if c is None:
                m.update({"cls": "not drawn", "reason": "no space found by the packer (see geometry_issues.csv)", "mass": 0})
                drawn_qty = 0
            else:
                m.setdefault("cls", c["class"])
                m.setdefault("geo", c["source"])
                m.setdefault("pos", c["position_source"])
                m.setdefault("mass", c["mass_kg"])
                m.setdefault("msrc", c["mass_source"])
                drawn_qty = c["qty"]
        else:
            drawn_qty = None
        offb = str(m.get("reason", "")).startswith(("offboard", "fallback", "set row"))
        onboard = not offb and q != 0
        if m.get("cls") == "not drawn" or by == "none":
            drawn, mq = "n", 0
        elif by == "harness" or str(by).startswith("inside:"):
            drawn, mq = "y", q
        else:
            drawn = "y"
            mq = drawn_qty if drawn_qty is not None else q
            if bid in ("MEC-001",):
                mq = 1
            if bid == "ARM-001":
                mq = 1
            if bid == "SAF-001":
                mq = 2
            if bid in ("PWR-001", "PWR-028"):
                mq = 1
            if bid == "MEC-015":
                mq = 2
            if bid == "MEC-008":
                mq = 1
        if "mqty" in m and drawn == "y":
            mq = m["mqty"]
        rows.append({"id": bid, "part": b.get("Component / assembly", ""), "part_number": b.get("Model / order code", "")[:90],
                     "qty": qty, "subsystem": b.get("Subsystem", ""), "onboard": "y" if onboard else "n",
                     "class": m.get("cls", "unmapped"), "geometry_source": m.get("geo", ""), "position_source": m.get("pos", ""),
                     "model_qty": mq if mq is not None else "", "model_component": by, "mass_kg": m.get("mass", ""), "mass_source": m.get("msrc", ""),
                     "drawn": drawn, "reason_not_drawn": m.get("reason", "") if drawn == "n" else ""})
    with open(os.path.join(MODEL, "bom_coverage.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]))
        w.writeheader()
        w.writerows(rows)
    with open(os.path.join(MODEL, "fastener_schedule.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=["joint", "part", "size", "qty", "standard", "material", "class", "drawn"])
        w.writeheader()
        w.writerows(fasteners)
    with open(os.path.join(MODEL, "cable_list.csv"), "w", newline="") as f:
        keys = ["id", "from", "to", "function", "domain", "gauge_or_type", "od_mm", "connector_a", "connector_b", "pin_or_terminal", "bom",
                "route", "route_length_m", "length_with_margin_m", "min_bend_radius_mm", "mass_kg", "from_part", "to_part", "from_xyz", "to_xyz"]
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        w.writerows(cab_rows)
    assembly(fasteners)
    # source snapshot for scripts/check_roadmap.py (CI has no ../src): the source values the model must match
    snap = {"about": "Source values the roadmap model is checked against (scripts/check_roadmap.py). Generated by build.py.",
            "datums_revision": rev, "base_link_z": FACTS["base_link_z"],
            "sensor_frames": {k: [R(x, 5) for x in v["xyz"]] for k, v in SF.items()},
            "frame_nodes": {"imu_link": "imu", "lidar_link": "lidar", "base_camera_link": "base_camera", "tof_front": "tof_front", "tof_rear": "tof_rear",
                            "us_front_left": "ultrasonic_front_left", "us_front_right": "ultrasonic_front_right",
                            "us_rear_left": "ultrasonic_rear_left", "us_rear_right": "ultrasonic_rear_right"},
            "datums": {k: v for k, v in D.items() if not isinstance(v, dict)},
            "owner_corrections": {"source": "owner, 2 Nov 2026 (to be entered in P-03 and M-01)", "getac_size": FACTS["getac"]["size"], "getac_lower_by": FACTS["getac"]["lower_by"],
                                  "light_gap": FACTS["getac"]["light_gap"], "zed_ahead_of_j1a": FACTS["zed_ahead_of_j1a"], "second_estop": FACTS["second_estop"]["position"],
                                  "receiver": {"lo": FACTS["tzbot_receiver"]["lo"], "hi": FACTS["tzbot_receiver"]["hi"], "status": FACTS["tzbot_receiver"]["status"]},
                                  "lift_rear": dict(LR, column_rear_x=FACTS["lift_rear"]["column_rear_x"], sensor_z=FACTS["lift_rear"]["sensor_z"])}}
    snap["sensor_frames_rpy"] = {k: [R(x, 5) for x in v["rpy"]] for k, v in SF.items()}
    snap["sensor_bodies"] = sensor_bodies(G, SF, snap["frame_nodes"])
    old_snap = os.path.join(MODEL, "source_snapshot.json")
    if os.path.exists(old_snap):
        keep = json.load(open(old_snap)).get("combined_model")
        if keep:
            snap["combined_model"] = keep
    json.dump(snap, open(os.path.join(REPO, "docs", "assets", "roadmap", "model", "source_snapshot.json"), "w"), indent=1)
    summary = {"packed": {k: [[R(x) for x in v[0]], [R(x * 1000, 1) for x in v[1]]] for k, v in placed.items()}, "nofit": nofit,
               "front_bay": {o: {"fit": fb_fit[o], "placed": {k: [v[0], [R(x) for x in v[1]], [R(x * 1000, 1) for x in v[2]]] for k, v in FBR[o]["placed"].items()},
                                 "plates": FBR[o]["plates"], "shelf": FBR[o].get("shelf"), "shelf_order": FBR[o].get("shelf_order")} for o in FBR},
               "front_bay_default": fb_default, "relocate": fb_relocate, "receiver": {"centre": FACTS["tzbot_receiver"]["centre"], "lo": TZL["lo"].round(4).tolist(), "hi": TZL["hi"].round(4).tolist(), "cutout": TZL["cutout"], "orientation": TZL["orientation"], "cutout_mm": TZL["cutout_mm"], "cutout_full_mm": TZL["cutout_full_mm"], "gap_m": R(TZL["lo"][2] - FACTS["tzbot_transmitter"]["size"][2]), "status": FACTS["tzbot_receiver"]["status"]},
               "rear_layout": {k: RL[k] for k in ("measured", "pocket_free", "pockets", "plate", "margin", "cutout", "trays", "link_z")},
               "k1k2_options": opt, "gi080": gi80, "battery_trays": tray_check, "cables_25mm2": BEND25, "bolts": bolts, "bay_plate_area_m2": R(area, 4), "seed": issues_seed,
               "coverage": {c: sum(1 for r in rows if r["class"] == c) for c in sorted({r["class"] for r in rows})},
               "onboard": sum(1 for r in rows if r["onboard"] == "y"), "records": len(rows)}
    json.dump(summary, open(os.path.join(HERE, "build_summary.json"), "w"), indent=1, default=str)
    print(json.dumps({k: summary[k] for k in ("nofit", "coverage", "onboard", "records")}, indent=0))
    print("K1/K2:", {k: v["fits"] for k, v in opt.items()})


SENSOR_TYPE = {"imu_link": "imu", "lidar_link": "lidar", "base_camera_link": "base_camera", "tof_front": "tof", "tof_rear": "tof",
               "us_front_left": "ultrasonic", "us_front_right": "ultrasonic", "us_rear_left": "ultrasonic", "us_rear_right": "ultrasonic"}


def rpy_matrix(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]) @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]) @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])


def sensor_bodies(G, SF, frame_nodes):
    """Reference body of each base sensor for the pose check of scripts/check_roadmap.py: its drawn GLB mesh expressed in
    its sensor_frames.yaml frame (mm, vertex order of the GLB), validated against the platform-sw visual STL of the sensor
    type (largest vertex-to-surface distance, recorded; at most 0.6 mm or the build stops)."""
    import trimesh
    stl_dir = os.path.join(os.path.dirname(os.path.dirname(SENSOR_FRAMES)), "meshes", "visual")
    out, meshes = {}, {}
    for frame, node in frame_nodes.items():
        typ = SENSOR_TYPE[frame]
        f = SF[frame]
        local = (G[node]["v"] - np.array(f["xyz"])) @ rpy_matrix(*f["rpy"])
        if typ not in meshes:
            meshes[typ] = trimesh.load(os.path.join(stl_dir, typ + ".stl"), force="mesh")
        _, dist, _ = trimesh.proximity.closest_point(meshes[typ], local)
        if dist.max() > 0.0006:
            raise SystemExit("sensor body %s: drawn mesh is %.2f mm off the source STL %s.stl in its frame" % (node, dist.max() * 1000, typ))
        lo, hi = local.min(0), local.max(0)
        out[frame] = {"node": node, "type": typ, "stl": "openamr-platform-sw ros2/src/openamrobot_description/meshes/visual/%s.stl" % typ,
                      "stl_residual_max_mm": round(float(dist.max()) * 1000, 3),
                      "centre_local_mm": [round(float(x) * 1000, 2) for x in (lo + hi) / 2],
                      "extents_mm": [round(float(x) * 1000, 2) for x in hi - lo],
                      "ref_local_mm": [[round(float(x) * 1000, 3) for x in p] for p in local]}
    return out


def assembly(fasteners):
    steps = [
        (1, "Base sheet (receiver cut-out at the rear reserved for release 3.0), panels, supports, centre bracket (MEC-001)", "MEC-001 sheet-metal joints (CAD v0.2)", "hex key 4 / 5 mm", "ISO 898-1 M5 8.8: 6 Nm", "open frame, all faces reachable"),
        (2, "Hub motors with MEC-015 brackets, castors with MEC-016 shims", "M8 x 20 bracket bolts; castor M6", "13 mm socket, torque wrench", "M8 8.8: 25 Nm", "from below with the base on its side; brake side inboard"),
        (3, "TZBOT receiver zone at the rear panel: reserved, not installed in 2.0 (release 3.0)", "none in 2.0", "", "", "keep the 20 mm metal-free margin and the plate underside 122 mm above the floor free"),
        (4, "Motor driver on MMP.02.00.00.002, electronics bracket MMP.04.00.00.002 (shortened to x 0.100) with the IMU board", "M3/M4", "hex key 2.5 / 3 mm", "M3: 1.2 Nm, M4: 2.8 Nm", "from above, cover off; nothing heavy or vibrating on the IMU bracket"),
        (5, "Front bay (one layout): lower plate on the base sheet (top z " + "%.3f" % FB.FLOOR + "), DIN carrier with PNOZ s3 and DDR-240B-24 on the arch front legs, RSD-100B-24 and small power parts, shelf on standoffs with compute (J401), NUCLEO, FB-C and terminal blocks; no receiver in the bay (A1)", "M4 standoffs, M5 carrier screws", "hex key 2.5 / 3 mm, nut driver 7 mm", "M4: 2.8 Nm", "strip boards first, then the lower plate, the DIN carrier, the shelf; every fuse (FB-C on the shelf) and the PNOZ terminals reachable from above with the cover off"),
        (6, "Battery: two removable pocket trays MEC-007 with 4 + 4 LF105 upright, straps; the 8S series link across the centre joins them through the keyed main connector PWR-018 (A9)", "M6 x 12 tray screws into rivet nuts", "hex key 5 mm, 13 mm socket for the M8 terminals", "M6 8.8: 10 Nm; cell terminals per EVE", "cells go in from above with the cover off (each tray with its 4 cells lowered or lifted on its own after PWR-018 is unplugged); side-panel return flanges notched at x -0.275 to -0.133 (GI-025, decided)"),
        (7, "Rear power plate MEC-006 above the receiver zone (underside 122 mm): F0, K1/K2, precharge, FB-A, PWR-017, KCHG, F-CHG; disconnect and SB50 on the rear panel", "M5 x 12", "hex key 4 mm, 13 mm socket for M8 lugs", "M5: 5.5 Nm; M8 lugs per maker", "after the trays; nothing above a fuse; plate on 4 standoffs from the base sheet outside the metal-free margin; it comes out without removing the cells (2 mm clear of the trays in plan) once PWR-018 on the series link above it is unplugged"),
        (8, "Sensors: LiDAR on the shortened MMP.07 on the lower plate + 17.5 mm spacer, Gemini on MEC-009, MB7060 with lock nuts, TF-Luna, E-stop, RESET", "M4 inserts, 3/4 in NPS nuts", "hex key 3 mm, 32 mm spanner", "M4: 1.5 Nm into PETG inserts", "front MB7060 nuts reached from inside before the bay plate goes in"),
        (9, "Harness: trunks (front trunk below the scan plane), grommets, P-clips, connectors; CAN terminations", "M4 P-clip screws", "crimp tools (TST-004), hex key 2.5 mm", "M4: 2 Nm", "cover off; every fuse and connector reachable"),
        (10, "Cover with the opening extended to x 0.260 around the lift base plate, flanges", "MEC-001 cover screws", "hex key 3 mm", "M4: 2.8 Nm", "from above"),
        (11, "DOLD column on the lift base plate MEC-019, from below, on the bench (bp000 or bp050 hole set)", "4 x M8 x 30 DIN 7500 countersunk, flush", "5 mm hex key, torque wrench", "M8 thread-forming: per DOLD", "plate upside down on the bench, full access to the underside; heads flush so the plate sits flat on the arch"),
        (12, "Lift base plate with the column onto the arch, bolted from above into the 4 arch rivet nuts", "4 x M8 x 20 ISO 4762 8.8 + ISO 7089 washers", "6 mm hex key or 6 mm bit on a torque wrench", "M8 8.8 into a stainless blind rivet nut: 15 Nm (rivet-nut limit, below the 25 Nm bolt value)", "bolt heads at y +/-0.050 beside the 60 mm column: 13.5 mm from the head edge to the column face, a 6 mm hex bit (13 mm socket body) fits; rivet nuts captive, no access from below needed"),
        (13, "Adapter plate (one part with the rear extension for the flag rod, A6), HFS6 post, rear upright, stiffener", "M8 x 25, M6 T-nuts", "6 / 5 mm hex key", "M8: 25 Nm, M6: 10 Nm", "post bolts from below the adapter plate before it goes on the carriage"),
        (14, "Arms on the post (1 mm spacers), ZED bracket and camera, Getac pocket and light plate, second E-stop housing on the adapter plate behind the post (A5)", "M6 T-nuts", "5 mm hex key", "M6: 10 Nm", "arms at home pose; Getac pocket last"),
        (15, "Lift stop sensors on the rear face of the static column (A6), flag rod under the adapter-plate rear extension (M5 into the rod end, corner bracket), flag", "LFT-007 set", "hex key 2.5 / 3 / 4 mm", "M4: 2 Nm", "lift at L1000; set the 2 mm flag gap"),
        (16, "Service loop and upper-body cables (arm cables and the second E-stop loop through the lift cable chain), function test", "", "", "", "check the loop at L1350 and L1000"),
    ]
    with open(os.path.join(MODEL, "assembly_sequence.csv"), "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["step", "parts", "fasteners", "tool", "standard_torque_reference", "access_check"])
        w.writerows(steps)


if __name__ == "__main__":
    main()
