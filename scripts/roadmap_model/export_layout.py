#!/usr/bin/env python3
"""Export one positioned layout STEP of the whole robot for the CAD owner (SolidWorks):
docs/assets/roadmap/model/export/openamrobot2_layout.step, base_footprint coordinates (metres in the scene,
millimetres in the STEP), lift L1000, bp000, hp30, arms in the page pose.
Contents: the design-intent parts (their own solids, placed) plus one box envelope per other drawn part
(world bounding box), one solid per part, named <BOM id>__<part id>. No meshes.
Usage: python3 scripts/roadmap_model/export_layout.py
"""
import json
import math
import os
import re

import cadquery as cq
import numpy as np

import analyse as A
from frames import MODEL, glb_nodes

OUT = os.path.join(MODEL, "export", "openamrobot2_layout.step")


def main():
    G = glb_nodes()
    P = json.load(open(os.path.join(MODEL, "placement.json")))
    chest, lift, reg = A.model_js()
    scene = A.build_scene(G, P, chest, lift)
    cfg = {"bp": "bp000", "travel": 0.0}
    bom = {}
    for c in reg + P["components"]:
        for p in c.get("nodes", []) + c.get("parts", []):
            bom[p] = (c.get("bom") or "NOBOM").split(",")[0].split(" ")[0].strip() or "NOBOM"
    alias = {"lift_column_stage": "MEC-018", "lift_column_head": "MEC-018", "second_estop": "SAF-001", "getac_tablet": "UI-001", "head_light": "AUX-001",
             "flag_rod": "LFT-004", "lift_flag": "LFT-006"}
    di = json.load(open(os.path.join(MODEL, "design_intent", "index.json")))
    di = di if isinstance(di, list) else di["items"]
    di_parts = {"motor_brackets", "battery_tray", "rear_estop_housing", "getac_pocket", "rear_estop_clear_ghost", "getac_second_position_ghost"}
    asm = cq.Assembly(name="OpenAMRobot2_layout_base_footprint")
    n = 0
    for p in scene:
        if p.id in di_parts or p.id.startswith(("motor_brackets", "keepout", "harness", "service_loop", "fasteners", "k1k2_option")):
            continue
        v = p.world(cfg) * 1000
        lo, hi = v.min(0), v.max(0)
        s = np.maximum(hi - lo, .5)
        b = cq.Workplane("XY").box(*s).translate(tuple((lo + hi) / 2))
        name = "%s__%s" % (alias.get(p.id, bom.get(p.id, bom.get(re.sub(r"_\d+$", "", p.id), "NOBOM"))), p.id)
        asm.add(b, name=name)
        n += 1
    # arms: one box per link (page pose)
    for side in ("left", "right"):
        q = [.25, -.12, 0, 1.9, 0, -.78, 0]  # M.ARM_POSE of model.js; the right arm mirrors the left
        if side == "right":
            q = [-q[0], -q[1], -q[2], q[3], -q[4], -q[5], -q[6]]
        parts, _ = A.arm_parts(side, q, .6, 1.0, .06)
        for lp in parts:
            v = lp.v0 * 1000
            lo, hi = v.min(0), v.max(0)
            asm.add(cq.Workplane("XY").box(*np.maximum(hi - lo, .5)).translate(tuple((lo + hi) / 2)), name="ARM-001__%s" % lp.id)
            n += 1
    # design-intent solids, placed
    for d in di:
        item = d["item"]
        pls = d["placement"] if isinstance(d["placement"], list) else [d["placement"]]
        for f in d["files"][:1] if item not in ("rear_estop_housing", "getac_pocket") else d["files"]:
            stp = os.path.join(MODEL, f["step"] if f["step"].startswith("design_intent") else "design_intent/" + f["step"])
            shp = cq.importers.importStep(stp)
            use = pls
            if item == "rear_estop_housing":
                use = [pls[1] if "ghost" in f["variant"] else pls[0]]
            if item in ("getac_pocket", "lift_base_plate"):
                use = pls[:1]
            for i, pl in enumerate(use):
                s2 = shp
                rx, ry, rz = [math.degrees(a) for a in pl["rpy"]]
                s2 = s2.rotate((0, 0, 0), (1, 0, 0), rx).rotate((0, 0, 0), (0, 1, 0), ry).rotate((0, 0, 0), (0, 0, 1), rz)
                s2 = s2.translate(tuple(np.array(pl["xyz"]) * 1000))
                asm.add(s2, name="%s__design_intent_%s_%s" % (d["bom"].split(",")[0].strip(), f["variant"], pl.get("name", i)))
                n += 1
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    asm.save(OUT, exportType="STEP")
    print("solids", n, "->", OUT, os.path.getsize(OUT))


if __name__ == "__main__":
    main()
