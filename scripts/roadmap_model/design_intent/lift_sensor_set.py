# SPDX-License-Identifier: MIT
"""j. Lift stop sensor set (LFT-001 to LFT-007, drawing LIFT-SNS-01 rev1), design intent.

Static (on the static DOLD profile, +y face, still to be confirmed): 3 x SICK IME12-04BNSZC0S (M12, NPN NO)
on SICK BEF-WN-M12 angle brackets in a T-slot, sensor axes at 120 / 295 / 470 mm above the column base for
L1000 / L1175 / L1350, sensing faces toward -x. Moving (hanging from the adapter-plate underside): MISUMI
5-series 20 x 20 rod L430, M5 tapped, a 20 corner bracket against rotation, and an SS400 steel flag
45 x 20 x 2 mm with its centre 410 mm below the plate underside, 2 mm air gap to the sensing faces; the rod
runs 9 mm beside the sensor bodies. Values from datums.yaml (revision 2026-11-01.c), which carries the
docs-model geometry; the BEF-WN-M12 outline is the docs envelope (issue #23: supplier drawing not matched).
Manufacturing: flag laser-cut SS400 2 mm; rod cut from profile; brackets and sensors bought.
Local frame: origin on the column axis at the column base (lift base-plate top), x forward, z up; moving
parts at L1000.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import run_single  # noqa: E402

COL_HALF_Y = 30.0
SENSOR_Z = (120.0, 295.0, 470.0)       # datums lift_stop_sensor_z_l1000 / l1175 / l1350
FACE_X = -95.0                          # datums lift_stop_sensor_face_x
AXIS_OFF = 15.0                         # datums lift_stop_sensor_axis_from_face
SENSOR = (12.0, 48.0)                   # diameter, length
BRACKET = (40.0, 4.0, 25.0, 28.0)       # leg, thickness, height, sensor-leg from sensor back (datums)
FLAG = (2.0, 45.0, 20.0)                # x, y, z
FLAG_GAP, FLAG_OFF, FLAG_BELOW = 2.0, 5.0, 410.0
ROD = (20.0, 430.0, 30.0)               # width, length, inner face from the column face
PLATE_UNDERSIDE_L1000 = 530.0           # retracted column length above the column base
CORNER = (20.0, 3.0)                    # corner bracket leg and thickness

META = {
    "mass_note": "rod mass from the solid 20 x 20 envelope (a slotted 5-series profile is lighter, about 0.4 of it)",
    "materials": {"BEF-WN-M12": "steel", "rod": "6063-T5", "corner_bracket": "6063-T5", "flag": "SS400"},
    "item": "lift_sensor_set", "bom": "LFT-001, LFT-002 (cable, not drawn here), LFT-003, LFT-004, LFT-005, LFT-006, LFT-007",
    "method": "bought sensors, brackets and profile; laser-cut SS400 flag", "material": "SS400", "thickness_mm": FLAG[0],
    "existing_cad": None,
    "configuration": "L1000 (moving parts), bp000",
    "adjustment": "sensor heights along the T-slot; sensing distance with the two M12 nuts; flag height on the rod",
    "placement": [{"name": "column_base_axis", "xyz": [0.060, 0.0, 0.304], "rpy": [0, 0, 0]}],
    "placement_note": "moving parts rise 0.175 / 0.350 m at L1175 / L1350",
    "fasteners": [
        {"joint": "BEF-WN-M12 to DOLD T-slot", "part": "bracket screw + T-nut (LFT-007)", "size": "M5 x 10 (DOLD slot to confirm)", "qty": 3, "standard": "ISO 4762", "class": "named"},
        {"joint": "sensor in bracket", "part": "M12 x 1 nuts (supplied with the sensor)", "size": "M12 x 1", "qty": 6, "standard": "supplier", "class": "named"},
        {"joint": "rod to adapter plate", "part": "ISO 4762 screw into the M5 rod end tap (LFT-007)", "size": "M5 x 20", "qty": 1, "standard": "ISO 4762", "class": "named"},
        {"joint": "corner bracket to rod", "part": "ISO 7380 screw + short M4 T-nut (LFT-007)", "size": "M4 x 8", "qty": 2, "standard": "ISO 7380", "class": "named"},
        {"joint": "corner bracket to plate", "part": "ISO 4762 screw (into tapped plate)", "size": "M4 x 10", "qty": 1, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "flag to rod", "part": "ISO 7380 screw + short M4 T-nut", "size": "M4 x 8", "qty": 2, "standard": "ISO 7380", "class": "proposed"},
    ],
    "next_step": "Confirm the column face (+y) and the BEF-WN-M12 outline (issue #23); increase the flag-to-bracket clearance (see note); M-09.",
}


def sensors_and_brackets():
    d, l = SENSOR
    leg, t, h, at = BRACKET
    y0 = COL_HALF_Y
    sens, brk = [], []
    for z in SENSOR_Z:
        s = cq.Workplane("YZ").center(y0 + AXIS_OFF, z).circle(d / 2).extrude(l).translate((FACE_X, 0, 0))
        sens.append(s)
        back = FACE_X + l
        bx = back - at
        b1 = cq.Workplane("XY").box(leg, t, h).translate((bx - leg / 2, y0 + t / 2, z))
        b2 = cq.Workplane("XY").box(t, leg, h).translate((bx - t / 2, y0 + leg / 2, z))
        b = b1.union(b2).cut(cq.Workplane("YZ").center(y0 + AXIS_OFF, z).circle(d / 2 + 0.3).extrude(200, both=True))
        brk.append(b)
    return sens, brk


def moving():
    w, l, off = ROD
    zt = PLATE_UNDERSIDE_L1000
    rx = FACE_X - FLAG_GAP - FLAG[0] - w / 2
    ry = COL_HALF_Y + off + w / 2
    rod = cq.Workplane("XY").box(w, w, l).translate((rx, ry, zt - l / 2))
    a, t = CORNER
    cb = (cq.Workplane("XY").box(w, a, t).translate((rx, ry - w / 2 - a / 2, zt - t / 2))
          .union(cq.Workplane("XY").box(w, t, a).translate((rx, ry - w / 2 - t / 2, zt - t - a / 2))))
    flag = cq.Workplane("XY").box(*FLAG).translate((FACE_X - FLAG_GAP - FLAG[0] / 2, COL_HALF_Y + FLAG_OFF + FLAG[1] / 2, zt - FLAG_BELOW))
    return rod, cb, flag


def build():
    sens, brk = sensors_and_brackets()
    rod, cb, flag = moving()
    parts = []
    for i, (s, b) in enumerate(zip(sens, brk)):
        parts += [("LFT-001_IME12_%d_envelope" % (i + 1), s), ("LFT-003_BEF-WN-M12_%d" % (i + 1), b)]
    parts += [("LFT-004_rod_L430", rod), ("LFT-005_corner_bracket", cb), ("LFT-006_flag_SS400", flag)]
    return {"lift_sensor_set": parts}


if __name__ == "__main__":
    run_single(META, build)
    print("flag inner edge to the bracket leg on the face: %.1f mm" % (FLAG_OFF - BRACKET[1]))
