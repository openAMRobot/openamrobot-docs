"""Rear section layout, owner correction A1 (owner, 2 Nov 2026; to be entered in P-03 and M-01).

TZBOT WCM-500-24 receiver reserved (not installed in 2.0) on the centre line, 170 mm along x and 150 mm across y, as close to the
rear panel inner face as possible without touching the rear TF-Luna, the rear MB7060s, their mounts or the rear panel flange
(owner correction of 2 Nov 2026; the 240 x 210 mm zone is withdrawn), bottom 2 mm below the base-sheet underside; 20 mm
metal-free margin around the receiver. Two side pockets beside the zone, each with 4 EVE LF105 cells upright (8S). Power electronics on a
mounting plate above the receiver, underside at least 20 mm above the receiver top, up to the cover underside.

The space is measured from the CAD (base GLB): rear panel, arch, top-cover supports, side panels and their return flanges
(GI-025), rear sensor mounts and the rear cover flange slope. layout() returns every box (base_footprint, m) and a report
with the CAD v0.2 dimensions as the reference (A9), and the cell arrangement chosen for each pocket.
"""
import itertools

import numpy as np

from frames import FACTS, glb_nodes

_L = None


def _box(lo, hi):
    return np.array(lo, float), np.array(hi, float)


def overlap(a, b, e=1e-6):
    return bool((np.minimum(a[1], b[1]) - np.maximum(a[0], b[0]) > e).all())


def ceiling(x):
    """Cover underside over the rear section: flat 0.290 ahead of x -0.315, then the rear flange slope to 0.232 at x -0.386."""
    cu = FACTS["cover_underside"]
    return cu if x > -0.315 else cu - (-0.315 - x) * (0.0628 / 0.0706)


