"""Flag rod guide (owner decision of 3 Nov 2026): a second support for the flag rod at the top of the static lift column.

The rod stays bolted to the moving adapter-plate rear extension (first support, with its corner bracket) and slides through an
open guide ring fixed to the static column head (second support). The ring is a U open toward -y: it wraps the rear (-x), the
column-side (+x) and the +y faces of the 20 mm rod and leaves the -y face open, the side that faces the IME12 sensors and
carries the flag, so the flag and the sensor bodies pass the opening at every lift position. The arm reaches the ring around
the +y side of the rod (not through the space between the rod and the column, where the corner bracket is) and is screwed to
the +y face of the static column at its head.

Frame: column frame of frames.lift_rear_layout() for x (x from the column axis), base_footprint y and z (static parts at their
height; the rod and its brackets at travel T). Units m. The wall, liner and clearance values are proposals to verify.
"""
import math

import numpy as np

from frames import FACTS, lift_rear_layout

CLEAR = 0.0003       # running clearance per side between the rod and the liner (proposed, verify against the profile tolerance)
LINER = 0.0005       # PTFE liner, bonded (proposed; UHMW-PE 1 mm is the alternative where the wall can grow)
WALL = 0.0015        # stainless U wall 1.5 mm (1.4301), laser cut and bent (proposed)
ARM_T = 0.003        # 6082-T6 arm 3 mm on the +y side of the ring
H = 0.020            # guide height
STEP = 0.025         # travel step of the checks (m)


