import * as THREE from 'three';
THREE.Object3D.DEFAULT_UP.set(0, 0, 1);
import { OrbitControls } from 'three/examples/jsm/controls/OrbitControls.js';
import { RoomEnvironment } from 'three/examples/jsm/environments/RoomEnvironment.js';
import { EffectComposer } from 'three/examples/jsm/postprocessing/EffectComposer.js';
import { RenderPass } from 'three/examples/jsm/postprocessing/RenderPass.js';
import { GTAOPass } from 'three/examples/jsm/postprocessing/GTAOPass.js';
import { OutputPass } from 'three/examples/jsm/postprocessing/OutputPass.js';
import { RectAreaLightUniformsLib } from 'three/examples/jsm/lights/RectAreaLightUniformsLib.js';
import { Store, AISLES } from './world.js';
import { Robot, ARM_MAT, ARM_HL } from './robot.js';
import { Analyzer, STOWQ, FINGER_T } from './analysis.js';
import { Planner, Player, Timeline, locCode } from './anim.js';
import { ROBOT, STORE, CAMS, DEG, ARMSPEC, TOTE } from './spec.js';
import { TYPES, productAsset } from './products.js';
import { fk as fkFast, newFK, PT_R } from './kin.js';

const $ = id => document.getElementById(id);
const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const cm = v => (v * 100).toFixed(0), sgn = v => (v >= 0 ? '+' : '−') + Math.abs(v * 100).toFixed(0);
const isPhone = window.matchMedia('(max-width: 900px)').matches;

// ------------------------------------------------------------------------------------------- renderer and scene
const stage = $('stage');
const renderer = new THREE.WebGLRenderer({ antialias: !window.__NOAA, powerPreference: 'high-performance' });
renderer.setPixelRatio(Math.min(isPhone ? 1.5 : 2, window.devicePixelRatio || 1));
renderer.toneMapping = THREE.ACESFilmicToneMapping; renderer.toneMappingExposure = 1.05;
renderer.outputColorSpace = THREE.SRGBColorSpace;
renderer.shadowMap.enabled = true; renderer.shadowMap.type = THREE.PCFSoftShadowMap;
stage.insertBefore(renderer.domElement, stage.firstChild);
const scene = new THREE.Scene();
scene.background = new THREE.Color(0xc9d0ce);
const pmrem = new THREE.PMREMGenerator(renderer);
scene.environment = pmrem.fromScene(new RoomEnvironment(renderer), 0.04).texture;
const camera = new THREE.PerspectiveCamera(42, 1, 0.03, 60); camera.layers.enable(1);
const controls = new OrbitControls(camera, renderer.domElement);
controls.enableDamping = true; controls.dampingFactor = 0.1; controls.screenSpacePanning = true; controls.maxPolarAngle = Math.PI * 0.495;
let needRender = true; controls.addEventListener('change', () => { needRender = true; });

RectAreaLightUniformsLib.init();
scene.add(new THREE.HemisphereLight(0xfdfcf7, 0x6f726c, 0.55));
const key = new THREE.DirectionalLight(0xfff8ee, 1.55); key.position.set(0.7, -2.6, 6.5); key.target.position.set(0.35, -1.05, 0);
key.castShadow = true; key.shadow.mapSize.set(isPhone ? 2048 : 4096, isPhone ? 2048 : 4096); key.shadow.bias = -0.0004; key.shadow.normalBias = 0.015;
Object.assign(key.shadow.camera, { left: -4.0, right: 4.0, top: 2.6, bottom: -2.6, near: 1, far: 10 }); key.shadow.radius = 3;
scene.add(key, key.target);
const areaLights = [];
function setupLights() { areaLights.forEach(l => scene.remove(l)); areaLights.length = 0; for (const [x, y] of store.lightSpots) { const ra = new THREE.RectAreaLight(0xfff6e8, 8, 1.25, 0.12); ra.position.set(x, y, 2.83); ra.lookAt(x, y, 0); scene.add(ra); areaLights.push(ra); } }

// post-processing (ambient occlusion)
const rt = new THREE.WebGLRenderTarget(4, 4, { type: THREE.HalfFloatType, samples: 4 });
const composer = new EffectComposer(renderer, rt);
composer.addPass(new RenderPass(scene, camera));
const gtao = new GTAOPass(scene, camera, 4, 4);
gtao.updateGtaoMaterial({ radius: 0.22, distanceExponent: 1.4, thickness: 1.2, scale: 1.0, samples: 12 });
gtao.blendIntensity = 0.85;
composer.addPass(gtao); composer.addPass(new OutputPass());

// ------------------------------------------------------------------------------------------- world
let store = new Store(scene, 1.10); store.finalize();
const robot = new Robot(scene);
const an = new Analyzer(window.OPENARM, store, (sh, bpX) => robot.selfBoxes(sh, bpX));
const planner = new Planner(robot, store, an), player = new Player(robot, store, scene);
setupLights(); robot.setRiser(0.12); an.cfg.riser = 0.12;

const dyn = new THREE.Group(); dyn.name = 'helpers'; scene.add(dyn);
const helperMat = { target: new THREE.MeshBasicMaterial({ color: 0xf1c40f, depthTest: false, transparent: true }), hit: new THREE.MeshBasicMaterial({ color: 0xe0473a, depthTest: false, transparent: true, opacity: 0.85 }) };
function clearDyn() { while (dyn.children.length) { const c = dyn.children.pop(); c.traverse(o => { if (o.geometry) o.geometry.dispose(); }); } }

