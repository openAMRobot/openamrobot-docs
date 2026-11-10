"""Harness routing of the roadmap model: named harnesses, supported routes, tie points, lift energy chain.

Called by build.py (section "harness"). Inputs are the placed model (GLB nodes, placement geometry, cable endpoints);
outputs are the cable routes (cable_list.csv columns), the drawn tubes, tie points, grommets, guards and chain parts,
and docs/assets/roadmap/model/harness_routes.json, which scripts/check_roadmap.py checks (spans, components, withdrawal
paths, bend radius, lift cables in the energy chain, harness and labels).

Base routes (base_footprint, bp000, L1000) are found on a 5 mm voxel grid of the base:
- structure (sheet-metal panels, centre-frame arch, brackets, plates) is voxelized as shells from its mesh; a route
  passes a shell only at a cable end (a grommet is recorded there) or at a declared opening;
- components are boxes; a route keeps its radius plus 3 mm from every one of them, never runs on top of one
  (40 mm band above the top; fuse parts: up to the cover) and never crosses a withdrawal path (battery trays and front
  tiers withdraw upward with the cover off, the cover band itself), except for the cable's own end parts;
- the wheels and their side zones are a keep-out up to the wheel guards: the side trunks cross the drive section on
  the guards (protected route over the wheel area);
- the cost of a step is low within 15 mm of a structure surface (tie base), higher within 40 mm (tie on a standoff)
  and high in free air, so routes follow the floor, the side panels and the uprights; cells already used by a cable
  are cheaper (bundles form trunks); sensitive signal cables (CAN, USB, SPI, LiDAR) pay extra within 30 mm of power.
The upper-body harness is drawn from fixed points: two cable openings left and right of the lift (power left, signal right, owner
decision 8 Nov 2026) with the disconnect points DP-LIFT-L and DP-LIFT-R on the lift base plate,
a fixed sleeve on the -y face of the static column, the energy chain behind the column, the moving section under the
adapter plate and up the arm post.
"""
import heapq
import math

import os

import numpy as np
import yaml
from scipy import ndimage

from slot_rule import cover_slot_keepouts, envelope_radius, slot_violations  # noqa: F401 (the slot rule, shared with the tests)

FACTS = yaml.safe_load(open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "facts.yaml")))

RES = 0.005
LO = np.array([-0.400, -0.295, 0.050])
HI = np.array([0.400, 0.295, 0.300])
COVER_BAND = 0.288          # z above which the cover (removable) is a withdrawal path
OVER_H = 0.040              # band above a component top that counts as "over the component"
MAX_SPAN = 0.150
TIE_PITCH = 0.140           # generation pitch (rule 150 mm)
TIE_NEAR = 0.045            # generation distance from a connector or branch (rule 50 mm)
SUPPORT_DIRECT = 0.015
SUPPORT_STANDOFF = 0.040
CLEAR = 0.0025              # cell-centre distance to an obstacle cell beyond the cable radius (a cable may lie against a part)
NO_OVER = ("battery_series_link",)
P2P_MAX = 0.0               # (was 0.30: smooth free curves between two ends; replaced by axis-aligned routes, 3 Nov 2026)
SUPPORT_MAX = 0.030         # every base route point within 30 mm of a supporting surface (floor, wall, member, plate, channel) ...
END_FREE = 0.060            # ... except within 60 mm of its connectors (local exit) and inside declared protected passages
AXIS_TOL_DEG = 15.0         # route segments within 15 degrees of the structure axes (except declared 45 degree transitions)
SEP_WORK = 0.030            # working separation sensitive / power (verify against the interface documents; no value documented)
DETOUR = 4.0                # a grid route longer than 4 x direct (and 400 mm more) means the layout has no passage (corridor routes are longer by design)
# two lift cable openings, 50 x 25 mm (x, y) on the channel centre lines, owner decision 8 Nov 2026
DECK_OPEN = {"L": ([-0.0025, 0.050, 0.285], [0.0475, 0.075, 0.306]), "R": ([-0.0025, -0.075, 0.285], [0.0475, -0.050, 0.306])}   # centres on grid cell centres
POWER_DOMS = ("BAT", "SAFE", "R24", "LV")   # left opening; SIG through the right opening


def dp_side(dom):
    return "L" if dom in POWER_DOMS else "R"


# declared cable openings in structure (CAD changes): id, part, box
OPENINGS = [{"id": "slot in the electronics bracket left wall (left hub-motor lead and brake)", "part": "electronics_bracket",
             "lo": [-0.016, 0.068, 0.120], "hi": [0.016, 0.096, 0.165]},
            {"id": "slot in the electronics bracket right wall (right hub-motor lead and brake)", "part": "electronics_bracket",
             "lo": [-0.016, -0.096, 0.120], "hi": [0.016, -0.068, 0.165]},
            {"id": "slot in the centre-bracket left side wall for the CH-B1 branch (edge trim)", "part": "centre_bracket", "lo": [-0.058, 0.160, 0.215], "hi": [-0.022, 0.182, 0.240]},
            {"id": "slot in the centre-bracket right side wall for the CH-B2 branch (edge trim)", "part": "centre_bracket", "lo": [-0.058, -0.182, 0.215], "hi": [-0.022, -0.160, 0.240]},
            {"id": "slot in the electronics bracket rear wall (both hub-motor leads from the ZLAC8015D motor ports, edge trim)", "part": "electronics_bracket",
             "lo": [-0.022, -0.075, 0.115], "hi": [-0.010, 0.075, 0.168]},
            # owner decision 8 Nov 2026: two cable openings left and right of the lift, near the middle of the platform length, through the
            # lift base plate MEC-019, the arch top sheet and the backing plate (between the 4 x M8 arch bolts; edge grommet in each)
            {"id": "slot in the centre-bracket rear wall at the CH-C1 end (power from the rear module into the channel, edge trim)", "part": "centre_bracket",
             "lo": [-0.142, 0.040, 0.212], "hi": [-0.118, 0.085, 0.250]},
            {"id": "slot in the centre-bracket rear wall at the CH-C2 end (signal from the rear module into the channel, edge trim)", "part": "centre_bracket",
             "lo": [-0.142, -0.085, 0.212], "hi": [-0.118, -0.040, 0.250]},
            {"id": "slot in the centre-bracket front wall at the CH-C1 end (front bay into the channel, edge trim)", "part": "centre_bracket",
             "lo": [0.090, 0.040, 0.212], "hi": [0.145, 0.085, 0.250]},
            {"id": "slot in the centre-bracket front wall at the CH-C2 end (front bay into the channel, edge trim)", "part": "centre_bracket",
             "lo": [0.090, -0.085, 0.212], "hi": [0.145, -0.040, 0.250]},
            {"id": "lift cable opening left (power: BAT, SAFE, R24, LV)", "part": "lift_base_plate", "lo": DECK_OPEN["L"][0], "hi": DECK_OPEN["L"][1]},
            {"id": "lift cable opening right (signal: CAN, USB, sensors)", "part": "lift_base_plate", "lo": DECK_OPEN["R"][0], "hi": DECK_OPEN["R"][1]}]   # cables drawn as parts: crossing them is not "over a component"

STRUCT_GLB = {"base_plate", "side_panel_left", "side_panel_right", "front_panel", "rear_panel", "centre_bracket",
              "electronics_bracket", "driver_mount", "support_front_left", "support_front_right", "support_rear_left",
              "support_rear_right", "lidar_support", "lidar_spacer", "camera_mount", "ultrasonic_mount_front_left",
              "ultrasonic_mount_front_right", "ultrasonic_mount_rear_left", "ultrasonic_mount_rear_right", "tof_mount_front",
              "tof_mount_rear", "controller_plate"}
NO_SUPPORT_GLB = {"cover", "cover_flange_front", "cover_flange_rear"}   # removable: never a tie surface, never crossed
STRUCT_PLACEMENT = ("bay_plate", "rear_plate", "motor_brackets", "lift_base_plate", "rp_", "side_plates", "ch_", "tz_receiver_frame")
IGNORE_PLACEMENT = ("harness", "fasteners", "shims", "can_term", "base_cutout", "service_loop", "lift_energy_chain", "us_locknut",
                    "feedthru")
TOP_ACCESS = ("rz_fba", "rz_fbb", "rz_f0", "rz_fchg", "rz_pre", "bay_fbc")
TOP_BAND = {"rz_f0": 0.060}   # F0 holder: 60 mm clear above for the cover and the fuse change (PWR-018 unplugged first); others up to the cover

# functional zones and service envelopes (Phase 1, 3 Nov 2026; base_footprint, m)
ZONES = [
    {"id": "Z-PWR", "name": "battery and power module (rear)", "lo": [-0.372, -0.290, 0.054], "hi": [-0.108, 0.290, 0.290],
     "service": "cover off: trays lift out after PWR-018 and the tray leads; FB-A and FB-B fuses from above; BMS through the right side panel; QS1 key and SB50 from outside"},
    {"id": "Z-DRV", "name": "drive section (wheels, motor driver, centre bracket)", "lo": [-0.135, -0.290, 0.054], "hi": [0.135, 0.290, 0.294],
     "service": "motor driver from above after the lift base plate and the channels' rear lids; wheels from below (keep-outs up to the wheel guards)"},
    {"id": "Z-FBC", "name": "front bay centre (two tiers, DIN carrier)", "lo": [0.105, -0.166, 0.054], "hi": [0.366, 0.166, 0.290],
     "service": "cover off: shelf lifts off its standoffs, then the lower plate (DP-FT connectors)"},
    {"id": "Z-FBL", "name": "front bay left side zone (power: FB-C, USB-PD, 3.3 V)", "lo": [0.130, 0.172, 0.054], "hi": [0.280, 0.250, 0.205],
     "service": "cover off: parts on the left side plate, fuses up; stays when the tiers lift out"},
    {"id": "Z-FBR", "name": "front bay right side zone (signal: USB hub, USB-CAN-FD, LiDAR UART)", "lo": [0.130, -0.250, 0.054], "hi": [0.280, -0.172, 0.205],
     "service": "cover off: parts on the right side plate; feed-throughs in the right side panel"},
    {"id": "Z-COL", "name": "lift column (static)", "lo": [-0.200, -0.100, 0.304], "hi": [0.200, 0.100, 0.834],
     "service": "DP-LIFT-L and DP-LIFT-R disconnect every lift cable; sleeve P-clips on the -y T-slot; flag rod guide on the +y face at the head"},
    {"id": "Z-UPR", "name": "moving upper body (adapter plate, arm post, arms, head)", "lo": [-0.200, -0.400, 0.834], "hi": [0.400, 0.400, 1.700],
     "service": "upper devices unplug at their own connectors; arms at the arm base connectors"},
]
# reserved main cable corridors (Phase 1): kept free of parts, the harness trunks run here
CORRIDORS = [
    {"id": "C-L", "name": "left side corridor: floor and side-panel lane beside the front side zone, over-wheel guard L, gap between the left tray and the side wall",
     "lo": [-0.290, 0.255, 0.054], "hi": [0.320, 0.288, 0.290]},
    {"id": "C-R", "name": "right side corridor: floor and side-panel lane beside the front side zone, over-wheel guard R (the rear part beside the right tray is the BMS slot)",
     "lo": [-0.110, -0.288, 0.054], "hi": [0.320, -0.255, 0.290]},
    {"id": "CH-C1", "name": "central power channel over the drive section, left (SAFE, BAT, motor driver power)", "lo": [-0.135, 0.040, 0.212], "hi": [0.098, 0.085, 0.240]},
    {"id": "CH-C2", "name": "central signal channel over the drive section, right (CAN, USB, sensor lines; right lift opening to DP-LIFT-R)", "lo": [-0.135, -0.085, 0.212], "hi": [0.098, -0.040, 0.240]},
    {"id": "C-FP", "name": "front panel lane behind the front sensors", "lo": [0.330, -0.190, 0.054], "hi": [0.370, 0.190, 0.200]},
    {"id": "C-RM", "name": "rear module exits over the F0 holder into the arch opening (|y| < 0.090)", "lo": [-0.190, -0.090, 0.218], "hi": [-0.135, 0.090, 0.270]},
]

# declared protected passages (cables may run over a component top here; they are supported by the channel or guard):
# the two central channels over the drive section and the over-wheel guards
PASSAGES = [{"id": "CH-C1 central power channel over the drive section", "lo": [-0.140, 0.040, 0.215], "hi": [0.145, 0.085, 0.250]},
            {"id": "CH-C2 central signal channel over the drive section", "lo": [-0.140, -0.085, 0.215], "hi": [0.145, -0.040, 0.250]},
            {"id": "fan lead strip on the arch front wall (fan bracket)", "lo": [0.097, -0.045, 0.235], "hi": [0.160, 0.045, 0.290]},
            {"id": "CH-B1 power branch to the left side corridor (over the wheel, through the arch side wall)", "lo": [-0.065, 0.040, 0.206], "hi": [-0.015, 0.240, 0.250]},
            {"id": "CH-B2 signal branch to the right side corridor (over the wheel, through the arch side wall)", "lo": [-0.065, -0.240, 0.206], "hi": [-0.015, -0.040, 0.250]},
            {"id": "C-RM rear module exit channel from FB-B over F0 into the arch (U-channel on the rear power module)", "lo": [-0.300, -0.090, 0.218], "hi": [-0.135, 0.090, 0.270]},
            {"id": "C-FL front tier to CH-C1 (left lift cable opening)", "lo": [0.098, 0.040, 0.215], "hi": [0.160, 0.085, 0.272]},
            {"id": "C-FR front tier to CH-C2 (right lift cable opening)", "lo": [0.098, -0.085, 0.215], "hi": [0.160, -0.040, 0.272]},
            {"id": "over-wheel guard L", "lo": [-0.135, 0.195, 0.206], "hi": [0.135, 0.288, 0.290]},   # 8 Nov 2026: from y 0.195, so cables climb
            {"id": "over-wheel guard R", "lo": [-0.135, -0.288, 0.206], "hi": [0.135, -0.195, 0.290]}]  # inboard of the cover slot onto the guard
