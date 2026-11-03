# SPDX-License-Identifier: MIT
"""e. Getac ZX80 pocket and head-light plate (UI-002, MEC-012, AUX-001 plate), design intent.

Owner correction A3 (owner, 2 Nov 2026; to be entered in P-03 and M-01): the Getac ZX80 is portrait (149.8 wide x 234 tall
x 17.6 deep), on a fixed mount (no rotation, decisions.yaml TABLET-MOUNT). Fixed aluminium back plate on the arm-post front face (two
M6 T-nuts per row in the HFS6 front slots), a short spacer hub and a PETG pocket screwed to it for the tablet; the USB-C PD cable runs
through the hub bore and a groove in the pocket back. The Falcon FLDL-i150x15-W lies flat on a 3 mm aluminium plate
(heat spreader) directly under the Getac, its top edge 10 mm below the Getac bottom edge.
Manufacturing: back plate and light plate laser-cut 5754-H22 aluminium (4 mm and 3 mm); spacer hub machined 6082-T6; pocket
PETG print, 3 mm walls.
Local frame: origin on the arm-post front face at the tablet centre height, x forward, z up.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

TAB = (17.6, 149.8, 234.0)        # Getac ZX80 depth x width x height, portrait on a fixed mount (owner correction A3, 2 Nov 2026)
CLR = 1.0                         # clearance per side in the pocket
WALL = 3.0                        # PETG pocket wall
LIP = 5.0                         # retaining lip over the screen edge (bottom and the two sides; top edge has a latch)
BACK = (4.0, 120.0, 160.0)        # back plate x thickness, y width, z height
HUB = (30.0, 14.0, 2.0)           # spacer hub OD, cable bore, gap between back plate and pocket
HUB_YZ = (0.0, 0.0)              # spacer hub axis at the tablet centre (y, z)
LIGHT = (20.0, 158.0, 17.0)       # FLDL-i150x15-W depth x width x height (datums.yaml head_light_size)
LIGHT_PLATE = (3.0, 180.0, 24.0)  # aluminium plate under the light (24 mm tall: clears the pocket bottom with the 10 mm gap)
GAP_LIGHT = 10.0                  # light top edge 10 mm below the Getac bottom edge (owner correction A3, 2 Nov 2026)
T_SLOT_Y = 15.0                   # HFS6 front-face slots at y +/-15 (60 mm face, 30 mm slot pitch)

POCKET = (TAB[0] + CLR + WALL, TAB[1] + 2 * (CLR + WALL), TAB[2] + 2 * (CLR + WALL))
TAB_REAR_X = BACK[0] + HUB[2] + WALL           # tablet rear face ahead of the profile face: 9 mm (datums say 0)
LIGHT_Z = -TAB[2] / 2 - GAP_LIGHT - LIGHT[2] / 2

META = {
    "materials": {"back_plate": "5754-H22", "light_plate": "5754-H22", "spacer_hub": "6082-T6", "pocket": "PETG"},
    "item": "getac_pocket", "bom": "UI-002, MEC-012 (pocket and back plate); AUX-001 plate", "method": "laser-cut 5754 aluminium plates, machined 6082-T6 spacer hub, PETG pocket",
    "material": "PETG", "thickness_mm": WALL,
    "existing_cad": None,
    "configuration": "L1000, portrait on a fixed mount (A3)",
    "adjustment": "none (fixed portrait mount); the tablet lifts out of the pocket",
    "placement": [{"name": "pocket_origin", "xyz": [0.300, 0.0, 1.040], "rpy": [0.0, 0.0, 0.0]}],
    "placement_note": "arm-post front face x 0.060 + 0.180 + 0.060 = 0.300 (bp000); tablet centre 0.246 above the column top at L1000 (datums.yaml getac_tablet_z_above_column_top), 0.834 + 0.246 - 0.040 (A3: 40 mm lower)",
    "fasteners": [
        {"joint": "back plate to arm post", "part": "ISO 4762 screw + ISO 7089 washer + M6 T-slot nut (HFS6)", "size": "M6 x 12", "qty": 4, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "hub to back plate", "part": "ISO 10642 countersunk screw", "size": "M4 x 10", "qty": 4, "standard": "ISO 10642", "class": "proposed"},
        {"joint": "pocket on hub", "part": "ISO 4762 screw + ISO 7089 washer", "size": "M4 x 8", "qty": 3, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "light plate to arm post", "part": "ISO 4762 screw + ISO 7089 washer + M6 T-slot nut (HFS6)", "size": "M6 x 10", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "head light to plate", "part": "ISO 4762 screw (thermal pad between)", "size": "M3 x 8", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
    ],
    "next_step": "Owner: enter the fixed portrait mount and the 10 mm light gap in P-03 and M-01; confirm the ZX80 USB-C port position, then CAD (M-09).",
}


def back_plate():
    t, w, h = BACK
    p = cq.Workplane("YZ").rect(w, h).extrude(t)
    p = p.cut(cq.Workplane("YZ").center(*HUB_YZ).circle(HUB[1] / 2 + 1).extrude(t + 1))
    for y in (-T_SLOT_Y, T_SLOT_Y):
        for z in (-40.0, 40.0):
            p = p.cut(cq.Workplane("YZ").center(y, z).circle(CLEAR["M6"] / 2).extrude(t + 1))
    return p


def hub():
    od, bore, gap = HUB
    h = cq.Workplane("YZ").center(*HUB_YZ).circle(od / 2).extrude(gap + WALL).translate((BACK[0], 0, 0))
    return h.cut(cq.Workplane("YZ").center(*HUB_YZ).circle(bore / 2).extrude(40, both=True))


def pocket():
    d, w, h = POCKET
    x0 = BACK[0] + HUB[2]
    p = cq.Workplane("YZ").rect(w, h).extrude(d).translate((x0, 0, 0))
    cav = cq.Workplane("YZ").rect(TAB[1] + 2 * CLR, TAB[2] + 2 * CLR).extrude(d).translate((x0 + WALL, 0, 0))
    p = p.cut(cav)
    # front lips: bottom and both sides (open window over the screen)
    lip = cq.Workplane("YZ").rect(w, h).extrude(WALL).translate((x0 + d, 0, 0))
    lip = lip.cut(cq.Workplane("YZ").rect(TAB[1] - 2 * LIP, TAB[2] - 2 * LIP).extrude(WALL + 1).translate((x0 + d - 0.5, 0, 0)))
    lip = lip.cut(cq.Workplane("YZ").center(0, h / 2 - (WALL + CLR + LIP) / 2).rect(TAB[1] - 2 * LIP, WALL + CLR + LIP + 0.1).extrude(WALL + 1).translate((x0 + d - 0.5, 0, 0)))
    p = p.union(lip)
    hy, hz = HUB_YZ
    p = p.cut(cq.Workplane("YZ").center(hy, hz).circle(HUB[0] / 2 + 0.3).extrude(WALL + 1).translate((x0 - 0.5, 0, 0)))  # hub seat
    p = p.union(cq.Workplane("YZ").center(hy, hz).circle(HUB[0] / 2 + 6).extrude(WALL).translate((x0, 0, 0))
                .cut(cq.Workplane("YZ").center(hy, hz).circle(HUB[0] / 2 + 0.3).extrude(WALL + 1).translate((x0 - 0.5, 0, 0))))
    # cable groove from the hub to the -y short edge, 6 mm wide, 2 mm deep in the back
    p = p.cut(cq.Workplane("XY").box(2.0, w / 2, 6.0).translate((x0 + WALL - 1.0, -w / 4, 0)))
    return p


def light_set():
    t, w, h = LIGHT_PLATE
    zc = LIGHT_Z
    pl = cq.Workplane("YZ").center(0, zc).rect(w, h).extrude(t)
    for y in (-T_SLOT_Y, T_SLOT_Y):
        pl = pl.cut(cq.Workplane("YZ").center(y, zc).circle(CLEAR["M6"] / 2).extrude(t + 1))
    lt = cq.Workplane("YZ").center(0, zc).rect(LIGHT[1], LIGHT[2]).extrude(LIGHT[0]).translate((t, 0, 0))
    return pl, lt


def build():
    pl, lt = light_set()
    base = [("MEC-012_back_plate", back_plate()), ("UI-002_spacer_hub", hub()), ("AUX-001_light_plate", pl),
            ("AUX-001_head_light_envelope", lt)]
    return {"getac_pocket": base + [("UI-002_pocket_portrait", pocket())]}


if __name__ == "__main__":
    run_single(META, build)
