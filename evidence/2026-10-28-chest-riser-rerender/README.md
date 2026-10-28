# Second E-stop, chest placeholders, head camera hp30, tote riser, re-rendered media: evidence (28 Oct 2026)

Simulation visualization only; not mechanical, electrical or safety evidence. The second E-stop, tablet and head
light positions are placeholders until work package M-09 (P-03 rev20.0 item 24). The riser is an illustration,
not a BOM part. The E-stops are drawn geometry only; no safety logic is touched.

## Sources

P-03 Decision Addendum rev20.0, read through the Google Drive connector on 28 Oct 2026 (last modified 19:32 UTC):

- 28 Oct 2026 corrections and layout update (head of the document): "tablet is the Getac ZX80 instead of the
  ZX10, same landscape orientation"; "the second E-stop moves from the moving chest to the rear face of the
  static DOLD lift profile, close to its upper edge; the Getac moves 50 mm up; the head light moves under the
  Getac, its top edge 30 mm below the Getac bottom edge; positions are placeholders until M-09"; "Head camera
  (items 15, 17 and 18): lens moved 20 mm forward, now 42 mm ahead of the shoulder, and baseline pitch 30
  degrees down (hp30, was hp25)".
- Item 15: "Head-camera pitch is 15 to 35 degrees down in 5 degree steps, baseline 30 degrees (raised from 25
  degrees ..., 28 Oct 2026 ...)". Item 17: "head_pitch (hp15 to hp35, baseline hp30 since 28 Oct 2026, was
  hp25)". Item 18: "lens 42 mm ahead of (moved 20 mm forward ...; was 22 mm) and 223 mm above the shoulder".
- Item 24: "Second E-stop (formerly the chest E-stop): on the rear face of the static DOLD lift profile, close to
  its upper edge, so it stays at the same height whatever the lift position"; "Chest layout on the moving part,
  from bottom up: head light 30 mm below the Getac bottom edge, then the Getac 50 mm higher than the earlier
  placeholder"; Getac ZX80 "234 mm wide x 149.8 mm tall x 17.6 mm, 590 g ..., mounted landscape like the ZX10 it
  replaces"; head light Falcon Illumination FLDL-i150x15-W, housing 158 x 17 x 20 mm, lit area 148 x 13 mm.
- Pending with their owners (not changed here): BOM Issue 7.14 UI-001 and UI-002 still name the previous tablet;
  the register CONFIG-IDS entry still gives hp25 as the head_pitch baseline; the platform-sw URDF evidence row on
  progress.html still records hp25; the BOM extract pages (hardware.html, BOM 7 architecture page) mirror the BOM
  and keep the BOM text for the head camera and tablet; the mass-and-stability page records the geometry the
  stability analysis used (lens 22 mm).
- The Falcon technical data page (Baumer product page 24090) is not reachable from this environment; the head
  light dimensions are the ones P-03 quotes.

## Drawn placeholders

- Second E-stop (`second_estop`, base E-stop parts and colours from the GLB node estop): on the rear face of the
  static DOLD profile, facing rearward, centre 40 mm below the static profile top (16.5 mm from the button top
  to the upper edge); built in the static lift group, so it stays at the same height at every lift position.
- Moving chest, front face of the arm profile, bottom up: head light 158 x 17 x 20 mm aluminium bar with a
  148 x 13 mm diffuse window, no glow and no light source; its top edge 30 mm below the Getac bottom edge; Getac
  ZX80 box 234 x 149.8 x 17.6 mm, landscape, dark grey housing with a 1 mm black screen face forward, 50 mm
  higher than the earlier placeholder; dock not drawn.
- Head camera: lens 42 mm ahead of and 223 mm above the shoulder (bracket moved with it, still on the profile
  top); pitch 30 degrees down by default on both pages (`headPitch: 30`; robot.html state, slider, readout and
  configuration table hp30). The pitch options hp15 to hp35 stay. Before this change robot.html built the model
  with `headPitch: 0` and never applied its hp25 state at load, so the store scene drew the camera level while
  the page said hp25; it now draws hp30.