BRANCH_X = (-0.060, -0.020)   # cross branches of the central channels: through the arch side wall above the wheel guard
CHANNELS = [{"id": "ch_central_power", "name": "CH-C1 central power channel (SAFE / BAT) over the drive section, left", "y": [0.040, 0.085]},
            {"id": "ch_central_signal", "name": "CH-C2 central signal channel (CAN, USB, sensor lines) over the drive section, right (right lift opening)", "y": [-0.085, -0.040]}]
CH_X, CH_FLOOR, CH_TOP = (-0.135, 0.098), 0.212, 0.240
CH_DROP = (-0.100, -0.040)   # drop-out in both channel floors above the motor driver (edge trim): motor driver power, CAN1


def channel_prims():
    """U-channels hung from the arch top sheet (CAD change): 3 mm floor, 2 mm walls; boxes (lo, hi) per channel."""
    out = {}
    for nm, s_ in (("ch_branch_power", 1), ("ch_branch_signal", -1)):   # cross branches: floor from the channel to the wheel guard
        y0, y1 = sorted([s_ * 0.085, s_ * 0.236])
        out[nm] = [([BRANCH_X[0], y0, CH_FLOOR], [BRANCH_X[1], y1, CH_FLOOR + 0.003]), ([BRANCH_X[0] - 0.002, y0, CH_FLOOR], [BRANCH_X[0], y1, CH_TOP]),
                   ([BRANCH_X[1], y0, CH_FLOOR], [BRANCH_X[1] + 0.002, y1, CH_TOP])]
    for c in CHANNELS:
        y0, y1 = c["y"]
        d0, d1 = CH_DROP
        out[c["id"]] = [([CH_X[0], y0, CH_FLOOR], [d0, y1, CH_FLOOR + 0.003]), ([d1, y0, CH_FLOOR], [CH_X[1], y1, CH_FLOOR + 0.003]),
                        ([CH_X[0], y0, CH_FLOOR], [CH_X[1], y0 + 0.002, CH_TOP]), ([CH_X[0], y1 - 0.002, CH_FLOOR], [CH_X[1], y1, CH_TOP])]
    return out


# cable classes: minimum bend radius (static, fixed installation) and, in the energy chain, the continuous-flex minimum
SENSITIVE = ("CAN", "USB", "SPI", "LiDAR", "RPLIDAR", "S3 cable", "ribbon", "STP")


def min_bend_static(gauge, od):
    """Static minimum bend radius (mm) per cable class: 25 mm² at least 60 mm (A9), USB 3 and STP 6 x OD
    (cable datasheets give 4 to 6 x OD fixed), others 6 x OD."""
    if gauge == "25 mm²":
        return 60
    if gauge.startswith("busbar"):
        return 4
    if "class 6" in gauge:
        return round(4 * od)   # extra-flexible fine-strand cable: 4 x OD (verify with the cable datasheet)   # formed copper bar: inner bend radius >= 1 x thickness (verify with the bar supplier)
    return max(15, round(6 * od))


def min_bend_flex(od):
    """Continuous-flex minimum bend radius (mm) of a chain-rated cable: 10 x OD."""
    return round(10 * od)


def is_sensitive(fn, gauge):
    t = fn + " " + gauge
    return any(k in t for k in SENSITIVE)


def is_power(dom, gauge):
    return dom in ("BAT", "SAFE", "R24") and any(g in gauge for g in ("busbar", "25 mm²", "10 mm²", "6 mm²", "2.5 mm²", "1.5 mm²", "16 AWG", "0.75 mm²"))


# ---------------------------------------------------------------- voxel model
class Vox:
    def __init__(self):
        self.n = np.ceil((HI - LO) / RES - 1e-6).astype(int)
        self.struct = np.zeros(self.n, bool)
        self.struct_id = np.full(self.n, -1, np.int16)
        self.nosupport = np.zeros(self.n, bool)
        self.names = []

    def cell(self, p):
        return tuple(np.clip(np.floor((np.asarray(p) - LO) / RES).astype(int), 0, self.n - 1))

    def centre(self, c):
        return LO + (np.asarray(c) + 0.5) * RES

    def slab(self, lo, hi):
        a = np.clip(np.floor((np.asarray(lo) - LO) / RES + 1e-3).astype(int), 0, self.n)
        b = np.clip(np.ceil((np.asarray(hi) - LO) / RES - 1e-3).astype(int), 0, self.n)
        return tuple(slice(a[i], max(a[i], b[i])) for i in range(3))

    def add_points(self, pts, name, grid=None):
        k = np.floor((pts - LO) / RES).astype(int)
        m = ((k >= 0) & (k < self.n)).all(1)
        k = k[m]
        g = self.struct if grid is None else grid
        g[k[:, 0], k[:, 1], k[:, 2]] = True
        if grid is None:
            i = len(self.names)
            self.names.append(name)
            self.struct_id[k[:, 0], k[:, 1], k[:, 2]] = i

    def add_box(self, lo, hi, name):
        s = self.slab(lo, hi)
        self.struct[s] = True
        i = len(self.names)
        self.names.append(name)
        self.struct_id[s] = i


def prim_box(p):
    if p["t"] == "box":
        s = np.array(p["s"]) / 2
        c = np.array(p["p"])
        if p.get("r") and any(abs(v) > 1e-6 for v in p["r"]):
            s = np.full(3, np.linalg.norm(s))
        return c - s, c + s
    if p["t"] == "cyl":
        s = np.array([p["r"]] * 3)
        s["xyz".index(p.get("ax", "z"))] = p["h"] / 2
        c = np.array(p["p"])
        return c - s, c + s
    if p["t"] == "mesh":
        v = np.array(p["v"]).reshape(-1, 3)
        return v.min(0), v.max(0)
    if p["t"] == "tube":
        v = np.array(p["pts"])
        return v.min(0) - p["r"], v.max(0) + p["r"]
    return None


def mesh_points(v, f, step=0.003):
    tri = v[f]
    out = [tri.reshape(-1, 3)]
    e = np.maximum(np.linalg.norm(tri[:, 1] - tri[:, 0], axis=1), np.linalg.norm(tri[:, 2] - tri[:, 0], axis=1))
    nn = np.ceil(e / step).astype(int).clip(1, 300)
    for n in sorted(set(nn)):
        if n <= 1:
            continue
        sel = tri[nn == n]
        a, b = np.meshgrid(np.arange(n + 1), np.arange(n + 1))
        m = (a + b) <= n
        a, b = a[m] / n, b[m] / n
        p = sel[:, None, 0] + a[None, :, None] * (sel[:, None, 1] - sel[:, None, 0]) + b[None, :, None] * (sel[:, None, 2] - sel[:, None, 0])
        out.append(p.reshape(-1, 3))
    return np.vstack(out)


def wheel_guards(G):
    """Over-wheel cable guards (new parts, CAD change): a 2 mm aluminium tray on the side-panel inner face above
    each drive wheel, 8 mm above the tyre top, from x -0.130 to 0.130; the side trunks cross the drive section on it."""
    out = []
    for side, s in (("left", 1), ("right", -1)):
        lo, hi = np.array(G["hub_motor_wheel_" + side]["v"]).min(0), np.array(G["hub_motor_wheel_" + side]["v"]).max(0)
        z0 = hi[2] + 0.008
        y_in = 0.236
        out.append({"id": "wheel_guard_" + side, "side": side, "z": round(z0, 4),
                    "plate": [[-0.130, min(s * y_in, s * 0.287), z0], [0.130, max(s * y_in, s * 0.287), z0 + 0.002]],
                    "lip": [[-0.130, min(s * y_in, s * (y_in + 0.002)), z0], [0.130, max(s * y_in, s * (y_in + 0.002)), z0 + 0.022]]})
    return out


def build_model(ctx):
    """Voxel structure model, component boxes, keep-outs and withdrawal paths of the base."""
    G, geo, fbd = ctx["G"], ctx["geo"], ctx["fbd"]
    V = Vox()
    comps = {}
    for k, nd in G.items():
        if k in ctx.get("hide", ()):
            continue
        v = np.array(nd["v"])
        if k in fbd:   # relocated by the front-bay layout
            _, cc, p = fbd[k]
            comps[k] = (np.array(cc) - np.array(p) / 2, np.array(cc) + np.array(p) / 2)
            continue
        if k in STRUCT_GLB:
            V.add_points(mesh_points(v, np.array(nd["f"])), k)
        elif k in NO_SUPPORT_GLB:
            V.add_points(mesh_points(v, np.array(nd["f"])), k, grid=V.nosupport)
        else:
            comps[k] = (v.min(0), v.max(0))
    for k, g in geo.items():
        if g.get("group", "base") != "base" or k.startswith(IGNORE_PLACEMENT) or k in ("tz_metal_free_zone",):
            continue
        if g.get("option") and g.get("option") != ctx.get("fb_default"):
            continue
        if k.startswith(STRUCT_PLACEMENT):
            for p in g["prims"]:
                if p.get("o") is not None and p["o"] < 0.5:
                    continue
                if p["t"] == "mesh":
                    v = np.array(p["v"]).reshape(-1, 3)
                    V.add_points(mesh_points(v, np.array(p["f"]).reshape(-1, 3)), k)
                else:
                    b = prim_box(p)
                    if b:
                        V.add_box(b[0], b[1], k)
            continue
        bs = [prim_box(p) for p in g["prims"] if not (p.get("o") is not None and p["o"] < 0.5)]
        bs = [b for b in bs if b is not None]
        if bs:
            comps[k] = (np.min([b[0] for b in bs], 0), np.max([b[1] for b in bs], 0))
    for o in OPENINGS:
        sl = V.slab(o["lo"], o["hi"])
        V.struct[sl] = False
        V.struct_id[sl] = -1
    guards = wheel_guards(G)
    for gd in guards:
        V.add_box(*gd["plate"], name=gd["id"])
        V.add_box(*gd["lip"], name=gd["id"])
    # keep-outs (hard) and withdrawal paths
    keep = []
    for side in ("left", "right"):
        lo, hi = comps["hub_motor_wheel_" + side]
        s = 1 if side == "left" else -1
        y0, y1 = sorted([s * (abs(lo[1] if s > 0 else hi[1]) + 0.005), s * 0.290])
        keep.append({"id": "wheel_zone_" + side, "lo": [lo[0] - 0.025, y0, 0.0], "hi": [hi[0] + 0.025, y1, guards[0]["z"]],
                     "why": "drive wheel and its side zone up to the wheel guard"})
    # LiDAR scan plane 222.05 mm +- 5 mm in the open sector (+-95 deg from lidar_link at x 0.330): no cable or tie in it
    keep.append({"id": "lidar_scan_band", "lo": [0.0, -0.295, 0.2120], "hi": [0.400, 0.295, 0.2325], "sector": {"x": 0.330, "y": 0.0, "deg": 95.0},
                 "members": ["lidar"], "why": "RPLIDAR S3 scan plane +-5 mm (and 5 mm margin) in the open sector"})
    # owner rule 8 Nov 2026 (P-03 rev20.5 item 29): the slot is the gap between the lower edge of the top cover and the upper edges
    # of the side, front and rear panels (214 to 232 mm). No cable, busbar or tie in it or on a panel upper edge, all around the robot
    # (the LiDAR looks out through the front and the slot is visible); there is no inward band. Inside the base, parts may rise
    # above the slot level (rear section) and their leads may leave at the top and run down inside.
    keep += cover_slot_keepouts(FACTS)
    mf = geo.get("tz_metal_free_zone")
    if mf:
        b = prim_box(mf["prims"][0])
        keep.append({"id": "tz_metal_free_zone", "lo": list(b[0]), "hi": list(b[1]), "members": ["tz_receiver", "tof_rear"],
                     "why": "receiver metal-free frame (20 mm on the sides, 15 mm above) (only the receiver's own cables and the rear TF-Luna lead enter it)"})
    withdraw = []
    for side in ("left", "right"):
        k = "battery_tray_" + side
        if k in comps:
            lo, hi = comps[k]
            withdraw.append({"id": k, "lo": [lo[0], lo[1], lo[2]], "hi": [hi[0], hi[1], 0.300], "members": [k, "battery_cells_" + side],
                             "why": "battery tray lifts out upward (cover off)"})
    bp = geo.get("bay_plate")
    if bp:
        bs = [prim_box(p) for p in bp["prims"]]
        lo, hi = np.min([b[0] for b in bs], 0), np.max([b[1] for b in bs], 0)
        side = {k for k, v in fbd.items() if str(v[0]).startswith("side")}   # side-zone parts stay when the tiers lift out
        mem = sorted(set([k for k in comps if k.startswith("bay_") and k.rsplit("_", 1)[0] not in side and k not in side] + [k for k in fbd if k not in side]))
        notch = [[round(x_, 3), round(y_, 3), 0.2] for x_ in (0.285, 0.305, 0.325) for y_ in (-0.024, 0.0, 0.024)]   # shelf notch around the LiDAR spacer
        withdraw.append({"id": "front_tiers", "lo": [lo[0], lo[1], 0.054], "hi": [hi[0], hi[1], 0.300], "members": mem, "except": notch,
                         "why": "front-bay tiers (lower plate, shelf, DIN carrier) lift out upward (cover off); the shelf notch around the LiDAR spacer is outside it"})
    withdraw.append({"id": "cover", "lo": [-0.390, -0.291, COVER_BAND], "hi": [0.390, 0.291, 0.300], "members": [],
                     "why": "cover lifts off; only the two lift cable openings beside the lift pass it", "except": list(ctx["deck_exits"].values())})
    return V, comps, keep, withdraw, guards


