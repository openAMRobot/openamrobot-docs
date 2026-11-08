#!/usr/bin/env python3
"""Mass export of the roadmap model for the combined model (convergence phase 1, input for the later platform-sw mass PR).

Writes docs/assets/roadmap/model/mass_export.yaml in the structure of openamr-upperbody-sw config/mass_provenance.yaml
(schema_version, groups with state / source / owner / note), plus, per group, the URDF links the masses attach to:
for each link the mass, the centre of mass in the link frame and a box inertia about it, and the components behind it,
each with mass, centre of mass (base_footprint), box size and its source (bom_coverage.csv, placement.json, the analysis
roll-up of analyse.py). Base components attach to base_link. Totals and the centre of mass at L1000 and L1350 (bp000),
and a comparison with the masses of the expanded combined model (combined_robot.urdf).
Usage: python3 mass_export.py (after build.py and analyse.py)
"""
import csv
import json
import os
import xml.etree.ElementTree as ET

import numpy as np
import yaml

from frames import FACTS, HERE, MODEL, glb_nodes

UPPER_LINK = {"col": "lift_column_base_link", "mov": "lift_carriage_link"}
GROUP_OF_LINK = {"base_link": "base", "lift_column_base_link": "lift", "lift_carriage_link": "lift_carriage", "getac_tablet_link": "equipment",
                 "head_light_link": "equipment", "head_camera_link": "sensors", "openarm": "openarm"}


def urdf_masses(path):
    root = ET.parse(path).getroot()
    out = {}
    for l in root.findall("link"):
        m = l.find("inertial/mass")
        if m is not None:
            out[l.get("name")] = float(m.get("value"))
    return out


def group_of_urdf_link(n):
    if n.startswith("openarm_"):
        return "openarm"
    if n in ("lift_column_base_link",):
        return "lift"
    if n in ("getac_tablet_link", "head_light_link"):
        return "equipment"
    if n in ("head_camera_link",) or n.endswith("wrist_camera_link"):
        return "sensors"
    if n.startswith(("lift_carriage", "adapter_plate", "arm_profile", "second_estop", "lift_stop", "lift_flag", "head_camera_bracket")):
        return "equipment_no_mass"
    return "base"


