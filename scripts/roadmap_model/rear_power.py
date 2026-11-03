"""Rear power module layout (GI-080, GI-126, GI-129, GI-130): explicit positions, studs, busbars and 25 mm² routes.

Source: the rear power owner's "BMS, Fuse Panel and PDB Layout Report" rev 2 (evans-kwashie, 2 Nov 2026; summary in
openamrobot-docs #68, comment of 3 Nov), implemented and adapted where the measured space needs it (every adaptation is
listed in ADAPTATIONS with its measured reason). Owner decision of 3 Nov 2026: components above the receiver may sit
anywhere with a 15 mm gap to the receiver top (z 117 mm up to the cover). The TZBOT manual asks for no metal within 20 mm of
the receiver, so everything within 20 mm (plate, plate fasteners, standoffs, part feet) is non-metallic (verify with TZBOT).

All values: base_footprint, mm in the tables below (converted to m by layout()). Catalogue outlines marked "verify" are not
in the repositories. The E-01 circuit is unchanged: busbars replace short stud-to-stud cables of the same circuit.

Levels (z, mm above the floor):
  L0  receiver (prepared, installed later) 50 to 102; 15 mm gap
  L1  power plate MEC-006 (G10 glass-epoxy, non-metal) underside 117, top 120: F0, BUS+ (on POM standoffs), K1, K2
  L2  main-line plane 202 (lugs and busbars on the stud tops of F0, QS1, BUS+, K1, K2)
  L3  FB-B shelf 231 to 234 above BUS+ / K1 / K2, FB-B 234 to 282, fuses up, nothing above
  rear: FB-A shelf 205 to 208 at the rear panel (sloped cover), FB-A 208 to 241, fuses up, nothing above
  side gap (right): BMS on edge, z 100 to 166; corners behind the trays: BUS-, Kpre, KCHG, F-CHG, brake suppression
"""
import math

import numpy as np

MM = 0.001

