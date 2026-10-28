# Chest equipment placeholders, tote riser, re-rendered media: evidence (28 Oct 2026)

Simulation visualization only; not mechanical, electrical or safety evidence. Chest positions are
placeholders until work package M-09 (P-03 rev20.0 item 24). The riser is an illustration, not a BOM part.

## Sources

- P-03 Decision Addendum rev20.0 item 24 (27 Oct 2026, correction 28 Oct 2026): chest layout on the moving
  part, bottom up: chest E-stop, Getac ZX10, head light. The chest E-stop is the same Schneider XB4BS8445 with
  ZBE-102 as the base button and replaces the OpenArm kit button. The head light is the Falcon Illumination
  FLDL-i150x15-W LED bar light (replaces the Banner WLS28): housing 158 x 17 x 20 mm, lit area 148 x 13 mm,
  metal housing with acrylic cover.
- Falcon FLDL-i150x15-W technical data (Baumer product page 24090): the host is not reachable from this
  environment, so the dimensions are taken from P-03 rev20.0 item 24, which quotes them.
- Getac ZX10 specification: 275 x 192 x 17.9 mm, 1.04 kg (values given with the task; the host is not
  reachable from this environment, so they were not fetched independently). Exact generation and SKU are
  pending in BOM Issue 7.14 (UI-001). The dock is not drawn.
- BOM Issue 7.14 (27 Oct 2026): SAF-001 quantity 2 (base front and chest), ARM-008 withdrawn, UI-001 Getac
  ZX10, AUX-001 head light.

Drawn placeholders (model.js `M.CHEST`, front face of the arm profile, bottom up): chest E-stop (base E-stop
parts and colours), Getac ZX10 box 275 x 192 x 17.9 mm in landscape with a 1 mm dark screen face forward,
head light 158 x 17 x 20 mm aluminium bar (long side across the chest, 20 mm deep) with a 148 x 13 mm
diffuse window on the front face; no glow, no light source in the scene.

Shared build option `chestPlaceholders` (`OAMR_MODEL.build(THREE, {chestPlaceholders: false})`, default true):
off draws the chest E-stop only. The exploded view builds with it on (all three items, static, no arm
motion, Placeholder badges). The robot page store scene builds with it off: the arms pass through the Getac
and head light placeholder positions during the order run (collision check below), so they are not shown
there until work package M-09 sets their positions; the page says so. No geometry was deleted.

## Stills

`node scripts/render_store.js 1280 720 --still 0 --cam front|rear --out <file>` on robot.html, and frame 0
of the exploded.html render mode (the one `scripts/render_tour.js` uses). Before: main at 7ac6543. After: this branch. Palette-reduced
PNG.

| File | Content |
|---|---|
| `robot_front_before.png`, `robot_front_after.png` | Before: illustrative chest E-stop (yellow box, red head) on the profile front, totes without support. After (chestPlaceholders off): the chest E-stop placeholder on the profile front (same parts and colours as the base E-stop), no Getac and no head light; a 20 x 20 mm aluminium riser frame under each tote |
| `robot_rear_before.png`, `robot_rear_after.png` | Rear: riser frames under both totes, standing on the cover; no tote rails |
| `exploded_assembled_before.png`, `exploded_assembled_after.png` | Exploded view, assembled (chestPlaceholders on): chest E-stop, Getac ZX10 and head light on the profile front |

## Geometry check

`geometry_diff.txt` (inventory from `geometry_dump.js`): every mesh of the robot page scene (render mode,
t = 0) and of a fresh `OAMR_MODEL.build` on exploded.html, compared by path, vertex count, position hash,
world box, colour, roughness, metalness and emissive colour.

- Against main 7ac6543: robot page 194 meshes identical; removed 2 (the illustrative chest E-stop); added 3
  (chest_estop) and 16 (tote riser bars). Exploded build: 138 identical, 7 added (chest_estop 3,
  getac_tablet 2, head_light 2). Nothing else changed.
- Against abb897e (Getac and head light drawn on both pages): robot page 213 identical, the 4 Getac and head
  light meshes removed, nothing added; exploded build 145 identical, nothing changed. The tour videos,
  posters and model/exploded-static.png rendered from abb897e therefore stay.

Robot-frame boxes at bp000 (m): chest E-stop x 0.300 to 0.382, z 0.8615 to 0.9085; Getac x 0.300 to 0.3179,
y -0.1375 to 0.1375, z 0.9185 to 1.1105; head light x 0.300 to 0.320, y -0.079 to 0.079, z 1.1515 to 1.1685
(window y -0.074 to 0.074, z 1.1535 to 1.1665).

## Collision check

Both runs: `node collision_check.js <out.json>` (page served on port 8765), robot.html order run in the
render mode at speed 4 and 24 fps (1536 frames, 255.9 s of simulated time), every 10th frame (154 samples);
bounding boxes of every arm link mesh (base, link1 to link7, two fingers, both arms) against each chest item
drawn in the scene, computed per vertex in the robot frame. Boxes are axis-aligned, so an overlap marks
possible contact, not proven mesh contact. The arms, the pick logic and the items were not changed.
`minGap` in each JSON gives the closest approach per link and item.

### Store scene as rendered (chestPlaceholders off)

`collision_store_scene.json`: chest items in the scene: chest_estop only. 0 overlaps.