// ------------------------------------------------------------------------------------------- locations and state
const SIDE_NAME = { L: 'left run', R: 'right run' };
const LOCS = [];
for (const A of AISLES) for (const side of ['L', 'R']) for (let b = 0; b < STORE.BAYS; b++) for (let lv = 0; lv < STORE.LEVELS.length; lv++) {
  const skus = A.plan[side][b][lv];
  skus.forEach(([type, v], seg) => LOCS.push({ id: `${A.id}${side}${b}${lv}${seg}`, aisle: A.id, side, bay: b, level: lv, seg, type, v, code: `${A.id}${side}-0${b + 1}-${lv + 1}${skus.length > 1 ? 'abc'[seg] : ''}` }));
}
const S = { loc: '3L020', row: 0, stop: 'auto', sh: null, view: 'over', tiles: !isPhone, hq: !isPhone, speed: 3, playing: false, dir: 1, lastRun: null, mtxAisle: 3 };
const locById = id => LOCS.find(l => l.id === id);
const slotOf = (L, row = 0) => store.slotFor(L.aisle, L.side, L.bay, L.level, L.seg, row) || store.slotFor(L.aisle, L.side, L.bay, L.level, L.seg, 0);
function currentSlot() { return slotOf(locById(S.loc), S.row); }

// ------------------------------------------------------------------------------------------- cameras on the robot
const PC = {}; for (const k in CAMS) { PC[k] = new THREE.PerspectiveCamera(50, 1.6, 0.02, 40); PC[k].matrixAutoUpdate = false; }
const _m = new THREE.Matrix4();
function lookM(eye, dir) { const m = new THREE.Matrix4(); m.lookAt(eye, eye.clone().add(dir), V3(0, 0, 1)); m.setPosition(eye); return m; }
function updateCams() {
  robot.g.updateMatrixWorld(true);
  const zw = robot.zed.matrixWorld, gw = robot.gemini.matrixWorld;
  const set = (k, M) => { const c = PC[k], sp = CAMS[k]; c.matrixWorld.copy(M); c.matrixWorldInverse.copy(M).invert();
    c.fov = sp.vfov || 2 * Math.atan(Math.tan(sp.hfov * DEG / 2) * sp.h / sp.w) / DEG; c.aspect = sp.w / sp.h; c.updateProjectionMatrix(); };
  set('head', lookM(V3().setFromMatrixPosition(zw).add(V3(0.003, 0, 0).applyMatrix4(new THREE.Matrix4().extractRotation(zw))), V3(1, 0, 0).transformDirection(zw)));
  set('base', lookM(V3().setFromMatrixPosition(gw).add(V3(0.003, 0, 0).transformDirection(gw)), V3(1, 0, 0).transformDirection(gw)));
  set('wristL', _m.copy(robot.g.matrixWorld).multiply(robot.wrist.wristL.g.matrix));
  set('wristR', _m.copy(robot.g.matrixWorld).multiply(robot.wrist.wristR.g.matrix));
}
const ray = new THREE.Raycaster(); ray.layers.set(0);
function itemWorldMatrix(slot) { return new THREE.Matrix4().compose(slot.pos, new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, slot.yaw)), V3(1, 1, 1)); }
function camEval(slot) {
  updateCams();
  const a = productAsset(slot.type, slot.v), bb = a.geo.boundingBox, M = itemWorldMatrix(slot), s = slot.side === 'L' ? 1 : -1;
  const pts = [V3((bb.min.x + bb.max.x) / 2, bb.min.y * 0.6, (bb.min.z + bb.max.z) / 2)];
  for (const fx of [0.75, -0.75]) for (const fz of [0.15, 0.85]) pts.push(V3(fx * bb.max.x, bb.min.y * 0.9, bb.min.z + fz * (bb.max.z - bb.min.z)));
  const W = pts.map(p => p.applyMatrix4(M)); const out = {};
  const targets = [store.root, robot.g];
  for (const k in PC) {
    const c = PC[k], sp = CAMS[k], pos = V3().setFromMatrixPosition(c.matrixWorld); let vis = 0, outv = 0, occ = 0, far = 0; const xs = [], ys = [];
    for (const p of W) {
      const n = p.clone().applyMatrix4(c.matrixWorldInverse); const depth = -n.z;
      const ndc = p.clone().project(c);
      if (depth <= 0 || Math.abs(ndc.x) > 1 || Math.abs(ndc.y) > 1) { outv++; continue; }
      if (sp.depth && (depth < sp.depth[0] || depth > sp.depth[1])) far++;
      xs.push(ndc.x); ys.push(ndc.y);
      const d = p.clone().sub(pos), L = d.length(); ray.set(pos, d.normalize()); ray.near = 0.035; ray.far = L - 0.015;
      const hits = ray.intersectObjects(targets, true).filter(h => !(h.object === slot.mesh && h.instanceId === slot.index) && h.object.visible && !(h.object.material && h.object.material.transparent && h.object.material.opacity < 0.5));
      if (hits.length) occ++; else vis++;
    }
    const px = xs.length > 1 ? Math.round((Math.max(...xs) - Math.min(...xs)) / 2 * sp.w) : 0;
    let st, cls;
    if (vis >= 4) { st = 'Visible'; cls = 'ok'; } else if (vis >= 1) { st = 'Partly visible'; cls = 'warn'; }
    else if (outv === W.length) { st = 'Out of view'; cls = 'bad'; } else { st = 'Blocked'; cls = 'bad'; }
    out[k] = { st, cls, vis, px, far };
  }
  return out;
}