# id: (name, bom, part, geometry source, [x0, x1], [y0, y1], [z0, z1], domain, level, mass kg)
PARTS = {
    "rear_plate": ("Rear power plate MEC-006, G10 glass-epoxy 3 mm (non-metal, within 20 mm of the receiver)", "MEC-006",
                   "G10 / FR4 sheet 3 mm (verify stiffness; ribs or 4 mm if needed)", "proposed outline",
                   [-366, -137], [-95, 95], [117, 120], "MECH", "L1", 0.20),
    "rz_f0": ("Main fuse F0 110 A Class T and holder, across the plate front edge", "PWR-003", "Blue Sea 5007100 + 5112",
              "about 159 x 51 x 58 mm (owner report rev 2, verify)", [-188, -137], [-90, 69], [120, 178], "BAT", "L1", 0.30),
    "rz_pwr017_1": ("Positive distribution block BUS+ (PWR-017), on POM standoffs", "PWR-017", "candidate Blue Sea 2307 (150 A, verify)",
                    "40 x 100 x 40 mm (proposed size, verify)", [-300, -260], [-56.5, 43.5], [156, 196], "BAT", "L1", 0.10),
    "rz_k1k2_1": ("K1 contactor, studs along y", "SAF-003", "Gigavac GX11CAC", "73 x 45 x 76 mm (catalogue outline, verify)",
                  [-255, -210], [-59.5, 13.5], [120, 196], "SAFE", "L1", 0.225),
    "rz_k1k2_2": ("K2 contactor, studs along y", "SAF-003", "Gigavac GX11CAC", "73 x 45 x 76 mm (catalogue outline, verify)",
                  [-255, -210], [18.5, 91.5], [120, 196], "SAFE", "L1", 0.225),
    "rz_fbb": ("SAFE bus fuse block FB-B (F-TRAC 40 A, F-ARM-L 30 A, F-ARM-R 30 A MIDI; F-LIFT 15 A ATO), on the L3 shelf", "FB-B",
               "Blue Sea 7748 SafetyHub 150", "165 x 129 x 48 mm (owner report rev 2, verify)", [-312, -183], [-82.5, 82.5], [234, 282], "SAFE", "L3", 0.45),
    "rz_fba": ("BAT bus fuse block FB-A (F-J401 10 A, F-5V 5 A, F-24V 7.5 A, 5 spare), rear shelf", "FB-A", "Blue Sea 5046 8-way ATO",
               "146 x 44 x 33 mm (owner report rev 2, verify)", [-362, -318], [-10, 136], [208, 241], "BAT", "rear", 0.12),
    "rz_bms": ("Smart BMS Daly M-series 8S 150 A, on edge in the right side gap (service through the right side panel)", "PWR-002",
               "Daly M-series 8S 150 A (order code open)", "164 x 66 x 21 mm catalogue outline (owner report rev 2; verify on the delivered order code)",
               [-283, -119], [-286.5, -265.5], [100, 166], "BAT", "side", 0.45),
    "rz_pwr017_2": ("Negative distribution block BUS- (PWR-017), upright in the right rear corner", "PWR-017", "candidate Blue Sea 2307 (150 A, verify)",
                    "40 x 40 x 100 mm (proposed size, upright, verify)", [-326, -286], [-160, -120], [100, 200], "BAT", "corner", 0.10),
    "rz_pre": ("Precharge kit Kpre + resistor + 1 A fuse (across K2), right rear corner above BUS-", "SAF-004", "Kpre relay, PWR-014 resistor, PWR-015 fuse",
               "80 x 50 x 35 mm (proposed size)", [-366, -286], [-163, -113], [205, 240], "SAFE", "corner", 0.12),
    "rz_kchg": ("Charge relay KCHG, left rear corner", "WCH-004", "24 V coil 1NO + 1NC", "35 x 30 x 30 mm (proposed size)",
                [-330, -295], [98, 128], [57, 87], "BAT", "corner", 0.05),
    "rz_fchg": ("Charge branch fuse F-CHG 30 A MIDI, left rear corner", "PWR-022", "MIDI fuse + holder", "66 x 30 x 32 mm (catalogue outline, verify)",
                [-350, -284], [133, 163], [57, 89], "BAT", "corner", 0.05),
    "rz_brake": ("Brake coil suppression, left rear corner above KCHG", "SAF-007", "matched transient control", "30 x 20 x 15 mm (proposed size)",
                 [-310, -280], [100, 120], [100, 115], "SAFE", "corner", 0.01),
    "rz_disc": ("Lockable battery disconnect QS1 BS-6004B through the rear panel, both M10 studs facing into the robot", "PWR-004", "Blue Sea BS-6004B",
                "67 mm face, 64 mm behind the panel (owner report rev 2, verify)", [-370, -306], [-89.5, -22.5], [158, 225], "BAT", "rear", 0.35),
}
# mounting parts (new, CAD changes): id: (name, [x0, x1], [y0, y1], [z0, z1], material)
MOUNTS = {
    "rp_fbb_shelf": ("FB-B shelf (L3) on four posts from the plate", [-312, -183], [-85, 85], [231, 234], "5052 aluminium 3 mm (more than 20 mm above the receiver); posts POM where they meet the plate"),
    "rp_fba_shelf": ("FB-A shelf on the rear panel and one post", [-364, -316], [-13, 139], [205, 208], "5052 aluminium 3 mm, bracket to the rear panel; post POM"),
    "rp_bus_standoffs": ("BUS+ insulating standoffs (2), plate to block", [-290, -270], [-20, 10], [120, 156], "POM, M6 (verify)"),
    "rp_f0_spacer": ("F0 holder fixing strip", [-188, -137], [-90, 69], [117, 120], "G10 (part of the plate), PA66 screws"),
    "rp_bms_bracket": ("BMS clamp strips on the right side panel (2), PA66 liner", [-275, -127], [-290, -287], [96, 170], "aluminium strip with PA66 liner; rivet nuts in the side panel"),
    "rp_busn_bracket": ("BUS- upright bracket on the rear panel / base sheet", [-330, -286], [-162, -118], [96, 100], "aluminium angle 2 mm"),
    "rp_corner_plate_l": ("Left rear corner mounting plate (KCHG, F-CHG, brake suppression)", [-352, -278], [98, 163], [54, 57], "aluminium 3 mm on the base sheet (outside the receiver margin)"),
}

