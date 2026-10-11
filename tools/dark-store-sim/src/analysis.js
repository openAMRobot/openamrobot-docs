import * as THREE from 'three';
import { makeChain, fk, newFK, ik, boxDist, PT_R, PT_NAME } from './kin.js';
import { ROBOT, TOTE, ARMSPEC, STORE, DEG } from './spec.js';
import { TYPES } from './products.js';

const g0 = 9.81;
export const mirrorQ = q => [-q[0], -q[1], -q[2], q[3], -q[4], -q[5], -q[6]];
const STOW_L = [0.25, -0.12, 0, 1.9, 0, -0.78, 0];
export const STOWQ = { left: STOW_L, right: mirrorQ(STOW_L) };
const SEEDS_L = [[-0.3, -0.9, 0, 1.3, 0, 0.3, 0], [0, -0.5, 0, 0.8, 0, 0.5, 0], [-0.6, -1.4, 0, 1.6, 0, 0, 0], [0.2, -0.3, -0.8, 1.0, 0, 0.6, 0.6], STOW_L];
export const SEEDS = { left: SEEDS_L, right: SEEDS_L.map(mirrorQ) };
export const FINGER_T = 0.012;          // assumed jaw finger thickness per side (m)

export class Analyzer {
  constructor(D, store, selfBoxes) {
    this.ch = { left: makeChain(D, 'left'), right: makeChain(D, 'right') };
    this.store = store; this.selfBoxes = selfBoxes; this.o = newFK(); this.o2 = newFK();
    this.cfg = { gap: 0.05, gapAuto: true, ahead: 0.10, approach: 'horizontal', riser: 0.12, bpX: ROBOT.BP.bp100 };
  }

  // robot parks with its chassis side `gap` from the target run, shoulder `ahead` behind the item along the aisle
  parkPose(slot, gap = this.cfg.gap) {
    const A = this.store.aisle, s = slot.side === 'L' ? 1 : -1;
    gap = Math.min(gap, A - 2 * ROBOT.HW - 0.05);
    return { x: slot.pos.x - this.cfg.bpX - this.cfg.ahead, y: slot.cy + s * (A / 2 - gap - ROBOT.HW), yaw: 0, gap };
  }
  armFor(slot) { return slot.side === 'L' ? 'left' : 'right'; }

  // TCP goal for a shelf item in the robot frame
  shelfGoal(slot, pose, pitchDeg) {
    const T = TYPES[slot.type], s = slot.side === 'L' ? 1 : -1, p = pitchDeg * DEG;
    const P = [slot.pos.x - pose.x, slot.pos.y - pose.y, slot.pos.z + T.grasp.z];
    return { p: P, a: [0, s * Math.cos(p), -Math.sin(p)], c: [1, 0, 0] };
  }

  obstacles(pose, sh, bpX) {
    const out = this.selfBoxes(sh, bpX).map(o => ({ name: o.name, box: o.box, self: true }));
    for (const c of this.store.colliders) {
      const b = c.box.clone(); b.min.x -= pose.x; b.max.x -= pose.x; b.min.y -= pose.y; b.max.y -= pose.y;
      if (b.max.x < -1.2 || b.min.x > 1.2 || b.max.y < -1.2 || b.min.y > 1.2) continue;
      out.push({ name: c.name, box: b });
    }
    return out;
  }

  // arm collision screen; returns { clear (m), hits: [{part, obstacle, d}] }
  collide(side, q, sh, bpX, obs, skipJaws = false) {
    const o = fk(this.ch[side], q, sh, bpX, this.o), hits = []; let clear = Infinity;
    for (let i = 1; i < 8; i++) {
      if (skipJaws && i === 7) continue;
      for (const ob of obs) {
        if (ob.name === 'carriage / chest E-stop' && i < 2) continue;
        const d = boxDist(o.pts[i], ob.box) - PT_R[i];
        if (d < clear) clear = d;
        if (d < 0) hits.push({ part: PT_NAME[i], obstacle: ob.name, d });
      }
    }
    return { clear, hits };
  }

  solve(side, goal, sh, bpX, seeds) { return ik(this.ch[side], Object.assign({ sh, bpX, pref: null }, goal), seeds || SEEDS[side]); }

