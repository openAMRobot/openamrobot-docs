import * as THREE from 'three';
import { RoundedBoxGeometry } from 'three/examples/jsm/geometries/RoundedBoxGeometry.js';
import { ROBOT, TOTE, ARMSPEC, CAMS, DEG } from './spec.js';
import { logoTex, toteTex, signTex } from './textures.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const D = window.OPENARM;

const MAT = {
  shell: new THREE.MeshPhysicalMaterial({ color: 0xeceef0, roughness: 0.38, metalness: 0.0, clearcoat: 0.35, clearcoatRoughness: 0.5 }),
  cover: new THREE.MeshPhysicalMaterial({ color: 0xf6f7f8, roughness: 0.32, clearcoat: 0.4 }),
  skirt: new THREE.MeshStandardMaterial({ color: 0x2b3037, roughness: 0.55 }),
  black: new THREE.MeshStandardMaterial({ color: 0x15181c, roughness: 0.35, metalness: 0.2 }),
  glossBlack: new THREE.MeshPhysicalMaterial({ color: 0x0a0b0d, roughness: 0.08, clearcoat: 1 }),
  steel: new THREE.MeshStandardMaterial({ color: 0x4a4f55, roughness: 0.45, metalness: 0.7 }),
  alu: new THREE.MeshStandardMaterial({ color: 0xc9cdd2, roughness: 0.32, metalness: 0.75 }),
  aluDark: new THREE.MeshStandardMaterial({ color: 0x9aa0a7, roughness: 0.38, metalness: 0.75 }),
  anod: new THREE.MeshStandardMaterial({ color: 0xd7dade, roughness: 0.28, metalness: 0.65 }),
  slot: new THREE.MeshStandardMaterial({ color: 0x2c3036, roughness: 0.6, metalness: 0.3 }),
  red: new THREE.MeshStandardMaterial({ color: 0xd8231f, roughness: 0.35 }),
  yellow: new THREE.MeshStandardMaterial({ color: 0xf2c200, roughness: 0.45 }),
  tyre: new THREE.MeshStandardMaterial({ color: 0x1b1d20, roughness: 0.85 }),
  led: new THREE.MeshStandardMaterial({ color: 0x0c3b38, emissive: 0x19d3c5, emissiveIntensity: 2.0 }),
  lens: new THREE.MeshPhysicalMaterial({ color: 0x050608, roughness: 0.02, clearcoat: 1, metalness: 0.3 }),
  cable: new THREE.MeshStandardMaterial({ color: 0x1a1c1f, roughness: 0.6 }),
  orange: new THREE.MeshStandardMaterial({ color: 0xf07a12, roughness: 0.5 }),
};
export const ROBOT_MAT = MAT;

function box(parent, w, d, h, m, x, y, z, name) { const b = new THREE.Mesh(new THREE.BoxGeometry(w, d, h), m); b.position.set(x, y, z); b.castShadow = true; b.receiveShadow = true; if (name) b.name = name; parent.add(b); return b; }
function rbox(parent, w, d, h, r, m, x, y, z) { const b = new THREE.Mesh(new RoundedBoxGeometry(w, d, h, 3, r), m); b.position.set(x, y, z); b.castShadow = true; b.receiveShadow = true; parent.add(b); return b; }
function cylAxis(parent, r, len, m, x, y, z, axis = 'z', seg = 24) {
  const c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), m); c.castShadow = true;
  if (axis === 'x') c.rotation.z = Math.PI / 2; else if (axis === 'z') c.rotation.x = Math.PI / 2;
  c.position.set(x, y, z); parent.add(c); return c;
}
function M4(xyz, rpy) { const m = new THREE.Matrix4(); m.makeRotationFromEuler(new THREE.Euler(rpy[0], rpy[1], rpy[2], 'ZYX')); m.setPosition(xyz[0], xyz[1], xyz[2]); return m; }

