import * as THREE from 'three';
import { ROBOT, TOTE, ARMSPEC } from './spec.js';
import { TYPES, productAsset } from './products.js';
import { STOWQ, SEEDS } from './analysis.js';

const V3 = (x, y, z) => new THREE.Vector3(x, y, z);
const smooth = t => t * t * (3 - 2 * t);
const lerp = (a, b, t) => a + (b - a) * t;

// Channel timeline: each channel is a list of keys {t, v, ease}; values are numbers or arrays.
export class Timeline {
  constructor() { this.ch = {}; this.T = 0; this.events = []; this.items = []; this.notes = []; }
  key(name, t, v, ease = true) { (this.ch[name] = this.ch[name] || []).push({ t, v: Array.isArray(v) ? v.slice() : v, ease }); this.T = Math.max(this.T, t); }
  last(name) { const k = this.ch[name]; return k && k.length ? k[k.length - 1].v : undefined; }
  value(name, t) {
    const k = this.ch[name]; if (!k || !k.length) return undefined;
    if (t <= k[0].t) return k[0].v;
    for (let i = 1; i < k.length; i++) if (t <= k[i].t) {
      const a = k[i - 1], b = k[i], u = b.t > a.t ? (t - a.t) / (b.t - a.t) : 1, e = b.ease ? smooth(u) : u;
      return Array.isArray(a.v) ? a.v.map((x, j) => lerp(x, b.v[j], e)) : lerp(a.v, b.v, e);
    }
    return k[k.length - 1].v;
  }
  note(t, text) { this.notes.push({ t, text }); }
}

// Builds pick-to-tote cycles on a timeline. state: {t, pose:{x,y,yaw}, sh, q:{left,right}, grip:{left,right}, tote:{left:[],right:[]}}
export class Planner {
  constructor(robot, store, an) { this.robot = robot; this.store = store; this.an = an; }

  init(tl, st) {
    tl.key('x', st.t, st.pose.x); tl.key('y', st.t, st.pose.y); tl.key('yaw', st.t, st.pose.yaw); tl.key('sh', st.t, st.sh);
    tl.key('qL', st.t, st.q.left); tl.key('qR', st.t, st.q.right); tl.key('gL', st.t, st.grip.left); tl.key('gR', st.t, st.grip.right);
  }
  hold(tl, st) { for (const n of ['x', 'y', 'yaw', 'sh', 'qL', 'qR', 'gL', 'gR']) { const v = tl.last(n); tl.key(n, st.t, v); } }