// ------------------------------------------------------------------------------------------- analysis of the selected location
let RES = null;
function setArmHighlight(side) {
  for (const sd of ['left', 'right']) { const A = robot.arm[sd], m = sd === side ? ARM_HL : ARM_MAT; [A.gBase, ...A.gLinks, ...A.fingers.map(f => f.g)].forEach(g => g.children.forEach(c => { c.material = m; })); }
}
function analyse() {
  stopPlay(true);
  const slot = currentSlot(); if (!slot) return;
  an.cfg.bpX = robot.bpX; an.cfg.riser = robot.riser;
  const stops = an.stopsFor(slot);
  let ev, stopKey;
  if (S.stop === 'auto') { stopKey = stops.pick; ev = stops.res[stopKey]; }
  else if (S.stop === 'manual') { stopKey = null; ev = an.evalShelf(slot, S.sh); }
  else { stopKey = S.stop; ev = stops.res[stopKey]; }
  const sh = ev.sh;
  robot.setPose(ev.pose.x, ev.pose.y, 0); robot.setLift(sh);
  const other = ev.side === 'left' ? 'right' : 'left';
  robot.applyArm(ev.side, ev.q); robot.applyArm(other, STOWQ[other]);
  const T = TYPES[slot.type], jawW = Math.min(1, (T.grasp.w + 2 * ARMSPEC.JAW_CLEAR) / ARMSPEC.JAW_MAX);
  robot.setGrip(ev.side, jawW); robot.setGrip(other, 0.6);
  setArmHighlight(ev.side);
  const gc = an.graspChecks(slot);
  const mom = an.moments(ev.side, ev.q, STOWQ[other], gc.payload.mass <= ARMSPEC.PAYLOAD_PEAK ? T.mass : 0, sh, robot.bpX);
  const tg = an.toteGoal(ev.side, slot.type, 0, 0, 1), place = an.placeAt(ev.side, tg, ROBOT.STOPS.L1000, robot.bpX);
  const cams = camEval(slot);
  RES = { slot, ev, stops, stopKey, gc, mom, place, cams, T };
  drawHelpers(); drawResult(); drawMatrixSel(); updateCfg();
  needRender = true;
}

function drawHelpers() {
  clearDyn(); if (!RES) return;
  const { ev } = RES, pw = robot.matrixFor(ev.pose);
  const P = V3(...ev.goal.p).applyMatrix4(pw);
  const ring = new THREE.Mesh(new THREE.TorusGeometry(0.035, 0.0035, 8, 40), helperMat.target); ring.position.copy(P);
  ring.lookAt(P.clone().add(V3(...ev.goal.a))); dyn.add(ring);
  const arr = new THREE.ArrowHelper(V3(...ev.goal.a).normalize(), P.clone().sub(V3(...ev.goal.a).multiplyScalar(0.18)), 0.15, 0xf1c40f, 0.035, 0.02);
  arr.traverse(o => { if (o.material) { o.material.depthTest = false; o.material.transparent = true; } }); dyn.add(arr);
  if (ev.col) for (const h of ev.col.hits.slice(0, 6)) {
    const o = fkFast(an.ch[ev.side], ev.q, ev.sh, robot.bpX, newFK()), idx = ['shoulder', 'upper arm', 'elbow', 'forearm', 'wrist', 'flange', 'gripper body', 'jaws'].indexOf(h.part);
    const s = new THREE.Mesh(new THREE.SphereGeometry(PT_R[idx] + 0.004, 16, 12), helperMat.hit); s.position.set(...o.pts[idx]).applyMatrix4(pw); dyn.add(s);
  }
  dyn.traverse(o => { o.layers.set(1); o.renderOrder = 5; });
}

