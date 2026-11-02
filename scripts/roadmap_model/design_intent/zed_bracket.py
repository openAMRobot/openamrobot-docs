# SPDX-License-Identifier: MIT
"""d. ZED Mini pitch bracket on the arm-post top (ARM-011 adapter), design intent.

The supplied ZED mount (1/4-20 UNC) screws to a pivoting cradle. The pivot axis runs along y through the
lens line, so the lens stays 42 mm ahead of and 223 mm above J1_A (1223 mm above the floor at L1000) in
every position. Locked positions hp15 to hp35 in 5 deg steps (hp30 default): one M4 screw per side into
a tapped hole in the cradle arm on a 40 mm radius; the left cheek carries hp15 / hp25 / hp35, the right
cheek hp20 / hp30 (holes 7 mm apart). Manufacturing: machined 6082-T6, foot 6 mm, cheeks and cradle 5 mm.
Local frame: origin at the lens-line centre, x forward, z up; pitch down is positive about y.
"""
import math
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, run_single  # noqa: E402

ZED = (26.5, 124.5, 30.5)      # ZED Mini depth x width x height (datums.yaml head_camera_size)
LENS_AHEAD = 42.0              # lens ahead of J1_A / the post centre (P-03 rev20.0, upperbody-sw #22)
LENS_ABOVE_POST_TOP = 39.0     # 1223 - 1184 (post top at L1000: 304 + 530 + 10 + 340)
POST = (120.0, 60.0)           # HFS6-60120 section, x x y; post centre 180 mm ahead of the column axis
LENS_FROM_POST_FRONT = POST[0] / 2 - LENS_AHEAD   # 18 mm behind the post front face
PITCHES = (15, 20, 25, 30, 35)  # hp positions, deg down; hp30 default
DEFAULT = 30
LOCK_R = 40.0
FOOT_T, PLATE_T = 6.0, 5.0
CHEEK_Y = ZED[1] / 2 + 2.0 + PLATE_T + PLATE_T / 2   # cheek centre; the cradle arm sits between the ZED (2 mm gap) and the cheek

META = {
    "item": "zed_bracket", "bom": "ARM-011", "method": "machined 6082-T6", "material": "6082-T6", "thickness_mm": PLATE_T,
    "existing_cad": None,
    "configuration": "L1000, hp30",
    "adjustment": "pitch hp15 to hp35 in 5 deg steps about the lens line, M4 lock screw (staggered holes, left 15/25/35, right 20/30)",
    "placement": [{"name": "lens_line", "xyz": [0.282, 0.0, 1.223], "rpy": [0.0, math.radians(DEFAULT), 0.0]}],
    "placement_note": "column axis x 0.060 (bp000) + 0.180 + 0.042; z 0.304 + 0.530 + 0.166 + 0.223 at L1000",
    "fasteners": [
        {"joint": "foot to post top", "part": "ISO 4762 screw + ISO 7089 washer into the post end tap", "size": "M8 x 16", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "cradle pivot", "part": "ISO 4762 screw + ISO 7089 washers + ISO 10511 nyloc nut", "size": "M5 x 16", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "pitch lock", "part": "ISO 4762 screw + ISO 7089 washer into M4 tapped cradle arm", "size": "M4 x 10", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "ZED mount to cradle", "part": "1/4-20 UNC screw (supplied with the ZED mount)", "size": "1/4-20 x 3/8in", "qty": 1, "standard": "ASME B18.3", "class": "named"},
    ],
    "next_step": "CAD owner: confirm the HFS6-60120 end-tap size in the order code and the ZED Mini mount interface; check the bracket against the arm sweep at hp35.",
}


def foot_and_cheeks():
    z0 = -LENS_ABOVE_POST_TOP
    xc = LENS_FROM_POST_FRONT - POST[0] / 2   # post centre in the lens frame (-42)
    f = cq.Workplane("XY").box(POST[0], 2 * CHEEK_Y + PLATE_T, FOOT_T).translate((xc, 0, z0 + FOOT_T / 2))
    for x in (xc - 30, xc + 30):
        f = f.cut(cq.Workplane("XY").center(x, 0).circle(CLEAR["M8"] / 2).extrude(50, both=True))
    for s in (-1, 1):
        y = s * CHEEK_Y
        ch = cq.Workplane("XZ").center(-22, (z0 + 12) / 2).rect(64, abs(z0) + 12).extrude(PLATE_T / 2, both=True)
        ch = ch.union(cq.Workplane("XZ").circle(9).extrude(PLATE_T / 2, both=True))
        ch = ch.cut(cq.Workplane("XZ").circle(CLEAR["M5"] / 2).extrude(10, both=True))
        hp = (15, 25, 35) if s > 0 else (20, 30)
        for p in hp:
            a = math.radians(p)
            ch = ch.cut(cq.Workplane("XZ").center(-LOCK_R * math.cos(a), LOCK_R * math.sin(a)).circle(CLEAR["M4"] / 2).extrude(10, both=True))
        f = f.union(ch.translate((0, y, 0)))
    return f


def cradle(p):
    d, w, h = ZED
    c = cq.Workplane("XY").box(d + 4, 2 * (CHEEK_Y - PLATE_T) + PLATE_T, PLATE_T).translate((-d / 2, 0, -h / 2 - PLATE_T / 2))
    c = c.cut(cq.Workplane("XY").center(-d / 2, 0).circle(6.6 / 2).extrude(30, both=True))  # 1/4-20 clearance
    for s in (-1, 1):
        y = s * (CHEEK_Y - PLATE_T)
        arm = cq.Workplane("XZ").center(-LOCK_R / 2, 0).rect(LOCK_R + 8, 10).extrude(PLATE_T / 2, both=True)
        arm = arm.union(cq.Workplane("XZ").center(0, -h / 4).rect(12, h / 2 + 2).extrude(PLATE_T / 2, both=True))
        arm = arm.cut(cq.Workplane("XZ").circle(CLEAR["M5"] / 2).extrude(10, both=True))
        arm = arm.cut(cq.Workplane("XZ").center(-LOCK_R, 0).circle(3.3 / 2).extrude(10, both=True))  # M4 tap drill
        c = c.union(arm.translate((0, y, 0)))
    return c.rotate((0, 0, 0), (0, 1, 0), p)


def build():
    return {"zed_bracket": [("ARM-011_foot_and_cheeks", foot_and_cheeks()), ("ARM-011_cradle_hp%d" % DEFAULT, cradle(DEFAULT))]}


if __name__ == "__main__":
    run_single(META, build)
