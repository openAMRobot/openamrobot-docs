import * as THREE from 'three';
import { STORE } from './spec.js';
import { TYPES, productAsset } from './products.js';
import { concreteTextures, priceStripTex, signTex, perforatedTex, pegboardTex, chillerDoorTex, rand, canvasTex, barcode } from './textures.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
export function boxMesh(w, d, h, mat, x, y, z, cast = true) {
  const m = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), mat); m.position.set(x, y, z);
  m.castShadow = cast; m.receiveShadow = true; return m;
}
export function boxOf(m) {
  const p = m.geometry.parameters, c = m.position;
  return new THREE.Box3(V3(c.x - p.width / 2, c.y - p.height / 2, c.z - p.depth / 2), V3(c.x + p.width / 2, c.y + p.height / 2, c.z + p.depth / 2));
}

// Planogram per aisle and run: [bay][level] = list of SKUs [type, variant] sharing the bay width. Level 0 is the floor deck.
// 'L' = run on the aisle's +Y side, 'R' = run on its -Y side. Heavy and bulky goods low, snacks high.
export const AISLES = [
  { id: 3, title: ['Drinks · Dairy', 'Beer · Water · Soft drinks'], plan: {
    L: [
      [[['pack', 0]], [['milk', 0], ['milk', 1]], [['juice', 0], ['icedtea', 0]], [['pretzel', 0], ['tube', 0]], [['chips', 0], ['chips', 1]]],
      [[['pack', 1]], [['milk', 1], ['milk', 0]], [['juice', 1], ['juice', 0]], [['can', 0], ['energy', 0]], [['chips', 1], ['gummy', 0]]],
      [[['pack', 0]], [['milk', 0], ['ketchup', 0]], [['water', 0], ['icedtea', 1]], [['can', 1], ['energy', 1]], [['chips', 2], ['nuts', 0]]],
    ],
    R: [
      [[['crate', 0]], [['can', 0], ['can', 1]], [['beer', 0]], [['beer', 1], ['energy', 0]], [['chips', 0], ['tube', 1]]],
      [[['crate', 1]], [['juice', 0], ['icedtea', 0]], [['water', 1]], [['beer', 0], ['beer', 1]], [['pretzel', 0], ['gummy', 1]]],
      [[['pack', 1]], [['milk', 1]], [['juice', 1], ['water', 0]], [['beer', 1]], [['chips', 1], ['nuts', 1]]],
    ] } },
  { id: 4, title: ['Snacks · Sweets', 'Breakfast · Pantry · Drinks'], plan: {
    L: [
      [[['cereal', 0], ['cereal', 1]], [['cookies', 0], ['cookies', 1]], [['choco', 0], ['choco', 1], ['choco', 2]], [['gummy', 0], ['gummy', 1]], [['chips', 0], ['chips', 2]]],
      [[['cereal', 1], ['cereal', 2]], [['pasta', 0], ['pasta', 1]], [['tube', 0], ['tube', 1]], [['nuts', 0], ['nuts', 1]], [['gummy', 1], ['chips', 1]]],
      [[['coffee', 0], ['coffee', 1]], [['ketchup', 0], ['ketchup', 1]], [['choco', 1], ['choco', 0]], [['cookies', 0], ['pretzel', 0]], [['chips', 2], ['tube', 0]]],
    ],
    R: [
      [[['pack', 0]], [['energy', 0], ['energy', 1]], [['icedtea', 0], ['icedtea', 1]], [['choco', 2], ['choco', 1]], [['tube', 1], ['tube', 0]]],
      [[['cereal', 0], ['coffee', 1]], [['coffee', 0], ['pasta', 0]], [['cookies', 1], ['cookies', 0]], [['gummy', 0], ['nuts', 0]], [['chips', 0], ['chips', 1]]],
      [[['crate', 0]], [['ketchup', 1], ['ketchup', 0]], [['pasta', 1], ['pasta', 0]], [['tube', 0], ['energy', 1]], [['gummy', 1], ['chips', 2]]],
    ] } },
];

