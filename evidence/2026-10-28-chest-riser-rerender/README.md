# Upper-body layout of 28 Oct 2026, lift stop sensors, one model on both pages: evidence

Simulation visualization only; not mechanical, electrical or safety evidence. The second E-stop, tablet, head
light and lift stop sensor set positions are placeholders until work package M-09. The riser is an illustration,
not a BOM part. E-stops and sensors are drawn geometry only; no safety logic is touched.

## Sources

- P-03 Decision Addendum rev20.0 (read through the Google Drive connector on 28 Oct 2026): item 24 and the layout
  update of 28 Oct 2026 (second E-stop on the rear face of the static DOLD lift profile, close to its upper edge;
  moving chest bottom up head light, its top edge 30 mm below the Getac, then the Getac ZX80, 234 mm wide x
  149.8 mm tall x 17.6 mm, landscape, 50 mm higher than before; lift stop sensors at z 120, 295 and 470 mm above
  the column base, flag centre 410 mm below the adapter plate underside, 2 mm air gap); items 15, 17 and 18 (head
  camera lens 42 mm ahead of the shoulder, baseline pitch hp30, was hp25; adapter plate 360 x 100 mm).
- Drawing LIFT-SNS-01 rev 1 (27 Oct 2026, read through the Google Drive connector): View 1 side elevation at
  L1000 (sensors S1 to S3 on a 60 mm end face of the static profile, rod hanging from the adapter plate overhang,
  M5 through the plate, corner bracket against rotation; static profile top "assumed z = 500 (TBC)"); View 2
  section at a sensor (sensor axis parallel to the face, 15 mm from it; flag 2 mm in front of the sensor face,
  5 to 50 mm from the profile face; rod 9 mm beside the sensor, 30 to 50 mm from the face; bracket legs 40 mm,
  4 mm thick).
- BOM Issue 7.14: LFT-001 three SICK IME12-04BNSZC0S, LFT-002 three cables (not drawn), LFT-003 three SICK
  BEF-WN-M12 (5308447), LFT-004 MISUMI 5 series 20 x 20 profile L 430 tapped M5, LFT-005 MISUMI 5 series corner
  bracket 20 square, LFT-006 SS400 plate 45 x 20 x 2 with 2 x 4.5 mm holes, LFT-007 fasteners (not drawn); SAF-001.
- Pending with their owners (not changed here): BOM Issue 7.14 UI-001 and UI-002 still name the previous tablet;
  the register CONFIG-IDS entry gives hp25; the platform-sw URDF still has the lens 22 mm ahead and hp25.

## What is drawn (both pages, one model)

- One robot on both pages: the `chestPlaceholders` option is removed; robot.html builds with `fittings` and
  `headPitch: 30`, exploded.html with `headPitch: 30`. Only robot page scene items that are not registry parts
  (store, totes, riser, decals, lift cable, wrist cameras) differ.
- Second E-stop: rear face of the static profile, facing rearward, centre 40 mm below its upper edge (P-03
  position, see the sweep below).
- Moving chest: head light (top edge 30 mm below the Getac bottom edge), Getac ZX80 landscape box.
- Lift stop sensor set (LFT-001, LFT-003 to LFT-006): LIFT-SNS-01 shows an end face but names neither end, and its
  60 mm plate overhang matches neither end of option B (front 120 mm under the arm profile, rear 0); the rear face
  carries the second E-stop at the S3 height. The set is therefore drawn on the left side face (+y), placeholder
  until M-09. Sensors and brackets in the static group at z 120, 295 and 470 mm above the column base; rod,
  corner bracket and flag in the moving group. check_roadmap.py checks that the flag faces S1, S2 and S3 at
  L1000, L1175 and L1350 (flag centre = plate underside - 410 mm = 120, 295, 470 mm above the column base), the
  2 mm gap and the 9 mm rod offset.
- Finding for M-01 and M-09: with the 100 mm adapter plate (20 mm side overhang) the rod, 30 to 50 mm from the
  face as in View 2, sits 10 to 30 mm outside the plate edge; the M5 fixing through the plate in View 1 needs the
  plate over the rod. The corner bracket is drawn bridging the plate edge.

## Visible defects fixed (before c646911, after this branch)

| Fix | Crop |
|---|---|
| Lift cable ran through the second E-stop housing (its rear drop hung at y 0.012 to 0.016 m, 30 mm behind the rear face, where the E-stop now stands); the rear drop now runs beside the rear face on the -y side (y -0.03 to -0.035 m), clear of the E-stop at every lift position | `fix_cable_second_estop_before_after.png` |
| Adapter plate drawn 72 mm wide; P-03 item 18 gives 360 x 100 mm; now 100 mm (20 mm side overhang) | `fix_adapter_plate_width_before_after.png` |

