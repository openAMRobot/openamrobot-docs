// Fast OpenArm 2.0 kinematics (official URDF chain), allocation-free FK and damped-least-squares IK.
// Robot frame: base_link at the drive-axle midpoint, +X forward, +Y left, +Z up.
import * as THREE from 'three';

const TCP_LEN = 0.150;

function m4(xyz, rpy) { const m = new THREE.Matrix4(); m.makeRotationFromEuler(new THREE.Euler(rpy[0], rpy[1], rpy[2], 'ZYX')); m.setPosition(xyz[0], xyz[1], xyz[2]); return m; }
function split(m) { const e = m.elements; return { R: [e[0], e[4], e[8], e[1], e[5], e[9], e[2], e[6], e[10]], p: [e[12], e[13], e[14]] }; }

export function makeChain(D, side) {
  const a = D.arms[side];
  return {
    side, mount: split(m4([0, a.mount.xyz[1], 0], a.mount.rpy)),
    fixed: a.joints.map(j => split(m4(j.xyz, j.rpy))),
    axis: a.joints.map(j => { const n = Math.hypot(...j.axis); return j.axis.map(v => v / n); }),
    lo: a.joints.map(j => j.lo), hi: a.joints.map(j => j.hi),
  };
}

// T <- T * (R, p)
function mulInto(TR, Tp, R, p) {
  const r0 = TR[0], r1 = TR[1], r2 = TR[2], r3 = TR[3], r4 = TR[4], r5 = TR[5], r6 = TR[6], r7 = TR[7], r8 = TR[8];
  Tp[0] += r0 * p[0] + r1 * p[1] + r2 * p[2]; Tp[1] += r3 * p[0] + r4 * p[1] + r5 * p[2]; Tp[2] += r6 * p[0] + r7 * p[1] + r8 * p[2];
  TR[0] = r0 * R[0] + r1 * R[3] + r2 * R[6]; TR[1] = r0 * R[1] + r1 * R[4] + r2 * R[7]; TR[2] = r0 * R[2] + r1 * R[5] + r2 * R[8];
  TR[3] = r3 * R[0] + r4 * R[3] + r5 * R[6]; TR[4] = r3 * R[1] + r4 * R[4] + r5 * R[7]; TR[5] = r3 * R[2] + r4 * R[5] + r5 * R[8];
  TR[6] = r6 * R[0] + r7 * R[3] + r8 * R[6]; TR[7] = r6 * R[1] + r7 * R[4] + r8 * R[7]; TR[8] = r6 * R[2] + r7 * R[5] + r8 * R[8];
}
const ZERO = [0, 0, 0], RQ = new Float64Array(9);
function rot(axis, q, out) {
  const [x, y, z] = axis, c = Math.cos(q), s = Math.sin(q), t = 1 - c;
  out[0] = t * x * x + c; out[1] = t * x * y - s * z; out[2] = t * x * z + s * y;
  out[3] = t * x * y + s * z; out[4] = t * y * y + c; out[5] = t * y * z - s * x;
  out[6] = t * x * z - s * y; out[7] = t * y * z + s * x; out[8] = t * z * z + c;
}

// result object reused by callers
export function newFK() { return { TR: new Float64Array(9), Tp: new Float64Array(3), pts: Array.from({ length: 8 }, () => new Float64Array(3)), tcp: new Float64Array(3), appr: new Float64Array(3), yax: new Float64Array(3), wrist: new Float64Array(3), elbow: new Float64Array(3), shoulder: new Float64Array(3) }; }

export function fk(ch, q, sh, bpX, o) {
  const TR = o.TR, Tp = o.Tp;
  TR[0] = 1; TR[1] = 0; TR[2] = 0; TR[3] = 0; TR[4] = 1; TR[5] = 0; TR[6] = 0; TR[7] = 0; TR[8] = 1; Tp[0] = bpX; Tp[1] = 0; Tp[2] = sh;
  mulInto(TR, Tp, ch.mount.R, ch.mount.p);
  for (let i = 0; i < 7; i++) {
    mulInto(TR, Tp, ch.fixed[i].R, ch.fixed[i].p);
    rot(ch.axis[i], q[i], RQ); mulInto(TR, Tp, RQ, ZERO);
    if (i === 1) o.shoulder.set(Tp);
    if (i === 3) o.elbow.set(Tp);
    if (i === 5) o.wrist.set(Tp);
  }
  // tool axis is -Z of the end-effector frame; jaws close along its Y axis
  o.appr[0] = -TR[2]; o.appr[1] = -TR[5]; o.appr[2] = -TR[8];
  o.yax[0] = TR[1]; o.yax[1] = TR[4]; o.yax[2] = TR[7];
  for (let k = 0; k < 3; k++) o.tcp[k] = Tp[k] + o.appr[k] * TCP_LEN;
  // collision sample points: shoulder, mid upper arm, elbow, mid forearm, wrist, flange, gripper body, jaws
  const P = o.pts;
  for (let k = 0; k < 3; k++) {
    P[0][k] = o.shoulder[k]; P[1][k] = (o.shoulder[k] + o.elbow[k]) / 2; P[2][k] = o.elbow[k]; P[3][k] = (o.elbow[k] + o.wrist[k]) / 2;
    P[4][k] = o.wrist[k]; P[5][k] = Tp[k]; P[6][k] = Tp[k] + o.appr[k] * 0.07; P[7][k] = Tp[k] + o.appr[k] * 0.125;
  }
  return o;
}
export const PT_R = [0.05, 0.045, 0.045, 0.04, 0.04, 0.038, 0.035, 0.014];
export const PT_NAME = ['shoulder', 'upper arm', 'elbow', 'forearm', 'wrist', 'flange', 'gripper body', 'jaws'];

