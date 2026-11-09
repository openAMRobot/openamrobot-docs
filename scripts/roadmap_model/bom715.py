#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""Re-import the Hardware BOM sheet of BOM Issue 7.15 (8 Nov 2026) into hardware.html.

The PARTS records (embedded JSON) take the BOM fields of the Hardware BOM sheet; the page-only fields (purchase package,
release status, procurement state) are kept. New records are added to their block table. Idempotent.
The workbook is not in the repository (internal plan-set file); pass its path. Only the Hardware BOM sheet is read: the
Overview header still says Issue 7.14 and the Mechanical sheet still describes the old lift plate, both recorded as drift.
Only fields that differ between Issue 7.14 and 7.15 are taken from the workbook; the other fields keep the page text,
which was edited for publication. Text taken from the workbook passes `public()` (no seller names, prices, first names
or partner names; see check_roadmap.py FORBIDDEN). Rows whose text differs from the record are rewritten.
Usage: python3 scripts/roadmap_model/bom715.py <BOM Issue 7.14.xlsx> <BOM Issue 7.15.xlsx> [docs/assets/roadmap/hardware.html]
"""
import json
import re
import sys

import openpyxl

from bom714 import obj_span, tr

ISSUE = "Issue 7.15 (8 Nov 2026)"
FIELDS = ("Subsystem", "Component / assembly", "Manufacturer", "Model / order code", "Qty", "Selection status", "Procurement status")
BLOCK_ADD = {"LFT-008": "upper", "MEC-022": "upper"}
SELLERS = r"Digi-?Key|Mouser|OpenELAB|Farnell|element14|RS Components|Conrad|Reichelt|AliExpress|Amazon|TME|Botland|Robotshop"
NAMES = {"Alex": "the project lead", "Evans": "the electrical and firmware lead", "Kunal": "the navigation lead",
         "Mohamed": "the tech lead", "Cuma": "the mechanical owner"}
for _n in ("Anushka", "Pragati", "Majd", "Karthikeyan", "Satya", "Anand"):
    NAMES[_n] = "the owner"


def public(t):
    """Workbook text made fit for the public page: prices, seller names, first names and partner names removed."""
    t = re.sub(r",?\s*(?:about|approx\.?|ca\.?)?\s*\d[\d,.]*\s?(?:EUR|USD|GBP)\b", "", t)
    t = re.sub(r"(?:EUR|USD|GBP|[\u20ac$\u00a3])\s?\d[\d,.]*", "", t)
    t = re.sub(r"\((?:RS|DigiKey|Mouser)\s+[\w-]+\s*\)", "", t)
    t = re.sub(r"\bRS\s+\d{3}-\d{3,4}\b,?\s*", "", t)
    t = re.sub(r"\b(?:%s)\b" % SELLERS, "a distributor", t)
    for k, v in NAMES.items():
        t = re.sub(r"\b%s\b" % k, v, t)
    t = re.sub(r"[^.;]*\b(?:Enactic|Reazon|PAIA)\b[^.;]*[.;]?\s*", "", t, flags=re.I)
    t = re.sub(r"\(\s*\)", "", t)
    return re.sub(r"\s{2,}", " ", t).strip(" ;,")


def read_bom(path):
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["Hardware BOM"]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "ID")
    head = [str(h) for h in rows[hi]]
    out = {}
    for r in rows[hi + 1:]:
        if r and r[0]:
            out[str(r[0]).strip()] = {h: ("" if v is None else str(v).strip()) for h, v in zip(head, r)}
    return out


def main():
    old, bom = read_bom(sys.argv[1]), read_bom(sys.argv[2])
    page = sys.argv[3] if len(sys.argv) > 3 else "docs/assets/roadmap/hardware.html"
    s = open(page, encoding="utf-8").read()
    a, b = obj_span(s, "var PARTS")
    parts = json.loads(s[a:b])
    changed = []
    for k, row in bom.items():
        p = parts.setdefault(k, {"ID": k, "Procurement state": "not yet requested"})
        o = old.get(k)
        new = {f: public(row.get(f, "")) for f in FIELDS if o is None or o.get(f, "") != row.get(f, "") or f not in p}
        if any(p.get(f, "") != v for f, v in new.items()):
            changed.append(k)
        p.update(new)
    s = s[:a] + json.dumps(parts, ensure_ascii=False) + s[b:]
    a, b = obj_span(s, "BLOCK")
    blk = json.loads(s[a:b])
    blk.update({k: v for k, v in BLOCK_ADD.items() if k not in blk})
    s = s[:a] + json.dumps(blk, ensure_ascii=False) + s[b:]
    for k in parts:
        m = re.search(r'<tr><td><code>%s</code></td>.*?</tr>' % re.escape(k), s)
        if k not in changed and m and m.group(0) != tr(parts[k]):
            changed.append(k)
    for k in changed:
        m = re.search(r'<tr><td><code>%s</code></td>.*?</tr>' % re.escape(k), s)
        if m:
            s = s[:m.start()] + tr(parts[k]) + s[m.end():]
            continue
        d = s.index('<details id="b-%s"' % blk.get(k, "upper"))
        t = s.index("</tbody>", d)
        s = s[:t] + tr(parts[k]) + s[t:]
    n = len([k for k in parts if k in bom])
    s = re.sub(r"The rows below are BOM Issue 7\.1[45][^.]*?\. BOM Issue 7\.1[45] has \d+ component rows",
               "The rows below are BOM %s. BOM Issue 7.15 has %d component rows" % (ISSUE, n), s)
    s = s.replace("Procurement state by purchase package (BOM Issue 7.14)", "Procurement state by purchase package (BOM Issue 7.15)")
    s = re.sub(r"The row, package and procurement counts on this page are BOM Issue 7\.1[45][^:]*: \d+ records",
               "The row, package and procurement counts on this page are BOM %s: %d records" % (ISSUE, n), s)
    open(page, "w", encoding="utf-8").write(s)
    print("PARTS records from BOM 7.15:", n, "changed or added:", len(changed))


if __name__ == "__main__":
    main()
