import * as THREE from 'three';
import { mergeGeometries } from 'three/examples/jsm/utils/BufferGeometryUtils.js';
import { ART, packArt } from './textures.js';

// Item local frame: origin at the bottom centre, +Z up, X = facing width along the shelf, -Y = front face (toward the aisle).
// grasp: width the jaws close across, z of the grasp point above the bottom, kind of grasp.

function lathe(profile, seg = 20) {
  const g = new THREE.LatheGeometry(profile.map(([r, z]) => new THREE.Vector2(r, z)), seg);
  g.rotateX(Math.PI / 2); return g;
}
function band(r, z0, z1, seg = 20) {
  const g = new THREE.CylinderGeometry(r, r, z1 - z0, seg, 1, true);
  g.rotateX(Math.PI / 2); g.translate(0, 0, (z0 + z1) / 2); return g;
}
function cyl(r, z0, z1, seg = 16) { const g = new THREE.CylinderGeometry(r, r, z1 - z0, seg); g.rotateX(Math.PI / 2); g.translate(0, 0, (z0 + z1) / 2); return g; }
function boxAt(w, d, h, x = 0, y = 0, z = 0) { const g = new THREE.BoxGeometry(w, d, h); g.translate(x, y, z + h / 2); return g; }
const NI = g => (g.index ? g.toNonIndexed() : g);
function merge(list) { return mergeGeometries(list.map(g => { const n = g.index ? NI(g) : g; if (!n.attributes.uv) n.setAttribute('uv', new THREE.BufferAttribute(new Float32Array(n.attributes.position.count * 2), 2)); return n; }), true); }

const M = {
  pet: () => new THREE.MeshPhysicalMaterial({ color: 0xdff1fb, roughness: 0.04, metalness: 0, transparent: true, opacity: 0.38, clearcoat: 1, side: THREE.DoubleSide, depthWrite: false }),
  water: () => new THREE.MeshPhysicalMaterial({ color: 0xbfe1f3, roughness: 0.05, transparent: true, opacity: 0.55, clearcoat: 1, depthWrite: false }),
  brownGlass: () => new THREE.MeshPhysicalMaterial({ color: 0x3b1a05, roughness: 0.07, metalness: 0.05, clearcoat: 1, clearcoatRoughness: 0.05, sheen: 0 }),
  greenGlass: () => new THREE.MeshPhysicalMaterial({ color: 0x173d16, roughness: 0.07, metalness: 0.05, clearcoat: 1 }),
  juice: (c) => new THREE.MeshPhysicalMaterial({ color: c, roughness: 0.12, clearcoat: 1, transmission: 0 }),
  cap: (c, metal = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: 0.35, metalness: metal }),
  label: (tex, rough = 0.45) => new THREE.MeshStandardMaterial({ map: tex, roughness: rough, metalness: 0 }),
  plain: (c, rough = 0.6, metal = 0) => new THREE.MeshStandardMaterial({ color: c, roughness: rough, metalness: metal }),
  film: () => new THREE.MeshPhysicalMaterial({ color: 0xffffff, roughness: 0.15, transparent: true, opacity: 0.18, clearcoat: 1, depthWrite: false }),
  print: (tex) => new THREE.MeshStandardMaterial({ map: tex, transparent: true, roughness: 0.3, depthWrite: false }),
};