  armTo(tl, st, side, q, minDur = 0.7, ease = true) {
    const q0 = st.q[side], d = Math.max(...q.map((v, i) => Math.abs(v - q0[i])));
    const dur = Math.max(minDur, d / 1.1);
    this.hold(tl, st); st.t += dur; tl.key(side === 'left' ? 'qL' : 'qR', st.t, q, ease); st.q[side] = q.slice(); this.hold(tl, st);
    return dur;
  }
  // straight-line TCP path via warm-started IK (n steps)
  lineTo(tl, st, side, goalFrom, goalTo, n, speed = 0.15) {
    const len = Math.hypot(...goalTo.p.map((v, i) => v - goalFrom.p[i])), dur = Math.max(0.5, len / speed);
    this.hold(tl, st); const t0 = st.t; let q = st.q[side];
    for (let k = 1; k <= n; k++) {
      const u = k / n, g = { p: goalFrom.p.map((v, i) => lerp(v, goalTo.p[i], u)), a: goalTo.a, c: goalTo.c };
      const r = this.an.solve(side, g, st.sh, this.an.cfg.bpX, [q]); q = r.q;
      tl.key(side === 'left' ? 'qL' : 'qR', t0 + dur * u, q, k === n || k === 1 ? true : false);
    }
    st.t = t0 + dur; st.q[side] = q.slice(); this.hold(tl, st); return q;
  }
  gripTo(tl, st, side, v, dur = 0.5) { this.hold(tl, st); st.t += dur; tl.key(side === 'left' ? 'gL' : 'gR', st.t, v); st.grip[side] = v; this.hold(tl, st); }
  liftTo(tl, st, sh) {
    if (Math.abs(sh - st.sh) < 1e-4) return;
    this.hold(tl, st); st.t += Math.abs(sh - st.sh) / ROBOT.COL.SPEED; tl.key('sh', st.t, sh); st.sh = sh; this.hold(tl, st);
  }
  straight(tl, st, x, y, speed) {
    const d = Math.hypot(x - st.pose.x, y - st.pose.y); if (d < 0.005) return;
    this.hold(tl, st); st.t += Math.max(0.8, d / speed + 0.6); tl.key('x', st.t, x); tl.key('y', st.t, y); tl.key('yaw', st.t, st.pose.yaw);
    st.pose = { x, y, yaw: st.pose.yaw }; this.hold(tl, st);
  }
  rotateTo(tl, st, yaw) {
    let d = yaw - st.pose.yaw; while (d > Math.PI) d -= 2 * Math.PI; while (d < -Math.PI) d += 2 * Math.PI;
    if (Math.abs(d) < 0.01) return;
    this.hold(tl, st); st.t += Math.abs(d) / 0.8 + 0.4; const y = st.pose.yaw + d; tl.key('yaw', st.t, y); st.pose = { ...st.pose, yaw: y }; this.hold(tl, st);
  }
  // open floor: turn on the spot, drive straight, turn to the final heading
  goTo(tl, st, x, y, yaw, speed = 0.5) {
    const dx = x - st.pose.x, dy = y - st.pose.y;
    if (Math.hypot(dx, dy) > 0.02) { this.rotateTo(tl, st, Math.atan2(dy, dx)); this.straight(tl, st, x, y, speed); }
    if (yaw !== undefined) this.rotateTo(tl, st, yaw);
  }
  // inside an aisle: straight moves plus a forward S-curve for lateral shifts (backs up first when there is no room)
  driveTo(tl, st, pose, speed) {
    const p0 = st.pose, dy = pose.y - p0.y;
    if (Math.abs(dy) < 0.02) { this.straight(tl, st, pose.x, p0.y, speed); if (Math.abs(dy) > 0.002) this.straight(tl, st, pose.x, pose.y, 0.1); return; }
    const need = Math.max(0.6, 1.3 * Math.abs(dy));
    if (pose.x - p0.x < need) this.straight(tl, st, pose.x - need, p0.y, speed);
    this.hold(tl, st);
    const q0 = st.pose, dx = pose.x - q0.x, c = dx / 2;
    const curve = new THREE.CubicBezierCurve3(V3(q0.x, q0.y, 0), V3(q0.x + c, q0.y, 0), V3(pose.x - c, pose.y, 0), V3(pose.x, pose.y, 0));
    const L = curve.getLength(), dur = Math.max(1.2, L / speed + 0.8), n = 20, t0 = st.t;
    for (let k = 1; k <= n; k++) {
      const u = k / n, sm = smooth(u), p = curve.getPointAt(sm), tg = curve.getTangentAt(Math.min(0.999, Math.max(0.001, sm)));
      tl.key('x', t0 + dur * u, p.x, false); tl.key('y', t0 + dur * u, p.y, false); tl.key('yaw', t0 + dur * u, k === n ? 0 : Math.atan2(tg.y, tg.x), false);
    }
    st.t = t0 + dur; st.pose = { x: pose.x, y: pose.y, yaw: 0 }; this.hold(tl, st);
  }
  aisleOf(y) { let best = null; for (const a of this.store.aisles) if (!best || Math.abs(y - a.cy) < Math.abs(y - best.cy)) best = a; return best; }
  // route between any two poses: S-curves inside one aisle, reverse out and turn on the open floor otherwise
  route(tl, st, target, speed = 0.5) {
    const inA = p => p.x > -0.45;
    if (inA(st.pose) && inA(target) && this.aisleOf(st.pose.y) === this.aisleOf(target.y)) { this.driveTo(tl, st, target, speed); return; }
    if (inA(st.pose)) { this.rotateTo(tl, st, 0); this.straight(tl, st, -0.85, st.pose.y, speed); }
    if (inA(target)) { this.goTo(tl, st, -0.85, target.y, 0, speed); this.straight(tl, st, target.x, target.y, speed); }
    else this.goTo(tl, st, target.x, target.y, target.yaw, speed);
  }
  stowBoth(tl, st) {
    for (const side of ['left', 'right']) if (STOWQ[side].some((v, i) => Math.abs(v - st.q[side][i]) > 0.05)) this.armTo(tl, st, side, STOWQ[side]);
  }

