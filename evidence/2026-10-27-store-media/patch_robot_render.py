#!/usr/bin/env python3
"""Offline render mode for docs/assets/roadmap/robot.html (after patch_robot_defaults.py of
evidence/2026-10-26-shared-model). Every replacement must match exactly once.

robot.html?render=1&frame=N&w=W&h=H&fps=F&speed=K&cam=C: frame N of one "Run order (8 items)" run at sim time
N / F x K, no page UI, camera tiles, Frames and Labels off, full look (model/look.js), deterministic:
- a seeded Math.random is installed before any script runs (the GTAO noise texture of the store page asks
  Math.random for its values);
- the realtime loop (wall-clock playback and rendering) does not run; frames are rendered on request;
- the camera of a frame is a function of the sim time only.
window.__renderFrame(n) and window.__renderAt(t, cam) return PNG (or JPEG) data URLs; window.__store gives fps,
speed, frame count and the pick and place times. scripts/render_store.js drives it.

Usage: python3 patch_robot_render.py docs/assets/roadmap/robot.html
"""
import sys

path = sys.argv[1]
html = open(path, encoding="utf-8").read()


def sub(old, new):
    global html
    n = html.count(old)
    if n != 1:
        sys.exit("expected one match, found %d: %s" % (n, old[:80]))
    html = html.replace(old, new)


HEAD = ("<script>/* render mode (robot.html?render=1): seeded Math.random before any other script, no realtime loop */"
        "if(/[?&]render=1(&|$)/.test(location.search)){window.__renderMode=!0;(function(){var s=20261027;"
        "Math.random=function(){s=s*16807%2147483647;return(s-1)/2147483646}})()}</script>")
sub("<head>", "<head>\n" + HEAD)
sub("function Wh(s){requestAnimationFrame(Wh);", "function Wh(s){if(window.__renderMode)return;requestAnimationFrame(Wh);")
sub("player:_s,MTX:Ct,LOCS:Sr}", "player:_s,MTX:Ct,LOCS:Sr,order:()=>Fh()}")
CTRL = open(sys.argv[2] if len(sys.argv) > 2 else __file__.replace("patch_robot_render.py", "render_mode.js"), encoding="utf-8").read()
sub("</body>", "<script>\n" + CTRL.strip() + "\n</script>\n</body>")
open(path, "w", encoding="utf-8").write(html)
print("page %d bytes" % len(html.encode("utf-8")))
