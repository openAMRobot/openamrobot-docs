# Chest equipment placeholders, tote riser, re-rendered media: evidence (28 Oct 2026)

Simulation visualization only; not mechanical, electrical or safety evidence. Chest positions are
placeholders until work package M-09 (P-03 rev20.0 item 24). The riser is an illustration, not a BOM part.

## Sources

- P-03 Decision Addendum rev20.0 item 24 (27 Oct 2026): chest layout on the moving part, bottom up:
  chest E-stop, Getac ZX10, head light; the chest E-stop is the same Schneider XB4BS8445 with ZBE-102 as the
  base button and replaces the OpenArm kit button.
- BOM Issue 7.14 (27 Oct 2026): SAF-001 quantity 2 (base front and chest), ARM-008 withdrawn, UI-001 Getac
  ZX10 (exact generation and SKU pending), AUX-001 Banner WLS28-2CW285DXPWMQ.
- Banner publication 179493 Rev H (15 Sep 2025), sha256
  `37152c1fecbfdd39e2c05c5b48b6ad68d4b0e53dab247602771dab138ba2ccba` (the value in the project datasheet
  index): IP50 285 mm model, housing L2 346 mm, lighted length L3 286 mm, section 28 x 21 mm, clear anodised
  aluminium housing, polycarbonate window (D = diffused).
- Getac ZX10: no datasheet in the project datasheet index, and the manufacturer host is not reachable from
  this environment. The tablet is listed in the registry and not drawn; no dimension is used.

## Stills (section 3)

`node scripts/render_store.js 1280 720 --still 0 --cam front|rear --out <file>` on robot.html, and frame 0
of the exploded.html render mode (assembled, front three-quarter). Before: main at 7ac6543. After: this
branch. Palette-reduced PNG.

| File | Content |
|---|---|
| `robot_front_before.png`, `robot_front_after.png` | Before: illustrative chest E-stop (yellow box, red head) on the profile front, totes without support. After: the chest E-stop placeholder (same parts and colours as the base E-stop), the head light bar across the top of the profile, a 20 x 20 mm aluminium riser frame under each tote |
| `robot_rear_before.png`, `robot_rear_after.png` | Rear: riser frames under both totes, standing on the cover; no tote rails |
| `exploded_assembled_before.png`, `exploded_assembled_after.png` | Exploded view, assembled: chest E-stop low and head light high on the profile front |

## Geometry check

`geometry_diff.txt`: every mesh of the robot page scene (render mode, t = 0) and of a fresh
`OAMR_MODEL.build` on exploded.html, compared by path, vertex count, position hash, world box, colour,
roughness, metalness and emissive colour. Robot page: 194 meshes identical; removed 2 (the illustrative chest
E-stop); added 3 (chest_estop), 2 (head_light) and 16 (tote riser bars). Exploded build: 138 identical, 5
added (chest_estop, head_light). Nothing else changed.

## Collision check

`collision.json`: robot.html order run in the render mode at speed 4 and 24 fps (1536 frames, 255.9 s of
simulated time), every 10th frame (154 samples); world bounding boxes (per vertex) of every arm link mesh
(base, link1 to link7, two fingers, both arms) against the chest E-stop and the head light. Boxes are
axis-aligned, so an overlap marks possible contact, not proven mesh contact. The arms, the pick logic and the
items were not changed.

18 overlaps, all with the head light, none with the chest E-stop:

| Frame | Sim time (s) | Arm | Link | Item | Box overlap x, y, z (m) |
|---|---|---|---|---|---|
| 110 | 18.33 | left | link4 | head_light | 0.022, 0.0311, 0.028 |
| 110 | 18.33 | left | link5 | head_light | 0.022, 0.0501, 0.0272 |
| 360 | 60.00 | right | link5 | head_light | 0.022, 0.0719, 0.0208 |
| 360 | 60.00 | right | link6 | head_light | 0.0093, 0.0735, 0.0078 |
| 360 | 60.00 | right | link7 | head_light | 0.022, 0.0541, 0.0266 |
| 380 | 63.33 | right | link5 | head_light | 0.022, 0.0738, 0.0163 |
| 380 | 63.33 | right | link7 | head_light | 0.022, 0.0839, 0.0097 |
| 670 | 111.67 | left | link5 | head_light | 0.022, 0.08, 0.028 |
| 680 | 113.33 | left | link4 | head_light | 0.0054, 0.0602, 0.028 |
| 680 | 113.33 | left | link5 | head_light | 0.022, 0.0038, 0.0254 |
| 690 | 115.00 | left | link5 | head_light | 0.022, 0.0728, 0.028 |
| 1070 | 178.33 | left | link3 | head_light | 0.022, 0.0008, 0.028 |
| 1080 | 180.00 | left | link3 | head_light | 0.022, 0.0197, 0.027 |
| 1290 | 215.00 | right | link3 | head_light | 0.0076, 0.0981, 0.028 |
| 1290 | 215.00 | right | link4 | head_light | 0.022, 0.1025, 0.028 |
| 1290 | 215.00 | right | link5 | head_light | 0.005, 0.0893, 0.0258 |
| 1300 | 216.67 | right | link4 | head_light | 0.022, 0.1068, 0.028 |
| 1300 | 216.67 | right | link5 | head_light | 0.022, 0.0941, 0.0267 |

Other placement findings: the head light housing (346 mm, placeholder orientation across the profile front)
extends 143 mm beyond each side face of the 60 mm profile, into the arms' working space near the shoulders.
The chest E-stop placeholder stands 82 mm ahead of the profile face: x 0.382 m at bp000 (inside the 0.39 m
chassis front edge) and 0.432 m at bp050 (42 mm ahead of it). The robot page pick logic keeps its
65 mm "arm profile / chest E-stop" self-collision box, as before.
