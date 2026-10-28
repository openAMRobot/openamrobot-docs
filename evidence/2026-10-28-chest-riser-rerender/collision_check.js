// node collision_check.js <out.json> [page, default robot.html] [base URL, default http://localhost:8765/]
// robot.html order run in the render mode (speed 4, 24 fps), every 10th frame. Bounding boxes in the robot frame
// (precise, per vertex; robot axes, so a turn of the robot does not grow the boxes) of
//   movers: every arm link mesh group (base, link1 to link7, two fingers, both arms) and the item a gripper carries;
//   upper-body targets: getac_tablet, head_light, head_camera, head_camera_bracket, second_estop, flag_rod,
//     rod_corner_bracket, lift_flag, lift_stop_sensors, lift_sensor_brackets (each sensor and bracket on its own);
//   lift parts against the scene: flag_rod, rod_corner_bracket, lift_flag, sensors and brackets against the two
//     totes, the two tote risers and the lift cable.
// Overlaps are listed (frame, sim time, mover or lift part, target, box overlap). second_estop_sweep: the second
// E-stop moved down from its drawn position in 10 mm steps (centre 40 to 100 mm below the static profile top), the
// overlaps with the movers at each step (0 to 300 mm down; the layout task accepts up to 100 mm below the top). Boxes are axis-aligned: an overlap marks possible contact, not proven
// mesh contact. Nothing in the scene is moved, except the second E-stop copy used for the sweep (computed only).
const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const out = process.argv[2], page = process.argv[3] || 'robot.html', base = process.argv[4] || 'http://localhost:8765/';
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 640, height: 360 } }); p.setDefaultTimeout(3600000);
  const errs = []; p.on('pageerror', e => errs.push(e.message));
  await p.goto(base + page + '?render=1&w=640&h=360&fps=24&speed=4&cam=auto#nomtx', { waitUntil: 'domcontentloaded' });
  await p.waitForFunction(() => window.__frameReady === true);
  const res = await p.evaluate(() => {
    const S = window.__sim, THREE = S.THREE, R = S.robot, st = window.__store, fps = st.fps, sp = st.speed, P = S.player;
    const inv = new THREE.Matrix4(), m = new THREE.Matrix4(), v = new THREE.Vector3();
    const rbox = (obj, b) => { b = b || new THREE.Box3(); obj.updateMatrixWorld(true); obj.traverse(o => { if (!o.isMesh || !o.visible) return;
      m.multiplyMatrices(inv, o.matrixWorld); const q = o.geometry.attributes.position;
      for (let i = 0; i < q.count; i++) b.expandByPoint(v.fromBufferAttribute(q, i).applyMatrix4(m)); }); return b; };
    const r4 = x => Math.round(x * 1e4) / 1e4;
    const ov = (a, c) => ['x', 'y', 'z'].map(k => r4(Math.min(a.max[k], c.max[k]) - Math.max(a.min[k], c.min[k])));
    const gap = (a, c) => r4(Math.max(0, ...['x', 'y', 'z'].map(k => Math.max(c.min[k] - a.max[k], a.min[k] - c.max[k]))));
    const parts = R.ubParts, one = id => (parts[id] || [])[0];
    // upper-body targets; sensors and brackets one box per stop (the meshes of one sensor share its z)
    const T = {};
    ['getac_tablet', 'head_light', 'head_camera', 'head_camera_bracket', 'second_estop', 'flag_rod', 'rod_corner_bracket', 'lift_flag']
      .forEach(id => { if (one(id)) T[id] = [one(id)]; });
    const perStop = id => { const g = one(id); if (!g) return; const by = {};
      g.children.forEach(c => { const k = Math.round(c.position.z * 1000); (by[k] = by[k] || []).push(c); });
      Object.keys(by).sort((a, c) => a - c).forEach((k, i) => { T[id + '_S' + (i + 1)] = by[k]; }); };
    perStop('lift_stop_sensors'); perStop('lift_sensor_brackets');
    const LIFT = Object.keys(T).filter(k => /^(flag_rod|rod_corner_bracket|lift_flag|lift_stop_sensors|lift_sensor_brackets)/.test(k));
    // scene targets for the lift parts: tote bodies (without the riser), risers, lift cable
    const SC = {};
    for (const side of ['left', 'right']) {
      const t = R.totes[side], ris = t.children.filter(c => /^tote_riser_/.test(c.name));
      SC['tote_' + side] = t.children.filter(c => ris.indexOf(c) < 0); SC['tote_riser_' + side] = ris;
    }
    if (R.cable) SC.lift_cable = [R.cable];
    const names = ['base', 'link1', 'link2', 'link3', 'link4', 'link5', 'link6', 'link7'];
    const out = [], lift = [], minGap = {}, sweep = {}, STEPS = Array.from({length: 31}, (_, i) => i / 100);
    STEPS.forEach(s => { sweep[s] = []; });
    let n = 0;
    for (let f = 0; f < st.frames; f += 10) {
      const t = f / fps * sp; S.applyAt(t); R.g.updateMatrixWorld(true); inv.copy(R.g.matrixWorld).invert(); n++;
      const tb = {}; for (const k in T) { const bx = new THREE.Box3(); T[k].forEach(o => rbox(o, bx)); tb[k] = bx; }
      const movers = [];
      for (const side of ['left', 'right']) {
        const a = R.arm[side], links = [a.gBase].concat(a.gLinks).concat(a.fingers.map(x => x.g));
        links.forEach((g, i) => { if (g.children.length) movers.push({name: side + ' ' + (i < 8 ? names[i] : 'finger' + (i - 7)), box: rbox(g)}); });
      }
      if (P.tl) P.tl.items.forEach(c => { let u = null; c.phases.forEach(ph => { if (t >= ph.t) u = ph; });
        const h = P.meshes.get(c); if (u && u.kind === 'grip' && h && h.parent) movers.push({name: 'carried item (' + u.side + ')', box: rbox(h)}); });
      for (const mv of movers) for (const k in tb) {
        const key = mv.name.replace(/carried item \((\w+)\)/, 'carried item $1') + ' / ' + k, g = gap(mv.box, tb[k]);
        if (minGap[key] === undefined || g < minGap[key].gap) minGap[key] = {gap: g, frame: f, t: r4(t)};
        if (mv.box.intersectsBox(tb[k])) out.push({frame: f, t: Math.round(t * 100) / 100, mover: mv.name, item: k, overlap_m: ov(mv.box, tb[k])});
      }
      // lift parts against totes, risers and the lift cable
      const sb = {}; for (const k in SC) { const bx = new THREE.Box3(); SC[k].forEach(o => rbox(o, bx)); sb[k] = bx; }
      for (const k of LIFT) for (const s in sb) {
        const key = k + ' / ' + s, g = gap(tb[k], sb[s]);
        if (minGap[key] === undefined || g < minGap[key].gap) minGap[key] = {gap: g, frame: f, t: r4(t)};
        if (!sb[s].isEmpty() && tb[k].intersectsBox(sb[s])) lift.push({frame: f, t: Math.round(t * 100) / 100, part: k, target: s, overlap_m: ov(tb[k], sb[s])});
      }
      // second E-stop sweep: the drawn box moved down
      if (tb.second_estop) STEPS.forEach(s => { const e = tb.second_estop.clone(); e.min.z -= s; e.max.z -= s;
        movers.forEach(mv => { if (mv.box.intersectsBox(e)) sweep[s].push({frame: f, t: Math.round(t * 100) / 100, mover: mv.name, overlap_m: ov(mv.box, e)}); }); });
    }
    return {page: location.pathname, frames: st.frames, fps, speed: sp, T: st.T, samples: n, targets: Object.keys(T), scene: Object.keys(SC),
      overlaps: out, lift_overlaps: lift, second_estop_sweep: sweep, minGap};
  });
  res.errs = errs; fs.writeFileSync(out, JSON.stringify(res, null, 1));
  const sw = {}; for (const s in res.second_estop_sweep) sw[s] = res.second_estop_sweep[s].length;
  console.log(JSON.stringify({samples: res.samples, T: res.T, targets: res.targets.length, overlaps: res.overlaps.length, lift_overlaps: res.lift_overlaps.length, sweep: sw, errs}));
  await b.close();
})();
