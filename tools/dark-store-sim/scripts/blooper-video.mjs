// "Pace the frontier" blooper: node chaos.mjs <preview|full> [list of preview seconds as JSON]
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs';
const MODE = process.argv[2] || 'preview';
const FPS = 25, W = 1280, H = 720, TOTAL = 28.5;
const OUT = MODE === 'full' ? 'out/chaos/frames' : 'out/chaos/preview';
fs.mkdirSync(OUT, { recursive: true });
const html = fs.readFileSync('out/web/index.html');
const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8795);
const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium', headless: false, args: ['--headless=new', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
p.on('pageerror', e => console.log('ERR', e.message)); p.on('console', m => { if (m.type() === 'error' || m.text().startsWith('[c]')) console.log(m.text()); });
await p.route(u => !u.toString().startsWith('http://localhost'), r => r.abort());
await p.goto('http://localhost:8795/', { waitUntil: 'domcontentloaded', timeout: 300000 });
await p.waitForFunction(() => window.__sim, null, { timeout: 300000 });
await p.addStyleTag({ content: 'header.top,aside.panel,.hud,.legend,.play,.tiles{display:none!important} .app,.work{display:block!important;height:100vh!important;width:100vw!important} .stage{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important}' });
await p.evaluate(({ W, H, FPS }) => {
  const s = window.__sim, THREE = s.THREE, R = s.robot, store = s.store, scene = s.scene;
  s.S.tiles = false; if (s.S.hq) document.getElementById('b-q').click();
  s.key.shadow.mapSize.set(2048, 2048); if (s.key.shadow.map) { s.key.shadow.map.dispose(); s.key.shadow.map = null; }
  let hemi; scene.traverse(o => { if (o.isRectAreaLight) o.visible = false; if (o.isHemisphereLight) { o.intensity = 1.1; hemi = o; } });
  const fill = new THREE.DirectionalLight(0xfff4e6, 0.6); fill.position.set(-1, 2, 6); scene.add(fill);
  s.camera.fov = 45; s.camera.updateProjectionMatrix();
  const emiss = []; scene.traverse(o => { if (o.material && !Array.isArray(o.material) && o.material.emissiveIntensity > 0.3 && o.material.emissive && o.material.emissive.getHex()) emiss.push([o.material, o.material.emissiveIntensity]); });
  const bg0 = scene.background.clone();
  const red = new THREE.PointLight(0xff2a1a, 0, 3.5, 1.6); scene.add(red);

  // deterministic RNG
  let seed = 7; const rnd = () => (seed = (seed * 16807) % 2147483647) / 2147483647; const rr = (a, b) => a + (b - a) * rnd();
  const V = (x, y, z) => new THREE.Vector3(x, y, z);

  // --- beer pick cycle from the real planner
  const beer = store.slotFor(3, 'R', 0, 2, 0, 0);
  s.startRun([beer], 'cycle'); s.S.playing = false;
  const it = s.TL.items[0], tGrip = it.phases.find(q => q.kind === 'grip').t;
  const tl0 = tGrip - 2.3, tSlip = tGrip + 1.05;

  // --- physics bodies
  const bodies = [], dummy = new THREE.Object3D();
  function body(o) {
    Object.assign(o, { vel: o.vel || V(0, 0, 0), w: o.w || V(0, 0, 0), active: false, contact: false, settled: false, inAisle: false });
    o.corners = []; const bb = o.bb; for (const x of [bb.min.x, bb.max.x]) for (const y of [bb.min.y, bb.max.y]) for (const z of [bb.min.z, bb.max.z]) o.corners.push(V(x, y, z));
    bodies.push(o); return o;
  }
  function instBody(sl, t0, vel, w) {
    const m = new THREE.Matrix4(); sl.mesh.getMatrixAt(sl.index, m); const pos = V(0, 0, 0), q = new THREE.Quaternion(), sc = V(0, 0, 0); m.decompose(pos, q, sc);
    if (sc.x < 0.01) return null; if (!sl.mesh.geometry.boundingBox) sl.mesh.geometry.computeBoundingBox();
    sl.fallen = true;
    return body({ kind: 'inst', sl, pos, q, bb: sl.mesh.geometry.boundingBox, t0, vel, w, glass: /^beer/.test(sl.key) });
  }
  function meshBody(mesh, t0, vel, w) {
    mesh.updateMatrixWorld(true); const pos = V(0, 0, 0), q = new THREE.Quaternion(), sc = V(0, 0, 0); mesh.matrixWorld.decompose(pos, q, sc);
    if (mesh.parent !== scene) { mesh.parent.remove(mesh); scene.add(mesh); }
    mesh.matrixAutoUpdate = true; mesh.position.copy(pos); mesh.quaternion.copy(q); mesh.scale.copy(sc);
    if (!mesh.geometry.boundingBox) mesh.geometry.computeBoundingBox();
    const bb = mesh.geometry.boundingBox.clone(); bb.min.multiply(sc); bb.max.multiply(sc); mesh.scale.copy(sc);
    return body({ kind: 'mesh', mesh, pos, q, bb, t0, vel, w });
  }
  const dirty = new Set();
  function writeBody(o) {
    if (o.kind === 'inst') { dummy.position.copy(o.pos); dummy.quaternion.copy(o.q); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); o.sl.mesh.setMatrixAt(o.sl.index, dummy.matrix); dirty.add(o.sl.mesh); }
    else { o.mesh.position.copy(o.pos); o.mesh.quaternion.copy(o.q); }
  }
  const tmp = V(0, 0, 0), qa = new THREE.Quaternion(), down = V(0, 0, -1), axes = [V(1, 0, 0), V(-1, 0, 0), V(0, 1, 0), V(0, -1, 0), V(0, 0, 1), V(0, 0, -1)];
  let floorCount = 0, breaks = 0;
  function step(o, dt, T) {
    if (!o.active) { if (T >= o.t0) o.active = true; else return; }
    if (o.settled) return;
    o.vel.z -= 9.81 * dt; o.pos.addScaledVector(o.vel, dt);
    const wl = o.w.length(); if (wl > 1e-6) { qa.setFromAxisAngle(tmp.copy(o.w).divideScalar(wl), wl * dt); o.q.premultiply(qa); }
    // aisle walls: items that reached the aisle stay between the shelf fronts
    const cy = o.cy ?? 0; if (Math.abs(o.pos.y - cy) < 0.5) o.inAisle = true;
    if (o.inAisle && Math.abs(o.pos.y - cy) > 0.53 && Math.sign(o.vel.y) === Math.sign(o.pos.y - cy)) { o.vel.y *= -0.3; o.pos.y = cy + Math.sign(o.pos.y - cy) * 0.53; }
    let minZ = 1e9; for (const c of o.corners) { tmp.copy(c).applyQuaternion(o.q); minZ = Math.min(minZ, tmp.z); }
    const zb = o.pos.z + minZ;
    if (zb < 0) {
      const impact = -o.vel.z; o.pos.z -= zb;
      if (!o.contact) { o.contact = true; floorCount += o.count === false ? 0 : 1; if (o.glass && impact > 2.2 && breaks < 18) { shatter(o.pos.clone(), o.big ? 70 : 14, o.big ? 0.36 : 0.16); breaks++; hideBody(o); return; } }
      if (o.vel.z < 0) o.vel.z = -o.vel.z * 0.22;
      o.vel.x *= 0.86; o.vel.y *= 0.86; o.w.multiplyScalar(0.8);
      // settle onto the face closest to the floor
      let best = null, bd = -2; for (const a of axes) { tmp.copy(a).applyQuaternion(o.q); const d = tmp.dot(down); if (d > bd) { bd = d; best = tmp.clone(); } }
      qa.setFromUnitVectors(best, down); const target = o.q.clone().premultiply(qa); o.q.slerp(target, 0.18);
      if (o.vel.length() < 0.05 && o.w.length() < 0.2 && bd > 0.995) o.settled = true;
    }
    writeBody(o);
  }
  function hideBody(o) { o.settled = true; if (o.kind === 'inst') { dummy.scale.set(1e-5, 1e-5, 1e-5); dummy.position.copy(o.pos); dummy.updateMatrix(); o.sl.mesh.setMatrixAt(o.sl.index, dummy.matrix); dirty.add(o.sl.mesh); } else o.mesh.visible = false; }

  // glass shards, beer puddles and foam
  const glassM = new THREE.MeshStandardMaterial({ color: 0x5a2e0e, roughness: 0.08, metalness: 0.1, transparent: true, opacity: 0.85 });
  const shardG = new THREE.TetrahedronGeometry(0.014);
  const puddleM = new THREE.MeshStandardMaterial({ color: 0xc98a1c, roughness: 0.05, metalness: 0.2, transparent: true, opacity: 0.78, depthWrite: false });
  const foamM = new THREE.MeshStandardMaterial({ color: 0xfff6e2, roughness: 0.9, transparent: true, opacity: 0.9, depthWrite: false });
  const puddles = [];
  let simT = 0;
  function shatter(at, n, size) {
    for (let i = 0; i < n; i++) {
      const m = new THREE.Mesh(shardG, glassM); m.scale.setScalar(rr(0.5, 1.6)); m.position.set(at.x, at.y, 0.03); m.castShadow = true; scene.add(m);
      const a = rr(0, Math.PI * 2), v = rr(0.4, 2.2);
      const o = meshBody(m, simT, V(Math.cos(a) * v, Math.sin(a) * v, rr(0.6, 2.4)), V(rr(-20, 20), rr(-20, 20), rr(-20, 20))); o.count = false; o.cy = 0;
    }
    const pd = new THREE.Mesh(new THREE.CircleGeometry(1, 40), puddleM); pd.position.set(at.x, at.y, 0.0025 + puddles.length * 0.0002); pd.scale.setScalar(0.001); pd.receiveShadow = true; scene.add(pd);
    const fm = new THREE.Mesh(new THREE.CircleGeometry(1, 30), foamM); fm.position.set(at.x + 0.02, at.y - 0.01, 0.0035 + puddles.length * 0.0002); fm.scale.setScalar(0.001); scene.add(fm);
    puddles.push({ pd, fm, t0: simT, r: size });
  }
  function updPuddles() { for (const q of puddles) { const u = Math.min(1, (simT - q.t0) / 1.1), e = 1 - (1 - u) * (1 - u); q.pd.scale.set(q.r * e, q.r * 0.8 * e, 1); const f = Math.max(0, 1 - (simT - q.t0) / 6); q.fm.scale.set(q.r * 0.55 * e * (0.4 + 0.6 * f), q.r * 0.4 * e * (0.4 + 0.6 * f), 1); } }

  // the beer that slips
  let slipBody = null;
  // loose water bottle lying in the aisle (what the robot runs into)
  const wg = store.inst.water1 || store.inst.water0; const bottle = new THREE.Mesh(wg.mesh.geometry, wg.mesh.material); bottle.castShadow = true;
  // spill programme
  function spill(side, x, r, t0, opts = {}) {
    const sg = side === 'L' ? 1 : -1;
    for (const sl of store.slots) {
      if (sl.aisle !== 3 || sl.side !== side || sl.picked || sl.fallen) continue;
      const dx = Math.abs(sl.pos.x - x); if (dx > r) continue;
      if (!opts.all && (sl.row > 1 || sl.level === 0)) continue;
      if (opts.levels && !opts.levels.includes(sl.level)) continue;
      const delay = dx / (opts.wave || 1.6) + rr(0, opts.jit ?? 0.25) + (opts.levelDelay ? (4 - sl.level) * opts.levelDelay : 0);
      const out = rr(0.5, 1.5) * (1 + sl.row * 0.6);
      const o = instBody(sl, t0 + delay, V(rr(-0.5, 0.5), -sg * out, rr(-0.1, 0.6)), V(rr(-7, 7), rr(-7, 7), rr(-4, 4)));
      if (o) o.cy = 0;
    }
  }
  // shelf collapse of run 3L: boards, lips, strips and brackets fall; uprights buckle
  const run = scene.getObjectByName('run_3L'), uprights = [], parts = [];
  run.children.slice().forEach(c => { if (!c.isMesh) return; const gp = c.geometry.parameters || {}; if (gp.depth === 2.0 && gp.width < 0.05) uprights.push({ m: c, x0: c.position.x, z0: c.position.z }); else if (c.geometry.type !== 'PlaneGeometry' || gp.height < 0.1) parts.push(c); });
  function collapse(t0) {
    for (const c of parts) { const lvl = c.position.z; const o = meshBody(c, t0 + (1.75 - lvl) * 0.25 + rr(0, 0.15), V(rr(-0.2, 0.2), -rr(0.1, 0.6), rr(-0.3, 0)), V(rr(-3, 3), rr(-1, 1), rr(-1, 1))); o.count = false; o.cy = 0; }
    for (const sl of store.slots) if (sl.aisle === 3 && sl.side === 'L' && !sl.fallen && !sl.picked) { const o = instBody(sl, t0 + (1.75 - sl.pos.z) * 0.25 + rr(0, 0.2), V(rr(-0.3, 0.3), -rr(0.3, 1.3), rr(0, 0.3)), V(rr(-6, 6), rr(-6, 6), rr(-3, 3))); if (o) o.cy = 0; }
  }

  // --- robot choreography (real seconds)
  const K = { pick: 0, slip: 3.4, slowEnd: 5.4, drive: 6.6, hit: 0, sway1: 0, sway2: 0, collapse: 12.2, flail: 13.2, flick: 16.6, dark: 19.3, black: 20.3, end: 28.5 };
  let rob = null, roll = 0, vx = 0;
  const STOWL = [0.25, -0.12, 0, 1.9, 0, -0.78, 0], mir = q => [-q[0], -q[1], -q[2], q[3], -q[4], -q[5], -q[6]];
  let shake = 0, lightF = 1, caption = '', capCol = '#f2c230', speedLbl = '1×', glitch = 0, swayDone = { l: false, r: false };
  function robotAt(T, dt) {
    if (T < K.slip) { s.applyAt(tl0 + T); caption = `Pick Beer 0.5 L at 3R-01-3`; return; }
    if (!rob) { // take over from the player
      s.applyAt(tl0 + K.slip); rob = { x: R.pose.x, y: R.pose.y, yaw: R.pose.yaw || 0, qL: R.arm.left.q.slice(), qR: R.arm.right.q.slice(), sh: R.sh };
      const held = [...s.player.meshes.values()][0]; held.updateMatrixWorld(true);
      const m = new THREE.Mesh(held.geometry, held.material); m.castShadow = true; m.matrix.copy(held.matrix); m.matrix.decompose(m.position, m.quaternion, m.scale); scene.add(m); held.visible = false; s.player.tl = null;
      slipBody = meshBody(m, simT, V(0.45, -0.04, 0.15), V(4, -6, 1)); slipBody.glass = true; slipBody.big = true; slipBody.cy = 0;
      R.setGrip(R.arm.right.grip > R.arm.left.grip ? 'left' : 'right', 1);
      bottle.position.set(rob.x + 1.15, 0.12, 0.045); bottle.rotation.set(Math.PI / 2, 0, 0.5); scene.add(bottle);
      rob.bottle = meshBody(bottle, 1e9, V(0, 0, 0), V(0, 0, 0)); rob.bottle.cy = 0; rob.bottle.count = false; rob.bottle.active = false;
    }
    const q0L = rob.qL, q0R = rob.qR;
    if (T < K.drive) { // startled: open both grippers, small recoil
      caption = T < K.slowEnd ? 'Grip lost' : 'Re-planning route'; capCol = '#e5484d';
      R.setGrip('left', 1); R.setGrip('right', 1);
      const u = Math.min(1, (T - K.slip) / 1.5); const q = (a, b) => a.map((v, i) => v + (b[i] - v) * u * 0.6);
      R.applyArm('left', q(q0L, STOWL)); R.applyArm('right', q(q0R, mir(STOWL)));
    } else if (T < K.collapse) {
      // drive forward, hit the bottle, sway left then right
      const front = rob.x + 0.39 + 0.02;
      if (!K.hit) { vx = Math.min(0.75, vx + 1.2 * dt); rob.x += vx * dt; caption = 'Driving to the next pick'; capCol = '#f2c230';
        if (front >= bottle.position.x - 0.05) { K.hit = T; rob.bottle.t0 = simT; rob.bottle.active = true; rob.bottle.vel.set(1.3, 0.35, 0.5); rob.bottle.w.set(2, 9, 3); shake = 1; } }
      else {
        const u = T - K.hit; vx = Math.max(0.1, vx - 0.6 * dt); rob.x += vx * dt * (u < 2.5 ? 1 : 0.2);
        roll = -0.2 * Math.sin(u * 2.4) * Math.exp(-0.05 * u) * Math.min(1, u * 3);   // negative = toward +Y (left run)
        caption = 'Obstacle! Recovering balance'; capCol = '#e5484d';
        if (!swayDone.l && u > 0.55) { swayDone.l = true; spill('L', rob.x + 0.15, 1.0, simT, { levels: [3, 4, 2], wave: 1.2 }); shake = 1; }
        if (!swayDone.r && u > 1.85) { swayDone.r = true; spill('R', rob.x + 0.15, 1.1, simT, { levels: [3, 4, 2], wave: 1.2 }); shake = 1; }
        if (u > 3.0 && !rob.cascade) { rob.cascade = true; spill('L', rob.x, 3.5, simT, { wave: 1.4, levels: [1, 2, 3, 4] }); spill('R', rob.x, 3.5, simT + 0.3, { wave: 1.4, levels: [1, 2, 3, 4] }); caption = 'Items on the floor'; }
      }
      const ph = T - K.drive; R.applyArm('left', STOWL.map((v, i) => v + 0.25 * Math.sin(ph * 3 + i) * (K.hit ? 1 : 0.2))); R.applyArm('right', mir(STOWL).map((v, i) => v + 0.25 * Math.sin(ph * 3.3 + i * 1.3) * (K.hit ? 1 : 0.2)));
    } else {
      if (!rob.collapsed) { rob.collapsed = true; collapse(simT); shake = 1.4; }
      const ph = T - K.collapse, a = Math.min(1, ph / 1.0);
      roll = -0.12 * Math.sin(ph * 5.3) * a + 0.05 * Math.sin(ph * 11);
      rob.x += 0.12 * Math.sin(ph * 7.0) * dt * 3; rob.yaw = 0.18 * Math.sin(ph * 4.1) * a;
      const flail = (side, k) => { const b = side === 'left' ? STOWL : mir(STOWL); return b.map((v, i) => v + a * (0.9 * Math.sin(ph * (5 + k + i * 0.7) + i * 1.7))); };
      R.applyArm('left', flail('left', 0)); R.applyArm('right', flail('right', 1.3));
      R.setGrip('left', 0.5 + 0.5 * Math.sin(ph * 14)); R.setGrip('right', 0.5 + 0.5 * Math.sin(ph * 12 + 1));
      const sh = 1.175 + 0.15 * Math.sin(ph * 3.2); if (Math.abs(sh - R.sh) > 1e-4) R.setLift(sh);
      caption = T < K.flick ? 'Clean-up required' : 'SYSTEM ERROR'; capCol = '#e5484d';
    }
    R.setPose(rob.x, rob.y, rob.yaw);
    // roll about the forward axis, pivoting on the low wheel
    R.g.rotation.set(roll, 0, rob.yaw, 'ZYX'); R.g.position.z = Math.abs(Math.sin(roll)) * 0.29; R.g.updateMatrixWorld(true);
  }
  function lights(T) {
    let f = 1;
    if (T >= K.flick && T < K.dark) { const k = Math.floor(T * 25); seed = 1000 + k; f = rnd() < 0.45 ? rr(0.02, 0.15) : rr(0.6, 1.1); glitch = rnd() < 0.35 ? 1 : 0; }
    else if (T >= K.dark) { f = Math.max(0, 0.06 * (1 - (T - K.dark) / 1.0)); glitch = 0; }
    seed = 7 + Math.floor(T * 1000);
    const dark = T >= K.dark;
    if (dark && scene.environment) { s.envSave = scene.environment; scene.environment = null; }
    s.renderer.toneMappingExposure = dark ? 1.05 : 1.05 * f;
    const lf = dark ? 0 : 1;
    lightF = f; hemi.intensity = 1.1 * lf; s.key.intensity = 1.55 * lf; fill.intensity = 0.6 * lf;
    for (const [m, i] of emiss) m.emissiveIntensity = dark ? 0 : i;
    scene.background.copy(bg0).multiplyScalar(dark ? 0.0 : 1);
    red.position.set(R.pose.x + 0.3, R.pose.y, 1.6); red.distance = 2.2; red.intensity = T >= K.flick && T < K.black ? (dark ? 2.2 * Math.max(0, 1 - (T - K.dark) / 1.1) : 1.5) * (0.5 + 0.5 * Math.sin(T * 9)) : 0;
  }
  // camera
  const Lp = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u), E = u => u * u * (3 - 2 * u);
  let camBase = null;
  function camera(T) {
    const g = R.g.position; let c, t;
    if (T < K.slip) { const u = E(T / K.slip); c = [g.x + 1.45 - 0.2 * u, g.y + 0.32 - 0.12 * u, 1.45 - 0.12 * u]; t = [g.x, g.y - 0.32, 1.0]; }
    else if (T < K.slowEnd) { const u = E((T - K.slip) / 2.0); const bp = slipBody.pos; if (!camBase) camBase = { x: g.x, y: g.y };
      if (!camBase.fp) camBase.fp = { x: bp.x, y: bp.y };
      c = [camBase.fp.x + 1.75 - 0.35 * u, -0.43, 0.95 - 0.6 * u]; t = [camBase.fp.x + 0.15, -0.38, Math.max(0.08, bp.z * 0.55)]; }
    else if (T < K.collapse) { if (!camBase.rear) camBase.rear = { x: g.x }; const u = E(Math.min(1, (T - K.slowEnd) / 6)); const fx = Math.max(camBase.rear.x - 1.6, g.x - 1.75); c = [fx + 0.2 * u, 0.0, 1.7 + 0.2 * u]; t = [g.x + 0.8, 0, 0.8]; }
    else { if (!camBase.front) camBase.front = { x: g.x }; const u = E(Math.min(1, (T - K.collapse) / 7)); c = [camBase.front.x + 2.3 - 0.5 * u, -0.05, 1.85 - 0.15 * u]; t = [g.x, 0, 0.9]; }
    if (shake > 0) { c = c.map((v, i) => v + (rnd() - 0.5) * 0.05 * shake); shake = Math.max(0, shake - 0.06); }
    s.closeUp(...c, ...t);
  }
  // overlay
  const oc = document.createElement('canvas'); oc.width = W; oc.height = H; const ctx = oc.getContext('2d');
  const F = (w, px, fam = 'Barlow') => `${w} ${px}px "${fam}", sans-serif`;
  function pill(x, y, text, font, bg, fg, pad = 12, hgt = 34) { ctx.font = font; const w = ctx.measureText(text).width + pad * 2; ctx.fillStyle = bg; ctx.beginPath(); ctx.roundRect(x, y, w, hgt, 8); ctx.fill(); ctx.fillStyle = fg; ctx.textBaseline = 'middle'; ctx.fillText(text, x + pad, y + hgt / 2 + 1); return w; }
  function hud(T) {
    let x = 28; x += pill(x, 26, 'OpenAMRobot 2.0', F(700, 19, 'Barlow Semi Condensed'), 'rgba(14,18,24,0.82)', '#fff') + 8;
    pill(x, 26, 'Dark-store order run · take 2', F(500, 17), 'rgba(255,255,255,0.86)', '#16202a');
    ctx.font = F(700, 20, 'Barlow Semi Condensed'); const bw = 78; ctx.fillStyle = speedLbl === '1×' ? '#f2c230' : '#ffffff'; ctx.beginPath(); ctx.roundRect(W - 28 - bw, 26, bw, 34, 8); ctx.fill();
    ctx.fillStyle = '#16202a'; ctx.textAlign = 'center'; ctx.textBaseline = 'middle'; ctx.fillText(speedLbl, W - 28 - bw / 2, 44); ctx.textAlign = 'left';
    const g = ctx.createLinearGradient(0, H - 150, 0, H); g.addColorStop(0, 'rgba(10,14,20,0)'); g.addColorStop(1, 'rgba(10,14,20,0.72)'); ctx.fillStyle = g; ctx.fillRect(0, H - 150, W, 150);
    ctx.fillStyle = capCol; ctx.fillRect(28, H - 92, 5, 58);
    ctx.fillStyle = '#fff'; ctx.textBaseline = 'alphabetic'; ctx.font = F(600, 30, 'Barlow Semi Condensed'); ctx.fillText(caption, 46, H - 62);
    ctx.font = F(500, 17); ctx.fillStyle = 'rgba(255,255,255,0.85)'; ctx.fillText(`Shoulder height ${Math.round(R.sh * 1000)} mm · DOLD Hexalift V4 lift · 2 × OpenArm 2.0`, 46, H - 36);
    const lab = `On the floor  ${floorCount}`; ctx.font = F(600, 22, 'Barlow Semi Condensed'); const lw = ctx.measureText(lab).width; ctx.fillStyle = floorCount ? '#ff8a80' : '#fff'; ctx.fillText(lab, W - 28 - lw, H - 62);
    const pw = 220; ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(W - 28 - pw, H - 46, pw, 6); ctx.fillStyle = '#e5484d'; ctx.fillRect(W - 28 - pw, H - 46, pw * Math.min(1, floorCount / 600), 6);
  }
  function smiley(cx, cy, r, col) {
    ctx.strokeStyle = col; ctx.fillStyle = col; ctx.lineWidth = r * 0.12; ctx.lineCap = 'round';
    ctx.beginPath(); ctx.arc(cx, cy, r, 0, Math.PI * 2); ctx.stroke();
    ctx.beginPath(); ctx.arc(cx - r * 0.35, cy - r * 0.25, r * 0.11, 0, Math.PI * 2); ctx.fill(); ctx.beginPath(); ctx.arc(cx + r * 0.35, cy - r * 0.25, r * 0.11, 0, Math.PI * 2); ctx.fill();
    ctx.beginPath(); ctx.arc(cx, cy + r * 0.02, r * 0.55, 0.15 * Math.PI, 0.85 * Math.PI); ctx.stroke();
  }
  function endCard(T) {
    ctx.fillStyle = '#07090c'; ctx.fillRect(0, 0, W, H);
    const a1 = Math.min(1, Math.max(0, (T - K.black - 0.4) / 0.8)), a2 = Math.min(1, Math.max(0, (T - K.black - 2.6) / 0.8)), a3 = Math.min(1, Math.max(0, (T - K.black - 4.2) / 0.8));
    ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    ctx.globalAlpha = a1; ctx.font = F(700, 76, 'Barlow Semi Condensed'); ctx.fillStyle = '#fff';
    const t1 = 'Pace the frontier', w1 = ctx.measureText(t1).width; ctx.fillText(t1, W / 2 - 40, H / 2 - 40); smiley(W / 2 - 40 + w1 / 2 + 52, H / 2 - 66, 30, '#f2c230');
    ctx.globalAlpha = a2; ctx.font = F(500, 32); ctx.fillStyle = 'rgba(255,255,255,0.92)'; ctx.fillText('Our project is open-source: you can help prevent this!', W / 2, H / 2 + 30);
    ctx.globalAlpha = a3; ctx.font = F(600, 24, 'Barlow Semi Condensed'); ctx.fillStyle = '#f2c230'; ctx.fillText('github.com/openAMRobot  ·  docs.openamrobot.ai', W / 2, H / 2 + 92);
    ctx.globalAlpha = 1; ctx.textAlign = 'left';
  }
  function doGlitch() {
    const img = ctx.getImageData(0, 0, W, H); ctx.putImageData(img, 0, 0);
    for (let i = 0; i < 7; i++) { const y = Math.floor(rnd() * H), h = 6 + Math.floor(rnd() * 40), dx = Math.floor((rnd() - 0.5) * 60); ctx.drawImage(oc, 0, y, W, h, dx, y, W, h); }
    ctx.fillStyle = 'rgba(229,72,77,0.10)'; ctx.fillRect(0, 0, W, H);
  }
  // main frame function: advances sequentially
  let T = 0; const SUB = 4;
  window.__chaos = (frame) => {
    const Tn = frame / FPS, dtR = 1 / FPS;
    // time scale: slow motion while the beer falls
    const scale = Tn >= K.slip && Tn < K.slowEnd ? 0.3 : 1; speedLbl = scale < 1 ? '0.3×' : '1×';
    for (let i = 0; i < SUB; i++) { const dt = dtR * scale / SUB; simT += dt; for (const o of bodies) step(o, dt, simT); }
    for (const m of dirty) m.instanceMatrix.needsUpdate = true; dirty.clear(); updPuddles();
    T = Tn;
    if (T < K.black) {
      robotAt(T, dtR * scale); lights(T); camera(T); s.render();
      ctx.drawImage(s.renderer.domElement, 0, 0, W, H);
      if (T < K.dark) hud(T);
      if (glitch) doGlitch();
      if (T < 0.5) { ctx.fillStyle = `rgba(0,0,0,${1 - T / 0.5})`; ctx.fillRect(0, 0, W, H); }
    } else endCard(T);
    return oc.toDataURL('image/jpeg', 0.93);
  };
  window.__chaosK = K;
}, { W, H, FPS });
const N = Math.round(TOTAL * FPS);
const FROM = +(process.env.FROM || 0); const want = MODE === 'full' ? (FROM ? new Set(Array.from({ length: N - FROM }, (_, i) => FROM + i)) : null) : new Set(JSON.parse(process.argv[3] || '[1,3,4,4.6,5.3,6.8,8.2,9.0,9.8,11,12.8,14,16,17.5,19,21.5,24]').map(x => Math.round(x * FPS)));
const t0 = Date.now(); let last = Math.max(...(want ? [...want] : [N - 1]));
for (let f = 0; f <= Math.min(N - 1, last); f++) {
  const keep = !want || want.has(f);
  if (!keep) { await p.evaluate(f => { window.__keepRender = false; window.__chaosSkip = true; return 0; }, f); }
  const d = keep ? await p.evaluate(f => window.__chaos(f), f) : await p.evaluate(f => { const sv = window.__sim.render; window.__sim.render = () => {}; const c = HTMLCanvasElement.prototype.toDataURL; HTMLCanvasElement.prototype.toDataURL = () => ''; window.__chaos(f); window.__sim.render = sv; HTMLCanvasElement.prototype.toDataURL = c; return ''; }, f);
  if (keep) { fs.writeFileSync(`${OUT}/${String(f).padStart(5, '0')}.jpg`, Buffer.from(d.split(',')[1], 'base64')); if (!want ? f % 25 === 0 : true) console.log('frame', f, (f / FPS).toFixed(2), ((Date.now() - t0) / 1000).toFixed(0) + 's'); }
}
await b.close(); srv.close(); console.log('done');
