#!/usr/bin/env python3
"""Add the "Video and pictures" section below the 3D view of docs/assets/roadmap/robot.html (one replacement,
must match once). Duration and size of the video are passed in; the pictures are listed in PICTURES.

Usage: python3 add_media_section.py docs/assets/roadmap/robot.html <duration s> <video bytes> <fps> <speed> <sim s>
"""
import sys

path, dur, size, fps, speed, sim = sys.argv[1], float(sys.argv[2]), int(sys.argv[3]), sys.argv[4], sys.argv[5], float(sys.argv[6])
PICTURES = [
    ("01_aisle_follow", "Driving down the aisle, seen from behind and above (Follow view)"),
    ("02_pick_side", "Arm reaching into a shelf to pick an item, close view from across the aisle"),
    ("03_place_tote", "Arm placing an item into a tote"),
    ("04_front_low", "In the aisle, front three-quarter, low camera, totes visible"),
    ("05_store_overview", "Overview of the store with the robot in an aisle"),
    ("06_dock", "Robot at the dock after the run"),
    ("02_pick_side_1080x1350", "Picking from a shelf, vertical 1080 x 1350"),
    ("04_front_low_1080x1350", "Front three-quarter, low camera, vertical 1080 x 1350"),
]
html = open(path, encoding="utf-8").read()
items = "".join(
    '<li><a href="media/store/%s.jpg"><img data-src="media/store/thumbs/%s.jpg" alt="%s (simulation visualization)" width="%d" height="%d" loading="lazy" decoding="async"></a><span>%s</span></li>'
    % (n, n, t, 640 if "1350" not in n else 512, 360 if "1350" not in n else 640, t) for n, t in PICTURES)
section = (
    '<main class="rm" style="padding-top:16px"><section class="card" id="media"><h2>Video and pictures</h2>'
    '<style>#media video{display:block;width:100%%;max-width:960px;height:auto;aspect-ratio:16/9;background:#1b2530;border-radius:6px}'
    '#media ul{list-style:none;padding:0;margin:12px 0 0;display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:12px}'
    '#media li{margin:0;min-width:0}#media img{display:block;width:100%%;height:auto;border-radius:4px;background:#e7ebe9}'
    '#media li span{display:block;font-size:12px;color:var(--mute);margin-top:4px}</style>'
    '<p class="small mute">Simulation visualization, rendered offline from this page: one "Run order (8 items)" run of the 3D view above '
    '(pick from the shelves into the totes, unload, back to the dock), the same robot model, store and full look. Not footage of the '
    'real robot and not evidence of its behaviour; the pick sequence is an illustration (3.0 scope store, 2.0 is built for Use Case 1).</p>'
    '<video id="store-video" controls preload="none" playsinline poster="media/store/thumbs/store_video_poster.jpg" width="1920" height="1080">'
    '<source src="media/openamrobot-2-store-1080p.mp4" type="video/mp4"></video>'
    '<p class="small mute">Store run: 1920 x 1080, %s fps, H.264, no audio, %.1f s, %.1f MB; played at %sx speed, %.1f s of simulated time in %.1f s of video. The camera follows the robot with short cuts to the side view at each pick. '
    'Download: <a href="media/openamrobot-2-store-1080p.mp4" download>store video (MP4)</a>, '
    '<a href="media/openamrobot-2-store-1080p-poster.png">poster (PNG)</a>, '
    '<a href="media/store/contact_sheet.jpg">all pictures on one sheet (JPEG)</a>.</p>'
    '<ul aria-label="Pictures of the store simulation">%s</ul>'
    '<p class="small mute">Pictures: 1920 x 1080 (two also 1080 x 1350), JPEG, from the same render mode; select a thumbnail for the full picture.</p>'
    # thumbnails get their src only when the grid comes within 200 px of the viewport (loading="lazy" alone
    # starts far earlier and would add every thumbnail to the first load)
    '<script>(function(){var im=[].slice.call(document.querySelectorAll("#media img[data-src]"));'
    'function show(i){i.src=i.getAttribute("data-src");i.removeAttribute("data-src")}'
    'if(!("IntersectionObserver" in window)){im.forEach(show);return}'
    'var o=new IntersectionObserver(function(es){es.forEach(function(e){if(e.isIntersecting){show(e.target);o.unobserve(e.target)}})},{rootMargin:"200px"});'
    'im.forEach(function(i){o.observe(i)})})();</script>'
    '</section></main>\n') % (fps, dur, size / 1e6, speed, sim, dur, items)
start = '<main class="rm" style="padding-top:16px"><section class="card" id="media">'
if start in html:  # replace an earlier version of the section
    i = html.index(start)
    html = html[:i] + html[html.index('</section></main>\n', i) + len('</section></main>\n'):]
old = '</div>\n<main class="rm" style="padding-top:16px"><section class="card" id="config">'
if html.count(old) != 1:
    sys.exit("anchor not found once")
html = html.replace(old, '</div>\n' + section + '<main class="rm" style="padding-top:16px"><section class="card" id="config">')
open(path, "w", encoding="utf-8").write(html)
print("page %d bytes" % len(html.encode("utf-8")))