function solve(A, b, n) {           // in-place Gauss-Jordan, A n x n (array of arrays), returns x
  for (let c = 0; c < n; c++) {
    let p = c; for (let r = c + 1; r < n; r++) if (Math.abs(A[r][c]) > Math.abs(A[p][c])) p = r;
    [A[c], A[p]] = [A[p], A[c]]; [b[c], b[p]] = [b[p], b[c]];
    const d = A[c][c] || 1e-12;
    for (let k = c; k < n; k++) A[c][k] /= d; b[c] /= d;
    for (let r = 0; r < n; r++) if (r !== c) { const f = A[r][c]; if (f) { for (let k = c; k < n; k++) A[r][k] -= f * A[c][k]; b[r] -= f * b[c]; } }
  }
  return b;
}

const fkA = newFK(), fkB = newFK();
// goal: { p:[3] TCP, a:[3] approach (unit), c:[3]|null jaw closing axis (unit, sign free), sh, bpX, pref:[7]|null }
function residual(ch, q, g, o, r) {
  fk(ch, q, g.sh, g.bpX, o);
  const wa = 0.30, wc = 0.15, wq = 0.015;
  r[0] = o.tcp[0] - g.p[0]; r[1] = o.tcp[1] - g.p[1]; r[2] = o.tcp[2] - g.p[2];
  r[3] = wa * (o.appr[0] - g.a[0]); r[4] = wa * (o.appr[1] - g.a[1]); r[5] = wa * (o.appr[2] - g.a[2]);
  if (g.c) { const d = o.yax[0] * g.c[0] + o.yax[1] * g.c[1] + o.yax[2] * g.c[2], s = g.strict || d >= 0 ? 1 : -1; r[6] = wc * (o.yax[0] - s * g.c[0]); r[7] = wc * (o.yax[1] - s * g.c[1]); r[8] = wc * (o.yax[2] - s * g.c[2]); }
  else { r[6] = r[7] = r[8] = 0; }
  for (let i = 0; i < 7; i++) r[9 + i] = g.pref ? wq * (q[i] - g.pref[i]) : 0;
  return r;
}

let rs = 99991; const rr = () => (rs = (rs * 1103515245 + 12345) % 2147483648) / 2147483648;
export function ik(ch, goal, seeds, opts = {}) {
  const iters = opts.iters || 80, nRand = opts.nRand === undefined ? 10 : opts.nRand, M = 16;
  const all = seeds.slice(); rs = 99991;
  for (let s = 0; s < nRand; s++) all.push(ch.lo.map((lo, i) => lo + (0.15 + 0.7 * rr()) * (ch.hi[i] - lo)));
  let best = null; const r0 = new Float64Array(M), r1 = new Float64Array(M), J = Array.from({ length: 7 }, () => new Float64Array(M));
  for (const q0 of all) {
    const q = q0.map((v, i) => Math.min(ch.hi[i], Math.max(ch.lo[i], v))); let lam = 0.003;
    let e0 = Infinity;
    for (let it = 0; it < iters; it++) {
      residual(ch, q, goal, fkA, r0); let e = 0; for (let i = 0; i < M; i++) e += r0[i] * r0[i];
      if (e < 2e-6) break;
      lam = e < e0 ? Math.max(1e-4, lam * 0.6) : Math.min(1, lam * 3); e0 = e;
      for (let k = 0; k < 7; k++) { const old = q[k]; q[k] += 1e-5; residual(ch, q, goal, fkB, r1); q[k] = old; for (let i = 0; i < M; i++) J[k][i] = (r1[i] - r0[i]) / 1e-5; }
      const H = [], gv = [];
      for (let a = 0; a < 7; a++) { const row = []; let s = 0; for (let i = 0; i < M; i++) s += J[a][i] * r0[i]; gv.push(-s);
        for (let b = 0; b < 7; b++) { let h = 0; for (let i = 0; i < M; i++) h += J[a][i] * J[b][i]; row.push(h + (a === b ? lam : 0)); } H.push(row); }
      const dq = solve(H, gv, 7);
      for (let k = 0; k < 7; k++) q[k] = Math.min(ch.hi[k], Math.max(ch.lo[k], q[k] + Math.max(-0.3, Math.min(0.3, dq[k]))));
    }
    fk(ch, q, goal.sh, goal.bpX, fkA);
    const pe = Math.hypot(fkA.tcp[0] - goal.p[0], fkA.tcp[1] - goal.p[1], fkA.tcp[2] - goal.p[2]);
    const ad = Math.max(-1, Math.min(1, fkA.appr[0] * goal.a[0] + fkA.appr[1] * goal.a[1] + fkA.appr[2] * goal.a[2]));
    const ae = Math.acos(ad) * 180 / Math.PI;
    let ce = 0; if (goal.c) { const d0 = fkA.yax[0] * goal.c[0] + fkA.yax[1] * goal.c[1] + fkA.yax[2] * goal.c[2], d = goal.strict ? d0 : Math.abs(d0); ce = Math.acos(Math.min(1, d)) * 180 / Math.PI; }
    const score = pe + 0.003 * ae + 0.001 * ce;
    if (!best || score < best.score) best = { q: q.slice(), pe, ae, ce, score };
    if (pe < 0.003 && ae < 3 && ce < 5) break;
  }
  best.ok = best.pe < 0.006 && best.ae < 6 && best.ce < 8;
  return best;
}

// distance from point to axis-aligned box (0 inside)
export function boxDist(p, b) {
  const dx = Math.max(b.min.x - p[0], 0, p[0] - b.max.x), dy = Math.max(b.min.y - p[1], 0, p[1] - b.max.y), dz = Math.max(b.min.z - p[2], 0, p[2] - b.max.z);
  return Math.hypot(dx, dy, dz);
}
