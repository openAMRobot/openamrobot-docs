# OpenAMRobot 2.0 dark-store pick simulation: source

Source of the interactive 3D simulation published at
[docs.openamrobot.ai/reference/openamrobot-2/dark-store-simulation](https://docs.openamrobot.ai/reference/openamrobot-2/dark-store-simulation/).
It builds into one self-contained HTML file (three.js, fonts and OpenArm meshes inlined, no external requests).

```bash
cd tools/dark-store-sim
npm ci
npm run build      # out/artifact.html and out/web/index.html
npm run publish    # build, then copy into docs/assets/simulation/
```

Open `out/web/index.html` in a browser to test. Commit the refreshed file in `docs/assets/simulation/` together with the source change.

## Status

Visualization only; grocery requirements belong to OpenAMRobot 3.0. Design discussion tool for the option B upper-body mounting of P-03 rev18.9 item 18 (DOLD Hexalift V4 lift on a two-position base plate, OpenArm 2.0 arm mount point 180 mm ahead of the column axis, front totes), with the column position and base sensor layout of P-03 rev19.0 (column axis x +0.060 m from base_link at bp000). Not a specification; about ±2 cm.

## Where to change what

| Change | File |
|---|---|
| Robot dimensions, lift data, stops, base-plate positions, camera poses | `src/spec.js` |
| Robot geometry (chassis, column, totes, arms, cameras) | `src/robot.js` |
| Store layout, aisles, planogram, packing table, dock | `src/world.js` |
| Product types, sizes, masses, labels | `src/products.js`, `src/textures.js` |
| Reach, collision, grasp, moment and camera checks | `src/analysis.js`, `src/kin.js` |
| Motion planning, timeline, order run, unloading | `src/anim.js` |
| UI, views, demo order (`ORDER`), recording and CSV export | `src/main.js`, `index.tpl.html` |
| OpenArm 2.0 meshes and kinematics (generated data) | `src/openarm_data.js` |

## Stills and videos

The scripts drive the built page headless and write frames to `out/`. They default to the SwiftShader software renderer; set `CHROMIUM` to your Chromium or Chrome binary. On a machine with a GPU, remove the SwiftShader flags to render many times faster.

| Command | Output |
|---|---|
| `npm run stills -- '<json shot list>'` | Full HD stills of chosen moments and camera positions |
| `npm run video` | Order run at 8× with camera moves, captions and end card (frames in `out/vid/frames`) |
| `npm run blooper` | "Build failed" blooper (frames in `out/chaos/frames`) |
| `node scripts/endcard.mjs <first frame> <count> <dir>` | Terminal end card frames for the blooper |

Encode frames with ffmpeg, for example:

```bash
ffmpeg -framerate 25 -i out/vid/frames/%05d.jpg -c:v libx264 -crf 18 -pix_fmt yuv420p out/order_run.mp4
```

## Repository boundaries

This folder holds the simulation source only. The published page lives in `docs/reference/openamrobot-2/dark-store-simulation.md` and the built file in `docs/assets/simulation/`. Engineering decisions are recorded in the plan set, not here.

## Licence

Code in this folder: MIT, per the [OpenAMRobot licensing standard](../../LICENSING.md). `src/openarm_data.js` is derived from the official OpenArm 2.0 description and remains under its upstream licence. Product names and brands in the store are invented.