// ------------------------------------------------------------------------------------------------ geometry builders
function beerBottle(v) {
  const prof = [[0, 0], [0.028, 0.0], [0.0335, 0.006], [0.0335, 0.150], [0.031, 0.172], [0.021, 0.200], [0.0145, 0.222], [0.0135, 0.243], [0.0148, 0.246], [0.0148, 0.251], [0, 0.252]];
  const glass = lathe(prof, 22), lab = band(0.0339, 0.045, 0.125, 22), neck = band(0.0152, 0.212, 0.232, 16), cap = cyl(0.0157, 0.249, 0.256, 16);
  return { geo: merge([glass, lab, neck, cap]), mats: [v ? M.greenGlass() : M.brownGlass(), M.label(ART.beer(v), 0.55), M.plain(v ? 0x7a1f1f : 0xd7b85a, 0.5), M.cap(0xc9a43a, 0.8)] };
}
function juiceBottle(v) {
  const prof = [[0, 0.001], [0.028, 0.0], [0.0365, 0.008], [0.037, 0.17], [0.034, 0.195], [0.024, 0.215], [0.0175, 0.225], [0, 0.226]];
  const body = lathe(prof, 22), lab = band(0.0375, 0.06, 0.165, 22), cap = cyl(0.0195, 0.225, 0.248, 18), ring = cyl(0.021, 0.222, 0.226, 18);
  return { geo: merge([body, lab, cap, ring]), mats: [M.juice(v ? 0xd8c25a : 0xf28c12), M.label(ART.juice(v), 0.4), M.cap(v ? 0x2f7d22 : 0xe2561b), M.cap(0xf2f2f2)] };
}
function waterBottle(v, label = true) {
  const prof = [[0, 0.002], [0.035, 0], [0.0445, 0.012], [0.0445, 0.06], [0.041, 0.07], [0.0445, 0.08], [0.0445, 0.215], [0.036, 0.255], [0.022, 0.282], [0.0145, 0.292], [0.0145, 0.300], [0, 0.300]];
  const body = lathe(prof, 22), cap = cyl(0.016, 0.298, 0.318, 16), list = [body, cap];
  if (label) list.splice(1, 0, band(0.045, 0.11, 0.19, 22));
  const mats = label ? [M.water(), M.label(ART.water(v), 0.35), M.cap(v ? 0x2fa44a : 0x2a6fb6)] : [M.water(), M.cap(v ? 0x2fa44a : 0x2a6fb6)];
  return { geo: merge(list), mats };
}
function sodaCan(v) {
  const prof = [[0, 0.001], [0.025, 0], [0.033, 0.008], [0.033, 0.103], [0.027, 0.113], [0.026, 0.115], [0, 0.1145]];
  return { geo: merge([lathe(prof, 22), band(0.0332, 0.012, 0.1, 22)]), mats: [M.plain(0xcfd3d6, 0.25, 0.9), M.label(ART.can(v), 0.3)] };
}
function milkCarton(v) {
  const g = new THREE.BoxGeometry(0.063, 0.095, 0.195); g.translate(0, 0, 0.0975);
  const top = boxAt(0.063, 0.012, 0.012, 0, 0, 0.195), cap = cyl(0.0125, 0.193, 0.207, 14); cap.translate(0, -0.022, 0);
  const side = M.label(ART.milkSide(v), 0.55), front = M.label(ART.milk(v), 0.5), white = M.plain(0xf7f7f2, 0.6);
  // BoxGeometry groups: +x, -x, +y, -y, +z, -z ; mergeGeometries keeps one group per source -> rebuild materials per box face
  const geo = mergeGeometries([NI(g), NI(top), NI(cap)], false);
  geo.clearGroups();
  const perFace = 6;   // box: 6 faces x 6 verts
  for (let f = 0; f < 6; f++) geo.addGroup(f * perFace, perFace, [1, 1, 2, 0, 3, 2][f]);
  geo.addGroup(36, NI(top).attributes.position.count, 2);
  geo.addGroup(36 + NI(top).attributes.position.count, NI(cap).attributes.position.count, 4);
  return { geo, mats: [front, side, white, white, M.cap(v ? 0xc8312b : 0x1f5fae)] };
}
function chipsBag(v) {
  const W = 0.19, D = 0.075, H = 0.26;
  const g = new THREE.BoxGeometry(W, D, H, 10, 4, 14), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i), u = z / H + 0.5, s = 2 * x / W;
    let k = Math.pow(Math.sin(Math.PI * Math.min(1, Math.max(0, (u - 0.04) / 0.92))), 0.45) * (1 - 0.35 * Math.pow(Math.abs(s), 6));
    if (u < 0.05 || u > 0.95) k = 0.04;
    p.setY(i, y * k); p.setZ(i, z + H / 2); p.setX(i, x * (1 - 0.03 * k));
  }
  g.computeVertexNormals();
  const art = M.label(ART.chips(v), 0.32); art.metalness = 0.35;
  const plainM = M.plain([0xd62a1f, 0x1f7fd6, 0x2c8f3b][v % 3], 0.35, 0.3);
  g.groups.forEach(gr => { gr.materialIndex = gr.materialIndex === 3 || gr.materialIndex === 2 ? 0 : 1; });
  return { geo: g, mats: [art, plainM] };
}
function pretzelBox() {
  const g = new THREE.BoxGeometry(0.068, 0.068, 0.24); g.translate(0, 0, 0.12);
  g.groups.forEach(gr => { gr.materialIndex = gr.materialIndex === 3 || gr.materialIndex === 2 ? 0 : 1; });
  return { geo: g, mats: [M.label(ART.pretzel(), 0.5), M.plain(0x123a73, 0.5)] };
}
function waterPack(v) {
  const list = [];
  const one = waterBottle(v, false).geo;
  for (let i = 0; i < 3; i++) for (let j = 0; j < 2; j++) { const b = one.clone(); b.translate((i - 1) * 0.09, (j - 0.5) * 0.09, 0); list.push(b); }
  const bottles = mergeGeometries(list.map(g => NI(g)), true);
  const wrap = boxAt(0.276, 0.186, 0.25, 0, 0, 0.012), printBand = boxAt(0.278, 0.188, 0.07, 0, 0, 0.12);
  const handle = boxAt(0.04, 0.12, 0.006, 0, 0, 0.318);
  const geo = mergeGeometries([bottles, NI(wrap), NI(printBand), NI(handle)], true);
  // groups from bottles: alternating body/cap per bottle -> remap
  geo.clearGroups();
  let off = 0;
  for (const b of list) { const n = NI(b); const bodyN = n.groups[0] ? n.groups[0].count : n.attributes.position.count; geo.addGroup(off, bodyN, 0); geo.addGroup(off + bodyN, n.attributes.position.count - bodyN, 1); off += n.attributes.position.count; }
  const wn = NI(wrap).attributes.position.count; geo.addGroup(off, wn, 2); off += wn;
  const pn = NI(printBand).attributes.position.count; geo.addGroup(off, pn, 3); off += pn;
  geo.addGroup(off, NI(handle).attributes.position.count, 4);
  return { geo, mats: [M.water(), M.cap(v ? 0x2fa44a : 0x2a6fb6), M.film(), M.print(ART.pack(v)), M.plain(0xffffff, 0.6)] };
}
function beerCrate(v) {
  const W = 0.30, D = 0.40, H = 0.31, t = 0.008, parts = [];
  parts.push(boxAt(W, D, 0.01));
  parts.push(boxAt(t, D, H, -W / 2 + t / 2), boxAt(t, D, H, W / 2 - t / 2), boxAt(W, t, H, 0, -D / 2 + t / 2), boxAt(W, t, H, 0, D / 2 - t / 2));
  const necks = [];
  for (let i = 0; i < 4; i++) for (let j = 0; j < 5; j++) {
    const x = (i - 1.5) * 0.071, y = (j - 2) * 0.077;
    const n = band(0.0145, 0.22, 0.29, 10); n.translate(x, y, 0); necks.push(n);
    const s = band(0.03, 0.17, 0.22, 12); s.translate(x, y, 0); necks.push(s);
    const c = cyl(0.0157, 0.29, 0.297, 10); c.translate(x, y, 0); necks.push(c);
  }
  const crate = mergeGeometries(parts.map(g => NI(g)), false);
  const glass = mergeGeometries(necks.filter((_, k) => k % 3 !== 2).map(g => NI(g)), false);
  const caps = mergeGeometries(necks.filter((_, k) => k % 3 === 2).map(g => NI(g)), false);
  const front = boxAt(W + 0.002, 0.002, H * 0.9, 0, -D / 2 - 0.001, 0.01);
  const geo = mergeGeometries([crate, glass, caps, NI(front)], true);
  return { geo, mats: [M.plain(v ? 0x1e4f2e : 0x5a2a14, 0.55), v ? M.greenGlass() : M.brownGlass(), M.cap(0xc9a43a, 0.8), M.label(ART.crate(v), 0.55)] };
}


