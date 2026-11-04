# Photos and videos re-rendered from the current model: evidence (4 Nov 2026)

Base: `85c813b` (main after #71 and #65). Visual and media only: no model geometry or data changed (`model.js`,
`placement.json`, `harness_routes.json` untouched; the sync audit stays at 164 parts, 0 mismatches). Every video and
picture is a simulation visualization rendered offline from the roadmap pages; none is footage of the real robot. The
grocery store is a visualization only.

Method: the October method of `evidence/2026-10-27-store-media` (resumable job scripts run with nohup, SwiftShader render
modes of exploded.html and robot.html, determinism checks, JPEG under 1 MB, lazy thumbnails, posters palette-reduced).
Scripts here: `media_job.sh` (store pictures, stills, posters, tour videos), `store_job.sh` (store determinism and full
run), `serve.sh` (server on port 8802 from this clone), `stills.js` and `stills_caption.py` (stills), `pictures.py`
(JPEG, thumbnails, contact sheets, posters), `tour_play.js` (live tour check).

## 1. Tour (exploded.html, model/exploded.json)

Existing keyframes and timing style kept (camera beats with a caption, a short hold with a small orbit drift). Tour
49.5 s to **87.5 s** (2626 frames at 30 fps).

New stops (labels of the parts shown, `names` on):

| Time (s) | Stop | Labels |
|---|---|---|
| 50 to 52.5 | Rear power module, cover off, from the rear left above: F0 at the plate front, K1 / K2 with the busbars, FB-B on its shelf, FB-A at the rear | F0 main fuse, K1 / K2, FB-B, FB-A, G10 power plate, BUS+ / BUS- |
| 54 to 56.5 | Rear power module, right side and rear panel faded: both levels, the BMS in the right side gap, the receiver below with the 15 mm gap | BMS, Receiver (prepared), G10 power plate, FB-B, K1 / K2 |
| 58.5 to 63 | Base harness, cover off: left power corridor, right signal corridor, covered central channels over the drive section, tie points | Central channels, Over-wheel guards, Tie points, Side zone plates, G10 power plate |
| 65 to 69.5 | Front bay side zones: power on the robot's left (FB-C, USB-PD, 3.3 V), signal on its right (USB hub, USB-CAN-FD, LiDAR UART) | the six side-zone parts |
| 71.5 to 77.5 | Lift energy chain at L1000, then the lift moving up to L1350 | Energy chain, DP-LIFT, Lift column |
| 79.5 to 84 | Flag rod guide: open ring at the top of the static column, at L1350 | Flag rod guide, Flag rod, Steel flag, Lift stop sensors |

Captions reviewed against the model and STATE.md and fixed:
- Battery stop: framed the `battery` cell-group envelope (the superseded single row of 8 cells, hidden on both pages) and
  said "eight EVE LF105 cells, 8S1P". Now frames `battery_cells`, `battery_tray`, the series link and PWR-018:
  "4 + 4 EVE LF105 cells (8S LiFePO4) upright in two removable side trays, joined by the keyed connector PWR-018".
  The opened-base labels name the cells and the G10 power plate instead of the envelope.
- Upper body: adds the Getac ZX80 in portrait.
- Lift stop sensors: "on the rear face of the static column".
- Stage 9 text: "the upper-body service loop" becomes "the lift energy chain".
- Checked and unchanged: no caption names a front receiver, a landscape Getac, the E-stop on the static column or a ZED
  at 42 mm.

Page code (exploded.html, tour engine only): keyframes take `lift` (travel above L1000, m; the carriage part groups, the
arms and the energy chain move; a part group inside a lifted part group is lifted once) and `hide` (components faded out,
`@upper` for the lift assembly and the arms), both interpolated between keyframes; the camera framing and the label
anchors follow the lift. The page text under the tour video says 87.5 s. `check_roadmap.py`: tour 40 to 90 s (was 40 to
50), `hide` ids and the `lift` range (0 to 0.35 m) checked. Labels added in exploded.json for the parts shown.

Live playback (`tour_play.js`, `tour_play.json`, normal page load, Playwright clock stepped): Play tour, the caption of
every new stop at its time, Pause holds the tour, the tour ends by itself and restores the view; no console errors or
warnings.

## 2. Videos

