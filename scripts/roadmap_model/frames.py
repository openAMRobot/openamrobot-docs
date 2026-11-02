"""Frames and source readers shared by the roadmap model scripts.

One conversion helper (bl_to_bf) is used everywhere: base_link (platform-sw sensor_frames.yaml, the base GLB)
to base_footprint (the roadmap model root, floor under the drive-axle midpoint, x forward, y left, z up; REP 103/105).
The three.js scene uses the same axes (model.js root group, camera.up = +z), so no other mapping is needed.
"""
import base64
import json
import os
import struct

import numpy as np
import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", ".."))
SRC = os.environ.get("OAMR_SRC", os.path.abspath(os.path.join(REPO, "..", "src")))
MODEL = os.path.join(REPO, "docs", "assets", "roadmap", "model")
DATUMS = os.path.join(SRC, "openamr-upperbody-sw", "ros2", "src", "openamrobot_upperbody_description", "config", "datums.yaml")
SENSOR_FRAMES = os.path.join(SRC, "openamr-platform-sw", "ros2", "src", "openamrobot_description", "config", "sensor_frames.yaml")


def load_yaml(p):
    with open(p, encoding="utf-8") as f:
        return yaml.safe_load(f)


FACTS = load_yaml(os.path.join(HERE, "facts.yaml"))
BASE_LINK_Z = FACTS["base_link_z"]


def bl_to_bf(p):
    """base_link point (x, y, z) to base_footprint (the only frame conversion of the model)."""
    return [float(p[0]), float(p[1]), float(p[2]) + BASE_LINK_Z]


def datums():
    d = load_yaml(DATUMS)
    return d["revision"], {k: v.get("value") for k, v in d["datums"].items()}


def sensor_frames():
    d = load_yaml(SENSOR_FRAMES)["frames"]
    return {k: {"xyz": bl_to_bf(v["xyz"]), "rpy": v["rpy"], "status": v.get("status")} for k, v in d.items()}


def glb_nodes(path=None):
    """Base GLB nodes as {id: {'extras', 'v' (base_footprint), 'f'}}."""
    path = path or os.path.join(MODEL, "base_glb.js")
    s = open(path, encoding="utf-8").read()
    t = base64.b64decode(s[s.index('"') + 1:s.rindex('"')].replace(".", ""))
    jl = struct.unpack("<I", t[12:16])[0]
    doc = json.loads(t[20:20 + jl])
    b0 = 28 + jl
    out = {}
    for n in doc["nodes"]:
        if "mesh" not in n:
            continue
        ex = n.get("extras", {"id": n["name"]})
        vs, fs, off = [], [], 0
        for p in doc["meshes"][n["mesh"]]["primitives"]:
            a = doc["accessors"][p["attributes"]["POSITION"]]
            bv = doc["bufferViews"][a["bufferView"]]
            o = b0 + bv.get("byteOffset", 0)
            v = np.frombuffer(t[o:o + bv["byteLength"]], dtype="<f4").reshape(-1, 3).astype(float)
            ia = doc["accessors"][p["indices"]]
            ibv = doc["bufferViews"][ia["bufferView"]]
            o = b0 + ibv.get("byteOffset", 0)
            idx = np.frombuffer(t[o:o + ibv["byteLength"]], dtype="<u2" if ia["componentType"] == 5123 else "<u4").reshape(-1, 3)
            fs.append(idx + off)
            vs.append(v)
            off += len(v)
        v = np.vstack(vs)
        v[:, 2] += BASE_LINK_Z
        out[ex["id"]] = {"extras": ex, "v": v, "f": np.vstack(fs)}
    return out


def aabb(v):
    return np.array(v).min(0), np.array(v).max(0)


_TZ = None


def tzbot_layout():
    """TZBOT WCM-500-24 receiver box (base_footprint, m) from facts.yaml: front edge front_gap behind the front panel inner
    face, centred on y, bottom below_base_sheet under the base sheet underside. Both orientations (170 mm along x or along y)
    are measured against the LiDAR support MMP.07 of the CAD (GLB mesh, surface samples) and by the base-sheet cut-out
    (receiver outline + metal_clear, up to the front panel bottom flange line x 0.370); the larger clearance wins, then the
    smaller cut-out. Also writes tzbot_receiver.centre / lo / hi / orientation into FACTS for the scripts that read them."""
    global _TZ
    if _TZ is not None:
        return _TZ
    f = FACTS["tzbot_receiver"]
    L, W, H = f["size"]
    mc = f["metal_clear"]
    x_front = f["front_panel_inner_x"] - f["front_gap"]
    z_bot = FACTS["base_sheet"]["bottom"] - f["below_base_sheet"]
    G = glb_nodes()
    v, fc = G["lidar_support"]["v"], G["lidar_support"]["f"]
    tri = v[fc]
    pts = np.vstack([tri.reshape(-1, 3)] + [tri[:, 0] * a + tri[:, 1] * b + tri[:, 2] * (1 - a - b)
                                             for a, b in ((1 / 3, 1 / 3), (.5, .25), (.25, .5), (.25, .25), (.5, .5), (.5, 0), (0, .5))])

    def sdf(lo, hi):
        c, h = (lo + hi) / 2, (hi - lo) / 2
        q = np.abs(pts - c) - h
        return float((np.linalg.norm(np.maximum(q, 0), axis=1) + np.minimum(q.max(1), 0)).min())

    cand = {}
    for key, (sx, sy) in (("170 mm along x, 150 mm along y", (L, W)), ("150 mm along x, 170 mm along y", (W, L))):
        lo = np.array([x_front - sx, -sy / 2, z_bot])
        hi = np.array([x_front, sy / 2, z_bot + H])
        cut = [lo[0] - mc, min(hi[0] + mc, 0.370), lo[1] - mc, hi[1] + mc]
        cand[key] = {"lo": lo.round(4).tolist(), "hi": hi.round(4).tolist(), "lidar_support_mm": round(sdf(lo, hi) * 1000, 1),
                     "cutout_full_mm": [round((sx + 2 * mc) * 1000), round((sy + 2 * mc) * 1000)],
                     "cutout_mm": [round((cut[1] - cut[0]) * 1000), round((cut[3] - cut[2]) * 1000)], "cutout": [round(c, 4) for c in cut]}
    best = max(cand, key=lambda k: (cand[k]["lidar_support_mm"], -cand[k]["cutout_mm"][0] * cand[k]["cutout_mm"][1]))
    c = cand[best]
    lo, hi = np.array(c["lo"]), np.array(c["hi"])
    f.update({"centre": ((lo + hi) / 2).round(4).tolist(), "lo": c["lo"], "hi": c["hi"], "orientation": best,
              "dims_xyz": (hi - lo).round(4).tolist()})
    _TZ = {"orientation": best, "candidates": cand, "lo": lo, "hi": hi, "centre": (lo + hi) / 2, "size": hi - lo, "cutout": c["cutout"],
           "cutout_mm": c["cutout_mm"], "cutout_full_mm": c["cutout_full_mm"], "metal_clear": mc, "electronics_min_z": hi[2] + mc}
    return _TZ
