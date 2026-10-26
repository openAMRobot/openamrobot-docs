#!/usr/bin/env python3
"""One-off migration of docs/assets/roadmap/robot.html (kept as evidence; run once on the #56 page).

The page carried one inline esbuild bundle: three.js r160 core, seven three.js addons and the page
application. This script keeps the application only, binds the three.js names it uses to window.THREE
(model/three-r160.min.js and, for the store addons, model/three-r160-store.min.js), and replaces the
in-page robot construction, robot materials and renderer look with model/model.js (OAMR_MODEL.build)
and model/look.js (OAMR_LOOK). Every replacement must match exactly once.

Usage: NODE_PATH=<node_modules with espree and eslint-scope> python3 split_robot_bundle.py docs/assets/roadmap/robot.html
"""
import json
import os
import re
import subprocess
import sys
import tempfile

path = sys.argv[1]
html = open(path, encoding="utf-8").read()
start = html.index("<script>(()=>{var Jh=")
end = html.index("</script>", start) + len("</script>")
bundle = html[start + len("<script>"):end - len("</script>")]

# 1. the three.js namespace object of the bundle: export name -> minified identifier
ns = bundle[bundle.index("jh(jn,{") + 7:bundle.index("});", bundle.index("jh(jn,{"))]
exports = {m.group(2): m.group(1) for m in re.finditer(r"(\w+):\(\)=>([\w$]+)", ns)}

# 2. application segments: from the first app module (spec, "var En=") to the end, without the two
#    addon modules esbuild placed between app modules (BufferGeometryUtils, RoundedBoxGeometry)
a0 = bundle.index("var En=Math.PI/180,d0=window.OAMR_MODEL.DIMS")
k0 = bundle.index("function Kn(s,e=!1){", a0)       # mergeGeometries ...
k1 = bundle.index("var m2=11,Ee=()=>", k0)           # ... and mergeAttributes end here
r0 = bundle.index("var zo=new A;function Kt(", k1)   # RoundedBoxGeometry module ...
r1 = bundle.index("var ot=(s,e,t)=>new A(", r0)       # ... ends here
tail = bundle.rindex("})();")
app = bundle[a0:k0] + bundle[k1:r0] + bundle[r1:tail]

# 3. names the application takes from three.js: core exports and addons
addons = {"s2": "OrbitControls", "r2": "RoomEnvironment", "l2": "EffectComposer", "c2": "RenderPass", "Bo": "GTAOPass",
          "f2": "OutputPass", "d2": "RectAreaLightUniformsLib", "Kn": "mergeGeometries", "x2": "RoundedBoxGeometry"}
used = sorted({i for i in exports if re.search(r"(?<![\w$.])%s(?![\w$])" % re.escape(i), app)} | set(addons))
bind = ["jn=window.THREE"] + ["%s=jn.%s" % (i, addons.get(i) or exports[i]) for i in used]

# 4. robot construction, materials and look from the shared model
def sub(old, new):
    global app
    n = app.count(old)
    if n != 1:
        sys.exit("expected one match, found %d: %s" % (n, old[:80]))
    app = app.replace(old, new)

sub("Oam=Object.assign({},jn,{RoundedBoxGeometry:x2}),z0=window.OAMR_MODEL.materials(jn);",
    "OB=window.OAMR_MODEL.build(jn,{fittings:!0,headPitch:0}),z0=OB.mats;")
sub("var Bc=window.OAMR_MODEL.armGeometries(jn),kc=z0.arm", "var kc=z0.arm")
sub('this.g=new ve,this.g.name="OpenAMRobot",e.add(this.g)', "this.g=OB.root,e.add(this.g)")
sub("this.buildFrames(),this.setBP(", "this.buildFrames(),window.OAMR_MODEL.prepare(jn,this.g),this.setBP(")
# buildChassis: the base and its fittings come from OB; the page keeps the base camera frame pivot
c0 = app.index("buildChassis(){")
c1 = app.index("buildColumn(){", c0)
app = app[:c0] + ("buildChassis(){let e=this.g,t=d0;this.baseCad=OB.base,this.gemini=new ve,"
                  "this.gemini.position.set(t.GEMINI.x,0,t.BASE_LINK_Z+t.GEMINI.z),e.add(this.gemini)}") + app[c1:]
