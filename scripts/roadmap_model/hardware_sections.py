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
        "<p><b>Front electronics bay</b>: two layouts with the TZBOT receiver in place, option A (two-tier, proposed default) and option B "
        "(28 Oct alternative), switched on the exploded view; see the front bay section below. Front bay parts placed in option A: %d; in option B: %d "
        "(not placed: %s).</p>" % (bs["front_bay"]["A"]["fit"]["placed"], bs["front_bay"]["B"]["fit"]["placed"], E(", ".join(bs["front_bay"]["B"]["fit"]["not_placed"])) or "none") +
        "<p><b>Rear power zone</b> (B5 accepted layout), packed around the design-intent battery tray MEC-007 and the real side-pocket section with 5 mm "
        "clearances (10 mm around converters); what B5 cannot hold goes under the arch top above the hub motors (overflow proposal, not B5). "
        "Not placed anywhere: %s (geometry issue %s). "
        "K1/K2 option A GX11CAC fits: %s. Option B TeSys D LC1D80BD fits: %s (drawn as a labelled ghost where the packer puts it). "
        "Siemens 3RT2 S3 fits: %s.</p>" % (E(", ".join(nofit)) or "none", gi("Rear zone layout"), "yes" if k["A"]["fits"] else "no", "yes" if k["B_tesys"]["fits"] else "no", "yes" if k["B_siemens"]["fits"] else "no") +
        "<p><b>Harness:</b> %d cables (%d routed, %.1f m with the 10 %% service margin), coloured by domain (BAT red, SAFE orange, regulated 24 V yellow, "
        "5 V / 3.3 V green, signal blue), with P-clips, grommets at the centre-bracket walls and the deck crossing, CAN terminations and one "
        "service loop for all upper-body cables sized for the 350 mm stroke; the front trunk drops below the LiDAR scan plane (222.05 mm, +/-5 mm) behind the open sector and stays 20 mm outside the receiver zone. <b>Fasteners:</b> %d schedule rows (named and proposed), the start of MEC-014; "
        "small parts load with High quality only.</p>" % (len(cab), len(routed), total_len, len(fas)) +
        "<p>Files: %s, %s, %s, %s, %s; layout STEP for SolidWorks: %s.</p>" % (
            A("model/bom_coverage.csv", "bom_coverage.csv"), A("model/fastener_schedule.csv", "fastener_schedule.csv"),
            A("model/cable_list.csv", "cable_list.csv"), A("model/assembly_sequence.csv", "assembly_sequence.csv"),
            A("model/geometry_issues.csv", "geometry_issues.csv"), A("model/export/openamrobot2_layout.step", "openamrobot2_layout.step")))
    return section("model3d", "3D model: BOM coverage, front bay, rear zone and harness", body,
                   "roadmap model build of %s (scripts/roadmap_model), BOM Issue 7.14, datums.yaml 2026-11-01.d, sensor_frames.yaml at platform-sw 4926f40" % SNAP)