# ---------------------------------------------------------------- routing
DIRS = np.array([d for d in __import__("itertools").product((-1, 0, 1), repeat=3) if 0 < sum(abs(v) for v in d) <= 2])


def _turn(a, b):
    u, v = DIRS[a], DIRS[b]
    c = float(np.dot(u, v)) / (np.linalg.norm(u) * np.linalg.norm(v))
    return math.acos(max(-1.0, min(1.0, c)))


ANG = np.array([[_turn(a, b) for b in range(len(DIRS))] for a in range(len(DIRS))])
DLEN = np.linalg.norm(DIRS, axis=1) * RES


AXIS = [i for i in range(len(DIRS)) if int(np.abs(DIRS[i]).sum()) == 1]
ROUTE_DIRS = list(range(len(DIRS)))   # axis steps and planar 45 degree transitions (penalised, declared in the output)
AXIS_SET = set(AXIS)
DIAG_COST = 2.5
T45_MAX = 0.120   # a 45 degree transition is at most 120 mm long
RELAX = set(__import__("os").environ.get("OAMR_RELAX", "").split(",")) - {""}   # debugging only


def _planar_angle(a, b):
    """Angle (deg) of a segment to the nearest axis inside its plane (45 for a planar diagonal)."""
    d = np.sort(np.abs(np.subtract(b, a)))[::-1]
    return math.degrees(math.atan2(d[1], d[0])) if d[0] > 1e-12 else 0.0


def is_axis(a, b, tol_deg=AXIS_TOL_DEG):
    """Segment within tol_deg of one structure axis."""
    d = np.abs(np.subtract(b, a))
    L = float(np.linalg.norm(d))
    return L < 1e-9 or math.degrees(math.acos(min(1.0, float(d.max()) / L))) <= tol_deg + 1e-9


def astar(free, w, start, goal, rmin, turn=0.05, hfac=1.0, max_angle=math.radians(91), goal_dirs=None, dirs=None):
    """A* on the voxel grid with 18 directions (axes and planar diagonals). A bend-radius rule is built in: after a
    change of direction by theta the route runs straight for at least 2 rmin tan(theta / 2) (both halves of the next
    corner fit), and it leaves and reaches a connector straight for at least rmin (90 degree bend at the end)."""
    n = free.shape
    nd_ = len(DIRS)
    W = w
    gc = np.array(goal)
    s = tuple(start)
    best = {(s, -1): 0.0}
    prev = {}
    q = [(0.0, 0.0, s, -1)]
    commit = {}
    use = list(range(nd_)) if dirs is None else list(dirs)
    for a in range(nd_):
        for b in range(nd_):
            th = ANG[a, b]
            if th < 1e-6 or th > max_angle:
                continue
            commit[(a, b)] = max(1, int(math.ceil(rmin * (math.tan(th / 2) + 1.0) / DLEN[b] - 1e-9)))   # this corner and a next one up to 90 deg
    first = {b: max(1, int(math.ceil(rmin / DLEN[b] - 1e-9))) for b in range(nd_)}
    expanded = 0
    while q:
        f, g, u, d = heapq.heappop(q)
        if best.get((u, d), 1e9) < g - 1e-12:
            continue
        expanded += 1
        if expanded > 3_000_000:
            return None
        if u == tuple(goal) and d >= 0 and (goal_dirs is None or d in goal_dirs):
            path, k = [u], (u, d)
            while k in prev:
                k = prev[k]
                path.append(k[0])
            return path[::-1]
        for b in use:
            if d >= 0 and b != d and (d, b) not in commit:
                continue
            m = 1 if b == d else (first[b] if d < 0 else commit[(d, b)])
            db = DIRS[b]
            c = list(u)
            cost = g + (0 if b == d or d < 0 else turn * ANG[d, b] / (math.pi / 2))
            ok = True
            reached = False
            for j in range(m):
                c = [c[0] + db[0], c[1] + db[1], c[2] + db[2]]
                if not (0 <= c[0] < n[0] and 0 <= c[1] < n[1] and 0 <= c[2] < n[2]) or not free[c[0], c[1], c[2]]:
                    ok = False
                    break
                cost += DLEN[b] * W[c[0], c[1], c[2]] * (1.0 if b in AXIS_SET else DIAG_COST)
                if tuple(c) == tuple(goal) and (j + 1) * DLEN[b] >= (rmin if d < 0 else 0.5 * m * DLEN[b]) - 1e-9:
                    reached = True
                    break
            if not ok:
                continue
            v = tuple(c)
            if reached and (v != tuple(goal) or (goal_dirs is not None and b not in goal_dirs)):
                continue
            key = (v, b)
            if cost < best.get(key, 1e9) - 1e-12:
                best[key] = cost
                prev[key] = (u, d)
                h = float(np.linalg.norm(np.subtract(v, gc))) * RES * hfac * 0.65
                heapq.heappush(q, (cost + h, cost, v, b))
    return None


def simplify(pts, tol_deg=3.0):
    """Drop points that are (nearly) collinear with their neighbours (direction change below tol_deg)."""
    out = [list(pts[0])]
    for i in range(1, len(pts) - 1):
        a, b, c = np.array(out[-1]), np.array(pts[i]), np.array(pts[i + 1])
        u, v = b - a, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        if lu < 1e-9 or lv < 1e-9 or math.acos(max(-1.0, min(1.0, float(np.dot(u, v) / (lu * lv))))) < math.radians(tol_deg):
            continue
        out.append(list(pts[i]))
    out.append(list(pts[-1]))
    return out


def seg_ok(free, w, V, a, b, wmax):
    L = np.linalg.norm(np.subtract(b, a))
    n = max(2, int(L / (RES / 2)) + 1)
    for t in np.linspace(0, 1, n):
        p = np.add(a, np.multiply(t, np.subtract(b, a)))
        if p[2] >= HI[2]:
            continue
        c = V.cell(p)
        if not free[c] or w[c] > wmax + 1e-9:
            return False
    return True


def string_pull(free, w, V, pts, rmin):
    """Shortcut corners with straight 3D segments that stay free and no less supported (fewer, gentler bends)."""
    pts = [np.array(p) for p in pts]
    out = [pts[0]]
    i = 0
    while i < len(pts) - 1:
        j = len(pts) - 1
        while j > i + 1:
            wm = max(w[V.cell(p)] for p in pts[i:j + 1])
            if seg_ok(free, w, V, pts[i], pts[j], max(wm, 1.0)):
                break
            j -= 1
        out.append(pts[j])
        i = j
    return out


def route_radius(pts):
    """Largest bend radius the polyline can hold at every corner: each corner i takes R tan(theta_i / 2) of straight
    cable from both neighbouring segments; a segment must hold the shares of its two corners (an end segment, at a
    connector, only one). Returns (radius in m, index of the limiting segment); inf for a straight route."""
    pts = simplify(pts)
    th = [0.0]
    for i in range(1, len(pts) - 1):
        u, v = np.subtract(pts[i], pts[i - 1]), np.subtract(pts[i + 1], pts[i])
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        a = 0.0 if lu < 1e-9 or lv < 1e-9 else math.acos(max(-1.0, min(1.0, float(np.dot(u, v) / (lu * lv)))))
        th.append(a if a >= math.radians(3) else 0.0)
    th.append(0.0)
    best, at = float("inf"), None
    for i in range(len(pts) - 1):
        t = math.tan(th[i] / 2) + math.tan(th[i + 1] / 2)
        if t < 1e-9:
            continue
        r = float(np.linalg.norm(np.subtract(pts[i + 1], pts[i]))) / t
        if r < best:
            best, at = r, i
    return best, at


def corner_radii(pts):
    """Available bend radius at each interior corner: straight length on both sides (the whole end segment at a
    connector, half of an interior segment) over tan(theta / 2)."""
    out = []
    for i in range(1, len(pts) - 1):
        u, v = np.subtract(pts[i], pts[i - 1]), np.subtract(pts[i + 1], pts[i])
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        if lu < 1e-9 or lv < 1e-9:
            out.append(float("inf"))
            continue
        th = math.acos(max(-1.0, min(1.0, float(np.dot(u, v) / (lu * lv)))))
        if th < math.radians(3):
            out.append(float("inf"))
            continue
        have = min(lu if i == 1 else lu / 2, lv if i == len(pts) - 2 else lv / 2)
        out.append(have / math.tan(th / 2))
    return out


def bend_repair(free, w, V, pts, rmin, wmax=1.6):
    """Remove corners that cannot hold the minimum bend radius when the shortcut stays free and supported."""
    pts = [list(p) for p in pts]
    for _ in range(40):
        r0, at = route_radius(pts)
        if r0 >= rmin - 1e-6 or at is None:
            break
        done = False
        for j0, j1 in ((at - 1, at + 1), (at, at + 2), (at - 1, at + 2), (at - 2, at + 1), (at, at + 3), (at - 2, at + 2)):
            if j0 < 0 or j1 > len(pts) - 1 or j1 - j0 < 2:
                continue
            if is_axis(pts[j0], pts[j1], 0.5) and seg_ok(free, w, V, pts[j0], pts[j1], wmax):
                cand = pts[:j0 + 1] + pts[j1:]
                if route_radius(cand)[0] > r0 + 1e-6:
                    pts = cand
                    done = True
                    break
        if not done:
            break
    return pts


def shortcut(free, w, V, pts, rmin, short_unsupported=0.100):
    """Replace runs of corners by one straight 3D segment where the segment stays free (keep-outs, components,
    withdrawal paths), stays supported (or is at most short_unsupported long) and the route still holds rmin."""
    pts = [list(p) for p in pts]
    i = 0
    while i < len(pts) - 2:
        best = None
        for j in range(len(pts) - 1, i + 1, -1):
            L = float(np.linalg.norm(np.subtract(pts[j], pts[i])))
            if not is_axis(pts[i], pts[j], 0.5) or not seg_ok(free, w, V, pts[i], pts[j], 1.6 if L > short_unsupported else 6.0):
                continue
            cand = pts[:i + 1] + pts[j:]
            if route_radius(cand)[0] >= rmin - 1e-6:
                best = cand
                break
        if best is not None:
            pts = best
        i += 1
    return pts


def resample(P, step=0.006):
    """Points at equal arc length along a polyline (keeps the ends)."""
    P = np.asarray(P, float)
    sl = np.concatenate([[0.0], np.cumsum(np.linalg.norm(np.diff(P, axis=0), axis=1))])
    n = max(2, int(math.ceil(sl[-1] / step)))
    s = np.linspace(0, sl[-1], n + 1)
    return np.stack([np.interp(s, sl, P[:, i]) for i in range(3)], axis=1)


def smooth_p2p(free, V, a, b, rmin, n=48):
    """Lug-to-lug link as one smooth cubic curve: lugs turn about their studs, so the cable may leave and arrive in any
    horizontal direction, 45 degrees up or down, or straight up or down. Returns the shortest curve (resampled every
    6 mm) that stays in free cells and keeps the curvature radius >= rmin, or None."""
    a, b = np.asarray(a, float), np.asarray(b, float)
    dirs = [np.array([0, 0, 1.0]), np.array([0, 0, -1.0])]
    for t_ in np.radians(np.arange(0, 360, 15)):
        for el in (0.0, math.radians(45), -math.radians(45)):
            dirs.append(np.array([math.cos(t_) * math.cos(el), math.sin(t_) * math.cos(el), math.sin(el)]))
    dirs = np.array(dirs)
    D = float(np.linalg.norm(b - a))
    hs = np.array([0.03, 0.05, 0.08, 0.12, 0.17])
    hs = hs[hs <= max(0.06, 1.6 * D)]
    t = np.linspace(0, 1, n + 1)[None, :, None]
    # all combinations at once, in chunks: (da, db, ha, hb)
    A, B_, HA, HB = np.meshgrid(np.arange(len(dirs)), np.arange(len(dirs)), np.arange(len(hs)), np.arange(len(hs)), indexing="ij")
    A, B_, HA, HB = A.ravel(), B_.ravel(), HA.ravel(), HB.ravel()
    best = None
    for i0 in range(0, len(A), 4000):
        sl = slice(i0, i0 + 4000)
        p1 = a + hs[HA[sl]][:, None] * dirs[A[sl]]
        p2 = b - hs[HB[sl]][:, None] * dirs[B_[sl]]
        p1, p2 = p1[:, None, :], p2[:, None, :]
        P = (1 - t) ** 3 * a + 3 * (1 - t) ** 2 * t * p1 + 3 * (1 - t) * t ** 2 * p2 + t ** 3 * b
        d1 = 3 * (1 - t) ** 2 * (p1 - a) + 6 * (1 - t) * t * (p2 - p1) + 3 * t ** 2 * (b - p2)
        d2 = 6 * (1 - t) * (p2 - 2 * p1 + a) + 6 * t * (b - 2 * p2 + p1)
        cr = np.linalg.norm(np.cross(d1, d2), axis=2)
        sp = np.linalg.norm(d1, axis=2)
        with np.errstate(divide="ignore", invalid="ignore"):
            rad = np.where(cr > 1e-12, sp ** 3 / cr, np.inf)
        ok = rad.min(axis=1) >= rmin * 1.02
        k = np.clip(np.floor((P - LO) / RES).astype(int), 0, V.n - 1)
        ok &= free[k[..., 0], k[..., 1], k[..., 2]].all(axis=1)
        if not ok.any():
            continue
        L = np.linalg.norm(np.diff(P, axis=1), axis=2).sum(axis=1)
        L[~ok] = np.inf
        j = int(np.argmin(L))
        if best is None or L[j] < best[0]:
            best = (float(L[j]), P[j])
    if best is None:
        return None
    return [[round(float(v), 4) for v in p] for p in resample(best[1])]


