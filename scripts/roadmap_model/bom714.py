#!/usr/bin/env python3
"""Apply the BOM Issue 7.14 (27 Oct 2026, with 1 Nov changes) re-import to hardware.html.

PARTS (embedded JSON), BLOCK (row to block map) and the per-block BOM tables are updated so that
PARTS holds the 146 records of Issue 7.14. Idempotent: rerunning changes nothing.
Usage: python3 scripts/roadmap_model/bom714.py [docs/assets/roadmap/hardware.html]
"""
import html as H
import json
import re
import sys

PAGE = sys.argv[1] if len(sys.argv) > 1 else "docs/assets/roadmap/hardware.html"
ISSUE = "Issue 7.14 (27 Oct 2026, with 1 Nov changes)"
PKG_LIFT = "BUY-53"


def row(i, sub, comp, mfr, model, qty, sel, pkg=PKG_LIFT, rel="HOLD - release checks first", state="not yet requested"):
    d = {"ID": i, "Subsystem": sub, "Component / assembly": comp, "Manufacturer": mfr, "Model / order code": model,
         "Qty": str(qty), "Selection status": sel, "Procurement status": "Not evidenced"}
    if pkg:
        d.update({"Purchase package": pkg, "Release status": rel, "Procurement state": state})
    else:
        d["Procurement state"] = "no purchase package (allocation or kit content)"
    return d


ADD = [
    row("LFT-001", "Lift sensing", "Lift stop sensors, one per stop (L1000, L1175, L1350)", "SICK", "IME12-04BNSZC0S, M12 inductive, NPN NO; always-on 24 V rail", 3, "Selected (P-03 rev20.0 item 24, LIFT-SNS-01 rev1)"),
    row("LFT-002", "Lift sensing", "Lift stop sensor cables", "SICK", "DOL-1204-G02M, M12 4-pin, 2 m", 3, "Selected"),
    row("LFT-003", "Lift sensing", "Lift stop sensor brackets in the static DOLD profile T-slot", "SICK", "BEF-WN-M12 (5308447)", 3, "Selected"),
    row("LFT-004", "Lift sensing", "Flag rod hanging from the adapter plate", "MISUMI", "5-series 20 x 20 profile, L 430 mm, M5 tapped", 1, "Selected"),
    row("LFT-005", "Lift sensing", "Rod corner bracket (anti-rotation)", "MISUMI", "20-series corner bracket", 1, "Selected"),
    row("LFT-006", "Lift sensing", "Steel flag for the stop sensors", "OpenAMRobot", "SS400 flag 45 x 20 x 2 mm", 1, "Specified (LIFT-SNS-01 rev1)"),
    row("LFT-007", "Lift sensing", "Lift sensor fastener set", "OpenAMRobot", "2 x M4 short nut, 2 x M4x8 ISO 7380, 1 x M5x20 ISO 4762, 3 x bracket screw plus T-nut", 1, "Specified (LIFT-SNS-01 rev1)"),
    row("AUX-002", "Upper-body auxiliary", "Head light low-side switching on the lift node", "OpenAMRobot", "Low-side switch channel on CTL-017 (no separate part)", 1, "Specified (P-03 rev20.2)", pkg=None),
    row("AUX-003", "Upper-body auxiliary", "Head light cable", "SICK", "DOL-0804-G02MRN, M8 4-pin, 2 m", 1, "Selected"),
    row("PWR-032", "Power", "3.3 V regulator for the four MB7060 sensors", "TBD", "3.3 V regulator, at least 300 mA, fed from the 5 V rail", 1, "Specified; SKU pending", pkg="BUY-20"),
]
EDIT = {
    "SAF-001": {"Qty": "2", "Component / assembly": "E-stop button assemblies: base front and static lift column",
                "Model / order code": "XB4BS8445 plus ZBE-102 (2NC + 1NO), one on the base front panel, one on the rear face of the static lift column"},
    "ARM-008": {"Qty": "0", "Selection status": "Withdrawn (P-03 rev20.0 item 24)",
                "Component / assembly": "Kit E-stop (ESTOP-KIT), withdrawn: the second robot button is SAF-001 on the static lift column"},
    "CTL-002": {"Qty": "0"},
    "AUX-001": {"Component / assembly": "Head light", "Manufacturer": "Falcon Illumination",
                "Model / order code": "FLDL-i150x15-W, 158 x 17 x 20 mm, 24 V 0.32 A, M8 4-pin; flat on an aluminium cooling plate, 30 mm below the Getac",
                "Selection status": "Selected (P-03 rev20.0 item 24)"},
    "MEC-018": {"Model / order code": "DOLD Hexalift V4 350, BS-HM240G350530-MFF24; 350 mm stroke; 530 mm retracted; 880 mm extended; 24 V; 800 N push; 400 N pull; 18 mm/s; 11.7 kg catalogue; 240 mm side fore-aft; written 800 N power-off holding confirmation received, delivered-unit holding test open"},
    "MEC-019": {"Qty": "1", "Model / order code": "6082-T6 plate 360 x 230 x 10 mm, positions bp000 and bp050; column to plate 4 x M8 DIN 7500 countersunk from below, at least 20 mm engagement; plate to deck 4 x M8 class 8.8 on a 190 x 300 mm pattern through the deck into the frame; plate not tapped"},
    "UI-002": {"Component / assembly": "Tablet mount, rotatable, two locked positions",
               "Model / order code": "Rotatable 2-position ZX80 mount: landscape default (234 wide x 149.8 tall), portrait (149.8 x 234); position from datums.yaml"},
}
BLOCK_ADD = {"LFT-001": "upper", "LFT-002": "upper", "LFT-003": "upper", "LFT-004": "upper", "LFT-005": "upper",
             "LFT-006": "upper", "LFT-007": "upper", "AUX-002": "upper", "AUX-003": "upper", "PWR-032": "sensors"}