Shared build option `chestPlaceholders` (`OAMR_MODEL.build(THREE, {chestPlaceholders: false})`, default true):
off draws the second E-stop only. The exploded view builds with it on (all three items, Placeholder badges). The
robot page store scene builds with it off: the arms pass through the tablet and head light placeholder positions
(collision check below), so they are not shown there until work package M-09 sets their positions; the page says
so. No geometry was deleted.

## Stills

`node scripts/render_store.js 1280 720 --still 0 --cam front|rear --out <file>` on robot.html, and frame 0 of the
exploded.html render mode (the one `scripts/render_tour.js` uses). Before: main at 7ac6543. After: this branch.
Palette-reduced PNG.

| File | Content |
|---|---|
| `robot_front_before.png`, `robot_front_after.png` | Before: illustrative chest E-stop on the profile front, totes without support. After (chestPlaceholders off): no E-stop, tablet or head light on the profile front; head camera at hp30, 20 mm further forward; a 20 x 20 mm aluminium riser frame under each tote |
| `robot_rear_before.png`, `robot_rear_after.png` | After: the second E-stop on the rear face of the static lift profile near its upper edge; riser frames under both totes; no tote rails |
| `exploded_assembled_before.png`, `exploded_assembled_after.png` | Exploded view, assembled (chestPlaceholders on): head light under the landscape Getac ZX80 on the profile front, head camera at hp30; the second E-stop is on the far side of the column in this view |
| `store_t65_second_estop_overlap.png` | Store run at t = 65 s, rear camera: the right gripper carries a bottle over the column rear into the right tote, past the second E-stop (the one store-scene overlap below) |

## Geometry check

`geometry_diff.txt` (inventory from `geometry_dump.js`): every mesh of the robot page scene (render mode, t = 0)
and of a fresh `OAMR_MODEL.build` on exploded.html, compared by path, vertex count, position hash, world box,
colour, roughness, metalness and emissive colour.

- Against main 7ac6543: robot page 188 identical, 8 removed, 25 added; exploded build 133 identical, 5 removed,
  12 added. The changes are the second E-stop (replaces the illustrative chest E-stop), the head camera body,
  lenses and bracket and the head_camera_link marker (lens 42 mm, hp30), the tablet and head light (exploded
  view only) and the 16 tote riser bars (robot page only). Nothing else changed.
- Against e3dc4a8: robot page 204 identical, 9 replaced (second E-stop, head camera, bracket, frame marker);
  exploded build 133 identical, 12 replaced (the same plus tablet and head light).

Robot-frame boxes at bp000, L1000 (m): second E-stop x -0.142 to -0.060, y -0.020 to 0.020, z 0.7525 to 0.7995
(static profile rear face at x -0.060, top at z 0.816); head light x 0.300 to 0.321, y -0.079 to 0.079, z 0.9581
to 0.9751; Getac ZX80 x 0.300 to 0.3176, y -0.117 to 0.117, z 1.0051 to 1.1549; head camera x 0.2516 to 0.2898,
z 1.2097 to 1.2493; bracket x 0.237 to 0.267.

## Collision check

`node collision_check.js <out.json> [page]` (page served on port 8765; default robot.html): robot.html order run
in the render mode at speed 4 and 24 fps (1536 frames, 255.9 s of simulated time), every 10th frame (154
samples); bounding boxes of every arm link mesh (base, link1 to link7, two fingers, both arms) against the second
E-stop and each chest item drawn in the scene, computed per vertex in the robot frame. Boxes are axis-aligned,
so an overlap marks possible contact, not proven mesh contact. The arms, the pick logic and the items were not
changed; nothing was moved. `minGap` in each JSON gives the closest approach per link and item.

### Store scene as rendered (chestPlaceholders off)

`collision_store_scene.json`: items in the scene: second_estop only. 1 overlap, kept and
reported as an input for M-09 (the store video shows the gripper passing it at about 16 s of video, 65 s of
simulated time):

| Frame | Sim time (s) | Arm | Link | Item | Box overlap x, y, z (m) |
|---|---|---|---|---|---|
| 390 | 65.00 | right | finger2 | second_estop | 0.0114, 0.04, 0.0307 |

