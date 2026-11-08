# SPDX-License-Identifier: MIT
"""Regression tests of scripts/check_roadmap.py (run: python3 -m unittest discover -s scripts/tests).

Sensor pose check (review of ef90d7f, 2 Nov 2026): the committed model passes; a drawn sensor moved by +20 mm in x,
+2 mm in y or +2 mm in z, or pitched by +1 deg about its own frame, fails. Chest retired-term check (review of
419e1c6): the labelled portrait second-position ghost passes, a portrait default fails. STATE.md figures: a stale
figure fails. Known contacts (TZBOT charging gap, 2 Nov 2026): the committed model passes; a receiver raised by 1 mm
(overlap 1 mm instead of the declared 2 mm) fails, and so does a missing issue row.
"""
import copy
import json
import math
import os
import subprocess
import shutil
import sys
import tempfile
import unittest

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(HERE))
import check_roadmap as C  # noqa: E402

ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "assets", "roadmap"))
MODEL = os.path.join(ROOT, "model")


def load():
    snap = json.load(open(os.path.join(MODEL, "source_snapshot.json"), encoding="utf-8"))
    payload = open(os.path.join(MODEL, "base_glb.js"), encoding="utf-8").read()
    js = open(os.path.join(MODEL, "model.js"), encoding="utf-8").read()
    verts = C.glb_vertices(payload, snap["base_link_z"])
    upper = C.upper_body_sensor_poses(js, os.path.join(MODEL, "combined_robot.urdf"))
    return snap, verts, upper


def rotate_about_frame_y(pts, origin, rpy, deg):
    """Pitch a drawn body by deg about the y axis of its own frame (origin, rpy)."""
    Rf = C._rpy(*rpy)
    a = math.radians(deg)
    Ry = [[math.cos(a), 0, math.sin(a)], [0, 1, 0], [-math.sin(a), 0, math.cos(a)]]
    M = C._mul(C._mul(Rf, Ry), C._tr(Rf))
    return [[o + d for o, d in zip(origin, C._mv(M, [p[i] - origin[i] for i in range(3)]))] for p in pts]