| File | Format | Bytes | Encode | Render |
|---|---|---|---|---|
| `openamrobot-2-tour-1080p.mp4` | 1920x1080, 30 fps, 2626 frames, 87.533 s | 13,252,159 | CRF 27 | from the frames of the second render |
| `openamrobot-2-tour-1080x1350.mp4` | 1080x1350, 30 fps, 2626 frames, 87.533 s | VERT_BYTES | CRF 27 | VERT_TIME |
| `openamrobot-2-store-1080p.mp4` | 1920x1080, 24 fps, 819 frames, 34.125 s | 14,089,451 | two-pass, `--target-bytes 14500000` | 275 min, 2 workers |

**Tour determinism.** The 1080p tour was rendered twice at CRF 23: once piped (155 min 37 s), once with its PNG frames
kept (114 min 49 s): **byte-identical**, sha256 `4b6598ea7cdb9a0da641e6844329e658e5a1bad5bb3e608cd8a422caf80bc36a`
(`tour_1080p_determinism.sha256`). At CRF 23 the 87.5 s tour is 24,066,049 bytes, over the 15 MB limit of
check_roadmap.py, so the published file is encoded from the kept frames of the second render at CRF 27. For this,
`scripts/render_tour.js` gained `--crf`, `--frames-dir` and `--resume` (as in render_store.js; the default is unchanged).

**Store run.** `render_store.js 1920 1080 ... --fps 24 --speed 7.5 --workers 2 --resume 1` (the October settings).
Determinism: frames 0 to 59 with one worker (16 min 54 s) and with two workers (22 min 20 s): identical sha256 for all
60 (`store_frames_0-59_1worker.sha256`, `store_frames_0-59_2workers.sha256`). The full run reused the one-worker frames
0 to 59 and rendered 60 to 818 with two workers (`store_frames_full_run.sha256`). The CRF 23 encode was 15,719,427
bytes, 9 KB under the limit; the published file is the two-pass encode at 14,500,000 target bytes from the same frames.
The robot page said "64.0 s ... 4x speed" (the PR #62 render); with the October settings it now says "34.1 s ... 7.5x
speed (255.9 s of simulated time in 34.1 s of video)". The corner caption of every frame reads "OpenAMRobot 2.0,
simulation visualization, 7.5x speed".

Posters: tour frame 780 (26 s, opened base) with labels and caption, 192 colours; `model/exploded-static.png` frame 0
raw canvas at 960 x 720, 128 colours; store frame 420 (sim 131.3 s, Follow), 192 colours, and its 640 px JPEG thumbnail
`store/thumbs/store_video_poster.jpg` used by the page.

Render times are with the store run and the tour sharing the 4 vCPU (SwiftShader).

## 3. Store pictures (media/store/)

Same sim times and cameras as October: 1 aisle 128 s Follow; 2 pick 15.6 s pick; 3 tote 21.6 s tote; 4 front 40 s
front; 5 store 100 s store; 6 dock 255.9 s Overview; verticals of 2 and 4 at 1080 x 1350. JPEG quality 90 (all under
1 MB, 244 to 439 KB), thumbnails 640 x 360 (512 x 640 vertical) at quality 82, `contact_sheet.jpg` 1952 x 1242.

## 4. High-resolution stills (media/stills/, not linked from the pages)

Ten stills at 2560 x 1440, JPEG quality 90 (94 to 621 KB, all under 1 MB), full look, grid lines hidden, no labels or
markers, caption line "OpenAMRobot 2.0, roadmap model, simulation visualization" burned in at the bottom
(`stills.js`, `stills_caption.py`; list in `media/stills/README.md`). Stills 1 to 8 from exploded.html render mode
(`window.__renderKey`, with `lift` and `hide`), 9 and 10 from robot.html render mode with the corner caption off.

## Contact sheets

- `contact_store_pictures.jpg`: the eight store pictures
- `contact_stills.jpg`: the ten stills
- `contact_tour_1080p.jpg`, `contact_tour_1080x1350.jpg`, `contact_store_1080p.jpg`: one frame every 10 s

## Checks

```bash
python3 scripts/check_roadmap.py          # passed (media sizes, first-load budget, store media section)
python3 -m pytest -q scripts/tests        # 72 passed
bash scripts/check_docs.sh                # passed, 0 warnings
mkdocs build --strict                     # passed locally (venv with requirements.txt)
node scripts/audit_sync.js http://localhost:8802/   # 164 parts, 0 mismatches
node evidence/2026-11-04-media/tour_play.js http://localhost:8802/
```

## Not verified

- Playback of the videos on a real GPU and in browsers other than headless Chromium.
- How the physical robot looks: these are renders of the visualization model.