def corner_need(pts, rmin):
    """Worst bend: for each interior corner the straight length needed (R tan(theta/2)) against the available one."""
    worst = None
    for i in range(1, len(pts) - 1):
        u, v = np.subtract(pts[i], pts[i - 1]), np.subtract(pts[i + 1], pts[i])
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        if lu < 1e-9 or lv < 1e-9:
            continue
        th = math.acos(max(-1.0, min(1.0, float(np.dot(u, v) / (lu * lv)))))
        if th < math.radians(3):
            continue
        need = rmin * math.tan(th / 2)
        have = min(lu if i == 1 else lu / 2, lv if i == len(pts) - 2 else lv / 2)
        r_av = have / math.tan(th / 2)
        if worst is None or r_av < worst["r_mm"] / 1000:
            worst = {"i": i, "deg": round(math.degrees(th)), "r_mm": round(r_av * 1000, 1)}
    return worst


def plen(pts):
    return float(sum(np.linalg.norm(np.subtract(pts[i + 1], pts[i])) for i in range(len(pts) - 1)))


def fillet(pts, rad):
    """Polyline with each corner replaced by an arc of radius rad (or the largest that fits) for drawing."""
    if len(pts) < 3:
        return [list(map(float, p)) for p in pts]
    out = [list(map(float, pts[0]))]
    for i in range(1, len(pts) - 1):
        a, b, c = map(np.array, (pts[i - 1], pts[i], pts[i + 1]))
        u, v = b - a, c - b
        lu, lv = np.linalg.norm(u), np.linalg.norm(v)
        u, v = u / lu, v / lv
        th = math.acos(max(-1.0, min(1.0, float(np.dot(u, v)))))
        if th < math.radians(3):
            out.append(list(map(float, b)))
            continue
        t = min(rad * math.tan(th / 2), (lu if i == 1 else lu / 2) * 0.999, (lv if i == len(pts) - 2 else lv / 2) * 0.999)
        p0, p1 = b - u * t, b + v * t
        k = max(2, int(math.degrees(th) / 15))
        for s in np.linspace(0, 1, k + 1):   # quadratic Bezier close to the arc
            q = (1 - s) ** 2 * p0 + 2 * (1 - s) * s * b + s ** 2 * p1
            out.append(list(map(float, q)))
    out.append(list(map(float, pts[-1])))
    return out


def inside_mask(V):
    """Cells inside the base outline (panel inner faces, chamfered corners); a cable leaves it only at its own end."""
    ii, jj, _ = np.indices(V.n)
    x = LO[0] + (ii + 0.5) * RES
    y = np.abs(LO[1] + (jj + 0.5) * RES)
    ax_ = np.abs(x)
    lim = np.where(ax_ > 0.320, 0.286 - (ax_ - 0.320) * (0.095 / 0.069), 0.286)
    return (ax_ <= 0.368) & (y <= lim)


def route_base(ctx, V, comps, keep, withdraw, cables, cached=None):
    """Route every base section; cables is a list of dicts with id, a/b points, own parts, radius, flags."""
    base_occ = V.struct.copy()
    comp_occ = {}
    for k, (lo, hi) in comps.items():
        g = np.zeros(V.n, bool)
        g[V.slab(lo, hi)] = True
        comp_occ[k] = g
    all_comp = np.zeros(V.n, bool)
    for g in comp_occ.values():
        all_comp |= g
    d_struct = ndimage.distance_transform_edt(~(V.struct), sampling=RES)
    d_struct[V.struct] = 0
    # keep-out grids
    kzs = []
    for k in keep:
        g = np.zeros(V.n, bool)
        g[V.slab(k["lo"], k["hi"])] = True
        if k.get("sector"):   # only the cells inside the bearing sector
            ii_, jj_, _ = np.indices(V.n)
            xx, yy = LO[0] + (ii_ + .5) * RES, LO[1] + (jj_ + .5) * RES
            g &= np.abs(np.degrees(np.arctan2(yy - k["sector"]["y"], xx - k["sector"]["x"]))) <= k["sector"]["deg"]
        kzs.append((k, g))
    slot_cells = np.zeros(V.n, bool)     # cover-slot keep-outs: a cable keeps its outer radius out of them (review of #83)
    for k in keep:
        if str(k["id"]).startswith("cover_slot_"):
            slot_cells[V.slab(k["lo"], k["hi"])] = True
    d_slot = ndimage.distance_transform_edt(~slot_cells, sampling=RES)
    pas = np.zeros(V.n, bool)            # declared protected passages (channels, over-wheel guards)
    for p_ in PASSAGES:
        pas[V.slab(p_["lo"], p_["hi"])] = True
    exz = np.zeros(V.n, bool)            # declared battery and power module exception zone
    if ctx.get("EXCEPTION"):
        exz[V.slab(ctx["EXCEPTION"]["lo"], ctx["EXCEPTION"]["hi"])] = True
    over = {}
    for k, (lo, hi) in comps.items():
        if k in NO_OVER:
            continue
        g = np.zeros(V.n, bool)
        top = (hi[2] + TOP_BAND[k] if k in TOP_BAND else 0.300) if k.startswith(TOP_ACCESS) else hi[2] + OVER_H
        g[V.slab([lo[0] + 0.001, lo[1] + 0.001, hi[2]], [hi[0] - 0.001, hi[1] - 0.001, top])] = True
        gf = np.zeros(V.n, bool)          # above the component top up to the next structure (parts under the base sheet: none)
        if hi[2] <= 0.056:
            over[k] = (g, gf)
            continue   # first structure above: shelf, plate, deck or the cover (3 Nov 2026 rule)
        sl_ = V.slab([lo[0] + 0.001, lo[1] + 0.001, hi[2]], [hi[0] - 0.001, hi[1] - 0.001, 0.300])
        gf[sl_] = ~np.logical_or.accumulate(V.struct[sl_], axis=2)
        over[k] = (g, gf & ~pas)
    wd = []
    for z in withdraw:
        g = np.zeros(V.n, bool)
        g[V.slab(z["lo"], z["hi"])] = True
        for e in z.get("except", []):
            g[V.slab(np.subtract(e, [0.012, 0.012, 0.2]), np.add(e, [0.012, 0.012, 0.2]))] = False
        wd.append((z, g))
    inside = inside_mask(V)
    used = np.zeros(V.n, np.float32)
    power_cells = np.zeros(V.n, bool)
    d_power = None
    ii, jj, kk = np.indices(V.n)
    centres = None
    results = {}
    cached = cached or {}
    for c in cables:
        if c.get("fixed") is not None:   # declared route (battery and power module exception zone): cable or busbar
            pts = [[round(float(v), 4) for v in p] for p in c["fixed"]]
            hit = slot_violations(pts, keep, radius=envelope_radius(c))
            if hit:   # fail closed: a declared route in the cover slot is an error of the declaration, never routed
                results[c["id"]] = {"ok": False, "why": "declared route enters %s (cover slot rule, P-03 rev20.5 item 29)" % ", ".join(hit)}
                continue
            cells = [V.cell(q) for _, q in sample(pts, RES / 2)]
            for p in cells:
                used[p] += 1
                power_cells[p] = True
            d_power = ndimage.distance_transform_edt(~power_cells, sampling=RES)
            results[c["id"]] = {"ok": True, "pts": pts}
            continue
        only = __import__("os").environ.get("OAMR_ROUTE_ONLY")
        if only and c["id"] not in only.split(","):   # test runs: route only the listed cables
            results[c["id"]] = {"ok": False, "why": "not routed in this test run (OAMR_ROUTE_ONLY)"}
            continue
        if c["id"] in cached and isinstance(cached[c["id"]], dict):   # blocked in the last build with the same inputs
            results[c["id"]] = {"ok": False, "why": cached[c["id"]]["blocked"]}
            continue
        if c["id"] in cached and slot_violations(cached[c["id"]], keep, radius=envelope_radius(c)):   # a cached route in the cover slot is dropped and routed again
            cached = {k_: v_ for k_, v_ in cached.items() if k_ != c["id"]}
        if c["id"] in cached:   # same inputs as the last build (harness_routes.json input_hash): reuse the route
            pts = cached[c["id"]]
            cells = [V.cell(q) for _, q in sample(pts, RES / 2)]
            for p in cells:
                used[p] += 1
            if c["power"]:
                for p in cells:
                    power_cells[p] = True
                d_power = ndimage.distance_transform_edt(~power_cells, sampling=RES)
            results[c["id"]] = {"ok": True, "pts": pts}
            continue
        own = set(c["own"])
        r = c["r"]
        occ = base_occ | np.any([comp_occ[k] for k in comp_occ if k not in own], axis=0) if comp_occ else base_occ
        d = ndimage.distance_transform_edt(~occ, sampling=RES)
        free = (d >= r + CLEAR) & inside
        kz = np.zeros(V.n, bool)
        for k, g in kzs:
            if not (own & set(k.get("members", []))):
                kz |= g
        forb = kz | slot_cells | (d_slot <= envelope_radius(c) + RES / 2)   # no cable exempt from the slot, its envelope included
        for k, (g, gf) in over.items():
            if k not in own:
                forb |= g | ((gf & ~exz if c.get("module") else gf) if "over" not in RELAX else False)   # module cables may pass over module parts
        for z, g in wd:
            if not (own & set(z["members"])):
                forb |= g
        free &= ~forb
        # connector entry: within 25 mm of each own end the cable may leave its part and pass the panel it is mounted on
        for p in (c["a"], c["b"]):
            if p is None:
                continue
            ce = V.cell(p)
            rr = int(math.ceil(0.025 / RES))
            sl = tuple(slice(max(0, ce[i] - rr), min(V.n[i], ce[i] + rr + 1)) for i in range(3))
            sub = ((ii[sl] - ce[0]) ** 2 + (jj[sl] - ce[1]) ** 2 + (kk[sl] - ce[2]) ** 2) * RES * RES <= 0.025 ** 2
            others = np.zeros(sub.shape, bool)
            for k, g in comp_occ.items():
                if k not in own:
                    others |= g[sl]
            free[sl] |= sub & ~others & ~kz[sl]
        # supported routes only: within 30 mm of a supporting surface, except near its own connectors, in passages and
        # (module cables) inside the battery and power module
        sup = (d_struct <= SUPPORT_MAX - RES / 2) | pas   # half a cell inside the rule: the check measures to the surfaces (8 Nov 2026)
        if c.get("ez"):   # W01 only (both ends in the module), as the checker applies it; other module cables only at their local exit
            sup |= exz
        for p in (c["a"], c["b"]):
            ce = V.cell(p)
            rr = int(math.ceil(END_FREE / RES))
            sl = tuple(slice(max(0, ce[i] - rr), min(V.n[i], ce[i] + rr + 1)) for i in range(3))
            sup[sl] |= ((ii[sl] - ce[0]) ** 2 + (jj[sl] - ce[1]) ** 2 + (kk[sl] - ce[2]) ** 2) * RES * RES <= END_FREE ** 2
        if "support" not in RELAX:
            free &= sup
        w = np.where(d_struct <= SUPPORT_DIRECT, 1.0, np.where(d_struct <= SUPPORT_STANDOFF, 1.6, 6.0)).astype(np.float32)
        w = np.where(used > 0, w * 0.65, w)
        if c["sensitive"] and d_power is not None:
            w = np.where(d_power < 0.030, w * 2.5, w)
        sa, sb = V.cell(c["a"]), V.cell(c["b"])
        free[sa] = free[sb] = True
        direct = float(np.linalg.norm(np.subtract(c["a"], c["b"])))
        tail = c.get("tail") or []
        sm = smooth_p2p(free, V, c["a"], c["b"], c["rmin"]) if direct <= P2P_MAX and not tail else None
        if sm is not None:   # short link: one smooth curve between the two lugs or connectors
            pts = sm
            path = None
        else:
            up = [i for i, d_ in enumerate(DIRS) if tuple(d_) == (0, 0, 1)]
            path = astar(free, w, sa, sb, c["rmin"], hfac=1.5, goal_dirs=up if tail else None, dirs=AXIS if "axisonly" in RELAX else ROUTE_DIRS)
        if sm is None:
            if path is None:
                results[c["id"]] = {"ok": False, "why": "no route that keeps the rules (components, withdrawal paths, keep-outs, bend radius %d mm)" % round(c["rmin"] * 1000)}
                continue
            pts = [V.centre(p) for p in path]   # ends at the cell centres (within 4.3 mm of the connector point)
            pts = simplify([list(map(float, p)) for p in pts] + [list(map(float, q)) for q in tail])
            pts = bend_repair(free, w, V, pts, c["rmin"])
            pts = simplify(shortcut(free, w, V, pts, c["rmin"]))
            bad45 = [i for i in range(len(pts) - 1) if not is_axis(pts[i], pts[i + 1], 0.5)
                     and (np.linalg.norm(np.subtract(pts[i + 1], pts[i])) > T45_MAX or abs(_planar_angle(pts[i], pts[i + 1]) - 45.0) > 3.0)]
            if bad45:   # a transition longer than 120 mm or not at 45 degrees: try the axis-only route
                p2 = astar(free, w, sa, sb, c["rmin"], hfac=1.5, goal_dirs=up if tail else None, dirs=AXIS)
                if p2 is not None:
                    q = simplify([list(map(float, V.centre(p))) for p in p2] + [list(map(float, q)) for q in tail])
                    q = simplify(shortcut(free, w, V, bend_repair(free, w, V, q, c["rmin"]), c["rmin"]))
                    pts = q
            Lr = plen(pts)
            if Lr > max(DETOUR * direct, direct + 0.40):
                results[c["id"]] = {"ok": False, "why": "the only compliant route is %.2f m for a %.2f m link: no cable passage in the layout" % (Lr, direct), "pts_rejected": pts}
                continue
        hit = slot_violations(pts, keep, radius=envelope_radius(c))
        if hit:   # the smoothed polyline must keep its outer surface out of the slot too (fail closed)
            results[c["id"]] = {"ok": False, "why": "route envelope enters %s (cover slot rule, P-03 rev20.5 item 29)" % ", ".join(hit), "pts_rejected": pts}
            continue
        cells = [V.cell(q) for _, q in sample(pts, RES / 2)]
        for p in cells:
            used[p] += 1
        if c["power"]:
            for p in cells:
                power_cells[p] = True
            d_power = ndimage.distance_transform_edt(~power_cells, sampling=RES)
        results[c["id"]] = {"ok": True, "pts": [[round(float(v), 4) for v in p] for p in pts]}
    return results, d_struct


