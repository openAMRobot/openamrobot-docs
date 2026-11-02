# SPDX-License-Identifier: MIT
"""h. Second E-stop housing on the rear face of the static DOLD column (SAF-001, second unit), design intent.

Schneider XB4BS8445 (40 mm mushroom, turn to release) + ZBE-102 contact blocks (2NC + 1NO) in a 22.5 mm
hole. Folded aluminium box, open toward the column, bolted to the column rear face with two M6 T-nuts in the
DOLD rear T-slot; the cable leaves through an M16 gland at the bottom and runs down the column to the base.
Two positions are exported: the decided placeholder (button axis 40 mm below the static profile top) and the
clear position found in simulation (180 mm below the top edge, P-03 simulation finding of 29 Oct) as a ghost.
Manufacturing: laser-cut and bent 5754-H22 aluminium, 2.0 mm sheet, bend radius 2 mm.
Local frame: origin on the column rear face at the button axis, x rearward (out of the face), z up.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

SHEET = 2.0
DEPTH = 48.0                 # panel face behind the profile rear face (datums.yaml second_estop_panel_behind_profile)
BOX_Y, BOX_Z = 50.0, 72.0    # outside width and height; contact block 30 x 47 (datums.yaml second_estop_contact_block_size) plus clearance
HOLE = 22.5                  # XB4 mounting hole (B4)
HEAD = (14.0, 40.0)          # mushroom head depth, diameter (datums.yaml second_estop_head_size)
COLLAR = 22.0
BLOCK = (46.0, 30.0, 47.0)   # contact block depth x width x height
GLAND = 16.5                 # M16 cable gland hole, bottom face
STATIC_TOP_Z = 0.816         # static profile top: column top 0.834 minus 0.018 (datums.yaml lift_static_profile_top_below_column_top)
COL_REAR_X = 0.060 - 0.120   # column rear face at bp000
BELOW_TOP = {"placeholder": 0.040, "clear_ghost": 0.180}

META = {
    "materials": {"rear_housing": "5754-H22"},
    "item": "rear_estop_housing", "bom": "SAF-001 (second unit), housing to MEC-014/MEC-013", "method": "laser-cut and bent 5754 aluminium sheet",
    "material": "5754-H22", "thickness_mm": SHEET,
    "existing_cad": None,
    "configuration": "static column, independent of lift position; bp000",
    "adjustment": "height along the DOLD rear T-slot (placeholder 40 mm below the top; clear position 180 mm below)",
    "placement": [{"name": "placeholder", "xyz": [COL_REAR_X, 0.0, STATIC_TOP_Z - BELOW_TOP["placeholder"]], "rpy": [0, 0, math.pi]},
                  {"name": "clear_ghost", "xyz": [COL_REAR_X, 0.0, STATIC_TOP_Z - BELOW_TOP["clear_ghost"]], "rpy": [0, 0, math.pi]}],
    "placement_note": "rpy yaw pi: local +x (out of the face) points to robot -x (rearward); button face 48 mm behind the column rear face",
    "fasteners": [
        {"joint": "housing to DOLD rear slot", "part": "ISO 4762 screw + ISO 7089 washer + T-slot nut (DOLD slot size to confirm)", "size": "M6 x 10", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "E-stop in housing", "part": "XB4 mounting nut (supplied)", "size": "22.5 mm", "qty": 1, "standard": "Schneider XB4", "class": "named"},
        {"joint": "cable exit", "part": "cable gland IP67", "size": "M16 x 1.5", "qty": 1, "standard": "EN 62444", "class": "proposed"},
    ],
    "next_step": "Decide the height (placeholder 40 mm vs 180 mm clear of the right gripper), confirm the DOLD T-slot nut, M-09.",
}


def housing():
    d, w, h, t = DEPTH, BOX_Y, BOX_Z, SHEET
    outer = cq.Workplane("XY").box(d, w, h).translate((d / 2, 0, 0))
    inner = cq.Workplane("XY").box(d, w - 2 * t, h - 2 * t).translate((d / 2 - t, 0, 0))
    b = outer.cut(inner)
    # top and bottom flanges on the column face (the column is only 60 mm wide, so no side flanges), 14 mm
    for s in (-1, 1):
        b = b.union(cq.Workplane("XY").box(t, w, 14.0).translate((t / 2, 0, s * (h / 2 + 7.0))))
        b = b.cut(cq.Workplane("YZ").center(0, s * (h / 2 + 7.0)).circle(CLEAR["M6"] / 2).extrude(10, both=True))
    b = b.cut(cq.Workplane("YZ").circle(HOLE / 2).extrude(d + 5))           # button hole in the rear face
    b = b.cut(cq.Workplane("XY").center(d / 2 + 4, 0).circle(GLAND / 2).extrude(-h))  # gland in the bottom
    return b


def button():
    hd, hdia = HEAD
    head = cq.Workplane("YZ").circle(hdia / 2).extrude(hd).translate((DEPTH + 2.0, 0, 0))
    collar = cq.Workplane("YZ").circle(COLLAR / 2).extrude(2.0 + SHEET).translate((DEPTH - SHEET, 0, 0))
    block = cq.Workplane("XY").box(*BLOCK).translate((DEPTH - SHEET - BLOCK[0] / 2, 0, 0))
    return head.union(collar).union(block)


def build():
    out = {}
    for name in ("placeholder", "clear_ghost"):
        key = "rear_estop_housing" if name == "placeholder" else "rear_estop_housing_clear_ghost"
        out[key] = [("SAF-001_rear_housing_%s" % name, housing()), ("SAF-001_XB4BS8445_ZBE-102_envelope", button())]
    return out


if __name__ == "__main__":
    run_single(META, build)
