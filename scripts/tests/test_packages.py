# SPDX-License-Identifier: MIT
"""Package evidence record (packages.py) and its checks (check_roadmap.package_errors), audit of 10 Nov 2026.

A card link pinned to anything but the recorded head of main, an rc.1 pin that differs from the record, a "tested"
badge without a named check, run, commit and profile, a hidden duplicate provider and a firmware list that drops an
entry each fail. The committed architecture page passes against the committed record.
"""
import json
import os
import re
import sys
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "roadmap_model"))
import check_roadmap as C  # noqa: E402
import packages as P  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "assets", "roadmap"))
SHA = "a" * 40
RUN = "https://github.com/openAMRobot/openamr-platform-sw/actions/runs/1"


def record():
    rc1 = {"sha": "b" * 40, "present": True, "same_as_main": False}
    return {"heads": {"openamr-platform-sw": {"sha": SHA, "date": "2026-11-10"}},
            "packages": {"openamrobot_nav2": {"rc1": rc1, "duplicates": []}}, "other": [{"name": "fw"}]}


def card(**kw):
    c = {"repo": "openamr-platform-sw", "url": "https://github.com/openAMRobot/openamr-platform-sw/blob/%s/x/package.xml" % SHA,
         "main": {"sha": SHA}, "rc1": {"sha": "b" * 40, "present": True, "same_as_main": False}, "duplicates": [],
         "status": "MERGED AND TESTED",
         "evidence": {"check": "nav-status-tests", "run": RUN, "commit": "f71f9f1", "profile": "simulation",
                      "conclusion": "success", "applies": True}}
    c.update(kw)
    return {"openamrobot_nav2": c}


class PackageErrors(unittest.TestCase):
    def test_complete_card_passes(self):
        self.assertEqual(C.package_errors(card(), record(), 1), [])

    def test_link_not_on_recorded_head_fails(self):
        url = "https://github.com/openAMRobot/openamr-platform-sw/blob/%s/x/package.xml" % ("c" * 40)
        self.assertRegex(" ".join(C.package_errors(card(url=url), record(), 1)), "not pinned to the recorded head")

    def test_tested_without_run_fails(self):
        ev = {"check": "nav-status-tests", "commit": "f71f9f1", "profile": "simulation", "conclusion": "success", "applies": True}
        self.assertRegex(" ".join(C.package_errors(card(evidence=ev), record(), 1)), "MERGED AND TESTED without run")

    def test_tested_needs_success_and_unchanged_package(self):
        base = card()["openamrobot_nav2"]["evidence"]
        self.assertRegex(" ".join(C.package_errors(card(evidence=dict(base, conclusion="failure")), record(), 1)),
                         "run conclusion is failure")
        self.assertRegex(" ".join(C.package_errors(card(evidence=dict(base, applies=False)), record(), 1)),
                         "package changed since the tested commit")

    def test_untested_without_run_passes(self):
        self.assertEqual(C.package_errors(card(status="MERGED UNTESTED", evidence={}), record(), 1), [])

    def test_rc1_pin_and_duplicates_follow_the_record(self):
        rec = record()
        rec["packages"]["openamrobot_nav2"]["duplicates"] = ["openamrobot-ui/x/package.xml"]
        errs = " ".join(C.package_errors(card(rc1={"sha": None}), rec, 1))
        self.assertIn("rc.1 pin differs", errs)
        self.assertIn("duplicate providers not shown", errs)

    def test_firmware_list_must_carry_every_entry(self):
        self.assertRegex(" ".join(C.package_errors(card(), record(), 0)), "firmware and placeholder list has 0 rows")


class Generator(unittest.TestCase):
    def test_evidence_rule_matches_the_checker(self):
        ok = {"check": "c", "run": RUN, "commit": "x", "profile": "p", "conclusion": "success", "applies": True}
        self.assertTrue(P.evidence_ok("MERGED AND TESTED", ok))
        self.assertFalse(P.evidence_ok("MERGED AND TESTED", dict(ok, run="")))
        self.assertFalse(P.evidence_ok("MERGED AND TESTED", dict(ok, conclusion="failure")))
        self.assertFalse(P.evidence_ok("MERGED AND TESTED", dict(ok, applies=False)))
        self.assertTrue(P.evidence_ok("MERGED UNTESTED", {}))

    def test_package_xml_description_has_no_em_dash(self):
        xml = ("<package><name>n</name><description>Model — URDF, meshes</description><license>MIT</license>"
               "<depend>rclcpp</depend><test_depend>ament_lint</test_depend></package>")
        p = P.parse_package(xml)
        self.assertEqual(p["description"], "Model, URDF, meshes")
        self.assertEqual(p["deps"], ["ament_lint", "rclcpp"])


class Drift(unittest.TestCase):
    def test_new_upstream_head_and_pin_are_reported(self):
        old = {"heads": {"r": {"sha": "a" * 40}}, "rc1_pins": {"r": "b" * 40}, "packages": {"p": {}}}
        new = {"heads": {"r": {"sha": "c" * 40}}, "rc1_pins": {"r": "d" * 40}, "packages": {"p": {}, "q": {}}}
        d = P.drift(old, new)
        self.assertEqual(d, ["r main aaaaaaa -> ccccccc", "rc.1 pin r bbbbbbb -> ddddddd", "package q added"])
        self.assertEqual(P.drift(new, new), [])


class CommittedPage(unittest.TestCase):
    def test_architecture_page_matches_the_committed_record(self):
        html = open(os.path.join(ROOT, "architecture.html"), encoding="utf-8").read()
        rec = json.load(open(os.path.join(ROOT, "model", "packages.json"), encoding="utf-8"))
        block = re.search(r"<!-- packages:other -->(.*?)<!-- /packages:other -->", html, flags=re.S)
        self.assertIsNotNone(block)
        rows = len(re.findall(r"<tr><td>", block.group(1)))
        self.assertEqual(C.package_errors(C.embedded(html, "PK"), rec, rows), [])


if __name__ == "__main__":
    unittest.main()
