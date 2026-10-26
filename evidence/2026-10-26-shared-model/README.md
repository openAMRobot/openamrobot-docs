# One shared robot model and physically based materials, step 1: evidence (26 Oct 2026)

Updated after review: colour calibration, light-look fallback, preview pictures (sections below). The
screenshots marked after and the geometry check were rerun after the calibration (full look).

Evidence for the shared robot model of `docs/assets/roadmap/robot.html` (dark-store page) and
`docs/assets/roadmap/exploded.html`: one three.js, one robot builder, one material system, one look.
Visualization only; not mechanical, electrical or safety evidence. Base: `5981e3b` (main after #56).

## Audit: what was defined twice before this change

| Item | robot.html (#56) | exploded.html (#56) | Now |
|---|---|---|---|
| three.js core | inline esbuild bundle of three.js r160 (core 663 KB of the 1,065 KB inline script) | `model/three-r160.min.js` | `model/three-r160.min.js` on both pages |
| three.js addons | the same inline bundle: OrbitControls, RoomEnvironment, EffectComposer, RenderPass, GTAOPass, OutputPass, RectAreaLightUniformsLib, BufferGeometryUtils, RoundedBoxGeometry | OrbitControls, RoundedBoxGeometry (in the core file) | core file: OrbitControls, RoundedBoxGeometry, RoomEnvironment; `model/three-r160-store.min.js` (robot page only): the store post-processing, area-light tables and mergeGeometries, built against the core file, no copy of the core |
| robot assembly (base, lift groups, head pivot, upper body, arms) | `buildChassis`, `buildColumn`, `buildArms` in the page, calling `OAMR_MODEL.base`, `upperBody`, `armGeometries` | its own assembly in `init3d`, calling `MODEL.base`, `upperBody`, `arm` | `OAMR_MODEL.build` in `model/model.js`, one call per page |
| OpenArm link meshes | built in the page (`buildArms`: mesh per link, URDF visual origin) | built by `MODEL.arm` (same meshes, other code) | `OAMR_MODEL.armRig` and `poseArm`; the robot page keeps its kinematics and sets the link matrices |
| robot geometry only in the page | `buildChassis`: base-plate hole marks, base E-stop, RESET button, belly skirt, LED strips, side and rear decals; `buildColumn`: column screw heads, column label, foot light, chest E-stop, lift cable; `buildArms`: wrist camera bodies | none | moved unchanged into `model/model.js` (robot page fittings, `build(..., {fittings: true})`); not in the component registry, so not in the exploded view |
| robot materials | `OAMR_MODEL.materials` plus four inline materials (RESET light, decal, column label, the arm highlight swap) | `MODEL.materials` | `model/model.js` only: material classes from `model/finish.json`; five unused legacy materials removed (body, cover, glossBlack, tyre, orange) |
| renderer look | ACES, exposure 1.05, sRGB, PCF soft shadows, RoomEnvironment through PMREM, in the page | ACES, exposure 1.25, sRGB, no shadows, no environment, in the page | `model/look.js`: `apply` (ACES, sRGB, PCF soft shadows, exposure per page), `environment` (RoomEnvironment through PMREM), `keyLight`, `shadowCatcher`, `contactShadow` |
| store (shelves, products, totes and tote rails, floor, store lights, GTAO, camera tiles, frames) | page | none | page (unchanged) |

Out of scope and unchanged: `tools/dark-store-sim/` builds the separate simulation page
(`docs/assets/simulation/`) with its own robot geometry; it does not use `model/`.

## How robot.html was migrated

`split_robot_bundle.py` (run once on the #56 page; `freevars.cjs` lists the names a script leaves
unresolved) keeps the page application of the inline bundle, drops the three.js core and addons, binds
the 46 three.js names the application uses to `window.THREE`, and replaces the robot construction,
materials and look with `OAMR_MODEL.build` and `OAMR_LOOK`. Each replacement must match exactly once.
`robot.html` keeps the page's own head pitch at load (0 degrees, as on #56; see Next steps).

The two three.js files are rebuilt reproducibly: `three-r160.entry.js` of #56 rebuilt with esbuild 0.28.2
and npm three@0.160.0 gives a file byte-identical to the #56 `three-r160.min.js` (sha256 `6e76633e...`);
the new entry adds RoomEnvironment. The store addon file is built from `three-r160-store.entry.js` with
`three` resolved to `window.THREE`; it contains none of `__THREE__`, `isWebGLRenderer`,
`THREE.WebGLRenderer:` (checked by `scripts/check_roadmap.py`).

## Materials (model/finish.json, schema oamr-finish/2)

Colours of #56 are unchanged. Each part has a material class; textures are generated in `model.js`
at load from a fixed seed (DataTexture, linear, tileable, at most 256 x 256); nothing is downloaded.

| Class | Parts | Values |
|---|---|---|
| powder_coated_steel | panels (RAL 7035), cover, flanges, supports, centre bracket, LiDAR support, electronics bracket (RAL 7016), base plate (GLB colour) | dielectric, roughness 0.6, orange-peel normal map (scale 0.12, 30 mm tile) |
| anodised_aluminium | arm profile, adapter plate, lift base plate, lift column, head camera bracket, tote rails on the robot page | metalness 0.9, mean roughness 0.35, brushed roughness map along the part length (50 mm tile) |
| printed_petg | camera, ToF and ultrasonic mounts | roughness 0.6, layer-line normal map (0.3 mm pitch) |
| rubber | hub motor wheels, castor wheels (primitive 1) | `#161616`, roughness 0.9 (the only colour change: the wheels were `#1f1f21` and `#d9d9d1`) |
| sensor_glass | LiDAR window band (primitive 2), Gemini front glass and lenses (primitives 1, 2), ZED Mini lenses | roughness 0.05, clearcoat 1, no transmission |
| pcb | compute boards, base controller board, IMU board (green of the GLB) | roughness 0.4 |
| heatsink | compute heatsink (primitive 3) | roughness 0.45, metalness 0.85 |
| openarm_as_delivered | OpenArm 2.0 meshes | vertex colours, values unchanged (the upstream description gives no per-part values) |
| battery_provisional | battery cell-group envelope | unchanged (translucent provisional look) |

Textured classes need texture coordinates: `OAMR_MODEL.prepare` sets a planar `uv` attribute on those
meshes (22 meshes, projected on the dominant normal axis). Positions, normals and indices are unchanged.
Per-mesh before and after values: `materials_exploded.json`, `materials_robot.json`.

## Geometry unchanged (mesh and silhouette check)

`geomcheck.js`: every mesh of the robot (exploded.html: the model built as the page builds it, test page
`geomtest.html`; robot.html: `window.__sim.robot.g` in the page, store excluded), matched by
position-array hash, vertex count, index hash and world matrix; then every mesh flat white on black,
front and rear three-quarter, 1280 x 960.

| Page | Meshes before | Meshes after | Matched | Largest world-matrix difference | Opacity or visibility changed | Silhouette pixels (front, rear) | Differing pixels |
|---|---|---|---|---|---|---|---|
| exploded.html | 132 | 132 | 132 | 0 | 0 | 126,726, 129,512 | **0**, **0** |
| robot.html | 203 | 203 | 203 | 0 | 0 | 149,425, 162,490 | **0**, **0** |

Masks: `mask_exploded_*`, `mask_robot_*`; the `_diff` images are black.

## Screenshots (same camera pose before and after)

Headless Chromium with SwiftShader, pages served locally from `docs/assets/roadmap/`.
Exploded view from the page's deterministic render mode (`exploded.html?render=1`, frame 0 assembled,
frame 780 opened base, 1280 x 720); the before frame 0 is byte-identical in size to the #56 evidence
image, so the pipeline matches. Robot page: the 3D stage after the Overview and Side presets, 1280 px.

| Before | After |
|---|---|
| `exploded_1280_assembled_before.png` | `exploded_1280_assembled_after.png` |
| `exploded_1280_open_base_before.png` | `exploded_1280_open_base_after.png` |
| `robot_1280_overview_before.png` | `robot_1280_overview_after.png` |
| `robot_1280_side_before.png` | `robot_1280_side_after.png` |
| `exploded_1280_page_before.png`, `exploded_375_before.png`, `robot_375_before.png` | `exploded_1280_page_after.png`, `exploded_375_after.png`, `robot_375_after.png` |
| | `exploded_base_detail_2x_after.png` (2560 x 1440 render, base crop) |

Console at 375 and 1280 px, both pages, before and after: no errors, no warnings, no failed requests,
no horizontal scroll (scrollWidth equal to the viewport width).

## Colour calibration (follow-up 1)

The first version of the look washed out the finish (RAL 7035 panels near white, RAL 7016 cover mid-grey).
`model/look.js` now calibrates per page (`OAMR_LOOK.CAL`):

| Page | Exposure | Key light | Environment, dielectric classes | Environment, metal and glass classes |
|---|---|---|---|---|
| exploded.html | 1.2 (was 0.9) | 2.8, moved to the camera side, front right above, about 55 degrees from the front, side and top faces (was 1.6, front left) | 0.14 (was 1) | 1.3 (was 1) |
| robot.html | 1.05 (unchanged, so the store look is unchanged) | the store lights, unchanged | 0.08 (was 1) | 1.3 (was 1) |

Shadows, contact shadow and material classes are unchanged. `colour.js` with `colour_sampler.js`: the
page's own frame, a part-ID pass and a normal pass of the same camera; pixels of the part whose 5 x 5
neighbourhood is the same part, whose face points to the key light (n . L > 0.35) and to the camera;
median sRGB per part. Exploded view: render mode frame 0 (assembled), 1280 x 720, key direction of the
calibrated light for both states (so the same pixels are compared). Robot page: `?look=full`, 1280 x 800,
camera tiles off, the store key light. Luma difference to the finish.json sRGB value (Rec. 709 weights on
sRGB values); largest single-channel difference in brackets. Before: branch head `b28a92f`.

| View | Part (finish.json sRGB) | Pixels | Before: median sRGB, luma | After: median sRGB, luma |
|---|---|---|---|---|
| exploded, assembled | side panel (`#CBD0CC`, 203 208 204) | 10,740 | 182 185 183, -10.9 % (11.1) | 192 195 192, **-6.1 %** (6.3) |
| exploded, assembled | cover (`#383E42`, 56 62 66) | 13,439 | 113 117 121, +90.8 % (101.8) | 54 59 63, **-4.6 %** (4.8) |
| exploded, assembled | arm profile (`#383E42`) | 4,612 | 33 37 40, -40.4 % (41.1) | 56 62 67, **+0.1 %** (1.5) |
| robot page, Side preset | arm profile (`#383E42`) | 333 | 48 53 56, -14.5 % (15.2) | 53 59 62, **-5.0 %** (6.1) |
| robot page, Side preset | side panel, cover | 0 | not in view (the preset frames the upper body) | not in view |
| robot page, Overview preset | side panel (`#CBD0CC`) | 78 | 228 229 227, +10.6 % (12.3) | 186 187 180, **-9.9 %** (11.8) |
| robot page, Overview preset | cover (`#383E42`) | 18,559 | 124 130 133, +111.3 % (121.4) | 64 67 67, **+8.8 %** (14.3) |
| robot page, Overview preset | arm profile (`#383E42`) | 212 | 49 53 55, -14.3 % (16.7) | 56 61 63, **-1.5 %** (4.5) |

All lit faces are within 10 % in luma. On the robot page the store lights are warm (area lights `#FFF5E8`),
so the cover reads 14 % high in red; the side panel shows only 78 pixels in the Overview preset.

## Light look fallback (follow-up 2)

`OAMR_LOOK.lightLook`: the robot materials of the metal and glass classes (anodised aluminium, heatsink,
sensor glass) keep the environment; the others switch to Lambert twins (same colour, map, vertex colours,
opacity; no image-based light); robot shadows off; the contact shadow stays. exploded.html also turns its
shadow map off, hides the shadow catcher and adds a hemisphere light for the non-metal parts.

| Page | Switches to the light look | Back to the full look |
|---|---|---|
| exploded.html | new "High quality" toggle off; or the first 30 frames (rendered every frame while probing) average over 33 ms and the toggle was not used | toggle on |
| robot.html | existing "High quality" toggle off (it also turns GTAO off, as before); or the first 30 frames average over 33 ms (the toggle then stays as it was) | toggle on |

`?look=full` or `?look=light` forces a look and skips the probe; the exploded render mode (videos,
previews) is always the full look unless `look=light` is given. Default: the full look.
`looktest.js` on SwiftShader: exploded.html probe 296.7 ms (1280 px) and 287.2 ms (375 px), robot.html
12,690 ms and 1,135 ms: all four switched to the light look; the toggles switch back and forth as listed;
no console errors or warnings; no horizontal scroll.

## Preview pictures (follow-up 3)

`preview.js`, 1920 x 1080, page UI hidden, full look (calibrated) unless noted. Exploded-view pictures
from the render mode (`exploded.html?render=1`, `window.__renderKey` with a pose written like a tour
keyframe; the wordmark of the render mode stays); robot-page pictures from `robot.html?look=full` with
everything but the 3D canvas hidden. 07, 08 and the contact sheet are palette-reduced (256 colours) to
stay under the 1 MB image limit of `scripts/check_docs.sh`.

| File | Picture |
|---|---|
| `preview/01_assembled_front_three_quarter.png` | robot assembled, front three-quarter, whole robot |
| `preview/02_assembled_rear_three_quarter.png` | robot assembled, rear three-quarter |
| `preview/03_base_close_up_front_three_quarter.png` | base close-up, front three-quarter (panels, cover, sensors, wheels and castors) |
| `preview/04_upper_body_close_up.png` | upper body: lift column, adapter plate, arm profile with the cyan strips, arms, head camera |
| `preview/05_exploded_explode_robot.png` | exploded view, Explode robot |
| `preview/06_exploded_open_base_labels.png` | exploded view, Open the base, name labels |
| `preview/07_robot_page_side_dark_store.png` | robot page, Side preset, dark store |
| `preview/08_robot_page_overview_dark_store.png` | robot page, Overview preset, dark store |
| `preview/09_light_look_assembled_front_three_quarter.png` | light look (fallback), same pose as 01 |
| `preview/contact_sheet.png` | all nine, labelled |

## Performance

`perf.js`: same machine (4 vCPU container, no GPU, SwiftShader), 1280 x 800, median of 30 renders after
5 warm-up renders, each render followed by a 1-pixel `readPixels` so that it is finished. Two rounds.

| Frame | Before (round 1, 2) | After (round 1, 2) | Change |
|---|---|---|---|
| exploded.html, parts moving (tour frames, shadow map updated) | 343, 380 ms | 1134, 1039 ms | +231 %, +173 % |
| exploded.html, camera only (orbit) | 152, 176 ms | 531, 520 ms | +249 %, +195 % |
| robot.html, store scene, high quality (GTAO, camera tiles) | 19,695, 18,546 ms | 18,843, 18,374 ms | -4 %, -1 % |

After the calibration, both looks (`perf.js 8802 full`, `perf.js 8802 light`, one round each):

| Frame | #56 (rounds 1, 2) | Full look | Light look |
|---|---|---|---|
| exploded.html, parts moving | 343, 380 ms | 1,183 ms (+211 to +245 %) | 290 ms (-15 to -24 %) |
| exploded.html, orbit | 152, 176 ms | 514 ms (+192 to +238 %) | 135 ms (-11 to -23 %) |
| robot.html, store, high quality | 19,695, 18,546 ms | 18,867 ms (-4 %, +2 %) | 17,410 ms (-12 %, -6 %) |

The light look is within the budget (faster than #56); the full look is not, on this CPU rasteriser. On a
device that slow the probe selects the light look (it did on SwiftShader, 287 to 297 ms per frame).

**The 10 % budget is not met on exploded.html on this machine.** Breakdown of one exploded frame
after (`prof*.js` runs, same set-up): 1,020 to 1,084 ms with everything; without shadows 848 to 863 ms;
without shadows and environment 346 ms; with plain materials as well 306 ms. The image-based light
(about 500 ms) and the shadow sampling (about 170 ms) cost the time; a depth pre-pass did not help
(1,299 ms), so it is per-pixel shading, not overdraw. Environment only on metal and glass with a
hemisphere light for the rest: 799 ms; hemisphere light with shadows, no environment: 519 ms. No
configuration with an environment map or shadows stays within +10 % on a CPU rasteriser, so the look is
kept as specified and the budget is an open item for review (see the PR). Not measured on a GPU (none
here). The robot page already used the room environment, shadows and GTAO; it did not get slower.

## Page weight

| Page and what it loads | Before | After | Change |
|---|---|---|---|
| robot.html (page, three.js files, model files, finish.json) | 4,061,252 bytes | 4,086,659 bytes | +25,407 |
| of which robot.html itself | 1,420,876 | 450,040 | -970,836 |
| exploded.html (page, scripts, finish.json, exploded.json, poster) | 3,714,807 | 3,740,359 | +25,552 |

`three-r160.min.js` (+1,852 bytes for RoomEnvironment) is now shared, so a visitor who opens both pages
loads it once. The exploded first-load budget of `check_roadmap.py` (4,000,000 bytes) still holds.

## Commands

```bash
python3 scripts/check_roadmap.py                      # passed
python3 scripts/check_roadmap.py --dir <#56 roadmap>   # fails: second three.js, robot code and look in the pages
mkdocs build --strict                                 # passed (pinned requirements.txt)
bash scripts/check_docs.sh                            # passed, 0 warnings
python3 linkcheck.py site                             # 34,571 local links, 0 missing (lychee could not be installed here)
node geomcheck.js 8800 8802 geomtest.html gx          # exploded: 132/132 meshes, 0 differing pixels
node geomcheck.js 8800 8802 robot.html gr             # robot: 203/203 meshes, 0 differing pixels
node perf.js 8800; node perf.js 8802                  # two rounds each
node perf.js 8802 full; node perf.js 8802 light       # after the calibration
node colour.js 8803 exploded; node colour.js 8802 exploded   # colour samples (8803: branch head b28a92f)
node colour.js 8802 robot '[{}]' side; node colour.js 8802 robot '[{}]' over
node looktest.js 8802                                  # probe and toggles
node preview.js 8802 preview                           # preview pictures
```

Ports: 8800 serves the #56 roadmap folder, 8802 this change (`python3 -m http.server`).

## Not verified

- Frame time on a GPU, and how many real devices the 33 ms probe sends to the light look; SwiftShader only.
- Colour on calibrated displays; the samples are sRGB values of the rendered frame.
- The offline link check ran with a Python equivalent, not lychee (the CI step runs lychee).
- The tour videos, posters and `model/exploded-static.png` still show the #56 look; not re-rendered in this step.
- Visual review on real displays and browsers other than headless Chromium.
