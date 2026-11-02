# SPDX-License-Identifier: MIT
"""Shared helpers for the OpenAMRobot 2.0 design-intent parts (roadmap model, section D).

Every item script defines META (dict) and build() -> {variant: cadquery.Workplane}; the first
variant is the primary part. Units inside the scripts: millimetres and degrees. Placements in
META are metres and radians in base_footprint (floor under the drive-axle midpoint, x forward,
y left, z up; base_link = base_footprint + 0.098 m in z).

Run one item:  python3 scripts/roadmap_model/design_intent/<item>.py
Run all:       python3 scripts/roadmap_model/design_intent/run_all.py
"""
import os

import cadquery as cq

HERE = os.path.dirname(os.path.abspath(__file__))
REPO = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
OUT = os.path.join(REPO, "docs", "assets", "roadmap", "model", "design_intent")

# density, kg/m3
DENSITY = {"PETG": 1270.0, "6082-T6": 2700.0, "5754-H22": 2660.0, "S355": 7850.0, "SS400": 7850.0,
           "6063-T5": 2700.0, "steel": 7850.0}

# Common standard hole sizes, mm (ISO 273 medium series clearance; heat-set insert bores per insert makers' typical values)
CLEAR = {"M2": 2.4, "M2.5": 2.9, "M3": 3.4, "M4": 4.5, "M5": 5.5, "M6": 6.6, "M8": 9.0, "M12": 13.5}
INSERT_BORE = {"M3": 4.0, "M4": 5.6}            # PETG heat-set inserts, hole before pressing (check against the insert used)
CSK_DIA = {"M8": 16.4}                           # 90 deg countersink head diameter (DIN 7500 / ISO 10642 M8)


def as_list(part):
    """A variant is one Workplane or a list of (sub-part name, Workplane): one named solid per sub-part."""
    return part if isinstance(part, list) else [(None, part)]


def compound(part):
    return cq.Compound.makeCompound([s for _, wp in as_list(part) for s in wp.solids().vals()])


def export(name, part, tol=0.25, ang=0.4):
    """Write <name>.step (one named solid per sub-part) and <name>.stl to OUT; return (step path, stl path)."""
    os.makedirs(OUT, exist_ok=True)
    step = os.path.join(OUT, name + ".step")
    stl = os.path.join(OUT, name + ".stl")
    items = as_list(part)
    if len(items) == 1 and items[0][0] is None:
        cq.exporters.export(items[0][1], step)
    else:
        assy = cq.Assembly(name=name)
        for i, (sub, wp) in enumerate(items):
            assy.add(wp, name=sub or "%s_%d" % (name, i))
        assy.export(step) if hasattr(assy, "export") else assy.save(step)
    cq.exporters.export(cq.Workplane().add(compound(part)), stl, tolerance=tol, angularTolerance=ang)
    return step, stl


def volume_mm3(part):
    return sum(s.Volume() for _, wp in as_list(part) for s in wp.solids().vals())


def run_single(meta, build):
    parts = build()
    for name, wp in parts.items():
        export(name, wp)
        print(name, "volume %.1f cm3" % (volume_mm3(wp) / 1000.0))