class SensorPose(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.snap, cls.verts, cls.upper = load()

    def errors(self, verts=None, upper=None):
        return C.sensor_pose_errors(self.snap, verts or self.verts, self.upper if upper is None else upper)

    def moved(self, node, d):
        v = copy.deepcopy(self.verts)
        v[node] = [[p[0] + d[0], p[1] + d[1], p[2] + d[2]] for p in v[node]]
        return v

    def test_committed_model_passes(self):
        self.assertEqual(self.errors(), [])

    def test_every_sensor_is_checked(self):
        self.assertEqual(len(self.snap["frame_nodes"]), 9)
        self.assertEqual(sorted(k for k in self.upper if not k.startswith("_")),
                         ["head_camera_link", "lift_stop_sensor_l1000_link", "lift_stop_sensor_l1175_link", "lift_stop_sensor_l1350_link"])

    def test_x_plus_20mm_fails(self):
        # the reviewer's case: ultrasonic body 20 mm forward, inside its old bounding box plus 1 mm on y and z
        e = self.errors(self.moved("ultrasonic_front_left", (0.020, 0, 0)))
        self.assertTrue(any("us_front_left" in x and " x " in x for x in e), e)

    def test_y_plus_2mm_fails(self):
        e = self.errors(self.moved("imu", (0, 0.002, 0)))
        self.assertTrue(any("imu_link" in x and " y " in x for x in e), e)

    def test_z_plus_2mm_fails(self):
        e = self.errors(self.moved("lidar", (0, 0, 0.002)))
        self.assertTrue(any("lidar_link" in x and " z " in x for x in e), e)

    def test_pitch_plus_1deg_fails(self):
        v = copy.deepcopy(self.verts)
        f = "tof_front"
        v["tof_front"] = rotate_about_frame_y(v["tof_front"], self.snap["sensor_frames"][f], self.snap["sensor_frames_rpy"][f], 1.0)
        e = self.errors(v)
        self.assertTrue(any("tof_front" in x and "orientation" in x for x in e), e)

    def test_each_case_fails_for_one_sensor_only(self):
        e = self.errors(self.moved("base_camera", (0, 0, 0.002)))
        self.assertTrue(e and all("base_camera_link" in x for x in e), e)

    def test_below_tolerance_passes(self):
        self.assertEqual(self.errors(self.moved("ultrasonic_rear_right", (0.0005, -0.0005, 0.0005))), [])

    def test_upper_body_sensor_moved_fails(self):
        up = copy.deepcopy(self.upper)
        b = up["lift_stop_sensor_l1175_link"]["drawn_body"]
        up["lift_stop_sensor_l1175_link"]["drawn_body"] = [b[0] + 0.020, b[1], b[2]]
        e = self.errors(upper=up)
        self.assertTrue(any("lift_stop_sensor_l1175_link" in x and " x " in x for x in e), e)

    def test_head_camera_pitch_fails(self):
        up = copy.deepcopy(self.upper)
        up["head_camera_link"]["drawn_R"] = C._rpy(0, math.radians(C.HEAD_PITCH_BASELINE + 1), 0)
        e = self.errors(upper=up)
        self.assertTrue(any("head_camera_link" in x and "orientation" in x for x in e), e)

    def test_no_ultrasonic_special_case(self):
        src = open(C.__file__, encoding="utf-8").read()
        self.assertNotIn('for frame in ("us_front_left", "us_front_right", "us_rear_left", "us_rear_right")', src)

    def test_rigid_fit_recovers_known_pose(self):
        local = [[0, 0, 0], [0.03, 0, 0], [0, 0.02, 0], [0, 0, 0.01], [0.01, 0.01, 0.01]]
        Rk = C._rpy(0.1, -0.2, 0.3)
        world = [[a + b for a, b in zip(C._mv(Rk, p), (0.4, -0.1, 0.2))] for p in local]
        R, t, rms = C.rigid_fit(local, world)
        self.assertLess(C._angle_deg(R, Rk), 1e-4)
        self.assertLess(max(abs(a - b) for a, b in zip(t, (0.4, -0.1, 0.2))), 1e-9)
        self.assertLess(rms, 1e-9)


class ChestRetired(unittest.TestCase):
    """A3 (2 Nov 2026): portrait only on a fixed mount; a landscape default, a rotatable mount, the portrait ghost and the E-stop ghosts fail."""
    def test_portrait_default_allowed(self):
        for text in ("Getac ZX80 in portrait, the decided default", "Getac drawn portrait by default", "149.8 wide x 234 tall"):
            self.assertEqual(C.retired_chest_hits(text), [], text)
        self.assertEqual(C.getac_default_errors([0.0176, 0.1498, 0.234]), [])

    def test_landscape_default_rejected(self):
        for text in ("mounted on a rotatable mount, landscape default", "landscape position (default)", "getac_second_position_ghost",
                     "Getac ZX80 pocket, portrait second position (ghost)", "estop_p1_ghost", "Getac ZX80 on a rotatable 2-position mount"):
            self.assertTrue(C.retired_chest_hits(text), text)
        self.assertTrue(C.getac_default_errors([0.0176, 0.234, 0.1498]))

    def test_zx10_rejected(self):
        self.assertTrue(C.retired_chest_hits("Getac ZX10 275 x 192"))


class StateFigures(unittest.TestCase):
    def test_committed_state_is_current(self):
        text = open(os.path.join(ROOT, "..", "..", "..", "STATE.md"), encoding="utf-8").read()
        self.assertEqual(C.state_errors(text, C.state_figures(ROOT), "2 Nov 2026"), [])

    def test_stale_figure_fails(self):
        figs = C.state_figures(ROOT)
        text = open(os.path.join(ROOT, "..", "..", "..", "STATE.md"), encoding="utf-8").read()
        n = figs["sync_audit"][0]
        stale = text.replace("Playwright visual audit: %s parts" % n, "Playwright visual audit: 63 parts")
        self.assertNotEqual(stale, text)
        self.assertTrue(C.state_errors(stale, figs, "2 Nov 2026"))

    def test_missing_figure_fails(self):
        self.assertTrue(C.state_errors("# State\n", C.state_figures(ROOT), "2 Nov 2026"))


class WholeCheck(unittest.TestCase):
    def test_committed_pages_pass(self):
        r = subprocess.run([sys.executable, os.path.join(HERE, "..", "check_roadmap.py")], capture_output=True, text=True)
        self.assertEqual(r.returncode, 0, r.stdout + r.stderr)


class ReferencePagesCurrent(unittest.TestCase):
    """Reference pages follow the 2 Nov 2026 register: E-stop on the adapter plate, 10 mm gap, ZED 57 mm, 4 + 4 cells proposed."""
    def test_committed_reference_pages_pass(self):
        errs = []
        C.check_reference_pages(os.path.join(ROOT, "docs", "assets", "roadmap"), lambda p, m: errs.append(p + ": " + m))
        self.assertEqual(errs, [])

    def test_superseded_values_fail(self):
        for text in ("second E-stop on the rear face of the static lift column", "head light, a 30 mm gap, Getac",
                     "lens 42 mm ahead of and 223 mm above", "eight upright cells in one row across the robot",
                     "wired outside the lift cable chain", "light flat on a cooling plate, 30 mm below the Getac",
                     "second E-stop on the rear face of the arm post", "Jetson Orin NX 16 GB on J401",
                     "no metal within 15 mm from any side of the receiver", "no cable in the slot or within 50 mm inside it"):
            self.assertTrue(C.superseded_reference_hits(text), text)

    def test_current_values_pass(self):
        for text in ("second E-stop on top of the moving adapter plate", "a 10 mm gap", "lens 57 mm ahead of",
                     "supersedes the static-column position of the E-stop", "lift stop sensors on the rear face of the static DOLD column",
                     "Battery (25 to 29 Oct): cells in one row; superseded 2 Nov 2026 by two trays",
                     "Jetson Orin NX 8 GB on the reComputer Robotics 104", "no metal within 20 mm of the receiver sides"):
            self.assertEqual(C.superseded_reference_hits(text), [], text)


class SelfCheck(unittest.TestCase):
    """The Python analysis scene must equal the page scene (owner review of #70: lift chain 263 mm)."""
    def test_small_deviation_passes(self):
        self.assertEqual(C.self_check_errors({"self_check": {"compared": 141, "max_dev_mm": 3.0, "worst": [["rod_corner_bracket", .003]]}}), [])

    def test_large_deviation_fails(self):
        self.assertTrue(C.self_check_errors({"self_check": {"compared": 141, "max_dev_mm": 263.058, "worst": [["lift_energy_chain", .263]]}}))

    def test_missing_self_check_fails(self):
        self.assertTrue(C.self_check_errors({"self_check": {}}))


if __name__ == "__main__":
    unittest.main()


class KnownContacts(unittest.TestCase):
    def run_check(self, edit_place=None, edit_rows=None):
        d = tempfile.mkdtemp()
        try:
            os.makedirs(os.path.join(d, "model"))
            P = json.load(open(os.path.join(MODEL, "placement.json"), encoding="utf-8"))
            rows = open(os.path.join(MODEL, "geometry_issues.csv"), encoding="utf-8").read()
            if edit_place:
                edit_place(P)
            if edit_rows:
                rows = edit_rows(rows)
            json.dump(P, open(os.path.join(d, "model", "placement.json"), "w", encoding="utf-8"))
            open(os.path.join(d, "model", "geometry_issues.csv"), "w", encoding="utf-8").write(rows)
            out = []
            C.check_known_contacts(d, lambda page, msg: out.append(msg))
            return out
        finally:
            shutil.rmtree(d)

    def test_committed_model_passes(self):
        self.assertEqual(self.run_check(), [])

    def test_changed_overlap_fails(self):
        def raise_rx(P):
            P["geometry"]["tz_receiver"]["prims"][0]["p"][2] += 0.001
        self.assertTrue(any("overlap 1.0 mm" in e for e in self.run_check(raise_rx)))

    def test_missing_issue_row_fails(self):
        drop = lambda rows = "": "\n".join(l for l in rows.splitlines() if "TZBOT receiver / floor transmitter WCM-500-24" not in l) + "\n"
        self.assertTrue(any("row missing" in e for e in self.run_check(edit_rows=drop)))

# ---------------------------------------------------------------- harness rules (harness_routes.json)
def _h(**kw):
    """Minimal harness data: one base cable along the floor between two connectors, tie points every 100 mm."""
    pts = [[0.0, 0.2, 0.065], [0.4, 0.2, 0.065]]
    H = {"rules": {"max_span_m": 0.150, "tie_near_m": 0.050, "tie_tol_m": 0.030, "over_band_m": 0.040, "entry_m": 0.025},
         "harnesses": [{"id": "W03"}],
         "obstacles": [{"id": "box_a", "lo": [0.10, -0.05, 0.054], "hi": [0.20, 0.05, 0.120], "top_access": False}],
         "withdrawal": [{"id": "tray", "lo": [-0.30, 0.10, 0.054], "hi": [-0.15, 0.26, 0.30], "members": ["tray_part"]}],
         "ties": [{"id": "T%d" % i, "p": [x, 0.2, 0.065]} for i, x in enumerate([0.04, 0.14, 0.24, 0.36])],
         "branches": [], "chain": None,
         "cables": [{"id": "CBL-X1", "harness": "W03", "gauge": "0.5 mm²", "od_mm": 3.0, "min_bend_mm": 18, "flex_min_mm": 30, "own": [],
                     "lift": False, "sections": [{"kind": "base", "group": "base", "pts": pts}]}]}
    H.update(kw)
    return H


def _chain(**kw):
    ch = {"R": 0.075, "stroke": 0.35, "min_bottom_z": 0.311, "slack_req_m": 0.02,
          "stops": [{"T": round(i * 0.025, 3), "fixed_run_m": 0.2 - i * 0.0125, "moving_run_m": 0.3 + i * 0.0125, "loop_bottom_z": 0.32 + i * 0.0125, "clash": []} for i in range(15)]}
    ch.update(kw)
    return ch


def _lift_cable(**kw):
    c = {"id": "CBL-L1", "harness": "W09", "gauge": "ZED", "od_mm": 5.0, "min_bend_mm": 30, "flex_min_mm": 50, "own": [], "lift": True, "slack_min_m": 0.03,
         "sections": [{"kind": "base", "group": "base", "pts": [[0.0, 0.0, 0.1], [0.03, 0.0, 0.1]]},
                      {"kind": "chain", "group": "col", "pts": [[0, 0, 0.6], [0, 0, 0.4]]},
                      {"kind": "moving", "group": "mov", "pts": [[0, 0.1, 0.80], [0.03, 0.1, 0.80]]}]}
    c.update(kw)
    return c


class HarnessSpan(unittest.TestCase):
    def test_supported_route_passes(self):
        self.assertEqual(C.harness_span_errors(_h()), [])

    def test_unsupported_span_fails(self):
        H = _h(ties=[{"id": "T0", "p": [0.04, 0.2, 0.065]}, {"id": "T1", "p": [0.36, 0.2, 0.065]}])
        self.assertTrue(any("unsupported span 320 mm" in e for e in C.harness_span_errors(H)))

    def test_no_tie_near_connector_fails(self):
        H = _h(ties=[{"id": "T%d" % i, "p": [x, 0.2, 0.065]} for i, x in enumerate([0.08, 0.18, 0.28, 0.36])])
        self.assertTrue(any("within 50 mm of the connector at its start" in e for e in C.harness_span_errors(H)))

    def test_branch_without_tie_fails(self):
        H = _h(branches=[{"cable": "CBL-X1", "p": [0.30, 0.2, 0.065]}])
        self.assertEqual(C.harness_span_errors(_h(branches=[{"cable": "CBL-X1", "p": [0.26, 0.2, 0.065]}])), [])
        H["ties"] = [t for t in H["ties"] if t["id"] != "T2" and t["id"] != "T3"] + [{"id": "T9", "p": [0.39, 0.2, 0.065]}]
        self.assertTrue(any("of the branch" in e for e in C.harness_span_errors(H)))


class HarnessSlotKeepOut(unittest.TestCase):
    """D-06 (P-03 rev20.5 item 29): no cable, busbar or tie in the cover slot band, all around; rear components allowed."""
    SLOT = {"id": "cover_slot_left", "lo": [-0.395, 0.188, 0.2112], "hi": [0.395, 0.295, 0.2351], "members": []}

    def test_route_below_the_slot_passes(self):
        self.assertEqual(C.harness_slot_errors(_h(keep_out=[self.SLOT])), [])

    def test_cable_crossing_the_slot_fails(self):
        H = _h(keep_out=[self.SLOT])
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.2, 0.065], [0.0, 0.2, 0.220], [0.4, 0.2, 0.220]]
        self.assertTrue(any("crosses cover_slot_left" in e for e in C.harness_slot_errors(H)))

    def test_busbar_touching_the_slot_fails(self):
        H = _h(keep_out=[self.SLOT])
        H["cables"][0].update(kind="busbar", sections=[{"kind": "base", "group": "base", "pts": [[0.0, 0.25, 0.200], [0.0, 0.25, 0.212]]}])
        self.assertTrue(any("(busbar)" in e for e in C.harness_slot_errors(H)))

    def test_tie_in_the_slot_fails(self):
        H = _h(keep_out=[self.SLOT])
        H["ties"].append({"id": "T9", "p": [0.1, 0.25, 0.225]})
        self.assertTrue(any("tie T9" in e for e in C.harness_slot_errors(H)))

    def test_inward_route_at_slot_height_passes(self):
        H = _h(keep_out=[self.SLOT])
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.10, 0.220], [0.4, 0.10, 0.220]]
        self.assertEqual(C.harness_slot_errors(H), [])

    def test_member_cable_is_exempt(self):
        H = _h(keep_out=[dict(self.SLOT, members=["lidar"])])
        H["cables"][0].update(own=["lidar"], sections=[{"kind": "base", "group": "base", "pts": [[0.0, 0.2, 0.220], [0.4, 0.2, 0.220]]}])
        self.assertEqual(C.harness_slot_errors(H), [])


