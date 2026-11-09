"""Burn the caption line into the bottom of each still and write JPEG (quality 90, lowered in steps if over 1 MB).
python3 stills_caption.py <png dir> <jpeg out dir>"""
import glob
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont

CAPTION = "OpenAMRobot 2.0, roadmap model, simulation visualization"
FONT = "/usr/share/fonts/opentype/inter/Inter-Medium.otf"
src, dst = sys.argv[1], sys.argv[2]
os.makedirs(dst, exist_ok=True)
for f in sorted(glob.glob(os.path.join(src, "*.png"))):
    im = Image.open(f).convert("RGB")
    w, h = im.size
    d = ImageDraw.Draw(im, "RGBA")
    font = ImageFont.truetype(FONT, round(h * 0.022))
    band = round(h * 0.05)
    d.rectangle([0, h - band, w, h], fill=(21, 46, 69, 225))
    tw = d.textlength(CAPTION, font=font)
    d.text(((w - tw) / 2, h - band / 2), CAPTION, font=font, fill=(255, 255, 255, 255), anchor="lm")
    out = os.path.join(dst, os.path.basename(f)[:-4] + ".jpg")
    for q in (90, 88, 86, 84, 82):
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= 1_000_000:
            break
    open(out, "wb").write(buf.getvalue())
    print(os.path.basename(out), w, h, "q", q, buf.tell())