// ------------------------------------------------------------------------------------------------ wider assortment
const pick = (arr, v) => arr[v % arr.length];
function bag(W, D, H, art, side) {
  const g = new THREE.BoxGeometry(W, D, H, 10, 4, 14), p = g.attributes.position;
  for (let i = 0; i < p.count; i++) {
    const x = p.getX(i), y = p.getY(i), z = p.getZ(i), u = z / H + 0.5, s = 2 * x / W;
    let k = Math.pow(Math.sin(Math.PI * Math.min(1, Math.max(0, (u - 0.05) / 0.9))), 0.45) * (1 - 0.35 * Math.pow(Math.abs(s), 6));
    if (u < 0.06 || u > 0.94) k = 0.05;
    p.setY(i, y * k); p.setZ(i, z + H / 2); p.setX(i, x * (1 - 0.03 * k));
  }
  g.computeVertexNormals();
  g.groups.forEach(gr => { gr.materialIndex = gr.materialIndex === 3 || gr.materialIndex === 2 ? 0 : 1; });
  const a = M.label(art, 0.3); a.metalness = 0.3;
  return { geo: g, mats: [a, M.plain(side, 0.35, 0.25)] };
}
function cartonBox(W, D, H, art, side) {
  const g = new THREE.BoxGeometry(W, D, H); g.translate(0, 0, H / 2);
  g.groups.forEach(gr => { gr.materialIndex = gr.materialIndex === 3 || gr.materialIndex === 2 ? 0 : 1; });
  return { geo: g, mats: [M.label(art, 0.55), M.plain(side, 0.6)] };
}
const GUMMY = [['Fruchtbär', 'Gummibärchen', ['#ffd23f', '#f7a400'], '#e63946', 'dots', '#7a1f1f'], ['Sauerwurm', 'saure Würmer', ['#7ae582', '#25a244'], '#ffd23f', 'dots', '#0b3d17']];
const NUTS = [['Nussgarten', 'Erdnüsse geröstet', ['#7f4f24', '#582f0e'], '#e9c46a', 'photo', '#fff'], ['Nussgarten', 'Studentenfutter', ['#386641', '#1b4332'], '#bc6c25', 'photo', '#fff']];
const TUBE = [['Stapelkrisp', 'Original', ['#c1121f', '#780000'], '#fdf0d5', 'burst', '#fff'], ['Stapelkrisp', 'Sour Cream', ['#2a9d8f', '#1d5c55'], '#e9f5db', 'burst', '#fff']];
const ENERGY = [['VOLTA', 'Energy · 250 ml', ['#1d1d1d', '#3c096c'], '#9d4edd', 'stripes', '#fff'], ['VOLTA', 'Zero · 250 ml', ['#e0e0e0', '#9e9e9e'], '#00b4d8', 'stripes', '#111']];
const TEA = [['Teegarten', 'Pfirsich Eistee', ['#ffb703', '#fb8500'], '#ffffff', 'band', '#5a2a00'], ['Teegarten', 'Zitrone Eistee', ['#d9ed92', '#76c893'], '#ffffff', 'band', '#1a4314']];
const CHOCO = [['Kakaowerk', 'Vollmilch', ['#5e3023', '#3b1f15'], '#c89f9c', 'band', '#fff'], ['Kakaowerk', 'Zartbitter 70%', ['#1b1b1b', '#3d2b1f'], '#bfa181', 'band', '#fff'], ['Kakaowerk', 'Haselnuss', ['#3a5a40', '#283618'], '#dda15e', 'band', '#fff']];
const CEREAL = [['Morgenstund', 'Cornflakes', ['#ffd60a', '#ffc300'], '#003566', 'photo', '#003566'], ['Morgenstund', 'Schoko Crunchy', ['#6f1d1b', '#432818'], '#ffe6a7', 'photo', '#fff'], ['Morgenstund', 'Hafer Müsli', ['#a3b18a', '#588157'], '#dad7cd', 'photo', '#fff']];
const COOKIE = [['Backstübchen', 'Butterkeks', ['#ffd166', '#f4a261'], '#e76f51', 'photo', '#5a2a00'], ['Backstübchen', 'Choco Cookies', ['#3d2b1f', '#5e3023'], '#d4a373', 'photo', '#fff']];
const COFFEE = [['Röstzeit', 'Crema · Bohnen', ['#283618', '#1b1b1b'], '#bc6c25', 'band', '#fefae0'], ['Röstzeit', 'Espresso · gemahlen', ['#6a040f', '#370617'], '#ffba08', 'band', '#fff']];
const PASTA = [['Nonna Lia', 'Spaghetti n.5', ['#023e8a', '#0077b6'], '#ffffff', 'band', '#fff'], ['Nonna Lia', 'Linguine', ['#9d0208', '#6a040f'], '#ffffff', 'band', '#fff']];
const art = (d, w, h, wrap) => packArt({ w, h, brand: d[0], name: d[1], bg: d[2], accent: d[3], style: d[4], ink: d[5], wrap });

