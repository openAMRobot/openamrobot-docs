#!/usr/bin/env bash
# Weekly rerun of the roadmap model (sources in ../src, see README.md).
set -euo pipefail
cd "$(dirname "$0")"
python3 urdf_expand.py
python3 design_intent/run_all.py
python3 build.py
(cd ../../docs/assets/roadmap && python3 -m http.server 8765 >/dev/null 2>&1 & echo $! > /tmp/oamr_http.pid)
sleep 1
trap 'kill $(cat /tmp/oamr_http.pid) 2>/dev/null || true' EXIT
node scene_dump.js http://localhost:8765/ /tmp/oamr_scene_dump.json
python3 analyse.py --dump /tmp/oamr_scene_dump.json
python3 mass_export.py
node parity_dump.js http://localhost:8765/ /tmp/oamr_parity_dump.json
python3 parity.py --dump /tmp/oamr_parity_dump.json --sync-roadmap-only
python3 hardware_sections.py
python3 export_layout.py
(cd ../.. && node scripts/audit_sync.js http://localhost:8765/ && python3 scripts/check_roadmap.py && python3 -m unittest discover -s scripts/tests)
