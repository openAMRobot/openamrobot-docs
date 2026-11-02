"""Frames and source readers shared by the roadmap model scripts.

One conversion helper (bl_to_bf) is used everywhere: base_link (platform-sw sensor_frames.yaml, the base GLB)
to base_footprint (the roadmap model root, floor under the drive-axle midpoint, x forward, y left, z up; REP 103/105).
The three.js scene uses the same axes (model.js root group, camera.up = +z), so no other mapping is needed.
"""
import base64
import json
import math
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
    """TZBOT WCM-500-24 receiver box (base_footprint, m), owner correction A1 (2 Nov 2026): reserved, not installed in 2.0, in the
    middle of the rear section, centred in the charger zone (rear_layout.layout()), 170 mm across (y) x 150 mm along (x), bottom
    2 mm below the base-sheet underside. Also writes tzbot_receiver.centre / lo / hi / orientation into FACTS."""
    global _TZ
    if _TZ is not None:
        return _TZ
    import rear_layout
    L = rear_layout.layout()
    f = FACTS["tzbot_receiver"]
    lo, hi = np.array(L["receiver"][0]), np.array(L["receiver"][1])
    mc = f["metal_clear"]
    cut = L["cutout"]
    f.update({"centre": ((lo + hi) / 2).round(4).tolist(), "lo": lo.tolist(), "hi": hi.tolist(),
              "orientation": "150 mm along x, 170 mm across y (rear charger zone)", "dims_xyz": (hi - lo).round(4).tolist()})
    _TZ = {"orientation": f["orientation"], "lo": lo, "hi": hi, "centre": (lo + hi) / 2, "size": hi - lo,
           "cutout": [cut[0][0], cut[1][0], cut[0][1], cut[1][1]],
           "cutout_mm": [round((cut[1][0] - cut[0][0]) * 1000), round((cut[1][1] - cut[0][1]) * 1000)],
           "cutout_full_mm": [round((cut[1][0] - cut[0][0]) * 1000), round((cut[1][1] - cut[0][1]) * 1000)],
           "metal_clear": mc, "electronics_min_z": hi[2] + mc, "location": "rear"}
    return _TZ


def lift_rear_layout():
    """A6 (2 Nov 2026): lift stop sensors on the rear face of the static column, centred in y, sensor axes along y (SICK
    BEF-WN-M12 angle bracket: one leg on the rear face, the sensor through the other leg, parallel to the face), sensing faces
    toward +y. Flag 2 mm off the faces, rod 9 mm clear of the face discs, rod bolted to the underside of the adapter-plate
    extension (M5 into the tapped rod end) with the corner bracket on the column side of the rod. The plate rear edge is the
    rod's rear face or its M5 edge distance, whichever reaches further back. Column frame, metres."""
    f = FACTS["lift_rear"]
    s, b, r = f["sensor"], f["bracket"], f["rod"]
    ax_x = f["column_rear_x"] - b["axis_from_face"]          # sensor axis x
    face_y = s["len"] / 2                                     # sensor centred in y, sensing face toward +y
    flag_y = [face_y + f["gap"], face_y + f["gap"] + f["flag"][1]]
    rod_x1 = ax_x - s["d"] / 2 - f["rod_clear"]               # rod face toward the column
    rod_x = [rod_x1 - r["w"], rod_x1]
    rod_y = [flag_y[1], flag_y[1] + r["w"]]                   # flag bolted to the rod side face facing the sensors
    flag_x = [rod_x[0], rod_x[0] + f["flag"][0]]
    corner_x = [rod_x[1], rod_x[1] + f["corner"]["leg"]]      # corner bracket on the column side of the rod
    rod_c = [(rod_x[0] + rod_x[1]) / 2, (rod_y[0] + rod_y[1]) / 2]
    rear = min(rod_x[0], rod_c[0] - f["bolt_edge"])
    rear = math.floor(rear * 200 + 1e-9) / 200.0             # 5 mm drawing grid, never shorter than the geometry needs
    p = f["plate"]
    half_w = p["width"] / 2
    return {"sensor_axis_x": round(ax_x, 4), "sensor_y": [round(-face_y, 4), round(face_y, 4)], "face_y": round(face_y, 4),
            "flag_x": [round(v, 4) for v in flag_x], "flag_y": [round(v, 4) for v in flag_y], "rod_x": [round(v, 4) for v in rod_x],
            "rod_y": [round(v, 4) for v in rod_y], "corner_x": [round(v, 4) for v in corner_x], "rod_centre": [round(v, 4) for v in rod_c],
            "plate_rear_x": round(rear, 4), "plate_front_x": p["front_x"], "plate_len": round(p["front_x"] - rear, 4), "plate_width": p["width"],
            "plate_t": p["t"], "extension": round(f["column_rear_x"] - rear, 4), "rod_inside_plate": rod_y[1] <= half_w + 1e-9 and rod_x[0] >= rear - 1e-9,
            "rod_clear_mm": round(math.hypot(rod_x1 - (ax_x - s["d"] / 2), rod_y[0] - face_y) * 1000, 1)}