export class Store {
  constructor(scene, aisle = 1.10) {
    this.scene = scene; this.root = new THREE.Group(); this.root.name = 'store'; scene.add(this.root);
    this.aisle = aisle;
    const A = aisle, D = STORE.DEPTH;
    this.aisles = AISLES.map((a, i) => Object.assign({}, a, { cy: -i * (A + 2 * D) }));
    this.yN = A / 2 + D + 0.02; this.yS = this.aisles[this.aisles.length - 1].cy - A / 2 - D - 0.02;
    this.X0 = -3.3; this.X1 = 4.0; this.H = 3.1;
    // packing table (order handover) against the west wall, between the aisle mouths
    this.table = { x0: this.X0 + 0.02, x1: this.X0 + 0.02 + 0.66, yc: (this.aisles[0].cy + this.aisles[1].cy) / 2, len: 1.5, h: 0.90 };
    this.dock = { x: -1.25, y: this.aisles[1].cy - 0.05, yaw: 0 };
    this.slots = []; this.colliders = []; this.inst = {};
    this.mats = {
      wall: new THREE.MeshStandardMaterial({ color: 0xe9eae7, roughness: 0.92 }),
      upright: new THREE.MeshStandardMaterial({ color: 0x3a3f45, roughness: 0.5, metalness: 0.5, map: perforatedTex() }),
      shelf: new THREE.MeshStandardMaterial({ color: 0xeef0f0, roughness: 0.42, metalness: 0.25 }),
      lip: new THREE.MeshStandardMaterial({ color: 0xd5d8da, roughness: 0.4, metalness: 0.3 }),
      kick: new THREE.MeshStandardMaterial({ color: 0x3a3f45, roughness: 0.5, metalness: 0.4 }),
      peg: new THREE.MeshStandardMaterial({ color: 0xffffff, map: pegboardTex(), roughness: 0.8 }),
      yellow: new THREE.MeshStandardMaterial({ color: 0xf1c40f, roughness: 0.6 }),
      dark: new THREE.MeshStandardMaterial({ color: 0x1f2328, roughness: 0.6 }),
      wood: new THREE.MeshStandardMaterial({ color: 0xc9a46a, roughness: 0.85 }),
      wire: new THREE.MeshStandardMaterial({ color: 0xb8bec4, roughness: 0.35, metalness: 0.8 }),
      steel: new THREE.MeshStandardMaterial({ color: 0x9aa2aa, roughness: 0.35, metalness: 0.8 }),
      top: new THREE.MeshStandardMaterial({ color: 0xd8c3a0, roughness: 0.55 }),
      kraft: new THREE.MeshStandardMaterial({ color: 0xb8875a, roughness: 0.9, side: THREE.DoubleSide }),
    };
    const c = concreteTextures(); c.map.repeat.set(4, 3); c.rough.repeat.set(4, 3);
    this.mats.floor = new THREE.MeshStandardMaterial({ map: c.map, roughnessMap: c.rough, roughness: 0.55, metalness: 0.0, color: 0xc4c6c4 });
    this.build();
  }

  aisleById(id) { return this.aisles.find(a => a.id === id); }

