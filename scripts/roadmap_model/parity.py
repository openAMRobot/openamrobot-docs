#!/usr/bin/env python3
"""Roadmap vs combined model parity report (convergence phase 1: warn only, nothing switches).

Compares, for every URDF link mapped in link_map.yaml and every configuration (bp000 at L1000 / L1175 / L1350,
bp050 at L1000; hp30; arms at all joints 0), the world pose (mm, deg) and primitive size of the expanded
combined robot model (docs/assets/roadmap/model/combined_robot*.urdf, written by urdf_expand.py) with the
roadmap model as the pages build it (parity_dump.js). Tolerance 0.5 mm and 0.2 deg. Lists unmapped links on both
sides and the intended pending differences of the 2 Nov 2026 owner decisions. Writes:
  docs/assets/roadmap/model/parity_report.csv
  scripts/roadmap_model/parity_summary.json   (counts for the hardware page, STATE.md and check_roadmap.py)
Usage:
  python3 parity.py --dump parity_dump.json [--sync-roadmap-only]   full run (needs ../src meshes and a page dump)
  python3 parity.py --ci                                               CI: re-reads the committed report, warns only
"""
import argparse
import csv
import hashlib
import json
import math
import os
import sys
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from frames import HERE, MODEL, REPO

TOL_MM, TOL_DEG = 0.5, 0.2
CONFIGS = [("bp000", "L1000", 0.0), ("bp000", "L1175", 0.175), ("bp000", "L1350", 0.350), ("bp050", "L1000", 0.0)]
URDF = {"bp000": "combined_robot.urdf", "bp050": "combined_robot_bp050.urdf"}
AMENT = os.path.abspath(os.path.join(REPO, "..", "ament", "share"))
# roadmap part groups of the upper body (page parts not in placement.json): the URDF link each attaches to
COL = {"lift_base_plate", "lift_column", "second_estop", "lift_stop_sensors", "lift_sensor_brackets"}
MOV = {"adapter_plate", "arm_profile", "head_camera_bracket", "head_camera", "getac_tablet", "head_light", "flag_rod", "lift_flag",
       "rod_corner_bracket", "slot_cover_strips", "openarm_left", "openarm_right"}
ATTACH = {"base": "base_link", "col": "lift_column_base_link", "mov": "lift_carriage_link"}


def rpy_m(r, p, y):
    cr, sr, cp, sp, cy, sy = math.cos(r), math.sin(r), math.cos(p), math.sin(p), math.cos(y), math.sin(y)
    return np.array([[cy, -sy, 0], [sy, cy, 0], [0, 0, 1]]) @ np.array([[cp, 0, sp], [0, 1, 0], [-sp, 0, cp]]) @ np.array([[1, 0, 0], [0, cr, -sr], [0, sr, cr]])


def tf(xyz="0 0 0", rpy="0 0 0"):
    M = np.eye(4)
    M[:3, :3] = rpy_m(*[float(v) for v in rpy.split()])
    M[:3, 3] = [float(v) for v in xyz.split()]
    return M


def axis_rot(ax, q):
    ax = np.array(ax, float) / np.linalg.norm(ax)
    K = np.array([[0, -ax[2], ax[1]], [ax[2], 0, -ax[0]], [-ax[1], ax[0], 0]])
    M = np.eye(4)
    M[:3, :3] = np.eye(3) + math.sin(q) * K + (1 - math.cos(q)) * K @ K
    return M


