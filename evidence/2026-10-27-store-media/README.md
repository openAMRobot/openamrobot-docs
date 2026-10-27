# No LED strips, re-rendered tour, store video and pictures: evidence (27 Oct 2026)

Base: `66790f3` (main after #58). Visual and media only. The store video and pictures are simulation
visualizations rendered offline from the robot page; they are not footage of the real robot and not
evidence of its behaviour.

## 1. LED strips and foot light removed

`model/model.js`, robot page fittings: the cyan LED strips on both sides and the rear of the base and the cyan
foot light ring around the lift column base are removed, with the unused `led` material; "status lights" is
removed from the illustration list on robot.html. Kept: the slot cover strips (RAL 5018), the store's chiller
strips, the E-stops, RESET and decals. `check_roadmap.py` fails if model.js defines an `led` material or any
cyan emissive colour on the robot (it fails on main: `led` material, emissive `1692613`).

Geometry check (`geomcheck.js` and `geomtest.html` of evidence/2026-10-26-shared-model, main `66790f3` against
this branch; `geometry_*.json`):

| Page | Meshes before / after / matched | Largest matrix difference | Differing silhouette pixels (front, rear) |
|---|---|---|---|
| exploded.html (registry meshes) | 132 / 132 / 132 | 0 | **0, 0** |
| robot.html (robot root) | 203 / 199 / 199 | 0 | 375, 696 (the removed strips, which stood 1 to 3 mm out) |

The four meshes that disappeared, all robot page fittings (no registry id), `MeshStandardMaterial` colour
`#0c3b38`, emissive `#19d3c5`:

| Mesh | Centre (mm, robot frame) | Size (mm) |
|---|---|---|
| left side LED strip | -20, 292, 272 | 620 x 3 x 8 |
| right side LED strip | -20, -292, 272 | 620 x 3 x 8 |
| rear LED strip | -391, 0, 272 | 3 x 400 x 8 |
| lift column foot light | 60, 0, 307 | 270 x 90 x 6 |

Before and after: `robot_overview_before.png` / `robot_overview_after.png` (Overview preset) and
`robot_base_close_before.png` / `robot_base_close_after.png` (close view of the base), `?look=full`.

## 2. Tour re-rendered (exploded.html)

`scripts/render_tour.js` unchanged (same tour, captions, settings: 30 fps, libx264 veryfast CRF 23, yuv420p,
faststart, no audio). Render mode now forces the full look (`model/look.js` `forced()`: `?render=1` gives
`full` unless `?look=` says otherwise; the frame-time probe never runs in render mode). Two 1080p renders are
byte-identical (sha256 `dee7b44d...`); render times 19 min 55 s and 19 min 52 s (1080p), 21 min 39 s
(1080 x 1350). Posters: frame 780 (26 s, opened base), palette-reduced to 192 colours; `model/exploded-static.png`:
the raw 3D canvas of frame 0 at 960 x 720, 128 colours (`exploded_stills.js`). Duration unchanged (49.5 s), so
the text under the video on exploded.html is unchanged.

## 3. Store video and pictures (robot.html)

**Render mode** (`patch_robot_render.py`, controller `render_mode.js`, inline in robot.html):
`robot.html?render=1&frame=N&w=W&h=H&fps=F&speed=K&cam=C` shows frame N of one "Run order (8 items)" run at
sim time N / F x K. Full look, Frames, Labels and camera tiles off, page UI hidden. Deterministic: a seeded
`Math.random` is installed before any script (the store's GTAO noise texture asks `Math.random`), the realtime
loop (wall-clock playback) does not run, the camera is a function of the sim time. Cameras: `auto` (Follow,
with a cut of 1.3 s of video to the Side view around each of the 8 grasps), the page presets, `front` (low,
from ahead along the aisle), `pick` (across the aisle onto the picking arm), `tote`. Corner caption on video
frames: "OpenAMRobot 2.0, simulation visualization, 7.5x speed" (the speed of the render); on pictures
without the speed. `scripts/render_store.js` drives it (workers, `--resume`, `--hashes`, `--still`,
`--recaption`, `--crf`). The realtime "Record order video" button still records (`page_checks.js`: started,
"Stop recording", stopped, "Video saved (WEBM)").

**Frame time and render length.** 30 frames before the full render: 491 s with one worker and 498 s with two
(16.4 s per frame; SwiftShader already uses all 4 vCPU, so workers do not speed it up). Estimate for 30 fps,
40 s (1200 frames): about 5.5 h, over 4 h; for 24 fps, 40 s (960 frames): about 4.4 h. **The video is 24 fps**
(not 30), and the sim speed is 7.5 so that the whole run (255.9 s of sim time) takes 34.1 s: 819 frames,
estimate 3.7 h. Actual: 117 frames in about 1,850 s, a container restart, then frames 117 to 818 in 9,255 s
(`--resume`); about 3.1 h in total (13.6 s per frame on average). Resolution unchanged (1920 x 1080).

**Determinism.**
- frames 0 to 29, one worker against two workers (before the full render): identical sha256 for all 30
  (`store_frames_0-29_estimate_*.sha256`);
- frames 0 to 59, rendered twice with the final page (one worker, then two workers): identical sha256 for all
  60 (`store_frames_0-59_run*.sha256`);
- the full run (`store_frames_full_run.sha256`) was rendered before the speed was added to the caption. Its
  frames 0 to 59 equal the final-page frames in every pixel outside the caption box (0 differing pixels); the
  encode lays the final caption (opaque box, `window.__captionOverlay`) over every frame (`--recaption 1`, CRF 25
  to stay under 15 MB; the first encode at CRF 23 without it was 15,554,176 bytes).

**Pictures** (`media_job.sh`, sim time and camera): 1 aisle 128 s Follow; 2 pick 15.6 s pick; 3 tote 21.6 s
tote; 4 front 40 s front; 5 store 100 s store; 6 dock 255.9 s Overview; verticals of 2 and 4 at 1080 x 1350.
JPEG quality 90 (each under 1 MB), thumbnails 640 x 360 (512 x 640 vertical) at quality 82, contact sheet
1952 x 1242 JPEG. Poster of the video: frame 420 (sim 131.3 s, Follow) with the final caption, PNG, 192 colours;
on the page the `poster` attribute uses its 640 px JPEG thumbnail so that the first load stays small.

**Page section** (`add_media_section.py`): "Video and pictures" below the 3D view, labelled as simulation
visualization, not real-robot footage; video with `preload="none"`, poster, download links; thumbnail grid
whose images get their `src` from an IntersectionObserver (200 px margin) when the grid comes near the
viewport (`loading="lazy"` alone made Chrome fetch all eight thumbnails at load, +494 KB).

**First load of robot.html** (`first_load.js`, Content-Length of every response until load plus 10 s,
1280 x 800, no scrolling): main 4,093,278 bytes, this branch 4,164,291 bytes: **+71,013 bytes** (budget
100 KB; the section, the render-mode controller and the 59 KB poster thumbnail). After scrolling to the
section all eight thumbnails load.

## Media

| File | Format | Bytes | sha256 |
|---|---|---|---|
| `media/openamrobot-2-store-1080p.mp4` | 1920x1080, 24 fps, 819 frames, 34.125 s | 12,276,656 | `95900207da19058b97551a3525e39425c2cec4263ae79ddf958c0597e740b263` |
| `media/openamrobot-2-store-1080p-poster.png` | 1920x1080 | 506,110 | `32ddf6558509b3fe15118c092c759672ffe1a749dc40678b10b5bba533030ad4` |
| `media/openamrobot-2-tour-1080p.mp4` | 1920x1080, 30 fps, 1486 frames, 49.533 s | 9,247,889 | `dee7b44d521d42f69e60558be3108465f7196fc2d98eae556869afbb1ff0edff` |
| `media/openamrobot-2-tour-1080x1350.mp4` | 1080x1350, 30 fps, 1486 frames, 49.533 s | 8,020,618 | `d2c689d1a5ae3c89d1d15bf4d6a1ccf24ee939f0a75897ddf82735af6060aa3d` |
| `media/openamrobot-2-tour-1080p-poster.png` | 1920x1080 | 175,399 | `7d952bc703d28ff194c59df0a3b0a7e18b82de95aac3c3fea9fa19c0b31573b8` |
| `media/openamrobot-2-tour-1080x1350-poster.png` | 1080x1350 | 139,023 | `e180d0f52e5d96a54ac005fbc3c112a57547bf9564d8cf853abb5cc8542f7ee0` |
| `model/exploded-static.png` | 960x720 | 60,075 | `7eb2b463b3b8f2621b7355c26e3a69631d37311c625e3700731aaa182939d834` |
| `media/store/01_aisle_follow.jpg` | 1920x1080 | 431,495 | `fe45704e97ea0c6dd99e0182079da202867a6c7d85d4c4a02cbaed989f332a8a` |
| `media/store/02_pick_side.jpg` | 1920x1080 | 405,209 | `b6935bbc6f98d453bf5759d65cf45ba1f0590031af8c4552614b6fd21fd7a646` |
| `media/store/02_pick_side_1080x1350.jpg` | 1080x1350 | 316,020 | `08d657f82f9a4f7050ff1ded9d9e3c247690a3c8decd27c9e4488bf494fac4c0` |
| `media/store/03_place_tote.jpg` | 1920x1080 | 336,248 | `99bd134ce294a407d3a585c54de986e6f10b201ecc677cec25d34ce49f2864d9` |
| `media/store/04_front_low.jpg` | 1920x1080 | 411,722 | `7f0c95ec3cd90c7e6b46b329cbe1b5d150a8d1878982b087ada9d74029abfd3b` |
| `media/store/04_front_low_1080x1350.jpg` | 1080x1350 | 246,827 | `f010b75c8663de1443c904cea3d2ff4ff548652fafb81bc3abed1a35023337ba` |
| `media/store/05_store_overview.jpg` | 1920x1080 | 419,544 | `0de94f25b40d339ab95869c1f9e6bde7d1b5c5a9983ce4f6c95d610de9856a10` |
| `media/store/06_dock.jpg` | 1920x1080 | 269,554 | `cb57d040cdaf50e1bca3afbc124fe194e87a501782f492a0c4b18901d1eac386` |
| `media/store/contact_sheet.jpg` | 1952x1242 | 474,628 | `5311fc6ff91d55f4fb65a061ef084cd641e3d99818c8b9be70495c51d76893ed` |

## Page checks

`page_checks.js` (pages served locally, headless Chromium with SwiftShader): robot.html and exploded.html at
375 and 1280 px: no console errors or warnings, no failed requests, scrollWidth equal to the viewport width.
robot.html defaults after a normal load: Follow, Frames off, Labels off, High quality on at 1280 px (narrow
screens start with it off, unchanged). Screenshots of the new section: `robot_1280_media_section.png`,
`robot_375_media_section.png`.

## Commands

```bash
python3 scripts/check_roadmap.py                 # passed (fails on main: led material, cyan emissive)
mkdocs build --strict                            # passed
bash scripts/check_docs.sh                       # passed
python3 linkcheck.py site                        # offline local link check (evidence/2026-10-26-shared-model)
node scripts/render_store.js 1920 1080 --frames 0:30 --frames-dir A --hashes a.sha               # estimate
node scripts/render_store.js 1920 1080 out.mp4 --fps 24 --speed 7.5 --frames-dir F --resume 1 --hashes s.sha
node scripts/render_store.js 1920 1080 store.mp4 --fps 24 --speed 7.5 --frames-dir F --resume 1 --recaption 1 --crf 25
node scripts/render_tour.js 1920 1080 tour.mp4 http://localhost:8802/       # twice, then 1080 1350
node evidence/2026-10-27-store-media/exploded_stills.js http://localhost:8802/ OUT
node evidence/2026-10-27-store-media/page_checks.js http://localhost:8802/ http://localhost:8806/ OUT
node evidence/2026-10-27-store-media/first_load.js http://localhost:8802/ http://localhost:8806/
```

Ports: 8802 this branch, 8806 main `66790f3`.

## Not verified

- Playback of the videos on a real GPU and in browsers other than headless Chromium.
- How the physical robot looks: these are renders of the visualization model.
- lychee itself (the offline link check ran with the Python equivalent; CI runs lychee).