  // one pick-to-tote cycle; returns info for the result panel
  cycle(tl, st, slot, stopKey) {
    const an = this.an, R = this.robot, side = an.armFor(slot), T = TYPES[slot.type], bpX = an.cfg.bpX;
    const sh = ROBOT.STOPS[stopKey];
    const ev = an.evalShelf(slot, sh), pose = ev.pose, goal = ev.goal, a = goal.a;
    const jawOpen = Math.min(1, (T.grasp.w + 2 * ARMSPEC.JAW_CLEAR + 0.004) / ARMSPEC.JAW_MAX), jawHold = Math.max(0.04, (T.grasp.w - 0.004) / ARMSPEC.JAW_MAX);
    const t0 = st.t, code = locCode(slot);
    this.stowBoth(tl, st);
    const travel = Math.hypot(pose.x - st.pose.x, pose.y - st.pose.y);
    if (travel > 0.05) { if (st.sh > ROBOT.STOPS.L1000) { tl.note(st.t, 'Lift to L1000 for travel'); this.liftTo(tl, st, ROBOT.STOPS.L1000); } tl.note(st.t, `Drive to ${code}`); this.route(tl, st, pose, 0.5); }
    const tArrive = st.t;
    if (Math.abs(sh - st.sh) > 1e-4) { tl.note(st.t, `Lift to ${stopKey} (arms stowed, base stopped)`); this.liftTo(tl, st, sh); }
    const pre = { p: goal.p.map((v, i) => v - a[i] * 0.12), a, c: goal.c };
    const rPre = an.solve(side, pre, sh, bpX, [ev.q, ...SEEDS[side]]);
    tl.note(st.t, `Pick ${T.short} at ${code}`); this.gripTo(tl, st, side, jawOpen, 0.3);
    this.armTo(tl, st, side, rPre.q, 1.0);
    this.lineTo(tl, st, side, pre, goal, 5, 0.12);
    this.gripTo(tl, st, side, jawHold, 0.6);
    const tGrasp = st.t, qGrasp = st.q[side].slice();
    const up = { p: [goal.p[0], goal.p[1], goal.p[2] + 0.015], a, c: goal.c };
    this.lineTo(tl, st, side, goal, up, 2, 0.05);
    const back = { p: up.p.map((v, i) => v - a[i] * 0.16), a, c: goal.c };
    this.lineTo(tl, st, side, up, back, 4, 0.15);
    const items = st.tote[side], lanes = Math.max(1, Math.floor((TOTE.W - 2 * TOTE.WALL) / (T.fx + 0.01)));
    const n = items.length, lane = n % lanes, layer = Math.floor(n / lanes);
    const tg = an.toteGoal(side, slot.type, layer, lane, lanes);
    const carry = { p: [tg.p[0], tg.p[1], sh - 0.40], a: [0, 0, -1], c: [0, 1, 0] };
    const rCarry = an.solve(side, carry, sh, bpX, [st.q[side], ...SEEDS[side]]);
    tl.note(st.t, 'Carry pose over the tote'); this.armTo(tl, st, side, rCarry.q, 1.2);
    if (sh > ROBOT.STOPS.L1000) { tl.note(st.t, 'Lift to L1000 (carry pose, base stopped)'); this.liftTo(tl, st, ROBOT.STOPS.L1000); }
    const carryLow = { p: [carry.p[0], carry.p[1], carry.p[2] - (sh - ROBOT.STOPS.L1000)], a: carry.a, c: carry.c };
    const place = an.placeAt(side, tg, ROBOT.STOPS.L1000, bpX);
    const placeG = { p: place.p, a: tg.a, c: tg.c };
    tl.note(st.t, `Place in the ${side} tote`); this.lineTo(tl, st, side, carryLow, placeG, 5, 0.15);
    this.gripTo(tl, st, side, jawOpen, 0.4);
    const tRelease = st.t;
    this.lineTo(tl, st, side, placeG, { p: [placeG.p[0], placeG.p[1], placeG.p[2] + 0.10], a: tg.a, c: tg.c }, 2, 0.15);
    this.armTo(tl, st, side, STOWQ[side], 1.0);
    this.gripTo(tl, st, side, 0.6, 0.3);
    // bookkeeping: item <- ee offset at the grasp, release and resting pose in the robot frame
    const eeG = new THREE.Matrix4().copy(R.matrixFor(pose)).multiply(R.fk(side, qGrasp, sh, bpX).ee);
    const itemW = new THREE.Matrix4().compose(slot.pos.clone(), new THREE.Quaternion().setFromEuler(new THREE.Euler(0, 0, slot.yaw)), V3(1, 1, 1));
    const offset = eeG.clone().invert().multiply(itemW);
    const eeR = R.fk(side, tl.value(side === 'left' ? 'qL' : 'qR', tRelease), ROBOT.STOPS.L1000, bpX).ee;
    const relLocal = eeR.clone().multiply(offset);
    const bb = productAsset(slot.type, slot.v).geo.boundingBox.clone().applyMatrix4(relLocal);
    const rest = relLocal.clone().premultiply(new THREE.Matrix4().makeTranslation(0, 0, tg.rest - bb.min.z));
    const rec = { slot, side, stop: stopKey, code, phases: [{ t: tGrasp, kind: 'grip', side, offset }, { t: tRelease, kind: 'robot', from: relLocal, rest }], offset, rest, tGrasp, tRelease };
    items.push(rec); tl.items.push(rec);
    return { slot, side, stop: stopKey, ev, cycle: st.t - t0, travelT: tArrive - t0, drop: Math.max(0, bb.min.z - tg.rest), placeOk: place.ok, rec };
  }