class Urdf:
    def __init__(self, path):
        self.root = ET.parse(path).getroot()
        self.links = {l.get("name"): l for l in self.root.findall("link")}
        self.joints = {j.find("child").get("link"): j for j in self.root.findall("joint")}

    def world(self, link, q):
        """World (base_footprint) matrix of a link; q: joint name -> position."""
        if link not in self.joints:
            return np.eye(4)
        j = self.joints[link]
        o = j.find("origin")
        M = self.world(j.find("parent").get("link"), q) @ (tf(o.get("xyz", "0 0 0"), o.get("rpy", "0 0 0")) if o is not None else np.eye(4))
        v = q.get(j.get("name"), 0.0)
        ax = j.find("axis")
        axv = [float(x) for x in ax.get("xyz").split()] if ax is not None else [1, 0, 0]
        if j.get("type") == "prismatic":
            T = np.eye(4)
            T[:3, 3] = np.array(axv) * v
            M = M @ T
        elif j.get("type") in ("revolute", "continuous") and v:
            M = M @ axis_rot(axv, v)
        return M

    def visuals(self, link):
        return self.links[link].findall("visual") if link in self.links else []

    def mass(self, link):
        m = self.links[link].find("inertial/mass") if link in self.links else None
        return float(m.get("value")) if m is not None else 0.0


_mesh_cache = {}


def mesh_points(fn, scale):
    if not fn.startswith("package://"):
        return None
    pkg, rel = fn[10:].split("/", 1)
    p = os.path.join(AMENT, pkg, rel)
    if not os.path.exists(p) or not p.lower().endswith(".stl"):
        return None
    if p not in _mesh_cache:
        import trimesh
        _mesh_cache[p] = np.asarray(trimesh.load(p, force="mesh").vertices)
    return _mesh_cache[p] * scale


def visual_points(v):
    g = v.find("geometry")[0]
    o = v.find("origin")
    T = tf(o.get("xyz", "0 0 0"), o.get("rpy", "0 0 0")) if o is not None else np.eye(4)
    if g.tag == "box":
        s = np.array([float(x) for x in g.get("size").split()]) / 2
        P = np.array([[a, b, c] for a in (-s[0], s[0]) for b in (-s[1], s[1]) for c in (-s[2], s[2])])
    elif g.tag == "cylinder":
        r, h = float(g.get("radius")), float(g.get("length"))
        a = np.linspace(0, 2 * np.pi, 72, endpoint=False)
        ring = np.c_[r * np.cos(a), r * np.sin(a)]
        P = np.vstack([np.c_[ring, np.full(72, -h / 2)], np.c_[ring, np.full(72, h / 2)]])
    elif g.tag == "sphere":
        r = float(g.get("radius"))
        P = np.array([[a, b, c] for a in (-r, r) for b in (-r, r) for c in (-r, r)])
    elif g.tag == "mesh":
        sc = np.array([float(x) for x in g.get("scale", "1 1 1").split()])
        P = mesh_points(g.get("filename"), sc)
        if P is None:
            return None, T
    else:
        return None, T
    return P, T


def urdf_box(U, names, q):
    pts, rot = [], None
    for n in names:
        link, _, idx = n.partition("#")
        W = U.world(link, q)
        vs = U.visuals(link)
        if idx:
            vs = [vs[int(idx)]]
        for v in vs:
            P, T = visual_points(v)
            if P is None:
                return None, None
            M = W @ T
            pts.append(P @ M[:3, :3].T + M[:3, 3])
            rot = M[:3, :3]
    if not pts:
        return None, None
    P = np.vstack(pts)
    return (P.min(0), P.max(0)), rot


def page_box(cfg, ids):
    lo, hi, q = None, None, None
    for pid in ids:
        name, _, idx = pid.partition("#")
        groups = cfg["parts"].get(name)
        if not groups:
            return None, None
        if idx:
            groups = [groups[int(idx)]]
        for g in groups:
            if g is None:
                continue
            a, b = np.array(g["min"]), np.array(g["max"])
            lo = a if lo is None else np.minimum(lo, a)
            hi = b if hi is None else np.maximum(hi, b)
            q = g["q"]
    return ((lo, hi), q) if lo is not None else (None, None)


