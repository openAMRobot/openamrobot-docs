#!/usr/bin/env python3
"""Third step on docs/assets/roadmap/robot.html (after patch_robot_look.py). Every replacement must match once.

- both OpenArm 2.0 arms keep the as-delivered arm material: the page no longer swaps the working arm to a
  blue-emissive highlight material (it read lavender under the store lights); the "Working arm" legend
  chip that described that tint is removed;
- page defaults: view preset Follow, Frames off, Labels off (the buttons still switch them on);
  High quality, the probe and ?look= are unchanged.

Usage: python3 patch_robot_defaults.py docs/assets/roadmap/robot.html
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


sub("kc=z0.arm,mh=z0.armHi,", "kc=z0.arm,")
sub("n=e===s?mh:kc;", "n=kc;")
sub('<span style="--c:#2a5bd7">Working arm</span>', "")
sub('view:"over",', 'view:"follow",')
sub('P2("over")', 'P2("follow")')
sub('<button data-view="over" class="on">', '<button data-view="over">')
sub('<button data-view="follow">', '<button data-view="follow" class="on">')
sub("var fs=!0;$e.layers.enable(2);", "var fs=!1;")
sub("vr=!0,Xo=", "vr=!1,Xo=")
sub('<button id="b-frames" class="on" aria-pressed="true">', '<button id="b-frames" aria-pressed="false">')
sub('<button id="b-labels" class="on" aria-pressed="true">', '<button id="b-labels" aria-pressed="false">')
open(path, "w", encoding="utf-8").write(html)
print("page %d bytes" % len(html.encode("utf-8")))
