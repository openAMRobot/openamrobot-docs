#!/usr/bin/env python3
"""Write the generated sections of docs/assets/roadmap/hardware.html from the model outputs:
3D model coverage (bom_coverage.csv, analysis_summary.json, build_summary.json, cable_list.csv), the mechanical
parts table (design_intent/index.json), the geometry and hardware issues (geometry_issues.csv, sorted by severity)
and the conflicts list (conflicts.yaml). The sections sit between <!--GEN:name--> and <!--/GEN:name--> markers,
after the "Hardware values with known drift" section. Rerun after build.py and analyse.py.
"""
import collections
import csv
import html
import json
import os
import re

from frames import HERE, MODEL, REPO, load_yaml

PAGE = os.path.join(REPO, "docs", "assets", "roadmap", "hardware.html")
E = html.escape
SNAP = "2 Nov 2026"
A = lambda href, text: '<a href="%s" target="_blank" rel="noopener">%s</a>' % (E(href), E(text))
OWNER = '<a class="who" href="https://github.com/fridayali" target="_blank" rel="noopener">@fridayali</a> <span class="role">(mechanical CAD)</span>'


def section(sid, title, body, src):
    return ('<!--GEN:%s--><section class="card" id="%s"><h2>%s</h2>%s<p class="src small mute">Source: %s · %s</p></section><!--/GEN:%s-->'
            % (sid, sid, E(title), body, src, SNAP, sid))


def table(head, rows, cls="tbl"):
    h = "".join("<th>%s</th>" % E(x) for x in head)
    b = "".join("<tr>%s</tr>" % "".join("<td%s>%s</td>" % (' class="small"' if i else "", c) for i, c in enumerate(r)) for r in rows)
    return '<div class="%s"><table><thead><tr>%s</tr></thead><tbody>%s</tbody></table></div>' % (cls, h, b)


