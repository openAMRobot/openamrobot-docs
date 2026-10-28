// node collide_rf.js <out.json>: robot.html order run (render mode, speed 4, 24 fps); every 10th frame, the bounding box in the
// robot frame (precise, per vertex; axes of the robot, so a turn of the robot does not grow the boxes) of each arm link mesh against the second E-stop and each chest item (second_estop, getac_tablet, head_light); overlaps reported.
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 640, height: 360 } }); p.setDefaultTimeout(1800000);
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto('http://localhost:8765/' + (process.argv[3] || 'robot.html') + '?render=1&w=640&h=360&fps=24&speed=4&cam=auto#nomtx', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => window.__frameReady === true);
  const res = await p.evaluate(() => {
    const S = window.__sim, THREE = S.THREE, R = S.robot, st = window.__store, out = [], fps = st.fps, sp = st.speed;
    const inv = new THREE.Matrix4(), m = new THREE.Matrix4(), v = new THREE.Vector3();
    const rbox = obj => { const b = new THREE.Box3(); obj.traverse(o => { if (!o.isMesh) return; m.multiplyMatrices(inv, o.matrixWorld);
      const p = o.geometry.attributes.position; for (let i = 0; i < p.count; i++) b.expandByPoint(v.fromBufferAttribute(p, i).applyMatrix4(m)); }); return b; };
    const names = ['base', 'link1', 'link2', 'link3', 'link4', 'link5', 'link6', 'link7'];
    const items = {}; R.g.traverse(o => { if (o.userData && (o.userData.id === 'second_estop' || o.userData.id === 'getac_tablet' || o.userData.id === 'head_light') && o.isGroup && !items[o.userData.id]) items[o.userData.id] = o; });
    let minGap = {}, n = 0;
    for (let f = 0; f < st.frames; f += 10) {
      const t = f / fps * sp; S.applyAt(t); R.g.updateMatrixWorld(true); inv.copy(R.g.matrixWorld).invert(); n++;
      const ib = {}; for (const k in items) ib[k] = rbox(items[k]);
      for (const side of ['left', 'right']) {
        const a = R.arm[side], links = [a.gBase].concat(a.gLinks).concat(a.fingers.map(x => x.g));
        links.forEach((g, i) => {
          if (!g.children.length) return;
          const lb = rbox(g), nm = i < 8 ? names[i] : 'finger' + (i - 7);
          for (const k in ib) {
            const key = side + ' ' + nm + ' / ' + k, gap = lb.distanceToPoint ? Math.max(0, ...['x','y','z'].map(c => Math.max(ib[k].min[c] - lb.max[c], lb.min[c] - ib[k].max[c]))) : 0;
            if (minGap[key] === undefined || gap < minGap[key].gap) minGap[key] = {gap: Math.round(gap * 1e4) / 1e4, frame: f, t: Math.round(t * 100) / 100};
            if (lb.intersectsBox(ib[k])) out.push({frame: f, t: Math.round(t * 100) / 100, arm: side, link: nm, item: k,
              overlap_m: ['x','y','z'].map(c => Math.round((Math.min(lb.max[c], ib[k].max[c]) - Math.max(lb.min[c], ib[k].min[c])) * 1e4) / 1e4)});
          }
        });
      }
    }
    return {frames: st.frames, fps, speed: sp, T: st.T, samples: n, items: Object.keys(items), overlaps: out, minGap};
  });
  res.errs = errs; fs.writeFileSync(process.argv[2], JSON.stringify(res, null, 1));
  console.log(JSON.stringify({frames: res.frames, T: res.T, samples: res.samples, items: res.items, overlaps: res.overlaps.length, errs}));
  await b.close();
})();