  // largest extension t along the approach beyond the goal that stays reachable (negative = short by)
  margin(side, goal, sh, bpX) {
    const at = t => ({ p: goal.p.map((v, i) => v + goal.a[i] * t), a: goal.a, c: goal.c });
    let r = this.solve(side, at(0), sh, bpX);
    if (r.ok) {
      let lo = 0, q = r.q, hi = null;
      for (let t = 0.03; t <= 0.45; t += 0.03) { const rr = this.solve(side, at(t), sh, bpX, [q, ...SEEDS[side].slice(0, 2)]); if (rr.ok) { lo = t; q = rr.q; } else { hi = t; break; } }
      if (hi !== null) for (let k = 0; k < 4; k++) { const m = (lo + hi) / 2, rr = this.solve(side, at(m), sh, bpX, [q]); if (rr.ok) { lo = m; q = rr.q; } else hi = m; }
      return { margin: lo, q: r.q, ok: true };
    }
    for (const t of [0.05, 0.10, 0.15]) { const rr = this.solve(side, at(t), sh, bpX); if (rr.ok) return { margin: null, q: r.q, ok: false, tooClose: t }; }
    let lo = null, q = null;
    for (let t = -0.06; t >= -0.36; t -= 0.06) { const rr = ik(this.ch[side], Object.assign({ sh, bpX, pref: null }, at(t)), [r.q, ...SEEDS[side].slice(0, 3)], { nRand: 1, iters: 45 }); if (rr.ok) { lo = t; q = rr.q; break; } }
    if (lo === null) return { margin: null, q: r.q, ok: false };
    let hi = lo + 0.06;
    for (let k = 0; k < 4; k++) { const m = (lo + hi) / 2, rr = this.solve(side, at(m), sh, bpX, [q]); if (rr.ok) { lo = m; q = rr.q; } else hi = m; }
    return { margin: lo, q: r.q, ok: false };
  }

  // full evaluation of one shelf slot at one shoulder height (or the best stop when sh is null)
  evalShelf(slot, sh) {
    const gaps = this.cfg.gapAuto ? [0.05, 0.10, 0.16, 0.22] : [this.cfg.gap];
    let best = null;
    for (const gap of gaps) {
      const r = this.evalAt(slot, sh, gap);
      const sc = (r.margin === null ? -9 : r.margin) - (r.col && r.col.hits.length ? 0.5 : 0) - (r.ok ? 0 : 1);
      if (!best || sc > best.sc + 0.01) best = Object.assign(r, { sc });
      if (r.ok && r.margin >= 0.03 && r.col && !r.col.hits.length) return r;
    }
    return best;
  }
  evalAt(slot, sh, gap) {
    const pose = this.parkPose(slot, gap), side = this.armFor(slot), bpX = this.cfg.bpX;
    const pitches = this.cfg.approach === 'horizontal' ? [0] : [0, 15, 30, 45];
    let best = null;
    for (const p of pitches) {
      const goal = this.shelfGoal(slot, pose, p), m = this.margin(side, goal, sh, bpX);
      const sc = m.margin === null ? -9 : m.margin;
      if (!best || sc > best.sc + 0.005) best = { sc, m, goal, pitch: p };
    }
    let col = null, q = best.m.q;
    if (best.m.ok) col = this.collide(side, q, sh, bpX, this.obstacles(pose, sh, bpX));
    return { slot, pose, side, sh, bpX, pitch: best.pitch, goal: best.goal, margin: best.m.margin, ok: best.m.ok, tooClose: best.m.tooClose, q, col };
  }

  stopsFor(slot) {
    const res = {}; for (const k in ROBOT.STOPS) res[k] = this.evalShelf(slot, ROBOT.STOPS[k]);
    let pick = null;
    for (const k of ['L1000', 'L1175', 'L1350']) { const r = res[k]; if (r.ok && r.margin >= 0.03 && r.col && !r.col.hits.length) { pick = k; break; } }
    if (!pick) { let bm = -Infinity; for (const k in res) { const r = res[k], s = (r.margin === null ? -9 : r.margin) - (r.col && r.col.hits.length ? 0.5 : 0); if (s > bm) { bm = s; pick = k; } } }
    return { res, pick };
  }