def layout():
    global _L
    if _L is not None:
        return _L
    G = glb_nodes()
    bb = {k: (G[k]["v"].min(0), G[k]["v"].max(0)) for k in G}
    RS = FACTS["rear_section"]
    RX = FACTS["tzbot_receiver"]
    C = FACTS["cells"]
    mc = RX["metal_clear"]
    x_rear, x_arch = RS["rear_panel_inner_x"], RS["arch_edge_x"]
    sx, sy, sz = RX["size"]   # 170 along x, 150 across y, 52 tall
    z0 = FACTS["base_sheet"]["bottom"] - RX["below_base_sheet"]
    # rearmost x the receiver may start at: in front of every rear body whose y and z overlap the receiver (+ touch clearance)
    rear_ids = ["rear_panel", "tof_rear", "tof_mount_rear", "ultrasonic_rear_left", "ultrasonic_rear_right",
                "ultrasonic_mount_rear_left", "ultrasonic_mount_rear_right", "support_rear_left", "support_rear_right"]
    clear_to, x0 = {}, -1.0
    for k in rear_ids:
        lo_, hi_ = bb[k]
        if hi_[1] > -sy / 2 and lo_[1] < sy / 2 and hi_[2] > z0 and lo_[2] < z0 + sz:
            x0 = max(x0, float(hi_[0]))
    x0 = round(x0 + RX["touch_clear"], 4)
    rx = _box([x0, -sy / 2, z0], [x0 + sx, sy / 2, z0 + sz])
    for k in rear_ids:
        lo_, hi_ = bb[k]
        gap = np.maximum(0, np.maximum(rx[0], lo_) - np.minimum(rx[1], hi_))
        clear_to[k] = round(float(np.linalg.norm(gap)) * 1000, 1)
    zone = _box([x_rear, -sy / 2 - mc, z0], [x_arch, sy / 2 + mc, FACTS["cover_underside"]])
    margin = _box(rx[0] - mc, rx[1] + mc)
    cut = _box([max(margin[0][0], x_rear), margin[0][1], FACTS["base_sheet"]["bottom"]], [margin[1][0], margin[1][1], FACTS["base_sheet"]["top"]])
    metal_in_margin = {k: clear_to[k] for k in clear_to if clear_to[k] < mc * 1000}
    plate_z = round(float(rx[1][2] + RS["power_plate"]["min_above_receiver"]), 4)
    plate = _box([x_rear + 0.004, margin[0][1], plate_z], [x_arch - 0.002, margin[1][1], plate_z + RS["power_plate"]["t"]])
    # measured space: the CAD v0.2 dimensions are the reference (A9)
    sup_l, sup_r = bb["support_rear_left"], bb["support_rear_right"]
    v = G["side_panel_left"]["v"]
    wall_in = float(v[(np.abs(v[:, 0]) < 0.3) & (v[:, 1] > 0.25), 1].min())
    measured = {"between_supports_mm": round((sup_l[0][1] - sup_r[1][1]) * 1000, 1),
                "between_side_walls_mm": round(2 * wall_in * 1000, 1),
                "rear_panel_to_arch_mm": round((x_arch - x_rear) * 1000, 1),
                "support_depth_from_rear_panel_mm": round((sup_l[1][0] - x_rear) * 1000, 1),
                "flange_line_y": 0.193, "flanges_z": [[0.051, 0.074], [0.191, 0.214]], "side_wall_inner_y": round(wall_in, 4)}
    # obstacles of one pocket (left side; the right side mirrors it)
    def obst_left(flanges=True):
        ob = [("support_rear_left", bb["support_rear_left"]), ("ultrasonic_mount_rear_left", bb["ultrasonic_mount_rear_left"]),
              ("ultrasonic_rear_left", bb["ultrasonic_rear_left"]), ("metal_free_margin", (margin[0], margin[1])),
              ("arch", _box([x_arch, -1, 0], [1, 1, 1])), ("rear_panel", _box([-1, -1, 0], [x_rear, 1, 1])),
              ("side_wall", _box([-1, wall_in, 0], [1, 1, 1])), ("hub_motor_wheel_left", bb["hub_motor_wheel_left"])]
        if flanges:
            ob += [("side_panel_bottom_flange", _box([-0.39, 0.193, 0.051], [0.39, 0.30, 0.074])),
                   ("side_panel_top_flange", _box([-0.39, 0.193, 0.191], [0.39, 0.30, 0.214]))]
        return ob
    w, l, h = C["w"], C["l"], C["h"]
    g, wall, floor = C["gap"], C["restraint_wall"], C["tray_floor"]
    z_cell = FACTS["base_sheet"]["top"] + floor
    arrangements = {"4 across (y), 130 along x": (1, 4, (l, w)), "4 along x, 130 across (y)": (4, 1, (w, l)), "2 x 2, 130 along x": (2, 2, (l, w)),
                    "2 x 2, 130 across (y)": (2, 2, (w, l))}

    def try_pocket(flanges):
        best = None
        for name, (nx, ny, (cxl, cyl)) in arrangements.items():
            dx, dy = nx * cxl + (nx - 1) * g, ny * cyl + (ny - 1) * g
            tray = (dx + 2 * wall, dy + 2 * wall)
            for x0 in np.arange(x_rear, x_arch - tray[0] + 1e-9, 0.002):
                for y0 in np.arange(margin[1][1] + C["clear_to_margin"], wall_in - tray[1] + 1e-9, 0.002):
                    tb = _box([x0, y0, FACTS["base_sheet"]["top"]], [x0 + tray[0], y0 + tray[1], z_cell + h + 0.003])
                    if tb[1][2] > min(ceiling(x0), ceiling(x0 + tray[0])) - 0.003:
                        continue
                    hit = [n for n, b in obst_left(flanges) if overlap(tb, b)]
                    if not hit:
                        cand = (name, tb, nx, ny, cxl, cyl)
                        # prefer the pocket closest to the centre line (short series link), then nearest the arch
                        key = (y0, -x0)
                        if best is None or key < best[0]:
                            best = (key, cand)
                        break
        return None if best is None else best[1]

    fit = try_pocket(True)
    flange_ok = fit is not None
    if fit is None:
        fit = try_pocket(False)
    pockets, cells, trays = {}, [], []
    if fit:
        name, tb, nx, ny, cxl, cyl = fit
        for s in (1, -1):
            lo, hi = tb[0].copy(), tb[1].copy()
            if s < 0:
                lo[1], hi[1] = -tb[1][1], -tb[0][1]
            trays.append({"side": "left" if s > 0 else "right", "lo": lo.round(4).tolist(), "hi": hi.round(4).tolist()})
            for i, j in itertools.product(range(nx), range(ny)):
                x = lo[0] + wall + i * (cxl + g)
                y = lo[1] + wall + j * (cyl + g)
                cells.append({"side": "left" if s > 0 else "right", "lo": [round(x, 4), round(y, 4), round(z_cell, 4)],
                              "hi": [round(x + cxl, 4), round(y + cyl, 4), round(z_cell + h, 4)]})
        pockets = {"arrangement": name, "clears_flanges": flange_ok, "tray_mm": [round((tb[1][i] - tb[0][i]) * 1000, 1) for i in range(3)]}
    # pocket free size
    pocket_free = {"y_mm": round((wall_in - margin[1][1]) * 1000, 1), "y_formula_mm": round((2 * wall_in - sy) / 2 * 1000, 1), "x_mm": round((x_arch - x_rear) * 1000, 1),
                   "x_beside_support_mm": round((x_arch - sup_l[1][0]) * 1000, 1), "y_inside_flanges_mm": round((0.193 - margin[1][1]) * 1000, 1)}
    # series link between the groups across the charger zone, above the metal-free margin, under the cover
    link_z = round(min(float(margin[1][2]) + 0.130, FACTS["cover_underside"] - 0.010), 4)
    _L = {"zone": [zone[0].round(4).tolist(), zone[1].round(4).tolist()], "receiver": [rx[0].round(4).tolist(), rx[1].round(4).tolist()],
          "margin": [margin[0].round(4).tolist(), margin[1].round(4).tolist()], "cutout": [cut[0].round(4).tolist(), cut[1].round(4).tolist()],
          "plate": [plate[0].round(4).tolist(), plate[1].round(4).tolist()], "plate_z": plate_z, "receiver_x": [round(float(rx[0][0]), 4), round(float(rx[1][0]), 4)],
          "receiver_clearance_mm": clear_to, "metal_in_margin_mm": metal_in_margin, "measured": measured, "pocket_free": pocket_free,
          "pockets": pockets, "cells": cells, "trays": trays, "link_z": link_z, "ceiling_rear_panel": round(ceiling(x_rear), 4)}
    return _L


