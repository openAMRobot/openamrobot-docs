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
Checks (the import stops on any of them): the sheet has the expected header, IDs match ID_RE and are unique, Qty is empty
or a number unless PAGE_OVERRIDE corrects it, and every page record is in the workbook or in PAGE_ONLY. The report lists
added, changed, removed and overridden records. JSON written into the page is escaped for the inline script (`</`).
Usage: python3 scripts/roadmap_model/bom715.py <BOM Issue 7.14.xlsx> <BOM Issue 7.15.xlsx> [docs/assets/roadmap/hardware.html]
"""
import json
import re
import sys

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


ID_RE = re.compile(r"^(?:[A-Z]{2,3}-\d{3}|F-[A-Z]+|FB-[A-Z])$")
# Records drawn on the page but not BOM lines (power-diagram nodes).
PAGE_ONLY = {"BAT", "SAFE"}
# Page corrections of workbook defects, each recorded in conflicts.yaml ("MEC-019 Qty cell").
PAGE_OVERRIDE = {
    "MEC-019": {
        "Qty": "1",
        "Model / order code": (
            "6082-T6, 350 x 140 x 10 mm, 8 x M8 tapped through. Joint 1, column to MEC-019: the DOLD foot tabs (260 x 30 mm) "
            "with 4 x DIN 7984 M8 x 14 8.8, no washer, medium threadlocker (LFT-008), screwed on the bench; 224 x 40 mm is "
            "DOLD-internal (D-20). Joint 2, MEC-019 to the centre-frame arch: column and plate go on as one unit and are bolted "
            "from above into the backing plate MEC-022 under the arch top sheet (D-21); service removes column and plate "
            "together at joint 2 (assembly order of 9 Nov 2026, P-03 rev20.6). Machining released only after the DOLD drawing "
            "and a dry fit."),
    },
}


class BomError(ValueError):
    pass


def check_rows(head, rows):
    """BOM records {ID: {field: text}} from the header and data rows of the Hardware BOM sheet; BomError on a bad sheet."""
    missing = [f for f in ("ID",) + FIELDS if f not in head]
    if missing:
        raise BomError("header lacks %s" % ", ".join(missing))
    out, errs = {}, []
    for r in rows:
        if not r or r[0] is None or str(r[0]).strip() == "":
            continue
        k = str(r[0]).strip()
        if not ID_RE.match(k):
            errs.append("%s: not a BOM ID" % k)
            continue
        if k in out:
            errs.append("%s: duplicate ID" % k)
            continue
        out[k] = {h: ("" if v is None else str(v).strip()) for h, v in zip(head, r)}
        q = PAGE_OVERRIDE.get(k, {}).get("Qty", out[k]["Qty"])
        if q and not re.fullmatch(r"\d+(?:\.\d+)?", q):
            errs.append("%s: Qty is not a number: %.40r" % (k, q))
    if errs:
        raise BomError("; ".join(errs))
    return out


def read_bom(path):
    import openpyxl   # only the import needs it (tests use check_rows)
    ws = openpyxl.load_workbook(path, data_only=True, read_only=True)["Hardware BOM"]
    rows = list(ws.iter_rows(values_only=True))
    hi = next(i for i, r in enumerate(rows) if r and r[0] == "ID")
    return check_rows([str(h) for h in rows[hi]], rows[hi + 1:])


def script_json(obj):
    """JSON for an inline <script>: no "</" (a "</script>" inside a string would end the script)."""
    return json.dumps(obj, ensure_ascii=False).replace("</", "<\\/")


def merge(parts, old, bom):
    """Update the page records from the workbook; returns the report {added, changed, removed, overridden}."""
    stray = sorted(k for k in parts if k not in bom and k not in PAGE_ONLY)
    if stray:
        raise BomError("page records not in the workbook and not in PAGE_ONLY: %s" % ", ".join(stray))
    rep = {"added": [], "changed": [], "removed": sorted(k for k in old if k not in bom), "overridden": []}
    for k, row in bom.items():
        if k not in parts:
            rep["added"].append(k)
        p = parts.setdefault(k, {"ID": k, "Procurement state": "not yet requested"})
        o = old.get(k)
        new = {f: public(row.get(f, "")) for f in FIELDS if o is None or o.get(f, "") != row.get(f, "") or f not in p}
        new.update(PAGE_OVERRIDE.get(k, {}))
        if k in PAGE_OVERRIDE:
            rep["overridden"].append(k)
        if any(p.get(f, "") != v for f, v in new.items()) and k not in rep["added"]:
            rep["changed"].append(k)
        p.update(new)
    return rep


def main():
    old, bom = read_bom(sys.argv[1]), read_bom(sys.argv[2])
    page = sys.argv[3] if len(sys.argv) > 3 else "docs/assets/roadmap/hardware.html"
    s = open(page, encoding="utf-8").read()
    a, b = obj_span(s, "var PARTS")
    parts = json.loads(s[a:b])
    rep = merge(parts, old, bom)
    changed = rep["added"] + rep["changed"]
    s = s[:a] + script_json(parts) + s[b:]
    a, b = obj_span(s, "BLOCK")
    blk = json.loads(s[a:b])
    blk.update({k: v for k, v in BLOCK_ADD.items() if k not in blk})
    s = s[:a] + script_json(blk) + s[b:]
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
    print("PARTS records from BOM 7.15:", n)
    for key in ("added", "changed", "removed", "overridden"):
        print("  %s (%d): %s" % (key, len(rep[key]), " ".join(rep[key])))


if __name__ == "__main__":
    main()
