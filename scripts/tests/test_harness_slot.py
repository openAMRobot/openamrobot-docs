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
