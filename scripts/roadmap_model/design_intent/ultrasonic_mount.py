# SPDX-License-Identifier: MIT
"""b. MB7060 ultrasonic mount (four identical sets), design intent.

Existing CAD: openamr-platform-hw MMP.00.00.00.006 Ultrasonic mount (no tilt, panel hole 29.46 mm in CAD).
This revision: 27.5 mm panel hole (M-01 rev19.7), 3/4in NPS lock nut seat on the panel outer face
(MEC-021), PETG retention plate with anti-rotation flats inside, optional tilt wedges 3 and 6 deg down.
Manufacturing: PETG print, 4.0 mm plate, 3 mm walls. Local frame: origin at the hole centre on the panel
OUTER face, x outward, z up.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

PANEL_HOLE = 27.5        # M-01 rev19.7 (CAD has 29.46, conflict)
PANEL_T = 2.0            # panel sheet, assumed from the 52.0 / 54.0 mm base sheet
NPS_OD = 26.67           # 3/4in NPS major diameter 1.050 in (ASME B1.20.1)
NUT_AF = 34.9            # lock-nut across flats 1-3/8 in (typical 3/4 conduit lock nut; check the MEC-021 part)
NUT_T = 5.0
PLATE = (55.0, 40.0, 4.0)  # retention plate behind the panel, y x z x thickness (same envelope as MMP.00.00.00.006)
FIX_Y = 21.0             # 2 x M3 to the panel (proposed)
TILTS = (0.0, 3.0, 6.0)  # wedge variants, deg down

META = {
    "item": "ultrasonic_mount", "bom": "MEC-011 (+ MEC-021 lock nut)", "method": "PETG print",
    "material": "PETG", "thickness_mm": PLATE[2],
    "existing_cad": "openamr-platform-hw mechanical/cad/production_files/MMP.00.00.00.006 Ultrasonic mount.STEP (no tilt; CAD panel hole 29.46 mm)",
    "configuration": "level (0 deg); wedges 3 and 6 deg down optional",
    "adjustment": "tilt wedge between panel and retention plate (0 / 3 / 6 deg); lock nut clamps the housing",
    "placement": [{"name": "front_left", "xyz": [0.390, 0.130, 0.0914], "rpy": [0, 0, 0]},
                  {"name": "front_right", "xyz": [0.390, -0.130, 0.0914], "rpy": [0, 0, 0]},
                  {"name": "rear_left", "xyz": [-0.390, 0.130, 0.0914], "rpy": [0, 0, math.pi]},
                  {"name": "rear_right", "xyz": [-0.390, -0.130, 0.0914], "rpy": [0, 0, math.pi]}],
    "placement_note": "hole y +/-0.130, 91.4 mm above the floor (sensor_frames.yaml us_*); panel outer face x +/-0.390 (decided 0.390, sensor_frames.yaml 0.3906 / -0.3886)",
    "fasteners": [
        {"joint": "MB7060 to panel", "part": "3/4in NPS lock nut (MEC-021)", "size": "3/4in NPS", "qty": 4, "standard": "ASME B1.20.1 thread", "class": "named"},
        {"joint": "retention plate to panel", "part": "ISO 7380 screw + ISO 7089 washer + ISO 4032 nut", "size": "M3 x 12", "qty": 8, "standard": "ISO 7380", "class": "proposed"},
    ],
    "next_step": "CAD owner: change the panel hole to 27.5 mm and confirm the lock-nut across-flats against the MEC-021 part.",
}


def retention(tilt):
    y, z, t = PLATE
    p = cq.Workplane("YZ").rect(y, z).extrude(-t)
    if tilt:
        # wedge on the plate back, thick at the top, so the sensor seat (and axis) tilts down by 'tilt'
        dz = z * math.tan(math.radians(tilt))
        w = cq.Workplane("XZ").polyline([(-t, -z / 2), (-t, z / 2), (-t - dz, z / 2)]).close().extrude(y / 2, both=True)
        p = p.union(w)
    p = p.cut(cq.Workplane("YZ").circle(NPS_OD / 2 + 0.3).extrude(-40, both=True))
    for s in (-1, 1):
        p = p.cut(cq.Workplane("YZ").center(s * FIX_Y, 0).circle(CLEAR["M3"] / 2).extrude(-40, both=True))
    return p


def nut_seat():
    # printed seat ring on the outer face: centres the lock nut on the 27.5 hole and protects the paint
    r = cq.Workplane("YZ").polygon(6, NUT_AF / math.cos(math.radians(30)) + 3).extrude(1.5).translate((PANEL_T * 0, 0, 0))
    return r.cut(cq.Workplane("YZ").circle(PANEL_HOLE / 2).extrude(5, both=True))


def build():
    out = {}
    for tilt in TILTS:
        name = "ultrasonic_mount" if tilt == 0 else "ultrasonic_mount_tilt%d" % tilt
        out[name] = [("MEC-011_retention_plate", retention(tilt).translate((-PANEL_T, 0, 0))), ("MEC-011_nut_seat", nut_seat())]
    return out


if __name__ == "__main__":
    run_single(META, build)
