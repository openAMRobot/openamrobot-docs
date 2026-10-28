# Chest equipment placeholders, tote riser, re-rendered media: evidence (28 Oct 2026)

Simulation visualization only; not mechanical, electrical or safety evidence. Chest positions are
placeholders until work package M-09 (P-03 rev20.0 item 24). The riser is an illustration, not a BOM part.

## Sources

- P-03 Decision Addendum rev20.0 item 24 (27 Oct 2026, 28 Oct 2026 correction), read through the Google
  Drive connector on 28 Oct 2026:
  - Chest layout on the moving part, bottom up: "chest E-stop, Getac ZX80 tablet (8 inch, 234 mm wide x
    149.8 mm tall x 17.6 mm, 590 g, IP67, USB-C PD), mounted landscape like the ZX10 it replaces (...; 28 Oct
    correction), head light". The chest E-stop is the same Schneider XB4BS8445 with ZBE-102 as the base button
    and replaces the OpenArm kit button.
  - 28 Oct 2026 corrections: "tablet is the Getac ZX80 instead of the ZX10, same landscape orientation";
    "234 mm wide x 149.8 mm tall, mounted landscape like the ZX10 it replaces; position from M-09".
  - Head light: Falcon Illumination FLDL-i150x15-W LED bar light, housing 158 x 17 x 20 mm, lit area
    148 x 13 mm, metal housing with acrylic cover; replaces the Banner WLS28.
- BOM Issue 7.14 (27 Oct 2026): SAF-001 quantity 2 (base front and chest), ARM-008 withdrawn, AUX-001 head
  light. UI-001 and UI-002 still name the previous tablet; that BOM correction is pending with the BOM
  owner. The BOM extract pages of this site (hardware.html, the BOM 7 architecture page) mirror the BOM
  and change with it.
- The Falcon technical data page (Baumer product page 24090) is not reachable from this environment; the
  head light dimensions are the ones P-03 quotes.

Drawn placeholders (model.js `M.CHEST`, front face of the arm profile, bottom up): chest E-stop (base E-stop
parts and colours); Getac ZX80 box 234 x 149.8 x 17.6 mm, landscape (234 mm across, 149.8 mm tall), dark grey
housing with a 1 mm black screen face forward, centred in the height between the chest E-stop and the head
light; head light 158 x 17 x 20 mm aluminium bar (long side across the chest, 20 mm deep) with a 148 x 13 mm
diffuse window on the front face, no glow, no light source in the scene. The tablet dock is not drawn.

Shared build option `chestPlaceholders` (`OAMR_MODEL.build(THREE, {chestPlaceholders: false})`, default true):
off draws the chest E-stop only. The exploded view builds with it on (all three items, static, no arm
motion, Placeholder badges). The robot page store scene builds with it off: the arms pass through the tablet
and head light placeholder positions during the order run (collision check below), so they are not shown
there until work package M-09 sets their positions; the page says so. No geometry was deleted.

## Stills

`node scripts/render_store.js 1280 720 --still 0 --cam front|rear --out <file>` on robot.html, and frame 0
of the exploded.html render mode (the one `scripts/render_tour.js` uses). Before: main at 7ac6543. After:
this branch. Palette-reduced PNG.

| File | Content |
|---|---|
| `robot_front_before.png`, `robot_front_after.png` | Before: illustrative chest E-stop (yellow box, red head) on the profile front, totes without support. After (chestPlaceholders off): the chest E-stop placeholder on the profile front (same parts and colours as the base E-stop), no tablet and no head light; a 20 x 20 mm aluminium riser frame under each tote |
| `robot_rear_before.png`, `robot_rear_after.png` | Rear: riser frames under both totes, standing on the cover; no tote rails |
| `exploded_assembled_before.png`, `exploded_assembled_after.png` | Exploded view, assembled (chestPlaceholders on): chest E-stop, Getac ZX80 (landscape) and head light on the profile front |

## Geometry check

`geometry_diff.txt` (inventory from `geometry_dump.js`): every mesh of the robot page scene (render mode,
t = 0) and of a fresh `OAMR_MODEL.build` on exploded.html, compared by path, vertex count, position hash,
world box, colour, roughness, metalness and emissive colour.

- Against main 7ac6543: robot page 194 meshes identical; removed 2 (the illustrative chest E-stop); added 3
  (chest_estop) and 16 (tote riser bars). Exploded build: 138 identical, 7 added (chest_estop 3,
  getac_tablet 2, head_light 2). Nothing else changed.
- Against 7c0a529 (ZX80 drawn upright, 149.8 mm across): robot page 213 identical; exploded build 143 identical, the 2
  tablet meshes replaced by the ZX80 landscape box.

Robot-frame boxes at bp000, L1000 (m): chest E-stop x 0.300 to 0.382, z 0.8615 to 0.9085; Getac ZX80
x 0.300 to 0.3176, y -0.117 to 0.117, z 0.9551 to 1.1049; head light x 0.300 to 0.320, y -0.079 to 0.079,
z 1.1515 to 1.1685 (window y -0.074 to 0.074, z 1.1535 to 1.1665). Gaps 46.6 mm below and above the tablet.

## Collision check