def layout(chain=None):
    """Guide boxes (column frame x, base y, z) and the clearance checks over the stroke. chain: harness.energy_chain() dict
    (x in base frame) for the chain clearance; None skips it."""
    F = FACTS
    LR = lift_rear_layout()
    f = F["lift_rear"]
    ax = F["lift_plate"]["col_axis_x"]["bp000"]
    top0 = F["lift_plate"]["top"] + F["column"]["retracted"]          # static column head and adapter-plate underside at L1000
    stroke = F["column"]["stroke"]
    rx0, rx1 = LR["rod_x"]
    ry0, ry1 = LR["rod_y"]
    cl = LR["corner_x"][1] - LR["corner_x"][0]
    corner_bottom_L1000 = top0 - 0.003 - cl                            # corner bracket lowest point at L1000
    flag_top_L1350 = top0 + stroke - f["flag_below_plate"] + f["flag"][2] / 2
    band = (flag_top_L1350, corner_bottom_L1000)
    z0 = (band[0] + band[1]) / 2 - H / 2
    z1 = z0 + H
    i0, i1 = rx0 - CLEAR - LINER, rx1 + CLEAR + LINER                    # liner inner faces in x
    iy = ry1 + CLEAR + LINER                                              # liner inner face on +y
    o0, o1, oy = i0 - WALL, i1 + WALL, iy + WALL                          # wall outer faces
    col_y = F["column"]["section"][1] / 2                                 # static column +y face
    rear = f["column_rear_x"]
    boxes = {
        "ring_rear_wall": ([o0, ry0, z0], [i0, oy, z1]),                  # -x wall (toward the energy chain)
        "ring_front_wall": ([i1, ry0, z0], [o1, oy, z1]),                 # +x wall (toward the column)
        "ring_side_wall": ([i0, iy, z0], [i1, oy, z1]),                   # +y wall
        "liner_rear": ([i0, ry0, z0], [i0 + LINER, iy, z1]),              # PTFE liner strips on the three wrapped faces
        "liner_front": ([i1 - LINER, ry0, z0], [i1, iy, z1]),
        "liner_side": ([i0, iy - LINER, z0], [i1, iy, z1]),
        "arm": ([o0, oy, z0], [rear + 0.035, oy + ARM_T, z1]),            # along x on the +y side, past the rear face of the column
        "foot": ([rear + 0.005, col_y, z0 - 0.010], [rear + 0.035, oy, z1 + 0.010]),   # spacer block to the column +y face
    }
    out = {"boxes": {k: [[round(v, 4) for v in a], [round(v, 4) for v in b]] for k, (a, b) in boxes.items()},
           "z": [round(z0, 4), round(z1, 4)], "band": [round(band[0], 4), round(band[1], 4)],
           "band_margin_mm": [round((z0 - band[0]) * 1000, 1), round((band[1] - z1) * 1000, 1)],
           "opening": "-y face open (sensor and flag side), width %.1f mm" % ((ry1 - ry0 + 2 * CLEAR) * 1000),
           "clearance_mm": CLEAR * 1000, "liner": "PTFE 0.5 mm bonded (verify; UHMW-PE alternative)", "wall": "stainless 1.4301, 1.5 mm, U bent",
           "arm": "6082-T6 3 mm plate on the +y side of the ring; spacer block to the static column +y face",
           "fasteners": [("arm and spacer to the static column +y face", "ISO 4762 + M5 T-slot nut", "M5 x 30", 2),
                         ("U ring to the arm", "ISO 7380 + nut (or rivets)", "M3 x 8", 2)],
           "rod_x_base": [round(rx0 + ax, 4), round(rx1 + ax, 4)], "z_base": [round(z0, 4), round(z1, 4)]}
    # checks over the stroke
    LRs = LR
    sens = []
    s, b = f["sensor"], f["bracket"]
    for zs in f["sensor_z"]:
        z = F["lift_plate"]["top"] + zs
        sens.append(("sensor %d mm" % round(zs * 1000), [LRs["sensor_axis_x"] - s["d"] / 2, -LRs["face_y"], z - s["d"] / 2], [LRs["sensor_axis_x"] + s["d"] / 2, LRs["face_y"], z + s["d"] / 2]))
        sens.append(("sensor bracket %d mm" % round(zs * 1000), [rear - b["leg"], -b["leg"], z - b["h"] / 2], [rear, 0.0, z + b["h"] / 2]))
    gbox = [(np.array(a), np.array(bb)) for a, bb in boxes.values()]

    def gap(lo, hi):
        return min(float(np.linalg.norm(np.maximum(0, np.maximum(np.array(lo) - g[1], g[0] - np.array(hi))))) for g in gbox)

    rows = []
    for T in [round(i * STEP, 3) for i in range(int(round(stroke / STEP)) + 1)]:
        c = top0 + T
        rod = ([rx0, ry0, c - f["rod"]["len"]], [rx1, ry1, c])
        flag = ([LRs["flag_x"][0], LRs["flag_y"][0], c - f["flag_below_plate"] - f["flag"][2] / 2], [LRs["flag_x"][1], LRs["flag_y"][1], c - f["flag_below_plate"] + f["flag"][2] / 2])
        corner = ([LRs["corner_x"][0], ry0, c - 0.003 - cl], [LRs["corner_x"][1], ry1, c])
        engaged = rod[0][2] <= z0 - 1e-9 and rod[1][2] >= z1 - 1e-9
        r = {"T": T, "rod_engaged": engaged, "rod_below_guide_mm": round((z0 - rod[0][2]) * 1000, 1), "flag_to_guide_mm": round(gap(*flag) * 1000, 1),
             "corner_to_guide_mm": round(gap(*corner) * 1000, 1), "flag_to_sensor_face_mm": round((LRs["flag_y"][0] - LRs["face_y"]) * 1000, 1),
             "sensors_to_guide_mm": round(min(gap(lo, hi) for _, lo, hi in sens) * 1000, 1)}
        if chain is not None:
            st = min(chain["stops"], key=lambda q: abs(q["T"] - T))
            x0, x1 = chain["x"] - chain["outer_w"] / 2 - ax, chain["x"] + chain["outer_w"] / 2 - ax
            hh = chain["outer_h"] / 2
            zc = st["loop_centre_z"]
            env = [([x0, chain["y_fixed"] - hh, zc], [x1, chain["y_fixed"] + hh, chain["fixed_z"]]),
                   ([x0, chain["y_moving"] - hh, zc], [x1, chain["y_moving"] + hh, st["moving_end_z"]]),
                   ([x0, -chain["R"] - hh, zc - chain["R"] - hh], [x1, chain["R"] + hh, zc])]
            r["chain_to_guide_mm"] = round(min(gap(lo, hi) for lo, hi in env) * 1000, 1)
            r["chain_to_rod_mm"] = round(min(float(np.linalg.norm(np.maximum(0, np.maximum(np.array(lo) - np.array(rod[1]), np.array(rod[0]) - np.array(hi))))) for lo, hi in env) * 1000, 1)
        rows.append(r)
    out["checks"] = rows
    key = lambda k: min(r[k] for r in rows if k in r)
    out["summary"] = {"rod_engaged_all": all(r["rod_engaged"] for r in rows), "min_rod_below_guide_mm": key("rod_below_guide_mm"),
                      "min_flag_to_guide_mm": key("flag_to_guide_mm"), "min_corner_to_guide_mm": key("corner_to_guide_mm"),
                      "flag_to_sensor_face_mm": rows[0]["flag_to_sensor_face_mm"], "min_sensors_to_guide_mm": key("sensors_to_guide_mm")}
    if chain is not None:
        out["summary"]["min_chain_to_guide_mm"] = key("chain_to_guide_mm")
        out["summary"]["min_chain_to_rod_mm"] = key("chain_to_rod_mm")
    out["summary"]["ok"] = (out["summary"]["rod_engaged_all"] and out["summary"]["min_flag_to_guide_mm"] >= 2.0 and out["summary"]["min_corner_to_guide_mm"] >= 2.0
                            and out["summary"]["min_sensors_to_guide_mm"] >= 5.0 and out["summary"].get("min_chain_to_guide_mm", 9) >= 5.0)
    out["removal"] = ("rod removal: stop the lift between the stops (flag between two sensors), remove the M5 rod screw and the corner bracket, "
                      "slide the rod out of the guide through its open -y side (the rod clears the sensor bodies by %.0f mm in x), then lower it" % ((LRs["sensor_axis_x"] - s["d"] / 2 - rx1) * 1000))
    return out


if __name__ == "__main__":
    import json
    import harness
    from frames import datums
    rev, D = datums()
    U = {"col_axis_x": FACTS["lift_plate"]["col_axis_x"]["bp000"], "col_top": FACTS["lift_plate"]["top"] + FACTS["column"]["retracted"]}
    G = layout(harness.energy_chain(U, FACTS))
    print(json.dumps({k: G[k] for k in ("z", "band", "band_margin_mm", "summary", "boxes", "removal")}, indent=1))
