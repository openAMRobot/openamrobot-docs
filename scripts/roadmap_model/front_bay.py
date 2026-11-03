"""Front bay, one layout (owner correction A2, owner, 2 Nov 2026; to be entered in P-03 and M-01).

The TZBOT receiver is no longer at the front (A1: reserved zone at the rear), so the bay plate MEC-005 lies on the base sheet
(top 0.057) and every front-bay part uses the full height up to the cover underside (0.290), clear of the LiDAR support MMP.07,
the S3 and its scan plane 222.05 mm +/-5 mm in the open sector (bearing +/-95 deg from lidar_link), the Gemini 336L and its
mount, the MB7060 and TF-Luna bodies and mounts, the E-stop and RESET bodies with their contact blocks, the arch legs and the
lift-plate top-access rule; air gaps of at least 10 mm around converters and top access to every fuse and terminal block.
One plate first (layout()); a second tier only if one plate does not fit. The Jetson moves off bracket MMP.04.00.00.002
(shortened to x 0.100, proposal of 2 Nov 2026); the EV_ICM-42688-P stays at imu_link with nothing heavy or vibrating on it.
Catalogue outlines and their sources are in parts.yaml (geom) and CATALOGUE below.
"""
import itertools
import math

import numpy as np

from frames import glb_nodes

MM = 0.001
PLATE_T = 0.003
PLATE_Z = 0.054              # base-sheet top: the bay plate lies on the base sheet (A2)
FLOOR = PLATE_Z + PLATE_T    # 0.057
COVER = 0.290
RX = None                    # no receiver in the front bay (A1)
METAL_CLEAR = 0.020
LIDAR = (0.330, 0.0)
SCAN = (0.22205 - 0.005, 0.22205 + 0.005)
SECTOR_DEG = 95.0
# compute and control parts that are drawn by the base GLB today, re-placed by the options (catalogue outlines)
CATALOGUE = {
    "compute": {"name": "Jetson Orin NX on reComputer Robotics J401 with heatsink and fan", "bom": "CMP-001, CMP-002, CMP-003, CMP-005, CMP-007",
                "dims": [118.1, 115.0, 45.0], "domain": "SIG", "mass": 0.62, "geom": "PROVENANCE.yaml components.compute (J401 outline with the fan kit), CAD v0.2 envelope", "standoff": "M3", "upright": True},
    "base_controller": {"name": "NUCLEO-H723ZG base controller on standoffs", "bom": "CTL-001", "dims": [133.34, 70.0, 22.0], "domain": "SIG", "mass": 0.09,
                        "geom": "NUCLEO-144 133.34 x 70 mm (ST UM2407); 12 mm standoffs plus parts", "standoff": "M3", "upright": True},
}
TIER = {  # option A tier of each front-bay part (lower: power conversion and safety, upper: compute and control)
    "bay_ddr240": "din", "bay_din": "din", "bay_rsd60": "lower", "bay_rsd100": "lower", "bay_fbc": "upper", "bay_pwr009": "lower",
    "bay_pwr029": "lower", "bay_pwr032": "lower", "bay_usbpd": "lower", "bay_ina228": "lower",
    "compute": "upper", "base_controller": "upper", "bay_can1": "upper", "bay_can2": "upper", "bay_can3": "upper", "bay_iso1212": "upper",
    "bay_tpl7407": "upper", "bay_usbhub": "upper", "bay_usbcan": "upper", "bay_lidar_uart": "upper",
}
SHELF_FIRST = ["compute", "base_controller", "bay_fbc", "bay_din_tb"]   # option A shelf priority (FB-C on the shelf: its fuses need top access)
TOP_ACCESS = {"bay_fbc", "bay_din", "bay_ddr240"}   # fuses and terminals: nothing above them


def under_lift_plate(lo, hi):
    """Footprint of the lift base plate MEC-019 and the column above it (x -0.080 to 0.250 plus 5 mm, |y| <= 0.075): no top access."""
    return lo[0] < 0.255 and hi[1] > -0.075 and lo[1] < 0.075


def bearing_in_sector(x, y):
    return abs(math.degrees(math.atan2(y - LIDAR[1], x - LIDAR[0]))) <= SECTOR_DEG