### Getac ZX10 and head light at their placeholder positions (input for work package M-09)

`collision_chest_placeholders_m09.json`, run on abb897e, where robot.html drew all three chest items.
The first report (Banner state) used world-axis boxes, which grow while the robot turns; it listed 18 head
light overlaps. With world-axis boxes abb897e gives 124; the robot-frame boxes below remove the turn
inflation.

37 overlaps in 23 of 154 sampled frames: 31 with the Getac ZX10 (right link2 9, right link3 7, left link2 6,
right link5 4, left link5 3, right link6 1, left link7 1), 6 with the head light (right link5 3, right link4
2, right link3 1), none with the chest E-stop.

| Frame | Sim time (s) | Arm | Link | Item | Box overlap x, y, z (m) |
|---|---|---|---|---|---|
| 110 | 18.33 | left | link5 | getac_tablet | 0.0179, 0.0146, 0.0649 |
| 170 | 28.33 | right | link3 | getac_tablet | 0.0179, 0.0637, 0.0264 |
| 170 | 28.33 | right | link5 | getac_tablet | 0.0177, 0.0229, 0.0602 |
| 180 | 30.00 | right | link2 | getac_tablet | 0.0108, 0.033, 0.0799 |
| 180 | 30.00 | right | link3 | getac_tablet | 0.0179, 0.0284, 0.0707 |
| 190 | 31.67 | right | link2 | getac_tablet | 0.0112, 0.033, 0.0786 |
| 190 | 31.67 | right | link3 | getac_tablet | 0.0179, 0.0645, 0.0814 |
| 190 | 31.67 | right | link6 | getac_tablet | 0.0002, 0.0101, 0.0517 |
| 380 | 63.33 | right | link5 | head_light | 0.021, 0.0083, 0.0108 |
| 530 | 88.33 | right | link3 | getac_tablet | 0.01, 0.0558, 0.0233 |
| 530 | 88.33 | right | link5 | getac_tablet | 0.0165, 0.0193, 0.048 |
| 540 | 90.00 | right | link2 | getac_tablet | 0.0108, 0.0329, 0.08 |
| 540 | 90.00 | right | link3 | getac_tablet | 0.0179, 0.0292, 0.0706 |
| 550 | 91.67 | right | link2 | getac_tablet | 0.0113, 0.033, 0.0787 |
| 550 | 91.67 | right | link3 | getac_tablet | 0.0179, 0.0652, 0.0815 |
| 670 | 111.67 | left | link5 | getac_tablet | 0.0179, 0.0445, 0.0428 |
| 690 | 115.00 | left | link5 | getac_tablet | 0.0179, 0.054, 0.0321 |
| 690 | 115.00 | left | link7 | getac_tablet | 0.011, 0.0363, 0.0686 |
| 930 | 155.00 | right | link2 | getac_tablet | 0.0045, 0.033, 0.0796 |
| 1080 | 180.00 | left | link2 | getac_tablet | 0.0073, 0.0329, 0.0855 |
| 1130 | 188.33 | left | link2 | getac_tablet | 0.0112, 0.033, 0.0817 |
| 1140 | 190.00 | left | link2 | getac_tablet | 0.011, 0.033, 0.0805 |
| 1180 | 196.67 | left | link2 | getac_tablet | 0.003, 0.0329, 0.0788 |
| 1190 | 198.33 | left | link2 | getac_tablet | 0.0067, 0.033, 0.0803 |
| 1240 | 206.67 | left | link2 | getac_tablet | 0.0009, 0.033, 0.0816 |
| 1290 | 215.00 | right | link3 | getac_tablet | 0.0076, 0.0626, 0.0532 |
| 1290 | 215.00 | right | link3 | head_light | 0.0076, 0.0041, 0.017 |
| 1290 | 215.00 | right | link4 | head_light | 0.021, 0.0196, 0.017 |
| 1290 | 215.00 | right | link5 | getac_tablet | 0.0009, 0.0893, 0.0552 |
| 1290 | 215.00 | right | link5 | head_light | 0.004, 0.0359, 0.017 |
| 1300 | 216.67 | right | link4 | head_light | 0.021, 0.0152, 0.017 |
| 1300 | 216.67 | right | link5 | getac_tablet | 0.0179, 0.0941, 0.0553 |
| 1300 | 216.67 | right | link5 | head_light | 0.021, 0.0366, 0.017 |
| 1400 | 233.33 | right | link2 | getac_tablet | 0.011, 0.033, 0.0833 |
| 1410 | 235.00 | right | link2 | getac_tablet | 0.0156, 0.033, 0.1096 |
| 1420 | 236.67 | right | link2 | getac_tablet | 0.0116, 0.033, 0.0878 |
| 1460 | 243.33 | right | link2 | getac_tablet | 0.0094, 0.033, 0.0811 |

Other placement findings: the Getac box (275 mm) extends 107.5 mm beyond each side face of the 60 mm
profile, at shoulder height, where the arm links pass. The chest E-stop placeholder stands 82 mm ahead of the
profile face: x 0.382 m at bp000 (inside the 0.39 m chassis front edge) and 0.432 m at bp050 (42 mm ahead of
it). The robot page pick logic keeps its 65 mm "arm profile / chest E-stop" self-collision box, as before.
These are inputs for work package M-09; nothing was moved.
