"""Store pictures, thumbnails, contact sheets and posters (October method).
python3 pictures.py store <png dir>        JPEG q90 (under 1 MB) into media/store, thumbnails 640 x 360 / 512 x 640 q82,
                                           contact_sheet.jpg (1952 x 1242, captions as in October)
python3 pictures.py poster <png> <out.png> <colours>   palette-reduced PNG (192 for the posters, 128 for exploded-static)
python3 pictures.py thumb <png> <out.jpg>  640 px JPEG thumbnail q82 (store video poster on the page)
python3 pictures.py sheet <out.jpg> <title> <cols> <cell w> <img>...    contact sheet of any images (file names as captions)"""
import io
import os
import sys

from PIL import Image, ImageDraw, ImageFont

R = os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "docs", "assets", "roadmap", "media")
STORE = os.path.join(R, "store")
BOLD = "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf"
REG = "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf"
NAMES = [("01_aisle_follow", "1 Driving down the aisle (Follow view)"), ("02_pick_side", "2 Picking from a shelf"),
         ("03_place_tote", "3 Placing an item into a tote"), ("04_front_low", "4 Front three-quarter, low camera"),
         ("05_store_overview", "5 Store overview"), ("06_dock", "6 At the dock"),
         ("02_pick_side_1080x1350", "2 vertical 1080 x 1350"), ("04_front_low_1080x1350", "4 vertical 1080 x 1350")]


def jpeg(im, path, limit=1_000_000, q=90):
    while True:
        buf = io.BytesIO()
        im.save(buf, "JPEG", quality=q, optimize=True, progressive=True)
        if buf.tell() <= limit or q <= 70:
            break
        q -= 2
    open(path, "wb").write(buf.getvalue())
    return q, buf.tell()


def thumb(im):
    return im.resize((512, 640) if im.height > im.width else (640, 360), Image.LANCZOS)


def store(src):
    os.makedirs(os.path.join(STORE, "thumbs"), exist_ok=True)
    ims = {}
    for n, _ in NAMES:
        im = Image.open(os.path.join(src, n + ".png")).convert("RGB")
        ims[n] = im
        q, size = jpeg(im, os.path.join(STORE, n + ".jpg"))
        tq, tsize = jpeg(thumb(im), os.path.join(STORE, "thumbs", n + ".jpg"), q=82)
        print(n, im.size, "q", q, size, "thumb", tsize)
    W, H, gap, top = 1952, 1242, 8, 36
    sh = Image.new("RGB", (W, H), (246, 248, 247))
    d = ImageDraw.Draw(sh)
    d.text((gap, 8), "OpenAMRobot 2.0 grocery store, simulation visualization (robot page render mode, full look). Not real-robot footage.",
           font=ImageFont.truetype(BOLD, 21), fill=(20, 33, 32))
    f = ImageFont.truetype(REG, 18)
    for i, (n, cap) in enumerate(NAMES):
        col, row = i % 3, i // 3
        x, y = gap + col * 648, top + 8 + row * 398
        d.text((x, y), cap, font=f, fill=(20, 33, 32))
        t = ims[n].resize((288, 360) if ims[n].height > ims[n].width else (640, 360), Image.LANCZOS)
        sh.paste(t, (x + (640 - t.width) // 2, y + 26))
    print("contact sheet", jpeg(sh, os.path.join(STORE, "contact_sheet.jpg"), q=88))


def sheet(out, title, cols, cw, files):
    cols, cw = int(cols), int(cw)
    ims = [Image.open(p).convert("RGB") for p in files]
    ch = max(round(cw * im.height / im.width) for im in ims)
    gap, top, lab = 8, 40, 24
    rows = (len(ims) + cols - 1) // cols
    sh = Image.new("RGB", (gap + cols * (cw + gap), top + rows * (ch + lab + gap)), (246, 248, 247))
    d = ImageDraw.Draw(sh)
    d.text((gap, 10), title, font=ImageFont.truetype(BOLD, 20), fill=(20, 33, 32))
    f = ImageFont.truetype(REG, 15)
    for i, (p, im) in enumerate(zip(files, ims)):
        x, y = gap + (i % cols) * (cw + gap), top + (i // cols) * (ch + lab + gap)
        d.text((x, y), os.path.basename(p), font=f, fill=(20, 33, 32))
        t = im.resize((cw, round(cw * im.height / im.width)), Image.LANCZOS)
        sh.paste(t, (x, y + lab))
    print(out, sh.size, jpeg(sh, out, q=85))


if __name__ == "__main__":
    a = sys.argv
    if a[1] == "store":
        store(a[2])
    elif a[1] == "poster":
        Image.open(a[2]).convert("RGB").quantize(colors=int(a[4]), method=Image.MEDIANCUT, dither=Image.NONE).save(a[3], optimize=True)
        print(a[3], os.path.getsize(a[3]))
    elif a[1] == "thumb":
        print(a[3], jpeg(thumb(Image.open(a[2]).convert("RGB")), a[3], q=82))
    elif a[1] == "sheet":
        sheet(a[2], a[3], a[4], a[5], a[6:])