# ---------------------------------------------------------------- ties, branches, grommets
def nearest_struct(V, d_struct, p):
    """Nearest structure cell to p (name and point), searched in an 80 mm cube."""
    c = V.cell(p)
    rr = 16
    sl = tuple(slice(max(0, c[i] - rr), min(V.n[i], c[i] + rr + 1)) for i in range(3))
    sub = V.struct[sl]
    if not sub.any():
        return None, None
    idx = np.argwhere(sub)
    ctr = LO + (idx + [s.start for s in sl] + 0.5) * RES
    j = int(np.argmin(np.linalg.norm(ctr - p, axis=1)))
    cell = tuple(idx[j] + [s.start for s in sl])
    return V.names[V.struct_id[cell]], ctr[j]


def sample(pts, step=0.005):
    out = []
    s0 = 0.0
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        L = np.linalg.norm(b - a)
        n = max(1, int(L / step))
        for t in np.arange(n) / n:
            out.append((s0 + t * L, a + t * (b - a)))
        s0 += L
    out.append((s0, np.array(pts[-1])))
    return out


def _proj(pts, p):
    best, s0 = (None, 1e9), 0.0
    for i in range(len(pts) - 1):
        a, b = np.array(pts[i]), np.array(pts[i + 1])
        ab = b - a
        L2 = float(ab @ ab)
        t = 0.0 if L2 < 1e-12 else max(0.0, min(1.0, float((np.asarray(p) - a) @ ab) / L2))
        d = float(np.linalg.norm(a + t * ab - p))
        if d < best[1]:
            best = (s0 + t * L2 ** 0.5, d)
        s0 += L2 ** 0.5
    return best


def tie_points(V, d_struct, routes, branches, own_of=None):
    """Tie points of the base routes. Each cable gets a support within 45 mm of both connectors and of every branch
    point and at 140 mm or less in between (the check allows 150 mm / 50 mm). A tie base sits on the structure within
    15 mm, on a standoff up to 60 mm; at a connector without structure nearby, a strain-relief clamp on the part's own
    mounting; at a branch without structure nearby, a lacing tie to the supported trunk. Ties within 15 mm of the route
    of another cable are shared (one tie per bundle)."""
    ties = []
    PITCH, NEAR, TOL = 0.140, 0.045, 0.020

    def new_tie(p, kind=None, on=None):
        for t in ties:
            if np.linalg.norm(np.subtract(t["p"], p)) < 0.012:
                return t
        d = float(d_struct[V.cell(p)])
        name, base = nearest_struct(V, d_struct, p)
        if kind is None:
            kind = "tie base" if d <= SUPPORT_DIRECT else "tie base on standoff"
        t = {"id": "T%03d" % (len(ties) + 1), "p": [round(float(v), 4) for v in p], "on": on or name,
             "base": [round(float(v), 4) for v in base] if (base is not None and kind.startswith("tie base")) else None, "kind": kind, "cables": []}
        if kind == "tie base on a bracket" and t["base"] is None:
            t["kind"] = kind
        ties.append(t)
        return t

    def supported(p):
        return d_struct[V.cell(p)] <= 0.060

    for cid, pts in routes.items():
        sm = sample(pts)
        L = sm[-1][0]
        sup = [(s, p) for s, p in sm if supported(p) and 0.008 <= s <= L - 0.008]
        mine = []

        def have(lo, hi):
            return any(lo - 1e-9 <= s <= hi + 1e-9 for s, _ in mine)

        def take(lo, hi, prefer, fallback_kind):
            for t in ties:   # an existing tie on this route in the window
                s, d = _proj(pts, t["p"])
                if d <= TOL and lo <= s <= hi and t["kind"] != "lacing tie":
                    mine.append((s, t))
                    return
            c = [q for q in sup if lo <= q[0] <= hi]
            if c:
                s, p = min(c, key=lambda q: abs(q[0] - prefer))
                mine.append((s, new_tie(p)))
                return
            if fallback_kind:
                s, p = min(sm, key=lambda q: abs(q[0] - prefer))
                ends = (own_of or {}).get(cid) or (None, None)
                mine.append((s, new_tie(p, kind=fallback_kind, on=ends[0] if s < L / 2 else ends[1])))

        if L > 2 * NEAR:
            take(0.008, NEAR, 0.025, "strain relief at the connector")
            take(L - NEAR, L - 0.008, L - 0.025, "strain relief at the connector")
        for b in branches.get(cid, []):
            sb, _ = _proj(pts, b)
            if not have(sb - NEAR, sb + NEAR):
                take(max(0.0, sb - NEAR), min(L, sb + NEAR), sb, "lacing tie")
        for _ in range(60):   # close the gaps
            ss = sorted([0.0] + [s for s, t in mine if t["kind"] != "lacing tie"] + [L])
            gaps = [(ss[i + 1] - ss[i], ss[i], ss[i + 1]) for i in range(len(ss) - 1)]
            g, a, b = max(gaps)
            if g <= PITCH:
                break
            n0 = len(mine)
            take(a + 0.010, min(b - 0.010, a + PITCH), a + min(PITCH, g / 2 if g < 2 * PITCH else PITCH), None)
            if len(mine) == n0:   # no structure within 60 mm: a tie base on a small bracket (up to 100 mm) where the route comes closest
                c = [q for q in sm if a + 0.010 <= q[0] <= min(b - 0.010, a + PITCH) and d_struct[V.cell(q[1])] <= 0.100]
                if not c:
                    break
                s_, p_ = min(c, key=lambda q: d_struct[V.cell(q[1])])
                mine.append((s_, new_tie(p_, kind="tie base on a bracket")))
        for s, t in mine:
            if cid not in t["cables"]:
                t["cables"].append(cid)
    return ties


def branch_points(routes, harness_of):
    """Points where a cable leaves the bundle of its harness (route within 12 mm of another cable of the harness)."""
    out = {}
    by_h = {}
    for cid, h in harness_of.items():
        if cid in routes:
            by_h.setdefault(h, []).append(cid)
    for h, ids in by_h.items():
        smp = {c: sample(routes[c], 0.005) for c in ids}
        arr = {c: np.array([p for _, p in smp[c]]) for c in ids}
        for c in ids:
            others = [arr[o] for o in ids if o != c]
            if not others:
                continue
            O = np.vstack(others)
            shared = [bool((np.linalg.norm(O - p, axis=1) < 0.012).any()) for p in arr[c]]
            for i in range(1, len(shared)):
                if shared[i] != shared[i - 1]:
                    out.setdefault(c, []).append(arr[c][i if shared[i] else i - 1])
    return out


def grommets(V, routes, own_panels):
    """Penetrations: where a route passes a structure shell (a panel hole at a sensor, a wall or deck opening)."""
    out = []
    for cid, pts in routes.items():
        prev = False
        for s, p in sample(pts, 0.0025):
            c = V.cell(p)
            hit = bool(V.struct[c])
            if hit and not prev:
                nm = V.names[V.struct_id[c]]
                if not any(np.linalg.norm(np.subtract(g["p"], p)) < 0.015 and g["on"] == nm for g in out):
                    out.append({"id": "G%02d" % (len(out) + 1), "p": [round(float(v), 4) for v in p], "on": nm, "cables": [cid]})
                else:
                    for g in out:
                        if np.linalg.norm(np.subtract(g["p"], p)) < 0.015 and cid not in g["cables"]:
                            g["cables"].append(cid)
            prev = hit
    return out


# ---------------------------------------------------------------- lift: energy chain
def energy_chain(U, F):
    """Vertical energy chain behind the static column (base_footprint x, y; z at L1000; travel T 0 to stroke).
    Fixed end on a bracket on the -y face of the static column, moving end under the adapter-plate rear extension;
    the chain hangs in a U with the bend in the y-z plane, 2R between the runs."""
    ax, top = U["col_axis_x"], U["col_top"]
    stroke = F["column"]["stroke"]
    ch = {"type": "plastic energy chain, vertical hanging U arrangement (catalogue class: inner 38 x 25 mm, bend radius 75 mm, "
                  "pitch about 33 mm, e.g. igus E2.1 series 2500; order code to be confirmed)",
          "inner_w": 0.038, "inner_h": 0.025, "outer_w": 0.050, "outer_h": 0.032, "R": 0.075, "pitch": 0.033,
          "x": round(ax - 0.216, 4), "y_fixed": -0.075, "y_moving": 0.075, "fixed_z": 0.600,
          "moving_z0": round(top - 0.080, 4), "stroke": stroke}
    zc_min = F["cover_underside"] + 0.005 + 0.030 + ch["R"]   # loop bottom 35 mm above the cover top at L1000
    L = ch["fixed_z"] + ch["moving_z0"] - 2 * zc_min + math.pi * ch["R"]
    L = math.ceil(L / ch["pitch"]) * ch["pitch"]
    ch["length"] = round(L, 3)
    ch["links"] = int(round(L / ch["pitch"]))
    stops = []
    for T in [round(i * 0.025, 3) for i in range(int(round(stroke / 0.025)) + 1)]:
        M = ch["moving_z0"] + T
        zc = (ch["fixed_z"] + M + math.pi * ch["R"] - L) / 2
        stops.append({"T": T, "moving_end_z": round(M, 4), "loop_centre_z": round(zc, 4), "loop_bottom_z": round(zc - ch["R"], 4),
                      "fixed_run_m": round(ch["fixed_z"] - zc, 4), "moving_run_m": round(M - zc, 4)})
    ch["stops"] = stops
    return ch


def chain_points(ch, T, n_arc=12):
    """Chain centreline at travel T (base frame, z absolute)."""
    st = min(ch["stops"], key=lambda s: abs(s["T"] - T))
    zc = st["loop_centre_z"]
    x = ch["x"]
    pts = [[x, ch["y_fixed"], ch["fixed_z"]], [x, ch["y_fixed"], zc]]
    for i in range(1, n_arc):
        a = math.pi * i / n_arc
        pts.append([x, -ch["R"] * math.cos(a), zc - ch["R"] * math.sin(a)])
    pts += [[x, ch["y_moving"], zc], [x, ch["y_moving"], st["moving_end_z"]]]
    return pts


# ---------------------------------------------------------------- upper body: fixed sleeve, chain, moving section
def arc(c, r, a0, a1, y0, y1, n=12):
    """Arc in the x-z plane about c (x, z) from angle a0 to a1, y linear from y0 to y1."""
    out = []
    for i in range(n + 1):
        t = i / n
        a = a0 + (a1 - a0) * t
        out.append([round(c[0] + r * math.cos(a), 4), round(y0 + (y1 - y0) * t, 4), round(c[1] + r * math.sin(a), 4)])
    return out


