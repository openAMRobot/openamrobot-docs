# SPDX-License-Identifier: MIT
"""f. Lift base plate MEC-019 on the centre-frame arch, design intent (owner decision of 2 Nov 2026).

One rectangular 10 mm plate, 6082-T6, on top of the central arch of the centre frame (MMP.04 centre bracket). It
replaces the earlier concept (360 x 230 mm, 4 x M8 through the deck on a 190 x 300 mm pattern).

Arch (CAD MMP.04.00.00.000 Center bracket assembly, openamr-platform-hw main): the 2 mm top sheet (S235JR, EN 1.0114,
BOM_specs_MMP.xlsx) carries 8 x M8 blind rivet nuts (round thin, stainless; mechanical-bom.md and BOM_specs_MMP.xlsx
"Applicability of fasteners": 8 per centre bracket assembly) in 11 mm wide, 18 mm long slots (slot along x), in two
patterns: inner 120 (x) x 100 (y) mm at x +/-0.060, y +/-0.050, and outer 190 (x) x 300 (y) mm at x +/-0.095,
y +/-0.150 (the B7 "190 x 300" pattern, with the 300 across). The plate uses the inner pattern: its width follows it.

The plate is bolted to the arch from above (4 x M8 class 8.8 through the arch top sheet into the backing plate, GI-082
fix, decision D-21). The DOLD Hexalift V4 column (foot 280 x 60.4 x 10 mm, profile 240 x 60 mm) sits forward of the arch
centre on the plate's upper surface. Decision D-20 (8 Nov 2026, approved): the foot is fixed from above through its four
mounting-tab holes (260 x 30 mm, counterbores on the foot top face, seat 4.5 mm) with 4 x DIN 7984 M8 x 14 8.8, no washer,
medium threadlocker, into M8 tapped through this plate (9.5 mm engagement, no inserts). The 224 x 40 mm pattern is
DOLD-internal and is not used by the robot. One tapped hole set for bp000 (column axis x +0.060) and one for bp050
(x +0.110). Plate top at 304 mm.

Plate length 350 mm: the foot ends at x -0.080 (bp000) and x 0.250 (bp050); the plate runs 10 mm past each end
(D-20), so every tab hole keeps 20 mm edge distance. Machining is released only after the DOLD drawing and a dry fit.
Local frame: base_footprint (the plate does not move with bp000 / bp050), metres in META, mm in build().
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

# ---- parameters (mm, base_footprint x / y)
T = 10.0                                  # 6082-T6 plate
ARCH_HOLES_X = (-60.0, 60.0)              # CAD MMP.04.00.00.000 rivet-nut slots (inner pattern)
ARCH_HOLES_Y = (-50.0, 50.0)
ARCH_OUTER = {"x": (-95.0, 95.0), "y": (-150.0, 150.0)}   # outer pattern, not used by this plate
COL_FOOT = (240.0, 60.0)                  # DOLD outer profile 240 x 60 (datums lift_column_section)
COL_AXIS = {"bp000": 60.0, "bp050": 110.0}
COL_SCREWS = (260.0, 30.0)                # DOLD foot tab holes x, y (supplier STEP, D-20); 224 x 40 is DOLD-internal
FOOT = (280.0, 60.4)                      # DOLD foot (supplier STEP)
END_EXT = 10.0                            # D-20: plate 10 mm longer than the foot at each end
TAP_DRILL_M8 = 6.8                        # M8 tapped through
EDGE = 20.0                               # edge distance from hole centre / column footprint
PLATE_TOP_Z = 0.304                       # arch top 294 + plate 10 (B7)
CORNER_R = 6.0

X_REAR = COL_AXIS["bp000"] - FOOT[0] / 2 - END_EXT          # -90
X_FRONT = COL_AXIS["bp050"] + FOOT[0] / 2 + END_EXT          # 260
WIDTH = (ARCH_HOLES_Y[1] - ARCH_HOLES_Y[0]) + 2 * EDGE       # 140
LENGTH = X_FRONT - X_REAR                                    # 350
X_CENTRE = (X_FRONT + X_REAR) / 2                            # 85

META = {
    "item": "lift_base_plate", "bom": "MEC-019", "method": "machined 6082-T6", "material": "6082-T6", "thickness_mm": T,
    "existing_cad": None,
    "configuration": "one plate for bp000 and bp050 (two column hole sets)",
    "adjustment": "two column hole sets (bp000, bp050); arch slots 18 mm long give +/-3.5 mm fore-aft",
    "placement": [{"name": "plate_top_in_base_footprint", "xyz": [0.0, 0.0, PLATE_TOP_Z], "rpy": [0, 0, 0]}],
    "placement_note": "plate x %.3f to %.3f, y +/-%.3f, z 0.294 to 0.304; arch bolts x +/-0.060, y +/-0.050; column tab holes (M8 tapped) bp000 x -0.070 / 0.190, bp050 x -0.020 / 0.240, y +/-0.015" % (
        X_REAR / 1000, X_FRONT / 1000, WIDTH / 2000),
    "parameters": {"length_mm": LENGTH, "width_mm": WIDTH, "thickness_mm": T, "x_rear_m": X_REAR / 1000, "x_front_m": X_FRONT / 1000,
                   "arch_holes_x_m": [x / 1000 for x in ARCH_HOLES_X], "arch_holes_y_m": [y / 1000 for y in ARCH_HOLES_Y],
                   "column_axis_x_m": {k: v / 1000 for k, v in COL_AXIS.items()}, "column_screws_mm": list(COL_SCREWS), "edge_mm": EDGE},
    "fasteners": [
        {"joint": "DOLD column foot to the lift base plate (from above through the foot tab holes into M8 tapped through MEC-019; no washer, medium threadlocker; D-20)", "part": "DIN 7984 low head socket cap screw, class 8.8", "size": "M8 x 14", "qty": 4, "standard": "DIN 7984", "class": "named"},
        {"joint": "lift base plate to the centre-frame arch (from above, through the arch top sheet into the backing plate; D-21)", "part": "ISO 4762 socket head cap screw class 8.8 + ISO 7089 washer", "size": "M8 x 25", "qty": 4, "standard": "ISO 4762 / ISO 7089", "class": "proposed"},
    ],
    "next_step": "CAD owner (mechanical owner): model the 350 x 140 mm plate with both tapped tab-hole sets (260 x 30 mm) and the two lift cable openings; machining only after the DOLD drawing and a dry fit (D-20).",
}


def build():
    p = (cq.Workplane("XY").box(LENGTH, WIDTH, T).edges("|Z").fillet(CORNER_R)
         .translate((X_CENTRE, 0, -T / 2)))
    # arch bolts: clearance holes plus a 13.5 mm counterbore 0.5 mm deep for the washer seat
    for x in ARCH_HOLES_X:
        for y in ARCH_HOLES_Y:
            p = p.cut(cq.Workplane("XY").center(x, y).circle(CLEAR["M8"] / 2).extrude(30, both=True))
    # column foot tab holes, both hole sets (D-20): M8 tapped through (drawn at the tap drill), screws from above
    for bp, ax in COL_AXIS.items():
        for sx in (-1, 1):
            for sy in (-1, 1):
                cx, cy = ax + sx * COL_SCREWS[0] / 2, sy * COL_SCREWS[1] / 2
                p = p.cut(cq.Workplane("XY").center(cx, cy).circle(TAP_DRILL_M8 / 2).extrude(30, both=True))
    # column foot marking (0.3 mm locating recess) at bp000 and bp050
    for ax in COL_AXIS.values():
        p = p.cut(cq.Workplane("XY").box(FOOT[0] + 0.4, FOOT[1] + 0.4, 0.3).translate((ax, 0, -0.15)))
    return {"lift_base_plate": [("MEC-019_lift_base_plate", p)]}


if __name__ == "__main__":
    run_single(META, build)