  // grasp and handling checks (independent of the arm pose)
  graspChecks(slot) {
    const T = TYPES[slot.type], jaw = T.grasp.w + 2 * ARMSPEC.JAW_CLEAR;
    const net = ARMSPEC.PAYLOAD_NOM - ARMSPEC.GRIPPER_MASS_ASSUMED, peak = ARMSPEC.PAYLOAD_PEAK - ARMSPEC.GRIPPER_MASS_ASSUMED;
    const sideNeed = (T.grasp.kind === 'seal' ? 0 : ARMSPEC.JAW_CLEAR + FINGER_T);
    const lvlGap = (STORE.LEVELS[slot.level + 1] || STORE.HEIGHT + 0.3) - STORE.SHELF_T - slot.pos.z;
    return {
      jaw: { need: jaw, max: ARMSPEC.JAW_MAX, ok: jaw <= ARMSPEC.JAW_MAX, kind: T.grasp.kind },
      payload: { mass: T.mass, net, peak, ok: T.mass <= net, peakOnly: T.mass > net && T.mass <= peak },
      neighbours: { gap: T.gap, need: sideNeed, ok: T.gap >= sideNeed },
      headroom: { gap: lvlGap - T.h, ok: lvlGap - T.h >= 0.03 },
    };
  }

  // static moments at the column foot from both arms and the item (no dynamic factor)
  moments(side, q, otherQ, item, sh, bpX) {
    const W = [1.4, 0.9, 0.9, 0.7, 0.6, 0.5, 0.5];      // kg at sample points 0..6 (sum 5.5 kg per arm, assumed split)
    let Mx = 0, My = 0, m = 0;
    for (const [sd, qq, it] of [[side, q, item], [side === 'left' ? 'right' : 'left', otherQ, 0]]) {
      const o = fk(this.ch[sd], qq, sh, bpX, this.o2);
      for (let i = 0; i < 7; i++) { Mx += W[i] * o.pts[i][1]; My += W[i] * (o.pts[i][0] - bpX); m += W[i]; }
      if (it) { Mx += it * o.tcp[1]; My += it * (o.tcp[0] - bpX); m += it; }
    }
    const carriage = 2.5;   // profile, plates, E-stop, ZED Mini, cable (assumed)
    return { lat: Math.abs(Mx) * g0, long: Math.abs(My) * g0, liftLoad: (m + carriage) * g0 };
  }

  // tote placement: item lying along the tote, jaws closing across the tote, straight-down approach
  toteGoal(side, item, layer = 0, lane = 0, nLanes = 1) {
    const T = TYPES[item], s = side === 'left' ? 1 : -1, cx = TOTE.X0 + TOTE.L / 2;
    const inner = TOTE.W - 2 * TOTE.WALL, w = T.fx + 0.01, used = nLanes * w;
    const yc = s * (TOTE.YIN + TOTE.W / 2) + (lane - (nLanes - 1) / 2) * w * (used <= inner ? 1 : inner / used);
    const thick = T.grasp.kind === 'neck' || T.grasp.kind === 'seal' ? T.d : T.d;
    const zf = ROBOT.COVER + this.cfg.riser + TOTE.WALL + layer * (thick + 0.004);
    return { p: [cx, yc, zf + thick / 2 + 0.006], a: [0, 0, -1], c: [0, 1, 0], rest: zf, thick };
  }
  // lowest reachable TCP height above the wanted place point at shoulder sh (drop = release height above resting)
  placeAt(side, goal, sh, bpX) {
    let r = this.solve(side, goal, sh, bpX), dz = 0, q = r.q;
    if (r.ok) return { ok: true, drop: 0, q, p: goal.p };
    for (dz = 0.01; dz <= 0.4; dz += 0.01) { const g = { p: [goal.p[0], goal.p[1], goal.p[2] + dz], a: goal.a, c: goal.c }; r = this.solve(side, g, sh, bpX, [q, STOWQ[side]]); if (r.ok) return { ok: true, drop: dz, q: r.q, p: g.p }; q = r.q; }
    return { ok: false, drop: null, q, p: goal.p };
  }
}
