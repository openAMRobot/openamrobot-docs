# SPDX-License-Identifier: MIT
"""BOM import checks (bom715.py; review of #84, 9 Nov 2026).

A workbook cell must not end the inline PARTS script, prose in Qty must stop the import, IDs must be valid and unique, a
page record that left the workbook must be reported, and private notes (prices, sellers, first names, partner names) must
not reach the page. The committed page must hold numeric quantities only and no "</" inside its PARTS script.
"""
import json
import os
import re
import sys
import unittest
from pathlib import Path

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.join(os.path.dirname(HERE), "roadmap_model"))
import bom715 as B  # noqa: E402
from bom714 import obj_span  # noqa: E402

PAGE = os.path.abspath(os.path.join(HERE, "..", "..", "docs", "assets", "roadmap", "hardware.html"))
HEAD = ["ID"] + list(B.FIELDS)


def row(k, qty="1", text="M8 screw"):
    return [k, "Lift mechanics", "Part", "Maker", text, qty, "selected", ""]


class Rows(unittest.TestCase):
    def test_prose_in_qty_stops_the_import(self):
        with self.assertRaisesRegex(B.BomError, "LFT-099: Qty is not a number"):
            B.check_rows(HEAD, [row("LFT-099", qty="Upper deck: 4 x M8; confirm the interface")])

    def test_override_corrects_a_known_qty_defect(self):
        self.assertIn("MEC-019", B.check_rows(HEAD, [row("MEC-019", qty="Upper deck: legacy STEP 190 x 300 mm")]))

    def test_duplicate_and_invalid_ids_stop_the_import(self):
        with self.assertRaisesRegex(B.BomError, "duplicate ID"):
            B.check_rows(HEAD, [row("LFT-001"), row("LFT-001")])
        with self.assertRaisesRegex(B.BomError, "not a BOM ID"):
            B.check_rows(HEAD, [row("Note: see sheet 2")])

    def test_missing_header_stops_the_import(self):
        with self.assertRaisesRegex(B.BomError, "header lacks Qty"):
            B.check_rows([h for h in HEAD if h != "Qty"], [])

    def test_removed_and_stray_records_are_reported(self):
        parts = {"LFT-001": {"ID": "LFT-001"}, "LFT-002": {"ID": "LFT-002"}}
        with self.assertRaisesRegex(B.BomError, "LFT-002"):
            B.merge(parts, {}, {"LFT-001": dict(zip(HEAD, row("LFT-001")))})
        rep = B.merge({"LFT-001": {"ID": "LFT-001"}}, {"LFT-001": {}, "LFT-005": {}}, {"LFT-001": dict(zip(HEAD, row("LFT-001")))})
        self.assertEqual(rep["removed"], ["LFT-005"])


class Publication(unittest.TestCase):
    def test_script_terminator_and_private_note_stay_out(self):
        bom = {"LFT-099": dict(zip(HEAD, row("LFT-099", text="M8 </script><script>alert(1)</script>, about 27 EUR, ask Alex, DigiKey RFQ")))}
        parts = {}
        B.merge(parts, {}, bom)
        page = "<script>var PARTS=%s;</script>" % B.script_json(parts)
        self.assertEqual(page.count("</script>"), 1)
        a, b = obj_span(page, "var PARTS")
        text = json.loads(page[a:b])["LFT-099"]["Model / order code"]
        for bad in ("EUR", "Alex", "DigiKey"):
            self.assertNotIn(bad, text)


class CommittedPage(unittest.TestCase):
    def test_parts_quantities_are_numbers_and_script_is_closed_once(self):
        s = open(PAGE, encoding="utf-8").read()
        a, b = obj_span(s, "var PARTS")
        self.assertNotIn("</", s[a:b])
        bad = {k: v["Qty"] for k, v in json.loads(s[a:b]).items() if v.get("Qty") and not re.fullmatch(r"\d+(?:\.\d+)?", v["Qty"])}
        self.assertEqual(bad, {})


    def test_mass_export_and_public_bom_use_the_same_revision(self):
        page = Path(PAGE)
        facts = Path(HERE).parent / "roadmap_model" / "facts.yaml"
        issue = re.search(r"^  BOM: (Issue [0-9.]+)", facts.read_text(encoding="utf-8"), re.M).group(1)
        export = (page.parent / "model" / "mass_export.yaml").read_text(encoding="utf-8")
        self.assertIn("BOM " + issue + " masses", export)
        self.assertIn("<h1>Hardware: BOM " + issue, page.read_text(encoding="utf-8"))


if __name__ == "__main__":
    unittest.main()