  build() {
    const R = this.root, A = this.aisle, B = STORE.BAYS * STORE.BAY_W, { X0, X1, H, yN, yS } = this, W = yN - yS, yc = (yN + yS) / 2;
    const fl = new THREE.Mesh(new THREE.PlaneGeometry(X1 - X0, W), this.mats.floor); fl.position.set((X0 + X1) / 2, yc, 0); fl.receiveShadow = true; R.add(fl);
    const wl = new THREE.Mesh(new THREE.PlaneGeometry(X1 - X0, H), this.mats.wall); wl.rotation.set(Math.PI / 2, 0, 0); wl.position.set((X0 + X1) / 2, yN, H / 2);
    const wr = new THREE.Mesh(new THREE.PlaneGeometry(X1 - X0, H), this.mats.wall); wr.rotation.set(Math.PI / 2, Math.PI, 0); wr.position.set((X0 + X1) / 2, yS, H / 2);
    const we = new THREE.Mesh(new THREE.PlaneGeometry(W, H), this.mats.wall); we.rotation.set(Math.PI / 2, -Math.PI / 2, 0); we.position.set(X1, yc, H / 2);
    const ww = new THREE.Mesh(new THREE.PlaneGeometry(W, H), this.mats.wall); ww.rotation.set(Math.PI / 2, Math.PI / 2, 0); ww.position.set(X0, yc, H / 2);
    for (const w of [wl, wr, we, ww]) { w.receiveShadow = true; R.add(w); }
    const ceil = new THREE.Mesh(new THREE.PlaneGeometry(X1 - X0, W), new THREE.MeshStandardMaterial({ color: 0xf2f2f0, roughness: 0.95 }));
    ceil.rotation.x = Math.PI; ceil.position.set((X0 + X1) / 2, yc, H); R.add(ceil);
    R.add(boxMesh(X1 - X0, 0.012, 0.08, this.mats.kick, (X0 + X1) / 2, yN - 0.006, 0.04, false));
    R.add(boxMesh(X1 - X0, 0.012, 0.08, this.mats.kick, (X0 + X1) / 2, yS + 0.006, 0.04, false));
    const batten = new THREE.MeshStandardMaterial({ color: 0xffffff, emissive: 0xfff7ea, emissiveIntensity: 2.2 });
    this.lightSpots = [];
    for (const a of this.aisles) for (const x of [0.5, 1.5, 2.5]) { R.add(boxMesh(1.25, 0.12, 0.04, batten, x, a.cy, H - 0.25, false)); this.lightSpots.push([x, a.cy]); }
    for (const x of [-2.4, -1.0]) for (const y of [this.aisles[0].cy - 0.2, this.aisles[1].cy + 0.2]) { R.add(boxMesh(1.25, 0.12, 0.04, batten, x, y, H - 0.25, false)); this.lightSpots.push([x, y]); }

    for (const a of this.aisles) {
      for (const s of [1, -1]) R.add(boxMesh(B + 0.4, 0.05, 0.002, this.mats.yellow, B / 2, a.cy + s * (A / 2 - 0.06), 0.001, false));
      for (const side of ['L', 'R']) this.buildRun(a, side);
      const hang = new THREE.Mesh(new THREE.PlaneGeometry(0.9, 0.3), new THREE.MeshStandardMaterial({ map: signTex(['AISLE ' + a.id, a.id === 3 ? 'drinks & dairy' : 'snacks & pantry'], '#f1c40f', '#1d2733'), roughness: 0.6, side: THREE.DoubleSide }));
      hang.rotation.set(Math.PI / 2, -Math.PI / 2, 0); hang.position.set(-0.2, a.cy, 2.55); R.add(hang);
      R.add(boxMesh(0.01, 0.01, 0.4, this.mats.wire, -0.2, a.cy + 0.3, 2.9, false)); R.add(boxMesh(0.01, 0.01, 0.4, this.mats.wire, -0.2, a.cy - 0.3, 2.9, false));
    }
    // end panel of the middle gondola
    const mid = this.aisles[0].cy - A / 2 - STORE.DEPTH;
    R.add(boxMesh(0.03, 2 * STORE.DEPTH, STORE.HEIGHT, this.mats.lip, -0.03, mid, STORE.HEIGHT / 2));
    const endSign = new THREE.Mesh(new THREE.PlaneGeometry(0.8, 0.32), new THREE.MeshStandardMaterial({ map: signTex(['Robot pick zone', 'OpenAMRobot at work · keep aisles clear'], '#0f8f86', '#ffffff', 1024, 410), roughness: 0.6 }));
    endSign.rotation.set(Math.PI / 2, -Math.PI / 2, 0); endSign.position.set(-0.05, mid, 1.65); R.add(endSign);
    this.buildChillers();
    this.buildStaging();
  }