  // drive to the packing table (facing it) and unload both totes onto it, items standing upright
  unload(tl, st) {
    const an = this.an, R = this.robot, Tb = this.store.table, bpX = an.cfg.bpX, sh = ROBOT.STOPS.L1000;
    this.stowBoth(tl, st); this.liftTo(tl, st, sh);
    const park = { x: Tb.x1 + 0.03 - ROBOT.X0, y: Tb.yc, yaw: Math.PI };
    tl.note(st.t, 'Drive to the packing table'); this.route(tl, st, { x: park.x + 0.5, y: park.y, yaw: Math.PI });
    this.straight(tl, st, park.x, park.y, 0.25);
    const RW = R.matrixFor(st.pose);                                   // table edge sits 0.42 m ahead of base_link
    const out = [];
    for (const side of ['left', 'right']) {
      const s = side === 'left' ? 1 : -1, list = st.tote[side].slice().reverse();
      let k = 0;
      for (const rec of list) {
        const T = TYPES[rec.slot.type];
        const jawOpen = Math.min(1, (T.grasp.w + 2 * ARMSPEC.JAW_CLEAR + 0.004) / ARMSPEC.JAW_MAX), jawHold = Math.max(0.04, (T.grasp.w - 0.004) / ARMSPEC.JAW_MAX);
        // re-grasp in the tote with the same grasp
        const E = rec.rest.clone().multiply(rec.offset.clone().invert());
        const e = E.elements, P = V3(0, 0, -ARMSPEC.TCP).applyMatrix4(E);
        const g = { p: [P.x, P.y, P.z], a: [-e[8], -e[9], -e[10]], c: [e[4], e[5], e[6]], strict: true };
        const above = { p: [g.p[0], g.p[1], g.p[2] + 0.12], a: g.a, c: g.c, strict: true };
        const rA = an.solve(side, above, sh, bpX, [st.q[side], STOWQ[side], ...SEEDS[side]]);
        tl.note(st.t, `Unload ${T.short} from the ${side} tote`);
        this.gripTo(tl, st, side, jawOpen, 0.3); this.armTo(tl, st, side, rA.q, 1.0);
        this.lineTo(tl, st, side, above, g, 3, 0.12);
        this.gripTo(tl, st, side, jawHold, 0.5);
        const tG = st.t, eeG = R.fk(side, st.q[side], sh, bpX).ee, off2 = eeG.clone().invert().multiply(rec.rest);
        this.lineTo(tl, st, side, g, above, 3, 0.15);
        // place standing upright on the table
        const Ri = new THREE.Matrix4().extractRotation(off2.clone().invert()), u = V3(0, 0, 1).applyMatrix4(Ri);
        const psi = -Math.atan2(-u.y, -u.x);
        // table spots [y, x ahead of the shoulder]; the shoulder sits at bpX + MOUNT_X ahead of base_link
        const spots = [[0.08, 0.40], [0.17, 0.40], [0.26, 0.40], [0.10, 0.50], [0.20, 0.50], [0.30, 0.48]], shX = bpX + ROBOT.MOUNT_X;
        let placed = null;
        for (; k < spots.length && !placed; k++) {
          const [yy, xx] = spots[k], itemT = new THREE.Matrix4().makeRotationZ(psi).setPosition(shX + xx, s * yy, Tb.h + 0.004);
          const Ep = itemT.clone().multiply(off2.clone().invert()), ep = Ep.elements, Pp = V3(0, 0, -ARMSPEC.TCP).applyMatrix4(Ep);
          const gp = { p: [Pp.x, Pp.y, Pp.z], a: [-ep[8], -ep[9], -ep[10]], c: [ep[4], ep[5], ep[6]], strict: true };
          const pre = { p: gp.p.map((v, i) => v - gp.a[i] * 0.12), a: gp.a, c: gp.c, strict: true };
          const r1 = an.solve(side, pre, sh, bpX, [st.q[side], ...SEEDS[side]]), r2 = an.solve(side, gp, sh, bpX, [r1.q]);
          if (r1.ok && r2.ok) placed = { gp, pre, q1: r1.q };
        }
        if (!placed) { tl.note(st.t, `${T.short}: no free reachable spot, stays in the tote`); this.armTo(tl, st, side, STOWQ[side]); continue; }
        this.armTo(tl, st, side, placed.q1, 1.2);
        this.lineTo(tl, st, side, placed.pre, placed.gp, 4, 0.12);
        this.gripTo(tl, st, side, jawOpen, 0.4);
        const tR = st.t, eeP = R.fk(side, st.q[side], sh, bpX).ee;
        const relW = RW.clone().multiply(eeP).multiply(off2);
        const bb = productAsset(rec.slot.type, rec.slot.v).geo.boundingBox.clone().applyMatrix4(relW);
        const restW = relW.clone().premultiply(new THREE.Matrix4().makeTranslation(0, 0, Tb.h - bb.min.z));
        rec.phases.push({ t: tG, kind: 'grip', side, offset: off2 }, { t: tR, kind: 'world', from: relW, rest: restW });
        rec.tTable = tR;
        this.lineTo(tl, st, side, placed.gp, placed.pre, 3, 0.15);
        out.push(rec);
      }
      this.armTo(tl, st, side, STOWQ[side], 1.0); this.gripTo(tl, st, side, 0.6, 0.2);
      st.tote[side] = st.tote[side].filter(r => !out.includes(r));
    }
    this.straight(tl, st, park.x + 0.5, park.y, 0.25);
    return out;
  }
}

