# SPDX-License-Identifier: MIT
"""h. Second E-stop housing (SAF-001, second unit), design intent, one position (owner correction A5, owner, 2 Nov 2026;
to be entered in P-03 and M-01).

On top of the adapter plate MEC-004 (the moving plate on the lift carriage that carries the post and the arms), centred
in y, in the free part of the plate behind the post, above the column axis; button facing up. The housing stands on
the plate so the ZBE-102 contact blocks sit inside it, above the plate. The cable leaves through an M16 gland in the
housing side into a hole in the plate and runs with the arm cables through the lift cable chain (service loop).
Schneider XB4BS8445 (40 mm mushroom, turn to release) + ZBE-102 contact blocks (2NC + 1NO) in a 22.5 mm hole.
Manufacturing: laser-cut and bent 5754-H22 aluminium, 2.0 mm sheet, bend radius 2 mm.
Local frame: origin on the mounting face (the adapter plate top) at the button axis, x out of the face (up after the
pitch of -pi/2), z along the robot x.
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
STATIC_TOP_Z_UNUSED = 0.816         # static profile top: column top 0.834 minus 0.018 (datums.yaml lift_static_profile_top_below_column_top)
COL_REAR_X = 0.060 - 0.120   # column rear face at bp000
POST_REAR_X = 0.060 + 0.180 - 0.060   # arm-post rear face at bp000 (post centre 180 mm ahead of the column axis, 120 deep)
POST_TOP_Z = 1.184           # post top at L1000: 0.304 + 0.530 + 0.010 + 0.340
FOOT_T = 6.0                 # ZED bracket foot (zed_bracket.py)
ADAPTER_TOP_Z = 0.844        # adapter plate top at L1000: 0.304 + 0.530 + 0.010
COL_AXIS_X = 0.060           # column axis at bp000; the post spans x 0.180 to 0.300, so the plate is free from -0.060 to 0.180
POS = {"adapter_top": ([COL_AXIS_X, 0.0, ADAPTER_TOP_Z], [0, -math.pi / 2, 0], "mov")}
VARIANT = {"adapter_top": "rear_estop_housing"}
ACTUATOR_Z = {k: round(ADAPTER_TOP_Z + DEPTH / 1000 + HEAD[0] / 2000 + tr, 4) for k, tr in (("L1000", 0.0), ("L1175", 0.175), ("L1350", 0.350))}

META = {
    "materials": {"rear_housing": "5754-H22"},
    "item": "rear_estop_housing", "bom": "SAF-001 (second unit), housing to MEC-014/MEC-013", "method": "laser-cut and bent 5754 aluminium sheet",
    "material": "5754-H22", "thickness_mm": SHEET,
    "existing_cad": None,
    "configuration": "one position (A5): adapter plate top behind the post, centred in y, above the column, button up; moves with the lift",
    "adjustment": "fore-aft on the plate between the column axis and the rear upright (slotted flange holes, +/-10 mm)",
    "actuator_height_m": ACTUATOR_Z,
    "placement": [{"name": k, "xyz": v[0], "rpy": v[1], "group": v[2], "variant": VARIANT[k]} for k, v in POS.items()],
    "placement_note": "xyz at bp000 and L1000, on the adapter plate top; moves with the lift (+0.175 / +0.350); pitch -pi/2: button up",
    "fasteners": [
        {"joint": "housing flanges to the adapter plate", "part": "ISO 4762 screw + ISO 7089 washer into tapped holes", "size": "M6 x 10", "qty": 4, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "E-stop in housing", "part": "XB4 mounting nut (supplied)", "size": "22.5 mm", "qty": 1, "standard": "Schneider XB4", "class": "named"},
        {"joint": "cable exit", "part": "cable gland IP67", "size": "M16 x 1.5", "qty": 1, "standard": "EN 62444", "class": "proposed"},
    ],
    "next_step": "Owner: enter the adapter-plate position in P-03 and M-01; CAD owner: tapped holes and the cable hole in MEC-004 (M-09).",
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
    return {"rear_estop_housing": [("SAF-001_housing_adapter_top", housing()), ("SAF-001_XB4BS8445_ZBE-102_envelope", button())]}


if __name__ == "__main__":
    run_single(META, build)
