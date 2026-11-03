# SPDX-License-Identifier: MIT
"""j. Lift stop sensor set (LFT-001 to LFT-007, drawing LIFT-SNS-01 rev1), design intent; A6 (owner correction, 2 Nov 2026).

Static, on the REAR face of the static DOLD profile, centred in y: 3 x SICK IME12-04BNSZC0S (M12, NPN NO) on SICK
BEF-WN-M12 angle brackets in the rear T-slot (one leg on the face, the sensor through the other leg, parallel to the
face), sensor axes along y at 120 / 295 / 470 mm above the column base for L1000 / L1175 / L1350, sensing faces
toward +y. Moving, hanging from the underside of the adapter-plate rear extension: MISUMI 5-series 20 x 20 rod L430
bolted with M5 into its tapped end, a 20 corner bracket on the column side against rotation, and an SS400 steel flag
45 x 20 x 2 mm with its centre 410 mm below the plate underside, 2 mm off the sensing faces; the rod is 9 mm clear of
the sensor faces. All positions from frames.lift_rear_layout() (facts.yaml lift_rear). The BEF-WN-M12 outline is the
docs envelope (issue #23: supplier drawing not matched). Manufacturing: flag laser-cut SS400 2 mm; rod cut from
profile; brackets and sensors bought.
Local frame: origin on the column axis at the column base (lift base-plate top), x forward, z up; moving parts at L1000.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from frames import FACTS, lift_rear_layout  # noqa: E402
from _common import run_single  # noqa: E402

_F, _LR = FACTS["lift_rear"], lift_rear_layout()
mm = lambda v: v * 1000.0
SENSOR_Z = tuple(mm(z) for z in _F["sensor_z"])            # datums lift_stop_sensor_z_l1000 / l1175 / l1350 (unchanged)
REAR_X = mm(_F["column_rear_x"])                            # rear face of the static column
AXIS_X = mm(_LR["sensor_axis_x"])                           # sensor axis (along y), behind the rear face
FACE_Y = mm(_LR["face_y"])                                  # sensing face, toward +y
SENSOR = (mm(_F["sensor"]["d"]), mm(_F["sensor"]["len"]))   # diameter, length
BRACKET = (mm(_F["bracket"]["leg"]), mm(_F["bracket"]["t"]), mm(_F["bracket"]["h"]))
FLAG = tuple(mm(v) for v in _F["flag"])                     # x, y, z (A6: flat in the xz plane)
FLAG_X, FLAG_Y = tuple(mm(v) for v in _LR["flag_x"]), tuple(mm(v) for v in _LR["flag_y"])
FLAG_BELOW = mm(_F["flag_below_plate"])
ROD = (mm(_F["rod"]["w"]), mm(_F["rod"]["len"]))
ROD_X, ROD_Y = tuple(mm(v) for v in _LR["rod_x"]), tuple(mm(v) for v in _LR["rod_y"])
CORNER_X = tuple(mm(v) for v in _LR["corner_x"])
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
    "next_step": "Confirm the rear T-slot of the DOLD profile and the BEF-WN-M12 outline (issue #23); M-09.",
}


def sensors_and_brackets():
    d, l = SENSOR
    leg, t, h = BRACKET
    sens, brk = [], []
    for z in SENSOR_Z:
        s = cq.Workplane("XZ").center(AXIS_X, z).circle(d / 2).extrude(-l).translate((0, FACE_Y - l, 0))
        sens.append(s)
        b1 = cq.Workplane("XY").box(t, leg, h).translate((REAR_X - t / 2, -leg / 2, z))      # leg on the rear face
        b2 = cq.Workplane("XY").box(leg, t, h).translate((REAR_X - leg / 2, -t / 2, z))      # leg carrying the sensor
        b = b1.union(b2).cut(cq.Workplane("XZ").center(AXIS_X, z).circle(d / 2 + 0.3).extrude(200, both=True))
        brk.append(b)
    return sens, brk


def moving():
    w, l = ROD
    zt = PLATE_UNDERSIDE_L1000
    rx, ry = sum(ROD_X) / 2, sum(ROD_Y) / 2
    rod = cq.Workplane("XY").box(w, w, l).translate((rx, ry, zt - l / 2))
    a, t = CORNER
    cb = (cq.Workplane("XY").box(a, w, t).translate((sum(CORNER_X) / 2, ry, zt - t / 2))
          .union(cq.Workplane("XY").box(t, w, a).translate((CORNER_X[0] + t / 2, ry, zt - t - a / 2))))
    flag = cq.Workplane("XY").box(*FLAG).translate((sum(FLAG_X) / 2, sum(FLAG_Y) / 2, zt - FLAG_BELOW))
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
    print("rod clearance to the sensor faces: %.1f mm" % _LR["rod_clear_mm"])
