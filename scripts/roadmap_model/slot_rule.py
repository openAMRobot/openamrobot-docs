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


def slot_violations(pts, keep, step=0.0025, radius=0.0):
    """Ids of the cover-slot keep-outs (cover_slot_*) that a cable of the given outer radius enters: a sample point within
    radius of a keep-out box (the box grown by radius). Checked on every route, searched, fixed (declared) and cached, so no
    route bypasses the slot rule."""
    hits = []
    zones = [k for k in keep if str(k["id"]).startswith("cover_slot_")]
    for q in _samples(pts, step):
        for k in zones:
            if k["id"] not in hits and all(k["lo"][i] - radius < q[i] < k["hi"][i] + radius for i in range(3)):
                hits.append(k["id"])
    return hits
