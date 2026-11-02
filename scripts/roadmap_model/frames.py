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
