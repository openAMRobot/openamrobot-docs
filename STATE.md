# State

Working state of this repository for maintainers and agents. Not published on the site (outside `docs/`).

## OpenAMRobot 2.0 plan set reflected in the docs

As of 1 November 2026: P-03 rev20.2, E-01 rev1.6, M-01 rev19.7, BOM Issue 7.14.

- Roadmap pages (`docs/assets/roadmap/`): design values aligned with this plan set; delivery status, evidence and repository heads are still the 24 October 2026 snapshot. The procurement table is still the BOM Issue 7.10 import (136 rows, 53 packages) and is labelled as such.
- Item-specific citations of earlier revisions (for example "P-03 rev19.7 item 23", "rev20.0 item 24") are kept as the record of where a decision was taken.
- Shared model (`docs/assets/roadmap/model/`): Getac ZX80 drawn landscape (default position of a rotatable mount, portrait second position not drawn); second E-stop on the rear face of the static lift column. `scripts/sync_audit.json` regenerated on 1 November 2026: 63 parts, 0 mismatches.
- `docs/assets/hardware/openamrobot2-hardware-architecture-bom7.html` is the BOM Issue 7 record; superseded notes at the top carry the later values.

## Open follow-ups

- Re-import the procurement view and row counts from BOM Issue 7.14.
- K1/K2 decision under the availability rule due 2 November 2026: update the pages with the outcome.
- Next roadmap snapshot: refresh statuses, evidence and repository heads, then move the snapshot date.
- Robot page first load is within about 10 bytes of its budget in `scripts/check_roadmap.py`; the next text addition to `robot.html` or `model/model.js` needs a trim or a budget decision.
