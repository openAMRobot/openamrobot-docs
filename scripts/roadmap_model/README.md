# Roadmap model builder

Builds the placement data of the OpenAMRobot 2.0 roadmap model (`docs/assets/roadmap/model/`) from its sources,
so that the weekly update is a rerun plus edits to the tables here.

Frame: `base_footprint` (floor under the drive-axle midpoint, x forward, y left, z up, REP 103/105).
`frames.bl_to_bf` is the only conversion (base_link = base_footprint + 0.098 m); the three.js scene uses the same axes.

| File | Role |
|---|---|
| `facts.yaml` | Facts of record of the snapshot (documents in force, heights, zones) |
| `parts.yaml` | Parts table: front bay and rear zone parts (packed), fixed parts with their position source |
| `bom_map.yaml` | BOM Issue 7.14 line to model coverage (class, geometry and position source, mass) |
| `conflicts.yaml` | Conflicts between sources (hardware page) |
| `bom714.py` | Re-imports BOM Issue 7.14 into the hardware page PARTS list (idempotent) |
| `build.py` | Writes `placement.json`, `exploded.json` entries, `bom_coverage.csv`, `fastener_schedule.csv`, `cable_list.csv`, `assembly_sequence.csv`, `source_snapshot.json` |
| `scene_dump.js` | Dumps the page scene (Playwright) for the self-check |
| `analyse.py` | Geometry and hardware analysis, writes `geometry_issues.csv` and `analysis_summary.json` |
| `hardware_sections.py` | Writes the generated sections of `hardware.html` |
| `export_layout.py` | Writes `export/openamrobot2_layout.step` for SolidWorks |
| `front_bay.py` | Front bay options A (two-tier) and B (DIN parts in the side pockets) with the TZBOT receiver in place; fit numbers |
| `estop_positions.py` | Second E-stop positions P1 to P4 against the reach requirement (heights, arm sweep, reach study, ZED view) |
| `lift_plate_check.py` | Load check of the lift base plate on the centre-frame arch (bolts, rivet nuts, plate, arch top sheet, tilt) |
| `urdf_expand.py` | Expands the combined robot model (combined_robot.xacro) without ROS: pip xacro and a minimal ament index under `../ament` |
| `link_map.yaml`, `parity_dump.js`, `parity.py` | Roadmap vs combined model parity report (warn only, convergence phase 1) |
| `mass_export.py` | `mass_export.yaml`: masses, COM and box inertia per URDF link, for the platform-sw mass PR and mass_provenance.yaml |
| `shots.js` | Screenshots of the shared model for the visual review |
| `design_intent/` | Parametric CadQuery scripts of the design-intent parts (`run_all.py`) |

Goal of the roadmap model: the roadmap becomes a renderer of the expanded combined_robot.xacro (openamr-upperbody-sw) at a pinned
commit, with no hand-typed dimensions in model.js. One geometry, two presentations. URDF only: physics, inertials, collisions,
ros2_control, MoveIt, Gazebo. Roadmap only: finishes, labels, exploded offsets, BOM classes, harness, fasteners, design-intent parts;
a roadmap-only part always attaches to a URDF link with an offset. Phases: 1) warn-only parity report; 2) URDF-to-GLB renderer plus
an overlay file keyed by URDF link name; 3) parity fails CI above 0.5 mm and the frozen fixture in upperbody-sw is removed; 4) the
combined model feeds the lift joint, limits, mass, COM, collision reports and MoveIt trajectories into the roadmap, and the roadmap
feeds BOM masses, visual-only detail links and confirmed design-intent datums back.

Sources are read from `../src` (clones of the openAMRobot repositories at the snapshot; override with `OAMR_SRC`):
`openamr-upperbody-sw` (datums.yaml), `openamr-platform-sw` (sensor_frames.yaml). Run everything with `./run_all.sh`.
Catalogue outlines marked "verify" in `parts.yaml` are not in the repositories and must be checked before CAD.