class Grid:
    """Voxel occupancy (5 mm) of a zone."""

    def __init__(self, lo, hi, res=0.005):
        self.lo, self.res = np.array(lo, float), res
        self.n = np.ceil((np.array(hi) - self.lo) / res - 1e-6).astype(int)
        self.occ = np.zeros(self.n, bool)

    def idx(self, lo, hi):
        a = np.floor((np.array(lo) - self.lo) / self.res + 1e-3).astype(int)
        b = np.ceil((np.array(hi) - self.lo) / self.res - 1e-3).astype(int)
        return np.clip(a, 0, self.n), np.clip(b, 0, self.n)

    def block(self, lo, hi):
        a, b = self.idx(lo, hi)
        if (b > a).all():
            self.occ[a[0]:b[0], a[1]:b[1], a[2]:b[2]] = True

    def free(self, lo, hi):
        if (np.array(lo) < self.lo - 1e-9).any() or (np.array(hi) > self.lo + self.n * self.res + 1e-9).any():
            return False
        a, b = self.idx(lo, hi)
        return not self.occ[a[0]:b[0], a[1]:b[1], a[2]:b[2]].any()

    def centres(self, k):
        return self.lo[k] + (np.arange(self.n[k]) + .5) * self.res


def make_zone(lo, hi, obstacles=(), ceiling=None, scan_band=True):
    g = Grid(lo, hi)
    for a, b in obstacles:
        g.block(a, b)
    xs, ys, zs = g.centres(0), g.centres(1), g.centres(2)
    for i, x in enumerate(xs):
        for j, y in enumerate(ys):
            c = ceiling(x, y) if ceiling else hi[2]
            k = int(max(0, math.floor((c - lo[2]) / g.res + 1e-6)))
            g.occ[i, j, k:] = True
            if scan_band and bearing_in_sector(x, y):
                band = (zs > SCAN[0] - g.res / 2) & (zs < SCAN[1] + g.res / 2)
                g.occ[i, j, band] = True
    return g


def perms(it):
    d = np.array(it["dims"]) * MM
    if it.get("upright"):  # boards and modules drawn by the base GLB: keep their height axis, yaw 0 or 90 deg
        return [np.array(p) for p in sorted({(d[0], d[1], d[2]), (d[1], d[0], d[2])}, key=lambda p: -p[0])]
    if it.get("din"):  # DIN rail on the plate: the depth from the rail stays vertical; width and height may swap
        return [np.array(p) for p in sorted({(d[0], d[1], d[2]), (d[1], d[0], d[2])})]
    out = sorted(set(itertools.permutations(d)), key=lambda p: (abs(p[2] - d[2]) > 1e-9, -p[0]))
    return [np.array(p) for p in out]


def place(items, zones, order=None):
    """Greedy floor placement: largest first, each item in its zone list order. Returns placed {key: (zone, centre,
    size)} and the keys that do not fit. Air gap 10 mm around converters, 3 mm elsewhere."""
    placed, nofit = {}, []
    for it in sorted(items, key=lambda it: (it.get("priority", 9), -np.prod(it["dims"]))):
        for q in range(int(it.get("qty", 1))):
            key = it["id"] if int(it.get("qty", 1)) == 1 else "%s_%d" % (it["id"], q + 1)
            best = None
            for zn in it["zones"]:
                g, z = zones[zn]
                gap = 0.010 if it.get("converter") else 0.003
                zlo, zhi = g.lo, g.lo + g.n * g.res
                for p in perms(it):
                    for x in np.arange(zlo[0], zhi[0] - p[0] + 1e-9, g.res):
                        for y in sorted(np.arange(zlo[1], zhi[1] - p[1] + 1e-9, g.res), key=lambda y: -abs(y + p[1] / 2)):
                            lo = np.array([x, y, zlo[2]])
                            hi = lo + p
                            if hi[2] > zhi[2] + 1e-9:
                                continue
                            if g.free(np.maximum(lo - [gap, gap, 0], zlo), np.minimum(hi + [gap, gap, gap], zhi)):
                                if it["id"] in TOP_ACCESS or it.get("top_access"):
                                    if (z.get("roof") is not None and z["roof"](lo, hi)) or under_lift_plate(lo, hi):
                                        continue
                                best = (zn, lo + p / 2, p)
                                break
                        if best:
                            break
                    if best:
                        break
                if best:
                    break
            if best:
                zn, c, p = best
                zones[zn][0].block(c - p / 2, c + p / 2)
                placed[key] = best
            else:
                nofit.append(key)
    return placed, nofit


