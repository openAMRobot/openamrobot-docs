# SPDX-License-Identifier: MIT
"""g. Lift adapter plate, vertical arm post, rear upright, stiffener and flag-rod mount (MEC-004, MEC-003), design intent.

Adapter plate: 6082-T6, 360 x 100 x 10 mm, machined, on the DOLD carriage; rear edge flush with the column
rear face, front edge 120 mm ahead of the column front face. A rear-left wing (40 x 35 mm, same plate)
keeps the LFT-004 flag rod inside the plate footprint: with the 100 mm plate the rod (y 60 to 80 mm from
the column axis) hangs 10 to 30 mm outside (P-03 simulation finding of 29 Oct).
Arm post: MISUMI HFS6-60120, 340 mm, end-tapped, vertical, 120 deep in x, 60 wide in y, centred 180 mm ahead
of the column axis, front face flush with the plate front; bolted from below through the plate.
Rear upright 10 mm and a 10 mm gusset (stiffener), both 6082-T6, on M6 T-nuts in the post rear slots and
bolted from below through the plate. OpenArm J1_A on the post side faces at y +/-31 mm (1 mm spacer each
side), 166 mm above the carriage reference (the adapter-plate underside).
Local frame: origin at the adapter-plate underside on the column axis, x forward, z up.
"""
import os
import sys

import cadquery as cq

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from _common import CLEAR, CSK_DIA, run_single  # noqa: E402

COL_HALF_X = 120.0                  # DOLD column 240 fore-aft
PLATE = (360.0, 100.0, 10.0)        # B7 adapter plate
POST = (120.0, 60.0, 340.0)         # HFS6-60120 x, y, length
POST_X = 180.0                      # post centre ahead of the column axis
J1_Z = 166.0                        # J1_A above the carriage reference
SPACER = (1.0, 90.0, 90.0)          # J1 spacer y thickness, x, z (outline as drawn in the docs model; hole pattern from the OpenArm mount, not drawn)
UPRIGHT = (10.0, 60.0, 150.0)       # rear upright x, y, z
GUSSET = (80.0, 10.0, 120.0)        # stiffener x leg, thickness, z leg
ROD = (20.0, 430.0)                 # LFT-004 section and length
ROD_XY = (-109.0, 70.0)             # rod centre from the column axis (datums.yaml lift_stop_sensor_face_x - gap - flag - rod/2; 30 + 30 + 10)
WING = (40.0, 35.0)                 # wing x length (from the plate rear edge), y extension beyond the 50 mm half width
CARRIAGE_PATTERN = (190.0, 30.0)    # DOLD carriage screw pattern: PLACEHOLDER (DOLD drawing not read)
CARRIAGE_Z_L1000 = 0.834            # 0.304 + 0.530

META = {
    "mass_note": "HFS6-60120 post drawn as a solid envelope and excluded from mass_kg: take the MISUMI catalogue mass per metre x 0.34 m",
    "materials": {"adapter_plate": "6082-T6", "rear_upright": "6082-T6", "stiffener": "6082-T6", "spacer": "5754-H22"},
    "item": "adapter_post", "bom": "MEC-004, MEC-003, LFT-004 mount", "method": "machined 6082-T6 plates; MISUMI HFS6-60120 profile cut and end-tapped",
    "material": "6082-T6", "thickness_mm": PLATE[2],
    "existing_cad": None,
    "configuration": "L1000, bp000",
    "adjustment": "post and upright on T-nuts (height of the upright adjustable); rod clamped in the wing with one M5",
    "placement": [{"name": "carriage_reference", "xyz": [0.060, 0.0, CARRIAGE_Z_L1000], "rpy": [0, 0, 0]}],
    "placement_note": "post spans z 0.844 to 1.184 at L1000; J1_A at z 1.000; L1175 / L1350 add 0.175 / 0.350",
    "fasteners": [
        {"joint": "adapter plate to DOLD carriage", "part": "ISO 10642 countersunk screw (from the top)", "size": "M8 x 20", "qty": 4, "standard": "ISO 10642", "class": "proposed"},
        {"joint": "post to adapter plate (from below)", "part": "ISO 4762 screw + ISO 7089 washer into the post end tap", "size": "M8 x 25", "qty": 2, "standard": "ISO 4762", "class": "named"},
        {"joint": "rear upright to post", "part": "ISO 4762 screw + M6 T-slot nut (HFS6)", "size": "M6 x 16", "qty": 4, "standard": "ISO 4762", "class": "named"},
        {"joint": "rear upright to plate (from below)", "part": "ISO 4762 screw into tapped upright", "size": "M6 x 20", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "stiffener to upright", "part": "ISO 4762 screw into tapped gusset", "size": "M6 x 20", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "stiffener to plate (from below)", "part": "ISO 4762 screw into tapped gusset", "size": "M6 x 20", "qty": 2, "standard": "ISO 4762", "class": "proposed"},
        {"joint": "J1_A spacer", "part": "1 mm spacer plate (aluminium)", "size": "90 x 90 x 1", "qty": 2, "standard": "-", "class": "named"},
        {"joint": "flag rod to wing", "part": "ISO 4762 screw into the M5 tapped rod end (LFT-007)", "size": "M5 x 20", "qty": 1, "standard": "ISO 4762", "class": "named"},
    ],
    "next_step": "CAD owner: read the DOLD carriage screw pattern; check the wing against the second E-stop housing and the lift cable; M-09.",
}


