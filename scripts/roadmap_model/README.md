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
| `design_intent/` | Parametric CadQuery scripts of the design-intent parts (`run_all.py`) |

Sources are read from `../src` (clones of the openAMRobot repositories at the snapshot; override with `OAMR_SRC`):
`openamr-upperbody-sw` (datums.yaml), `openamr-platform-sw` (sensor_frames.yaml). Run everything with `./run_all.sh`.
Catalogue outlines marked "verify" in `parts.yaml` are not in the repositories and must be checked before CAD.