X0 = 0.105   # bay rear limit between the arch legs (electronics bracket MMP.04.00.00.002 shortened to x 0.100 for the receiver zone)


def arch_obstacles():
    """Centre-bracket arch seen from the bay: the two front legs (x 0.097 to 0.140 with the foot, |y| 0.088 to 0.166) and
    the arch front wall above z 0.247 (x 0.097 to 0.120, full width)."""
    return [([X0, 0.088, FLOOR], [0.140, 0.166, COVER]), ([X0, -0.166, FLOOR], [0.140, -0.088, COVER]), ([X0, -0.166, 0.247], [0.120, 0.166, COVER])]


def front_obstacles():
    """CAD bodies in the bay (base GLB, inflated 3 mm): LiDAR support MMP.07, spacer and S3, Gemini 336L and mount, MB7060 and
    TF-Luna bodies and mounts, E-stop and RESET with their contact blocks, front corner supports."""
    G = glb_nodes()
    ids = ["lidar_support", "lidar_spacer", "lidar", "base_camera", "camera_mount", "estop", "reset_button", "tof_front", "tof_mount_front",
           "ultrasonic_front_left", "ultrasonic_front_right", "ultrasonic_mount_front_left", "ultrasonic_mount_front_right",
           "support_front_left", "support_front_right"]
    return [(G[k]["v"].min(0) - 0.003, G[k]["v"].max(0) + 0.003) for k in ids if k in G]


def lidar_support_short():
    """MMP.07 shortened to stand on the raised bay plate (both options): walls from the plate top (z 0.125) to 0.174, the 17.5 mm spacer
    and the S3 unchanged, so the scan plane stays at 222.05 mm."""
    return [([0.262, -0.071, FLOOR], [0.366, 0.071, 0.174]), ([0.2824, -0.0351, 0.174], [0.3623, 0.0349, 0.1915]),
            ([0.3022, -0.0278, 0.1915], [0.3578, 0.0277, 0.2327])]


def ceiling_bay(x, y):
    return COVER if x < 0.315 else COVER - (x - 0.315) * (0.0628 / 0.0706)


def option_a(items):
    """Two-tier bay: the best of the shelf priority orders (most parts placed, then most compute and control parts on the shelf)."""
    global SHELF_FIRST
    keep, best = list(SHELF_FIRST), None
    for order in itertools.permutations(["bay_rsd100", "compute", "bay_fbc", "bay_din_tb"]):
        SHELF_FIRST = list(order)
        r = _option_a([dict(i) for i in items])
        on_shelf = sum(1 for k, v in r["placed"].items() if v[0] == "A_upper" and TIER.get(k.rsplit("_", 1)[0] if k[-2:] in ("_1", "_2") else k, "upper") == "upper")
        score = (len(r["placed"]) + sum(1 for k in r["nofit"] if k in STAY) * 0.5, on_shelf, -len(r["nofit"]))
        if best is None or score > best[0]:
            best = (score, r, list(order))
    SHELF_FIRST = keep
    best[1]["shelf_order"] = best[2]
    return stays(best[1])


STAY = {"base_controller": "stays on its controller plate MMP.04.00.00.003 on the IMU bracket (today's position; not heavy or vibrating, inside the shortened bracket at x <= 0.094)"}


def stays(r):
    """Parts that keep their present position when the bay has no room for them (not a no-fit)."""
    r["stays"] = {k: STAY[k] for k in r["nofit"] if k in STAY}
    r["nofit"] = [k for k in r["nofit"] if k not in STAY]
    return r


