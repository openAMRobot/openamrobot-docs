# Changelog

All notable changes to the OpenAMRobot documentation site are recorded here. The format follows Keep a Changelog; the site has no version numbers, so entries are dated.

## 2026-11-02

### Changed

- TZBOT wireless charging values from the TZBOT WCM-500-24 Wireless Charger Instruction Manual V2.5 (2021-09-23): receiver 170 x 150 x 52 mm, about 1.5 kg, air gap 20 +-10 mm, misalignment X and Y +-20 mm, no metal within 20 mm (replacing 240 x 210 x 65 mm, about 5 kg, 0 to 50 mm, +-30 mm).
- Owner corrections of 2 Nov 2026 (to be entered in P-03 and M-01): wireless charging is a release 3.0 item; the TZBOT receiver is reserved at the rear panel on the centre line (170 mm along x, bottom 50 mm, not installed in 2.0) with 4 + 4 LF105 cells in the side pockets and the power electronics on a plate above it (`scripts/roadmap_model/rear_layout.py`); one front bay layout (two tiers, no options); Getac ZX80 portrait, 40 mm lower, light bar 10 mm below; ZED Mini lens 57 mm ahead of J1_A; second E-stop on the adapter plate, button up (P1 to P4, their ghosts and the arm checks limited to valid poses). The -2 mm charging gap is a minor issue (reserved for 3.0) and a known contact in `scripts/check_roadmap.py`.
- Independent review of 2 Nov 2026: GI-080 options 4 (four compact MIDI fuse holders instead of FB-B) and 5 (BMS upright against a tray wall) tried, neither fits; the arm valid-pose check counts the gripper fingers as adjacent to link7 (no false self-collision stops); the Documentation workflow installs the parity dependencies and the parity step no longer hides execution errors (out-of-tolerance items stay warnings).
- Owner corrections A5 to A9 of 2 Nov 2026 (to be entered in P-03 and M-01): arm checks use only valid poses (joint limits, no self-collision, no collision with the robot body; GI-081 closed); lift stop sensors on the rear face of the static DOLD column at z 120 / 295 / 470 mm with the cables down the static column, and a one-piece 6082-T6 adapter plate, 425 x 100 x 10 mm, with a 65 mm rear extension carrying the 20 x 20 flag rod (no separate rod bracket; GI-010 closed; design-intent STEP/STL updated); GI-082 and GI-025 are minor decided fixes, CAD pending; the CAD rear dimensions (552 / 337.6 / 235 mm) are the reference; GI-080 stays a blocker after five attempts (the three A9 options, then four MIDI holders for FB-B and the BMS on a tray wall from the independent review, none fits); new GI-126 for the F0 distance and the 25 mm² bend radius; two removable battery trays joined by the keyed connector PWR-018 (conflict with B-02 rev18.10 listed).
- OpenAMRobot 2.0 roadmap snapshot moved to 2 November 2026 (window 24 October to 1 November): the combined robot model merged (openamr-upperbody-sw #14, 41ff4ea) first in a new "This week" block, the P-03 rev19.8 to rev20.2 and battery decisions, the Gate A partial result of 30 October, real PR states and repository heads at 1 November 23:59 CET, decisions.yaml a9e229e.
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
