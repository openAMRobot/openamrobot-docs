# Base E-stop and RESET on the robot page: stills (28 Oct 2026)

Evidence for the robot page (`docs/assets/roadmap/robot.html`) on the base GLB of openamr-platform-sw
PR #100 (head 1939b82, draft): base E-stop and RESET as placeholders in the release 001 button holes of
the front panel. Visualization only; not mechanical, electrical or safety evidence.

Rendered with the page's render mode, served locally, headless Chromium with SwiftShader WebGL:

```bash
(cd docs/assets/roadmap && python3 -m http.server 8765) &
node scripts/render_store.js 1280 720 --still 0 --cam front --out robot_1280x720_<state>_front.png
node scripts/render_store.js 1280 720 --still 0 --cam rear --out robot_1280x720_<state>_rear.png
```

`rear` is a raised rear three-quarter close-up added to the render mode for these stills (viewpoint
only). The PNGs are palette-reduced (256 colours) to stay under the 1 MB image limit.

| File | Content |
|---|---|
| `robot_1280x720_before_front.png` | Before: the E-stop twice (GLB placeholder at the lower front left, plus the old illustrative yellow box and red head high on the front panel at y -0.2) and the RESET twice (GLB placeholder at the lower front right, plus the old one on the rear deck); dark tote rail bars on the top cover beside both totes |
| `robot_1280x720_before_rear.png` | Before, from the rear: the old RESET (blue) on the rear deck and the tote rail bars on the cover |
| `robot_1280x720_after_front.png` | After: exactly one base E-stop (red, lower front, robot left, +y) and one RESET (blue, lower front, robot right, -y), both from the GLB; the chest E-stop on the arm profile (arm kit E-stop) unchanged |
| `robot_1280x720_after_rear.png` | After, from the rear: no RESET on the rear deck, no bars on the cover; totes, riser and base-plate hole marks unchanged |
