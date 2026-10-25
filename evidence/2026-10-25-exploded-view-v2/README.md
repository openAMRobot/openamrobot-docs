# Exploded view v2, opened base, guided tour and video: evidence (25 Oct 2026)

Evidence for `docs/assets/roadmap/exploded.html` (exploded view v2) and the tour videos in
`docs/assets/roadmap/media/`. Visualization only; not mechanical, electrical or safety evidence.

The base geometry is the GLB of openamr-platform-sw PR #96 (recognisable envelopes; sha256
`fb41c555b1e429804e2794355a08d61bce8315ed0454b4957e3f435d0796b7b0`, 844,332 bytes), embedded in
`model/base_glb.js` in the same dotted base64 format as before.

All screenshots come from the built site (`mkdocs build --strict`), served locally and opened in
headless Chromium with SwiftShader WebGL (software rendering). The browser console showed no errors
or warnings in any of them, and no page scrolled horizontally (scrollWidth equal to the viewport
width). No video was requested on page load.

| File | Content |
|---|---|
| `exploded_1280_assembled.png` | 1280 px, assembled, three-quarter view; the viewer fills the window below the nav |
| `exploded_1280_cutaway.png` | Cutaway: cover and flanges at 14 %, front and side panels at 30 % opacity; the cells, J401 with heatsink and NUCLEO in context |
| `exploded_1280_open_base_labels.png` | Open the base: cover lifted and faded, panels out, internal components raised above the deck with name labels, none overlapping |
| `exploded_1280_stage4_framed.png` | Build stage 4 (compute and base controller): the camera frames the base, short names next to the numbers |
| `exploded_1280_selected_battery_open.png` | Opened base, battery cell-group envelope selected: fly-to, eight LF105 cell boxes inside the translucent envelope shell |
| `exploded_1280_tour.png` | Guided tour at about 29 s: Pause and Stop shown, the other view controls disabled |
| `exploded_375_assembled.png`, `exploded_375_open_base.png`, `exploded_375_selected_lidar.png` | 375 px: bottom sheet collapsed; opened base with labels; a selection opens the sheet |
| `exploded_1280_no_webgl.png` | WebGL disabled: static image and the component list |
| `robot_1280_overview.png`, `robot_375.png` | Robot page on the shared model with the new envelopes, otherwise unchanged |

Behaviour checks in the same browser (Playwright):

- Play tour, then Escape: the tour stops, the caption hides, the view returns to Assembled.
- Record video: shown (MediaRecorder available); recording 3 s and pressing Stop gave a WebM
  download (`openamrobot-2-tour-880x755.webm`, the viewer's canvas size).
- `prefers-reduced-motion: reduce`: Open the base jumps to the end pose without animation.

## Videos

Rendered with `node scripts/render_tour.js` from the page's render mode
(`exploded.html?render=1&frame=N&w=W&h=H`), frame by frame at 30 fps, piped into ffmpeg
(`-c:v libx264 -preset veryfast -crf 23 -pix_fmt yuv420p -movflags +faststart -an`). Captions,
labels and the wordmark are drawn into each frame in the page fonts. Posters are the frame at
26 s (opened base), palette-reduced PNG.

| File | Size | Duration | Video | sha256 |
|---|---|---|---|---|
| `openamrobot-2-tour-1080p.mp4` | 9,304,005 bytes | 49.533 s | h264 1920x1080, 30 fps, yuv420p, 1486 frames, 0 audio streams | `7b7b5e2d44a9fb18b81faa9432efd0e1db3828df1b567c95941e09bb11bd2eab` |
| `openamrobot-2-tour-1080x1350.mp4` | 8,126,409 bytes | 49.533 s | h264 1080x1350, 30 fps, yuv420p, 1486 frames, 0 audio streams | `6dc36a85fbdc4faeac3f8c32fbbe24db297b7fc87ea9f8636c56359841b6c35d` |
| `openamrobot-2-tour-1080p-poster.png` | 320,711 bytes | - | PNG poster | `37b672ca1e8d26e1d21b42607cf194d9a555b68a0b3bcfd0ab70c9f9a4c28355` |
| `openamrobot-2-tour-1080x1350-poster.png` | 244,975 bytes | - | PNG poster | `b9e044f778558268910a6c8bb9e3c3a12d9a6f57c78856182141c8d52d5c304f` |

Two renders of the 1080p video from the same page are byte-identical (same sha256). Rendering took
about 7 minutes per video with SwiftShader; the 1080p video is 9.3 MB and the vertical cut 8.1 MB,
both under 15 MB.