def model_section():
    cov = list(csv.DictReader(open(os.path.join(MODEL, "bom_coverage.csv"))))
    an = json.load(open(os.path.join(HERE, "analysis_summary.json")))
    bs = json.load(open(os.path.join(HERE, "build_summary.json")))
    cab = list(csv.DictReader(open(os.path.join(MODEL, "cable_list.csv"))))
    fas = list(csv.DictReader(open(os.path.join(MODEL, "fastener_schedule.csv"))))
    on = [r for r in cov if r["onboard"] == "y"]
    cnt = collections.Counter(r["class"] for r in on)
    drawn = sum(1 for r in on if r["drawn"] == "y")
    qmis = [r["id"] for r in on if r["drawn"] == "y" and r["model_qty"] not in ("", r["qty"])]
    rows = [[E(k), str(v)] for k, v in sorted(cnt.items(), key=lambda kv: -kv[1])]
    m = an["mass"]
    st = an["stability"]
    ld = an["loads"]
    routed = [c for c in cab if c["route_length_m"]]
    total_len = sum(float(c["length_with_margin_m"]) for c in routed)
    nofit = bs["nofit"]
    k = bs["k1k2_options"]
    body = (
        '<p>The shared model now draws every onboard BOM Issue 7.14 line it has a geometry or position source for. '
        'Positions come from datums.yaml (%s), sensor_frames.yaml and the section B facts through '
        '<code>scripts/roadmap_model/build.py</code>; nothing is placed by hand. A part without a position source is drawn '
        'provisional with a label; parts the model proposes (front bay, rear zone, harness, fasteners) are marked proposed.</p>'
        % E(an.get("datums_revision", "2026-11-01.c")) +
        "<p><b>Coverage:</b> %d BOM records, %d onboard by the model rule (offboard, qty 0 and the fallback lift excluded; "
        "the BOM states 115 onboard, see the conflicts list); %d onboard lines drawn, %d not drawn. Model quantity differs from the BOM "
        "quantity on: %s.</p>" % (len(cov), len(on), drawn, len(on) - drawn, E(", ".join(qmis)) or "none") +
        table(["Class (onboard lines)", "Lines"], rows) +
        "<p><b>Mass and centre of mass</b> (coverage roll-up, MEC-001 from the CAD volume as steel, %.1f kg): %.1f kg against the 120 kg cap. "
        "COM at L1000 x %.0f, y %.0f, z %.0f mm; at L1350 z %.0f mm. Static tip-over margins to the castor polygon: fore %.0f, aft %.0f, lateral %.0f mm; "
        "maximum deceleration before tip-over %.1f m/s² at L1000 and %.1f m/s² at L1350 (fore), %.1f m/s² lateral at L1350. "
        "Drive pair load by the lever rule %.0f kg (rating 120 kg per pair).</p>" % (
            an["steel_chassis_kg"], m["L1000"]["mass"], m["L1000"]["com"][0] * 1000, m["L1000"]["com"][1] * 1000, m["L1000"]["com"][2] * 1000,
            m["L1350"]["com"][2] * 1000, st["L1000"]["margin_fore_m"] * 1000, st["L1000"]["margin_aft_m"] * 1000, st["L1000"]["margin_lat_m"] * 1000,
            st["L1000"]["a_max_fore"], st["L1350"]["a_max_fore"], st["L1350"]["a_max_lat"], ld["L1350"]["drive_pair_kg"]) +
        "<p><b>Front electronics bay</b> (between the front panel and the centre bracket, removable plate MEC-005): parts packed with 3 mm gaps and "
        "10 mm around converters, clear of the LiDAR support, the sensor bodies, the E-stop and RESET contact blocks, the cover and a 20 mm keep-out "
        "around each lift-plate bolt (bp000 and bp050). The ZLAC8015D and the IMU board stay at their CAD positions. "
        "Not placed anywhere: %s. Moved to the rear side pockets (28 Oct alternative, not decided): %s.</p>" % (
            E(", ".join(nofit)) or "none", E(", ".join(x for x, v in bs["packed"].items() if x.startswith("bay_") and v[0][0] < 0)) or "none") +
        "<p><b>Rear power zone</b> (B5 accepted layout: distribution behind the cells, BMS and fuse panel in the side pockets): "
        "K1/K2 option A GX11CAC fits: %s. Option B TeSys D LC1D80BD fits: %s (drawn as a labelled ghost where the packer puts it). "
        "Siemens 3RT2 S3 fits: %s.</p>" % ("yes" if k["A"]["fits"] else "no", "yes" if k["B_tesys"]["fits"] else "no", "yes" if k["B_siemens"]["fits"] else "no") +
        "<p><b>Harness:</b> %d cables (%d routed, %.1f m with the 10 %% service margin), coloured by domain (BAT red, SAFE orange, regulated 24 V yellow, "
        "5 V / 3.3 V green, signal blue), with P-clips, grommets at the centre-bracket walls and the deck crossing, CAN terminations and one "
        "service loop for all upper-body cables sized for the 350 mm stroke. <b>Fasteners:</b> %d schedule rows (named and proposed), the start of MEC-014; "
        "small parts load with High quality only.</p>" % (len(cab), len(routed), total_len, len(fas)) +
        "<p>Files: %s, %s, %s, %s, %s; layout STEP for SolidWorks: %s.</p>" % (
            A("model/bom_coverage.csv", "bom_coverage.csv"), A("model/fastener_schedule.csv", "fastener_schedule.csv"),
            A("model/cable_list.csv", "cable_list.csv"), A("model/assembly_sequence.csv", "assembly_sequence.csv"),
            A("model/geometry_issues.csv", "geometry_issues.csv"), A("model/export/openamrobot2_layout.step", "openamrobot2_layout.step")))
    return section("model3d", "3D model: BOM coverage, front bay, rear zone and harness", body,
                   "roadmap model build of %s (scripts/roadmap_model), BOM Issue 7.14, datums.yaml 2026-11-01.c, sensor_frames.yaml at platform-sw 4926f40" % SNAP)


