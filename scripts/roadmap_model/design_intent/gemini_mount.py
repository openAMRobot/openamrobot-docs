# SPDX-License-Identifier: MIT
"""c. Orbbec Gemini 336L mount with locked bt05 / bt10 / bt15 positions, design intent.

Existing CAD: openamr-platform-hw MMP.01.00.00.003 Camera mount (fixed 10 deg up, 144 x 42 x 32 mm).
This revision: a fixed base (same footprint) with two cheeks and a pivoting cradle; the pivot axis runs
along y through the front-glass line so base_camera_link stays at (0.387, 0, 0.046) in every position.
Lock: one M4 screw per side into a heat-set insert in the cradle (the 2 x M4 inserts of MEC-009); the
left cheek has the bt05 and bt15 holes, the right cheek the bt10 hole, on a 36 mm radius behind the pivot,
so a wrong hole cannot be picked by accident. Manufacturing: PETG print, 4.0 mm walls.
Local frame: origin at base_camera_link (front-glass centre), x forward, z up; pitch up is negative about y.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, INSERT_BORE, run_single  # noqa: E402

CAM = (26.0, 124.0, 29.0)     # Gemini 336L depth x width x height (Orbbec product data; matches the GLB envelope at 10 deg)
WALL = 4.0
TILTS = {"bt05": 5.0, "bt10": 10.0, "bt15": 15.0}   # deg up, P-03 / M-01 rev19.7; baseline bt10
LOCK_R = 36.0                 # lock-hole radius about the pivot (bt05 to bt15 holes 6.3 mm apart, 1.8 mm web)
BASE = (42.0, 144.0, 4.0)     # base plate x (depth) x y x thickness, same footprint as MMP.01.00.00.003
CHEEK_H = 36.0
CAM_SCREW = "M4"              # camera bottom M4 threads (Gemini 336L has 2 x M4 + 1/4-20 on the bottom; verify spacing)

META = {
    "item": "gemini_mount", "bom": "MEC-009", "method": "PETG print", "material": "PETG", "thickness_mm": WALL,
    "existing_cad": "openamr-platform-hw mechanical/cad/production_files/MMP.01.00.00.003 Camera mount.STEP (fixed 10 deg)",
    "configuration": "bt10 (baseline); bt05 and bt15 locked alternatives",
    "adjustment": "cradle pivots about the front-glass line; locked at bt05 / bt10 / bt15 by an M4 screw into the cradle insert",
    "placement": [{"name": "base_camera_link", "xyz": [0.387, 0.0, 0.144], "rpy": [0.0, -0.1745, 0.0]}],
    "placement_note": "base_camera_link (0.387, 0, 0.046) in base_link (sensor_frames.yaml); housing centre 142.5 mm above the floor (M-01 rev19.7)",
    "fasteners": [
        {"joint": "cradle lock", "part": "ISO 4762 screw + ISO 7089 washer", "size": "M4 x 10", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "cradle lock inserts", "part": "brass heat-set insert", "size": "M4 x 8.1", "qty": 2, "standard": "manufacturer", "class": "named"},
        {"joint": "cradle pivot", "part": "ISO 4762 shoulder-free screw + ISO 7089 washer + ISO 10511 nyloc nut", "size": "M4 x 12", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "camera to cradle", "part": "ISO 4762 screw", "size": "M4 x 8", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "base to chassis", "part": "ISO 7380 screw + ISO 4032 nut + ISO 7089 washer", "size": "M4 x 12", "qty": 2, "standard": "ISO 7380", "class": "proposed"},
    ],
    "next_step": "CAD owner: check the Gemini 336L bottom-thread spacing and the front opening (about 126 x 36 mm) at bt15, then update MMP.01.00.00.003.",
}


def cradle(tilt):
    d, w, h = CAM
    c = cq.Workplane("XY").box(d + WALL, w + 2 * WALL, WALL).translate((-(d + WALL) / 2 + 1, 0, -h / 2 - WALL / 2))
    for s in (-1, 1):
        c = c.union(cq.Workplane("XY").box(d + WALL, WALL, h * 0.6).translate((-(d + WALL) / 2 + 1, s * (w / 2 + WALL / 2), -h / 2 + h * 0.3 - WALL)))
        # pivot boss and insert bosses on the outside of each side wall
        c = c.union(cq.Workplane("XZ").circle(6).extrude(WALL / 2, both=True).translate((0, s * (w / 2 + WALL * 1.5), 0)))
        arm = cq.Workplane("XZ").center(-LOCK_R / 2, 0).rect(LOCK_R, 8).extrude(WALL / 2, both=True)
        arm = arm.union(cq.Workplane("XZ").center(-LOCK_R, 0).circle(6).extrude(WALL / 2, both=True))
        arm = arm.cut(cq.Workplane("XZ").center(-LOCK_R, 0).circle(INSERT_BORE["M4"] / 2).extrude(10, both=True))
        c = c.union(arm.translate((0, s * (w / 2 + WALL * 1.5), 0)))
    for x in (-8.0, -18.0):
        c = c.cut(cq.Workplane("XY").center(x, 0).circle(CLEAR[CAM_SCREW] / 2).extrude(-40).translate((0, 0, -h / 2 + 5)))
    return c.rotate((0, 0, 0), (0, 1, 0), -tilt)


def base_and_cheeks():
    bx, by, bt = BASE
    d, w, h = CAM
    z0 = -h / 2 - WALL - 6.0  # base top below the cradle floor at bt15
    b = cq.Workplane("XY").box(bx, by, bt).translate((-bx / 2 + 4, 0, z0 - bt / 2))
    for s in (-1, 1):
        y = s * (w / 2 + WALL * 2.5)
        ch = cq.Workplane("XZ").center(-16, (z0 + 14) / 2).rect(52, abs(z0) + 14).extrude(WALL / 2, both=True).translate((0, y, 0))
        ch = ch.union(cq.Workplane("XZ").circle(8).extrude(WALL / 2, both=True).translate((0, y, 0)))
        ch = ch.cut(cq.Workplane("XZ").circle(CLEAR["M4"] / 2).extrude(10, both=True).translate((0, y, 0)))
        names = ("bt05", "bt15") if s > 0 else ("bt10",)
        for n in names:
            t = math.radians(TILTS[n])  # the cradle insert at (-LOCK_R, 0) moves to (-R cos t, -R sin t) when pitched up by t
            ch = ch.cut(cq.Workplane("XZ").center(-LOCK_R * math.cos(t), -LOCK_R * math.sin(t))
                        .circle(CLEAR["M4"] / 2).extrude(10, both=True).translate((0, y, 0)))
        b = b.union(ch)
    for s in (-1, 1):
        b = b.cut(cq.Workplane("XY").center(-bx / 2 + 4, s * 60).circle(CLEAR["M4"] / 2).extrude(20, both=True).translate((0, 0, z0)))
    return b


def build():
    return {"gemini_mount": [("MEC-009_base_and_cheeks", base_and_cheeks()), ("MEC-009_cradle_bt10", cradle(TILTS["bt10"]))]}


if __name__ == "__main__":
    run_single(META, build)