def upper_layout(U, ch):
    """Fixed points of the lift and upper-body harness (base_footprint, bp000; moving points at L1000)."""
    ax, top = U["col_axis_x"], U["col_top"]
    # owner decision 8 Nov 2026: two openings left and right of the lift, near the middle of the platform length; a disconnect
    # bulkhead DP-LIFT-L / DP-LIFT-R on the lift base plate over each opening (power left, signal right)
    sides = {}
    for k_, sg in (("L", 1), ("R", -1)):
        lo_, hi_ = DECK_OPEN[k_]
        xc, yc = (lo_[0] + hi_[0]) / 2, (lo_[1] + hi_[1]) / 2
        xo = ax - 0.060   # bulkhead centred on the lift motor lead axis (x 0 at bp000): the motor lead runs straight in y into the column
        sides[k_] = {"inlet": [round(xc, 4), round(yc, 4), 0.318], "outlet": [round(xo, 4), sg * 0.047, 0.345],
                     "box": [[xo - 0.020, min(sg * 0.048, sg * 0.064), 0.306], [xo + 0.020, max(sg * 0.048, sg * 0.064), 0.372]],
                     "deck": [round(xc, 4), round(yc, 4), 0.296]}
    xs = ax - 0.060                                   # sleeve straight up the -y face of the static column from DP-LIFT-R (8 Nov 2026)
    xc_ = ax - 0.175                                  # left bundle crosses behind the lift node to the -y side (clear of the chain)
    dp = dict(sides["R"], node=[ax - 0.1325, -0.050, 0.355], sides=sides,
              cross=[sides["L"]["outlet"], [xc_, 0.047, 0.345], [xc_, -0.047, 0.345], [xs, -0.047, 0.345]])
    rr = (xs - ch["x"]) / 2                           # 180 degree turn of the sleeve into the chain fixed end
    sleeve = [dp["outlet"], [xs, -0.047, ch["fixed_z"]]] + \
        arc([xs - rr, ch["fixed_z"]], rr, 0.0, math.pi, -0.047, ch["y_fixed"])[1:]
    zt = ch["moving_z0"] + 0.051                      # moving trunk under the adapter plate +y edge, on a hung angle
    trunk = [[ch["x"], ch["y_moving"], ch["moving_z0"]], [ch["x"], ch["y_moving"], zt]]
    xp = ax + 0.105                                   # riser beside the plate edge, 15 mm behind the arm post rear face
    up = {"z_trunk": round(zt, 4), "x_riser": round(xp, 4), "sleeve_r": round(rr, 4)}
    return dp, sleeve, trunk, up


def ortho(a, b, order="zyx"):
    """Points from a to b changing one coordinate at a time in the given order (axis-aligned runs along the structure)."""
    out, p = [], list(map(float, a))
    for ax_ in order:
        k = "xyz".index(ax_)
        if abs(p[k] - b[k]) > 1e-6:
            p = list(p)
            p[k] = float(b[k])
            out.append(p)
    return out


def upper_sections(cid, end, U, ch, term, side="R"):
    """Sections of an upper-body cable after DP-LIFT: list of (kind, group, pts). end: the upper terminal key.
    Every run is axis-aligned (3 Nov 2026): along the column T-slots, the hung angle under the adapter plate, the riser on the
    arm post rear face and the post side faces; the chain and the sleeve turn are the only curves."""
    dp, sleeve, trunk, up = upper_layout(U, ch)
    ax, top = U["col_axis_x"], U["col_top"]
    zt, xp = up["z_trunk"], up["x_riser"]
    T = term
    if end in ("lift_node", "lift_motor", "lsens1", "lsens2", "lsens3"):
        if end == "lift_node":   # DP-LIFT node outlet straight along y into the node -y face
            a = [T[end][0], dp["node"][1], T[end][2]]
            return [("column", "col", [a, [T[end][0], T[end][1] - 0.020, T[end][2]]])]
        if end == "lift_motor":
            a = list(dp["sides"][side]["outlet"])
            return [("column", "col", [a] + ortho(a, T[end], "yxz"))]
        p = list(T[end])
        node = list(T["lift_node"])
        # down the column rear face beside the sensors at y -0.060 (T-slot clips), then into the node's -y face
        q = [p[0], -0.060, p[2]]
        r = [p[0], -0.060, node[2]]
        return [("column", "col", [p, q, r, [p[0], -0.020, node[2]]])]   # into the node -y face (the node spans the sensor x)
    chain = chain_points(ch, 0.0)
    sl_ = sleeve if side == "R" else dp["cross"] + sleeve[1:]   # the left bundle crosses behind the lift node and joins the sleeve
    secs = [("sleeve", "col", [list(map(float, q)) for q in sl_]), ("chain", "col", chain)]
    base_mov = trunk + [[xp, ch["y_moving"], zt]]
    p = list(T[end])
    s0 = base_mov[-1]
    if end == "estop2":   # up the chain moving-end bracket, forward along the +y edge of the adapter plate (clip strip), into the gland on the +y side
        a = trunk[0]
        mv = [a, [a[0], a[1], p[2]], [p[0], a[1], p[2]], p]
    elif end in ("arm_l", "arm_r"):   # riser on the arm post rear face to the shoulder height, along the post rear face in y, forward to the arm base connector
        mv = base_mov + ortho(s0, p, "zyx")
    elif end == "zed":
        mv = base_mov + ortho(s0, p, "zyx")
    elif end in ("getac", "light"):   # riser, forward along the post +y side face, in to the device at the profile front
        # a short rise (under two bend radii of a 30 mm class cable, 8 Nov 2026: the light 55 mm lower with the Getac) runs forward at
        # the trunk height first and rises once, into the device from below
        mv = base_mov + ortho(s0, p, "xzy" if abs(p[2] - s0[2]) < 0.065 else "zxy")
    else:
        raise KeyError(end)
    secs.append(("moving", "mov", mv))
    return secs


# ---------------------------------------------------------------- harnesses, labels, disconnect points
HARNESSES = [
    {"id": "W01", "name": "Rear power harness", "route": "rear bay: battery terminals, F0, disconnect, PWR-017, K1/K2, FB-A, charge path; on the rear power plate and the tray-pocket walls"},
    {"id": "W02", "name": "Drive-section harness", "route": "inside the centre-frame arch: motor driver, hub-motor leads and brakes, CAN1, IMU SPI; on the arch walls and the electronics bracket"},
    {"id": "W03", "name": "Left side trunk", "route": "front bay to the rear bay along the left side: floor lane beside the front tier, over-wheel guard L, lane between the left tray and the side panel"},
    {"id": "W04", "name": "Right side trunk", "route": "front bay to the rear bay along the right side: floor lane beside the front tier, over-wheel guard R, lane between the right tray and the side panel"},
    {"id": "W05", "name": "Front sensor harness", "route": "front panel lane behind the front sensors (E-stop, RESET, MB7060 front, TF-Luna front, RPLIDAR, Gemini), into the front tier at the side"},
    {"id": "W07", "name": "Front-tier harness", "route": "inside the front tier (lower plate, shelf, DIN carrier); goes out with the tier"},
    {"id": "W08", "name": "Lift column harness", "route": "lift cable openings beside the lift, DP-LIFT-L (lift motor power) and DP-LIFT-R (CAN3, stop sensors), rear and -y faces of the static column: lift motor, lift node CAN3, lift stop sensors"},
    {"id": "W09", "name": "Upper-body harness", "route": "lift cable openings left (power) and right (signal) of the lift, DP-LIFT-L and DP-LIFT-R, the left bundle behind the lift node to the -y side, fixed sleeve on the -y face of the static column, energy chain behind the column, moving trunk under the adapter plate, risers at the arm post: arms (power, CAN-FD, wrist cameras), ZED Mini, Getac USB-PD, head light, second E-stop"},
]
DEFERRED = {"CBL-P30": "receiver prepared, installed later; KCHG to the receiver output is laid when the receiver is installed (WCH-002)"}
UP_MOV = {"arm_l", "arm_r", "zed", "getac", "light", "estop2"}
UP_COL = {"lift_node", "lift_motor", "lsens1", "lsens2", "lsens3"}
FRONT_SENS = {"estop", "reset", "us_fl", "us_fr", "tof_f", "lidar", "gemini"}
REAR = ("rz_", "battery", "disc", "sb50", "rx")
DRIVE = {"zlac", "zlac_m2", "zlac_pwr", "zlac_can", "motor_l", "motor_r", "imu"}


def harness_of(a, b, pts, tier):
    e = {a, b}
    if e & UP_MOV:
        return "W09"
    if e & UP_COL:
        return "W08"
    if all(x.startswith(REAR) for x in e):
        return "W01"
    if e & DRIVE:
        return "W02"
    if e & FRONT_SENS:
        return "W05"
    if all(x in tier for x in e):
        return "W07"
    mid = [p for p in (pts or []) if abs(p[0]) < 0.12]
    if mid:
        return "W03" if np.mean([p[1] for p in mid]) > 0 else "W04"
    return "W03" if any(x.startswith(("bay_din", "bay_ddr", "bay_pwr032", "bay_rsd60")) for x in e) else "W04"


def zones_of(pts, tier_box):
    """Readable route: the zones a base route passes."""
    out = []
    for p in pts:
        x, y, z = p
        if tier_box[0][0] <= x <= tier_box[1][0] and abs(y) <= tier_box[1][1]:
            k = "front tier"
        elif x > 0.330:
            k = "front panel lane"
        elif x > 0.137:
            k = "front %s lane" % ("left" if y > 0 else "right")
        elif x > -0.137:
            k = ("over-wheel guard %s" % ("L" if y > 0 else "R")) if abs(y) > 0.20 and z > 0.19 else ("lift cable opening" if z > 0.285 else "drive section (arch)")
        elif x > -0.277:
            k = ("rear %s lane (beside the tray)" % ("left" if y > 0 else "right")) if abs(y) > 0.255 else ("battery tray (own)" if abs(y) > 0.097 else "between the trays")
        else:
            k = "rear zone"
        if not out or out[-1] != k:
            out.append(k)
    return out