  buildRun(a, side) {
    const R = this.root, s = side === 'L' ? 1 : -1, A = this.aisle, D = STORE.DEPTH, yF = a.cy + s * A / 2, yB = a.cy + s * (A / 2 + D), yC = (yF + yB) / 2;
    const run = new THREE.Group(); run.name = `run_${a.id}${side}`; R.add(run);
    const B = STORE.BAYS * STORE.BAY_W, U = STORE.UPRIGHT, code = `${a.id}${side}`;
    const back = new THREE.Mesh(new THREE.PlaneGeometry(B, STORE.HEIGHT), this.mats.peg); back.rotation.set(Math.PI / 2, s > 0 ? 0 : Math.PI, 0);
    back.position.set(B / 2, yB - s * 0.01, STORE.HEIGHT / 2); back.receiveShadow = true; run.add(back);
    for (let i = 0; i <= STORE.BAYS; i++) {
      const x = i * STORE.BAY_W;
      for (const y of [yF + s * 0.015, yB - s * 0.03]) {
        run.add(boxMesh(U, 0.03, STORE.HEIGHT, this.mats.upright, x, y, STORE.HEIGHT / 2));
        this.colliders.push({ name: 'upright', box: new THREE.Box3(V3(x - U / 2, y - 0.015, 0), V3(x + U / 2, y + 0.015, STORE.HEIGHT)) });
      }
      STORE.LEVELS.forEach(z => run.add(boxMesh(0.006, D - 0.02, 0.07, this.mats.upright, x, yC, z - 0.06)));
      if (i < STORE.BAYS) {
        const lbl = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.05), new THREE.MeshStandardMaterial({ map: signTex([`${code}-0${i + 1}`], '#ffffff', '#111111', 256, 120), roughness: 0.7 }));
        lbl.rotation.set(Math.PI / 2, s > 0 ? 0 : Math.PI, 0); lbl.position.set(x + 0.1, yF - s * 0.001, STORE.HEIGHT - 0.06); run.add(lbl);
      }
    }
    run.add(boxMesh(B, 0.02, STORE.LEVELS[0] - STORE.SHELF_T, this.mats.kick, B / 2, yF + s * 0.012, (STORE.LEVELS[0] - STORE.SHELF_T) / 2));
    const hdr = new THREE.Mesh(new THREE.PlaneGeometry(B, 0.26), new THREE.MeshStandardMaterial({ map: signTex([a.title[side === 'L' ? 0 : 1], `Aisle ${a.id} · ${side === 'L' ? 'left' : 'right'} run · bays ${code}-01 to ${code}-03`], side === 'L' ? '#1d2733' : '#0f8f86'), roughness: 0.6 }));
    hdr.rotation.set(Math.PI / 2, s > 0 ? 0 : Math.PI, 0); hdr.position.set(B / 2, yF - s * 0.02, STORE.HEIGHT + 0.18); R.add(hdr);
    for (let b = 0; b < STORE.BAYS; b++) {
      const x0 = b * STORE.BAY_W + U / 2 + 0.003, x1 = (b + 1) * STORE.BAY_W - U / 2 - 0.003, w = x1 - x0, xc = (x0 + x1) / 2;
      STORE.LEVELS.forEach((z, lv) => {
        const sh = boxMesh(w, D - 0.02, STORE.SHELF_T, this.mats.shelf, xc, yC - s * 0.005, z - STORE.SHELF_T / 2); run.add(sh);
        this.colliders.push({ name: `shelf ${code}-0${b + 1} level ${lv + 1}`, box: boxOf(sh) });
        run.add(boxMesh(w, 0.014, 0.038, this.mats.lip, xc, yF - s * 0.002, z - 0.017));
        const skus = a.plan[side][b][lv], seg = w / skus.length;
        const labels = (skus.length === 1 ? [skus[0], skus[0], skus[0]] : skus).map(([t]) => ({ name: TYPES[t].short, price: TYPES[t].price }));
        const tex = priceStripTex(`${code}0${b + 1}-${lv + 1}`, labels);
        const strip = new THREE.Mesh(new THREE.PlaneGeometry(w, 0.032), new THREE.MeshStandardMaterial({ map: tex, roughness: 0.5 }));
        strip.rotation.set(Math.PI / 2, s > 0 ? 0 : Math.PI, 0); strip.position.set(xc, yF - s * 0.0095, z - 0.017); run.add(strip);
        this._multi = skus.length > 1; skus.forEach(([type, v], k) => this.fill(a, side, b, lv, k, x0 + k * seg + (k ? 0.01 : 0), x0 + (k + 1) * seg - (k < skus.length - 1 ? 0.01 : 0), z, type, v));
      });
    }
  }

  fill(a, side, b, lv, seg, x0, x1, z, type, v) {
    const T = TYPES[type], s = side === 'L' ? 1 : -1, A = this.aisle, D = STORE.DEPTH;
    const pitchX = T.fx + T.gap, nx = Math.max(1, Math.floor((x1 - x0 + T.gap) / pitchX));
    const rows = Math.max(1, Math.min(type === 'pack' || type === 'crate' ? 2 : 5, Math.floor((D - 0.04) / (T.d + 0.006))));
    const xs = []; const span = nx * pitchX - T.gap; for (let i = 0; i < nx; i++) xs.push(x0 + (x1 - x0 - span) / 2 + T.fx / 2 + i * pitchX);
    const key = type + v; let im = this.inst[key]; if (!im) { im = { list: [] }; this.inst[key] = im; }
    for (let r = 0; r < rows; r++) for (let i = 0; i < nx; i++) {
      if (r > 0 && rand() < 0.08) continue;
      const y = a.cy + s * (A / 2 + 0.018) + s * (T.d / 2 + r * (T.d + 0.006));
      const pos = V3(xs[i] + (rand() - 0.5) * 0.004, y, z), yaw = (s > 0 ? 0 : Math.PI) + (rand() - 0.5) * 0.06;
      const slot = { multi: this._multi, type, v, aisle: a.id, cy: a.cy, side, bay: b, level: lv, seg, row: r, col: i, pos, yaw, key, index: im.list.length, picked: false };
      im.list.push(slot); this.slots.push(slot);
    }
  }

  finalize() {
    const dummy = new THREE.Object3D();
    for (const key in this.inst) {
      const im = this.inst[key], s0 = im.list[0], asset = productAsset(s0.type, s0.v);
      const mesh = new THREE.InstancedMesh(asset.geo, asset.mats, im.list.length);
      mesh.castShadow = true; mesh.receiveShadow = true; mesh.name = 'products_' + key;
      im.list.forEach((sl, i) => { dummy.position.copy(sl.pos); dummy.rotation.set(0, 0, sl.yaw); dummy.scale.set(1, 1, 1); dummy.updateMatrix(); mesh.setMatrixAt(i, dummy.matrix); sl.mesh = mesh; });
      mesh.instanceMatrix.needsUpdate = true; mesh.computeBoundingSphere();
      im.mesh = mesh; this.root.add(mesh);
    }
  }

  hideSlot(sl, hide = true) {
    const m = new THREE.Matrix4(); sl.mesh.getMatrixAt(sl.index, m);
    const p = new THREE.Vector3(), q = new THREE.Quaternion(), sc = new THREE.Vector3(); m.decompose(p, q, sc);
    m.compose(p, q, hide ? V3(1e-5, 1e-5, 1e-5) : V3(1, 1, 1)); sl.mesh.setMatrixAt(sl.index, m); sl.mesh.instanceMatrix.needsUpdate = true;
    sl.picked = hide;
  }

  // centre-most free instance of one SKU segment
  slotFor(aisle, side, bay, level, seg = 0, row = 0) {
    const list = this.slots.filter(s => s.aisle === aisle && s.side === side && s.bay === bay && s.level === level && s.seg === seg && s.row === row && !s.picked);
    if (!list.length) return null;
    const xs = list.map(s => s.pos.x), xc = (Math.min(...xs) + Math.max(...xs)) / 2;
    list.sort((a, b) => Math.abs(a.pos.x - xc) - Math.abs(b.pos.x - xc));
    return list[0];
  }

  buildChillers() {
    const R = this.root, frame = new THREE.MeshStandardMaterial({ color: 0x23272c, roughness: 0.4, metalness: 0.6 });
    const ct = chillerDoorTex(), inner = new THREE.MeshStandardMaterial({ map: ct, emissive: 0xffffff, emissiveMap: ct, emissiveIntensity: 0.55, roughness: 0.4 });
    const glass = new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.02, transparent: true, opacity: 0.12, clearcoat: 1, depthWrite: false });
    const w = 0.72, x = this.X1 - 0.02, n = Math.floor((this.yN - this.yS - 0.3) / (w + 0.04)), y0 = (this.yN + this.yS) / 2 - (n - 1) / 2 * (w + 0.04);
    for (let i = 0; i < n; i++) {
      const y = y0 + i * (w + 0.04);
      const p = new THREE.Mesh(new THREE.PlaneGeometry(w, 1.9), inner); p.rotation.set(Math.PI / 2, -Math.PI / 2, 0); p.position.set(x - 0.01, y, 1.05); R.add(p);
      const g = new THREE.Mesh(new THREE.PlaneGeometry(w, 1.9), glass); g.rotation.copy(p.rotation); g.position.set(x - 0.05, y, 1.05); R.add(g);
      for (const yy of [y - w / 2, y + w / 2]) R.add(boxMesh(0.06, 0.04, 2.0, frame, x - 0.04, yy, 1.05, false));
      R.add(boxMesh(0.03, 0.02, 0.5, this.mats.wire, x - 0.08, y + w / 2 - 0.06, 1.05, false));
    }
    const yc = y0 + (n - 1) / 2 * (w + 0.04);
    R.add(boxMesh(0.06, n * (w + 0.04) + 0.04, 0.06, frame, x - 0.04, yc, 2.05, false));
    R.add(boxMesh(0.06, n * (w + 0.04) + 0.04, 0.1, frame, x - 0.04, yc, 0.05, false));
    const sg = new THREE.Mesh(new THREE.PlaneGeometry(1.6, 0.22), new THREE.MeshStandardMaterial({ map: signTex(['CHILLED · 2–7 °C'], '#1f5fae'), roughness: 0.6 }));
    sg.rotation.set(Math.PI / 2, -Math.PI / 2, 0); sg.position.set(x - 0.02, yc, 2.3); R.add(sg);
  }

  buildStaging() {
    const R = this.root, M = this.mats, T = this.table;
    // dock marking in front of aisle 4
    const d = this.dock;
    const hatch = new THREE.Mesh(new THREE.PlaneGeometry(1.0, 0.75), new THREE.MeshStandardMaterial({ map: signTex(['ROBOT DOCK', 'charging · keep clear'], 'rgba(0,0,0,0)', '#f1c40f', 512, 384), transparent: true, roughness: 0.7 }));
    hatch.position.set(d.x, d.y, 0.0015); R.add(hatch);
    for (const [w, dd, x, y] of [[0.04, 0.75, -0.5, 0], [0.04, 0.75, 0.5, 0], [1.0, 0.04, 0, 0.375], [1.0, 0.04, 0, -0.375]]) R.add(boxMesh(w, dd, 0.002, M.yellow, d.x + x, d.y + y, 0.0012, false));
    // charger wall box is on the south wall near the dock
    // packing table: steel frame, beech-coloured top, order bags, label printer, scanner
    const tg = new THREE.Group(); tg.name = 'packing_table'; R.add(tg);
    const xc = (T.x0 + T.x1) / 2, dx = T.x1 - T.x0;
    tg.add(boxMesh(dx, T.len, 0.035, M.top, xc, T.yc, T.h - 0.0175));
    this.colliders.push({ name: 'packing table', box: new THREE.Box3(V3(T.x0, T.yc - T.len / 2, 0), V3(T.x1, T.yc + T.len / 2, T.h)) });
    for (const x of [T.x0 + 0.04, T.x1 - 0.04]) for (const y of [T.yc - T.len / 2 + 0.04, T.yc + T.len / 2 - 0.04]) tg.add(boxMesh(0.04, 0.04, T.h - 0.035, M.steel, x, y, (T.h - 0.035) / 2));
    tg.add(boxMesh(dx - 0.08, T.len - 0.08, 0.02, M.steel, xc, T.yc, 0.15));
    tg.add(boxMesh(0.02, T.len, 0.5, M.steel, T.x0 + 0.01, T.yc, T.h + 0.25));            // back panel / upstand
    const ord = new THREE.Mesh(new THREE.PlaneGeometry(0.62, 0.3), new THREE.MeshStandardMaterial({ map: signTex(['ORDER HANDOVER', 'robot unloads here · packers bag and dispatch'], '#1d2733', '#f1c40f', 1024, 500), roughness: 0.6 }));
    ord.rotation.set(Math.PI / 2, Math.PI / 2, 0); ord.position.set(T.x0 + 0.022, T.yc, T.h + 0.33); R.add(ord);
    // paper bags at the two ends, label printer and scanner
    for (const s of [-1, 1]) {
      const by = T.yc + s * (T.len / 2 - 0.16), bx = T.x0 + 0.16;
      const bg = new THREE.Group(); bg.position.set(bx, by, T.h);
      for (const [w, d2, x, y] of [[0.24, 0.002, 0, 0.075], [0.24, 0.002, 0, -0.075], [0.002, 0.15, 0.12, 0], [0.002, 0.15, -0.12, 0]]) bg.add(boxMesh(w, d2, 0.3, M.kraft, x, y, 0.15));
      bg.add(boxMesh(0.24, 0.15, 0.002, M.kraft, 0, 0, 0.001)); tg.add(bg);
    }
    tg.add(boxMesh(0.16, 0.12, 0.09, M.dark, T.x0 + 0.12, T.yc + 0.32, T.h + 0.045));
    tg.add(boxMesh(0.02, 0.07, 0.003, new THREE.MeshStandardMaterial({ color: 0xffffff }), T.x0 + 0.205, T.yc + 0.32, T.h + 0.06));
    const sc = boxMesh(0.05, 0.08, 0.16, new THREE.MeshStandardMaterial({ color: 0x2b2b2b, roughness: 0.5 }), T.x0 + 0.12, T.yc - 0.32, T.h + 0.08); sc.rotation.y = 0.3; tg.add(sc);
    // Euro pallet with water packs, north-west; roll container south-west
    const pal = new THREE.Group(); pal.position.set(-2.25, this.yN - 0.48, 0); R.add(pal);
    for (const y of [-0.37, 0, 0.37]) pal.add(boxMesh(1.2, 0.1, 0.022, M.wood, 0, y, 0.133));
    for (const x of [-0.55, 0, 0.55]) for (const y of [-0.35, 0, 0.35]) pal.add(boxMesh(0.1, 0.1, 0.078, M.wood, x, y, 0.083));
    for (const y of [-0.35, 0, 0.35]) pal.add(boxMesh(1.2, 0.1, 0.022, M.wood, 0, y, 0.033));
    const pack = productAsset('pack', 0), n = 32, im = new THREE.InstancedMesh(pack.geo, pack.mats, n), o = new THREE.Object3D(); let k = 0;
    for (let l = 0; l < 2; l++) for (let i = 0; i < 4; i++) for (let j = 0; j < 4; j++) { o.position.set(-0.45 + i * 0.29, -0.29 + j * 0.193, 0.144 + l * 0.322); o.updateMatrix(); im.setMatrixAt(k++, o.matrix); }
    im.castShadow = true; im.receiveShadow = true; pal.add(im);
    this.colliders.push({ name: 'pallet', box: new THREE.Box3(V3(-2.85, this.yN - 0.88, 0), V3(-1.65, this.yN - 0.08, 0.8)) });
    const rc = new THREE.Group(); rc.position.set(-2.75, this.yS + 0.45, 0); R.add(rc);
    rc.add(boxMesh(0.8, 0.67, 0.03, M.wire, 0, 0, 0.16));
    for (const x of [-0.39, 0.39]) for (let k2 = 0; k2 < 9; k2++) rc.add(boxMesh(0.008, 0.008, 1.55, M.wire, x, -0.32 + k2 * 0.08, 0.95));
    rc.add(boxMesh(0.008, 0.67, 0.008, M.wire, -0.39, 0, 1.72)); rc.add(boxMesh(0.008, 0.67, 0.008, M.wire, 0.39, 0, 1.72));
    for (const x of [-0.33, 0.33]) for (const y of [-0.28, 0.28]) { const w = new THREE.Mesh(new THREE.CylinderGeometry(0.06, 0.06, 0.03, 16), M.dark); w.position.set(x, y, 0.06); rc.add(w); }
    const tm = new THREE.MeshStandardMaterial({ color: 0x305f9a, roughness: 0.55 });
    for (let l = 0; l < 4; l++) rc.add(boxMesh(0.6, 0.4, 0.2, tm, 0, (l % 2 ? 1 : -1) * 0.03, 0.29 + l * 0.205));
    // charging station on the south wall at the dock
    const ch = boxMesh(0.3, 0.12, 0.45, new THREE.MeshStandardMaterial({ color: 0xf2f3f4, roughness: 0.4 }), d.x, this.yS + 0.06, 0.55); R.add(ch);
    R.add(boxMesh(0.2, 0.004, 0.03, new THREE.MeshStandardMaterial({ color: 0x0c3b38, emissive: 0x19d3c5, emissiveIntensity: 2 }), d.x, this.yS + 0.122, 0.7, false));
  }
}