function gummyBag(v) { const d = pick(GUMMY, v); return bag(0.14, 0.055, 0.20, art(d, 512, 768), d[2][1]); }
function nutsBag(v) { const d = pick(NUTS, v); return bag(0.12, 0.05, 0.17, art(d, 512, 768), d[2][1]); }
function crispTube(v) {
  const d = pick(TUBE, v);
  return { geo: merge([cyl(0.0375, 0, 0.228, 22), band(0.0377, 0.004, 0.226, 22), cyl(0.039, 0.228, 0.24, 22)]), mats: [M.plain(d[2][1], 0.4, 0.3), M.label(art(d, 1024, 300, true), 0.3), M.cap(d[2][0], 0.2)] };
}
function energyCan(v) {
  const d = pick(ENERGY, v), prof = [[0, 0.001], [0.02, 0], [0.0265, 0.007], [0.0265, 0.124], [0.022, 0.133], [0.021, 0.135], [0, 0.1345]];
  return { geo: merge([lathe(prof, 20), band(0.0267, 0.01, 0.12, 20)]), mats: [M.plain(0xcfd3d6, 0.25, 0.9), M.label(art(d, 1024, 300, true), 0.25)] };
}
function teaBottle(v) {
  const d = pick(TEA, v), prof = [[0, 0.001], [0.025, 0], [0.0325, 0.008], [0.0325, 0.14], [0.03, 0.16], [0.02, 0.18], [0.0145, 0.19], [0, 0.191]];
  return { geo: merge([lathe(prof, 20), band(0.033, 0.05, 0.13, 20), cyl(0.0165, 0.19, 0.208, 16)]), mats: [M.juice(v ? 0xc9d96b : 0xd98a2b), M.label(art(d, 1024, 300, true), 0.35), M.cap(0xffffff)] };
}
function chocoBar(v) { const d = pick(CHOCO, v); return cartonBox(0.08, 0.018, 0.16, art(d, 512, 1024), d[2][1]); }
function cerealBox(v) { const d = pick(CEREAL, v); return cartonBox(0.19, 0.065, 0.28, art(d, 512, 768), d[2][1]); }
function cookieBox(v) { const d = pick(COOKIE, v); return cartonBox(0.12, 0.05, 0.18, art(d, 512, 768), d[2][1]); }
function coffeeBag(v) { const d = pick(COFFEE, v); return bag(0.10, 0.075, 0.21, art(d, 512, 1024), d[2][1]); }
function pastaBox(v) { const d = pick(PASTA, v); return cartonBox(0.075, 0.03, 0.27, art(d, 512, 1536), d[2][1]); }
function ketchup(v) {
  const prof = [[0, 0.016], [0.03, 0.016], [0.037, 0.03], [0.038, 0.13], [0.03, 0.17], [0.0, 0.172]];
  const body = lathe(prof, 20); body.scale(1, 0.7, 1);
  const cap = cyl(0.021, 0, 0.018, 18), lab = band(0.0385, 0.05, 0.12, 20); lab.scale(1, 0.7, 1);
  const geo = merge([body, lab, cap]); geo.rotateZ(Math.PI / 2);
  return { geo, mats: [M.juice(0xb3120f), M.label(packArt({ w: 1024, h: 300, brand: 'Tomatino', name: v ? 'Curry Ketchup' : 'Tomaten Ketchup', bg: ['#ffffff', '#f1f1f1'], accent: '#d00000', style: 'band', ink: '#9d0208', wrap: true }), 0.4), M.cap(0xffffff)] };
}

