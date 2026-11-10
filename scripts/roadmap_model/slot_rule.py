# SPDX-License-Identifier: MIT
"""Cover-slot rule (owner rule 8 Nov 2026, P-03 rev20.5 item 29): the keep-outs and the polyline test, without numpy, so the
router (harness.py) and the unit tests use the same code. The slot is the gap between the lower edge of the top cover and the upper
edges of the side, front and rear panels; no cable, busbar or tie lies in it or on a panel upper edge (the side-panel top flanges
included), all around the robot, with no inward band."""
import math


def cover_slot_keepouts(F):
    """The four cover-slot keep-outs (left, right, front, rear) from facts.yaml cover_slot."""
    cs = F["cover_slot"]
    z0_, z1_ = cs["panel_top"] - cs["margin"], cs["cover_edge"] + cs["margin"]
    yi = 0.193 - cs["depth"]   # side panels: their top flange reaches in to y 0.193 (CAD v0.2); nothing lies on it in the band
    xf_ = 0.370 - cs["depth"]
    xr_ = F["rear_section"]["rear_panel_inner_x"] + cs["depth"]
    out = []
    for k_, lo_, hi_ in (("left", [-0.395, yi, z0_], [0.395, 0.295, z1_]), ("right", [-0.395, -0.295, z0_], [0.395, -yi, z1_]),
                         ("front", [xf_, -0.295, z0_], [0.395, 0.295, z1_]), ("rear", [-0.395, -0.295, z0_], [xr_, 0.295, z1_])):
        out.append({"id": "cover_slot_" + k_, "lo": lo_, "hi": hi_, "members": ["lidar"] if k_ == "front" else [],
                    "why": "%s slot between the panel upper edge (side panels: the whole top flange) and the cover, plus 5 mm (owner rule 8 Nov 2026, P-03 rev20.5 item 29)" % k_})
    return out


def _samples(pts, step):
    pts = [[float(v) for v in p] for p in pts]
    for a, b in zip(pts, pts[1:]):
        n = max(1, int(math.dist(a, b) / step))
        for i in range(n):
            t = i / n
            yield [a[k] + t * (b[k] - a[k]) for k in range(3)]
    if pts:
        yield pts[-1]


TIE_RADIUS = 0.004   # envelope of a cable tie or tie base around its point (head about 8 mm across)


def envelope_radius(cable):
    """Outer radius of a cable or busbar in m: half its envelope diameter od_mm (a busbar's od_mm is the envelope the model
    routes it with). Review of #83, 8 Nov 2026: the slot rule applies to the outer surface, not the centre line."""
    return float(cable.get("od_mm") or 0.0) / 2000.0


def _segment_hits_box(a, b, lo, hi):
    """Exact test: does the closed segment a-b meet the closed box [lo, hi]? Slab method, no sampling, so a segment whose
    endpoints lie outside the box but whose middle crosses it is caught. Touching the box counts as a hit (conservative)."""
    t0, t1 = 0.0, 1.0
    for i in range(3):
        d = b[i] - a[i]
        if abs(d) < 1e-12:
            if a[i] < lo[i] or a[i] > hi[i]:
                return False
            continue
        ta, tb = (lo[i] - a[i]) / d, (hi[i] - a[i]) / d
        if ta > tb:
            ta, tb = tb, ta
        t0, t1 = max(t0, ta), min(t1, tb)
        if t0 > t1:
            return False
    return True


def slot_violations(pts, keep, step=None, radius=0.0):
    """Ids of the cover-slot keep-outs (cover_slot_*) that a cable of the given outer radius meets. Clearance model: each
    keep-out box is grown by the cable's outer radius on every side (a conservative envelope: it also counts the box corners,
    where the true rounded envelope would be slightly smaller), and every route segment is tested exactly against the grown
    box, so continuous clearance is proven, not sampled. Touching counts as a violation. A single point (a cable tie) is
    tested as a point inside the box grown by its envelope radius. Checked on every route, searched, fixed (declared) and
    cached, so no route bypasses the slot rule. `step` is accepted for compatibility and ignored."""
    pts = [[float(v) for v in p] for p in pts]
    zones = [k for k in keep if str(k["id"]).startswith("cover_slot_")]
    hits = []
    for k in zones:
        lo = [k["lo"][i] - radius for i in range(3)]
        hi = [k["hi"][i] + radius for i in range(3)]
        if len(pts) == 1:
            hit = all(lo[i] <= pts[0][i] <= hi[i] for i in range(3))
        else:
            hit = any(_segment_hits_box(a, b, lo, hi) for a, b in zip(pts, pts[1:]))
        if hit:
            hits.append(k["id"])
    return hits