class HarnessOverComponent(unittest.TestCase):
    def test_route_beside_component_passes(self):
        self.assertEqual(C.harness_over_errors(_h()), [])

    def test_route_over_component_fails(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.0, 0.140], [0.4, 0.0, 0.140]]
        self.assertTrue(any("passes over box_a" in e for e in C.harness_over_errors(H)))

    def test_route_through_component_fails(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.0, 0.080], [0.4, 0.0, 0.080]]
        self.assertTrue(any("passes through box_a" in e for e in C.harness_over_errors(H)))

    def test_own_end_part_is_exempt(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.0, 0.140], [0.4, 0.0, 0.140]]
        H["cables"][0]["own"] = ["box_a"]
        self.assertEqual(C.harness_over_errors(H), [])

    def test_top_access_part_has_no_height_limit(self):
        H = _h()
        H["obstacles"][0]["top_access"] = True
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.0, 0.250], [0.4, 0.0, 0.250]]
        self.assertTrue(any("passes over box_a" in e for e in C.harness_over_errors(H)))


class HarnessWithdrawal(unittest.TestCase):
    def test_route_outside_withdrawal_path_passes(self):
        self.assertEqual(C.harness_withdrawal_errors(_h()), [])

    def test_route_across_tray_path_fails(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[-0.20, 0.0, 0.27], [-0.20, 0.30, 0.27]]
        self.assertTrue(any("withdrawal path of tray" in e for e in C.harness_withdrawal_errors(H)))

    def test_own_assembly_cable_passes(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[-0.20, 0.0, 0.27], [-0.20, 0.30, 0.27]]
        H["cables"][0]["own"] = ["tray_part"]
        self.assertEqual(C.harness_withdrawal_errors(H), [])