function li(cls, k, v) { return `<li><span class="dot ${cls}"></span><span class="k">${k}</span><span class="v">${v}</span></li>`; }
function drawResult() {
  const { slot, ev, stops, stopKey, gc, mom, place, cams, T } = RES, L = locById(S.loc);
  $('t-code').textContent = `${L.code} · aisle ${L.aisle} ${SIDE_NAME[L.side]} · bay ${L.bay + 1} · level ${L.level + 1}, shelf at ${cm(STORE.LEVELS[L.level])} cm · ${['front', '2nd', '3rd'][S.row]} row`;
  $('t-name').textContent = `${T.name}, ${T.mass.toFixed(2).replace(/\.?0+$/, '')} kg`;
  const shTxt = `${Math.round(ev.sh * 1000)} mm shoulder`;
  const reachOk = ev.ok && ev.margin >= 0.03, colOk = ev.col && !ev.col.hits.length;
  const handOk = gc.jaw.ok && (gc.payload.ok);
  const v = $('verdict');
  let main, sub, cls = '';
  if (!gc.jaw.ok || (!gc.payload.ok && !gc.payload.peakOnly)) { main = 'Not pickable with the pinch gripper'; sub = !gc.jaw.ok ? `needs ${cm1(gc.jaw.need)} cm jaw opening, the gripper opens 8.8 cm` : `${T.mass} kg is above the arm payload`; cls = 'bad'; }
  else if (!ev.ok) { main = ev.tooClose ? 'Too close to reach' : 'Out of reach'; sub = ev.tooClose ? `park ${cm(ev.tooClose)} cm farther from the shelf` : ev.margin === null ? `nothing reachable at ${shTxt}` : `short by ${cm(-ev.margin)} cm at ${shTxt}`; cls = 'bad'; }
  else if (!colOk) { main = `Reachable at ${stopKey || shTxt}, arm touches ${ev.col.hits[0].obstacle}`; sub = `margin ${sgn(ev.margin)} cm`; cls = 'warn'; }
  else if (!reachOk) { main = `Marginal at ${stopKey || shTxt}`; sub = `only ${sgn(ev.margin)} cm reach margin`; cls = 'warn'; }
  else { main = `Pickable at ${stopKey || shTxt}`; sub = `${sgn(ev.margin)} cm reach margin, ${ev.side} arm${ev.pitch ? ', approach ' + ev.pitch + '° down' : ''}`; }
  if (S.stop === 'auto' && cls !== 'bad') sub += ' · lowest stop that works';
  v.className = 'verdict ' + cls; $('v-main').textContent = main; $('v-sub').textContent = sub;
  const rows = [];
  const stopTxt = ['L1000', 'L1175', 'L1350'].map(k => { const r = stops.res[k]; return `${k} ${r.margin === null ? '✗' : sgn(r.margin)}${r.col && r.col.hits.length ? '*' : ''}`; }).join(' · ');
  rows.push(li('na', 'Parking', `chassis ${cm(ev.pose.gap)} cm from the shelf front, ${cm(store.aisle - 2 * ROBOT.HW - ev.pose.gap)} cm free on the other side`));
  rows.push(li(reachOk ? 'ok' : ev.ok ? 'warn' : 'bad', 'Reach margin', `${ev.margin === null ? (ev.tooClose ? 'too close' : 'none') : sgn(ev.margin) + ' cm'} at ${shTxt}<br><span class="num" style="font-size:12px;color:var(--mute)">${stopTxt} cm</span>`));
  rows.push(li(!ev.col ? 'na' : colOk ? 'ok' : 'warn', 'Arm clearance', !ev.col ? 'not checked (out of reach)' : colOk ? `${cm(ev.col.clear)} cm to the nearest shelf, tote or column` : ev.col.hits.slice(0, 2).map(h => `${h.part} into ${h.obstacle} by ${cm(-h.d)} cm`).join('; ')));
  rows.push(li(gc.jaw.ok ? (gc.jaw.need > 0.08 ? 'warn' : 'ok') : 'bad', 'Jaw opening', `${T.grasp.kind === 'neck' ? 'neck grasp, ' : T.grasp.kind === 'seal' ? 'top seal grasp, ' : ''}needs ${cm1(gc.jaw.need)} of 8.8 cm${T.grasp.kind === 'neck' ? ` (body ${cm1(T.grasp.body)} cm does not fit)` : ''}`));
  rows.push(li(gc.neighbours.ok ? 'ok' : 'warn', 'Neighbour gap', gc.neighbours.need === 0 ? 'seal grasp, no side clearance needed' : `${Math.round(gc.neighbours.gap * 1000)} mm on the shelf, fingers need ${Math.round(gc.neighbours.need * 1000)} mm${gc.neighbours.ok ? '' : ': space facings wider or nudge first'}`));
  rows.push(li(gc.headroom.ok ? 'ok' : 'warn', 'Headroom', `${cm(gc.headroom.gap)} cm above the item to the next shelf`));
  rows.push(li(gc.payload.ok ? 'ok' : gc.payload.peakOnly ? 'warn' : 'bad', 'Payload', `${T.mass} kg vs ${gc.payload.net.toFixed(1)} kg net nominal (${gc.payload.peak.toFixed(1)} kg peak)`));
  const lat = mom.lat, lng = mom.long;
  rows.push(li(lat <= ROBOT.COL.M_LAT_DYN * 0.6 && lng <= ROBOT.COL.M_LONG_DYN * 0.6 ? 'ok' : lat <= ROBOT.COL.M_LAT_DYN && lng <= ROBOT.COL.M_LONG_DYN ? 'warn' : 'bad', 'Column moment', `lateral ${lat.toFixed(0)} of 225 N·m, lengthwise ${lng.toFixed(0)} of 500 N·m (static, dynamic ratings)`));
  rows.push(li(mom.liftLoad < ROBOT.COL.PUSH * 0.6 ? 'ok' : 'warn', 'Lift load', `${mom.liftLoad.toFixed(0)} N moving mass vs 800 N push`));
  rows.push(li(place.ok ? (place.drop <= 0.02 ? 'ok' : 'warn') : 'bad', 'Tote place', place.ok ? (place.drop <= 0.005 ? `placed on the tote floor at L1000` : `released ${cm(place.drop)} cm above the tote floor at L1000${place.drop > 0.02 ? ': add a tote riser' : ''}`) : 'tote floor not reachable'));
  for (const k of ['head', 'base', ev.side === 'left' ? 'wristL' : 'wristR']) { const c = cams[k]; rows.push(li(c.cls, CAMS[k].name, `${c.st}${c.px ? `, item about ${c.px} px wide` : ''}`)); }
  if (S.lastRun) rows.push(li('na', 'Last run', S.lastRun));
  $('checks').innerHTML = rows.join('');
  for (const k in cams) { const el = document.querySelector(`.tile[data-cam="${k}"] i`); if (el) el.textContent = cams[k].st; }
}
const cm1 = v => (v * 100).toFixed(1);