# studs and terminals (mm): used by the routes, the busbars and the cable list
STUDS = {
    "pack+": [-156, 117, 261], "pack-": [-156, -117, 261],
    "f0_line": [-156, 49, 178], "f0_load": [-156, -70, 178],
    "qs1_s1": [-306, -70, 183], "qs1_s2": [-306, -41.5, 202],
    "bus+_a": [-280, -41.5, 196], "k1_in": [-232.5, -41.5, 196], "k1_out": [-232.5, -4.5, 196],
    "k2_in": [-232.5, 36.5, 196], "k2_out": [-232.5, 73.5, 196], "fbb_in": [-232.5, 82.5, 258],
    "bms_bminus": [-125, -266, 166], "bms_pminus": [-125, -276, 100], "bus-_a": [-286, -140, 110],
}

# 25 mm² cables with a fixed route in the declared exception zone (one 90 degree bend at most, legs >= 63 mm)
FIXED_CABLES = {
    "CBL-P01": [[-156, 117, 268], [-156, 49, 268], [-156, 49, 183]],      # pack + lug, along -y at the lug height, down onto the F0 line stud
    "CBL-P02": [[-156, -70, 183], [-306, -70, 183]],                      # F0 load stud straight back along x to QS1 S1 (90 degree lug at QS1)
}
# insulated copper busbars (E-01 circuit unchanged): cable id, name, section, points
BUSBARS = {
    "CBL-P03": ("BB-01 QS1 S2 to BUS+", "Cu 25 x 4 mm, heat-shrink insulated (verify >= 150 A continuous, creepage)",
                [[-306, -41.5, 202], [-280, -41.5, 202]]),
    "CBL-P04": ("BB-02 BUS+ to K1", "Cu 25 x 4 mm, heat-shrink insulated (verify)", [[-280, -41.5, 202], [-232.5, -41.5, 202]]),
    "CBL-P05": ("BB-03 K1 to K2 (studs facing each other)", "Cu 25 x 4 mm, heat-shrink insulated (verify)", [[-232.5, -4.5, 202], [-232.5, 36.5, 202]]),
    "CBL-P06": ("BB-04 K2 to FB-B input (formed riser beside the L3 shelf)", "Cu 25 x 4 mm, heat-shrink insulated (verify)",
                [[-232.5, 73.5, 202], [-232.5, 89, 202], [-232.5, 89, 258], [-232.5, 82.5, 258]]),
    "CBL-P59": ("BB-05 BMS P- to BUS- (under the BMS, behind the right tray)", "flexible laminated Cu 25 x 3 mm in silicone sleeve (verify ampacity and voltage drop)",
                [[-125, -276, 100], [-125, -276, 78], [-278, -276, 78], [-278, -140, 78], [-278, -140, 110], [-286, -140, 110]]),
    "CBL-P62": ("BB-06 BMS B- to pack - (tray lead, DP-TRAY-R)", "flexible laminated Cu 25 x 3 mm in silicone sleeve (verify)",
                [[-125, -266, 166], [-125, -266, 270], [-162, -266, 270], [-162, -117, 270], [-162, -117, 261]]),
}
BAR_W, BAR_T = 25, 4   # drawn section (mm)

# declared exception zone: the battery and power module (W01 only)
EXCEPTION = {"id": "EZ-W01", "harness": "W01", "lo": [-372, -290, 54], "hi": [-108, 290, 292],
             "why": "battery and power module: short direct links between the trays, BMS, fuses, contactors and distribution blocks "
                    "follow the E-01 schematic and may pass over the top inside this module; insulated, supported, clear of the "
                    "service parts; the trays come out after unplugging PWR-018 and the tray leads (DP-TRAY-L, DP-TRAY-R)"}
SERIES_LINK = {"x": -146, "z": 280, "ends_y": [150, -150], "connector": {"c": [-150, 0, 262], "s": [30, 60, 40]}}