// ------------------------------------------------------------------------------- OpenArm meshes
function decode(b64, Type) { const s = atob(b64), n = s.length, u = new Uint8Array(n); for (let i = 0; i < n; i++) u[i] = s.charCodeAt(i); return new Type(u.buffer); }
const GEO = {};
for (const k in D.meshes) {
  const m = D.meshes[k], p16 = decode(m.pos, Int16Array), pos = new Float32Array(p16.length);
  for (let i = 0; i < p16.length; i++) pos[i] = p16[i] * m.q;
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.BufferAttribute(decode(m.col, Uint8Array), 3, true));
  g.computeVertexNormals(); g.computeBoundingSphere(); GEO[k] = g;
}
export const ARM_MAT = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.42, metalness: 0.15, clearcoat: 0.3, side: THREE.DoubleSide });
export const ARM_HL = new THREE.MeshPhysicalMaterial({ vertexColors: true, roughness: 0.42, metalness: 0.15, side: THREE.DoubleSide, emissive: 0x2a5bd7, emissiveIntensity: 0.35 });

export const mirrorQ = q => [-q[0], -q[1], -q[2], q[3], -q[4], -q[5], -q[6]];
export const STOW = { left: [0.25, -0.12, 0, 1.9, 0, -0.78, 0], right: mirrorQ([0.25, -0.12, 0, 1.9, 0, -0.78, 0]) };

export class Robot {
  constructor(scene) {
    this.g = new THREE.Group(); this.g.name = 'OpenAMRobot'; scene.add(this.g);
    this.sh = ROBOT.STOPS.L1000; this.bpKey = 'bp000'; this.bpX = ROBOT.BP.bp000; this.hp = 30; this.bt = 10; this.riser = 0;
    this.pose = { x: 0, y: 0, yaw: 0 };
    this.buildChassis(); this.buildColumn(); this.buildTotes(); this.buildArms();
    this.setBP('bp000'); this.setLift(this.sh);
    this.applyArm('left', STOW.left); this.applyArm('right', STOW.right);
    this.setGrip('left', 0.6); this.setGrip('right', 0.6);
  }