# buildColumn: lift assembly, stage, head pivot, upper body and fittings from OB
c0 = app.index("buildColumn(){")
c1 = app.index("buildTotes(){", c0)
app = app[:c0] + ("buildColumn(){this.colAsm=OB.col,this.mov=OB.mov,this.zed=OB.zed,this.ubParts=OB.parts;"
                  "let c=d0.PLATE_TOP+d0.COL.RETRACTED;this.zedTop=c+d0.MOUNT_ABOVE_COL+d0.ZED_ABOVE_SH,"
                  "this.carriageZ=c,this.cable=OB.fit.cable}") + app[c1:]
# buildArms: link groups and wrist camera bodies from OB; the page keeps its kinematics
sub("this.arm={};let e=t=>{let n=new ve;if(n.matrixAutoUpdate=!1,t&&Bc[t.key]){let i=new b0(Bc[t.key],kc);"
    "i.castShadow=!0,i.receiveShadow=!0,i.matrix.copy(y2(t.xyz,t.rpy)).multiply(new y0().makeScale(t.scale[0],t.scale[1],t.scale[2])),"
    "i.matrixAutoUpdate=!1,n.add(i)}return this.g.add(n),n};",
    "this.arm={};")
sub("gBase:e(n.base_visual),gLinks:n.joints.map(i=>e(i.visual)),fingers:n.fingers.map(i=>({T:y2(i.xyz,i.rpy),"
    "axis:ot(...i.axis).normalize(),lo:i.lo,hi:i.hi,g:e(i.visual)}))",
    "gBase:OB.arms[t].gBase,gLinks:OB.arms[t].gLinks,fingers:n.fingers.map((i,j)=>({T:y2(i.xyz,i.rpy),"
    "axis:ot(...i.axis).normalize(),lo:i.lo,hi:i.hi,g:OB.arms[t].fingers[j].g}))")
sub("let o=new ve;o.matrixAutoUpdate=!1;let a=new b0(new Ie(.018,.018,.012),z0.black);a.position.z=.006,o.add(a),this.g.add(o),this.wrist[t]={side:n,T:r,g:o}",
    "this.wrist[t]={side:n,T:r,g:OB.fit.wrist[n]}")
# the decal texture of the robot page fittings moved to model.js with them
d0_ = app.index("function lh(){return Ye(1024,128,")
app = app[:d0_] + app[app.index("function ch(", d0_):]
# lift cable geometry from the model
u0 = app.index("updateCable(){")
u1 = app.index("setPose(", u0)
app = app[:u0] + "updateCable(){this.cable.geometry.dispose(),this.cable.geometry=window.OAMR_MODEL.cableGeometry(jn,this.colTop())}" + app[u1:]
# renderer look and environment from model/look.js; the store lights stay
sub("he.toneMapping=pr;he.toneMappingExposure=1.05;he.outputColorSpace=Pe;he.shadowMap.enabled=!0;he.shadowMap.type=X1;",
    "window.OAMR_LOOK.apply(jn,he,{exposure:1.05});")
sub("var Sm=new $i(he);at.environment=Sm.fromScene(new r2(he),.04).texture;", "at.environment=window.OAMR_LOOK.environment(jn,he);")

# bind exactly the names the application leaves unresolved (freevars.cjs), all of them from three.js
with tempfile.NamedTemporaryFile("w", suffix=".js", delete=False) as f:
    f.write(app)
free = set(json.loads(subprocess.check_output(["node", os.path.join(os.path.dirname(os.path.abspath(__file__)), "freevars.cjs"), f.name])))
os.unlink(f.name)
names = {b.split("=")[0]: b for b in bind[1:]}
used2 = [names[n] for n in sorted(free) if n in names]
glob = {"Array", "Blob", "Boolean", "Event", "Float32Array", "Float64Array", "Map", "Math", "MediaRecorder", "Object",
        "ResizeObserver", "String", "URL", "Uint8Array", "atob", "document", "location", "performance",
        "requestAnimationFrame", "setTimeout", "window", "jn"}
left = sorted(free - set(names) - glob)
if left:
    sys.exit("unresolved names: %s" % left)
script = "<script>(()=>{var %s;%s})();</script>" % (",".join(bind[:1] + used2), app)
libs = ('<script src="model/three-r160.min.js"></script><script src="model/three-r160-store.min.js"></script>'
        '<script src="model/look.js"></script>')
html = html[:start] + libs + script + html[end:]
open(path, "w", encoding="utf-8").write(html)
print("app %d bytes, %d three.js bindings, page %d bytes" % (len(app), len(used2), len(html.encode("utf-8"))))
