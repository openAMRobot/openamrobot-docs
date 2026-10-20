# Changelog

All notable changes to the OpenAMRobot documentation site are recorded here. The format follows Keep a Changelog; the site has no version numbers, so entries are dated.

## 2026-10-20

### Added

- OpenAMRobot 2.0 roadmap and status (snapshot 19 October 2026): a reference page with five linked interactive pages (Overview, Robot, Hardware, Architecture, Progress), including a step-by-step action plan to v2.0.0 under `docs/assets/roadmap/`. Each part shows delivery status, runtime evidence and physical acceptance separately, with links to its evidence. Linked from the project status page.

## 2026-10-12

### Changed

- OpenAMRobot 2.0 design pages follow P-03 revision 19.0 and BOM Issue 7.7:
  - Column position: the column axis is 330 mm behind the chassis front edge, x +0.060 m from `base_link` at `bp000` and +0.110 m at `bp050`.
  - Base camera: the Gemini 336L housing centre is 142.5 mm above the floor, `base_camera_link` (0.376, 0, 0.0445).
  - Near-field sensors: four MB7060 ultrasonic sensors and two TF-Luna cliff sensors.
  - IMU: the ICM-42688-P is on the centreline at x 0.195 m; the MPU6500 is the Gate A unit only.
  - LiDAR: the RPLIDAR S3 beam is 222.0 mm above the floor.
- The hardware architecture page no longer embeds the BOM Issue 7 diagram; the asset carries a superseded banner.
- The dark-store simulation uses the same column, camera, LiDAR and near-field positions and is labelled visualization only; grocery requirements belong to OpenAMRobot 3.0.

## 2026-10-11

### Changed

- Dark-store pick simulation follows option B: two base-plate positions (`bp000` default, `bp050`) instead of five, the OpenArm arm mount point 180 mm ahead of the column axis on the HFS6-60120 arm profile, the ZED Mini lens 22 mm ahead of and 223 mm above the arm mount point, and packing-table spots measured from the shoulder. Source in `tools/dark-store-sim/`, rebuilt into `docs/assets/simulation/`.

## 2026-10-09

### Changed

- OpenAMRobot 2.0 design pages follow the upper-body mounting option B (P-03 revision 18.9 item 18): DOLD Hexalift V4 lift column on a two-position base plate (`bp000`, `bp050`), OpenArm arm mount point 180 mm ahead of the column axis, shoulder 1000 to 1350 mm, ZED Mini head camera on the lift carriage and the configuration IDs. The general arrangement drawings of 28 September 2026 are withdrawn until they are regenerated from the option B CAD, and the F2S results of 28 September 2026 are withdrawn pending the option B rerun.

## 2026-09-28

### Added

- Collapsible table of contents on desktop: an arrow in the right sidebar hides it and widens the page; a tab on the right edge brings it back. The choice is remembered in the browser.

- Reference section "OpenAMRobot 2.0 design": section index, interactive hardware architecture diagram (BOM Issue 7), general arrangement drawings with parts list and mast detail, and the F2S mass and stability summary.
- Embedded-drawing styles (`oamr-frame`, `oamr-figure`) in `stylesheets/brand.css`.
- Cross-links from the mobile platform, upper body and reference index pages.