class HarnessBend(unittest.TestCase):
    def test_gentle_route_passes(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[0, 0.2, 0.065], [0.2, 0.2, 0.065], [0.2, 0.4, 0.065]]
        self.assertEqual(C.harness_bend_errors(H), [])

    def test_tight_corner_fails(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[0, 0.2, 0.065], [0.2, 0.2, 0.065], [0.2, 0.21, 0.065], [0.3, 0.21, 0.065]]
        self.assertTrue(any("bend radius" in e for e in C.harness_bend_errors(H)))

    def test_25mm2_below_class_minimum_fails(self):
        H = _h()
        H["cables"][0].update(gauge="25 mm²", min_bend_mm=40)
        self.assertTrue(any("class minimum 60 mm" in e for e in C.harness_bend_errors(H)))

    def test_chain_radius_below_flex_minimum_fails(self):
        H = _h(cables=[_lift_cable(flex_min_mm=80)], chain=_chain())
        self.assertTrue(any("continuous-flex minimum" in e for e in C.harness_bend_errors(H)))
        self.assertEqual(C.harness_bend_errors(_h(cables=[_lift_cable()], chain=_chain())), [])


class HarnessLift(unittest.TestCase):
    def test_cable_in_chain_passes(self):
        self.assertEqual(C.harness_lift_errors(_h(cables=[_lift_cable()], chain=_chain())), [])

    def test_lift_cable_outside_chain_fails(self):
        c = _lift_cable()
        c["sections"] = [c["sections"][0], {"kind": "moving", "group": "mov", "pts": [[0, 0, 0.3], [0, 0, 0.8]]}]
        self.assertTrue(any("outside the energy chain" in e for e in C.harness_lift_errors(_h(cables=[c], chain=_chain()))))

    def test_chain_too_short_fails(self):
        ch = _chain()
        ch["stops"][-1]["fixed_run_m"] = -0.01
        self.assertTrue(any("shorter than zero" in e for e in C.harness_lift_errors(_h(cables=[_lift_cable()], chain=ch))))

    def test_chain_contact_fails(self):
        ch = _chain()
        ch["stops"][3]["clash"] = ["loop / flag rod"]
        self.assertTrue(any("touches loop / flag rod" in e for e in C.harness_lift_errors(_h(cables=[_lift_cable()], chain=ch))))

    def test_taut_cable_fails(self):
        self.assertTrue(any("slack" in e for e in C.harness_lift_errors(_h(cables=[_lift_cable(slack_min_m=0.0)], chain=_chain()))))