Closest other approaches to the second E-stop: right finger1 18.6 mm and right link7 21.3 mm, both at t = 65 s.

### Getac ZX80, head light and second E-stop at their placeholder positions (input for work package M-09)

`collision_chest_placeholders_m09.json`: the same run on a temporary copy of robot.html with the option on (all
three items drawn; the copy was deleted after the run). 26 overlaps in 20 of 154 sampled
frames: 23 with the Getac ZX80 (right link2 7, left link2 6, right link5 3, left link5 2, right link4 2, left link4 1, left link7 1, right link3 1), 2 with the head light
(right link3 2), 1 with the second E-stop (right finger2 1).

| Frame | Sim time (s) | Arm | Link | Item | Box overlap x, y, z (m) |
|---|---|---|---|---|---|
| 190 | 31.67 | right | link2 | getac_tablet | 0.0112, 0.0125, 0.0026 |
| 190 | 31.67 | right | link3 | head_light | 0.021, 0.006, 0.017 |
| 360 | 60.00 | right | link5 | getac_tablet | 0.0176, 0.0159, 0.0017 |
| 390 | 65.00 | right | finger2 | second_estop | 0.0114, 0.04, 0.0307 |
| 550 | 91.67 | right | link2 | getac_tablet | 0.0113, 0.0125, 0.0027 |
| 550 | 91.67 | right | link3 | head_light | 0.021, 0.0067, 0.017 |
| 670 | 111.67 | left | link5 | getac_tablet | 0.0176, 0.024, 0.0872 |
| 680 | 113.33 | left | link4 | getac_tablet | 0.0054, 0.0042, 0.0269 |
| 690 | 115.00 | left | link5 | getac_tablet | 0.0176, 0.0335, 0.0765 |
| 690 | 115.00 | left | link7 | getac_tablet | 0.0107, 0.0158, 0.0801 |
| 930 | 155.00 | right | link2 | getac_tablet | 0.0045, 0.0125, 0.0073 |
| 1080 | 180.00 | left | link2 | getac_tablet | 0.0073, 0.0124, 0.0696 |
| 1130 | 188.33 | left | link2 | getac_tablet | 0.0112, 0.0125, 0.0107 |
| 1140 | 190.00 | left | link2 | getac_tablet | 0.011, 0.0125, 0.0073 |
| 1180 | 196.67 | left | link2 | getac_tablet | 0.003, 0.0124, 0.0626 |
| 1190 | 198.33 | left | link2 | getac_tablet | 0.0067, 0.0125, 0.0618 |
| 1240 | 206.67 | left | link2 | getac_tablet | 0.0009, 0.0125, 0.0572 |
| 1290 | 215.00 | right | link3 | getac_tablet | 0.0076, 0.0421, 0.0976 |
| 1290 | 215.00 | right | link4 | getac_tablet | 0.0176, 0.0576, 0.029 |
| 1290 | 215.00 | right | link5 | getac_tablet | 0.0006, 0.0739, 0.0996 |
| 1300 | 216.67 | right | link4 | getac_tablet | 0.0176, 0.0532, 0.027 |
| 1300 | 216.67 | right | link5 | getac_tablet | 0.0176, 0.0746, 0.0997 |
| 1400 | 233.33 | right | link2 | getac_tablet | 0.011, 0.0125, 0.0286 |
| 1410 | 235.00 | right | link2 | getac_tablet | 0.0156, 0.0125, 0.0475 |
| 1420 | 236.67 | right | link2 | getac_tablet | 0.0116, 0.0125, 0.0325 |
| 1460 | 243.33 | right | link2 | getac_tablet | 0.0094, 0.0125, 0.0095 |

Other placement findings: the ZX80 box (234 mm across) extends 87 mm beyond each side face of the 60 mm profile,
the head light (158 mm) 49 mm; both sit where the upper arm links pass. The second E-stop stands 82 mm behind the
static profile rear face (x -0.142 m at bp000, -0.092 m at bp050), in the path the right gripper takes to the
right tote. The robot page pick logic keeps its 65 mm "arm profile / chest E-stop" self-collision box in front of
the profile, as before (pick logic unchanged); nothing occupies it now in the store scene.
