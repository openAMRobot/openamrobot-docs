#!/usr/bin/env python3
"""Side-by-side before / after sheets of review renders: before_after.py <before dir> <after dir> <out dir> name_before:name_after:title ..."""
import os
import sys

from PIL import Image, ImageDraw, ImageFont


def sheet(a, b, title, out):
    A, B = Image.open(a).convert("RGB"), Image.open(b).convert("RGB")
    h = max(A.height, B.height)
    W = A.width + B.width + 30
    S = Image.new("RGB", (W, h + 70), "white")
    S.paste(A, (0, 70))
    S.paste(B, (A.width + 30, 70))
    d = ImageDraw.Draw(S)
    try:
        f = ImageFont.truetype("DejaVuSans-Bold.ttf", 30)
        f2 = ImageFont.truetype("DejaVuSans.ttf", 24)
    except OSError:
        f = f2 = ImageFont.load_default()
    d.text((14, 8), title, fill="#1d2733", font=f)
    d.text((14, 42), "Before (main e074e68)", fill="#c0392b", font=f2)
    d.text((A.width + 44, 42), "After (this PR)", fill="#117a65", font=f2)
    d.line([(A.width + 15, 70), (A.width + 15, h + 70)], fill="#9aa3ab", width=3)
    S.save(out, optimize=True)


if __name__ == "__main__":
    bd, ad, od = sys.argv[1:4]
    os.makedirs(od, exist_ok=True)
    for spec in sys.argv[4:]:
        nb, na, title = spec.split(":", 2)
        sheet(os.path.join(bd, nb + ".png"), os.path.join(ad, na + ".png"), title, os.path.join(od, "compare_" + na + ".png"))
        print("wrote compare_" + na)