def plate():
    lx, ly, t = PLATE
    x0, x1 = -COL_HALF_X, -COL_HALF_X + lx
    p = cq.Workplane("XY").box(lx, ly, t).translate(((x0 + x1) / 2, 0, t / 2))
    wing = cq.Workplane("XY").box(WING[0], WING[1], t).translate((x0 + WING[0] / 2, ly / 2 + WING[1] / 2, t / 2))
    p = p.union(wing)
    for x in (POST_X - 30, POST_X + 30):                     # post bolts from below
        p = p.cut(cq.Workplane("XY").center(x, 0).circle(CLEAR["M8"] / 2).extrude(30, both=True))
    for sx in (-1, 1):                                       # carriage screws, countersunk from the top
        for sy in (-1, 1):
            c = (sx * CARRIAGE_PATTERN[0] / 2, sy * CARRIAGE_PATTERN[1] / 2)
            p = p.cut(cq.Workplane("XY").center(*c).circle(CLEAR["M8"] / 2).extrude(30, both=True))
            p = p.cut(cq.Workplane().add(cq.Solid.makeCone(CLEAR["M8"] / 2, CSK_DIA["M8"] / 2, (CSK_DIA["M8"] - CLEAR["M8"]) / 2,
                                                            cq.Vector(c[0], c[1], t - (CSK_DIA["M8"] - CLEAR["M8"]) / 2 + 0.01), cq.Vector(0, 0, 1))))
    p = p.cut(cq.Workplane("XY").center(*ROD_XY).circle(CLEAR["M5"] / 2).extrude(30, both=True))  # rod screw
    for x in (POST_X - UPRIGHT[0] / 2 - POST[0] / 2 - 0, ):
        for y in (-15.0, 15.0):
            p = p.cut(cq.Workplane("XY").center(x, y).circle(CLEAR["M6"] / 2).extrude(30, both=True))
    gx = POST_X - POST[0] / 2 - UPRIGHT[0] - GUSSET[0]
    for x in (gx + 15, gx + 55):
        p = p.cut(cq.Workplane("XY").center(x, 0).circle(CLEAR["M6"] / 2).extrude(30, both=True))
    return p


def post():
    x, y, l = POST
    return cq.Workplane("XY").box(x, y, l).edges("|Z").fillet(3).translate((POST_X, 0, PLATE[2] + l / 2))


def upright_and_gusset():
    ux = POST_X - POST[0] / 2 - UPRIGHT[0] / 2
    u = cq.Workplane("XY").box(*UPRIGHT).translate((ux, 0, PLATE[2] + UPRIGHT[2] / 2))
    gx1 = POST_X - POST[0] / 2 - UPRIGHT[0]
    g = (cq.Workplane("XZ").polyline([(gx1, PLATE[2]), (gx1, PLATE[2] + GUSSET[2]), (gx1 - GUSSET[0], PLATE[2])]).close()
         .extrude(GUSSET[1] / 2, both=True))
    return u, g


def spacers():
    out = []
    for s in (-1, 1):
        out.append(cq.Workplane("XY").box(SPACER[1], SPACER[0], SPACER[2]).translate((POST_X, s * (POST[1] / 2 + SPACER[0] / 2), J1_Z)))
    return out


def rod():
    w, l = ROD
    r = cq.Workplane("XY").box(w, w, l).translate((ROD_XY[0], ROD_XY[1], -l / 2))
    return r


def build():
    u, g = upright_and_gusset()
    sl, sr = spacers()
    return {"adapter_post": [("MEC-004_adapter_plate", plate()), ("MEC-003_arm_post_HFS6-60120_envelope", post()),
                             ("MEC-004_rear_upright", u), ("MEC-004_stiffener", g), ("MEC-004_J1A_spacer_left", sr),
                             ("MEC-004_J1A_spacer_right", sl), ("LFT-004_flag_rod_ref", rod())]}


if __name__ == "__main__":
    run_single(META, build)