// ------------------------------------------------------------------------------------------------ catalogue
export const TYPES = {
  milk:   { name: 'Milk 1 L carton', short: 'Milk 1 L', build: milkCarton, fx: 0.063, d: 0.095, h: 0.207, mass: 1.04, grasp: { w: 0.063, z: 0.12, kind: 'body' }, gap: 0.006, price: '1,19' },
  juice:  { name: 'Juice 1 L PET bottle', short: 'Juice 1 L', build: juiceBottle, fx: 0.074, d: 0.074, h: 0.248, mass: 1.08, grasp: { w: 0.074, z: 0.12, kind: 'body' }, gap: 0.008, price: '2,49' },
  beer:   { name: 'Beer 0.5 L glass bottle', short: 'Beer 0.5 L', build: beerBottle, fx: 0.067, d: 0.067, h: 0.256, mass: 0.86, grasp: { w: 0.067, z: 0.10, kind: 'body' }, gap: 0.006, price: '0,99' },
  water:  { name: 'Water 1.5 L PET bottle', short: 'Water 1.5 L', build: waterBottle, fx: 0.089, d: 0.089, h: 0.318, mass: 1.56, grasp: { w: 0.032, z: 0.275, kind: 'neck', body: 0.089 }, gap: 0.006, price: '0,49' },
  can:    { name: 'Soft drink 0.33 L can', short: 'Can 0.33 L', build: sodaCan, fx: 0.066, d: 0.066, h: 0.115, mass: 0.35, grasp: { w: 0.066, z: 0.06, kind: 'body' }, gap: 0.004, price: '0,89' },
  chips:  { name: 'Crisps 150 g bag', short: 'Crisps 150 g', build: chipsBag, fx: 0.19, d: 0.075, h: 0.26, mass: 0.17, grasp: { w: 0.006, z: 0.248, kind: 'seal' }, gap: 0.012, price: '1,99' },
  pretzel:{ name: 'Pretzel sticks 250 g box', short: 'Pretzels 250 g', build: pretzelBox, fx: 0.068, d: 0.068, h: 0.24, mass: 0.27, grasp: { w: 0.068, z: 0.15, kind: 'body' }, gap: 0.008, price: '1,29' },
  pack:   { name: 'Water 6 × 1.5 L shrink pack', short: 'Water 6-pack', build: waterPack, fx: 0.276, d: 0.186, h: 0.32, mass: 9.5, grasp: { w: 0.276, z: 0.20, kind: 'body' }, gap: 0.01, price: '2,99' },
  crate:  { name: 'Beer crate 20 × 0.5 L', short: 'Beer crate', build: beerCrate, fx: 0.30, d: 0.40, h: 0.31, mass: 17.5, grasp: { w: 0.30, z: 0.25, kind: 'body' }, gap: 0.01, price: '15,99' },
};

