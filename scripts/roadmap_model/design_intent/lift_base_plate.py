# SPDX-License-Identifier: MIT
"""f. Lift-to-base interface plate MEC-019, design intent.

6082-T6, 360 x 230 x 10 mm, machined. The plate carries the DOLD Hexalift V4 column (4 x M8 DIN 7500
self-forming screws, countersunk from below, at least 20 mm engagement in the column) and is bolted to the
deck with 4 x M8 class 8.8 through-bolts on a 190 x 300 mm pattern, through the deck into the frame below.
The plate is NOT tapped. bp000 and bp050: the plate moves with the column (column axis x 0.060 or 0.110),
so the deck carries both 4-hole patterns, 50 mm apart; the plate itself has one pattern.
Orientation proposed here: 300 along x (fore-aft), 190 along y; B7 gives the pattern size, not its
orientation. The DOLD column-screw pattern is a placeholder until the DOLD STEP / drawing is read.
Local frame: origin at the plate top on the column axis, x forward, z up.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, CSK_DIA, run_single  # noqa: E402

PLATE = (360.0, 230.0, 10.0)        # B7 MEC-019
DECK_PATTERN = (300.0, 190.0)       # x, y (orientation proposed)
COL_PATTERN = (190.0, 30.0)         # DOLD column-screw pattern x, y: PLACEHOLDER (DOLD drawing not read)
COL_FOOT = (240.0, 60.0)            # DOLD column section (datums.yaml lift_column_section)
CORNER_R = 8.0
BP = {"bp000": 0.060, "bp050": 0.110}   # column axis x in base_footprint (P-03 / B7)
PLATE_TOP_Z = 0.304                 # deck 294 + plate 10 (B7)

META = {
    "item": "lift_base_plate", "bom": "MEC-019", "method": "machined 6082-T6", "material": "6082-T6", "thickness_mm": PLATE[2],
    "existing_cad": None,
    "configuration": "bp000 (bp050: same part, 50 mm forward)",
    "adjustment": "two deck hole patterns (bp000, bp050); no slots",
    "placement": [{"name": "bp000", "xyz": [BP["bp000"], 0.0, PLATE_TOP_Z], "rpy": [0, 0, 0]},
                  {"name": "bp050 (alternative)", "xyz": [BP["bp050"], 0.0, PLATE_TOP_Z], "rpy": [0, 0, 0]}],
    "placement_note": "deck bolt positions in base_footprint: bp000 x -0.090 / +0.210, bp050 x -0.040 / +0.260, y +/-0.095",
    "fasteners": [
        {"joint": "column to plate", "part": "DIN 7500 thread-forming countersunk screw (from below, >= 20 mm engagement)", "size": "M8 x 30", "qty": 4, "standard": "DIN 7500", "class": "named"},
        {"joint": "plate to deck and frame", "part": "ISO 4017 hex screw class 8.8 + 2 x ISO 7089 washer + ISO 7040 nyloc nut", "size": "M8 x 40", "qty": 4, "standard": "ISO 4017", "class": "named"},
    ],
    "next_step": "CAD owner: read the DOLD column-screw pattern, confirm the 190 x 300 orientation, and give the front bolt row a load path (see geometry note).",
}


def build():
    lx, ly, t = PLATE
    p = cq.Workplane("XY").box(lx, ly, t).edges("|Z").fillet(CORNER_R).translate((0, 0, -t / 2))
    for sx in (-1, 1):
        for sy in (-1, 1):
            p = p.cut(cq.Workplane("XY").center(sx * DECK_PATTERN[0] / 2, sy * DECK_PATTERN[1] / 2).circle(CLEAR["M8"] / 2).extrude(30, both=True))
            # column screws: clearance hole plus a 90 deg countersink from below
            p = p.cut(cq.Workplane("XY").center(sx * COL_PATTERN[0] / 2, sy * COL_PATTERN[1] / 2).circle(CLEAR["M8"] / 2).extrude(30, both=True))
            cone = cq.Solid.makeCone(CSK_DIA["M8"] / 2, CLEAR["M8"] / 2, (CSK_DIA["M8"] - CLEAR["M8"]) / 2,
                                     cq.Vector(sx * COL_PATTERN[0] / 2, sy * COL_PATTERN[1] / 2, -t - 0.01), cq.Vector(0, 0, 1))
            p = p.cut(cq.Workplane().add(cone))
    # column footprint marking: 0.3 mm deep locating recess on the top face
    p = p.cut(cq.Workplane("XY").box(COL_FOOT[0] + 0.4, COL_FOOT[1] + 0.4, 0.3).translate((0, 0, -0.15)))
    return {"lift_base_plate": [("MEC-019_lift_base_plate", p)]}


if __name__ == "__main__":
    run_single(META, build)