def mech_section():
    di = json.load(open(os.path.join(MODEL, "design_intent", "index.json")))
    di = di if isinstance(di, list) else di["items"]
    names = {"tof_mount": "a. TF-Luna mounts, front and rear", "ultrasonic_mount": "b. MB7060 mounts (4)", "gemini_mount": "c. Gemini 336L mount",
             "zed_bracket": "d. ZED Mini bracket on the post top", "getac_pocket": "e. Getac ZX80 pocket and light-bar plate",
             "lift_base_plate": "f. Lift base plate on the centre-frame arch", "adapter_post": "g. Adapter plate, HFS6-60120 post, upright, stiffener, rod mount",
             "rear_estop_housing": "h. Second E-stop housing, post mount P2 (P1, P3, P4 ghosts)", "motor_bracket": "i. Hub motor shaft-flat brackets", "lift_sensor_set": "j. Lift stop sensor set",
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


def decisions_section():
    an = json.load(open(os.path.join(HERE, "analysis_summary.json")))
    ep = an["estop_positions"]
    pl = an["lift_base_plate"]
    tz = an["tzbot"]
    ic = an["intended_contacts"][0]
    lp = load_yaml(os.path.join(HERE, "facts.yaml"))["lift_plate"]
    # B2 table
    rows = []
    for n in ("P1", "P2", "P3", "P4"):
        p = ep["positions"][n]
        h = " / ".join("%.3f" % v["actuator_centre_m"] for v in p["stops"].values())
        hits = " / ".join(str(sum(v["reach_study_hits"].values())) for v in p["stops"].values())
        rows.append([E(n + (" (recommended, proposed)" if n == ep["recommended"] else "")), E(p["mount"]), E(h), E("yes" if p["meets_height"] else "no"),
                     E("sweep clear; reach study %s" % hits), E("no" if p["out_of_zed_view"] else "yes"), E(p["cable"])])
    t_estop = table(["Position", "Mount", "Actuator centre at L1000 / L1175 / L1350 (m)", "0.90 to 1.50 m at every stop", "Arms (single-joint sweep; reach-study poses within 5 mm, both arms)", "In the ZED Mini view", "Cable"], rows)
    # B3 load check
    rows = []
    for c in pl["cases"]:
        rows.append([E(c["case"]), E(c["bp"]), "%.1f" % max(c["bolt_tension_per_bolt_N"].values()), "%.1f" % c["bolt_shear_per_bolt_N"], "%.2f" % c["bolt_utilisation"],
                     "%.2f" % c["rivet_nut_pull_through_utilisation"], "%.0f (%.2f)" % (c["plate_stress_MPa"], c["plate_utilisation"]),
                     "%.0f (%.2f)" % (c["arch_sheet_stress_MPa"], c["arch_sheet_utilisation"]), "%.3f" % c["plate_deflection_at_column_front_mm"], "%.2f" % c["column_tilt_deg"]])
    t_plate = table(["Load case", "Plate hole set", "Bolt tension (N, worst)", "Bolt shear (N)", "Bolt (EN 1993-1-8)", "Rivet-nut pull-through", "Plate stress MPa (Rp0.2 255)", "Arch sheet stress MPa (fy 235)", "Plate deflection at the column front (mm)", "Column tilt (deg)"], rows)
    ab = pl["above_plate"]
    mu = pl["max_utilisation"]
    ok = max(mu.values()) <= 0.67
    # B4
    metal = [[E(m["part"]), "%.1f" % m["clearance_mm"], "%.1f" % m["overlap_mm"], E(m["fix"])] for m in tz["metal_within_20mm"]]
    emc = [[E(k), "-" if v is None else "%.1f" % v, "under 50 mm" if (v is not None and v < 50) else "ok"] for k, v in tz["emc_distances_mm"].items()]
    cut = tz["cutout"]
    low = tz["lowest_point"]
    body = (
        "<p>Decisions of 2 Nov 2026 by the robot owner, to be entered in P-03 and M-01. Values below are generated by "
        "<code>scripts/roadmap_model/analyse.py</code>, <code>estop_positions.py</code> and <code>lift_plate_check.py</code>.</p>"
        "<h3>Wheel and axle (B1)</h3><p>The drive wheels are rubber, radius 0.100 m, with the axle (base_link) at 0.098 m: the 2 mm is intended tyre "
        "compression under load and levels the rigid chassis, which has no suspension. The model shows it as an intended contact (wheel-to-floor overlap "
        "%.1f mm, limit 2 mm), not as a conflict.</p>" % ic["overlap_mm"] +
        "<h3>Second E-stop, reach requirement (B2)</h3><p>A standing adult close to the robot presses it by hand without bending or sitting down: actuator "
        "centre 0.90 to 1.50 m above the floor at L1000, L1175 and L1350, facing outward and visible, no contact in the arm sweep, out of the ZED Mini view, "
        "cable routed. The reach study (%d random poses per arm and stop within the joint limits, poses through the post, the column, the adapter plate or "
        "the Getac discarded) counts the poses with an arm link within 5 mm of the housing. Recommended (proposed): <b>%s</b>. %s The combined model keeps "
        "P1 (datums second_estop_below_profile_top, parent lift_column_base_link) until the P-03 entry.</p>" % (ep["n_per_arm"], E(ep["recommended"]), E(ep["recommendation"])) + t_estop +
        "<h3>Lift base plate (B3)</h3><p>One 10 mm 6082-T6 plate, %.0f x %.0f mm, on the top of the centre-frame arch (top 304 mm). The arch top (2 mm "
        "S235JR, CAD MMP.04.00.00.000) carries 8 x M8 blind rivet nuts in two patterns: 120 x 100 mm (x +/-0.060, y +/-0.050) and 190 x 300 mm "
        "(x +/-0.095, y +/-0.150); the plate uses the inner one and is bolted from above with 4 x ISO 4762 M8 x 20 class 8.8. The DOLD column stands forward "
        "of the arch centre on the plate, screwed from below (4 x DIN 7500 M8, flush) with hole sets for bp000 (x 0.060) and bp050 (x 0.110). Length: "
        "from the rear arch holes minus 20 mm (x -0.080) to the column front at bp050 plus 20 mm (x 0.250). Assembly: the column onto the plate from below "
        "first, on the bench; then the plate onto the arch from above. The column front overhangs the arch front wall by %.0f mm at bp050 (%.0f mm at bp000).</p>" % (
            lp["size"][0] * 1000, lp["size"][1] * 1000, pl["overhang"]["bp050"]["column_front_ahead_of_arch_front_wall_m"] * 1000,
            pl["overhang"]["bp000"]["column_front_ahead_of_arch_front_wall_m"] * 1000) +
        "<p>Load check (above the plate %.1f kg, COM x %.3f, z %.3f m at L1350; braking at %.2f m/s2, the tip-over limit at L1350; arms at full forward "
        "reach with 2 x 4.1 kg: %.1f kg, COM x %.3f, z %.3f m). Sources: 6082-T6 Rp0.2 255 MPa (EN 485-2), S235JR fy 235 MPa (EN 10025-2), M8 8.8 "
        "Ft,Rd %.1f kN and Fv,Rd %.1f kN, rivet-nut flange pull-through Bp,Rd %.1f kN (EN 1993-1-8 Table 3.4). Largest utilisation: bolts %.2f, rivet-nut "
        "pull-through %.2f, plate %.2f, arch top sheet %.2f; column tilt up to %.2f deg. %s</p>" % (
            ab["L1350"]["mass_kg"], ab["L1350"]["com_m"][0], ab["L1350"]["com_m"][2], pl["decel_m_s2"], pl["arms_forward"]["mass_kg"], pl["arms_forward"]["com_m"][0],
            pl["arms_forward"]["com_m"][2], pl["cases"][0]["bolt_Ft_Rd_kN"], pl["cases"][0]["bolt_Fv_Rd_kN"], pl["cases"][0]["Bp_Rd_kN"], mu["bolt_utilisation"],
            mu["rivet_nut_pull_through_utilisation"], mu["plate_utilisation"], mu["arch_sheet_utilisation"], pl["max_column_tilt_deg"],
            "The load path goes into the arch with margin." if ok else "The 2 mm arch top sheet is the limit: it is over its yield in the worst case, so the load path needs a doubler under the arch top between the rear rivet nuts and the rear wall (or the outer rivet-nut pattern as well) before the arms carry a payload at full reach.") + t_plate +
        "<h3>TZBOT WCM-500-24 wireless charging (B4)</h3><p>Receiver 240 x 210 x 65 mm, about 5 kg, at the front of the base, centred, 240 mm along x "
        "(the narrower 210 mm across keeps it between the ultrasonic mounts), front edge %.1f mm from the front panel inner face, occupying %.0f to %.0f mm "
        "above the floor under the bay plate and the LiDAR. Bottom 50.0 mm above the floor, 2 mm below the base sheet; the lowest points of the robot "
        "apart from the wheels are the castor M6 bolt tips at %.1f mm and the M5 bolt tips at %.1f mm (full assembly STEP), so the ground clearance does not "
        "change. Floor gap = 50.0 mm minus the transmitter height, which is not in the datasheet folder: for the WCM-500 air gap of 10 to 30 mm the "
        "transmitter must be 20 to 40 mm tall; under 45 mm gives at least 5 mm. Base-sheet cut-out %d x %d mm (x %.3f to %.3f, y +/-%.3f), extending the "
        "contact-charger cut-out under the LiDAR; it removes: %s. A thin ferrite sheet on the receiver top (not metal foil) shields the electronics above.</p>" % (
            tz["position"]["front_edge_to_front_panel_inner_mm"], tz["position"]["occupies_z_mm"][0], tz["position"]["occupies_z_mm"][1],
            low["cad"]["castor_bolt_tips_m6x20"] * 1000, low["cad"]["m5x20_bolt_tips"] * 1000, cut["size_mm"][0], cut["size_mm"][1], cut["xy_m"][0], cut["xy_m"][1],
            cut["xy_m"][3], E("; ".join(cut["removes"]))) +
        "<p><b>Metal within 20 mm of the receiver</b> (front bay option %s):</p>" % E(an.get("front_bay_default", "A")) +
        table(["Part", "Clearance (mm)", "Overlap (mm)", "Proposed fix"], metal) +
        "<p><b>Distances from the receiver coil</b> (%s):</p>" % E(tz["emc_note"]) + table(["Item", "Distance (mm)", "Flag"], emc) +
        "<p>Questions to TZBOT: the transmitter height; the permitted shielding material and thickness on the receiver top; the minimum distance from the "
        "receiver to electronics; the magnetic field at 50 mm and 100 mm from the receiver during charging.</p>")
    return section("decisions", "Owner decisions of 2 Nov 2026: wheels, second E-stop, lift base plate, wireless charging", body,
                   "owner decisions of 2 Nov 2026; roadmap model analysis; CAD MMP.04.00.00.000 and the full assembly STEP (openamr-platform-hw main)")


def gi(prefix):
    """ID of the geometry issue whose parts start with prefix (IDs are assigned by analyse.py)."""
    for r in csv.DictReader(open(os.path.join(MODEL, "geometry_issues.csv"))):
        if r["parts"].startswith(prefix):
            return r["id"]
    return "?"


def frontbay_section():
    bs = json.load(open(os.path.join(HERE, "build_summary.json")))
    fb = bs["front_bay"]
    rows = []
    for o, title in (("A", "A: two-tier bay (proposed default)"), ("B", "B: DIN parts in the rear side pockets (28 Oct alternative)")):
        f = fb[o]["fit"]
        rows.append([E(title), str(f["placed"]), E(", ".join(f["not_placed"]) or "none"), E("; ".join("%s %s" % (k, v) for k, v in f.get("stays_in_place", {}).items()) or "none"),
                     "%.1f" % f["lowest_metal_above_receiver_mm"] if f["lowest_metal_above_receiver_mm"] is not None else "-",
                     "%.1f" % f["cover_margin_mm"], E(", ".join(f["scan_band_parts"]) or "none"), "%.1f" % f["min_gap_mm"]])
    t = table(["Option", "Parts placed", "Not placed", "Stays in place", "Lowest metal above the receiver (mm, >= 20)", "Margin to the cover (mm)", "Parts in the scan band", "Smallest gap (mm)"], rows)
    zones = lambda o: "; ".join("%s: %s" % (k, ", ".join(v)) for k, v in fb[o]["fit"]["by_zone"].items())
    body = ("<p>Both options keep the TZBOT receiver of B4 in place: electronics start at least 20 mm above its top (bay plate MEC-005 at z 0.135 on "
            "standoffs outside |y| 0.125), stay under the cover (0.290 m), out of the LiDAR scan plane band in the open sector, with 10 mm air gaps "
            "around converters and top access to every fuse (the fuse block and the PNOZ are not under the shelf or the lift base plate overhang). "
            "Catalogue outlines and their sources are in <code>scripts/roadmap_model/parts.yaml</code> and <code>front_bay.py</code> (PNOZ s3 750103 "
            "22.5 x 98 x 120.3 mm, MEAN WELL DDR-240B-24 63 x 125.2 x 100 mm, RSD-100B-24 159 x 97 x 38 mm, RSD-60G-5 120 x 50 x 33 mm, Blue Sea 5046 "
            "102 x 74 x 41 mm, reComputer J401 with the Orin NX and fan 118 x 115 x 45 mm, NUCLEO-144 133.34 x 70 mm). The exploded view has a "
            "switch, Front bay: option A / option B.</p>" + t +
            "<p><b>Option A</b> zones: %s. The DIN carrier sits on the centre-bracket front legs with the rail along y; the Jetson moves off bracket "
            "MMP.04.00.00.002, the EV_ICM-42688-P stays at imu_link with nothing heavy or vibrating on its bracket.</p>"
            "<p><b>Option B</b> zones: %s. The rear side pockets are 91 mm wide only between z 74 and 191 mm (36 mm at the flanges, %s), 71 mm with the "
            "battery tray wall: with the rail fore-aft, the DDR-240B-24 needs 125.2 mm across (rail on the floor) or 100 mm (rail on the side wall), the "
            "PNOZ s3 98 or 120 mm, so neither fits.</p>"
            "<p><b>Recommendation (proposed):</b> option A, the only one that places every front-bay part with the receiver in place. %s stays open for "
            "the rear zone (FB-A, FB-B and the BMS).</p>" % (E(zones("A")), E(zones("B")), gi("Rear side pockets"), gi("Rear zone layout")))
    return section("frontbay", "Front bay with the TZBOT receiver: option A vs option B", body, "front_bay.py; owner decision of 2 Nov 2026 (B4); P-03 rev20.2, E-01 rev1.6")


def parity_section():
    ps = json.load(open(os.path.join(HERE, "parity_summary.json")))
    ms = json.load(open(os.path.join(HERE, "mass_summary.json")))
    src = ps["sources"]
    srcs = ", ".join("%s %s" % (v["repository"].split("/")[-1], v["commit"][:7]) for v in src.values())
    rows = [[E(x)] for x in ps["out_list"]]
    pend = [[E(x)] for x in ps["pending_list"]]
    tot = ms["totals"]
    body = ("<p><b>Goal:</b> the roadmap becomes a renderer of the expanded combined_robot.xacro (openamr-upperbody-sw) at a pinned commit, with no "
            "hand-typed dimensions in model.js. One geometry, two presentations. URDF only: physics, inertials, collisions, ros2_control, MoveIt, Gazebo. "
            "Roadmap only: finishes, labels, exploded offsets, BOM classes, harness, fasteners, design-intent parts; a roadmap-only part always attaches to a "
            "URDF link with an offset.</p><p><b>Phases:</b> 1) warn-only parity report (this update); 2) URDF-to-GLB renderer plus an overlay file keyed by "
            "URDF link name; 3) the parity check fails CI above 0.5 mm, and the frozen fixture in openamr-upperbody-sw is removed; 4) the combined model "
            "feeds the lift joint, limits, mass, COM, collision reports and recorded MoveIt trajectories into the roadmap, and the roadmap feeds BOM masses, "
            "visual-only detail links and confirmed design-intent datums back.</p>"
            "<p><b>Phase 1 result</b> (combined model expanded with pip xacro and a minimal ament index at %s; bp000 and bp050, L1000, L1175 and L1350, hp30, "
            "arms at zero; tolerance 0.5 mm and 0.2 deg): %d mapped items, <b>%d matched</b>, <b>%d out of tolerance</b>, %d intended pending differences "
            "(%d mapped, %d roadmap-only), %d URDF links without a roadmap part, %d roadmap-only parts attached to URDF links. Report: %s; map: "
            "<code>scripts/roadmap_model/link_map.yaml</code>. CI runs it as a warning.</p>" % (
                E(srcs), ps["mapped_items"], ps["matched"], ps["out_of_tolerance"], ps["pending"], ps["pending_mapped"], ps["pending_roadmap_only"],
                ps["unmapped_urdf"], ps["roadmap_only"], A("model/parity_report.csv", "parity_report.csv")) +
            "<details><summary>Out of tolerance (%d)</summary>%s</details>" % (len(rows), table(["URDF link / roadmap part"], rows)) +
            "<details><summary>Intended pending differences (%d)</summary>%s</details>" % (len(pend), table(["Item and reason"], pend)) +
            "<p><b>Mass:</b> the combined model carries %.1f kg in total (base URDF %.1f kg); the roadmap model from BOM Issue 7.14 carries %.1f kg, COM "
            "(%.3f, %.3f, %.3f) m at L1000 and z %.3f m at L1350. %s gives the per-link masses for the platform-sw mass PR and for mass_provenance.yaml.</p>" % (
                ms["comparison"]["combined_model_total_kg"], ms["comparison"]["base_urdf_kg"], tot["L1000"]["mass_kg"], tot["L1000"]["com_m"][0], tot["L1000"]["com_m"][1],
                tot["L1000"]["com_m"][2], tot["L1350"]["com_m"][2], A("model/mass_export.yaml", "mass_export.yaml")))
    return section("parity", "Roadmap vs combined model", body, "combined_robot.xacro expanded at %s; scripts/roadmap_model/parity.py" % E(srcs))


def main():
    s = open(PAGE, encoding="utf-8").read()
    secs = [decisions_section(), frontbay_section(), model_section(), mech_section(), issues_section(), parity_section(), conflicts_section()]
    s = re.sub(r"<!--GEN:(\w+)-->.*?<!--/GEN:\1-->", "", s, flags=re.S)
    anchor = s.index('<section class="card" id="hwdrift">')
    end = s.index("</section>", anchor) + len("</section>")
    s = s[:end] + "".join(secs) + s[end:]
    open(PAGE, "w", encoding="utf-8").write(s)
    print("hardware.html sections written")


if __name__ == "__main__":
    main()