export function locCode(sl) { return `${sl.aisle}${sl.side}-0${sl.bay + 1}-${sl.level + 1}${'abc'[sl.seg] && sl.multi ? 'abc'[sl.seg] : ''}`; }

// Applies the timeline state at time t to the robot and the moving items.
export class Player {
  constructor(robot, store, scene) { this.robot = robot; this.store = store; this.scene = scene; this.meshes = new Map(); this.tl = null; this.t = 0; }
  meshFor(it) {
    let m = this.meshes.get(it);
    if (!m) { const a = productAsset(it.slot.type, it.slot.v); m = new THREE.Mesh(a.geo, a.mats); m.castShadow = true; m.receiveShadow = true; m.matrixAutoUpdate = false; this.meshes.set(it, m); }
    return m;
  }
  clear() {
    for (const [it, m] of this.meshes) { if (m.parent) m.parent.remove(m); if (it.slot.picked) this.store.hideSlot(it.slot, false); }
    this.meshes.clear(); this.tl = null;
  }
  apply(t) {
    const tl = this.tl, R = this.robot; if (!tl) return;
    this.t = t;
    R.setPose(tl.value('x', t), tl.value('y', t), tl.value('yaw', t));
    const sh = tl.value('sh', t); if (Math.abs(sh - R.sh) > 1e-6) R.setLift(sh);
    R.arm.left.grip = tl.value('gL', t); R.arm.right.grip = tl.value('gR', t);
    R.applyArm('left', tl.value('qL', t)); R.applyArm('right', tl.value('qR', t));
    R.g.updateMatrixWorld(true);
    const a = new THREE.Vector3(), b = new THREE.Vector3(), q = new THREE.Quaternion(), s = new THREE.Vector3();
    for (const it of tl.items) {
      const m = this.meshFor(it); let cur = null;
      for (const p of it.phases) if (t >= p.t) cur = p;
      if (!cur) { if (m.parent) m.parent.remove(m); if (it.slot.picked) this.store.hideSlot(it.slot, false); continue; }
      if (!it.slot.picked) this.store.hideSlot(it.slot, true);
      if (cur.kind === 'grip') {
        if (m.parent !== this.scene) this.scene.add(m);
        m.matrix.copy(R.g.matrixWorld).multiply(R.arm[cur.side].ee).multiply(cur.offset);
      } else {
        const par = cur.kind === 'robot' ? R.g : this.scene; if (m.parent !== par) par.add(m);
        const u = Math.min(1, (t - cur.t) / 0.25), e = u * u;
        cur.from.decompose(a, q, s); b.setFromMatrixPosition(cur.rest);
        m.matrix.compose(a.lerp(b, e), q, s);
      }
      m.matrixWorldNeedsUpdate = true;
    }
  }
}