def quat_m(q):
    x, y, z, w = q
    return np.array([[1 - 2 * (y * y + z * z), 2 * (x * y - z * w), 2 * (x * z + y * w)],
                     [2 * (x * y + z * w), 1 - 2 * (x * x + z * z), 2 * (y * z - x * w)],
                     [2 * (x * z - y * w), 2 * (y * z + x * w), 1 - 2 * (x * x + y * y)]])


def ang(Ra, Rb):
    c = (np.trace(Ra.T @ Rb) - 1) / 2
    return math.degrees(math.acos(max(-1.0, min(1.0, c))))


def page_frame(cfg, ref):
    arm, _, k = ref.partition(":")
    a = cfg["arms"][arm.split("_")[1]]
    if k == "base":
        m = a["base"]
    elif k.startswith("link"):
        m = a["links"][int(k[4:]) - 1]
    else:
        m = a["fingers"][int(k[6:]) - 1]
    M = np.array(m).reshape(4, 4).T  # three.js column-major
    return M


def groups_of():
    P = json.load(open(os.path.join(MODEL, "placement.json")))
    g = {k: v["group"] for k, v in P["geometry"].items()}
    for k in COL:
        g.setdefault(k, "col")
    for k in MOV:
        g.setdefault(k, "mov")
    return g


