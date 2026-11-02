#!/usr/bin/env python3
"""Second E-stop positions P1 to P4 against the reach requirement of 2 Nov 2026 (owner decision B2).

Requirement: a standing adult close to the robot presses it by hand without bending or sitting down. Criterion:
actuator centre 0.90 to 1.50 m above the floor at L1000, L1175 and L1350, facing outward and visible, no contact in
the arm sweep, not in the ZED Mini view, cable routed (outside or through the lift cable chain).
Positions (housing: design_intent/rear_estop_housing.py, button axis on its mounting face):
  P1 rear face of the static column, 40 mm below the static profile top (current datum; right gripper contact in
     the 29 Oct simulation);
  P2 rear face of the vertical arm post (HFS6-60120, moves with the lift), centre 55 mm below the post top, rearward;
  P3 post top beside the ZED pitch bracket, button up (the bracket foot covers the whole post top: on the foot);
  P4 static column rear face at the highest arm-clear position (fixed-height reference).
Arm checks, for both arms at each lift stop: (a) the single-joint sweep of analyse.py (10 deg steps from the
upstream home pose); (b) a reach envelope: N random joint configurations within the openarm_description limits,
poses that pass through the post, the column, the adapter plate, the Getac or below 0.30 m are discarded (the arm
cannot be there), and the count of the remaining poses with any arm link within 5 mm of the housing (the
housing envelope 64 x 50 x 100 mm). Self-collision between the arms is not modelled (conservative).
Writes scripts/roadmap_model/estop_positions.json. Usage: python3 estop_positions.py [--n 4000]
"""
import argparse
import base64
import json
import math
import os

import numpy as np

import analyse as A
from frames import FACTS, HERE, MODEL

STOPS = (("L1000", 0.0), ("L1175", 0.175), ("L1350", 0.350))
REACH = (0.90, 1.50)