def run(ctx, F, cache=None):
    """Route and document the whole harness. Returns a dict for build.py (see the keys at the end)."""
    U, TERM0, IDT, CAB = ctx["U"], ctx["TERM"], ctx["ID_OF_TERM"], ctx["CAB"]
    ch = energy_chain(U, F)
    dp, sleeve, trunk, upl = upper_layout(U, ch)
    TERM = dict(TERM0)
    ax, top = U["col_axis_x"], U["col_top"]
    eh = F["second_estop"]["housing"]
    TERM["estop2"] = [round(ax - 0.025, 4), round(eh[1] / 2 + 0.002, 4), round(top + 0.010 + 0.014, 4)]   # gland on the +y side
    deck = dp["deck"]
    decks = {k_: v_["deck"] for k_, v_ in dp["sides"].items()}
    ctx = dict(ctx, deck_exit=deck, deck_exits=decks)
    V, comps, keep, withdraw, guards = build_model(ctx)
    tier = set(withdraw[[w["id"] for w in withdraw].index("front_tiers")]["members"]) if any(w["id"] == "front_tiers" for w in withdraw) else set()
    tier_box = [w for w in withdraw if w["id"] == "front_tiers"][0]
    tier_box = (tier_box["lo"], tier_box["hi"])

    def own(a):
        p = IDT.get(a, a)
        s = {p}
        for g in comps:
            if g == a or g.startswith(a + "_"):
                s.add(g)
        if a == "battery+":
            s |= {"battery_cells_left", "battery_tray_left"}
        if a == "battery-":
            s |= {"battery_cells_right", "battery_tray_right"}
        return s

    tier_ends = {k for k in TERM if own(k) & tier}
    base_jobs, meta = [], {}
    for c in CAB:
        cid, a, b, fn, dom, gauge, od, ca, cb, pin, bomref = c
        m = {"id": cid, "a": a, "b": b, "fn": fn, "dom": dom, "gauge": gauge, "od": od, "ca": ca, "cb": cb, "pin": pin, "bom": bomref,
             "rmin": min_bend_static(gauge, od), "flex": min_bend_flex(od), "own": sorted(own(a) | own(b)), "sections": []}
        meta[cid] = m
        if cid in DEFERRED:
            m["status"] = "deferred: " + DEFERRED[cid]
            continue
        if a not in TERM or b not in TERM:
            miss = ", ".join(k for k in (a, b) if k not in TERM)
            if b in UP_MOV and a not in TERM:   # the upper part (DP-LIFT to the consumer) is defined; the base end waits for its part
                m["lift"] = True
                m["upper"] = (None, b)
                m["status"] = "partly routed: DP-LIFT to %s; base end not placed (%s, GI-080)" % (b, miss)
                continue
            m["status"] = "not routed: endpoint not placed (%s)" % miss
            continue
        up_b = b in UP_MOV or b in UP_COL
        up_a = a in UP_MOV or a in UP_COL
        m["lift"] = b in UP_MOV or a in UP_MOV
        if up_a and up_b:
            m["upper"] = (a, None)
            continue
        if up_a:   # route from the base end; the sections run base > chain > moving, the A end is the upper one
            a, b = b, a
            up_a, up_b = False, True
            m["swap"] = True
        if up_b:
            m["upper"] = (None, b)
        pa = list(TERM[a])
        m["dp_side"] = dp_side(dom)
        dk_ = decks[m["dp_side"]]
        pb = [dk_[0], dk_[1], 0.2975] if up_b else list(TERM[b])
        m["module"] = any(str(x).startswith(REAR) for x in (a, b))
        fx = (ctx.get("FIXED") or {}).get(cid)
        if fx:
            m["fixed"] = fx["kind"]
            m["zone"] = fx["zone"]
        base_jobs.append({"id": cid, "a": pa, "b": pb, "own": own(a) | own(b), "r": od / 2000, "rmin": m["rmin"] / 1000, "fixed": fx["pts"] if fx else None,
                          "sensitive": is_sensitive(fn, gauge) and dom == "SIG", "power": is_power(dom, gauge), "dom": dom, "up": up_b,
                          "module": any(str(x).startswith(REAR) for x in (a, b)),
                          "ez": all(str(x).startswith(REAR) or x in ("battery+", "battery-") for x in (a, b)),
                          "tail": [list(dp["sides"][m["dp_side"]]["inlet"])] if up_b else []})
    order = {"BAT": 0, "SAFE": 1, "R24": 2, "LV": 3, "SIG": 4}
    base_jobs.sort(key=lambda c: (order[c["dom"]], -c["r"], c["id"]))
    key = cache.get("key") if cache else None
    res, d_struct = route_base(ctx, V, comps, keep, withdraw, base_jobs, cached=(cache or {}).get("routes"))
    routes = {}
    for j in base_jobs:
        r = res[j["id"]]
        m = meta[j["id"]]
        if not r["ok"]:
            m["status"] = "blocked: %s" % r["why"]
            continue
        pts = r["pts"]
        routes[j["id"]] = pts
        m["sections"].append({"kind": "base", "group": "base", "pts": pts})
    for cid, m in meta.items():
        if "upper" in m and (m["upper"][0] is not None or cid in routes or m["status"].startswith("partly")):
            a, b = m["upper"]
            for kind, grp, pts in upper_sections(cid, a or b, U, ch, TERM, m.get("dp_side") or dp_side(m["dom"])):
                m["sections"].append({"kind": kind, "group": grp, "pts": [[round(float(v), 4) for v in p] for p in pts]})
            m.setdefault("status", "routed")
        elif m["sections"]:
            m.setdefault("status", "routed")
    for cid, m in meta.items():
        pts_all = [p for s in m["sections"] for p in s["pts"]]
        m["harness"] = harness_of(m["a"], m["b"], [p for s in m["sections"] if s["kind"] == "base" for p in s["pts"]], tier_ends)
    # rule data for the checker: support distance along each base route (every 10 mm), declared 45 degree transitions
    for cid, m in meta.items():
        for sec in m["sections"]:
            if sec["kind"] not in ("base", "moving", "column"):
                continue
            pts = sec["pts"]
            t45 = [i for i in range(len(pts) - 1) if not is_axis(pts[i], pts[i + 1], 0.5)]
            sec["t45"] = t45
            if sec["kind"] == "base":
                sec["support"] = [[round(float(sv), 3), round(float(d_struct[V.cell(q)]) * 1000, 1)] for sv, q in sample(pts, 0.010)]
    sep = separation(routes, meta, base_jobs)
    hmap = {cid: m["harness"] for cid, m in meta.items() if cid in routes}
    br = branch_points(routes, hmap)
    ends_of = {}
    for c_ in routes:
        a_, b_ = meta[c_]["a"], meta[c_]["b"]
        if meta[c_].get("swap"):
            a_, b_ = b_, a_
        ends_of[c_] = (IDT.get(a_, a_), IDT.get(b_, b_) if b_ not in UP_MOV and b_ not in UP_COL else "lift cable opening grommet")
    ties = tie_points(V, d_struct, routes, br, ends_of)
    # upper-body clips: sleeve and column on the static column T-slots, moving trunk on the hung angle, risers on the post
    for cid, m in meta.items():
        for s in m["sections"]:
            if s["kind"] in ("sleeve", "column", "moving"):
                on = {"sleeve": "static column -y T-slot (P-clip)", "column": "static column rear T-slot (clip)", "moving": "hung angle under the adapter plate / arm post T-slot (clip)"}[s["kind"]]
                for p in clip_points(s["pts"]):
                    t = next((t for t in ties if np.linalg.norm(np.subtract(t["p"], p)) < 0.012), None)
                    if t is None:
                        t = {"id": "T%03d" % (len(ties) + 1), "p": [round(float(v), 4) for v in p], "on": on, "base": None, "kind": "clip", "cables": [], "group": "col" if s["group"] == "col" else "mov"}
                        ties.append(t)
                    if cid not in t["cables"]:
                        t["cables"].append(cid)
    grom = grommets(V, routes, None)
    for k_, dk_ in sorted(decks.items()):
        grom.append({"id": "G%02d" % (len(grom) + 1), "p": [dk_[0], dk_[1], 0.294], "on": "lift cable opening %s (%s) beside the lift: edge grommet" % ("left" if k_ == "L" else "right", "power" if k_ == "L" else "signal"),
                     "cables": sorted(c for c in routes if meta[c].get("upper") and meta[c].get("dp_side") == k_)})
    xe = TERM["estop2"]
    grom.append({"id": "G%02d" % (len(grom) + 1), "p": [round(xe[0] - 0.010, 4), 0.036, round(top + 0.005, 4)], "on": "adapter plate (second E-stop loop, moving)", "cables": [c for c, m in meta.items() if m["b"] == "estop2"]})
    # labels and disconnect points
    for cid, m in meta.items():
        n = cid.split("-")[1]
        m["label_a"], m["label_b"] = "%s-%s-A" % (m["harness"], n), "%s-%s-B" % (m["harness"], n)
        dps = []
        if m["a"] in tier_ends and m["b"] not in tier_ends or m["b"] in tier_ends and m["a"] not in tier_ends:
            dps.append("DP-FT (front tier: pluggable connector at the tier part)")
        if {m["a"], m["b"]} & {"battery+", "battery-"} or cid == "CBL-P60":
            dps.append("DP-TRAY-%s (tray lead connector)" % ("L" if "battery+" in (m["a"], m["b"]) else "R"))
        if m.get("upper") and m["upper"][0] is None:   # cables between the base and the lift; not the ones that stay on the column
            dps.append("DP-LIFT-%s (bulkhead on the lift base plate, %s of the lift)" % (m.get("dp_side", "R"), "left" if m.get("dp_side") == "L" else "right"))
        if "fan" in (m["a"], m["b"]):
            dps.append("DP-FAN (fan lead connector at the front end of CH-C1; the fan comes off with the cover)")
        if "rz_bms" in (m["a"], m["b"]):
            dps.append("DP-BMS (at the BMS: B- and P- bolted, sense and CAN2 plugged; BMS out through the right side panel)")
        if m["b"] in ("arm_l", "arm_r"):
            dps.append("arm base connector (existing)")
        m["disconnect"] = "; ".join(dps)
    # chain clearances per state (moving obstacles drawn by model.js, static ones from the layout)
    LRj = ctx["LR"]
    for st in ch["stops"]:
        st["clash"] = chain_clash(ch, st, U, F, LRj, dp)
    ch["min_bottom_z"] = round(F["cover_underside"] + 0.006 + 0.015, 4)
    ch["slack_req_m"] = 0.020
    ch["bundle"] = chain_bundle(meta)
    upl["sleeve_r_bundle"] = round((math.sqrt(sum(m["od"] ** 2 for m in meta.values() if m.get("lift"))) * 1.15 + 2) / 2000, 4)
    over_to = {}
    for k, (lo, hi) in comps.items():   # z of the first structure above each 10 mm cell
        if hi[2] <= 0.056:   # under the base sheet (castors): the base sheet is above it
            continue   # (z of a component footprint cell: the cover if no structure above)
        xs = np.arange(lo[0] + 0.005, hi[0], 0.010)
        ys = np.arange(lo[1] + 0.005, hi[1], 0.010)
        grid = []
        for x in xs:
            row = []
            for y in ys:
                c0 = V.cell([x, y, hi[2]])
                col = V.struct[c0[0], c0[1], c0[2]:]
                idx = np.argmax(col) if col.any() else None
                row.append(round(float(LO[2] + (c0[2] + idx) * RES), 3) if idx is not None else 0.300)
            grid.append(row)
        over_to[k] = {"x0": round(float(lo[0]), 4), "y0": round(float(lo[1]), 4), "res": 0.010, "z": grid}
    return {"over_to": over_to, "separation": sep, "meta": meta, "routes": routes, "ties": ties, "branches": br, "grommets": grom, "guards": guards, "chain": ch, "dp": dp,
            "sleeve": sleeve, "upper": upl, "comps": comps, "keep": keep, "withdraw": withdraw, "jobs": {j["id"]: j for j in base_jobs},
            "raw": {k: v for k, v in res.items()}, "tier": sorted(tier), "exception": ctx.get("EXCEPTION")}


def separation(routes, meta, jobs):
    """Separation of each sensitive cable from the power cables: share of its base route length farther than SEP_WORK from
    every power cable route (crossings excluded within 15 mm of a crossing point). Working value, verify."""
    J = {j["id"]: j for j in jobs}
    pw = [np.array([q for _, q in sample(routes[c], 0.005)]) for c in routes if J.get(c, {}).get("power")]
    P = np.vstack(pw) if pw else np.zeros((0, 3))
    out = []
    for c in sorted(routes):
        if not J.get(c, {}).get("sensitive"):
            continue
        sm = sample(routes[c], 0.005)
        L = sm[-1][0]
        if L <= 0 or not len(P):
            continue
        Q = np.array([q for _, q in sm])
        d = np.sqrt(((Q[:, None, :] - P[None, :, :]) ** 2).sum(-1)).min(1)
        ok = float((d >= SEP_WORK).mean())
        out.append({"id": c, "length_m": round(L, 3), "pct_separated": round(100 * ok, 1), "work_mm": SEP_WORK * 1000,
                    "min_mm": round(float(d.min()) * 1000, 1)})
    return out


