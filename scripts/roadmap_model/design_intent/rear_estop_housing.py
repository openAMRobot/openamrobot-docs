# SPDX-License-Identifier: MIT
"""h. Second E-stop housing (SAF-001, second unit), design intent, four candidate positions (owner request of 2 Nov 2026).

Reach requirement (owner, 2 Nov 2026): a standing adult close to the robot presses it by hand without bending or
sitting down. Criterion: actuator centre 0.90 to 1.50 m above the floor at L1000, L1175 and L1350, facing outward
and visible, no contact in the arm sweep, not in the ZED Mini view, cable routed.
  P1 rear face of the static column, 40 mm below the static profile top (the current datum; right gripper contact
     in the 29 Oct simulation), fixed height 0.776 m;
  P2 rear face of the vertical arm post (MISUMI HFS6-60120, moves with the lift), centre 55 mm below the post top,
     facing rearward, on two M6 T-nuts per flange in the post rear slots; above the 150 mm rear upright and the
     stiffener, below the ZED bracket foot; 1.129 / 1.304 / 1.479 m (recommended, proposed);
  P3 post top beside the ZED pitch bracket, button up: the bracket foot covers the whole 120 x 60 mm post top, so
     the housing can only sit on the foot; 1.245 / 1.420 / 1.595 m (over 1.50 at L1350);
  P4 static column rear face at the highest arm-clear position (280 mm below the static profile top, random-pose
     reach study), fixed height 0.536 m (fixed-height reference).
Schneider XB4BS8445 (40 mm mushroom, turn to release) + ZBE-102 contact blocks (2NC + 1NO) in a 22.5 mm hole.
Folded aluminium box open toward the mounting face, M16 gland in the bottom face; P2 and P3 cables run with the arm
cables through the lift cable chain (service loop), P1 and P4 down the static column.
Manufacturing: laser-cut and bent 5754-H22 aluminium, 2.0 mm sheet, bend radius 2 mm.
Local frame: origin on the mounting face at the button axis, x out of the face (toward the operator), z up.
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
POST_REAR_X = 0.060 + 0.180 - 0.060   # arm-post rear face at bp000 (post centre 180 mm ahead of the column axis, 120 deep)
POST_TOP_Z = 1.184           # post top at L1000: 0.304 + 0.530 + 0.010 + 0.340
FOOT_T = 6.0                 # ZED bracket foot (zed_bracket.py)
POS = {  # name: (xyz at bp000 and L1000, rpy, group, actuator-centre offset from the floor at L1000 [m], moves with the lift)
    "P1": ([COL_REAR_X, 0.0, STATIC_TOP_Z - 0.040], [0, 0, math.pi], "col"),
    "P2": ([POST_REAR_X, 0.0, POST_TOP_Z - 0.055], [0, 0, math.pi], "mov"),
    "P3": ([POST_REAR_X + 0.020, 0.0, POST_TOP_Z + FOOT_T / 1000], [0, -math.pi / 2, 0], "mov"),
    "P4": ([COL_REAR_X, 0.0, STATIC_TOP_Z - 0.280], [0, 0, math.pi], "col"),
}
VARIANT = {"P2": "rear_estop_housing", "P1": "rear_estop_housing_p1_ghost", "P3": "rear_estop_housing_p3_ghost", "P4": "rear_estop_housing_p4_ghost"}

META = {
    "materials": {"rear_housing": "5754-H22"},
    "item": "rear_estop_housing", "bom": "SAF-001 (second unit), housing to MEC-014/MEC-013", "method": "laser-cut and bent 5754 aluminium sheet",
    "material": "5754-H22", "thickness_mm": SHEET,
    "existing_cad": None,
    "configuration": "P2 (recommended, proposed): arm-post rear face, moves with the lift; P1, P3, P4 exported as labelled ghosts",
    "adjustment": "height along the HFS6 rear slots (40 to 60 mm below the post top)",
    "placement": [{"name": k, "xyz": v[0], "rpy": v[1], "group": v[2], "variant": VARIANT[k]} for k, v in POS.items()],
    "placement_note": "xyz at bp000 and L1000; P2 and P3 move with the lift (+0.175 / +0.350); yaw pi: local +x points rearward; P3 pitch -pi/2: button up",
    "variants_note": {k: VARIANT[k] for k in POS},
    "fasteners": [
        {"joint": "P2 housing to the HFS6 post rear slots", "part": "ISO 4762 screw + ISO 7089 washer + M6 T-slot nut (HFS6)", "size": "M6 x 10", "qty": 4, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "E-stop in housing", "part": "XB4 mounting nut (supplied)", "size": "22.5 mm", "qty": 1, "standard": "Schneider XB4", "class": "named"},
        {"joint": "cable exit", "part": "cable gland IP67", "size": "M16 x 1.5", "qty": 1, "standard": "EN 62444", "class": "proposed"},
    ],
    "next_step": "Owner: take P2 into P-03 (datums second_estop_below_profile_top and its parent link change then), CAD (M-09).",
}


def housing():
    d, w, h, t = DEPTH, BOX_Y, BOX_Z, SHEET
    outer = cq.Workplane("XY").box(d, w, h).translate((d / 2, 0, 0))
    inner = cq.Workplane("XY").box(d, w - 2 * t, h - 2 * t).translate((d / 2 - t, 0, 0))
    b = outer.cut(inner)
    # top and bottom flanges on the mounting face (column and post are 60 mm wide, so no side flanges), 14 mm,
    # two M6 holes each at the 30 mm slot pitch (HFS6 rear slots y +/-15; DOLD rear slot: the centre hole pair fits)
    for s in (-1, 1):
        b = b.union(cq.Workplane("XY").box(t, w, 14.0).translate((t / 2, 0, s * (h / 2 + 7.0))))
        for y in (-15.0, 15.0):
            b = b.cut(cq.Workplane("YZ").center(y, s * (h / 2 + 7.0)).circle(CLEAR["M6"] / 2).extrude(10, both=True))
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
    for name, key in VARIANT.items():
        out[key] = [("SAF-001_rear_housing_%s" % name, housing()), ("SAF-001_XB4BS8445_ZBE-102_envelope", button())]
    return {k: out[k] for k in ("rear_estop_housing", "rear_estop_housing_p1_ghost", "rear_estop_housing_p3_ghost", "rear_estop_housing_p4_ghost")}


if __name__ == "__main__":
    run_single(META, build)
