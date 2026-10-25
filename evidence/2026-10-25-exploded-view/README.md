# Exploded view and shared robot model: screenshots (25 Oct 2026)

Evidence for `docs/assets/roadmap/exploded.html` and the robot page on the shared model in
`docs/assets/roadmap/model/`. Visualization only; not mechanical, electrical or safety evidence.

All pictures come from the built site (`mkdocs build --strict`, social plugin on), served
locally and opened in headless Chromium with SwiftShader WebGL (software rendering). The browser
console showed no errors or warnings, and no page scrolled horizontally (scrollWidth equal to
the viewport width).

| File | Content |
|---|---|
| `exploded_1280_assembled.png` | Exploded view at 1280 px, assembled, three-quarter view; numbers only on components that are not hidden |
| `exploded_1280_exploded.png` | after Explode |
| `exploded_1280_stage5.png` | exploded, build stage 5 (near-field sensors, LiDAR and base camera): only its components highlighted |
| `exploded_1280_selected_battery.png` | exploded, battery cell-group envelope selected (provisional, 35 % opacity) |
| `exploded_375_exploded.png`, `exploded_375_selected_lidar.png` | 375 px: exploded with the bottom sheet collapsed; a selection opens the sheet |
| `exploded_1280_no_webgl.png` | WebGL disabled (`--disable-3d-apis`): static image and the component list |
| `robot_1280_overview_before.png`, `robot_1280_overview_after.png`, `robot_1280_overview_diff.png` | Robot page, Overview preset, main f492795 against this branch; changed pixels in red |
| `robot_1280_base_link_before.png`, `robot_1280_base_link_after.png`, `robot_1280_base_link_diff.png` | same camera pose (the page's `base_link` frame focus) |
| `robot_375_before.png`, `robot_375_after.png` | Robot page at 375 px |

Pixel differences over 30 (sum of RGB): two captures of the unchanged page differ in 4275 pixels
(render noise). Overview before against after: 6767 pixels. `base_link` pose: 18432 pixels, in
the new nav entry, where the battery envelope on main (above the cover) was, and in render
noise. The cell-group envelope (210 mm high, behind the centre bracket) sits under the cover at
35 % opacity.
