#!/usr/bin/env python3
"""Collision check of every cable and busbar route against the solid parts of the model (Phase 7, 3 Nov 2026).

Reads model/harness_routes.json (routes, obstacle boxes, grommets, openings) and the base GLB (structure meshes). Reports:
- a route point inside a component box farther than 25 mm from the cable's own ends (through a part);
- a route passing a structure panel (GLB mesh, sampled) away from a recorded grommet, a declared opening or its own ends;
- a zero-radius bend (a corner the route cannot hold at its class minimum, from route_radius).
Writes a JSON summary (argument 1, default evidence path) and prints the counts. Static parts at bp000, L1000.
"""
import json
import math
import os
import sys

import numpy as np

import harness as HN
from frames import MODEL, glb_nodes


def main(out_path=None):
    H = json.load(open(os.path.join(MODEL, "harness_routes.json"), encoding="utf-8"))
    G = glb_nodes()
    struct = []
    for k in HN.STRUCT_GLB:
        if k in G:
            pts = HN.mesh_points(np.array(G[k]["v"]), np.array(G[k]["f"]), 0.004)
            struct.append((k, pts))
    opens = [(np.array(o["lo"]), np.array(o["hi"])) for o in HN.OPENINGS]
    grom = [np.array(g["p"]) for g in H.get("grommets", [])]
    obs = [(o["id"], np.array(o["lo"]), np.array(o["hi"])) for o in H["obstacles"]]
    through, panels, bends = [], [], []
    for c in H["cables"]:
        own = set(c.get("own", []))
        r = c["od_mm"] / 2000
        for sec in c["sections"]:
            if sec["kind"] != "base":
                continue
            pts = sec["pts"]
            ends = [np.array(pts[0]), np.array(pts[-1])]
            sm = [q for _, q in HN.sample(pts, 0.003)]
            hit = {}
            for q in sm:
                if min(np.linalg.norm(q - e) for e in ends) <= 0.025:
                    continue
                for oid, lo, hi in obs:
                    if oid in own:
                        continue
                    if (q > lo + 0.0005).all() and (q < hi - 0.0005).all():
                        hit.setdefault(oid, q)
            for oid, q in hit.items():
                through.append({"cable": c["id"], "part": oid, "at": [round(float(v), 4) for v in q]})
            S = np.array(sm)
            for k, P in struct:
                lo, hi = S.min(0) - r - 0.01, S.max(0) + r + 0.01
                m = ((P > lo) & (P < hi)).all(1)
                if not m.any():
                    continue
                Pk = P[m]
                for q in sm:
                    d = np.linalg.norm(Pk - q, axis=1).min()
                    if d >= r * 0.6:
                        continue
                    if min(np.linalg.norm(q - e) for e in ends) <= 0.030:
                        continue
                    if any((q >= a - 0.003).all() and (q <= b + 0.003).all() for a, b in opens):
                        continue
                    if any(np.linalg.norm(q - g) <= 0.025 for g in grom):
                        continue
                    panels.append({"cable": c["id"], "panel": k, "at": [round(float(v), 4) for v in q]})
                    break
        for sec in c["sections"]:
            if sec["kind"] == "chain" or len(sec["pts"]) < 3:
                continue
            rr = HN.route_radius(sec["pts"])[0]
            if rr * 1000 < max(1.0, c["min_bend_mm"]) - 0.5:
                bends.append({"cable": c["id"], "section": sec["kind"], "radius_mm": round(rr * 1000, 1), "min_mm": c["min_bend_mm"]})
    res = {"cables": len(H["cables"]), "busbars": sum(1 for c in H["cables"] if c.get("kind") == "busbar"), "through_parts": through,
           "through_panels_without_opening": panels, "bends_below_minimum": bends,
           "note": "static parts at bp000 and L1000; moving sections and the energy chain are checked by check_roadmap.py (lift rules) and analyse.py"}
    print("collision check: %d routes (%d busbars); through parts %d, through panels without an opening %d, bends below the minimum %d" % (
        res["cables"], res["busbars"], len(through), len(panels), len(bends)))
    if out_path:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
        json.dump(res, open(out_path, "w"), indent=1)
    return res


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
