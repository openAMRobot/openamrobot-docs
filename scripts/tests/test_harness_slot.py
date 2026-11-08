# SPDX-License-Identifier: MIT
"""Cover-slot rule for every harness route (owner rule 8 Nov 2026, P-03 rev20.5 item 29; review of #83).

The router checks declared (fixed) and cached routes against the cover-slot keep-outs, not only the routes it searches.
The old P62 declared route, which rose at x -0.125 through the rear slot band, must be flagged; the corrected P62 route
and every route in the committed harness_routes.json must be clear. The mass ledger test checks the count-once rule.
"""
import json
import os
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "roadmap_model"))
import harness as H  # noqa: E402
import rear_power as RP  # noqa: E402

MODEL = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "assets", "roadmap", "model"))
KEEP = H.cover_slot_keepouts(H.FACTS)
OLD_P62 = [[-0.125, -0.266, 0.166], [-0.125, -0.266, 0.270]]


class CoverSlot(unittest.TestCase):
    def test_old_p62_declared_route_is_rejected(self):
        self.assertIn("cover_slot_right", H.slot_violations(OLD_P62, KEEP))

    def test_corrected_p62_route_is_clear(self):
        pts = [[v / 1000.0 for v in p] for p in RP.BUSBARS["CBL-P62"][2]]
        self.assertEqual(H.slot_violations(pts, KEEP), [])

    def test_committed_routes_are_clear(self):
        with open(os.path.join(MODEL, "harness_routes.json"), encoding="utf-8") as f:
            R = json.load(f)
        cables = R["cables"].values() if isinstance(R["cables"], dict) else R["cables"]
        bad, n = {}, 0
        for c in cables:
            for sec in c.get("sections", []):
                if sec.get("kind") == "base":
                    n += 1
                    hit = H.slot_violations(sec["pts"], KEEP)
                    if hit:
                        bad[c["id"]] = hit
        self.assertGreater(n, 50)
        self.assertEqual(bad, {})


if __name__ == "__main__":
    unittest.main()
