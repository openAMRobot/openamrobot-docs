# SPDX-License-Identifier: MIT
"""Cover-slot rule for every harness route (owner rule 8 Nov 2026, P-03 rev20.5 item 29; review of #83).

The router (harness.py) checks declared (fixed) and cached routes against the cover-slot keep-outs, not only the routes it
searches, with the shared slot_rule module. The old P62 declared route, which rose at x -0.125 through the right slot band, must
be flagged; the corrected P62 route and every base section in the committed harness_routes.json must be clear.
"""
import json
import os
import sys
import unittest

import yaml

HERE = os.path.dirname(os.path.abspath(__file__))
SRC = os.path.join(os.path.dirname(HERE), "roadmap_model")
sys.path.insert(0, SRC)
import slot_rule as S  # noqa: E402

MODEL = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "assets", "roadmap", "model"))
with open(os.path.join(SRC, "facts.yaml"), encoding="utf-8") as f_:
    KEEP = S.cover_slot_keepouts(yaml.safe_load(f_))
with open(os.path.join(MODEL, "harness_routes.json"), encoding="utf-8") as f_:
    ROUTES = json.load(f_)
CABLES = ROUTES["cables"].values() if isinstance(ROUTES["cables"], dict) else ROUTES["cables"]
OLD_P62 = [[-0.125, -0.266, 0.166], [-0.125, -0.266, 0.270]]


def base_sections(cid=None):
    for c in CABLES:
        if cid is None or c["id"] == cid:
            for sec in c.get("sections", []):
                if sec.get("kind") == "base":
                    yield c["id"], sec["pts"]


class CoverSlot(unittest.TestCase):
    def test_old_p62_declared_route_is_rejected(self):
        self.assertIn("cover_slot_right", S.slot_violations(OLD_P62, KEEP))

    def test_cable_envelope_near_the_boundary_is_rejected(self):
        """Review of #83 (8 Nov 2026): a 6 mm cable whose centre line is 2 mm outside cover_slot_left (y 0.188) reaches it with
        its outer surface; the centre-line test alone called this clear."""
        seg = [[0.0, 0.186, 0.220], [0.1, 0.186, 0.220]]
        r = S.envelope_radius({"od_mm": 6.0})
        self.assertAlmostEqual(r, 0.003)
        self.assertIn("cover_slot_left", S.slot_violations(seg, KEEP, radius=r))
        self.assertEqual(S.slot_violations([[0.0, 0.184, 0.220], [0.1, 0.184, 0.220]], KEEP, radius=r), [])   # 1 mm clear

    def test_committed_routes_keep_their_envelope_out(self):
        bad = {}
        for c in CABLES:
            for sec in c.get("sections", []):
                if sec.get("kind") == "base":
                    hit = S.slot_violations(sec["pts"], KEEP, radius=S.envelope_radius(c))
                    if hit:
                        bad[c["id"]] = hit
        self.assertEqual(bad, {})

    def test_corrected_p62_route_is_clear(self):
        secs = list(base_sections("CBL-P62"))
        self.assertTrue(secs, "CBL-P62 has no base section")
        for _, pts in secs:
            self.assertEqual(S.slot_violations(pts, KEEP), [])

    def test_committed_routes_are_clear(self):
        secs = list(base_sections())
        self.assertGreater(len(secs), 50)
        bad = {cid: S.slot_violations(pts, KEEP) for cid, pts in secs if S.slot_violations(pts, KEEP)}
        self.assertEqual(bad, {})


if __name__ == "__main__":
    unittest.main()


class ExactSegmentTest(unittest.TestCase):
    """Review of #83 (10 Nov 2026): a sampled scan can miss a segment whose endpoints are outside a keep-out but whose middle
    crosses it (a corner cut). The slot rule now tests every segment exactly against the radius-grown box."""
    BOX = [{"id": "cover_slot_test", "lo": [0.0, 0.0, 0.0], "hi": [0.010, 0.010, 0.010]}]

    def test_crossing_between_samples_is_caught(self):
        # a 0.8 mm thin keep-out; the old 2.5 mm scan sampled this 5 mm segment at x -1.5, 1.0 and 3.5 mm, all outside it
        thin = [{"id": "cover_slot_thin", "lo": [0.0, 0.0, 0.0], "hi": [0.0008, 0.010, 0.010]}]
        seg = [[-0.0015, 0.005, 0.005], [0.0035, 0.005, 0.005]]
        self.assertEqual(S.slot_violations(seg, thin), ["cover_slot_thin"])

    def test_corner_cut_is_caught(self):
        seg = [[-0.0012, 0.0050, 0.005], [0.0050, -0.0012, 0.005]]
        self.assertEqual(S.slot_violations(seg, self.BOX), ["cover_slot_test"])

    def test_long_segment_through_the_box_is_caught_with_any_step(self):
        seg = [[-1.0, 0.005, 0.005], [1.0, 0.005, 0.005]]
        self.assertEqual(S.slot_violations(seg, self.BOX, step=1.0), ["cover_slot_test"])

    def test_near_clearance_passes(self):
        seg = [[-1.0, 0.0105, 0.005], [1.0, 0.0105, 0.005]]   # 0.5 mm above the box, centre line only
        self.assertEqual(S.slot_violations(seg, self.BOX), [])

    def test_radius_makes_near_clearance_a_hit(self):
        seg = [[-1.0, 0.0105, 0.005], [1.0, 0.0105, 0.005]]
        self.assertEqual(S.slot_violations(seg, self.BOX, radius=0.001), ["cover_slot_test"])

    def test_touching_counts_as_violation(self):
        seg = [[-1.0, 0.010, 0.005], [1.0, 0.010, 0.005]]
        self.assertEqual(S.slot_violations(seg, self.BOX), ["cover_slot_test"])

    def test_tie_point(self):
        self.assertEqual(S.slot_violations([[0.012, 0.005, 0.005]], self.BOX, radius=0.004), ["cover_slot_test"])
        self.assertEqual(S.slot_violations([[0.015, 0.005, 0.005]], self.BOX, radius=0.004), [])