  // ----------------------------------------------------------------------------- chassis
  buildChassis() {
    const g = this.g, R = ROBOT, L = R.X1 - R.X0, W = 2 * R.HW;
    rbox(g, L - 0.004, W - 0.004, 0.236, 0.028, MAT.shell, 0, 0, 0.052 + 0.118);
    rbox(g, L + 0.004, W + 0.004, 0.062, 0.022, MAT.skirt, 0, 0, 0.052 + 0.031);
    // top cover 2 mm with cut-out around the lift base plate
    const sh = new THREE.Shape(), rr = 0.03, x0 = R.X0 + 0.002, x1 = R.X1 - 0.002, y0 = -R.HW + 0.002, y1 = R.HW - 0.002;
    sh.moveTo(x0 + rr, y0); sh.lineTo(x1 - rr, y0); sh.quadraticCurveTo(x1, y0, x1, y0 + rr); sh.lineTo(x1, y1 - rr); sh.quadraticCurveTo(x1, y1, x1 - rr, y1);
    sh.lineTo(x0 + rr, y1); sh.quadraticCurveTo(x0, y1, x0, y1 - rr); sh.lineTo(x0, y0 + rr); sh.quadraticCurveTo(x0, y0, x0 + rr, y0);
    const hole = new THREE.Path(); const hx0 = -0.165, hx1 = 0.365, hy = 0.056;
    hole.moveTo(hx0, -hy); hole.lineTo(hx0, hy); hole.lineTo(hx1, hy); hole.lineTo(hx1, -hy); hole.lineTo(hx0, -hy); sh.holes.push(hole);
    const cov = new THREE.Mesh(new THREE.ExtrudeGeometry(sh, { depth: 0.002, bevelEnabled: false, curveSegments: 6 }), MAT.cover);
    cov.position.z = R.DECK; cov.castShadow = true; cov.receiveShadow = true; g.add(cov);
    box(g, hx1 - hx0, 2 * hy, 0.002, MAT.steel, (hx0 + hx1) / 2, 0, R.DECK - 0.001);                     // steel deck in the cut-out
    const hg = new THREE.CircleGeometry(0.0045, 12);
    for (const k in R.BP) for (const dx of [-0.13, 0.13]) for (const y of [-0.035, 0.035]) {           // M8 deck holes for the two plate positions
      const h = new THREE.Mesh(hg, MAT.black); h.position.set(R.BP[k] + dx, y, R.DECK + 0.0005); g.add(h);
    }
    // drive wheels (hub motors) and castors
    for (const y of [-R.WHEEL_Y, R.WHEEL_Y]) {
      const w = cylAxis(g, R.WHEEL_R, 0.05, MAT.tyre, 0, y, R.WHEEL_R, 'y', 36);
      cylAxis(g, 0.06, 0.052, MAT.aluDark, 0, y, R.WHEEL_R, 'y', 24);
    }
    for (const [x, y] of R.CASTER) {
      box(g, 0.06, 0.06, 0.006, MAT.steel, x, y, R.BELLY - 0.003);
      box(g, 0.008, 0.03, 0.022, MAT.steel, x - 0.012, y, 0.035);
      cylAxis(g, 0.0175, 0.025, MAT.tyre, x - 0.015, y, 0.0175, 'y', 16);
    }
    // LiDAR scan window (RPLIDAR S3 behind, scan plane 222 mm above the floor), open slot round the front corners
    const z = R.LIDAR_Z;
    box(g, 0.006, 0.50, 0.032, MAT.glossBlack, R.X1 + 0.0005, 0, z);
    for (const s of [-1, 1]) box(g, 0.13, 0.006, 0.032, MAT.glossBlack, R.X1 - 0.08, s * (R.HW + 0.0005), z);
    cylAxis(g, 0.046, 0.04, MAT.black, R.LIDAR_X, 0, z, 'z', 32);
    // Gemini 336L (front centre, housing centre at base_camera_link, 142.5 mm above the floor) on a tilt pivot;
    // the group origin is the housing front face, 13 mm (half the 26 mm depth) ahead of base_camera_link
    this.gemini = new THREE.Group(); this.gemini.position.set(R.GEMINI.x + 0.013, 0, R.BASE_LINK_Z + R.GEMINI.z); g.add(this.gemini);
    box(this.gemini, 0.026, 0.124, 0.029, MAT.black, -0.013, 0, 0);
    for (const y of [-0.047, -0.016, 0.016, 0.047]) cylAxis(this.gemini, y === -0.016 ? 0.006 : 0.0045, 0.003, MAT.lens, 0.0005, y, 0, 'x', 16);
    // Four MB7060 in the front and rear edge holes (us_front_left, us_front_right, us_rear_left, us_rear_right)
    // and two TF-Luna cliff sensors in the front and rear centre holes (tof_front, tof_rear), P-03 rev19.0
    for (const [x, s] of [[R.X1, 1], [R.X0, -1]]) {
      for (const y of [R.US_Y, -R.US_Y]) { cylAxis(g, 0.0115, 0.008, MAT.aluDark, x + s * 0.003, y, R.NEAR_Z, 'x', 20); cylAxis(g, 0.009, 0.004, MAT.black, x + s * 0.007, y, R.NEAR_Z, 'x', 20); }
      box(g, 0.006, 0.035, 0.021, MAT.black, x + s * 0.002, 0, R.NEAR_Z);
      for (const dy of [-0.008, 0.008]) cylAxis(g, 0.004, 0.003, MAT.lens, x + s * 0.005, dy, R.NEAR_Z, 'x', 12);
    }
    // base E-stop (rear, top cover) with yellow housing
    box(g, 0.065, 0.065, 0.04, MAT.yellow, R.X0 + 0.06, -0.21, R.COVER + 0.02);
    cylAxis(g, 0.02, 0.022, MAT.red, R.X0 + 0.06, -0.21, R.COVER + 0.051, 'z', 24);
    cylAxis(g, 0.012, 0.02, MAT.black, R.X0 + 0.06, -0.21, R.COVER + 0.04, 'z', 16);
    // charge inlet (rear), status light strips, branding
    box(g, 0.004, 0.06, 0.04, MAT.black, R.X0 - 0.001, 0.12, 0.2); box(g, 0.006, 0.04, 0.025, MAT.orange, R.X0 - 0.003, 0.12, 0.2);
    for (const s of [-1, 1]) box(g, 0.62, 0.003, 0.008, MAT.led, -0.02, s * (R.HW + 0.001), 0.272);
    box(g, 0.003, 0.4, 0.008, MAT.led, R.X0 - 0.001, 0, 0.272);
    const logo = new THREE.MeshStandardMaterial({ map: logoTex(), transparent: true, roughness: 0.5 });
    for (const s of [-1, 1]) {
      const p = new THREE.Mesh(new THREE.PlaneGeometry(0.40, 0.05), logo);
      p.rotation.set(Math.PI / 2, s > 0 ? Math.PI : 0, 0); p.position.set(-0.08, s * (R.HW + 0.0015), 0.17); g.add(p);
    }
    const lr = new THREE.Mesh(new THREE.PlaneGeometry(0.34, 0.043), logo); lr.rotation.set(Math.PI / 2, -Math.PI / 2, 0); lr.position.set(R.X0 - 0.0015, -0.05, 0.155); g.add(lr);
  }