def main():
    an = json.load(open(os.path.join(HERE, "analysis_summary.json")))
    P = json.load(open(os.path.join(MODEL, "placement.json")))
    cov = {r["id"]: r for r in csv.DictReader(open(os.path.join(MODEL, "bom_coverage.csv")))}
    G = glb_nodes()
    size = {k: (v["v"].max(0) - v["v"].min(0)).tolist() for k, v in G.items()}
    group = {}
    for k, e in P["geometry"].items():
        pts = []
        for q in e["prims"]:
            if q["t"] == "box":
                c, s = np.array(q["p"]), np.array(q["s"])
                pts += [c - s / 2, c + s / 2]
            elif q["t"] == "mesh":
                v = np.array(q["v"]).reshape(-1, 3)
                pts += [v.min(0), v.max(0)]
        if pts:
            size[k] = (np.max(pts, 0) - np.min(pts, 0)).tolist()
        group[k] = e["group"]
    comp_parts = {c["id"]: c["parts"] for c in P["components"]}
    for c in P["components"]:
        for p in c["parts"]:
            group.setdefault(p, P["geometry"].get(p, {}).get("group", "base"))
    up = P["upper_body"]
    ax = FACTS["lift_plate"]["col_axis_x"]["bp000"]

    # owner decision 8 Nov 2026: the roadmap model is the reference for the URDF masses. Parts that ride the lift carriage belong to
    # lift_carriage_link, the static column parts to lift_column_base_link, each BOM line to exactly one link (no double count)
    LINK_OF_BOM = {"ARM-004": "openarm", "ARM-003": "head_camera_link", "MEC-003": "lift_carriage_link", "MEC-004": "lift_carriage_link",
                   "LFT-004": "lift_carriage_link", "LFT-005": "lift_carriage_link", "LFT-006": "lift_carriage_link",
                   "LFT-001": "lift_column_base_link", "LFT-003": "lift_column_base_link"}
    LINK_OF_PART = {"second_estop": "lift_carriage_link", "estop": "base_link"}

    def link_of(bid, comp):
        if bid in LINK_OF_BOM:
            return LINK_OF_BOM[bid]
        if bid == "ARM-001":
            return "openarm"
        if bid in ("MEC-018",):
            return "lift_column_base_link"
        if bid in ("UI-001",):
            return "getac_tablet_link"
        if bid in ("AUX-001",):
            return "head_light_link"
        if bid in ("ARM-011",):
            return "head_camera_link"
        ids = [x.strip() for x in str(comp).replace("inside:", "").split(",")]
        for pid in ids:
            parts = comp_parts.get(pid, [pid])
            g = group.get(parts[0] if parts else pid) or group.get(pid)
            if g in UPPER_LINK:
                return UPPER_LINK[g]
        return "base_link"

    from parity import Urdf
    U = Urdf(os.path.join(MODEL, "combined_robot.urdf"))

    def link_origin(link, tr):
        """World origin of the URDF link (bp000, lift joint tr); the OpenArm group uses the left J1_A mount frame."""
        name = "openarm_left_base_link" if link == "openarm" else link
        return U.world(name, {"lift_joint": tr})[:3, 3]

    centre = {k: ((v["v"].max(0) + v["v"].min(0)) / 2).tolist() for k, v in G.items()}
    for k, e in P["geometry"].items():
        if e.get("group", "base") != "base":
            continue
        pts = []
        for q in e["prims"]:
            if q["t"] == "box":
                c_, s_ = np.array(q["p"]), np.array(q["s"])
                pts += [c_ - s_ / 2, c_ + s_ / 2]
            elif q["t"] == "mesh":
                v_ = np.array(q["v"]).reshape(-1, 3)
                pts += [v_.min(0), v_.max(0)]
        if pts:
            centre[k] = ((np.max(pts, 0) + np.min(pts, 0)) / 2).tolist()
    dump = "/tmp/oamr_scene_dump.json"   # page dump of run_all.sh (every drawn part, bp000, L1000): boxes of the parts model.js draws
    if os.path.exists(dump):
        for k, (lo_, hi_) in json.load(open(dump))["parts"].items():
            size.setdefault(k, (np.subtract(hi_, lo_)).tolist())
            centre.setdefault(k, ((np.add(hi_, lo_)) / 2).tolist())
    col = FACTS["column"]
    env = [k for k in ("base_plate", "side_panel_left", "side_panel_right", "front_panel", "rear_panel") if k in G]
    env_lo = np.min([G[k]["v"].min(0) for k in env], 0)
    env_hi = np.max([G[k]["v"].max(0) for k in env], 0)
    # real boxes where the part has no single drawn box (8 Nov 2026): DOLD column from the supplier STEP, chassis envelope (solid box,
    # a lower bound for the sheet-metal shell), hub motors as their two GLB wheels
    SIZE_OF_PART = {"lift_column": [col["section"][0], col["section"][1], col["static_top"]], "chassis": (env_hi - env_lo).tolist()}
    PARTS_OF = {"DRV-001": ["hub_motor_wheel_left", "hub_motor_wheel_right"]}

    def parts_of(bid, comp):
        if bid in PARTS_OF:
            return PARTS_OF[bid]
        ids = [x.strip() for x in str(comp).replace("inside:", "").split(",")]
        return [p for pid in ids for p in comp_parts.get(pid, [pid])]

    def box_size(bid, comp):
        for p in parts_of(bid, comp):
            if p in SIZE_OF_PART:
                return SIZE_OF_PART[p]
            if p in size:
                return size[p]
        return None

    def split(bid, m, c, comp):
        """One mass item as sub-items (part, mass, com, size, link): split over its drawn base parts by box volume (the two battery
        groups, trays, wheels, brackets) and by part link (SAF-001: base front button and the second E-stop on the carriage)."""
        ps = parts_of(bid, comp)
        if bid == "SAF-001":
            return [(p, m / len(ps), c, box_size(bid, p) or [0.05, 0.05, 0.064], LINK_OF_PART.get(p, "base_link")) for p in ps]
        link = link_of(bid, comp)
        if link == "base_link" and len(ps) > 1 and all(p in size and p in centre for p in ps):
            vol = np.array([max(np.prod(size[p]), 1e-9) for p in ps])
            w = vol / vol.sum()
            return [(p, m * wi, centre[p], size[p], link) for p, wi in zip(ps, w)]
        return [(comp, m, c, box_size(bid, comp) or [0, 0, 0], link)]

    out = {"schema_version": 1, "about": "Roadmap model masses per URDF link, generated by scripts/roadmap_model/mass_export.py from bom_coverage.csv (BOM Issue 7.14 masses), placement.json and the analysis roll-up. Input for the platform-sw mass PR (base) and for mass_provenance.yaml (upper body). Frame of com_m in links: the link frame (identity rotations); components: base_footprint at bp000.",
           "snapshot": FACTS["snapshot"],
           "status": "estimate, under ledger review (D-26): design values from BOM Issue 7.14, nothing weighed. Held until the unique physical-instance mass ledger (mechanical owner): the battery pack definition (whether the 20 to 23 kg includes tray, BMS, F0 and disconnect), the hub motors and castors against the URDF wheel and castor links, and the static and moving split of the 11.7 kg DOLD lift are open. Do not use as inertial evidence.",
           "groups": {}, "totals": {}, "comparison": {}}
    links = {}
    for stop, tr in (("L1000", 0.0), ("L1350", 0.35)):
        for bid, m, c, comp in an["mass_items"][stop]:
            for part, mp, cp, sz, link in split(bid, m, c, comp):
                if link != "base_link" and bid != "SAF-001" and len(parts_of(bid, comp)) == 1:
                    cp = c   # moving and column parts: the analysis centre of mass at this stop
                elif bid == "SAF-001":   # two equal buttons: the base one at its drawn centre, the moving one so that their mean is the analysis centre
                    cf = np.array(centre.get("estop", c))
                    cp = cf.tolist() if part == "estop" else (2 * np.array(c) - cf).tolist()
                e = links.setdefault(stop, {}).setdefault(link, {"items": []})
                e["items"].append({"bom": bid, "component": part, "mass_kg": round(float(mp), 3), "com_m": [round(float(v), 4) for v in cp], "size_m": [round(float(x), 3) for x in sz],
                                   "source": (cov.get(bid) or {}).get("mass_source", "") or "chassis volume x 7850 (CAD)" if bid == "MEC-001" else (cov.get(bid) or {}).get("mass_source", "")})
    # link aggregates at L1000 (link frames move with the lift; COM in the link frame is the same at both stops)
    for link, e in links["L1000"].items():
        ms = np.array([i["mass_kg"] for i in e["items"]])
        cs = np.array([i["com_m"] for i in e["items"]])
        M = float(ms.sum())
        com = (ms[:, None] * cs).sum(0) / M
        I = np.zeros(3)
        for i, mi, ci in zip(e["items"], ms, cs):
            s = np.array(i["size_m"])
            I += mi / 12 * np.array([s[1] ** 2 + s[2] ** 2, s[0] ** 2 + s[2] ** 2, s[0] ** 2 + s[1] ** 2])
            d = ci - com
            I += mi * np.array([d[1] ** 2 + d[2] ** 2, d[0] ** 2 + d[2] ** 2, d[0] ** 2 + d[1] ** 2])
        e.update({"mass_kg": round(M, 3), "com_m": [round(float(x), 4) for x in (com - link_origin(link, 0.0))],
                  "inertia_kgm2": {"ixx": round(float(I[0]), 5), "iyy": round(float(I[1]), 5), "izz": round(float(I[2]), 5)},
                  "inertia_note": "sum of the component boxes (uniform density) about the link centre of mass, by the parallel-axis theorem; products of inertia not given",
                  "link_origin_m": [round(float(x), 4) for x in link_origin(link, 0.0)]})
    grp_meta = {
        "base": ("roadmap_estimate", "BOM Issue 7.14 masses (bom_coverage.csv; estimates and catalogue figures) and MEC-001 from the CAD volume as steel, placed at the roadmap model positions", "platform-sw (base); hardware owner for the BOM masses"),
        "lift": ("external_nominal", "DOLD Hexalift V4 350 catalogue 11.7 kg (MEC-018) plus the lift base plate MEC-019 and the parts on the static column", "upper body (A6) with the hardware owner"),
        "lift_carriage": ("roadmap_estimate", "adapter plate, arm post, Getac pocket, E-stop P2, harness and fasteners on the carriage (design intent and estimates)", "upper body (A6)"),
        "equipment": ("external_nominal", "Getac ZX80 and head light supplier figures (BOM)", "upper body (A6)"),
        "sensors": ("external_nominal", "ZED Mini and its bracket (BOM)", "upper body (A6)"),
        "openarm": ("external_nominal", "OpenArm 2.0 arms (ARM-001 BOM mass); the combined model keeps the upstream link masses", "upstream openarm_description"),
    }
    for link, e in links["L1000"].items():
        gname = GROUP_OF_LINK.get(link, "base")
        st, src, own = grp_meta[gname]
        g = out["groups"].setdefault(gname, {"state": st, "source": src, "owner": own, "links": {}})
        g["links"][link] = e
    for stop in ("L1000", "L1350"):
        ms = np.array([i["mass_kg"] for e in links[stop].values() for i in e["items"]])
        cs = np.array([i["com_m"] for e in links[stop].values() for i in e["items"]])
        com = (ms[:, None] * cs).sum(0) / ms.sum()
        out["totals"][stop] = {"mass_kg": round(float(ms.sum()), 2), "com_m": [round(float(x), 4) for x in com], "frame": "base_footprint, bp000"}
    um = urdf_masses(os.path.join(MODEL, "combined_robot.urdf"))
    ug = {}
    for n, m in um.items():
        ug[group_of_urdf_link(n)] = ug.get(group_of_urdf_link(n), 0.0) + m
    rg = {}
    for gname, g in out["groups"].items():
        rg[gname] = round(sum(e["mass_kg"] for e in g["links"].values()), 2)
    out["comparison"] = {"combined_model_urdf_kg": {k: round(v, 3) for k, v in sorted(ug.items())}, "combined_model_total_kg": round(sum(um.values()), 2),
                         "roadmap_kg": rg, "roadmap_total_kg": out["totals"]["L1000"]["mass_kg"],
                         "base_urdf_kg": round(ug.get("base", 0.0), 2),
                         "note": "The base URDF at the PLATFORM-PIN carries %.1f kg in total; the roadmap base group from BOM Issue 7.14 is %.1f kg. Upper-body groups: see mass_provenance.yaml (lift 11.7 kg, equipment 0.70 kg, sensors 0.063 kg, OpenArm upstream nominals)." % (ug.get("base", 0.0), rg.get("base", 0.0))}
    yaml.safe_dump(out, open(os.path.join(MODEL, "mass_export.yaml"), "w"), sort_keys=False, width=160)
    json.dump({"status": out["status"], "totals": out["totals"], "comparison": out["comparison"]}, open(os.path.join(HERE, "mass_summary.json"), "w"), indent=1)
    print(json.dumps({"totals": out["totals"], "comparison": out["comparison"]}, indent=1))


if __name__ == "__main__":
    main()
