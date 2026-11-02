# State

Working state of this repository for maintainers and agents. Not published on the site (outside `docs/`).

## OpenAMRobot 2.0 plan set reflected in the docs

As of the 2 November 2026 snapshot (state at 1 Nov 23:59 CET): P-03 rev20.2, E-01 rev1.6, M-01 rev19.7, BOM Issue 7.14, B-02 rev18.10, decisions.yaml a9e229e.

- Roadmap pages (`docs/assets/roadmap/`): snapshot 2 Nov 2026; PARTS is BOM Issue 7.14 (146 records, `scripts/roadmap_model/bom714.py`).
- Model placement data is generated: `scripts/roadmap_model/run_all.sh` (sources in `../src`). Weekly update: edit `facts.yaml`, `parts.yaml`, `bom_map.yaml`, `conflicts.yaml`, then rerun.
- Item-specific citations of earlier revisions (for example "P-03 rev19.7 item 23", "rev20.0 item 24") are kept as the record of where a decision was taken.
- Shared model (`docs/assets/roadmap/model/`): Getac ZX80 drawn landscape (default position of a rotatable mount, portrait second position not drawn); second E-stop on the rear face of the static lift column. `scripts/sync_audit.json` regenerated on 1 November 2026: 63 parts, 0 mismatches.
- `docs/assets/hardware/openamrobot2-hardware-architecture-bom7.html` is the BOM Issue 7 record; superseded notes at the top carry the later values.

## Open follow-ups

- K1/K2 decision of 2 November 2026: update the pages and `parts.yaml` with the outcome.
- Catalogue outlines marked "verify" in `parts.yaml` need the datasheets; PNOZ DIN assembly, DDR-240B-24 and RSD-60G-5 have no space in the proposed layout.
- Wrist cameras are robot-page fittings, not registry parts.
- Tour and store media were not re-rendered (tour script unchanged).