class HarnessLabels(unittest.TestCase):
    ROW = {"id": "CBL-X1", "harness": "W03", "label_a": "W03-X1-A", "label_b": "W03-X1-B"}

    def test_labelled_cable_passes(self):
        self.assertEqual(C.harness_label_errors(_h(), [dict(self.ROW)]), [])

    def test_cable_without_harness_fails(self):
        self.assertTrue(any("has no harness" in e for e in C.harness_label_errors(_h(), [dict(self.ROW, harness="")])))

    def test_cable_without_label_fails(self):
        self.assertTrue(any("has no label_b" in e for e in C.harness_label_errors(_h(), [dict(self.ROW, label_b="")])))

    def test_unknown_harness_fails(self):
        self.assertTrue(any("is not defined" in e for e in C.harness_label_errors(_h(), [dict(self.ROW, harness="W99")])))


class HarnessAxis(unittest.TestCase):
    """Route segments along the structure axes; 45 degree transitions only when declared and short."""
    def test_axis_route_passes(self):
        self.assertEqual(C.harness_axis_errors(_h()), [])

    def test_diagonal_span_fails(self):
        H = _h()
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.2, 0.065], [0.3, 0.0, 0.065]]
        self.assertTrue(any("off the structure axes" in e for e in C.harness_axis_errors(H)))

    def test_declared_45_transition_passes(self):
        H = _h(rules=dict(_h()["rules"], t45_max_m=0.12))
        H["cables"][0]["sections"][0].update(pts=[[0.0, 0.2, 0.065], [0.2, 0.2, 0.065], [0.25, 0.25, 0.065], [0.4, 0.25, 0.065]], t45=[1])
        self.assertEqual(C.harness_axis_errors(H), [])

    def test_long_45_transition_fails(self):
        H = _h(rules=dict(_h()["rules"], t45_max_m=0.12))
        H["cables"][0]["sections"][0].update(pts=[[0.0, 0.2, 0.065], [0.15, 0.35, 0.065]], t45=[0])
        self.assertTrue(any("off the structure axes" in e for e in C.harness_axis_errors(H)))


