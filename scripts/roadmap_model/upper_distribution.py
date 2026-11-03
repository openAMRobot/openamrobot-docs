#!/usr/bin/env python3
"""Upper distribution enclosure: evaluation (Phase 4c, 3 Nov 2026), not added automatically.

Compares a compact upper enclosure (DC/DC, USB hub, low-voltage distribution) near the second E-stop or between the arm bases
with direct connections from the base, from a load table of documented values (no value is sized from a guess: a load
without a document is marked "verify") and from the USB lengths along the routed paths (cable_list.csv, lift travel included in
the energy-chain length). Writes a JSON report (argument 1) and prints the decision.
"""
import csv
import json
import os
import sys

from frames import MODEL

LOADS = [  # device, supply, operating, peak, source
    {"device": "Head light Falcon FLDL-i150x15-W", "supply": "24 V (F-PANEL via the lift node low-side switch)", "operating": "0.32 A at 24 V (7.7 W)", "peak": "verify (inrush)",
     "source": "docs general-arrangement (P-03 rev20.2 values): 0.32 A at 24 V", "cable": "CBL-P24"},
    {"device": "Getac ZX80 USB-C PD", "supply": "24 V into the USB-PD module PWR-008 in the base, USB-C PD to the tablet", "operating": "15 to 30 W PD (module rating)", "peak": "30 W PD; 3 A F-PANEL fuse on the 24 V side",
     "source": "BOM Issue 7.14 PWR-008 (24 V in, USB-C PD 15 to 30 W); E-01 rev1.6 F-PANEL 3 A", "cable": "CBL-P23"},
    {"device": "ZED Mini", "supply": "USB 3 bus power from the powered hub CMP-009", "operating": "verify (Stereolabs datasheet: USB bus powered)", "peak": "verify",
     "source": "Stereolabs ZED Mini datasheet (not in the repositories): verify", "cable": "CBL-P49"},
    {"device": "Wrist cameras (2)", "supply": "USB from the hub through the matched gripper-camera harness", "operating": "verify", "peak": "verify",
     "source": "BOM Issue 7.14 ARM-010 (matched harness); no current documented", "cable": "CBL-P52, CBL-P53"},
    {"device": "Arms (logic and motors), 2", "supply": "SAFE bus F-ARM-L / F-ARM-R 30 A each, 6 mm²", "operating": "verify (OpenArm documentation)", "peak": "fuse 30 A per arm",
     "source": "E-01 rev1.6 fuse schedule (F-ARM-L, F-ARM-R 30 A)", "cable": "CBL-P14, CBL-P15"},
    {"device": "Arm USB-to-CAN-FD adapters (2)", "supply": "USB bus power in the base (right side zone)", "operating": "verify", "peak": "verify",
     "source": "BOM Issue 7.14 ARM-006", "cable": "CBL-P50, CBL-P51"},
    {"device": "Second E-stop (2NC)", "supply": "hardwired safety loop to the PNOZ s3 (series with the base E-stop)", "operating": "safety loop current per PNOZ s3", "peak": "-",
     "source": "E-01 rev1.6; SAFETY-PROCUREMENT", "cable": "CBL-P33"},
]
USB_LIMIT_M = 3.0   # practical passive USB 3 (5 Gbit/s) cable length; working value, verify with the ZED Mini interface sheet
PD_LIMIT_M = 4.0    # USB Type-C specification: USB 2.0 C-to-C cable (PD) at most 4 m


def main(out=None):
    rows = {r["id"]: r for r in csv.DictReader(open(os.path.join(MODEL, "cable_list.csv"), encoding="utf-8"))}
    H = json.load(open(os.path.join(MODEL, "harness_routes.json"), encoding="utf-8"))
    ch = H["chain"]
    bundle = ch.get("bundle", {})
    usb = []
    for cid in ("CBL-P49", "CBL-P52", "CBL-P53", "CBL-P23", "CBL-P58"):
        r = rows.get(cid)
        if not r or not r["route_length_m"]:
            usb.append({"id": cid, "length_m": None, "ok": None})
            continue
        L = float(r["length_with_margin_m"])
        usb.append({"id": cid, "function": r["function"], "route_m": float(r["route_length_m"]), "with_service_margin_m": L, "connectors": "%s / %s" % (r["connector_a"], r["connector_b"]),
                    "limit_m": PD_LIMIT_M if "PD" in r["gauge_or_type"] else USB_LIMIT_M,
                    "ok": L <= (PD_LIMIT_M if "PD" in r["gauge_or_type"] else USB_LIMIT_M)})
    decision = {
        "adopted": False,
        "decision": "No upper distribution enclosure: every upper load is fed directly from the base. The documented upper loads are small (head light 0.32 A at 24 V, Getac PD at most 30 W through the base USB-PD module); the arm power (2 x 6 mm², F-ARM 30 A) and the hardwired second E-stop loop pass the chain in any case, so an enclosure would not remove the larger cables from the chain; it would add a DC/DC converter and a hub (heat and mass) on the moving stage between the arm bases. USB lengths along the routes (lift travel included in the chain length, 10 % service margin): the ZED Mini (CBL-P49) and the wrist-camera leads (CBL-P52, CBL-P53) reach or exceed the 3 m working limit of a passive USB 3 cable, so they are specified as active (repeater) USB 3 cables, powered from the base hub (verify with Stereolabs and the gripper-camera supplier); a powered USB 3 hub on the moving stage is the fallback if active cables are not accepted. The Getac USB-C PD cable stays within the 4 m Type-C limit. Revisit if the wrist-camera or arm-logic currents (verify) need a local supply.",
        "chain_fill_pct": bundle.get("fill_pct"), "chain_cables": bundle.get("count"), "chain_length_m": ch.get("length"),
        "usb": usb, "loads": LOADS,
        "estop": "The second E-stop stays hardwired (2NC loop CBL-P33 in series with the base E-stop into the PNOZ s3); never USB or software.",
    }
    if out:
        json.dump(decision, open(out, "w"), indent=1)
    print(json.dumps({k: decision[k] for k in ("adopted", "chain_fill_pct", "usb")}, indent=1))
    return decision


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else None)