No other visible defect was found in the review stills of both pages (front, rear, side, top; close-ups of the
base, column, chest and head).

## Stills (1280 x 720, palette-reduced PNG)

| File | Content |
|---|---|
| `robot_front_after.png`, `robot_rear_after.png`, `robot_overview_after.png` | robot.html front, rear and store overview (render mode, t = 0) |
| `exploded_assembled_after.png`, `exploded_rear_after.png` | exploded.html assembled, front and rear three-quarter |
| `column_top_L1000.png`, `column_top_L1350.png` | Column top close-ups: second E-stop, sensors, rod and flag, lift cable at L1000 and L1350 |
| `lift_sensors_exploded.png` | Exploded view, assembled: the sensor set on the left side face |
| `store_t65_second_estop_overlap.png` | Store run at 65 s: the right gripper with a bottle at the column rear |
| `*_before.png` | main 7ac6543 |

## Geometry diff

`geometry_diff.txt` (inventory from `geometry_dump.js`): against main 7ac6543, robot page 186 identical, 10 removed,
55 added; exploded build 132 identical, 6 removed, 37 added. Against c646911: robot page 211 identical, 2 replaced
(adapter plate, lift cable), 28 added (Getac 2 and head light 2 now drawn on the robot page, sensors 12, brackets
6, rod 3, corner bracket 2, flag 1); exploded build 144 identical, adapter plate replaced, 24 added (the sensor set).

## Synchronization audit

`node scripts/audit_sync.js` writes `scripts/sync_audit.json`; check_roadmap.py fails when it reports a mismatch or
is older than model.js, exploded.json, robot.html or exploded.html. Robot page at L1000, bp000, hp30, arms at the
assembled pose; exploded view in the render mode at frame 0 (explode factor 0, largest part offset from home
0 m). 63 part groups, 0 mismatches. The robot page applies the order-run timeline at load (left
arm at its first pick pose); the audit sets both arms to the assembled pose first.

## Collision report

`node collision_check.js collision.json` (page served on port 8765): robot.html order run in the render mode at
speed 4 and 24 fps (1536 frames, 255.9 s of simulated time), every 10th frame (154 samples); boxes in
the robot frame. Movers: every arm link (base, link1 to link7, two fingers, both arms) and the item a gripper
carries. Targets: Getac, head light, head camera, head camera bracket, second E-stop, rod, corner bracket, flag,
each sensor and each bracket. Axis-aligned boxes: an overlap marks possible contact, not proven mesh contact.
Arms and pick logic unchanged; nothing moved.

37 overlaps in 20 sampled frames: getac_tablet 23, rod_corner_bracket 3, head_light 2, flag_rod 2, second_estop 2, lift_stop_sensors_S3 2, lift_sensor_brackets_S3 2, head_camera 1.

