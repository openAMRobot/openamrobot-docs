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

## TZBOT reserved position (WCM-500-24 manual V2.5, release 3.0)

The TZBOT WCM-500-24 receiver (170 x 150 x 52 mm) is reserved at the rear under the battery (release 3.0, not installed in 2.0);
the front position and its images are removed. Orthographic views of the shared model in Playwright Chromium (swiftshader); the six
pages load with no console errors.

- `tzbot_reserved_rear_section.jpg`: side view, other parts ghosted; reserved receiver in orange at z 50 to 102 mm under the cells
  (overlap 48 mm with the cells, the warning issue); the 52 mm floor transmitter is not drawn (gap -2 mm).
- `front_bay_options_A_B_rear_receiver.jpg`: front bay option A (left) and B (right) with the bay plate on the base sheet, top view
  with the cover off and left side elevation.
- `tzbot_receiver_zone.jpg`, `tzbot_receiver_below.jpg` and `front_bay_A_vs_B_*.jpg` show the earlier front receiver (kept as the record).