// ------------------------------------------------------------------------------------------- lift stop matrix
const MTX = {};
function drawMatrix() {
  const head = '<tr><th>Location · cm</th><th>Item</th><th>L1000</th><th>L1175</th><th>L1350</th><th>Jaw</th><th>Payload</th></tr>';
  const body = LOCS.filter(L => L.aisle === S.mtxAisle).map(L => {
    const r = MTX[L.id], T = TYPES[L.type];
    const cells = ['L1000', 'L1175', 'L1350'].map(k => {
      if (!r) return '<td>…</td>';
      const e = r.res[k], c = e.margin === null || !e.ok ? 'bad' : (e.margin >= 0.03 && e.col && !e.col.hits.length) ? 'ok' : 'warn';
      return `<td class="${c}${r.pick === k && r.gc.jaw.ok && (r.gc.payload.ok || r.gc.payload.peakOnly) && e.ok ? ' pick' : ''}">${e.margin === null ? '✗' : sgn(e.margin)}${e.col && e.col.hits.length ? '*' : ''}</td>`;
    }).join('');
    const gc = r ? r.gc : null;
    return `<tr data-loc="${L.id}"${L.id === S.loc ? ' class="sel"' : ''}><td>${L.code} · ${cm(STORE.LEVELS[L.level])}</td><td style="text-align:left;font-family:var(--f-ui)">${T.short}</td>${cells}<td class="${gc ? (gc.jaw.ok ? 'ok' : 'bad') : ''}">${gc ? (gc.jaw.ok ? '✓' : '✗') : '…'}</td><td class="${gc ? (gc.payload.ok ? 'ok' : gc.payload.peakOnly ? 'warn' : 'bad') : ''}">${gc ? (gc.payload.ok ? '✓' : gc.payload.peakOnly ? 'peak' : '✗') : '…'}</td></tr>`;
  }).join('');
  $('mtx').innerHTML = head + body;
}
function drawMatrixSel() { document.querySelectorAll('#mtx tr[data-loc]').forEach(tr => tr.classList.toggle('sel', tr.dataset.loc === S.loc)); }
let mtxJob = 0;
function computeMatrix() {
  const job = ++mtxJob; let i = 0; an.cfg.bpX = robot.bpX; an.cfg.riser = robot.riser;
  for (const k in MTX) delete MTX[k]; drawMatrix();
  const step = () => {
    if (job !== mtxJob) return;
    const list = LOCS.filter(L => L.aisle === S.mtxAisle), L = list[i], slot = slotOf(L);
    const st = an.stopsFor(slot); MTX[L.id] = Object.assign(st, { gc: an.graspChecks(slot) });
    i++; $('mtx-busy').textContent = i < list.length ? `${i} of ${list.length}` : 'done';
    if (i % 4 === 0 || i === list.length) drawMatrix();
    if (i < list.length) setTimeout(step, 0);
  };
  setTimeout(step, 0);
}
$('mtx').addEventListener('click', e => { const tr = e.target.closest('tr[data-loc]'); if (tr) { S.loc = tr.dataset.loc; $('slot').value = S.loc; analyse(); } });
$('b-mtx').addEventListener('click', computeMatrix);
chips('mtxa', v => { S.mtxAisle = +v; mtxJob++; drawMatrix(); computeMatrix(); });

// ------------------------------------------------------------------------------------------- playback
let TL = null, playT = 0;
function setPlayUI() {
  $('b-pause').disabled = !TL; $('b-pause').textContent = S.playing ? 'Pause' : 'Play';
  $('scrub').disabled = !TL;
}
function stopPlay(restore) {
  S.playing = false;
  if (restore && TL) { player.clear(); for (const s of ['left', 'right']) robot.totes[s].userData.items = []; TL = null; }
  setPlayUI();
}
function startRun(slots, mode) {
  stopPlay(true); clearDyn();
  an.cfg.bpX = robot.bpX; an.cfg.riser = robot.riser;
  const tl = new Timeline(), D = store.dock;
  const st = { t: 0, pose: { x: D.x, y: D.y, yaw: D.yaw }, sh: ROBOT.STOPS.L1000, q: { left: STOWQ.left.slice(), right: STOWQ.right.slice() }, grip: { left: 0.6, right: 0.6 }, tote: { left: [], right: [] } };
  planner.init(tl, st);
  const infos = [], skipped = [];
  for (const slot of slots) {
    const gc = an.graspChecks(slot), T = TYPES[slot.type];
    if (!gc.jaw.ok || !(gc.payload.ok || gc.payload.peakOnly)) { skipped.push(T.short); continue; }
    const stops = an.stopsFor(slot), key = stops.pick; if (!key || !stops.res[key] || !stops.res[key].ok) { skipped.push(T.short); continue; }
    infos.push(planner.cycle(tl, st, slot, key));
  }
  let unloaded = [];
  if (mode === 'order' && infos.length) {
    unloaded = planner.unload(tl, st);
    tl.note(st.t, 'Return to the dock'); planner.route(tl, st, store.dock);
  }
  tl.note(st.t, 'Done');
  TL = tl; player.tl = tl; S.dir = mode === 'repl' ? -1 : 1; playT = S.dir > 0 ? 0 : tl.T; S.playing = true; S.runMode = mode; S.runInfos = infos;
  setArmHighlight(null);
  const tot = tl.T, picks = infos.map(i => i.cycle - i.travelT);
  S.lastRun = mode === 'order' ? `${infos.length} items picked in two aisles, ${unloaded.length} unloaded on the packing table; ${(tot / 60).toFixed(1)} min dock to dock, ${(picks.reduce((a, b) => a + b, 0) / Math.max(1, picks.length)).toFixed(0)} s per pick at the shelf${skipped.length ? `; skipped ${skipped.join(', ')}` : ''}`
    : infos.length ? `${mode === 'repl' ? 'Replenish' : 'Pick'} cycle ${tot.toFixed(0)} s from the dock, ${picks[0].toFixed(0)} s at the shelf; lift moves ${infos[0].stop}${infos[0].drop > 0.01 ? `, item released ${cm(infos[0].drop)} cm above the tote floor` : ''}` : 'Nothing to run: this item is not pickable';
  if (RES) drawResult();
  setPlayUI(); needRender = true;
  return tl;
}
function phaseAt(t) { if (!TL) return ''; let s = ''; for (const n of TL.notes) if (n.t <= t + 1e-6) s = n.text; return s; }
$('b-cycle').addEventListener('click', () => { const s = currentSlot(); if (s) startRun([s], 'cycle'); });
$('b-repl').addEventListener('click', () => { const s = currentSlot(); if (s) startRun([s], 'repl'); });
// demo order: four items for each arm, from both aisles
const ORDER = ['3L020', '3R020', '3L130', '3R120', '4L120', '4R020', '4L110', '4R131'];
function orderSlots() { return ORDER.map(id => slotOf(locById(id))).filter(Boolean).sort((a, b) => (a.aisle - b.aisle) || (a.pos.x - b.pos.x)); }
$('b-order').addEventListener('click', () => startRun(orderSlots(), 'order'));