| Frame | Sim time (s) | Mover | Target | Box overlap x, y, z (m) |
|---|---|---|---|---|
| 190 | 31.67 | right link2 | getac_tablet | 0.0112, 0.0125, 0.0026 |
| 190 | 31.67 | right link3 | head_light | 0.021, 0.006, 0.017 |
| 360 | 60.00 | right link5 | getac_tablet | 0.0176, 0.0159, 0.0017 |
| 390 | 65.00 | right finger1 | flag_rod | 0.0188, 0.0224, 0.0159 |
| 390 | 65.00 | right finger1 | rod_corner_bracket | 0.0188, 0.02, 0.0159 |
| 390 | 65.00 | right finger2 | second_estop | 0.0114, 0.04, 0.0307 |
| 390 | 65.00 | right finger2 | rod_corner_bracket | 0.02, 0.0145, 0.023 |
| 390 | 65.00 | right finger2 | lift_stop_sensors_S3 | 0.0255, 0.0165, 0.0147 |
| 390 | 65.00 | right finger2 | lift_sensor_brackets_S3 | 0.04, 0.0245, 0.0177 |
| 390 | 65.00 | carried item (right) | second_estop | 0.016, 0.0037, 0.047 |
| 390 | 65.00 | carried item (right) | flag_rod | 0.02, 0.0224, 0.1707 |
| 390 | 65.00 | carried item (right) | rod_corner_bracket | 0.02, 0.02, 0.023 |
| 390 | 65.00 | carried item (right) | lift_stop_sensors_S3 | 0.048, 0.0165, 0.019 |
| 390 | 65.00 | carried item (right) | lift_sensor_brackets_S3 | 0.04, 0.04, 0.025 |
| 550 | 91.67 | right link2 | getac_tablet | 0.0113, 0.0125, 0.0027 |
| 550 | 91.67 | right link3 | head_light | 0.021, 0.0067, 0.017 |
| 670 | 111.67 | left link5 | getac_tablet | 0.0176, 0.024, 0.0872 |
| 680 | 113.33 | left link4 | getac_tablet | 0.0054, 0.0042, 0.0269 |
| 690 | 115.00 | left link5 | getac_tablet | 0.0176, 0.0335, 0.0765 |
| 690 | 115.00 | left link7 | getac_tablet | 0.0107, 0.0158, 0.0801 |
| 930 | 155.00 | right link2 | getac_tablet | 0.0045, 0.0125, 0.0073 |
| 1080 | 180.00 | left link2 | getac_tablet | 0.0073, 0.0124, 0.0696 |
| 1130 | 188.33 | left link2 | getac_tablet | 0.0112, 0.0125, 0.0107 |
| 1140 | 190.00 | left link2 | getac_tablet | 0.011, 0.0125, 0.0073 |
| 1180 | 196.67 | left link2 | getac_tablet | 0.003, 0.0124, 0.0626 |
| 1190 | 198.33 | left link2 | getac_tablet | 0.0067, 0.0125, 0.0618 |
| 1240 | 206.67 | left link2 | getac_tablet | 0.0009, 0.0125, 0.0572 |
| 1290 | 215.00 | right link3 | getac_tablet | 0.0076, 0.0421, 0.0976 |
| 1290 | 215.00 | right link4 | getac_tablet | 0.0176, 0.0576, 0.029 |
| 1290 | 215.00 | right link4 | head_camera | 0.0382, 0.0028, 0.038 |
| 1290 | 215.00 | right link5 | getac_tablet | 0.0006, 0.0739, 0.0996 |
| 1300 | 216.67 | right link4 | getac_tablet | 0.0176, 0.0532, 0.027 |
| 1300 | 216.67 | right link5 | getac_tablet | 0.0176, 0.0746, 0.0997 |
| 1400 | 233.33 | right link2 | getac_tablet | 0.011, 0.0125, 0.0286 |
| 1410 | 235.00 | right link2 | getac_tablet | 0.0156, 0.0125, 0.0475 |
| 1420 | 236.67 | right link2 | getac_tablet | 0.0116, 0.0125, 0.0325 |
| 1460 | 243.33 | right link2 | getac_tablet | 0.0094, 0.0125, 0.0095 |

Lift parts against the scene (308 entries): sensors S1 and S2 overlap the left tote body in every
sampled frame (box overlap 0.021 x 0.0032 x 0.0175 m and 0.021 x 0.0032 x 0.019 m: the tote wall is 3.2 mm
inside the sensor envelope); no overlap of the rod, flag, corner bracket, brackets or S3 with the totes, risers or
the lift cable (closest: corner bracket to cable 18.3 mm, flag to cable 13.3 mm, brackets to cable 8.3 mm).

### Second E-stop height sweep

The E-stop box moved down from the drawn position in 10 mm steps against every mover over the full run:

| Moved down (mm) | Centre below the static top (mm) | Overlaps | Movers |
|---|---|---|---|
| 0 | 40 | 2 | carried item (right), right finger2 |
| 10 | 50 | 2 | carried item (right), right finger2 |
| 20 | 60 | 2 | carried item (right), right finger2 |
| 30 | 70 | 2 | carried item (right), right finger2 |
| 40 | 80 | 1 | carried item (right) |
| 50 | 90 | 1 | carried item (right) |
| 60 | 100 | 1 | carried item (right) |
| 70 | 110 | 1 | carried item (right) |
| 80 | 120 | 1 | carried item (right) |
| 90 | 130 | 1 | carried item (right) |
| 100 | 140 | 1 | carried item (right) |
| 110 | 150 | 1 | carried item (right) |
| 120 | 160 | 1 | carried item (right) |
| 130 | 170 | 1 | carried item (right) |
| 140 | 180 | 0 | - |
| 150 | 190 | 0 | - |

The first clear height is 140 mm below the drawn position, a centre 180 mm below the static profile top: more than
the 100 mm allowed, so the P-03 position (centre 40 mm below the top) is kept; the registry records the result as
an input for M-09.