Object.assign(TYPES, {
  gummy:  { name: 'Gummy sweets 200 g bag', short: 'Gummies 200 g', build: gummyBag, fx: 0.14, d: 0.055, h: 0.20, mass: 0.21, grasp: { w: 0.006, z: 0.19, kind: 'seal' }, gap: 0.01, price: '1,49' },
  nuts:   { name: 'Roasted nuts 200 g bag', short: 'Nuts 200 g', build: nutsBag, fx: 0.12, d: 0.05, h: 0.17, mass: 0.21, grasp: { w: 0.006, z: 0.162, kind: 'seal' }, gap: 0.01, price: '2,29' },
  tube:   { name: 'Stacked crisps 165 g tube', short: 'Crisps tube', build: crispTube, fx: 0.078, d: 0.078, h: 0.24, mass: 0.21, grasp: { w: 0.075, z: 0.14, kind: 'body' }, gap: 0.008, price: '2,79' },
  energy: { name: 'Energy drink 0.25 L slim can', short: 'Energy 0.25 L', build: energyCan, fx: 0.053, d: 0.053, h: 0.135, mass: 0.27, grasp: { w: 0.053, z: 0.07, kind: 'body' }, gap: 0.005, price: '1,29' },
  icedtea:{ name: 'Iced tea 0.5 L PET bottle', short: 'Iced tea 0.5 L', build: teaBottle, fx: 0.065, d: 0.065, h: 0.208, mass: 0.53, grasp: { w: 0.065, z: 0.10, kind: 'body' }, gap: 0.006, price: '1,09' },
  choco:  { name: 'Chocolate bar 100 g', short: 'Chocolate 100 g', build: chocoBar, fx: 0.08, d: 0.018, h: 0.16, mass: 0.10, grasp: { w: 0.08, z: 0.10, kind: 'body' }, gap: 0.004, price: '1,39' },
  cereal: { name: 'Breakfast cereal 375 g box', short: 'Cereal 375 g', build: cerealBox, fx: 0.19, d: 0.065, h: 0.28, mass: 0.40, grasp: { w: 0.19, z: 0.16, kind: 'body' }, gap: 0.006, price: '2,99' },
  cookies:{ name: 'Biscuits 200 g box', short: 'Biscuits 200 g', build: cookieBox, fx: 0.12, d: 0.05, h: 0.18, mass: 0.22, grasp: { w: 0.12, z: 0.10, kind: 'body' }, gap: 0.006, price: '1,79' },
  coffee: { name: 'Coffee 500 g bag', short: 'Coffee 500 g', build: coffeeBag, fx: 0.10, d: 0.075, h: 0.21, mass: 0.52, grasp: { w: 0.10, z: 0.12, kind: 'body' }, gap: 0.008, price: '6,99' },
  pasta:  { name: 'Spaghetti 500 g box', short: 'Pasta 500 g', build: pastaBox, fx: 0.075, d: 0.03, h: 0.27, mass: 0.52, grasp: { w: 0.075, z: 0.16, kind: 'body' }, gap: 0.006, price: '1,19' },
  ketchup:{ name: 'Ketchup 500 ml squeeze bottle', short: 'Ketchup 500 ml', build: ketchup, fx: 0.076, d: 0.054, h: 0.172, mass: 0.58, grasp: { w: 0.054, z: 0.11, kind: 'body' }, gap: 0.008, price: '1,89' },
});
// squeeze bottle is gripped across its narrow side, so it faces the aisle with the narrow side
TYPES.ketchup.fx = 0.054; TYPES.ketchup.d = 0.076;

const cache = {};
export function productAsset(type, v = 0) {
  const k = type + v;
  if (!cache[k]) { const a = TYPES[type].build(v); a.geo.computeBoundingBox(); cache[k] = a; }
  return cache[k];
}
