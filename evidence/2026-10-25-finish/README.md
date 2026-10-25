# Finish colours on the shared roadmap model: evidence (25 Oct 2026)

Evidence for `docs/assets/roadmap/model/finish.json`, the finish step in `model/model.js`, the two
slot cover strips, the caption timing of the guided tour and the re-rendered tour videos.
Visualization only; not mechanical, electrical or safety evidence.

## What changed

- `model/finish.json` (new): colours keyed by the existing part ids, with the RAL reference and a
  standard sRGB approximation, and two finishes (matte: roughness 0.85, metalness 0.05; satin:
  roughness 0.42, metalness 0.35).
- `model/model.js`: reads `finish.json` at load and applies it to the GLB nodes and upper-body
  primitives it names; adds the slot cover strips inside the arm-profile group; one new registry
  entry (`slot_cover_strips`, primitive). Parts that `finish.json` does not name keep their colours.
- `model/exploded.json`: `slot_cover_strips` in stage 8 with a zero offset (it moves with the profile).
- `exploded.html`: the tour caption changes only when the camera reaches its keyframe (three lines in
  `tourAt`). Geometry, camera presets, labels and stages are unchanged.
- `robot.html`: unchanged.
- Re-rendered: both tour videos, both posters and the no-WebGL image `model/exploded-static.png`.

| Parts | RAL | sRGB | Finish |
|---|---|---|---|
| side, front and rear panels | RAL 7035 | `#CBD0CC` | matte |
| cover and flanges; corner supports, centre bracket, LiDAR support, electronics bracket | RAL 7016 | `#383E42` | matte |
| camera, ToF and ultrasonic mounts | RAL 9005 | `#0A0A0A` | matte |
| arm profile | RAL 7016 | `#383E42` | satin |
| adapter plate, lift base plate | RAL 9005 | `#0A0A0A` | satin |
| slot cover strips | RAL 5018 | `#3F888F` | matte |

The internal parts in the graphite row are those that show under the cover edge in the assembled
view: an ID render (each part a flat colour, front and rear three-quarter cameras, 1280 x 960)
counted visible pixels for the four supports (8 to 275 px each), the centre bracket (1,322 and
1,800 px), the LiDAR support (324 px) and the electronics bracket (51 and 30 px). The base plate,
controller plate, motor driver mount and LiDAR spacer are not named in finish.json and stay as they
were, as do the lift column, OpenArm 2.0 meshes, hub motors, castors, sensors, compute, head camera
and its bracket, battery envelope (still translucent and provisional), E-stop and RESET.

## Slot cover strips

Two primitives, 8.5 x 2.6 x 85 mm, in the front-most slot of each side face of the arm profile
(the model draws two slots per side face, 30 mm either side of the profile centre). They sit
**above** the arm mounts, from 247.5 to 332.5 mm above the column top, not below them: the robot
page draws the chest E-stop on the front face of the profile, from 16 to 86 mm above the column top,
so any strip below the arm mounts would be about 30 mm from it. Minimum distances (box to box, robot
frame, lift 0, bp000):

| Object drawn by robot.html | Distance to the nearest strip |
|---|---|
| chest E-stop yellow bezel | 163.5 mm |
| chest E-stop red mushroom | 188.2 mm |
| base E-stop bezel, front panel | 813.8 mm |
| RESET button, rear deck | 984.1 mm |

The lift moves the profile and the chest E-stop together, so these distances hold at every lift
height. Nothing orange was added.

## Geometry unchanged (pixel and mesh check)

A test page (not committed) builds the shared model exactly as `exploded.html` does, with
`model.js` from before and after this change:

- meshes: 130 before, 132 after; every one of the 130 has the same position-array hash and the same
  world matrix; the two added meshes are the strips (`slot_cover_strips`, `#3f888f`).
- 24 parts changed colour, roughness and metalness only; opacity and transparency are unchanged on
  every existing mesh (the battery envelope keeps its 35 % shell).
- silhouettes (every mesh flat white on black, front and rear three-quarter, 1280 x 960):
  208,799 and 193,630 lit pixels; **0 pixels differ** between before and after in both views
  (`mask_front_*.png`, `mask_rear_*.png`; the diff images are black). The strips lie on the
  profile face and do not change its outline.

## Screenshots (same camera pose before and after)

All from the built site (`mkdocs build --strict`), served locally, headless Chromium with SwiftShader.
Exploded-view images come from the page's deterministic render mode (`exploded.html?render=1`,
frame 0 assembled, frame 780 = 26 s opened base).

| Before | After |
|---|---|
| `exploded_1280_assembled_before.png` | `exploded_1280_assembled_after.png` |
| `exploded_1280_open_base_before.png` | `exploded_1280_open_base_after.png` |
| `robot_1280_overview_before.png` | `robot_1280_overview_after.png` |
| `robot_1280_side_before.png` (Side preset) | `robot_1280_side_after.png` |
| | `robot_375_after.png`, `exploded_375_after.png`, `exploded_1280_page_after.png` |

Browser console at 375 and 1280 px, robot and exploded pages, before and after: no errors and no
warnings, no failed requests, no horizontal scroll (scrollWidth equal to the viewport width).

`tour_caption_12.9s_before_12.9s_after_13.0s_after.png`: at 12.9 s, while the camera still moves to
the cutaway beat, the old page already showed the cutaway caption (top); the new page still shows
the previous caption (middle) and shows the cutaway caption from 13.0 s, when the camera has arrived
(bottom).

## Videos

Rendered with the existing `node scripts/render_tour.js` (unchanged; same settings: frame by frame at
30 fps from `exploded.html?render=1`, `-c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p
-movflags +faststart -an`), the roadmap folder served with `python3 -m http.server 8765`. Posters
are the frame at 26 s (opened base) from the same render mode, palette-reduced PNG (192 colours);
`model/exploded-static.png` is the raw 3D canvas of frame 0 at 960 x 720, palette-reduced (128 colours).

| File | Size | Duration | Video | sha256 |
|---|---|---|---|---|
| `openamrobot-2-tour-1080p.mp4` | 9,309,909 bytes | 49.533 s | h264 1920x1080, 30 fps, yuv420p, 1486 frames, 1 stream (no audio) | `26fda64c1ee14a0537208ef080aaeb4a1780b6d1af2edda0ffce1fc16339eb0c` |
| `openamrobot-2-tour-1080x1350.mp4` | 8,101,971 bytes | 49.533 s | h264 1080x1350, 30 fps, yuv420p, 1486 frames, 1 stream (no audio) | `b716cfdedd47d3af97847ba36a400bc78ecddc088a485d91e86cd5e6f049b200` |
| `openamrobot-2-tour-1080p-poster.png` | 135,558 bytes | - | PNG poster | `4db2b01e290ffca585eaa8b411b3a70f785cd567f9bd57002ac4a16554e78cb9` |
| `openamrobot-2-tour-1080x1350-poster.png` | 109,674 bytes | - | PNG poster | `99b78e46122d98b22ad11a426ed8ea2db30cac1984e137dc672a70a343c1d0a6` |

Two 1080p renders from the same page are byte-identical (both sha256 `26fda64c...39eb0c`). Render
times with SwiftShader: 746 s and 448 s (1080p), 413 s (1080x1350). Both videos are under 15 MB.