ADAPTATIONS = [
    ("FB-B", "on the plate (owner report)", "L3 shelf above BUS+, K1 and K2, x -312 to -183, z 234 to 282",
     "with F0 across the front edge, the F0 to QS1 run (y -70) and the QS1 to BUS+ to K1 to K2 line (y -41.5) on the plate, the free plate floor "
     "is at most 57 x 190 mm (x -255 to -193 next to the contactors) or 46 x 190 mm behind BUS+; FB-B needs 129 x 165 mm"),
    ("FB-A", "shelf above K1/K2 (owner report)", "rear shelf at the rear panel, x -362 to -318, z 208 to 241",
     "the shelf above K1/K2 is taken by FB-B; at the rear the cover slope leaves 7 mm above FB-A at x -362"),
    ("pack -", "-", "kept at the inner front corner of the right tray", "B- to pack - is a tray lead (BB-06, DP-TRAY-R); unbolted before the right tray lifts out"),
    ("P- (CBL-P59)", "along the tray front to BUS- (owner report)", "BB-05 under the BMS and behind the right tray to BUS- in the right rear corner",
     "the right tray front touches the centre arch (1 mm): a lead along the tray front is inside the tray withdrawal path; under the BMS "
     "(46 mm free) and behind the tray (12 mm gap at the rear support) a flat bar fits"),
    ("series link", "front, x -164 at z 252", "x -146 at z 280, tray ends at the second cell (y +-150), PWR-018 at x -150",
     "the old link ends coincided with pack + and pack - (8 mm); battery owner to confirm the string ends (B-02)"),
]


def mm(v):
    return [round(float(x) * MM, 4) for x in v]


def ceiling(x):
    import rear_layout
    return rear_layout.ceiling(x)


def boxes():
    out = {}
    for k, (nm, bom, part, geom, xs, ys, zs, dom, lvl, mass) in PARTS.items():
        out[k] = (np.array([xs[0], ys[0], zs[0]]) * MM, np.array([xs[1], ys[1], zs[1]]) * MM)
    return out


def fit_check(obstacles=None, receiver=None, trays=None):
    """Clearances between the module parts, to the cover, the trays and the given fixed obstacles; parts within 20 mm of the
    receiver; returns a report dict (mm)."""
    B = boxes()
    for k, (nm, xs, ys, zs, mat) in MOUNTS.items():
        B[k] = (np.array([xs[0], ys[0], zs[0]]) * MM, np.array([xs[1], ys[1], zs[1]]) * MM)
    gaps, clashes = [], []

    def gap(a, b):
        d = np.maximum(0, np.maximum(a[0] - b[1], b[0] - a[1]))
        return float(np.linalg.norm(d)) * 1000

    allowed = {("rp_fbb_shelf", "rz_fbb"), ("rp_fba_shelf", "rz_fba"), ("rp_bus_standoffs", "rz_pwr017_1"), ("rp_bus_standoffs", "rear_plate"),
               ("rp_f0_spacer", "rz_f0"), ("rp_f0_spacer", "rear_plate"), ("rear_plate", "rz_f0"), ("rear_plate", "rz_k1k2_1"), ("rear_plate", "rz_k1k2_2"),
               ("rp_bms_bracket", "rz_bms"), ("rp_busn_bracket", "rz_pwr017_2"), ("rp_corner_plate_l", "rz_kchg"), ("rp_corner_plate_l", "rz_fchg")}
    plate_tray_ok = ("rear_plate", "left_tray"), ("rear_plate", "right_tray")   # 2 mm, recorded A1 plate outline between the trays
    ks = sorted(B)
    for i, a in enumerate(ks):
        for b in ks[i + 1:]:
            g = gap(B[a], B[b])
            if (a, b) in allowed or (b, a) in allowed:
                continue
            gaps.append((g, a, b))
            if g < 4.99:
                clashes.append("%s / %s %.1f mm" % (a, b, g))
    for k, (lo, hi) in B.items():
        c = min(ceiling(lo[0]), ceiling(hi[0]))
        if hi[2] > c - 0.003 + 1e-9:
            clashes.append("%s top %.0f mm, cover %.0f mm" % (k, hi[2] * 1000, c * 1000))
    for nm, (lo, hi) in (obstacles or {}).items():
        lo, hi = np.asarray(lo), np.asarray(hi)
        for k, b in B.items():
            g = gap(b, (lo, hi))
            gaps.append((g, k, nm))
            if g < 2.99 and (k, nm) not in plate_tray_ok:
                clashes.append("%s / %s %.1f mm" % (k, nm, g))
    near = []
    if receiver is not None:
        rlo, rhi = np.asarray(receiver[0]), np.asarray(receiver[1])
        for k, b in B.items():
            g = gap(b, (rlo, rhi))
            if g < 20 - 1e-6:
                near.append({"part": k, "gap_mm": round(g, 1)})
    gaps.sort()
    return {"clashes": clashes, "closest": [{"a": a, "b": b, "gap_mm": round(g, 1)} for g, a, b in gaps[:12]], "within_20mm_of_receiver": near}


