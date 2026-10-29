// Synchronization audit of the shared robot model between the robot page and the exploded view.
//   node scripts/audit_sync.js [base URL, default http://localhost:8765/] [out, default scripts/sync_audit.json]
// Serve docs/assets/roadmap first, for example: (cd docs/assets/roadmap && python3 -m http.server 8765).
// For every registry part (model.js M.COMPONENTS) it records (a) drawn on robot.html (page load, lift L1000,
// bp000, hp30), (b) drawn on exploded.html (render mode, frame 0, explode factor 0), (c) stage and offsets in
// exploded.json, (d) the mesh count and the transform relative to the robot root of the part groups and of
// every mesh under them, on both pages. Mismatches are listed; check_roadmap.py fails on a mismatch or when
// the audit is older than the files it read (sha256 fingerprint).
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path'), crypto = require('crypto');
const BASE = process.argv[2] || 'http://localhost:8765/', OUT = process.argv[3] || path.join(__dirname, 'sync_audit.json');
const ROOT = path.join(__dirname, '..', 'docs', 'assets', 'roadmap');
const FILES = ['model/model.js', 'model/exploded.json', 'robot.html', 'exploded.html'];
const GL = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];

// runs in the page: per part id, drawn, meshes, part-group and mesh transforms relative to the root
const dump = (root, parts, comps) => {
  const inv = root.matrixWorld.clone().invert(), out = {};
  const r = m => Array.from(m.elements).map(v => Math.round(v * 1e5) / 1e5);
  const shown = o => { for (let p = o; p && p !== root; p = p.parent) if (!p.visible) return false; return true; };
  root.updateMatrixWorld(true);
  comps.forEach(c => (c.nodes || c.parts || []).forEach(pid => {
    const gs = parts[pid] || [], meshes = [], groups = [];
    let drawn = false;
    gs.forEach(g => {
      groups.push(r(inv.clone().multiply(g.matrixWorld)));
      g.traverse(o => { if (!o.isMesh) return; meshes.push(r(inv.clone().multiply(o.matrixWorld))); if (shown(o)) drawn = true; });
    });
    out[pid] = {comp: c.id, groups: gs.length, meshes: meshes.length, drawn, groupT: groups, meshT: meshes};
  }));
  return out;
};

(async () => {
  const fp = {};
  FILES.forEach(f => { fp[f] = crypto.createHash('sha256').update(fs.readFileSync(path.join(ROOT, f))).digest('hex'); });
  const X = JSON.parse(fs.readFileSync(path.join(ROOT, 'model/exploded.json'), 'utf8'));
  const b = await chromium.launch({ args: GL }), errs = [];
  const open = async (url) => {
    const p = await b.newPage({ viewport: { width: 1280, height: 720 } });
    p.setDefaultTimeout(1800000);
    p.on('pageerror', e => errs.push(url + ': ' + e.message));
    await p.goto(BASE + url, { waitUntil: 'domcontentloaded' });
    return p;
  };
  const rp = await open('robot.html#nomtx');
  await rp.waitForFunction(() => window.__sim && window.__sim.robot && window.OAMR_MODEL);
  // the page applies the order-run timeline at load (its first arm pose); the audit compares the model, so
  // both arms go to the assembled pose of the exploded view (M.ARM_POSE, grip M.ARM_GRIP) first
  const loadPose = await rp.evaluate(() => {
    const R = window.__sim.robot, M = window.OAMR_MODEL, q = {left: R.arm.left.q.slice(), right: R.arm.right.q.slice()};
    ['left', 'right'].forEach(s => { R.applyArm(s, M.ARM_POSE[s].slice()); R.setGrip(s, M.ARM_GRIP); });
    R.g.updateMatrixWorld(true);
    return q;
  });
  const robot =await rp.evaluate(`(${dump})(window.__sim.robot.g, window.__sim.robot.ubParts, window.OAMR_MODEL.COMPONENTS)`);
  const rstate = await rp.evaluate(() => ({lift: window.__sim.robot.sh, bp: window.__sim.robot.bpKey, hp: window.__sim.robot.hp}));
  const comps = await rp.evaluate(() => window.OAMR_MODEL.COMPONENTS.map(c => ({id: c.id, pids: c.nodes || c.parts || []})));
  const xp = await open('exploded.html?render=1&frame=0&w=640&h=360');
  await xp.waitForFunction(() => window.__frameReady === true && window.__model);
  const expl = await xp.evaluate(`(${dump})(window.__model.root, window.__model.parts, window.OAMR_MODEL.COMPONENTS)`);
  const home = await xp.evaluate(() => {  // explode factor 0: every part group at its home position
    let worst = 0;
    for (const pid in window.__model.parts) window.__model.parts[pid].forEach(g => { worst = Math.max(worst, g.position.distanceTo(g.userData.home)); });
    return worst;
  });
  await b.close();
  const rows = [], mism = [];
  const same = (a, c) => a.length === c.length && a.every((m, i) => m.every((v, k) => Math.abs(v - c[i][k]) < 2e-5));
  comps.forEach(c => {
    const e = X.components[c.id] || {};
    c.pids.forEach(pid => {
      const r = robot[pid] || {}, x = expl[pid] || {}, off = (e.offsets || {})[pid];
      const row = {comp: c.id, part: pid, robot_drawn: !!r.drawn, exploded_drawn: !!x.drawn, stage: e.stage || null,
        offset: off || null, robot_meshes: r.meshes || 0, exploded_meshes: x.meshes || 0,
        same_transform: !!(r.groupT && x.groupT && same(r.groupT, x.groupT) && same(r.meshT, x.meshT))};
      const bad = [];
      if (!row.robot_drawn) bad.push('not drawn on robot.html');
      if (!row.exploded_drawn) bad.push('not drawn on exploded.html');
      if (!row.stage || !row.offset) bad.push('no stage or offset in exploded.json');
      if (row.robot_meshes !== row.exploded_meshes) bad.push('mesh count ' + row.robot_meshes + ' vs ' + row.exploded_meshes);
      else if (!row.same_transform) bad.push('different transform');
      row.mismatch = bad;
      if (bad.length) mism.push(pid + ': ' + bad.join(', '));
      rows.push(row);
    });
  });
  const res = {fingerprint: fp, robot_state: rstate, robot_load_arm_pose: loadPose, exploded_home_offset_m: home, parts: rows.length, mismatches: mism, errors: errs, rows};
  fs.writeFileSync(OUT, JSON.stringify(res, null, 1) + '\n');
  console.log(JSON.stringify({parts: rows.length, mismatches: mism.length, robot_state: rstate, exploded_home_offset_m: home, errors: errs.length}));
  mism.forEach(m => console.log('  ' + m));
})();
