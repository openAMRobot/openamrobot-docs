# SPDX-License-Identifier: MIT
"""i. Hub-motor shaft-flat brackets MEC-015 (4 per robot: both shaft ends of both wheels), design intent.

ZLTECH ZLLG80ASM250-L-B2 V1.01 double shaft (openamr-platform-hw datasheets/ZLTech/wheel_ZLLG80ASM250):
shafts M14 x 1.5 with 10 mm flats, overall 167.8 mm, brake-side shaft 40 mm, hub width 59.2 mm, supplied nut
13 mm and washer 4 mm per side (STEP solids). Brake side inboard on both wheels (P-03).
Each bracket is an L bent from 5 mm S355 steel: a vertical leg with a 10.2 mm wide slot that engages the
shaft flats (anti-rotation) and is elongated +/-2 mm vertically (axle height 98 to 102 mm: base_link 0.098
vs wheel radius 0.100 is open), and a foot bolted through the 2 mm base sheet with 2 x M8. Assembly: fit one
bracket on each shaft end (nut loose), lower wheel and brackets into the deck cut-out, bolt the feet, set
the height, torque the shaft nuts.
Strength (factor of safety target 3.0, B7): peak motor torque 16 Nm reacted on the two flats of one bracket
(worst case, the other bracket loose): flat contact force 16 / (2 x 3.3e-3) = 2.4 kN on 5 x 4.9 mm, bearing
stress about 100 MPa, S355 yield 355 MPa, factor 3.5. Vertical wheel load 120 kg x 9.81 x 0.5 x 2 (dynamic)
= 1.2 kN per wheel in plane of the leg: negligible stress.
Local frame: origin on the shaft axis at the bracket inner face (wheel side), y pointing away from the
wheel, z up.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

T = 5.0                  # sheet, S355
FLAT = 10.0              # shaft flats across (B2 drawing)
SLOT_W = FLAT + 0.2
SLOT_ADJ = 2.0           # +/- vertical adjustment
SHAFT_D = 14.0
AXLE_Z = 98.0            # axle above the floor (base_link 0.098, B7; 100 if rounded)
DECK_TOP = 54.0          # base sheet top (B7, 52.0 / 54.0)
LEG_W = 70.0             # leg width along x
LEG_TOP_ABOVE_AXLE = 25.0
FOOT = 40.0              # foot length (away from the wheel)
BEND_R = 5.0
WHEEL_Y = 200.0          # wheel centre |y| (track 0.400 placeholder)
# shaft geometry along the wheel axis from the tyre centre (STEP): brake-side shoulder 73.4 mm inboard, outer hub face 29.6 mm outboard
INNER_FACE = WHEEL_Y - 73.4     # 126.6: bracket inner face, brake side (bears on the shaft shoulder at STEP x 88.9)
OUTER_FACE = WHEEL_Y + 29.6     # 229.6: bracket inner face, outer side (bears on the hub face at STEP x -14.1)
BRAKE_FACE = WHEEL_Y - 65.6     # 134.4: brake housing outer face (STEP x 81.1)
OUTER_SHAFT_END = WHEEL_Y + 54.4  # 254.4

META = {
    "item": "motor_bracket", "bom": "MEC-015", "method": "laser-cut and bent S355 steel sheet, zinc plated",
    "material": "S355", "thickness_mm": T,
    "existing_cad": None,
    "existing_cad_note": "MMP.03.00.00.001 to .004 (wheel brackets, motor bracket, drive shaft) belong to the release 001 drive-shaft wheel, not the ZLLG80 hub motor",
    "configuration": "4 brackets; brake side inboard on both wheels",
    "adjustment": "axle height +/-2 mm in the slot (98 to 102 mm), foot shims MEC-016",
    "placement": [{"name": "left_inner", "xyz": [0.0, INNER_FACE / 1000, AXLE_Z / 1000], "rpy": [0, 0, 3.141592653589793]},
                  {"name": "left_outer", "xyz": [0.0, OUTER_FACE / 1000, AXLE_Z / 1000], "rpy": [0, 0, 0]},
                  {"name": "right_inner", "xyz": [0.0, -INNER_FACE / 1000, AXLE_Z / 1000], "rpy": [0, 0, 0]},
                  {"name": "right_outer", "xyz": [0.0, -OUTER_FACE / 1000, AXLE_Z / 1000], "rpy": [0, 0, 3.141592653589793]}],
    "placement_note": "local +y points away from the wheel: inner brackets face inboard, outer brackets outboard",
    "fasteners": [
        {"joint": "bracket on shaft", "part": "supplied M14 x 1.5 nut and washer (ZLTECH)", "size": "M14 x 1.5", "qty": 4, "standard": "supplier", "class": "named"},
        {"joint": "bracket foot to base sheet", "part": "ISO 4017 hex screw 8.8 + 2 x ISO 7089 washer + ISO 7040 nyloc nut", "size": "M8 x 20", "qty": 8, "standard": "ISO 4017", "class": "proposed"},
        {"joint": "height shim", "part": "MEC-016 shim 0.5 / 1 / 2 mm", "size": "70 x 40", "qty": 4, "standard": "-", "class": "named"},
    ],
    "next_step": "CAD owner: model MEC-015 against the B2 drawing, confirm the deck cut-out and the side-panel clearance at the outer feet, FEA for factor 3.0.",
}


def bracket():
    h = AXLE_Z + LEG_TOP_ABOVE_AXLE - DECK_TOP          # leg height above the deck
    zb = DECK_TOP - AXLE_Z                               # leg bottom relative to the axle (-44)
    leg = cq.Workplane("XZ").center(0, zb + h / 2).rect(LEG_W, h).extrude(-T)   # extrude toward +y (away from the wheel)
    slot = cq.Workplane("XZ").slot2D(SHAFT_D + 2 * SLOT_ADJ, SLOT_W, 90).extrude(-T - 2).translate((0, 1, 0))
    leg = leg.cut(slot)
    foot = cq.Workplane("XY").box(LEG_W, FOOT, T).translate((0, T + FOOT / 2 - T, zb + T / 2))
    for x in (-22.0, 22.0):
        foot = foot.cut(cq.Workplane("XY").center(x, T + FOOT / 2 - T + 4).circle(CLEAR["M8"] / 2).extrude(50, both=True))
    b = leg.union(foot)
    try:
        b = b.edges("|X").edges(cq.selectors.NearestToPointSelector((0, T, zb + T))).fillet(BEND_R)
    except Exception:
        pass
    return b


def build():
    return {"motor_bracket": [("MEC-015_shaft_flat_bracket", bracket())]}


if __name__ == "__main__":
    run_single(META, build)
    nut_out = OUTER_FACE + T + 4.0 + 13.0
    print("outer: thread beyond the nut %.1f mm; brake housing to inner bracket %.1f mm" % (OUTER_SHAFT_END - nut_out, BRAKE_FACE - INNER_FACE))