def main_path():
    """The 25 mm² main path, lengths and bends (mm), cables and busbars in order."""
    out = []
    for cid in ("CBL-P01", "CBL-P02"):
        pts = FIXED_CABLES[cid]
        out.append({"id": cid, "kind": "25 mm² cable", "polyline_mm": round(_plen(pts), 1), "bends_90": len(pts) - 2,
                    "legs_mm": [round(_plen(pts[i:i + 2]), 1) for i in range(len(pts) - 1)],
                    "length_on_r63_mm": round(_plen(pts) - (len(pts) - 2) * (2 * 63 - math.pi / 2 * 63), 1)})
    for cid, (nm, sec, pts) in BUSBARS.items():
        out.append({"id": cid, "kind": "busbar " + nm.split()[0], "polyline_mm": round(_plen(pts), 1), "bends_90": len(pts) - 2, "section": sec})
    return out


def _plen(pts):
    return sum(math.dist(pts[i], pts[i + 1]) for i in range(len(pts) - 1))


def layout():
    """Everything in metres for build.py and harness.py."""
    return {"parts": {k: {"name": v[0], "bom": v[1], "part": v[2], "geom": v[3], "lo": mm([v[4][0], v[5][0], v[6][0]]), "hi": mm([v[4][1], v[5][1], v[6][1]]),
                          "domain": v[7], "level": v[8], "mass": v[9]} for k, v in PARTS.items()},
            "mounts": {k: {"name": v[0], "lo": mm([v[1][0], v[2][0], v[3][0]]), "hi": mm([v[1][1], v[2][1], v[3][1]]), "material": v[4]} for k, v in MOUNTS.items()},
            "studs": {k: mm(v) for k, v in STUDS.items()},
            "fixed_cables": {k: [mm(p) for p in v] for k, v in FIXED_CABLES.items()},
            "busbars": {k: {"name": v[0], "section": v[1], "pts": [mm(p) for p in v[2]]} for k, v in BUSBARS.items()},
            "exception": dict(EXCEPTION, lo=mm(EXCEPTION["lo"]), hi=mm(EXCEPTION["hi"])),
            "series_link": SERIES_LINK, "adaptations": ADAPTATIONS}


if __name__ == "__main__":
    import json
    import rear_layout
    RL = rear_layout.layout()
    from frames import glb_nodes
    G = glb_nodes()
    obst = {t["side"] + "_tray": (t["lo"], t["hi"]) for t in RL["trays"]}
    for k in ("support_rear_left", "support_rear_right", "ultrasonic_mount_rear_left", "ultrasonic_mount_rear_right", "tof_mount_rear", "hub_motor_wheel_right"):
        v = np.array(G[k]["v"])
        obst[k] = (v.min(0), v.max(0))
    obst["pwr018"] = (np.array(SERIES_LINK["connector"]["c"]) * MM - np.array(SERIES_LINK["connector"]["s"]) * MM / 2,
                      np.array(SERIES_LINK["connector"]["c"]) * MM + np.array(SERIES_LINK["connector"]["s"]) * MM / 2)
    print(json.dumps(fit_check(obst, RL["receiver"]), indent=1))
    print(json.dumps(main_path(), indent=1))
