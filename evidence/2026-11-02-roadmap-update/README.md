# Roadmap update, snapshot 2 Nov 2026: visual review

Screenshots taken with the preinstalled Playwright Chromium (swiftshader) against a local server of
`docs/assets/roadmap` on the branch `roadmap/2026-11-02`: the six pages loaded with no console errors, and the
exploded-view switch "Front bay: option A / option B" shows one option at a time.
Model renders come from `scripts/roadmap_model/shots.js` (exploded view, render mode, `window.__renderKey`);
robot page stills from `scripts/render_store.js --still 4 --cam front|rear` (not retaken: robot page geometry
outside the changed parts is unchanged).

Retaken for the owner decisions of 2 Nov 2026 and the layout fixes:

- Front bay, option A vs B side by side: `front_bay_A_vs_B_top.jpg` (top view, cover off), `front_bay_A_vs_B_side_section.jpg`
  (side view through the TZBOT receiver), `front_bay_A_vs_B_opened.jpg` (opened base); single views `front_bay_A_*.jpg`, `front_bay_B_*.jpg`.
- TZBOT receiver: `tzbot_receiver_below.jpg` (base-sheet cut-out, floor transmitter with a placeholder height),
  `tzbot_receiver_zone.jpg` (ferrite sheet, 20 mm metal-free zone, MMP.07 and MMP.04.00.00.002 inside it).
- Second E-stop: `estop_positions_rear.jpg` (P2 drawn, P1, P3, P4 as ghosts), `estop_p2_closeup.jpg`.
- Lift base plate on the centre-frame arch: `lift_base_plate_arch.jpg`, `lift_base_plate_side.jpg`.
- Rear zone around the battery tray: `rear_zone.jpg`. Harness below the LiDAR scan plane: `harness_front.jpg`.
- Getac pocket portrait with the eccentric pivot: `getac_portrait.jpg`.
- Overview: `exploded_assembled.jpg`, `exploded_opened_base.jpg`.
- Hardware page sections: `hardware_decisions.jpg`, `hardware_frontbay.jpg`, `hardware_parity.jpg`.

Kept from the first pass of this snapshot (unchanged parts): `robot_front.jpg`, `robot_rear.jpg`, `exploded_exploded.jpg`,
`exploded_cutaway.jpg`, `exploded_stage1.jpg` to `exploded_stage9.jpg`, `getac_landscape.jpg`, `harness_upper_service_loop.jpg`,
`rear_k1k2_option_b_ghost.jpg`, `issue_flag_rod_outside_plate.jpg`, `hardware_model_coverage.jpg`, `hardware_mechanical_parts.jpg`,
`hardware_geometry_issues.jpg`, `index_this_week.jpg`. Superseded and removed: the deck-bolt, old receiver, old front bay, old rear zone,
old portrait and old harness images.

## TZBOT correction (WCM-500-24 manual V2.5)

Retaken after the TZBOT values were corrected to the WCM-500-24 Wireless Charger Instruction Manual V2.5 (170 x 150 x 52 mm,
about 1.5 kg, air gap 20 +-10 mm, X and Y +-20 mm, no metal within 20 mm). Orthographic views of the shared model (`model.js`
with `placement.json`) in Playwright Chromium (swiftshader); the six pages load with no console errors.

- `tzbot_side_section.jpg`: receiver (blue, 50 to 102 mm) and floor transmitter (0 to 52 mm) from the side, other parts ghosted;
  red band: the 2 mm overlap (GI-036, known, warn only); ferrite sheet on the receiver top; metal-free zone in pink.
- `tzbot_cutout_below.jpg`: from below, the base-sheet cut-out (197 x 190 mm to the front panel flange line; receiver + 20 mm is
  210 x 190 mm) around the 170 x 150 mm receiver.
- `tzbot_front_bay_options_A_B.jpg`: front bay option A (left) and option B (right) with the new receiver, top view with the cover
  off and left side elevation; bay plate at 122 mm (receiver top + 20 mm).
- `tzbot_receiver_zone.jpg` and `tzbot_receiver_below.jpg` show the earlier 240 x 210 x 65 mm receiver (kept as the record).
