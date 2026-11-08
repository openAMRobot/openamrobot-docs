# Changelog

All notable changes to the OpenAMRobot documentation site are recorded here. The format follows Keep a Changelog; the site has no version numbers, so entries are dated.

## 2026-11-08

### Changed

- Decision baseline of 8 Nov 2026 (P-03 rev20.6 item 30, decisions D-01 to D-34; register patch for openAMRobot/.github#90): compute Jetson Orin NX 8 GB on the reComputer Robotics 104 (D-01); lift foot fixed from above through the 260 x 30 mm tabs with 4 x DIN 7984 M8 x 14 8.8 into M8 tapped through MEC-019, now 350 x 140 mm, 224 x 40 mm DOLD-internal (D-20); backing plate tapped steel or 5 mm S235 with press-in nuts, the mechanical owner confirms (D-21); Build 1 base speed ceiling 0.5 m/s, designed limit, not measured (D-07); CTL-017 upper-body controller on CAN3 node 0x10 with NPN NO stop sensors (D-11); two battery trays (D-27); receiver frame owner and metal-free values unchanged (D-02, D-03). `check_roadmap.py` checks every cable, busbar and tie of `harness_routes.json` against the `cover_slot_*` keep-outs (D-06) and rejects the superseded compute, receiver and inward-band wording. Mass values unchanged and labelled "estimate, under ledger review (D-26)".
- Owner decisions of 8 Nov 2026 (P-03 rev20.4 item 28 and rev20.5 item 29; register update in openAMRobot/.github#90, change request openAMRobot/.github#89): the roadmap model is the reference for components, mass and placement. Getac ZX80 portrait on the fixed mount 55 mm lower than the item 26 placeholder, head light 10 mm below it; ZED Mini lens 60 mm ahead of J1_A (was 57 mm).
- TZBOT receiver: air gap 20 +-10 mm (no effect on the enclosure); no metal within 20 mm of the receiver sides, held by a 3D-printed plastic frame screwed to the steel base sheet (new part `tz_receiver_frame`, design by the mechanical owner, with a cable notch for the rear TF-Luna lead); parts above it 15 mm above its top. The receiver sits 20 mm in front of the rear panel; the trays stay 20 mm beside it; the G10 plate keeps its width. GI-121 to GI-123 keep their IDs with the new wording, GI-105 to GI-110 and GI-166 are closed.
- DOLD lift drawn from the supplier STEP (`facts.yaml` `column`): foot with mounting tabs 280 x 60.4 x 10 mm on a 224 x 40 mm screw pattern, static profile 240 x 60 mm to 503 mm plus a 2 mm cover, inner stage 209.5 x 53.3 x 470 mm from 60 mm retracted; head plate and lugs removed.
- Arch reinforcement GI-082: 4 x M8 8.8 ISO 4762 through-bolts into captive nuts in a 5 mm S235JR backing plate (`facts.yaml` `arch_fix`, decided fix, CAD pending).
- K1/K2 are Gigavac GX11CAC only (electrical owner, docs #68; P-03 rev20.4): option B is no longer reported, GI-008 and GI-009 closed.
- Harness: the slot is the gap between the cover lower edge and the panel upper edges (z 214 to 232 mm); `harness.py` keeps every cable, busbar and tie out of it and off the panel upper edges, the side-panel top flanges included, all around the robot, with no inward band; at the rear, parts may rise above it and their leads run down inside. The BMS busbar BB-06 (CBL-P62) rises inboard of the flange. Upper-body cables enter the base through two 50 x 25 mm openings left and right of the lift on the channel centre lines (power left, signal right) with disconnect points DP-LIFT-L and DP-LIFT-R; the centre bracket gets channel entry slots in its front and rear walls and the C-RM channel runs over the rear power module. Lift-cable support follows the checker: only W01 cables are exempt inside the battery and power module.
- Mass export (`mass_export.py`): each BOM line on one URDF link (adapter plate, arm profile, tablet mount, second E-stop, flag rod and flag on lift_carriage_link; stop sensors on lift_column_base_link; head camera on head_camera_link), real boxes for the DOLD column, the chassis envelope and the two hub motors, multi-part lines split over their parts; `analyse.py` places each mass at its part's box centre (the vertex mean put the cells 66 mm high) and counts the Getac pocket once, on the purchased line UI-002 (MEC-012 is allocation only, included in UI-002).
- Mass ledger (`scripts/roadmap_model/mass_ledger.yaml`, owner instruction 8 Nov 2026): every part counted once, quantity x its datasheet mass (EVE LF105 cells 8 x 1.98 kg, ZLLG80 hub motors 2 x 3.45 kg, Blickle LPA-VSTH 35K castors 4 x 0.3 kg, RPLIDAR S3 115 g, Gemini 336L 135 g, DDR-240B-24 0.8 kg, RSD-100B-24 0.6 kg, BS-6004 0.29 kg); custom parts from their design-intent solids (pocket trays with straps 1.479 kg, adapter plate set 1.546 kg, lift base plate 1.293 kg) or estimated from dimensions and material. The battery pack is no longer a 21.5 kg line: cells, busbars, sense harness, probes and insulation are their own lines, the trays, BMS, F0 and disconnect stay separate. The DOLD column is split into its static (8.89 kg) and moving (2.81 kg) share (`facts.yaml` `column.mass_split`). The export now holds every URDF link with mass: base_link, the wheel links (hub motors), the castor and castor-wheel links, lidar_link, the column, the carriage, the Getac, the head light, the head camera with its bracket and the wrist cameras; `mass_export.py` stops on a part counted twice or a line marked "included" that carries mass.
- Router: declared and cached base routes are checked against the cover-slot keep-outs like searched ones; a declared route in the slot is reported blocked and a cached one is routed again (`slot_rule.py`, shared by `harness.py` and `scripts/tests/test_harness_slot.py`, with the old P62 route as the failing case).
- P-03 rev20.6 item 30: lift fixing through the DOLD foot tabs on 260 x 30 mm with 4 x DIN 7984 M8 x 14 into the tapped MEC-019, now 350 x 140 x 10 mm (D-20; 224 x 40 mm is DOLD-internal); arch backing plate tapped steel or 5 mm S235 with press-in nuts (D-21); receiver fasteners outside the 20 mm frame zone (D-02); compute Jetson Orin NX 8 GB on the reComputer Robotics 104 (D-01); documents P-03 rev20.6, E-01 rev1.7, M-01 rev19.9.
- Reference pages: hardware architecture, OpenAMRobot 2.0 overview, general arrangement (lift energy chain instead of the mast-era rear slot zone), mass and stability, dark-store simulation and the platform-hw concepts and configuration pages carry the 8 Nov values; the configuration page drops the shop links and prices for the E-stop.

## 2026-11-03

### Changed

- Roadmap model harness: every cable of `cable_list.csv` belongs to a named harness (W01 rear power, W02 drive section, W03 and W04 left and right side trunks, W05 front sensors, W07 front tier, W08 lift column, W09 upper body) on a defined, supported route found by `scripts/roadmap_model/harness.py` on a voxel model of the base: along the floor, the side panels and the uprights, branching inward at each consumer, never over a component, never across the withdrawal path of a battery tray, the front tiers or the cover, crossing the drive section on two new over-wheel guards; tie points at 150 mm or less and within 50 mm of every connector and branch, grommets at the penetrations, labels at both ends of every cable, disconnect points DP-TRAY-L/R, DP-FT and DP-LIFT. Short lug-to-lug links are smooth curves at their class bend radius (25 mm² at least 60 mm).
- Lift and upper-body harness: deck exit and DP-LIFT behind the lift base plate, a fixed sleeve on the -y face of the static column and a vertical energy chain behind the column (inner 38 x 25 mm, bend radius 75 mm, 24 links, 0.792 m) checked at every 25 mm of the 350 mm stroke; the chain is drawn for the current lift height on the robot and exploded pages (the free lift cable of the robot page is removed).
- New files: `model/harness_routes.json` (routes, tie points, chain states; checked), `model/harness_cad_changes.csv` (mounting points and parts for CAD); `cable_list.csv` gains harness, labels, disconnect, route radius and tie-point columns; harness fasteners in `fastener_schedule.csv`; harness steps 9 to 11 and 18 in `assembly_sequence.csv`.
- `scripts/check_roadmap.py`: fails on an unsupported span over 150 mm or no tie point within 50 mm of a connector or branch, a cable over the top of or through a component, a cable across a withdrawal path, a bend radius below its class minimum, a lift cable outside the energy chain or a chain that does not hold over the stroke, and a cable without a harness or labels; with a failing and a passing test per rule.

## 2026-11-02

### Changed

- Register alignment after the owner decisions of 2 Nov 2026 were recorded in openAMRobot/.github#84 (decisions.yaml 5ed600e): TZBOT WCM-500-24 wireless charging is prepared in 2.0, the receiver unit is installed later (class "prepared, installed later"; base-sheet cut-out, F-CHG, KCHG and the start and fault lines prepared; manual charging through SB50 with the Daly 28.4 V / 20 A charger at any time); the charging-gap issues GI-036 and GI-121 to GI-123 are of kind "to solve before receiver installation" (minor); the Getac ZX80 is portrait only on a fixed portrait mount (BOM UI-002, design-intent pocket without pivot or detents; the checker still fails a landscape Getac); GI-080 is a major of kind "manual layout pending" (evans-kwashie), a manual two-level layout with datasheet outlines follows in the next PR; the charging register conflict is removed from the conflicts list (14 source conflicts). Issues: 0 blockers, 4 majors, 47 minors.
- TZBOT wireless charging values from the TZBOT WCM-500-24 Wireless Charger Instruction Manual V2.5 (2021-09-23): receiver 170 x 150 x 52 mm, about 1.5 kg, air gap 20 +-10 mm, misalignment X and Y +-20 mm, no metal within 20 mm (replacing 240 x 210 x 65 mm, about 5 kg, 0 to 50 mm, +-30 mm).
- Owner corrections of 2 Nov 2026 (to be entered in P-03 and M-01): wireless charging is prepared in 2.0; the TZBOT receiver position is at the rear panel on the centre line (170 mm along x, bottom 50 mm, class "prepared, installed later") with 4 + 4 LF105 cells in the side pockets and the power electronics on a plate above it (`scripts/roadmap_model/rear_layout.py`); one front bay layout (two tiers, no options); Getac ZX80 portrait only on a fixed mount, 40 mm lower, light bar 10 mm below; ZED Mini lens 57 mm ahead of J1_A; second E-stop on the adapter plate, button up (P1 to P4, their ghosts and the arm checks limited to valid poses). The -2 mm charging gap is a minor issue (to solve before receiver installation) and a known contact in `scripts/check_roadmap.py`.
- Independent review of 2 Nov 2026: GI-080 options 4 (four compact MIDI fuse holders instead of FB-B) and 5 (BMS upright against a tray wall) tried, neither fits; the arm valid-pose check counts the gripper fingers as adjacent to link7 (no false self-collision stops); the Documentation workflow installs the parity dependencies and the parity step no longer hides execution errors (out-of-tolerance items stay warnings).
- Owner corrections A5 to A9 of 2 Nov 2026 (to be entered in P-03 and M-01): arm checks use only valid poses (joint limits, no self-collision, no collision with the robot body; GI-081 closed); lift stop sensors on the rear face of the static DOLD column at z 120 / 295 / 470 mm with the cables down the static column, and a one-piece 6082-T6 adapter plate, 425 x 100 x 10 mm, with a 65 mm rear extension carrying the 20 x 20 flag rod (no separate rod bracket; GI-010 closed; design-intent STEP/STL updated); GI-082 and GI-025 are minor decided fixes, CAD pending; the CAD rear dimensions (552 / 337.6 / 235 mm) are the reference; the automatic packer placed neither FB-B nor the BMS after five attempts (the three A9 options, then four MIDI holders for FB-B and the BMS on a tray wall from the independent review; GI-080); new GI-126 for the F0 distance and the 25 mm² bend radius; two removable battery trays joined by the keyed connector PWR-018 (conflict with B-02 rev18.10 listed).
- OpenAMRobot 2.0 roadmap snapshot moved to 2 November 2026 (window 24 October to 1 November): the combined robot model merged (openamr-upperbody-sw #14, 41ff4ea) first in a new "This week" block, the P-03 rev19.8 to rev20.2 and battery decisions, the Gate A partial result of 30 October, real PR states and repository heads at 1 November 23:59 CET, decisions.yaml 5ed600e.
- Hardware page PARTS re-imported from BOM Issue 7.14 (146 records) by `scripts/roadmap_model/bom714.py`; new sections: 3D model coverage, mechanical parts, geometry and hardware issues, conflicts between sources.
- Shared roadmap model: placement data generated from datums.yaml, sensor_frames.yaml and the facts of record by `scripts/roadmap_model/build.py` (`model/placement.json`): front electronics bay, rear power zone, harness by domain, fittings, fasteners, design-intent parts; stage 9 Harness; lift base plate drawn 360 x 230 x 10 mm; small parts only with High quality. New model files: `bom_coverage.csv`, `fastener_schedule.csv`, `cable_list.csv`, `assembly_sequence.csv`, `geometry_issues.csv`, `source_snapshot.json`, `design_intent/`, `export/openamrobot2_layout.step`.
- `scripts/check_roadmap.py`: BOM coverage and model quantities, one model source for the robot and exploded pages, sensors and upper-body items within 1 mm of their sources, design heights, cable endpoints, partner terms; payload budget 15 MB for the default view.

## 2026-11-01

### Changed

- OpenAMRobot 2.0 roadmap pages, reference pages and the shared roadmap model aligned with the plan set of 1 November 2026 (P-03 rev20.2, E-01 rev1.6, M-01 rev19.7, BOM Issue 7.14): K1/K2 Gigavac GX11CAC recorded with the decision under the availability rule due 2 November 2026 (LEV100H withdrawn); no click shield (CTL-002 removed), IMU board TDK EV_ICM-42688-P on SPI4; second E-stop on the rear face of the static lift column, the OpenArm kit button ESTOP-KIT withdrawn; Gate A full run 6 November (30 October was Gate A partial, A1 control only); head camera baseline `hp30` recorded in the register; Getac ZX80 on a rotatable mount, landscape default and portrait second position (item 26); precharge fitted; SAFE 24 V converter MEAN WELL DDR-240B-24; DOLD written holding confirmation received, holding test still open; components follow the availability rule. Delivery status, evidence and repository heads stay at the 24 October snapshot. The BOM Issue 7 diagram carries a further superseded note. No part of the model moved; `scripts/sync_audit.json` regenerated.
- `scripts/check_roadmap.py`: the retired-chest-layout rule allows the phrase "portrait second position" and rejects "chest E-stop" in the model and the 3D pages.

## 2026-10-28

### Changed

- OpenAMRobot 2.0 upper-body decisions of 28 October 2026 (P-03 rev20.0 corrections line and items 15, 17, 18 and 24; E-01 rev1.5) in the reference pages, the roadmap hardware and progress pages and the dark-store pick simulation: chest tablet Getac ZX80 (replaces the ZX10), Falcon FLDL-i150x15-W head light (the Banner WLS28 is dropped), chest layout from the bottom up (head light, 30 mm gap, Getac; placeholders until M-09), the second E-stop, a Schneider XB4BS8445 with ZBE-102, on the rear face of the static lift column (the OpenArm kit button is superseded), fuse F-PD renamed F-PANEL, and the ZED Mini lens 42 mm ahead of the arm mount point with baseline pitch `hp30`. The simulation draws the second E-stop on the static column and starts at 30 degrees head pitch; the BOM Issue 7 diagram carries a superseded note.

## 2026-10-24

### Changed

- OpenAMRobot 2.0 roadmap snapshot of 24 October 2026, checked against P-03 rev19.7 (in force), E-01 rev1.4, BOM Issue 7.10 (corrected 24 October), P-02 rev19.2, the decisions register at 1c3f516 and main of every repository: system map, timeline with confirmed and proposed dates by source, the 35-step action plan, procurement state per BOM package, sensor frames with drift markers, the motion chain as designed and on main, and new Governance and organisation and Known drift sections.

### Added

- `scripts/check_roadmap.py`, run in CI: parses the embedded roadmap data, checks status counts, anchors, snapshot dates and forbidden terms.

## 2026-10-20

### Added

- OpenAMRobot 2.0 roadmap and status (snapshot 19 October 2026): a reference page with five linked interactive pages (Overview, Robot, Hardware, Architecture, Progress), including a step-by-step action plan to v2.0.0 under `docs/assets/roadmap/`. Each part shows delivery status, runtime evidence and physical acceptance separately, with links to its evidence. Linked from the project status page.

## 2026-10-12

### Changed

- OpenAMRobot 2.0 design pages follow P-03 revision 19.0 and BOM Issue 7.7:
  - Column position: the column axis is 330 mm behind the chassis front edge, x +0.060 m from `base_link` at `bp000` and +0.110 m at `bp050`.
  - Base camera: the Gemini 336L housing centre is 142.5 mm above the floor, `base_camera_link` (0.376, 0, 0.0445).
  - Near-field sensors: four MB7060 ultrasonic sensors and two TF-Luna cliff sensors.
  - IMU: the ICM-42688-P is on the centreline at x 0.195 m; the MPU6500 is the Gate A unit only.
  - LiDAR: the RPLIDAR S3 beam is 222.0 mm above the floor.
- The hardware architecture page no longer embeds the BOM Issue 7 diagram; the asset carries a superseded banner.
- The dark-store simulation uses the same column, camera, LiDAR and near-field positions and is labelled visualization only; grocery requirements belong to OpenAMRobot 3.0.

## 2026-10-11

### Changed

- Dark-store pick simulation follows option B: two base-plate positions (`bp000` default, `bp050`) instead of five, the OpenArm arm mount point 180 mm ahead of the column axis on the HFS6-60120 arm profile, the ZED Mini lens 22 mm ahead of and 223 mm above the arm mount point, and packing-table spots measured from the shoulder. Source in `tools/dark-store-sim/`, rebuilt into `docs/assets/simulation/`.

## 2026-10-09

### Changed

- OpenAMRobot 2.0 design pages follow the upper-body mounting option B (P-03 revision 18.9 item 18): DOLD Hexalift V4 lift column on a two-position base plate (`bp000`, `bp050`), OpenArm arm mount point 180 mm ahead of the column axis, shoulder 1000 to 1350 mm, ZED Mini head camera on the lift carriage and the configuration IDs. The general arrangement drawings of 28 September 2026 are withdrawn until they are regenerated from the option B CAD, and the F2S results of 28 September 2026 are withdrawn pending the option B rerun.

## 2026-09-28

### Added

- Collapsible table of contents on desktop: an arrow in the right sidebar hides it and widens the page; a tab on the right edge brings it back. The choice is remembered in the browser.

- Reference section "OpenAMRobot 2.0 design": section index, interactive hardware architecture diagram (BOM Issue 7), general arrangement drawings with parts list and mast detail, and the F2S mass and stability summary.
- Embedded-drawing styles (`oamr-frame`, `oamr-figure`) in `stylesheets/brand.css`.
- Cross-links from the mobile platform, upper body and reference index pages.