def clip_points(pts):
    """Clip positions along a fixed upper-body section: <= 140 mm apart, <= 45 mm from both ends."""
    sm = sample(pts, 0.005)
    L = sm[-1][0]
    if L <= 0.09:
        return [sm[len(sm) // 2][1]]
    n = max(1, int(math.ceil((L - 2 * 0.040) / TIE_PITCH)))
    ss = [0.040 + i * (L - 0.080) / n for i in range(n + 1)]
    out = []
    for s in ss:
        j = min(range(len(sm)), key=lambda k: abs(sm[k][0] - s))
        out.append(sm[j][1])
    return out


def chain_bundle(meta):
    cab = [m for m in meta.values() if m.get("lift") and any(s["kind"] == "chain" for s in m["sections"])]
    area = sum(math.pi * (m["od"] / 2) ** 2 for m in cab)
    return {"cables": [m["id"] for m in cab], "count": len(cab), "area_mm2": round(area, 1), "max_od_mm": max(m["od"] for m in cab) if cab else 0,
            "fill_pct": round(100 * area / (38 * 25), 1), "flex_min_mm": max(m["flex"] for m in cab) if cab else 0,
            "width_sum_mm": round(sum(m["od"] for m in cab) * 1.1, 1)}


def chain_clash(ch, st, U, F, LR, dp):
    """Chain envelope (both runs and the loop) against the column, the lift sensors, the flag rod and flag (moving),
    the lift node, DP-LIFT, the fixed sleeve and the cover, at travel st['T'] (3 mm clearance)."""
    ax, top = U["col_axis_x"], U["col_top"]
    T = st["T"]
    x0, x1 = ch["x"] - ch["outer_w"] / 2, ch["x"] + ch["outer_w"] / 2
    h = ch["outer_h"] / 2
    zc = st["loop_centre_z"]
    env = [("fixed run", [x0, ch["y_fixed"] - h, zc], [x1, ch["y_fixed"] + h, ch["fixed_z"]]),
           ("moving run", [x0, ch["y_moving"] - h, zc], [x1, ch["y_moving"] + h, st["moving_end_z"]]),
           ("loop", [x0, -ch["R"] - h, zc - ch["R"] - h], [x1, ch["R"] + h, zc])]
    rod_x = [ax + v for v in LR["rod_x"]] if "rod_x" in LR else [ax - 0.183, ax - 0.163]
    rod_y = LR.get("rod_y", [0.028, 0.048])
    c = top + T
    obs = [("static column", [ax - 0.120, -0.030, F["lift_plate"]["top"]], [ax + 0.120, 0.030, U["static_top"]]),
           ("lift stop sensors and brackets", [ax - 0.160, -0.040, 0.30], [ax - 0.120, 0.024, 0.80]),
           ("flag rod", [rod_x[0], rod_y[0], c - F["lift_rear"]["rod"]["len"]], [rod_x[1], rod_y[1], c]),
           ("adapter plate", [ax + LR.get("plate_rear_x", -0.185), -0.050, c], [ax + 0.300, 0.050, c + 0.010]),
           ("lift node", [ax - 0.145, -0.020, 0.325], [ax - 0.120, 0.020, 0.385]),
           ("DP-LIFT-L", dp["sides"]["L"]["box"][0], dp["sides"]["L"]["box"][1]),
           ("DP-LIFT-R", dp["sides"]["R"]["box"][0], dp["sides"]["R"]["box"][1]),
           ("left bundle cross run", [dp["cross"][1][0] - 0.009, -0.056, 0.336], [dp["cross"][1][0] + 0.009, 0.056, 0.354]),
           ("cover", [-0.390, -0.291, 0.0], [0.390, 0.291, F["cover_underside"] + 0.006])]
    for k, (lo, hi) in (LR.get("guide_boxes") or {}).items():   # flag rod guide (static, column frame x)
        obs.append(("flag rod guide " + k, [ax + lo[0] - 0.002, lo[1] - 0.002, lo[2] - 0.002], [ax + hi[0] + 0.002, hi[1] + 0.002, hi[2] + 0.002]))
    out = []
    for nm, lo, hi in env:
        for on, olo, ohi in obs:
            if all(lo[i] < ohi[i] + 0.003 and olo[i] - 0.003 < hi[i] for i in range(3)):
                out.append("%s / %s" % (nm, on))
    return out


# ---------------------------------------------------------------- outputs
def input_key(ctx, F, jobs_src=None):
    """Hash of everything the base routes depend on (geometry, endpoints, cable classes, this module)."""
    import hashlib
    import json as _j
    import os as _o
    import inspect
    h = hashlib.sha256()
    for fn in (build_model, wheel_guards, inside_mask, route_base, astar, smooth_p2p, resample, shortcut, bend_repair, seg_ok, simplify, route_radius, is_axis, channel_prims):
        h.update(inspect.getsource(fn).encode())
    h.update(repr((BRANCH_X, CH_DROP, DIAG_COST, T45_MAX, PASSAGES, SUPPORT_MAX, END_FREE, AXIS_TOL_DEG, RES, LO.tolist(), HI.tolist(), COVER_BAND, OVER_H, SUPPORT_DIRECT, SUPPORT_STANDOFF, CLEAR, NO_OVER, P2P_MAX, DETOUR, OPENINGS,
                   STRUCT_GLB, NO_SUPPORT_GLB, STRUCT_PLACEMENT, IGNORE_PLACEMENT, TOP_ACCESS, UP_MOV, UP_COL)).encode())
    for k in sorted(ctx["G"]):
        h.update(k.encode())
        h.update(np.round(np.asarray(ctx["G"][k]["v"]), 4).tobytes())
    geo = {k: v for k, v in ctx["geo"].items() if not k.startswith(IGNORE_PLACEMENT)}
    h.update(_j.dumps(geo, sort_keys=True, default=str).encode())
    h.update(_j.dumps({k: [round(float(x), 4) for x in v] for k, v in ctx["TERM"].items()}, sort_keys=True).encode())
    h.update(_j.dumps([list(map(str, c)) for c in ctx["CAB"]]).encode())
    h.update(_j.dumps({k: [list(map(float, v[1])), list(map(float, v[2]))] for k, v in ctx["fbd"].items()}, sort_keys=True).encode())
    h.update(_j.dumps(F, sort_keys=True, default=str).encode())
    h.update(_j.dumps(ctx.get("FIXED") or {}, sort_keys=True, default=str).encode())
    return h.hexdigest()[:16]


def load_cache(path, ctx, F):
    import json as _j
    key = input_key(ctx, F)
    try:
        old = _j.load(open(path, encoding="utf-8"))
    except (OSError, ValueError):
        return {"key": key}
    if old.get("input_hash") == key:
        return {"key": key, "routes": old.get("base_routes_raw", {})}
    return {"key": key}


def routes_json(HR, rows, key):
    meta = HR["meta"]
    cables = []
    for r in rows:
        m = meta[r["id"]]
        if not m["sections"] or not (m["status"] == "routed" or m["status"].startswith("partly")):
            continue
        cables.append({"id": r["id"], "harness": m["harness"], "label_a": m["label_a"], "label_b": m["label_b"], "gauge": m["gauge"], "kind": m.get("fixed", "cable"),
                       "module": bool(m.get("module")), "power": is_power(m["dom"], m["gauge"]), "sensitive": is_sensitive(m["fn"], m["gauge"]) and m["dom"] == "SIG",
                       "od_mm": m["od"], "min_bend_mm": m["rmin"], "flex_min_mm": m["flex"], "own": m["own"], "lift": bool(m.get("lift")),
                       "slack_min_m": 0.030 if m.get("lift") else 0.0,
                       "sections": [dict({"kind": s["kind"], "group": s["group"], "pts": [[round(float(v), 4) for v in p] for p in s["pts"]]},
                                         **{k: s[k] for k in ("t45", "support") if k in s}) for s in m["sections"]]})
    obstacles = [dict({"id": k, "lo": [round(float(v), 4) for v in lo], "hi": [round(float(v), 4) for v in hi], "top_access": k.startswith(TOP_ACCESS)},
                      **({"top_band_m": TOP_BAND[k]} if k in TOP_BAND else {}))
                 for k, (lo, hi) in sorted(HR["comps"].items()) if k not in NO_OVER]
    ch = dict(HR["chain"])
    return {"about": "Harness routes of the roadmap model (generated by scripts/roadmap_model/harness.py through build.py; checked by "
                     "scripts/check_roadmap.py). Frame base_footprint, bp000; moving sections at L1000. Units m.",
            "input_hash": key,
            "rules": {"max_span_m": MAX_SPAN, "tie_near_m": 0.050, "tie_tol_m": 0.030, "over_band_m": OVER_H, "entry_m": 0.025,
                      "axis_tol_deg": AXIS_TOL_DEG, "t45_max_m": T45_MAX, "support_max_m": SUPPORT_MAX, "end_free_m": END_FREE, "sep_work_m": SEP_WORK,
                      "over_to_structure": True,
                      "class_min_bend_mm": {"25 mm²": 60}},
            "harnesses": [dict(h, cables=sorted(c["id"] for c in cables if c["harness"] == h["id"]),
                               all_cables=sorted(k for k, m in meta.items() if m["harness"] == h["id"])) for h in HARNESSES],
            "obstacles": obstacles, "withdrawal": HR["withdraw"], "keep_out": HR["keep"],
            "exception_zones": [dict(HR["exception"], cables=sorted(c["id"] for c in cables if c["harness"] == HR["exception"]["harness"]))] if HR.get("exception") else [],
            "zones": ZONES, "corridors": CORRIDORS,
            "passages": PASSAGES, "separation": HR.get("separation", []), "over_to": HR.get("over_to", {}),
            "ties": [{k: t[k] for k in ("id", "p", "on", "kind", "cables")} for t in HR["ties"]],
            "branches": [{"cable": c, "p": [round(float(v), 4) for v in p]} for c, ps in sorted(HR["branches"].items()) for p in ps],
            "grommets": HR["grommets"], "guards": HR["guards"], "dp_lift": HR["dp"], "chain": ch, "cables": cables,
            "unrouted": {k: m["status"] for k, m in meta.items() if m["status"] != "routed"},
            "base_routes_raw": {k: (v["pts"] if v.get("ok") else {"blocked": v.get("why", "")}) for k, v in HR["raw"].items()}}


def fasteners(HR):
    """Fastener schedule rows (joint, part, size, qty, standard, material, class, drawn) of the harness fittings."""
    ties = HR["ties"]
    direct = [t for t in ties if t["kind"] == "tie base"]
    stand = [t for t in ties if t["kind"] == "tie base on standoff"]
    clips = [t for t in ties if t["kind"] == "clip"]
    sr = [t for t in ties if t["kind"] == "strain relief at the connector"]
    brk = [t for t in ties if t["kind"] == "tie base on a bracket"]
    lace = [t for t in ties if t["kind"] == "lacing tie"]
    col = [t for t in clips if t.get("group") == "col"]
    mov = [t for t in clips if t.get("group") == "mov"]
    out = [("Harness tie bases on the base sheet, side panels, arch and brackets (screw-mount tie base, cable tie)", "ISO 7380 button head screw + M4 blind rivet nut", "M4 x 8", len(direct), "ISO 7380", "A2", "proposed", "y"),
           ("Harness tie bases on standoffs (route 15 to 40 mm from the surface)", "M4 hex standoff F-F + 2 x ISO 7380 + M4 blind rivet nut", "M4 x 20 standoff, M4 x 8", len(stand), "DIN 7380 / hex standoff", "A2 / brass", "proposed", "y"),
           ("Strain-relief clamps at connectors with no structure within 60 mm (on the part's own mounting bracket or DIN rail)", "cable clamp + ISO 7380 into the part mounting", "M3 x 8", len(sr), "ISO 7380", "A2", "proposed", "y"),
           ("Tie bases on small brackets (route 60 to 100 mm from the nearest structure)", "2 mm aluminium angle bracket + ISO 7380 + M4 blind rivet nut; tie base M4 x 8", "M4 x 8", 2 * len(brk), "ISO 7380", "A2", "proposed", "y"),
           ("Lacing ties at branches to the supported trunk (cable tie, no fastener)", "cable tie", "-", len(lace), "-", "PA66", "proposed", "y"),
           ("Sleeve and lift-sensor cable clips on the static column T-slots", "P-clip + M5 T-slot nut + ISO 7380", "M5 x 10", len(col), "ISO 7380", "steel zinc", "proposed", "y"),
           ("Moving-trunk and riser clips on the hung angle and the arm post", "P-clip + ISO 7380 (angle: M4 rivet nut; post: M6 T-slot nut)", "M4 x 8 / M6 x 10", len(mov), "ISO 7380", "A2", "proposed", "y"),
           ("Over-wheel cable guards to the side-panel inner faces", "ISO 7380 + M4 blind rivet nut", "M4 x 8", 3 * len(HR["guards"]), "ISO 7380", "A2", "proposed", "y"),
           ("DP-LIFT-L and DP-LIFT-R connector plates to the lift base plate", "ISO 4762 into tapped holes", "M5 x 10", 4, "ISO 4762", "A2", "proposed", "n"),
           ("Energy-chain fixed end bracket to the static column -y T-slot", "ISO 4762 + M5 T-slot nut", "M5 x 10", 2, "ISO 4762", "steel zinc", "proposed", "n"),
           ("Energy-chain end connectors to their brackets (fixed and moving end)", "ISO 7380 + nut (chain end pins)", "M4 x 10", 4, "ISO 7380", "A2", "proposed", "n"),
           ("Energy-chain moving end bracket and hung angle under the adapter plate +y edge", "ISO 4762 into tapped holes in the adapter plate", "M5 x 10", 4, "ISO 4762", "A2", "proposed", "n")]
    return [o for o in out if o[3]]


def cad_changes(HR):
    """Chassis mounting points and parts for the mechanical owner (CAD changes)."""
    rows = []
    by = {}
    for t in HR["ties"]:
        if t["kind"] == "clip":
            continue
        by.setdefault((t["on"] or "unknown", t["kind"]), []).append(t)
    for (on, kind), ts in sorted(by.items()):
        what = {"tie base": "M4 blind rivet nut (6.0 mm hole) for a screw-mount tie base", "tie base on standoff": "M4 blind rivet nut (6.0 mm hole) for a tie base on an M4 standoff",
                "strain relief at the connector": "M3 tapped hole in the part mounting for a strain-relief clamp", "lacing tie": "no hole (lacing tie to the trunk)",
                "tie base on a bracket": "small angle bracket (new part) on an M4 blind rivet nut, tie base on the bracket"}[kind]
        rows.append({"item": "tie points" if kind != "lacing tie" else "lacing ties", "part": on, "change": "%d x %s" % (len(ts), what),
                     "qty": len(ts), "where": "; ".join("%s %s" % (t["id"], [round(v * 1000) for v in t["p"]]) for t in ts)})
    gb = {}
    for g in HR["grommets"]:
        gb.setdefault(g["on"], []).append(g)
    for on, gs in sorted(gb.items()):
        rows.append({"item": "penetrations", "part": on, "change": "%d x cable hole with grommet or edge trim (hole size per cable set)" % len(gs), "qty": len(gs),
                     "where": "; ".join("%s %s" % (g["id"], [round(v * 1000) for v in g["p"]]) for g in gs)})
    for gd in HR["guards"]:
        rows.append({"item": "new part", "part": gd["id"], "change": "over-wheel cable guard, 2 mm aluminium tray with a 22 mm lip, 260 mm long, 3 x M4 rivet nuts in the side panel; edge trim on both ends",
                     "qty": 1, "where": "z %.0f mm (8 mm above the tyre top), x -130 to 130 mm" % (gd["z"] * 1000)})
    ch = HR["chain"]
    rows += [{"item": "new part", "part": "DP-LIFT-L and DP-LIFT-R brackets", "change": "bulkhead connector plate over each lift cable opening on the lift base plate (2 x M5 tapped holes each in MEC-019)", "qty": 2, "where": "; ".join(str([[round(v * 1000) for v in p] for p in HR["dp"]["sides"][k]["box"]]) for k in ("L", "R"))},
             {"item": "deck", "part": "lift base plate MEC-019, arch top sheet and backing plate", "change": "two lift cable openings 50 x 24 mm left and right of the lift, between the 4 x M8 arch bolts, edge grommet in each (owner decision 8 Nov 2026)", "qty": 2, "where": "; ".join(str([round(v * 1000) for v in HR["dp"]["sides"][k]["deck"]]) for k in ("L", "R"))},
             {"item": "new part", "part": "energy-chain fixed end bracket", "change": "angle bracket on the -y T-slot of the static column, chain fixed end at z %.0f mm" % (ch["fixed_z"] * 1000), "qty": 1, "where": "x %.0f, y %.0f mm" % (ch["x"] * 1000, ch["y_fixed"] * 1000)},
             {"item": "new part", "part": "energy-chain moving end bracket and hung angle", "change": "bracket under the adapter-plate rear extension and a 25 x 25 x 3 angle along the plate +y edge (4 x M5 tapped holes in the adapter plate)", "qty": 1, "where": "x %.0f to %.0f, y %.0f mm" % (ch["x"] * 1000, HR["upper"]["x_riser"] * 1000, ch["y_moving"] * 1000)},
             {"item": "adapter plate", "part": "adapter plate (moving)", "change": "cable hole with grommet for the second E-stop loop beside the lift stage", "qty": 1, "where": str([round(v * 1000) for v in HR["grommets"][-1]["p"]])},
             {"item": "static column", "part": "DOLD column -y face", "change": "T-slot nuts for the sleeve P-clips and the chain fixed end (no machining)", "qty": len([t for t in HR["ties"] if t.get("group") == "col"]) + 2, "where": "-y and rear faces"}]
    return rows