class HarnessSupport(unittest.TestCase):
    """Every base route point within 30 mm of a supporting surface, except near its connectors and in declared passages."""
    def _sup(self, d_mid):
        H = _h(rules=dict(_h()["rules"], support_max_m=0.030, end_free_m=0.060))
        H["cables"][0]["sections"][0]["support"] = [[round(s / 100, 2), d_mid if 0.1 < s / 100 < 0.3 else 5.0] for s in range(0, 41)]
        return H

    def test_supported_route_passes(self):
        self.assertEqual(C.harness_support_errors(self._sup(12.0)), [])

    def test_unsupported_route_fails(self):
        self.assertTrue(any("from the nearest supporting surface" in e for e in C.harness_support_errors(self._sup(80.0))))

    def test_declared_passage_passes(self):
        H = self._sup(80.0)
        H["passages"] = [{"id": "channel", "lo": [0.05, 0.15, 0.0], "hi": [0.35, 0.25, 0.2]}]
        self.assertEqual(C.harness_support_errors(H), [])


class HarnessAbove(unittest.TestCase):
    """No base route above a component top up to the next structure (shelf, deck, cover) outside the exception zone."""
    def _ab(self, z):
        H = _h(rules=dict(_h()["rules"], over_to_structure=True))
        H["over_to"] = {"box_a": {"x0": 0.10, "y0": -0.05, "res": 0.01, "z": [[0.30] * 10 for _ in range(10)]}}
        H["cables"][0]["sections"][0]["pts"] = [[0.0, 0.0, z], [0.4, 0.0, z]]
        return H

    def test_beside_component_passes(self):
        self.assertEqual(C.harness_above_errors(_h(rules=dict(_h()["rules"], over_to_structure=True), over_to={})), [])

    def test_route_above_component_fails(self):
        self.assertTrue(any("runs above the top of box_a" in e for e in C.harness_above_errors(self._ab(0.200))))

    def test_exception_zone_passes_for_its_harness(self):
        H = self._ab(0.200)
        H["cables"][0]["harness"] = "W01"
        H["exception_zones"] = [{"id": "EZ-W01", "harness": "W01", "lo": [-0.1, -0.1, 0.0], "hi": [0.5, 0.1, 0.3]}]
        self.assertEqual(C.harness_above_errors(H), [])

    def test_module_cable_of_other_harness_is_not_exempt_in_the_zone(self):
        # owner review of #71: module=True must not exempt a W02 or W03 cable inside EZ-W01 (above-component case)
        H = self._ab(0.200)
        H["cables"][0].update({"harness": "W03", "module": True})
        H["exception_zones"] = [{"id": "EZ-W01", "harness": "W01", "lo": [-0.1, -0.1, 0.0], "hi": [0.5, 0.1, 0.3]}]
        self.assertTrue(any("runs above the top of box_a" in e for e in C.harness_above_errors(H)))

    def test_module_cable_of_other_harness_through_obstacle_fails(self):
        # the reviewer's reproduction: CBL-P07 (W02, module) through a foreign obstacle inside EZ-W01
        H = _h()
        H["obstacles"] = [{"id": "foreign", "lo": [-0.25, -0.02, 0.13], "hi": [-0.20, 0.02, 0.17], "top_access": False}]
        H["exception_zones"] = [{"id": "EZ-W01", "harness": "W01", "lo": [-0.372, -0.29, 0.054], "hi": [-0.108, 0.29, 0.292]}]
        H["cables"][0].update({"id": "CBL-P07", "harness": "W02", "module": True, "own": []})
        H["cables"][0]["sections"][0]["pts"] = [[-0.30, 0.0, 0.15], [-0.15, 0.0, 0.15]]
        self.assertTrue(any("foreign" in e for e in C.harness_over_errors(H)))

    def test_module_cable_exempt_only_at_its_local_exit(self):
        z = {"id": "EZ-W01", "harness": "W01", "lo": [-0.372, -0.29, 0.054], "hi": [-0.108, 0.29, 0.292]}
        c = {"id": "CBL-P07", "harness": "W02", "module": True,
             "sections": [{"kind": "base", "pts": [[-0.30, 0.0, 0.15], [-0.15, 0.0, 0.15]]}]}
        H = {"exception_zones": [z], "passages": []}
        self.assertTrue(C._exempt(c, [-0.28, 0.0, 0.15], H))     # 20 mm from its end in the zone
        self.assertFalse(C._exempt(c, [-0.22, 0.0, 0.15], H))    # 80 mm from both ends

    def test_listed_passage_covers_only_its_cables(self):
        q = {"id": "C-RM", "lo": [-0.195, -0.09, 0.19], "hi": [-0.135, 0.09, 0.27], "cables": ["CBL-P07"]}
        H = {"exception_zones": [], "passages": [q]}
        p = [-0.17, 0.0, 0.24]
        self.assertTrue(C._exempt({"id": "CBL-P07", "harness": "W02", "sections": []}, p, H))
        self.assertFalse(C._exempt({"id": "CBL-P99", "harness": "W02", "sections": []}, p, H))

    def test_exception_zone_does_not_cover_other_harnesses(self):
        H = self._ab(0.200)
        H["exception_zones"] = [{"id": "EZ-W01", "harness": "W01", "lo": [-0.1, -0.1, 0.0], "hi": [0.5, 0.1, 0.3]}]
        self.assertTrue(any("runs above the top of box_a" in e for e in C.harness_above_errors(H)))