def mech_section():
    di = json.load(open(os.path.join(MODEL, "design_intent", "index.json")))
    di = di if isinstance(di, list) else di["items"]
    names = {"tof_mount": "a. TF-Luna mounts, front and rear", "ultrasonic_mount": "b. MB7060 mounts (4)", "gemini_mount": "c. Gemini 336L mount",
             "zed_bracket": "d. ZED Mini bracket on the post top", "getac_pocket": "e. Getac ZX80 pocket and light-bar plate",
             "lift_base_plate": "f. Lift-to-base interface plate", "adapter_post": "g. Adapter plate, HFS6-60120 post, upright, stiffener, rod mount",
             "rear_estop_housing": "h. Rear E-stop housing", "motor_bracket": "i. Hub motor shaft-flat brackets", "lift_sensor_set": "j. Lift stop sensor set",
             "battery_tray": "k. Battery tray"}
    rows = []
    for d in di:
        status = "design intent" + ("; CAD exists for the fixed-angle version" if d.get("existing_cad") else "")
        src = "%s, %s, %s mm; %s" % ("design_intent/%s.step" % d["files"][0]["variant"], d.get("method", ""), d.get("thickness_mm", ""), d.get("existing_cad") or "no CAD in openamr-platform-hw or openamr-upperbody-hw")
        rows.append([E(names.get(d["item"], d["item"])), E(d.get("bom", "")), E(status), E(src), E(d.get("next_step", "CAD owner to model from the design intent")), OWNER])
    rows.append([E("Layout STEP of the whole robot"), "", E("design intent"), E("export/openamrobot2_layout.step: design-intent solids plus one box per drawn part, named by BOM id, base_footprint"),
                 E("open in SolidWorks as the skeleton for M-02 to M-09"), OWNER])
    rows.append([E("M-09 positions (Getac, light, second E-stop, lift sensors)"), "UI-001, AUX-001, SAF-001, LFT-001", E("not started"),
                 E("placeholders from datums.yaml; no CAD commit since 16 Oct (6c32fba)"), E("confirm the absolute positions; CAD fixes promised 31 Oct are not pushed"), OWNER])
    body = ("<p>Parametric design-intent parts (CadQuery, one script per item in <code>scripts/roadmap_model/design_intent/</code>, change a value and "
            "rerun <code>run_all.py</code>), exported as STEP and STL. They are proposals from B7 and the datasheets, class provisional, not CAD. "
            "Work packages M-02, M-03, M-04, M-05, M-07 and M-09.</p>" + table(["Item", "BOM ID", "Status", "Source", "Next step", "Owner"], rows))
    return section("mechparts", "Mechanical parts", body, "M-01 rev19.7, P-03 rev20.2, decisions.yaml a9e229e, design_intent/index.json")


def issues_section():
    rows = list(csv.DictReader(open(os.path.join(MODEL, "geometry_issues.csv"))))
    big = [r for r in rows if r["severity"] in ("blocker", "major")]
    small = [r for r in rows if r["severity"] == "minor"]
    who = lambda h: '<a class="who" href="https://github.com/%s" target="_blank" rel="noopener">@%s</a>' % (E(h), E(h))
    mk = lambda rs: [[E(r["id"]), E(r["severity"]), E(r["parts"]), E(r["configuration"]), E(r["measured"]), E(r["limit"]), E(r["suggested_fix"]), who(r["owner"])] for r in rs]
    head = ["ID", "Severity", "Parts", "Configuration", "Measured", "Limit", "Suggested fix", "Owner"]
    c = collections.Counter(r["severity"] for r in rows)
    body = ("<p>Generated from %s by <code>scripts/roadmap_model/analyse.py</code> on the shared model: interference of all part pairs at L1000, L1175 and "
            "L1350, bp000 and bp050, hp15 to hp35 and both Getac positions; a single-joint arm sweep through the URDF limits at 10 deg steps at L1000 and "
            "L1350; the Gemini 336L and ZED Mini views and the LiDAR plane; mass, stability, the TZBOT receiver, service access and the K1/K2 fit. "
            "Box parts are tested exactly, meshes on 0.75 mm surface samples. %d blocker, %d major, %d minor.</p>" % (A("model/geometry_issues.csv", "geometry_issues.csv"), c["blocker"], c["major"], c["minor"]) +
            table(head, mk(big)) + "<details><summary>%d minor issues</summary>%s</details>" % (len(small), table(head, mk(small))))
    return section("geoissues", "Geometry and hardware issues", body, "roadmap model analysis of %s; B8 simulation findings of 29 Oct 2026" % SNAP)


def conflicts_section():
    C = load_yaml(os.path.join(HERE, "conflicts.yaml"))
    rows = [[E(c["item"]), E(c["a"]), E(c["b"]), E(c["status"])] for c in C["conflicts"]]
    body = ("<p>Where a repository disagrees with the documents in force, the document wins unless the repository change is later. "
            "Proposed register changes are in the pull request of this update.</p>" + table(["Item", "One source says", "The other says", "State"], rows))
    return section("conflicts", "Conflicts between sources", body, "P-03 rev20.2, E-01 rev1.6, M-01 rev19.7, BOM Issue 7.14, decisions.yaml a9e229e, repository main at the snapshot")


def main():
    s = open(PAGE, encoding="utf-8").read()
    secs = [model_section(), mech_section(), issues_section(), conflicts_section()]
    s = re.sub(r"<!--GEN:(\w+)-->.*?<!--/GEN:\1-->", "", s, flags=re.S)
    anchor = s.index('<section class="card" id="hwdrift">')
    end = s.index("</section>", anchor) + len("</section>")
    s = s[:end] + "".join(secs) + s[end:]
    open(PAGE, "w", encoding="utf-8").write(s)
    print("hardware.html sections written")


if __name__ == "__main__":
    main()