def full(args):
    LM = yaml.safe_load(open(os.path.join(HERE, "link_map.yaml")))
    dump = json.load(open(args.dump))["configs"]
    U = {bp: Urdf(os.path.join(MODEL, f)) for bp, f in URDF.items()}
    rows = []
    mapped_r, mapped_u = set(), set()
    for e in LM["mapped"]:
        for n in e["urdf"]:
            mapped_u.add(n.partition("#")[0])
        for r in e["roadmap"]:
            mapped_r.add(r.partition("#")[0].partition(":")[0])
    for bp, stop, tr in CONFIGS:
        cfg = dump["%s %s" % (bp, stop)]
        q = {"lift_joint": tr}
        for e in LM["mapped"]:
            row = {"configuration": "%s %s" % (bp, stop), "urdf": " + ".join(e["urdf"]), "roadmap": " + ".join(e["roadmap"]), "mode": e["mode"],
                   "dx_mm": "", "dy_mm": "", "dz_mm": "", "dpos_mm": "", "dsize_mm": "", "drot_deg": "", "status": "", "note": e.get("pending") or e.get("note", "")}
            if e["mode"] == "frame":
                W = U[bp].world(e["urdf"][0], q)
                P = page_frame(cfg, e["roadmap"][0])
                d = (P[:3, 3] - W[:3, 3]) * 1000
                row.update(dx_mm=round(d[0], 2), dy_mm=round(d[1], 2), dz_mm=round(d[2], 2), dpos_mm=round(float(np.linalg.norm(d)), 2),
                           drot_deg=round(ang(W[:3, :3], P[:3, :3]), 3), dsize_mm="n/a (upstream mesh)")
                bad = row["dpos_mm"] > TOL_MM or row["drot_deg"] > TOL_DEG
            else:
                ub, urot = urdf_box(U[bp], e["urdf"], q)
                pb, pq = page_box(cfg, e["roadmap"])
                if ub is None or pb is None:
                    row["status"] = "not compared (%s)" % ("URDF visual not readable" if ub is None else "not drawn on the page")
                    rows.append(row)
                    continue
                cu, cp = (ub[0] + ub[1]) / 2, (pb[0] + pb[1]) / 2
                d = (cp - cu) * 1000
                ds = ((pb[1] - pb[0]) - (ub[1] - ub[0])) * 1000
                row.update(dx_mm=round(d[0], 2), dy_mm=round(d[1], 2), dz_mm=round(d[2], 2), dpos_mm=round(float(np.linalg.norm(d)), 2),
                           dsize_mm=round(float(np.abs(ds).max()), 2), size_urdf_mm="x".join("%.1f" % v for v in (ub[1] - ub[0]) * 1000),
                           size_roadmap_mm="x".join("%.1f" % v for v in (pb[1] - pb[0]) * 1000))
                if e.get("rot") and pq is not None:
                    row["drot_deg"] = round(ang(urot, quat_m(pq)), 3)
                bad = row["dpos_mm"] > TOL_MM or row["dsize_mm"] > TOL_MM or (row["drot_deg"] != "" and row["drot_deg"] > TOL_DEG)
            row["status"] = ("pending (intended)" if e.get("pending") else "out of tolerance") if bad else "matched"
            rows.append(row)
    # unmapped
    ref = dump["bp000 L1000"]
    G = groups_of()
    u_links = [n for n, l in U["bp000"].links.items() if l.findall("visual")]
    u_un = [n for n in u_links if n not in mapped_u]
    r_un = sorted(k for k in ref["parts"] if k not in mapped_r)
    if args.sync_roadmap_only:
        W0 = {lk: U["bp000"].world(lk, {}) for lk in ATTACH.values()}
        ro = {}
        for k in r_un:
            b, _ = page_box(ref, [k])
            lk = ATTACH[G.get(k, "base")]
            c = (b[0] + b[1]) / 2 if b else np.zeros(3)
            off = np.linalg.inv(W0[lk]) @ np.r_[c, 1]
            ro[k] = {"attach": lk, "offset_m": [round(float(x), 4) for x in off[:3]]}
        txt = open(os.path.join(HERE, "link_map.yaml")).read().split("\nroadmap_only:")[0]
        lines = ["", "roadmap_only:"] + ["  %s: {attach: %s, offset_m: [%s]}" % (k, v["attach"], ", ".join("%g" % x for x in v["offset_m"])) for k, v in ro.items()]
        open(os.path.join(HERE, "link_map.yaml"), "w").write(txt + "\n".join(lines) + "\n")
        LM = yaml.safe_load(open(os.path.join(HERE, "link_map.yaml")))
    listed = set(LM.get("roadmap_only") or {})
    for k in u_un:
        rows.append({"configuration": "all", "urdf": k, "roadmap": "", "mode": "unmapped", "status": "unmapped (URDF only)",
                     "note": (LM.get("urdf_only") or {}).get(k, "not in link_map.yaml")})
    for k in r_un:
        att = (LM.get("roadmap_only") or {}).get(k, {})
        pend = (LM.get("pending_roadmap_only") or {}).get(k)
        rows.append({"configuration": "all", "urdf": att.get("attach", ""), "roadmap": k, "mode": "roadmap only",
                     "status": "pending (intended)" if pend else ("roadmap only" if k in listed else "unmapped (roadmap, not listed)"),
                     "note": pend or ("offset %s m in %s" % (att.get("offset_m"), att.get("attach")) if att else "add to link_map.yaml roadmap_only")})
    keys = ["configuration", "urdf", "roadmap", "mode", "status", "dx_mm", "dy_mm", "dz_mm", "dpos_mm", "dsize_mm", "drot_deg", "size_urdf_mm", "size_roadmap_mm", "note"]
    with open(os.path.join(MODEL, "parity_report.csv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=keys)
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "") for k in keys})
    cmp_rows = [r for r in rows if r["mode"] in ("aabb", "frame")]
    items = {}
    for r in cmp_rows:
        items.setdefault(r["urdf"], []).append(r["status"])
    summ = {"tolerance_mm": TOL_MM, "tolerance_deg": TOL_DEG, "configurations": ["%s %s" % c[:2] for c in CONFIGS],
            "mapped_items": len(items),
            "matched": sum(1 for v in items.values() if all(s == "matched" for s in v)),
            "out_of_tolerance": sum(1 for v in items.values() if "out of tolerance" in v),
            "pending": sum(1 for v in items.values() if "pending (intended)" in v) + sum(1 for r in rows if r["mode"] == "roadmap only" and r["status"] == "pending (intended)"),
            "pending_mapped": sum(1 for v in items.values() if "pending (intended)" in v),
            "pending_roadmap_only": sum(1 for r in rows if r["mode"] == "roadmap only" and r["status"] == "pending (intended)"),
            "pending_list": sorted({(r["urdf"] if r["mode"] != "roadmap only" else r["roadmap"]) + ": " + r["note"] for r in rows if r["status"] == "pending (intended)"}),
            "out_list": sorted({r["urdf"] + " / " + r["roadmap"] for r in rows if r["status"] == "out of tolerance"}),
            "not_compared": sum(1 for v in items.values() if any(s.startswith("not compared") for s in v)),
            "unmapped_urdf": len(u_un), "roadmap_only": sum(1 for r in rows if r["mode"] == "roadmap only"),
            "unmapped_roadmap": sum(1 for r in rows if r["status"] == "unmapped (roadmap, not listed)"),
            "comparisons": len(cmp_rows), "comparisons_out": sum(1 for r in cmp_rows if r["status"] == "out of tolerance"),
            "worst": sorted(({"urdf": r["urdf"], "roadmap": r["roadmap"], "configuration": r["configuration"], "dpos_mm": r["dpos_mm"], "dsize_mm": r["dsize_mm"]}
                             for r in cmp_rows if r["status"] == "out of tolerance"), key=lambda x: -max(x["dpos_mm"] or 0, x["dsize_mm"] if isinstance(x["dsize_mm"], float) else 0))[:12],
            "urdf_sha256": {f: hashlib.sha256(open(os.path.join(MODEL, f), "rb").read()).hexdigest() for f in URDF.values()},
            "sources": json.load(open(os.path.join(MODEL, "source_snapshot.json"))).get("combined_model", {}).get("sources", {})}
    json.dump(summ, open(os.path.join(HERE, "parity_summary.json"), "w"), indent=1, default=float)
    print(json.dumps({k: summ[k] for k in ("mapped_items", "matched", "out_of_tolerance", "pending", "not_compared", "unmapped_urdf", "roadmap_only", "unmapped_roadmap")}))