class HarnessSeparation(unittest.TestCase):
    """Separation of each sensitive cable from the power routes is reported and matches the routes."""
    def _sep(self, reported):
        sig = {"id": "CBL-S1", "harness": "W03", "gauge": "STP", "od_mm": 6.0, "min_bend_mm": 36, "flex_min_mm": 60, "own": [], "lift": False, "sensitive": True,
               "sections": [{"kind": "base", "group": "base", "pts": [[0.0, 0.0, 0.065], [0.4, 0.0, 0.065]]}]}
        pw = {"id": "CBL-W1", "harness": "W03", "gauge": "10 mm²", "od_mm": 7.5, "min_bend_mm": 45, "flex_min_mm": 75, "own": [], "lift": False, "power": True,
              "sections": [{"kind": "base", "group": "base", "pts": [[0.0, 0.1, 0.065], [0.4, 0.1, 0.065]]}]}
        H = _h(rules=dict(_h()["rules"], sep_work_m=0.030), cables=[sig, pw])
        H["separation"] = [] if reported is None else [{"id": "CBL-S1", "pct_separated": reported}]
        return H

    def test_matching_report_passes(self):
        self.assertEqual(C.harness_separation_errors(self._sep(100.0)), [])

    def test_missing_report_fails(self):
        self.assertTrue(any("without a separation figure" in e for e in C.harness_separation_errors(self._sep(None))))

    def test_wrong_report_fails(self):
        self.assertTrue(any("reported" in e for e in C.harness_separation_errors(self._sep(40.0))))


class HarnessCommitted(unittest.TestCase):
    def test_committed_harness_passes(self):
        H = json.load(open(os.path.join(MODEL, "harness_routes.json"), encoding="utf-8"))
        import csv
        rows = list(csv.DictReader(open(os.path.join(MODEL, "cable_list.csv"), encoding="utf-8")))
        self.assertEqual(C.harness_errors(H, rows), [])
