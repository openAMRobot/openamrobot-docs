# SPDX-License-Identifier: MIT
"""a. TF-Luna mount, front and rear (identical parts), design intent.

Existing CAD: openamr-platform-hw MMP.00.00.00.005 TF-Luna mount (fixed 10 deg, for the 22 mm hole).
This design-intent revision adds the +/-5 deg adjustment slot and a variant for the proposed
30 x 23 mm window. Manufacturing: PETG print, 3.0 mm walls, 0.2 mm layers, 4 perimeters.
Local frame: origin at the centre of the panel opening on the panel INNER face, x out of the robot
through the panel, z up. The sensor pitches nose-down about the y axis through the pivot.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

# --- parameters (mm, deg) ---
SENSOR = (35.0, 21.25, 12.5)   # TF-Luna L x W x H, Benewake datasheet PD-TF-Luna-Datasheet-A05; L along the optical axis
PITCH_NOM = 10.0               # decided pitch down (P-03 / M-01 rev19.7, conflicts with sensor_frames.yaml 20 deg)
PITCH_ADJ = 5.0                # +/- adjustment (section D a)
HOLE_D = 22.0                  # M-01 rev19.7 panel hole
WINDOW = (30.0, 23.0)          # proposed window (CAD owner proposal, open), width x height
WALL = 3.0                     # PETG wall
PLATE = (56.0, 38.0)           # back plate on the panel inner face, y x z
PANEL_FIX_Y = 22.0             # 2 x M3 panel fixings at y +/-22 (match MMP.00.00.00.005 fixing or drill the panel; proposed)
PIVOT_X = -9.0                 # pivot axis behind the panel inner face (sensor front face then clears the 2 mm panel at 15 deg)
SLOT_R = 13.0                  # radius of the clamp-screw arc slot about the pivot
CLAMP = "M3"                   # clamp screw into a heat-set insert in the carrier

META = {
    "item": "tof_mount", "bom": "MEC-010", "method": "PETG print",
    "material": "PETG", "thickness_mm": WALL,
    "existing_cad": "openamr-platform-hw mechanical/cad/production_files/MMP.00.00.00.005 TF-Luna mount.STEP (fixed 10 deg, 22 mm hole)",
    "configuration": "pitch 10 deg down (adjustable 5 to 15 deg), front and rear identical",
    "adjustment": "arc slot +/-5 deg about a y-axis pivot at the panel, M3 clamp; hole and window variants",
    "placement": [{"name": "front", "xyz": [0.388, 0.0, 0.0914], "rpy": [0.0, 0.0, 0.0]},
                  {"name": "rear", "xyz": [-0.388, 0.0, 0.0914], "rpy": [0.0, 0.0, math.pi]}],
    "placement_note": "panel inner face assumed 2 mm inside the panel outer face x +/-0.390; height 91.4 mm (front centre opening, sensor_frames.yaml); "
                      "x of the lens face then 0.390 (P-03 rev19.7, BOM 7.14), not 0.399 (sensor_frames.yaml)",
    "fasteners": [
        {"joint": "TF-Luna mount to panel", "part": "ISO 7380 button head screw + ISO 4032 nut + ISO 7089 washer", "size": "M3 x 10", "qty": 2, "standard": "ISO 7380", "class": "proposed"},
        {"joint": "carrier pivot", "part": "ISO 4762 screw into heat-set insert", "size": "M3 x 8", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "pitch clamp", "part": "ISO 4762 screw + ISO 7089 washer into heat-set insert", "size": "M3 x 8", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "carrier heat-set inserts", "part": "brass heat-set insert", "size": "M3 x 5.7", "qty": 4, "standard": "manufacturer", "class": "proposed"},
        {"joint": "TF-Luna to carrier", "part": "ISO 7380 screw", "size": "M2 x 6", "qty": 2, "standard": "ISO 7380", "class": "proposed"},
    ],
    "next_step": "CAD owner: check the TF-Luna M2 hole pattern against the datasheet drawing, decide 22 mm hole vs 30 x 23 window, then update MMP.00.00.00.005.",
}


def carrier(pitch):
    L, W, H = SENSOR
    w = W + 2 * WALL
    # U-carrier: floor + two side walls, sensor face at the pivot plane (x = PIVOT_X + 1), lens forward
    body = cq.Workplane("XY").box(L + WALL, w, H + WALL).translate((PIVOT_X - (L + WALL) / 2 + 1, 0, -WALL / 2))
    pocket = cq.Workplane("XY").box(L, W + 0.4, H + 1).translate((PIVOT_X - L / 2 + 1 - 0.01, 0, 0.5))
    body = body.cut(pocket)
    # cable exit at the rear
    body = body.cut(cq.Workplane("XY").box(WALL + 2, 12, 6).translate((PIVOT_X - L - WALL / 2 + 1, 0, 0)))
    return body.rotate((PIVOT_X, 0, 0), (PIVOT_X, 1, 0), pitch)


def cheeks():
    L, W, H = SENSOR
    yo = W / 2 + WALL + 0.5 + WALL / 2
    out = None
    for s in (-1, 1):
        ch = cq.Workplane("XZ").center(-(WALL + 29.0 / 2), 0).rect(29.0, 30).extrude(WALL / 2, both=True).translate((0, s * yo, 0))  # x -3 (plate back) to -32
        ch = ch.cut(cq.Workplane("XZ").center(PIVOT_X, 0).circle(CLEAR["M3"] / 2).extrude(10, both=True))
        # arc slot about the pivot covering PITCH_NOM +/- PITCH_ADJ, clamp screw on the rear (-x) side
        pts = []
        for k in range(0, 21):
            a = math.radians(180 + (-PITCH_ADJ + k * 2 * PITCH_ADJ / 20))
            pts.append((PIVOT_X + SLOT_R * math.cos(a), SLOT_R * math.sin(a)))
        for (x, z) in pts:
            ch = ch.cut(cq.Workplane("XZ").center(x, z).circle(CLEAR["M3"] / 2).extrude(10, both=True).translate((0, s * yo, 0)))
        out = ch if out is None else out.union(ch)
    return out


def plate(aperture):
    p = cq.Workplane("YZ").rect(*PLATE).extrude(-WALL)
    if aperture == "hole":
        p = p.cut(cq.Workplane("YZ").circle(HOLE_D / 2).extrude(-WALL - 1))
    else:
        p = p.cut(cq.Workplane("YZ").rect(*WINDOW).extrude(-WALL - 1))
    for y in (-PANEL_FIX_Y, PANEL_FIX_Y):
        p = p.cut(cq.Workplane("YZ").center(y, 0).circle(CLEAR["M3"] / 2).extrude(-WALL - 1))
    return p


def build():
    out = {}
    for ap, name in (("hole", "tof_mount_hole22"), ("window", "tof_mount_window30x23")):
        out[name] = [("MEC-010_plate_and_cheeks", plate(ap).union(cheeks())), ("MEC-010_carrier_10deg", carrier(PITCH_NOM))]
    return out


if __name__ == "__main__":
    run_single(META, build)
