# SPDX-License-Identifier: MIT
"""k. Battery pocket trays MEC-007, left and right, design intent only.

Owner correction A1 (owner, 2 Nov 2026; to be entered in P-03 and M-01): 8 x EVE LF105 (200 h x 130 x 38 mm) upright,
4 cells in each side pocket beside the reserved TZBOT receiver zone in the middle of the rear section, 8S; replaces the
single row of 8 cells across the robot (B-02 rev18.10). The pocket positions and the cell arrangement come from
scripts/roadmap_model/rear_layout.py (CAD v0.2 free space; the arrangement that fits each pocket with restraint and
terminal access). Each tray: 3 mm floor, 3 mm walls 120 mm tall (restraint below the terminals), an insulated top strap
across the cells; terminals on top, reachable with the cover off; the series link between the groups runs across the
charger zone above the 20 mm metal-free margin. The tray bolts to the base sheet with 4 x M6.
Local frame: base_footprint (the parts are exported in place, placement origin 0).
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), ".."))
from _common import CLEAR, run_single  # noqa: E402
import rear_layout  # noqa: E402

SHEET = 3.0
WALL_H = 120.0
STRAP = (20.0, 4.0)
L = rear_layout.layout()

META = {
    "materials": {"tray": "5754-H22", "strap": "PETG"},   # strap mass approximated as PETG (PA66 strap)
    "item": "battery_tray", "bom": "MEC-007 (with PWR-027 restraint)", "method": "laser-cut and bent 5754 aluminium trays",
    "material": "5754-H22", "thickness_mm": SHEET,
    "existing_cad": None,
    "configuration": "two side pockets of the rear section (A1), arrangement %s" % L["pockets"].get("arrangement", ""),
    "adjustment": "strap tension; trays lift out vertically with the cover off",
    "placement": [{"name": "in_place", "xyz": [0.0, 0.0, 0.0], "rpy": [0, 0, 0]}],
    "placement_note": "parts exported in base_footprint; trays %s" % "; ".join("%s x %.3f..%.3f y %.3f..%.3f" % (t["side"], t["lo"][0], t["hi"][0], t["lo"][1], t["hi"][1]) for t in L["trays"]),
    "clears_side_panel_flanges": L["pockets"].get("clears_flanges"),
    "fasteners": [
        {"joint": "tray to base sheet", "part": "ISO 4762 screw + ISO 7089 washer + rivet nut", "size": "M6 x 12", "qty": 8, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "cell strap", "part": "strap with buckle", "size": "20 mm", "qty": 2, "standard": "proposed", "class": "proposed"},
    ],
    "next_step": "Hardware owner: BMS and busbar layout with real parts; CAD owner: MEC-007 pocket trays and the side-panel flange notches (GI-025).",
}


def tray(t):
    lo = [v * 1000 for v in t["lo"]]
    hi = [v * 1000 for v in t["hi"]]
    dx, dy = hi[0] - lo[0], hi[1] - lo[1]
    cx, cy = (lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2
    z0 = lo[2]
    b = cq.Workplane("XY").box(dx, dy, SHEET).translate((cx, cy, z0 + SHEET / 2))
    for sx in (-1, 1):
        b = b.union(cq.Workplane("XY").box(SHEET, dy, WALL_H).translate((cx + sx * (dx - SHEET) / 2, cy, z0 + WALL_H / 2)))
    for sy in (-1, 1):
        b = b.union(cq.Workplane("XY").box(dx, SHEET, WALL_H).translate((cx, cy + sy * (dy - SHEET) / 2, z0 + WALL_H / 2)))
    for sx in (-1, 1):
        for sy in (-1, 1):
            b = b.cut(cq.Workplane("XY").center(cx + sx * (dx / 2 - 12), cy + sy * (dy / 2 - 12)).circle(CLEAR["M6"] / 2).extrude(z0 + 20).translate((0, 0, -10)))
    strap = cq.Workplane("XY").box(dx, STRAP[0], STRAP[1]).translate((cx, cy, hi[2] - STRAP[1] / 2))
    return b, strap


def build():
    parts = []
    for t in L["trays"]:
        b, s = tray(t)
        parts += [("MEC-007_pocket_tray_%s" % t["side"], b), ("PWR-027_strap_%s" % t["side"], s)]
    return {"battery_tray": parts}


if __name__ == "__main__":
    run_single(META, build)
