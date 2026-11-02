# SPDX-License-Identifier: MIT
"""k. Battery tray MEC-007 with restraint and detachable end panels, design intent only.

Holds the provisional cell-group envelope 314 (y) x 140 (x) x 210 (z) mm (8 x EVE LF105 upright in one row
across the robot plus 5 mm per outer face, B-02 rev18.10 / P-03 item 9). Tray: floor and front/rear walls
folded from one 2.5 mm 5754 aluminium sheet; two detachable end panels (y ends, 5 mm 6082-T6) that also
compress the cell stack through two M6 tie rods along y behind the cells and, in front, through the front
wall bolted to both end panels (nothing on top of the cells, B5). The envelope front face is only 2 mm behind
the centre bracket, so the front wall has no outward flange and the tray sits 1 mm behind the bracket
(envelope 1.5 mm further rearward than the GLB node). Lift-out handle: the folded top flange of the rear wall. The tray bolts to
the deck with 4 x M6. Height check: deck 54 mm (sheet top) + floor 2.5 + 210 = 266.5 mm, cover underside
290 mm (deck to cover underside 236 mm): 23.5 mm free above the envelope (26 mm without the tray floor).
Local frame: origin at the envelope bottom centre (on the tray floor), x forward, z up.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

ENV = (140.0, 314.0, 210.0)      # x, y, z (provisional)
SHEET = 2.5
WALL_H = 120.0                   # front/rear walls (restraint height, below the terminals)
END_T = 5.0
TIE_D = 6.0
TIE_Z = (40.0, 160.0)            # tie-rod heights
FLANGE = 15.0
DECK_TOP = 0.054
CENTRE_BRACKET_REAR_X = -0.135   # base GLB centre_bracket rear face
ENV_CENTRE_X = CENTRE_BRACKET_REAR_X - 0.001 - SHEET / 1000 - ENV[0] / 2000   # -0.2085 (GLB node -0.207)

META = {
    "materials": {"tray": "5754-H22", "end_panel": "6082-T6", "tie_rod": "steel"},
    "item": "battery_tray", "bom": "MEC-007 (with PWR-027 restraint, PWR-028 enclosure interface)", "method": "laser-cut and bent 5754 aluminium tray, machined 6082-T6 end panels",
    "material": "5754-H22", "thickness_mm": SHEET,
    "existing_cad": None,
    "configuration": "rear deck, behind the centre bracket",
    "adjustment": "tie-rod nuts set the cell compression; end panels detachable",
    "placement": [{"name": "envelope_bottom_centre", "xyz": [ENV_CENTRE_X, 0.0, DECK_TOP + SHEET / 1000], "rpy": [0, 0, 0]}],
    "placement_note": "the tray floor raises the provisional envelope by 2.5 mm against the GLB battery node",
    "fasteners": [
        {"joint": "tray to deck", "part": "ISO 4762 screw + ISO 7089 washer + ISO 7040 nyloc nut", "size": "M6 x 16", "qty": 4, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "cell restraint tie rods", "part": "threaded rod + ISO 4032 nuts + ISO 7089 washers (insulated sleeve)", "size": "M6 x 340", "qty": 2, "standard": "DIN 976", "class": "proposed"},
        {"joint": "end panel to tray walls", "part": "ISO 7380 screw + ISO 7089 washer into rivet nut", "size": "M5 x 10", "qty": 8, "standard": "ISO 7380", "class": "proposed"},
    ],
    "next_step": "Hardware owner: BMS/PDB layout with real part sizes; CAD owner: MEC-007 work package, removal path with the cover off.",
}


def build():
    ex, ey, ez = ENV
    t = SHEET
    floor = cq.Workplane("XY").box(ex + 2 * t, ey, t).translate((0, 0, -t / 2))
    walls = None
    for s in (-1, 1):
        w = cq.Workplane("XY").box(t, ey, WALL_H).translate((s * (ex / 2 + t / 2), 0, WALL_H / 2))
        if s < 0:  # rear wall only: flange and lift handle
            w = w.union(cq.Workplane("XY").box(FLANGE, ey, t).translate((-(ex / 2 + t + FLANGE / 2), 0, WALL_H - t / 2)))
        walls = w if walls is None else walls.union(w)
    tray = floor.union(walls)
    for sx in (-1, 1):
        for sy in (-1, 1):
            tray = tray.cut(cq.Workplane("XY").center(sx * (ex / 2 - 15), sy * (ey / 2 - 20)).circle(CLEAR["M6"] / 2).extrude(20, both=True))
    ends = []
    for s in (-1, 1):
        e = cq.Workplane("XY").box(ex + 2 * t + 12, END_T, WALL_H + 70).translate((-6, s * (ey / 2 + END_T / 2), (WALL_H + 70) / 2))
        for x in (-(ex / 2 + t + 6),):
            for z in TIE_Z:
                e = e.cut(cq.Workplane("XZ").center(x, z).circle(CLEAR["M6"] / 2).extrude(20, both=True).translate((0, s * (ey / 2 + END_T / 2), 0)))
        ends.append(e)
    rods = []
    for x in (-(ex / 2 + t + 6),):
        for z in TIE_Z:
            rods.append(cq.Workplane("XZ").center(x, z).circle(TIE_D / 2).extrude((ey + 2 * END_T + 30) / 2, both=True))
    env = cq.Workplane("XY").box(ex, ey, ez).translate((0, 0, ez / 2))
    parts = [("MEC-007_tray", tray), ("MEC-007_end_panel_left", ends[1]), ("MEC-007_end_panel_right", ends[0])]
    parts += [("MEC-007_tie_rod_%d" % (i + 1), r) for i, r in enumerate(rods)]
    parts += [("PWR-001_cell_group_envelope", env)]
    return {"battery_tray": parts}


if __name__ == "__main__":
    run_single(META, build)