if __name__ == "__main__":
    import json
    print(json.dumps(layout(), indent=1))


def gi080_step_result(st):
    """Result text of one GI-080 attempt (build_summary.json gi080 steps) with its measured numbers."""
    o = st["option"]
    if o == 2:
        ok = bool(st.get("fits"))
        return "fits" if ok else "no fit: the %s front bay has no place for FB-B" % st.get("front_bay_layout", "").split(" (")[0]
    if o == 4:
        if not st.get("nofit"):
            return "fits"
        return "no fit: %.0f of %.0f cm² of plate floor free with 5 mm gaps, largest free rectangle %d x %d mm, a holder needs %d x %d mm" % (
            st["plate_free_floor_cm2"], st["plate_floor_cm2"], st["largest_free_rectangle_mm"][0], st["largest_free_rectangle_mm"][1],
            st["holder_footprint_mm"][0], st["holder_footprint_mm"][1])
    if o == 5:
        if st.get("fits"):
            return "fits"
        s = next(iter(st["sides"].values()))
        return ("no fit on either tray: %.0f mm between the tray wall and the margin in y, %.0f mm of tray length outside the margin in x, "
                "%.0f mm from the tray floor to the plate underside; the BMS needs 40 x 110 x 200 mm") % (
            s["gap_wall_to_margin_y_mm"], s["strip_outside_margin_x_mm"], s["height_tray_floor_to_plate_mm"])
    return "fits" if not st.get("nofit") else "no fit: " + ", ".join(st["nofit"])