def obj_span(s, name):
    i = s.index(name + "=") + len(name) + 1
    _, end = json.JSONDecoder().raw_decode(s, i)
    return i, end


def tr(p):
    pk = p.get("Purchase package")
    proc = "%s: %s" % (pk, p.get("Procurement state", "")) if pk else p.get("Procurement state", "")
    e = H.escape
    return ('<tr><td><code>%s</code></td><td>%s</td><td class="small">%s</td><td class="small">%s</td>'
            '<td class="small">%s</td><td class="small">%s</td></tr>') % (
        e(p["ID"]), e(p["Component / assembly"]), e(p["Model / order code"]), e(p["Qty"]), e(p["Selection status"]), e(proc))


def main():
    s = open(PAGE, encoding="utf-8").read()
    a, b = obj_span(s, "var PARTS")
    parts = json.loads(s[a:b])
    for r in ADD:
        parts.setdefault(r["ID"], r)
    for k, v in EDIT.items():
        parts[k].update(v)
    s = s[:a] + json.dumps(parts, ensure_ascii=False) + s[b:]
    a, b = obj_span(s, "BLOCK")
    blk = json.loads(s[a:b])
    blk.update({k: v for k, v in BLOCK_ADD.items() if k not in blk})
    s = s[:a] + json.dumps(blk, ensure_ascii=False) + s[b:]
    # per-block tables: rewrite edited rows, append new rows to their block table
    for k in list(EDIT) + [r["ID"] for r in ADD]:
        p = parts[k]
        m = re.search(r'<tr><td><code>%s</code></td>.*?</tr>' % re.escape(k), s)
        if m:
            s = s[:m.start()] + tr(p) + s[m.end():]
            continue
        b_id = "b-" + BLOCK_ADD.get(k, blk.get(k, "upper"))
        d = s.index('<details id="%s"' % b_id)
        t = s.index("</tbody>", d)
        s = s[:t] + tr(p) + s[t:]
    n = len([k for k in parts if re.match(r"^[A-Z]+(?:-[A-Z0-9]+)+$", k)])
    s = s.replace("The rows below are the BOM Issue 7.10 import and are not yet re-imported from BOM Issue 7.14. BOM Issue 7.10 has 136 component rows",
                  "The rows below are BOM %s. BOM Issue 7.14 has %d component rows" % (ISSUE, n))
    s = s.replace("Procurement state by purchase package (BOM Issue 7.10 import)", "Procurement state by purchase package (BOM Issue 7.14)")
    s = s.replace("The row, package and procurement counts on this page are from the BOM Issue 7.10 import (136 rows, 53 purchase packages; corrected 24 Oct) and are not yet re-imported.",
                  "The row, package and procurement counts on this page are BOM %s: %d records, 53 purchase packages." % (ISSUE, n))
    open(PAGE, "w", encoding="utf-8").write(s)
    print("PARTS records:", n)


if __name__ == "__main__":
    main()
