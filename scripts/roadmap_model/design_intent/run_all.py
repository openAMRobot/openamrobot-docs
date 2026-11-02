# SPDX-License-Identifier: MIT
"""Regenerate every design-intent part (STEP + STL) and docs/assets/roadmap/model/design_intent/index.json.

Each item script is imported, built and exported; every STEP is read back and every solid checked with
BRep validity. Mass: sum over the solids of volume x density (META["materials"] maps a sub-part name
fragment to a material, else META["material"]); solids named *_envelope or *_ref are references and are
not counted. Usage: python3 scripts/roadmap_model/design_intent/run_all.py
"""
import importlib
import json
import os
import sys

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
from _common import DENSITY, OUT, as_list, export  # noqa: E402

ITEMS = ["tof_mount", "ultrasonic_mount", "gemini_mount", "zed_bracket", "getac_pocket", "lift_base_plate",
         "adapter_post", "rear_estop_housing", "motor_bracket", "lift_sensor_set", "battery_tray"]
LETTER = dict(zip(ITEMS, "abcdefghijk"))


def material_of(meta, sub):
    for frag, mat in (meta.get("materials") or {}).items():
        if frag in (sub or ""):
            return mat
    return meta["material"]


def main():
    index = []
    for item in ITEMS:
        mod = importlib.import_module(item)
        meta, parts = mod.META, mod.build()
        files, primary_mass, solids_ok = [], None, True
        for variant, part in parts.items():
            step, stl = export(variant, part)
            back = cq.importers.importStep(step).solids().vals()
            n = len(as_list(part))
            ok = all(s.isValid() for s in back) and len(back) >= n
            solids_ok &= ok
            mass = 0.0
            for sub, wp in as_list(part):
                if sub and (sub.endswith("_envelope") or sub.endswith("_ref")):
                    continue
                vol = sum(s.Volume() for s in wp.solids().vals()) * 1e-9
                mass += vol * DENSITY[material_of(meta, sub)]
            if primary_mass is None:
                primary_mass = mass
            files.append({"variant": variant, "step": os.path.relpath(step, os.path.dirname(OUT)),
                          "stl": os.path.relpath(stl, os.path.dirname(OUT)),
                          "solids": [sub for sub, _ in as_list(part)], "step_bytes": os.path.getsize(step),
                          "stl_bytes": os.path.getsize(stl), "reimport_valid": ok, "mass_kg": round(mass, 3)})
            print("%-32s solids %d valid %s mass %.3f kg  stl %d kB" % (variant, len(back), ok, mass, os.path.getsize(stl) // 1024))
        entry = {"letter": LETTER[item], "item": item, "bom": meta["bom"], "status": "design intent",
                 "existing_cad": meta.get("existing_cad"), "method": meta["method"], "thickness_mm": meta["thickness_mm"],
                 "mass_kg": round(primary_mass, 3), "mass_basis": "per set as exported, volume x density",
                 "placement": meta["placement"], "placement_note": meta.get("placement_note", ""),
                 "configuration": meta["configuration"], "adjustment": meta["adjustment"], "fasteners": meta["fasteners"],
                 "files": files, "source_script": "scripts/roadmap_model/design_intent/%s.py" % item,
                 "next_step": meta["next_step"], "owner": "fridayali"}
        for k in ("mass_note", "existing_cad_note"):
            if meta.get(k):
                entry[k] = meta[k]
        index.append(entry)
    doc = {"schema": 1, "frame": "base_footprint: floor under the drive-axle midpoint, x forward, y left, z up; metres and radians (base_link = +0.098 m z)",
           "snapshot": "2026-11-01", "units_in_scripts": "mm, deg", "items": index}
    with open(os.path.join(OUT, "index.json"), "w") as f:
        json.dump(doc, f, indent=1)
        f.write("\n")
    print("index.json: %d items" % len(index))


if __name__ == "__main__":
    main()