// ------------------------------------------------------------------------------------------- recording and run log
let rec = null;
async function saveFile(name, data) {
  try { const d = window.claude && window.claude.use ? await window.claude.use('downloads') : null; if (d) { await d.save({ filename: name, data }); return 'saved'; } }
  catch (e) { if (e && (e.code === 'declined' || e.code === 'rate_limited')) return e.code; }
  const url = URL.createObjectURL(data instanceof Blob ? data : new Blob([data], { type: 'text/csv' }));
  const a = document.createElement('a'); a.href = url; a.download = name; document.body.appendChild(a); a.click(); a.remove(); setTimeout(() => URL.revokeObjectURL(url), 10000);
  return 'saved';
}
function setRecUI(msg) { $('b-rec').textContent = rec ? 'Stop recording' : 'Record order video'; $('b-rec').classList.toggle('rec', !!rec); if (msg !== undefined) $('rec-msg').textContent = msg; }
function stopRec() { if (rec && rec.state !== 'inactive') rec.stop(); }
$('b-rec').addEventListener('click', () => {
  if (rec) { stopRec(); return; }
  const cv = renderer.domElement;
  if (!cv.captureStream || !window.MediaRecorder) { setRecUI('This browser cannot record the 3D view. Use a screen recorder instead.'); return; }
  const mime = ['video/webm;codecs=vp9', 'video/webm;codecs=vp8', 'video/webm', 'video/mp4'].find(t => MediaRecorder.isTypeSupported(t));
  const chunks = [];
  rec = new MediaRecorder(cv.captureStream(30), { mimeType: mime, videoBitsPerSecond: 12e6 });
  rec.ondataavailable = e => { if (e.data && e.data.size) chunks.push(e.data); };
  rec.onstop = async () => {
    const ext = mime.includes('mp4') ? 'mp4' : 'webm', blob = new Blob(chunks, { type: mime.split(';')[0] }); rec = null;
    setRecUI(`Recorded ${(blob.size / 1e6).toFixed(1)} MB. Saving…`);
    const r = await saveFile(`OpenAMRobot2-order-run-${S.speed}x.${ext}`, blob);
    setRecUI(r === 'saved' ? `Video saved (${(blob.size / 1e6).toFixed(1)} MB, ${ext.toUpperCase()}).` : 'Save cancelled.');
  };
  startRun(orderSlots(), 'order'); setView('follow');
  rec.start(500); setRecUI(`Recording at ${S.speed}× speed. It stops by itself when the robot is back at the dock.`);
});
function runLogCSV() {
  if (!TL) return null;
  const rows = [['time_s', 'event', 'item', 'location', 'arm', 'lift_stop']];
  for (const n of TL.notes) rows.push([n.t.toFixed(1), n.text, '', '', '', '']);
  for (const it of TL.items) {
    const T = TYPES[it.slot.type];
    rows.push([it.tGrasp.toFixed(1), 'grasped on shelf', T.name, it.code, it.side, it.stop]);
    rows.push([it.tRelease.toFixed(1), 'placed in tote', T.name, it.code, it.side, 'L1000']);
    if (it.tTable) rows.push([it.tTable.toFixed(1), 'placed on packing table', T.name, it.code, it.side, 'L1000']);
  }
  const head = rows.shift(); rows.sort((a, b) => a[0] - b[0]);
  const cfg = [['# OpenAMRobot 2.0 dark-store simulation run log'], ['# ' + robot.configId() + ` · tote riser ${Math.round(robot.riser * 1000)} mm · aisle ${store.aisle.toFixed(2)} m · total ${TL.T.toFixed(1)} s`]];
  return cfg.concat([head], rows).map(r => r.map(v => /[",]/.test(v) ? `"${String(v).replace(/"/g, '""')}"` : v).join(',')).join('\n');
}
$('b-log').addEventListener('click', async () => {
  const csv = runLogCSV(); if (!csv) { setRecUI('Run a pick cycle or an order first.'); return; }
  const r = await saveFile(`OpenAMRobot2-run-log.csv`, csv); setRecUI(r === 'saved' ? 'Run log saved (CSV).' : 'Save cancelled.');
});
$('b-pause').addEventListener('click', () => { if (!TL) return; if (!S.playing && (playT >= TL.T || playT <= 0)) playT = S.dir > 0 ? 0 : TL.T; S.playing = !S.playing; setPlayUI(); });
$('b-reset').addEventListener('click', () => { stopPlay(true); S.lastRun = null; analyse(); });
$('scrub').addEventListener('input', e => { if (!TL) return; S.playing = false; playT = TL.T * e.target.value / 1000; player.apply(playT); setPlayUI(); needRender = true; });
document.querySelectorAll('#speed button').forEach(b => b.addEventListener('click', () => { S.speed = +b.dataset.s; document.querySelectorAll('#speed button').forEach(x => x.classList.toggle('on', x === b)); }));

// ------------------------------------------------------------------------------------------- UI wiring
function chips(id, fn) { const box = $(id); box.addEventListener('click', e => { const b = e.target.closest('button'); if (!b) return; box.querySelectorAll('button').forEach(x => x.classList.toggle('on', x === b)); fn(b.dataset.v); }); }
function buildSelect() {
  const sel = $('slot'); sel.innerHTML = '';
  for (const A of AISLES) for (const side of ['L', 'R']) {
    const og = document.createElement('optgroup'); og.label = `Aisle ${A.id}, ${side === 'L' ? 'left' : 'right'} run: ${A.title[side === 'L' ? 0 : 1]}`;
    LOCS.filter(l => l.aisle === A.id && l.side === side).forEach(l => { const o = document.createElement('option'); o.value = l.id; o.textContent = `${l.code} · ${cm(STORE.LEVELS[l.level])} cm · ${TYPES[l.type].short}`; og.appendChild(o); });
    sel.appendChild(og);
  }
  sel.value = S.loc;
}
$('slot').addEventListener('change', e => { S.loc = e.target.value; analyse(); });
chips('rowc', v => { S.row = +v; analyse(); });
chips('stopc', v => { S.stop = v; if (v !== 'auto') { $('sh').value = ROBOT.STOPS[v] * 1000; } analyse(); syncSh(); });
$('sh').addEventListener('input', e => { S.stop = 'manual'; S.sh = e.target.value / 1000; document.querySelectorAll('#stopc button').forEach(x => x.classList.remove('on')); syncSh(); analyse(); });
function syncSh() { $('sh-v').textContent = `${Math.round(robot.sh * 1000)} mm`; }
chips('bpc', v => { robot.setBP(v); analyse(); for (const k in MTX) delete MTX[k]; drawMatrix(); });
$('hp').addEventListener('input', e => { robot.setHeadPitch(+e.target.value); $('hp-v').textContent = e.target.value + '°'; analyse(); });
chips('btc', v => { robot.setBaseTilt(+v); analyse(); });
chips('riserc', v => { robot.setRiser(+v); analyse(); });
chips('apc', v => { an.cfg.approach = v; analyse(); for (const k in MTX) delete MTX[k]; drawMatrix(); });
$('gap').addEventListener('input', e => { an.cfg.gap = +e.target.value; an.cfg.gapAuto = false; $('gap-v').textContent = cm(an.cfg.gap) + ' cm'; document.querySelectorAll('#gapc button').forEach(b => b.classList.toggle('on', b.dataset.v === 'fixed')); analyse(); for (const k in MTX) delete MTX[k]; drawMatrix(); });
chips('gapc', v => { an.cfg.gapAuto = v === 'auto'; analyse(); for (const k in MTX) delete MTX[k]; drawMatrix(); });
$('ahead').addEventListener('input', e => { an.cfg.ahead = +e.target.value; $('ahead-v').textContent = sgn(an.cfg.ahead) + ' cm'; analyse(); });
chips('aislec', v => {
  stopPlay(true);
  scene.remove(store.root); store.root.traverse(o => { if (o.geometry) o.geometry.dispose(); });
  store = new Store(scene, +v); store.finalize(); an.store = store; planner.store = store; player.store = store; setupLights();
  for (const k in MTX) delete MTX[k]; drawMatrix(); analyse();
});
function updateCfg() { $('cfgid').textContent = robot.configId() + ` · lift ${Math.round(robot.sh * 1000)} mm`; syncSh(); }
$('b-tiles').addEventListener('click', e => { S.tiles = !S.tiles; e.target.classList.toggle('on', S.tiles); $('tiles').hidden = !S.tiles; needRender = true; });
$('b-q').addEventListener('click', e => { S.hq = !S.hq; e.target.classList.toggle('on', S.hq); resize(); needRender = true; });

// views
function setView(v) {
  S.view = v; document.querySelectorAll('[data-view]').forEach(b => b.classList.toggle('on', b.dataset.view === v));
  const p = robot.g.position, x = p.x, y = p.y;
  const cy = planner.aisleOf(y).cy;
  const V = { store: [[-3.1, -2.95, 2.75], [0.9, -0.7, 0.45]], over: [[x - 1.45, cy + (y - cy) * 0.25 - 0.3, 2.3], [x + 0.3, cy + (y - cy) * 0.6, 0.72]], aisle: [[x - 1.6, cy + (y - cy) * 0.2, 1.55], [x + 0.6, cy + (y - cy) * 0.2, 0.95]], side: [[x + 0.1, -store.aisle / 2 - 0.02 + (y > 0 ? 0 : 0), 1.2], [x + 0.1, y + 1, 0.95]],
    top: [[x + 0.15, y - 0.01, 4.2], [x + 0.15, y, 0]], follow: [[x - 1.5, y - 1.0, 1.9], [x, y, 0.8]] };
  if (v === 'side') { const s = y >= cy ? -1 : 1; V.side = [[x + 0.1, cy + s * (store.aisle / 2 - 0.05), 1.15], [x + 0.1, cy - s * 1, 0.95]]; }
  if (v === 'follow') { followCam(); controls.update(); needRender = true; return; }
  const [c, t] = V[v]; camera.position.set(...c); controls.target.set(...t); controls.update(); needRender = true;
}
document.querySelectorAll('[data-view]').forEach(b => b.addEventListener('click', () => setView(b.dataset.view)));

// click a product to select its location
let downAt = null;
renderer.domElement.addEventListener('pointerdown', e => { downAt = [e.clientX, e.clientY]; });
renderer.domElement.addEventListener('pointerup', e => {
  if (!downAt || Math.hypot(e.clientX - downAt[0], e.clientY - downAt[1]) > 4) return;
  const r = renderer.domElement.getBoundingClientRect(), m = new THREE.Vector2(((e.clientX - r.left) / r.width) * 2 - 1, -((e.clientY - r.top) / r.height) * 2 + 1);
  const rc = new THREE.Raycaster(); rc.setFromCamera(m, camera);
  const meshes = Object.values(store.inst).map(i => i.mesh).filter(Boolean);
  const h = rc.intersectObjects(meshes, false)[0]; if (!h) return;
  const key = h.object.name.replace('products_', ''), sl = store.inst[key].list[h.instanceId]; if (!sl) return;
  S.loc = `${sl.aisle}${sl.side}${sl.bay}${sl.level}${sl.seg}`; S.row = Math.min(2, sl.row); $('slot').value = S.loc;
  document.querySelectorAll('#rowc button').forEach(b => b.classList.toggle('on', +b.dataset.v === S.row));
  analyse();
});

// ------------------------------------------------------------------------------------------- render loop
function tileRects() {
  const c = renderer.domElement.getBoundingClientRect();
  return [...document.querySelectorAll('.tile')].map(el => { const r = el.getBoundingClientRect(); return { k: el.dataset.cam, x: r.left - c.left, y: c.bottom - r.bottom, w: r.width, h: r.height }; });
}
function render() {
  if (S.hq) composer.render(); else { renderer.setRenderTarget(null); renderer.render(scene, camera); }
  if (S.tiles) {
    updateCams(); renderer.setScissorTest(true);
    const bg = scene.background;
    for (const t of tileRects()) {
      if (t.w < 10) continue;
      const c = PC[t.k]; c.aspect = t.w / t.h; c.updateProjectionMatrix();
      renderer.setViewport(t.x, t.y, t.w, t.h); renderer.setScissor(t.x, t.y, t.w, t.h);
      renderer.render(scene, c);
    }
    renderer.setScissorTest(false); const s = renderer.getSize(new THREE.Vector2()); renderer.setViewport(0, 0, s.x, s.y);
  }
}
function followCam(dt) {
  const p = robot.g.position, yaw = robot.pose.yaw || 0, c = Math.cos(yaw), sn = Math.sin(yaw), k = dt === undefined ? 1 : Math.min(1, dt * 2.5);
  const camT = V3(p.x - 1.65 * c + 0.25 * sn, p.y - 1.65 * sn - 0.25 * c, 1.95), tgtT = V3(p.x + 0.55 * c, p.y + 0.55 * sn, 0.75);
  camera.position.lerp(camT, k); controls.target.lerp(tgtT, k);
}
let last = performance.now();
function loop(now) {
  requestAnimationFrame(loop);
  const dt = Math.min(0.1, (now - last) / 1000); last = now;
  if (S.playing && TL) {
    playT += dt * S.speed * S.dir;
    if (playT >= TL.T || playT <= 0) { playT = Math.max(0, Math.min(TL.T, playT)); S.playing = false; setPlayUI(); if (rec) setTimeout(stopRec, 600); }
    player.apply(playT);
    $('scrub').value = Math.round(playT / TL.T * 1000);
    $('tread').textContent = `${playT.toFixed(1)} / ${TL.T.toFixed(0)} s`; $('phase').textContent = phaseAt(playT);
    if (S.view === 'follow') followCam(dt);
    updateCfg(); needRender = true;
  }
  if (controls.update()) needRender = true;
  if (needRender) { needRender = false; render(); }
}
function resize() {
  const w = stage.clientWidth, h = stage.clientHeight;
  renderer.setPixelRatio(S.hq ? Math.min(isPhone ? 1.5 : 2, window.devicePixelRatio || 1) : 1);
  renderer.setSize(w, h, false); camera.aspect = w / h; camera.updateProjectionMatrix();
  composer.setPixelRatio(renderer.getPixelRatio()); composer.setSize(w, h); needRender = true;
}
new ResizeObserver(resize).observe(stage);

// ------------------------------------------------------------------------------------------- start
$('tiles').hidden = !S.tiles; $('b-tiles').classList.toggle('on', S.tiles); $('b-q').classList.toggle('on', S.hq);
robot.setHeadPitch(30); $('hp-v').textContent = '30°'; $('gap-v').textContent = '5 cm'; $('ahead-v').textContent = '+10 cm'; setRecUI('');
buildSelect(); drawMatrix(); resize(); analyse(); setView('over'); setPlayUI();
requestAnimationFrame(loop);
if (location.hash !== '#nomtx') setTimeout(computeMatrix, 400);
window.__sim = { THREE, renderer, scene, key, composer, gtao, rt, camera, controls, closeUp: (x, y, z, tx, ty, tz) => { camera.position.set(x, y, z); controls.target.set(tx, ty, tz); controls.update(); needRender = true; }, stopMatrix: () => { mtxJob++; }, applyAt: t => { playT = t; player.apply(t); needRender = true; }, robot, store, an, analyse, startRun, S, render: () => render(), setView, get TL() { return TL; }, player, MTX, LOCS };