`node collision_check.js <out.json> [page]` (page served on port 8765; default robot.html): robot.html order
run in the render mode at speed 4 and 24 fps (1536 frames, 255.9 s of simulated time), every 10th frame (154
samples); bounding boxes of every arm link mesh (base, link1 to link7, two fingers, both arms) against each
chest item drawn in the scene, computed per vertex in the robot frame. Boxes are axis-aligned, so an overlap
marks possible contact, not proven mesh contact. The arms, the pick logic and the items were not changed.
`minGap` in each JSON gives the closest approach per link and item.

### Store scene as rendered (chestPlaceholders off)

`collision_store_scene.json`: chest items in the scene: chest_estop only. 0 overlaps.

### Getac ZX80 and head light at their placeholder positions (input for work package M-09)

`collision_chest_placeholders_m09.json`: the same run on a temporary copy of robot.html with the option on
(all three chest items drawn; the copy was deleted after the run). Getac ZX80 landscape: 32 overlaps in 21 of
154 sampled frames: 26 with the Getac ZX80 (right link2 9, left link2 6, right link3 5, right link5 3, left
link5 2, left link7 1), 6 with the head light (right link5 3, right link4 2, right link3 1), none with the
chest E-stop.

| Frame | Sim time (s) | Arm | Link | Item | Box overlap x, y, z (m) |
|---|---|---|---|---|---|
| 170 | 28.33 | right | link5 | getac_tablet | 0.0174, 0.0024, 0.0236 |
| 180 | 30.00 | right | link2 | getac_tablet | 0.0108, 0.0125, 0.0498 |
| 180 | 30.00 | right | link3 | getac_tablet | 0.0176, 0.0079, 0.0341 |
| 190 | 31.67 | right | link2 | getac_tablet | 0.0112, 0.0125, 0.0526 |
| 190 | 31.67 | right | link3 | getac_tablet | 0.0176, 0.044, 0.0448 |
| 380 | 63.33 | right | link5 | head_light | 0.021, 0.0083, 0.0108 |
| 540 | 90.00 | right | link2 | getac_tablet | 0.0108, 0.0124, 0.0498 |
| 540 | 90.00 | right | link3 | getac_tablet | 0.0176, 0.0087, 0.034 |
| 550 | 91.67 | right | link2 | getac_tablet | 0.0113, 0.0125, 0.0527 |
| 550 | 91.67 | right | link3 | getac_tablet | 0.0176, 0.0447, 0.0449 |
| 670 | 111.67 | left | link5 | getac_tablet | 0.0176, 0.024, 0.0372 |
| 690 | 115.00 | left | link5 | getac_tablet | 0.0176, 0.0335, 0.0265 |
| 690 | 115.00 | left | link7 | getac_tablet | 0.0107, 0.0158, 0.063 |
| 930 | 155.00 | right | link2 | getac_tablet | 0.0045, 0.0125, 0.0573 |
| 1080 | 180.00 | left | link2 | getac_tablet | 0.0073, 0.0124, 0.0855 |
| 1130 | 188.33 | left | link2 | getac_tablet | 0.0112, 0.0125, 0.0607 |
| 1140 | 190.00 | left | link2 | getac_tablet | 0.011, 0.0125, 0.0573 |
| 1180 | 196.67 | left | link2 | getac_tablet | 0.003, 0.0124, 0.0788 |
| 1190 | 198.33 | left | link2 | getac_tablet | 0.0067, 0.0125, 0.0803 |
| 1240 | 206.67 | left | link2 | getac_tablet | 0.0009, 0.0125, 0.0816 |
| 1290 | 215.00 | right | link3 | getac_tablet | 0.0076, 0.0421, 0.0476 |
| 1290 | 215.00 | right | link3 | head_light | 0.0076, 0.0041, 0.017 |
| 1290 | 215.00 | right | link4 | head_light | 0.021, 0.0196, 0.017 |
| 1290 | 215.00 | right | link5 | getac_tablet | 0.0006, 0.0739, 0.0496 |
| 1290 | 215.00 | right | link5 | head_light | 0.004, 0.0359, 0.017 |
| 1300 | 216.67 | right | link4 | head_light | 0.021, 0.0152, 0.017 |
| 1300 | 216.67 | right | link5 | getac_tablet | 0.0176, 0.0746, 0.0497 |
| 1300 | 216.67 | right | link5 | head_light | 0.021, 0.0366, 0.017 |
| 1400 | 233.33 | right | link2 | getac_tablet | 0.011, 0.0125, 0.0786 |
| 1410 | 235.00 | right | link2 | getac_tablet | 0.0156, 0.0125, 0.0975 |
| 1420 | 236.67 | right | link2 | getac_tablet | 0.0116, 0.0125, 0.0825 |
| 1460 | 243.33 | right | link2 | getac_tablet | 0.0094, 0.0125, 0.0595 |

Other placement findings: the ZX80 box (234 mm across) extends 87 mm beyond each side face of the 60 mm
profile, at shoulder height, where the arm links pass; the head light (158 mm) extends 49 mm. The chest
E-stop placeholder stands 82 mm ahead of the profile face: x 0.382 m at bp000 (inside the 0.39 m chassis
front edge) and 0.432 m at bp050 (42 mm ahead of it). The robot page pick logic keeps its 65 mm "arm profile
/ chest E-stop" self-collision box, as before. These are inputs for work package M-09; nothing was moved.