  // ----------------------------------------------------------------------------- DOLD Hexalift V4 + carriage
  buildColumn() {
    const C = ROBOT.COL, P = ROBOT.PLATE_TOP;
    this.colAsm = new THREE.Group(); this.colAsm.name = 'lift_assembly'; this.g.add(this.colAsm);
    const a = this.colAsm;
    box(a, 0.30, 0.10, ROBOT.PLATE_T, MAT.alu, 0, 0, P - ROBOT.PLATE_T / 2, 'base_plate');
    for (const dx of [-0.13, 0.13]) for (const y of [-0.035, 0.035]) cylAxis(a, 0.0065, 0.005, MAT.steel, dx, y, P + 0.0025, 'z', 6);
    // outer stage: 240 x 60 profile, six T-slots
    const outerH = C.RETRACTED - C.HEAD - 0.012;
    rbox(a, C.L, C.W, outerH, 0.007, MAT.anod, 0, 0, P + outerH / 2);
    const slots = (parent, L, W, H, z) => {
      for (const s of [-1, 1]) { for (const x of [-L / 4, L / 4]) box(parent, 0.008, 0.002, H - 0.01, MAT.slot, x, s * (W / 2 + 0.0002), z); box(parent, 0.002, 0.008, H - 0.01, MAT.slot, s * (L / 2 + 0.0002), 0, z); }
    };
    slots(a, C.L, C.W, outerH, P + outerH / 2);
    box(a, C.L + 0.004, C.W + 0.004, 0.012, MAT.aluDark, 0, 0, P + outerH - 0.006);           // stage collar
    const lab = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.035), new THREE.MeshStandardMaterial({ map: signTex(['HEXALIFT V4', '800 N · 18 mm/s · 24 V'], '#e9ecef', '#1d2733', 512, 160), roughness: 0.5 }));
    lab.rotation.set(Math.PI / 2, 0, 0); lab.position.set(0, -C.W / 2 - 0.0012, P + 0.12); a.add(lab);
    // second E-stop on the rear face of the static column, close to its upper edge (P-03 rev20.0 item 24, 28 Oct 2026);
    // Schneider XB4BS8445 with ZBE-102 as on the base. Position is a placeholder until M-09.
    const sz = P + outerH - 0.05;
    box(a, 0.036, 0.07, 0.07, MAT.yellow, -C.L / 2 - 0.018, 0, sz);
    cylAxis(a, 0.019, 0.02, MAT.red, -C.L / 2 - 0.046, 0, sz, 'x', 24);
    // status light ring at the column foot
    box(a, C.L + 0.03, C.W + 0.03, 0.006, MAT.led, 0, 0, P + 0.003);
    // moving parts
    this.mov = new THREE.Group(); a.add(this.mov);
    const m = this.mov, innerH = 0.44, top = P + C.RETRACTED;                 // positions below at retracted state; mov.z = extension
    rbox(m, C.L - 0.016, C.W - 0.012, innerH, 0.005, MAT.alu, 0, 0, top - C.HEAD - innerH / 2);
    slots(m, C.L - 0.016, C.W - 0.012, innerH, top - C.HEAD - innerH / 2);
    box(m, 0.25, 0.072, C.HEAD, MAT.aluDark, 0, 0, top - C.HEAD / 2, 'head_plate');
    for (const s of [-1, 1]) box(m, 0.03, 0.012, 0.05, MAT.aluDark, s * 0.11, 0, top + 0.025);   // mounting straps
    // carriage (option B): 10 mm adapter plate on the column head, MISUMI HFS6-60120 arm profile 340 mm long,
    // J1_A plates at the shoulder 180 mm ahead of the column axis, ZED Mini. The second E-stop is on the static column (above).
    // The chest equipment envelope (Getac ZX80, head light) stays in the self-collision box below; its position comes from M-09.
    // The adapter-plate outline is approximate until it is drawn.
    const PR = ROBOT.PROFILE, px = ROBOT.MOUNT_X, pz0 = top + PR.ADAPTER, ax0 = -C.L / 2, ax1 = px + PR.X / 2;
    box(m, ax1 - ax0, 0.072, PR.ADAPTER, MAT.aluDark, (ax0 + ax1) / 2, 0, top + PR.ADAPTER / 2, 'adapter_plate');
    rbox(m, PR.X, PR.Y, PR.L, 0.004, MAT.alu, px, 0, pz0 + PR.L / 2);
    for (const s of [-1, 1]) {
      for (const dx of [-PR.X / 4, PR.X / 4]) box(m, 0.008, 0.002, PR.L - 0.01, MAT.slot, px + dx, s * (PR.Y / 2 + 0.0002), pz0 + PR.L / 2);
      box(m, 0.002, 0.008, PR.L - 0.01, MAT.slot, px + s * (PR.X / 2 + 0.0002), 0, pz0 + PR.L / 2);
    }
    for (const s of [-1, 1]) box(m, 0.09, 0.001, 0.09, MAT.steel, px, s * 0.0305, top + ROBOT.MOUNT_ABOVE_COL);   // 1 mm spacers
    const lensZ = top + ROBOT.MOUNT_ABOVE_COL + ROBOT.ZED_ABOVE_SH, ptop = pz0 + PR.L;
    box(m, 0.03, 0.03, 0.006, MAT.alu, ROBOT.ZED_X - 0.03, 0, ptop + 0.003);
    box(m, 0.012, 0.03, lensZ - ptop, MAT.aluDark, ROBOT.ZED_X - 0.03, 0, (ptop + lensZ) / 2);
    this.zed = new THREE.Group(); this.zed.position.set(ROBOT.ZED_X, 0, lensZ); m.add(this.zed);
    box(this.zed, 0.0265, 0.1245, 0.0305, MAT.black, -0.013, 0, 0);
    for (const y of [-0.0315, 0.0315]) cylAxis(this.zed, 0.0085, 0.003, MAT.lens, 0.0005, y, 0, 'x', 20);
    this.zedTop = top + ROBOT.MOUNT_ABOVE_COL + ROBOT.ZED_ABOVE_SH;
    // drag cable (rebuilt on lift change)
    this.cable = new THREE.Mesh(new THREE.BufferGeometry(), MAT.cable); this.cable.castShadow = true; a.add(this.cable);
  }

  // ----------------------------------------------------------------------------- totes
  buildTotes() {
    this.totes = {};
    for (const [side, s] of [['left', 1], ['right', -1]]) {
      const t = new THREE.Group(); t.name = 'tote_' + side;
      const col = side === 'left' ? '#2f5f9e' : '#2c7a6e', mt = new THREE.MeshStandardMaterial({ color: 0xffffff, map: toteTex(col), roughness: 0.6 });
      const T = TOTE, w = T.WALL;
      box(t, T.L, T.W, w, mt, 0, 0, w / 2);
      box(t, T.L, w, T.H, mt, 0, T.W / 2 - w / 2, T.H / 2); box(t, T.L, w, T.H, mt, 0, -T.W / 2 + w / 2, T.H / 2);
      box(t, w, T.W, T.H, mt, T.L / 2 - w / 2, 0, T.H / 2); box(t, w, T.W, T.H, mt, -T.L / 2 + w / 2, 0, T.H / 2);
      for (const sx of [-1, 1]) { box(t, 0.004, 0.09, 0.03, MAT.black, sx * (T.L / 2 + 0.0005), 0, T.H - 0.035); }
      box(t, T.L + 0.012, 0.012, 0.008, mt, 0, T.W / 2 + 0.002, T.H - 0.004); box(t, T.L + 0.012, 0.012, 0.008, mt, 0, -T.W / 2 - 0.002, T.H - 0.004);
      box(t, 0.012, T.W, 0.008, mt, T.L / 2 + 0.002, 0, T.H - 0.004); box(t, 0.012, T.W, 0.008, mt, -T.L / 2 - 0.002, 0, T.H - 0.004);
      const card = new THREE.Mesh(new THREE.PlaneGeometry(0.11, 0.05), new THREE.MeshStandardMaterial({ map: signTex([side === 'left' ? 'ORDER A' : 'ORDER B', '#40' + (side === 'left' ? '217' : '218')], '#ffffff', '#111', 256, 120), roughness: 0.6 }));
      card.rotation.set(Math.PI / 2, Math.PI / 2, 0); card.position.set(T.L / 2 + 0.003, 0, T.H - 0.07); t.add(card);
      t.position.set(T.X0 + T.L / 2, s * (T.YIN + T.W / 2), ROBOT.COVER);
      this.g.add(t); this.totes[side] = t; t.userData.items = [];
      // retention rails (aluminium angle) on the outer and front edges
      box(this.g, T.L, 0.012, 0.012, MAT.aluDark, T.X0 + T.L / 2, s * (T.YIN + T.W + 0.008), ROBOT.COVER + 0.006);
      box(this.g, 0.012, T.W, 0.012, MAT.aluDark, T.X0 + T.L + 0.008, s * (T.YIN + T.W / 2), ROBOT.COVER + 0.006);
    }
  }
  setRiser(h) { this.riser = h; for (const k in this.totes) this.totes[k].position.z = ROBOT.COVER + h; }
  toteFloorZ() { return ROBOT.COVER + this.riser + TOTE.WALL; }

  // ----------------------------------------------------------------------------- arms
  buildArms() {
    this.arm = {};
    const visual = (v) => {
      const gg = new THREE.Group(); gg.matrixAutoUpdate = false;
      if (v && GEO[v.key]) { const mm = new THREE.Mesh(GEO[v.key], ARM_MAT); mm.castShadow = true; mm.receiveShadow = true; mm.matrix.copy(M4(v.xyz, v.rpy)).multiply(new THREE.Matrix4().makeScale(v.scale[0], v.scale[1], v.scale[2])); mm.matrixAutoUpdate = false; gg.add(mm); }
      this.g.add(gg); return gg;
    };
    for (const side of ['left', 'right']) {
      const a = D.arms[side];
      this.arm[side] = { mount: M4([ROBOT.MOUNT_X, a.mount.xyz[1], 0], a.mount.rpy),
        J: a.joints.map(j => ({ T: M4(j.xyz, j.rpy), axis: V3(...j.axis).normalize(), lo: j.lo, hi: j.hi })),
        gBase: visual(a.base_visual), gLinks: a.joints.map(j => visual(j.visual)),
        fingers: a.fingers.map(f => ({ T: M4(f.xyz, f.rpy), axis: V3(...f.axis).normalize(), lo: f.lo, hi: f.hi, g: visual(f.visual) })),
        q: STOW[side].slice(), grip: 0.6, ee: new THREE.Matrix4(), tcp: new THREE.Matrix4() };
    }
    this.wrist = {};
    for (const [k, side] of [['wristL', 'left'], ['wristR', 'right']]) {
      const c = CAMS[k], T = new THREE.Matrix4().makeRotationFromEuler(new THREE.Euler(c.eul[0], c.eul[1], c.eul[2], 'XYZ')); T.setPosition(c.pos[0], c.pos[1], c.pos[2]);
      const hsg = new THREE.Group(); hsg.matrixAutoUpdate = false; const hb = new THREE.Mesh(new THREE.BoxGeometry(0.018, 0.018, 0.012), MAT.black); hb.position.z = 0.006; hsg.add(hb); this.g.add(hsg);
      this.wrist[k] = { side, T, g: hsg };
    }
  }

  // forward kinematics in the robot frame
  fk(side, q, sh = this.sh, bpX = this.bpX, want = false) {
    const A = this.arm[side], R = new THREE.Matrix4();
    const T = new THREE.Matrix4().makeTranslation(bpX, 0, sh).multiply(A.mount);
    const out = { base: T.clone(), frames: [] };
    for (let i = 0; i < 7; i++) {
      T.multiply(A.J[i].T); R.makeRotationAxis(A.J[i].axis, q[i]); T.multiply(R);
      if (want) out.frames.push(T.clone());
      if (i === 1) out.shoulder = V3(0, 0, 0).setFromMatrixPosition(T);
      if (i === 3) out.elbow = V3(0, 0, 0).setFromMatrixPosition(T);
      if (i === 5) out.wrist = V3(0, 0, 0).setFromMatrixPosition(T);
    }
    out.ee = T;
    out.tcp = V3(0, 0, -ARMSPEC.TCP).applyMatrix4(T);
    const e = T.elements; out.zAxis = V3(e[8], e[9], e[10]); out.yAxis = V3(e[4], e[5], e[6]); out.xAxis = V3(e[0], e[1], e[2]);
    out.approach = out.zAxis.clone().negate();
    return out;
  }

  applyArm(side, q) {
    const A = this.arm[side], f = this.fk(side, q, this.sh, this.bpX, true);
    A.gBase.matrix.copy(f.base); A.gBase.matrixWorldNeedsUpdate = true;
    for (let i = 0; i < 7; i++) { A.gLinks[i].matrix.copy(f.frames[i]); A.gLinks[i].matrixWorldNeedsUpdate = true; }
    A.ee.copy(f.ee); A.tcp.copy(f.ee).multiply(new THREE.Matrix4().makeTranslation(0, 0, -ARMSPEC.TCP)); A.q = q.slice(); A.f = f;
    this.updateFingers(side);
    const wk = side === 'left' ? 'wristL' : 'wristR'; this.wrist[wk].g.matrix.copy(f.ee).multiply(this.wrist[wk].T); this.wrist[wk].g.matrixWorldNeedsUpdate = true;
    return f;
  }
  // opening 0 = closed, 1 = 88 mm
  setGrip(side, open) { this.arm[side].grip = Math.max(0, Math.min(1, open)); this.updateFingers(side); }
  updateFingers(side) {
    const A = this.arm[side];
    A.fingers.forEach(fg => {
      const lim = Math.abs(fg.lo) > Math.abs(fg.hi) ? fg.lo : fg.hi, ang = lim * A.grip;
      fg.g.matrix.copy(A.ee).multiply(fg.T).multiply(new THREE.Matrix4().makeRotationAxis(fg.axis, ang)); fg.g.matrixWorldNeedsUpdate = true;
    });
  }

  setBP(key) { this.bpKey = key; this.bpX = ROBOT.BP[key]; this.colAsm.position.x = this.bpX; this.refreshArms(); }
  setLift(sh) {
    this.sh = Math.max(ROBOT.STOPS.L1000, Math.min(ROBOT.STOPS.L1350, sh));
    this.mov.position.z = this.sh - ROBOT.STOPS.L1000;
    this.updateCable(); this.refreshArms();
  }
  colTop() { return ROBOT.PLATE_TOP + ROBOT.COL.RETRACTED + (this.sh - ROBOT.STOPS.L1000); }
  setHeadPitch(d) { this.hp = d; this.zed.rotation.y = d * DEG; }
  setBaseTilt(d) { this.bt = d; this.gemini.rotation.y = -d * DEG; }
  refreshArms() { if (this.arm) for (const s of ['left', 'right']) this.applyArm(s, this.arm[s].q); }
  updateCable() {
    const ct = this.colTop(), P = ROBOT.PLATE_TOP;
    const pts = [V3(ROBOT.MOUNT_X - ROBOT.PROFILE.X / 2 - 0.012, 0.012, ct + 0.06), V3(0.03, 0.012, ct + 0.03), V3(-0.06, 0.012, ct + 0.02), V3(-0.125, 0.014, ct - 0.06), V3(-0.15, 0.016, (ct + P) / 2 + 0.05), V3(-0.15, 0.016, P + 0.1), V3(-0.14, 0.016, P + 0.012)];
    this.cable.geometry.dispose(); this.cable.geometry = new THREE.TubeGeometry(new THREE.CatmullRomCurve3(pts), 48, 0.0055, 8, false);
  }
  setPose(x, y, yaw = 0) { this.pose = { x, y, yaw }; this.g.position.set(x, y, 0); this.g.rotation.set(0, 0, yaw); this.g.updateMatrixWorld(true); }
  matrixFor(pose) { const m = new THREE.Matrix4().makeRotationZ(pose.yaw || 0); m.setPosition(pose.x, pose.y, 0); return m; }
  configId() { return `column=dold_v4_350 · base_plate=${this.bpKey} · head_pitch=hp${this.hp} · base_tilt=bt${String(this.bt).padStart(2, '0')}`; }

  // robot-frame obstacle boxes (for the arm collision screen)
  selfBoxes(sh = this.sh, bpX = this.bpX) {
    const C = ROBOT.COL, B = (x0, y0, z0, x1, y1, z1, name) => ({ name, box: new THREE.Box3(V3(x0, y0, z0), V3(x1, y1, z1)) });
    const ct = ROBOT.PLATE_TOP + C.RETRACTED + (sh - ROBOT.STOPS.L1000);
    const out = [B(ROBOT.X0, -ROBOT.HW, 0, ROBOT.X1, ROBOT.HW, ROBOT.COVER, 'chassis'),
      B(bpX - C.L / 2, -C.W / 2, ROBOT.PLATE_TOP, bpX + C.L / 2, C.W / 2, ct, 'lift column'),
      B(bpX + ROBOT.MOUNT_X - ROBOT.PROFILE.X / 2, -ROBOT.PROFILE.Y / 2, ct, bpX + ROBOT.MOUNT_X + ROBOT.PROFILE.X / 2 + 0.065, ROBOT.PROFILE.Y / 2, sh - 0.06, 'arm profile / chest equipment')];
    const T = TOTE, zf = ROBOT.COVER + this.riser;
    for (const s of [1, -1]) {
      const yi = s * T.YIN, yo = s * (T.YIN + T.W), lo = Math.min(yi, yo), hi = Math.max(yi, yo), x0 = T.X0, x1 = T.X0 + T.L, zt = zf + T.H;
      const nm = 'tote ' + (s > 0 ? 'left' : 'right');
      out.push(B(x0, lo, zf, x1, lo + 0.006, zt, nm), B(x0, hi - 0.006, zf, x1, hi, zt, nm), B(x0, lo, zf, x0 + 0.006, hi, zt, nm), B(x1 - 0.006, lo, zf, x1, hi, zt, nm));
    }
    return out;
  }
}