def _option_a(items):
    """Two-tier bay. DIN carrier: hand placed on the centre-bracket front wall (rail along y, left side), the rest packed."""
    din = []
    # rail 35 mm on a carrier bolted to the left front leg of the arch and the arch front wall (x 0.117), device backs at x 0.140
    y0 = 0.160
    seq = [("bay_din_pnoz", "PNOZ s3 750103 (22.5 x 98 x 120.3)", [120.3, 22.5, 98.0], 0.003),
           ("bay_ddr240", "DDR-240B-24 (63 x 125.2 x 100)", [100.0, 63.0, 125.2], 0.010)]
    rail_z = 0.205
    for k, nm, d, gap in seq:
        d = np.array(d) * MM
        y0 -= gap if k == "bay_ddr240" else 0
        c = np.array([0.140 + d[0] / 2, y0 - d[1] / 2, rail_z])
        din.append((k, c, d))
        y0 -= d[1] + gap
    din_lo = min(c[1] - d[1] / 2 for _, c, d in din) - 0.010
    obst = front_obstacles() + [(np.array(c) - d / 2 - .003, np.array(c) + d / 2 + .003) for _, c, d in din]
    obst.append(([0.276, -0.040, FLOOR], [0.366, 0.040, COVER]))   # shelf notch around the LiDAR spacer and the S3
    obst += arch_obstacles()
    # the DIN carrier region is not available to the shelf or the lower plate
    obst.append(([0.140, din_lo, FLOOR], [0.270, 0.166, COVER]))
    shelf_z = FLOOR + 0.055           # lower parts at most 38 mm (RSD-100 lying) + 10 mm converter air gap + 5 mm grid and standoff margin
    shelf = {"x": [X0, 0.330], "y": [-0.163, din_lo - 0.003]}
    under_shelf = lambda x, y: shelf["x"][0] <= x <= shelf["x"][1] and shelf["y"][0] <= y <= shelf["y"][1]
    lower = make_zone([X0, -0.163, FLOOR], [0.330, 0.163, COVER], obst,
                      lambda x, y: (shelf_z - 0.005) if under_shelf(x, y) else ceiling_bay(x, y))
    upper = make_zone([shelf["x"][0], shelf["y"][0], shelf_z + PLATE_T], [shelf["x"][1], shelf["y"][1], COVER], obst, ceiling_bay)
    zones = {"A_lower": (lower, {"roof": lambda lo, hi: under_shelf((lo[0] + hi[0]) / 2, (lo[1] + hi[1]) / 2)}), "A_upper": (upper, {})}
    its = [dict(id="bay_din_tb", name="DIN terminal blocks on a short rail", dims=[31.2, 47.5, 42.5], din=True, domain="SIG",
                converter=False, zones=["A_upper"], top_access=True, priority=SHELF_FIRST.index("bay_din_tb") if "bay_din_tb" in SHELF_FIRST else 3)]
    for it in items:
        t = TIER.get(it["id"])
        if t in (None, "din"):
            continue
        if t == "lower":
            it = dict(it, zones=["A_lower", "A_upper"], priority=SHELF_FIRST.index(it["id"]) if it["id"] in SHELF_FIRST else 9)
        elif it["id"] in SHELF_FIRST and t != "lower":
            it = dict(it, zones=["A_upper", "A_lower"], priority=SHELF_FIRST.index(it["id"]))
        elif it["id"] == "bay_usbhub":
            it = dict(it, zones=["A_lower", "A_upper"], priority=8)   # the shelf is kept for compute, NUCLEO, FB-C and the terminal blocks
        else:  # small boards: on the plates
            it = dict(it, zones=["A_upper", "A_lower"])
        its.append(it)
    placed, nofit = place(its, zones)
    for k, c, d in din:
        placed[k] = ("A_din", c, d)
    return {"placed": placed, "nofit": nofit, "shelf": {"x": shelf["x"], "y": [shelf["y"][0], shelf["y"][1]], "z": shelf_z},
            "din_region_y": [din_lo, 0.166], "plates": plates_a(shelf, shelf_z)}


def plates_a(shelf, shelf_z):
    y1 = shelf["y"][1]
    return [{"name": "MEC-005 lower plate on the base sheet", "lo": [0.140, -0.163, PLATE_Z], "hi": [0.330, 0.163, FLOOR]},
            {"name": "MEC-005 lower plate tongue between the arch legs", "lo": [X0, -0.086, PLATE_Z], "hi": [0.140, 0.086, FLOOR]},
            {"name": "MEC-005 upper shelf on 4 standoffs (rear part)", "lo": [0.140, shelf["y"][0], shelf_z], "hi": [0.276, y1, shelf_z + PLATE_T]},
            {"name": "MEC-005 upper shelf tongue between the arch legs", "lo": [X0, -0.086, shelf_z], "hi": [0.140, min(y1, 0.086), shelf_z + PLATE_T]},
            {"name": "MEC-005 upper shelf, right arm beside the LiDAR spacer", "lo": [0.276, shelf["y"][0], shelf_z], "hi": [shelf["x"][1], -0.040, shelf_z + PLATE_T]},
            {"name": "MEC-005 upper shelf, left arm beside the LiDAR spacer", "lo": [0.276, 0.040, shelf_z], "hi": [shelf["x"][1], y1, shelf_z + PLATE_T]},
            {"name": "DIN carrier on the centre-bracket front wall (rail along y)", "lo": [0.117, shelf["y"][1] + 0.013, 0.150], "hi": [0.140, 0.163, 0.262]}]