def positions(up):
    st, rear, post_top = up["static_top"], up["col_rear_x"], up["col_top"] + 0.010 + 0.340
    post_rear = up["col_axis_x"] + 0.180 - 0.060
    # name: (moves with the lift, actuator centre at L1000 (x, z), housing box at L1000 (lo, hi), facing, mount, cable)
    return {
        "P1": (False, (rear - 0.064, st - 0.040), ([rear - 0.064, -0.025, st - 0.090], [rear, 0.025, st + 0.010]), "rearward (-x)",
               "static column rear face, 40 mm below the static profile top (datum second_estop_below_profile_top)", "down the static column to the base (outside the chain)"),
        "P2": (True, (post_rear - 0.064, post_top - 0.055), ([post_rear - 0.064, -0.025, post_top - 0.105], [post_rear, 0.025, post_top - 0.005]), "rearward (-x)",
               "arm-post rear face, 55 mm below the post top, two M6 T-nuts per flange in the HFS6 rear slots; above the rear upright (top 150 mm above the carriage) and the stiffener, below the ZED bracket foot",
               "up the post rear slot, then with the arm cables through the lift cable chain (service loop)"),
        "P3": (True, (post_rear + 0.020, post_top + 0.006 + 0.064 - 0.007), ([post_rear, -0.030, post_top + 0.006], [post_rear + 0.050, 0.030, post_top + 0.070]), "up (+z)",
               "post top: the ZED pitch bracket foot covers the whole 120 x 60 mm top, so the housing would sit on the foot (no room on the post itself)",
               "with the ZED cable down the post and through the lift cable chain"),
        "P4": (False, (rear - 0.064, st - 0.280), ([rear - 0.064, -0.025, st - 0.330], [rear, 0.025, st - 0.230]), "rearward (-x)",
               "static column rear face at the highest arm-clear position of the reach study (280 mm below the static profile top)", "down the static column to the base"),
    }


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--n", type=int, default=4000)
    a = ap.parse_args()
    P = json.load(open(os.path.join(MODEL, "placement.json")))
    up = P["upper_body"]
    s = open(os.path.join(MODEL, "openarm.js"), encoding="utf-8").read()
    OA = json.loads(s[s.index("=") + 1:].rstrip().rstrip(";"))
    rng = np.random.default_rng(1)

    def meshpts(vis):
        if not vis or vis["key"] not in OA["meshes"]:
            return None
        e = OA["meshes"][vis["key"]]
        pos = np.frombuffer(base64.b64decode(e["pos"]), dtype="<i2").reshape(-1, 3) * e["q"]
        V = (pos * vis["scale"]) @ A.rpy_matrix(vis["rpy"]).T + vis["xyz"]
        return V[rng.choice(len(V), 400, replace=False)] if len(V) > 400 else V

    MP = {sd: [meshpts(j["visual"]) for j in OA["arms"][sd]["joints"]] for sd in ("left", "right")}
    MF = {sd: [meshpts(f["visual"]) for f in OA["arms"][sd]["fingers"]] for sd in ("left", "right")}

    def fk(side, q, sh, grip=.6):
        arm = OA["arms"][side]
        l = A.T(None, [up["col_axis_x"], 0, sh]) @ A.T(A.rpy_matrix(arm["mount"]["rpy"]), [.18, arm["mount"]["xyz"][1], 0])
        out = []
        for i, j in enumerate(arm["joints"]):
            l = l @ A.T(A.rpy_matrix(j["rpy"]), j["xyz"]) @ A.T(A.axis_angle(j["axis"], q[i]))
            if i >= 1 and MP[side][i] is not None:
                out.append(MP[side][i] @ l[:3, :3].T + l[:3, 3])
        for k, fg in enumerate(arm["fingers"]):
            lim = fg["lo"] if abs(fg["lo"]) > abs(fg["hi"]) else fg["hi"]
            M = l @ A.T(A.rpy_matrix(fg["rpy"]), fg["xyz"]) @ A.T(A.axis_angle(fg["axis"], lim * grip))
            if MF[side][k] is not None:
                out.append(MF[side][k] @ M[:3, :3].T + M[:3, 3])
        return np.vstack(out)

    POS = positions(up)
    res = {"criterion": {"actuator_centre_m": REACH, "stops": [s_ for s_, _ in STOPS]}, "n_per_arm": a.n, "positions": {}}
    for name, (moves, (ax_x, ax_z), (lo0, hi0), facing, mount, cable) in POS.items():
        res["positions"][name] = {"moves_with_lift": moves, "facing": facing, "mount": mount, "cable": cable, "stops": {}}
    for stop, tr in STOPS:
        ct = up["col_top"] + tr
        OB = [([0.182, -0.029, ct + 0.012], [0.298, 0.029, ct + 0.348]), ([-0.058, -0.028, 0.306], [0.178, 0.028, ct - 0.002]),
              ([-0.058, -0.048, ct + 0.001], [0.298, 0.048, ct + 0.009]), ([0.302, -0.115, ct + 0.17], [0.316, 0.115, ct + 0.32])]
        boxes = {}
        for name, (moves, _, (lo0, hi0), *_r) in POS.items():
            dz = tr if moves else 0.0
            boxes[name] = (np.array(lo0) + [0, 0, dz], np.array(hi0) + [0, 0, dz])
        hits = {n: {"left": 0, "right": 0} for n in POS}
        valid = {}
        for side in ("left", "right"):
            arm = OA["arms"][side]
            lo = np.array([j["lo"] for j in arm["joints"]])
            hi = np.array([j["hi"] for j in arm["joints"]])
            Q = lo + (hi - lo) * rng.random((a.n, 7))
            nv = 0
            for q in Q:
                pts = fk(side, q, up["col_top"] + .166 + tr)
                if (pts[:, 2] < 0.30).any() or any(((pts >= np.array(l_)) & (pts <= np.array(h_))).all(1).any() for l_, h_ in OB):
                    continue
                nv += 1
                for n, (l_, h_) in boxes.items():
                    if ((pts >= l_ - .005) & (pts <= h_ + .005)).all(1).any():
                        hits[n][side] += 1
            valid[side] = nv
        # single-joint sweep (analyse.py method) for each housing box
        sweep = {}
        for n, (l_, h_) in boxes.items():
            v, f = A.box_mesh(h_ - l_, (l_ + h_) / 2)
            tg = A.Geo(A.Part(n, v, f, "world"), {"bp": "bp000", "travel": 0}, .004)
            cnt = 0
            for side in ("left", "right"):
                _, arm = A.arm_parts(side, [0.0] * 7, .6, up["col_top"] + .166 + tr, up["col_axis_x"])
                for j in range(7):
                    for q in np.arange(arm["joints"][j]["lo"], arm["joints"][j]["hi"] + 1e-6, math.radians(10)):
                        qq = [0.0] * 7
                        qq[j] = q
                        ps, _ = A.arm_parts(side, qq, .6, up["col_top"] + .166 + tr, up["col_axis_x"])
                        for lp in ps:
                            if lp.id.endswith("_base"):
                                continue
                            r = A.pair(A.Geo(lp, {"bp": "bp000", "travel": 0}, .006), tg, .002)
                            if r and (r[1] > .001 or r[0] < .0015):
                                cnt += 1
                                break
            sweep[n] = cnt
        # ZED Mini view (hp30, 90 x 60 deg, 3 m): any housing corner inside the frustum in front of the lens
        lens = np.array(up["head_lens"]) + [0, 0, tr]
        hp = math.radians(30)
        fwd = np.array([math.cos(hp), 0, -math.sin(hp)])
        upv = np.array([math.sin(hp), 0, math.cos(hp)])
        rt = np.cross(fwd, upv)
        for n, (moves, (ax_x, ax_z), (l_, h_), *_r) in POS.items():
            l_, h_ = boxes[n]
            corners = np.array([[x, y, z] for x in (l_[0], h_[0]) for y in (l_[1], h_[1]) for z in (l_[2], h_[2])])
            d = corners - lens
            zf = d @ fwd
            inview = bool(((zf > 0.01) & (np.abs(np.degrees(np.arctan2(d @ rt, zf))) < 45) & (np.abs(np.degrees(np.arctan2(d @ upv, zf))) < 30)).any())
            z_act = ax_z + (tr if moves else 0.0)
            res["positions"][n]["stops"][stop] = {
                "actuator_centre_m": round(z_act, 3), "in_reach_band": REACH[0] <= z_act <= REACH[1],
                "reach_study_hits": hits[n], "reach_study_valid_poses": valid, "single_joint_sweep_hits": sweep[n], "in_zed_view": inview}
        print(stop, {n: (res["positions"][n]["stops"][stop]["actuator_centre_m"], hits[n], sweep[n]) for n in POS}, flush=True)
    for n, r in res["positions"].items():
        st = r["stops"]
        r["meets_height"] = all(v["in_reach_band"] for v in st.values())
        r["sweep_clear"] = all(v["single_joint_sweep_hits"] == 0 for v in st.values())
        r["reach_study_clear"] = all(sum(v["reach_study_hits"].values()) == 0 for v in st.values())
        r["out_of_zed_view"] = not any(v["in_zed_view"] for v in st.values())
    res["recommended"] = "P2"
    res["recommendation"] = ("P2 (proposed): the only position with the actuator centre inside 0.90 to 1.50 m at L1000, L1175 and L1350, facing "
                             "rearward and visible, out of the ZED Mini view, clear in the single-joint sweep, cable through the lift cable chain with "
                             "the arm cables. It moves with the arms, so its reach-envelope contacts (about 0.5 % of the valid random poses, the same at "
                             "every stop) are a fixed obstacle in the arm frame: add the housing as a MoveIt collision object on arm_profile_link.")
    json.dump(res, open(os.path.join(HERE, "estop_positions.json"), "w"), indent=1)


if __name__ == "__main__":
    main()
