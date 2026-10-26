#!/usr/bin/env python3
"""Second migration step of docs/assets/roadmap/robot.html (after split_robot_bundle.py): calibrated look
and the light-look fallback from model/look.js. Every replacement must match exactly once.

- robot materials take the calibrated environment intensity (OAMR_LOOK.CAL.robot), exposure from CAL;
- the existing High quality toggle also switches the robot between the full and the light look;
- the first 30 frames are probed (rendered every frame); over 33 ms on average: light look;
  ?look=full or ?look=light forces a look and skips the probe;
- the arm highlight picks the material of the current look.

Usage: python3 patch_robot_look.py docs/assets/roadmap/robot.html
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


L = "window.OAMR_LOOK"
sub("OB=window.OAMR_MODEL.build(jn,{fittings:!0,headPitch:0}),z0=OB.mats;",
    "OB=window.OAMR_MODEL.build(jn,{fittings:!0,headPitch:0}),z0=OB.mats;%s.robotEnv(OB.root,%s.CAL.robot);"
    "function OBlook(e){%s.lightLook(jn,OB.root,e,{contact:!0}),dt=!0}" % (L, L, L))
sub("r.material=n", "r.material=%s.pick(n)" % L)
sub('C0.hq=!C0.hq,s.target.classList.toggle("on",C0.hq),i3(),dt=!0',
    'C0.hq=!C0.hq,s.target.classList.toggle("on",C0.hq),i3(),OBlook(!C0.hq),dt=!0')
sub("Rt.update()&&(dt=!0),dt&&(dt=!1,n3())", "Rt.update()&&(dt=!0),(dt||%s.probing())&&(dt=!1,n3(),%s.frame(s))" % (L, L))
sub("window.OAMR_LOOK.apply(jn,he,{exposure:1.05});", "%s.apply(jn,he,{exposure:%s.CAL.robot.exposure});" % (L, L))
sub("requestAnimationFrame(Wh);location",
    "requestAnimationFrame(Wh);(function(){var f=%s.forced();f?f===\"light\"&&OBlook(!0):"
    "%s.startProbe(function(m){m>%s.FRAME_BUDGET_MS&&OBlook(!0)})})();location" % (L, L, L))
open(path, "w", encoding="utf-8").write(html)
print("page %d bytes" % len(html.encode("utf-8")))