def ci():
    """Warn-only CI step: report present and made from the committed URDF; one warning per out-of-tolerance item."""
    try:
        summ = json.load(open(os.path.join(HERE, "parity_summary.json")))
        rows = list(csv.DictReader(open(os.path.join(MODEL, "parity_report.csv"))))
    except (OSError, ValueError) as e:
        print("::warning::parity report missing (%s); run scripts/roadmap_model/parity.py" % e)
        return
    for f, h in summ.get("urdf_sha256", {}).items():
        p = os.path.join(MODEL, f)
        if not os.path.exists(p) or hashlib.sha256(open(p, "rb").read()).hexdigest() != h:
            print("::warning::parity report is older than %s; rerun urdf_expand.py and parity.py" % f)
    seen = set()
    for r in rows:
        if r["status"] in ("out of tolerance", "unmapped (roadmap, not listed)") and (r["urdf"], r["roadmap"]) not in seen:
            seen.add((r["urdf"], r["roadmap"]))
            print("::warning::roadmap vs combined model: %s / %s %s (%s, dpos %s mm, dsize %s mm)" % (r["urdf"], r["roadmap"], r["status"], r["configuration"], r["dpos_mm"], r["dsize_mm"]))
    print("parity (warn only): %d mapped items, %d matched, %d out of tolerance, %d pending, %d URDF-only, %d roadmap-only" % (
        summ["mapped_items"], summ["matched"], summ["out_of_tolerance"], summ["pending"], summ["unmapped_urdf"], summ["roadmap_only"]))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dump")
    ap.add_argument("--ci", action="store_true")
    ap.add_argument("--sync-roadmap-only", action="store_true")
    a = ap.parse_args()
    if a.ci or not a.dump:
        ci()
        return
    full(a)


if __name__ == "__main__":
    sys.exit(main())
