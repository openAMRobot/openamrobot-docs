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
                     "lens 42 mm ahead of and 223 mm above", "eight upright cells in one row across the robot"):
            self.assertTrue(C.superseded_reference_hits(text), text)

    def test_current_values_pass(self):
        for text in ("second E-stop on top of the moving adapter plate", "a 10 mm gap", "lens 57 mm ahead of",
                     "supersedes the static-column position of the E-stop", "lift stop sensors on the rear face of the static DOLD column"):
            self.assertEqual(C.superseded_reference_hits(text), [], text)


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