def layout(items):
    """One layout: a single plate on the base sheet with every front-bay part (DIN rail with PNOZ s3, DDR-240B-24 and the
    terminal blocks on the plate). Falls back to the two-tier bay only if the single plate does not take every part."""
    obst = front_obstacles() + arch_obstacles()
    bay = make_zone([X0, -0.163, FLOOR], [0.366, 0.163, COVER], obst, ceiling_bay)
    zones = {"bay": (bay, {})}
    its = []
    for it in items:
        t = TIER.get(it["id"])
        if t is None or it["id"] == "bay_din":
            continue
        its.append(dict(it, zones=["bay"], din=(t == "din") or it.get("din"),
                        priority=0 if it["id"] in ("compute", "base_controller", "bay_rsd100", "bay_ddr240") else 9))
    for d in (dict(id="bay_din_pnoz", name="PNOZ s3 750103 on a short DIN rail", dims=[22.5, 98.0, 120.3], din=True, domain="SIG", converter=False, top_access=True, priority=1),
              dict(id="bay_din_tb", name="DIN terminal blocks on the short rail", dims=[31.2, 47.5, 42.5], din=True, domain="SIG", converter=False, top_access=True, priority=1)):
        its.append(dict(d, zones=["bay"]))
    placed, nofit = place(its, zones)
    plates = [{"name": "MEC-005 plate on the base sheet (single tier)", "lo": [0.140, -0.163, PLATE_Z], "hi": [0.366, 0.163, FLOOR]},
              {"name": "MEC-005 plate tongue between the arch legs", "lo": [X0, -0.086, PLATE_Z], "hi": [0.140, 0.086, FLOOR]}]
    res = {"placed": placed, "nofit": nofit, "plates": plates, "layout": "single plate"}
    if nofit:
        two = option_a([dict(i) for i in items])
        if len(two["nofit"]) < len(nofit):
            two["layout"] = "two-tier (one plate does not take every part)"
            return two
    return stays(res)


def fit_numbers(res, items):
    """Fit numbers of an option: parts placed, plate area used, lowest metal part above the receiver, height margin to the
    cover, scan-band intrusions in the open sector, smallest gap between parts."""
    P = res["placed"]
    boxes = [(k, np.array(c) - np.array(d) / 2, np.array(c) + np.array(d) / 2) for k, (_, c, d) in P.items()]
    e = 1e-6
    low, lateral = None, None   # no receiver in the front bay (A1)
    top = max(b[2][2] for b in boxes)
    scan = [b[0] for b in boxes if b[2][2] > SCAN[0] and b[1][2] < SCAN[1] and any(bearing_in_sector(x, y) for x in (b[1][0], b[2][0]) for y in (b[1][1], b[2][1]))]
    gap = 9.0
    for (ka, alo, ahi), (kb, blo, bhi) in itertools.combinations(boxes, 2):
        g = np.maximum(0, np.maximum(alo, blo) - np.minimum(ahi, bhi))
        gap = min(gap, float(np.linalg.norm(g)))
    plate = res["plates"][0]
    area = (plate["hi"][0] - plate["lo"][0]) * (plate["hi"][1] - plate["lo"][1])
    used = sum((b[2][0] - b[1][0]) * (b[2][1] - b[1][1]) for b in boxes if res["placed"][b[0]][0] in ("A_lower", "B_bay", "bay"))
    by_zone = {}
    for k, (zn, c, d) in P.items():
        by_zone.setdefault(zn, []).append(k)
    return {"layout": res.get("layout", ""), "placed": len(P), "not_placed": list(res["nofit"]), "stays_in_place": res.get("stays", {}), "lowest_metal_above_receiver_mm": None if low is None else round((low - RX["hi"][2]) * 1000, 1),
            "lowest_part_beside_receiver_lateral_mm": None if lateral is None else round(lateral * 1000, 1),
            "top_mm": round(top * 1000, 1), "cover_margin_mm": round((COVER - top) * 1000, 1), "scan_band_parts": scan,
            "min_gap_mm": round(gap * 1000, 1), "plate_area_used_pct": round(100 * used / area, 1), "by_zone": by_zone}
