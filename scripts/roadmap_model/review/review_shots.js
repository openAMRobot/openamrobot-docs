// Labelled review renders of the roadmap model: own camera, numbered markers on parts and cables, legend panel.
// Serve docs/assets/roadmap first: (cd docs/assets/roadmap && python3 -m http.server 8765)
//   node scripts/roadmap_model/review/review_shots.js scripts/roadmap_model/review/views.json <out dir> [name filter] [base URL]
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const VIEWS = JSON.parse(fs.readFileSync(process.argv[2], 'utf8'));
const OUT = process.argv[3];
const ONLY = process.argv[4] || '';
fs.mkdirSync(OUT, {recursive: true});

(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage({viewport: {width: 1700, height: 1000}});
  p.setDefaultTimeout(900000);
  const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.goto((process.argv[5] || 'http://localhost:8765/') + 'exploded.html?render=1', {waitUntil: 'load'});
  await p.waitForTimeout(3000);
  await p.evaluate(async () => {
    const csv = await (await fetch('model/cable_list.csv')).text();
    const rows = [], lines = csv.trim().split('\n');
    const parse = l => { const out = []; let cur = '', q = false; for (const ch of l) { if (ch === '"') q = !q; else if (ch === ',' && !q) { out.push(cur); cur = ''; } else cur += ch; } out.push(cur); return out; };
    const hd = parse(lines[0]);
    lines.slice(1).forEach(l => { const v = parse(l), o = {}; hd.forEach((h, i) => o[h] = v[i]); rows.push(o); });
    window.__cables = {}; rows.forEach(r => window.__cables[r.id] = r);
    window.__place = await (await fetch('model/placement.json')).json();
  });
  for (const v of VIEWS.filter(v => v.name.includes(ONLY))) {
    const url = await p.evaluate((v) => {
      const T = window.THREE, M = window.OAMR_MODEL;
      const W = 1150, H = 1000, LW = 550;
      const R = M.build(T, {headPitch: 30, fittings: true});
      const travel = v.lift || 0;
      if (travel) { R.mov.position.z += travel; M.setChain(T, travel); }
      const scene = new T.Scene();
      scene.background = new T.Color(0xf4f6f8);
      scene.add(R.root);
      scene.add(new T.HemisphereLight(0xffffff, 0x8a8f96, 1.6));
      const d1 = new T.DirectionalLight(0xffffff, 1.6); d1.position.set(2, -3, 5); scene.add(d1);
      const d2 = new T.DirectionalLight(0xffffff, 0.7); d2.position.set(-3, 2, 3); scene.add(d2);
      const names = {};
      (M.COMPONENTS || []).forEach(c => (c.nodes || c.parts || []).forEach(n => names[n] = c.name));
      const ids = Object.keys(R.parts);
      const match = (id, pats) => (pats || []).some(q => q.endsWith('*') ? id.startsWith(q.slice(0, -1)) : id === q);
      ids.forEach(id => {
        const hide = match(id, v.hide), ghost = v.ghostAll ? !match(id, v.keep) : match(id, v.ghost);
        R.parts[id].forEach(g => {
          if (hide) { g.visible = false; return; }
          if (ghost) g.traverse(o => { if (o.isMesh) { const m = (Array.isArray(o.material) ? o.material : [o.material]).map(x => { const c = x.clone(); c.transparent = true; c.opacity = v.ghostOpacity || 0.18; c.depthWrite = false; return c; }); o.material = Array.isArray(o.material) ? m : m[0]; } });
        });
      });
      if (v.hideUpper) { R.mov.visible = false; if (v.hideUpper === 2) R.col.visible = false; }
      R.root.updateMatrixWorld(true);
      const renderer = new T.WebGLRenderer({antialias: true, preserveDrawingBuffer: true});
      renderer.setSize(W, H);
      renderer.setPixelRatio(1);
      const tg = new T.Vector3(...v.target);
      let cam;
      const az = v.az * Math.PI / 180, el = v.el * Math.PI / 180;
      const dir = new T.Vector3(Math.cos(el) * Math.cos(az), Math.cos(el) * Math.sin(az), Math.sin(el));
      if (v.ortho) { const h = v.ortho, w = h * W / H; cam = new T.OrthographicCamera(-w / 2, w / 2, h / 2, -h / 2, 0.01, 20); }
      else cam = new T.PerspectiveCamera(v.fov || 30, W / H, 0.01, 20);
      cam.up.set(0, 0, 1);
      if (Math.abs(v.el) > 88) cam.up.set(1, 0, 0);
      cam.position.copy(tg).add(dir.multiplyScalar(v.dist || 3));
      cam.lookAt(tg);
      cam.updateMatrixWorld(true);
      renderer.render(scene, cam);
      // labels
      const marks = [];
      const proj = (x) => { const q = x.clone().project(cam); return [(q.x + 1) / 2 * W, (1 - q.y) / 2 * H, q.z]; };
      const box = id => { const bb = new T.Box3(); (R.parts[id] || []).forEach(g => { if (g.visible !== false) bb.expandByObject(g); }); return bb; };
      (v.labels || []).forEach(L => {
        const id = typeof L === 'string' ? L : L.id;
        const bb = box(id);
        if (bb.isEmpty()) return;
        let pt = bb.getCenter(new T.Vector3());
        if (typeof L === 'object' && L.at) pt = new T.Vector3(...L.at);
        if (typeof L === 'object' && L.top) pt.z = bb.max.z;
        marks.push({pt: proj(pt), text: (L.name || names[id] || id), sub: id, color: L.color || '#1f4e79'});
      });
      const C = window.__cables, P = window.__place;
      const ax = (P.lift_plate || {}).col_axis_x;
      (v.cables || []).forEach(cid => {
        const c = C[cid]; if (!c) return;
        let pts = null, grp = 'base';
        for (const k in P.geometry) if (k.startsWith('harness')) P.geometry[k].prims.forEach(q => { if (q.cid === cid && q.pts && !pts) { pts = q.pts; grp = P.geometry[k].group; } });
        let pt;
        if (pts) { const q = pts[Math.floor(pts.length / 2)]; pt = new T.Vector3(...q); }
        else if (c.from_xyz) { try { pt = new T.Vector3(...JSON.parse(c.from_xyz)); } catch (e) {} }
        if (!pt) return;
        if (grp === 'col' || grp === 'mov') { const o = new T.Vector3(); (grp === 'col' ? R.col : R.mov).localToWorld(o.copy(pt)); pt = o; }
        const blocked = (c.route || '').startsWith('blocked');
        marks.push({pt: proj(pt), text: cid.replace('CBL-', '') + '  ' + c.function + ' [' + c.harness + ', ' + c.gauge_or_type + (c.route_length_m ? ', ' + (+c.route_length_m).toFixed(2) + ' m' : '') + ']' + (blocked ? '  BLOCKED, drawn as fallback' : ''), color: blocked ? '#c0392b' : '#7d3c98', short: cid.replace('CBL-', '')});
      });
      (v.points || []).forEach(q => marks.push({pt: proj(new T.Vector3(...q.p)), text: q.name, color: q.color || '#117a65'}));
      const cv = document.createElement('canvas'); cv.width = W + LW; cv.height = H;
      const g = cv.getContext('2d');
      g.fillStyle = '#ffffff'; g.fillRect(0, 0, cv.width, cv.height);
      g.drawImage(renderer.domElement, 0, 0);
      g.fillStyle = 'rgba(255,255,255,.88)'; g.fillRect(0, 0, W, 54);
      g.fillStyle = '#1d2733'; g.font = '600 22px sans-serif'; g.fillText(v.title, 14, 24);
      g.font = '14px sans-serif'; g.fillStyle = '#4a5561'; g.fillText(v.sub || '', 14, 45);
      // markers with collision avoidance
      const placed = [];
      marks.forEach((m, i) => {
        m.n = i + 1;
        let [x, y] = m.pt, mx = x, my = y, tries = 0;
        while (placed.some(q => Math.hypot(q[0] - mx, q[1] - my) < 24) && tries < 40) { tries++; const a = tries * 0.9, r = 14 + tries * 4; mx = x + Math.cos(a) * r; my = y + Math.sin(a) * r; }
        mx = Math.max(14, Math.min(W - 14, mx)); my = Math.max(66, Math.min(H - 14, my));
        placed.push([mx, my]);
        if (Math.hypot(mx - x, my - y) > 3) { g.strokeStyle = m.color; g.lineWidth = 1.5; g.beginPath(); g.moveTo(x, y); g.lineTo(mx, my); g.stroke(); g.fillStyle = m.color; g.beginPath(); g.arc(x, y, 3, 0, 7); g.fill(); }
        g.fillStyle = m.color; g.beginPath(); g.arc(mx, my, 11, 0, 7); g.fill();
        g.strokeStyle = '#fff'; g.lineWidth = 2; g.stroke();
        g.fillStyle = '#fff'; g.font = '700 12px sans-serif'; g.textAlign = 'center'; g.textBaseline = 'middle'; g.fillText(String(m.n), mx, my + 0.5);
        g.textAlign = 'left'; g.textBaseline = 'alphabetic';
      });
      // legend
      g.fillStyle = '#f8f9fa'; g.fillRect(W, 0, LW, H);
      g.fillStyle = '#1d2733'; g.font = '600 16px sans-serif'; g.fillText('Legend', W + 14, 26);
      const rowH = Math.min(22, (H - 170) / Math.max(1, marks.length));
      const fs = Math.max(10, Math.min(13, rowH - 6));
      marks.forEach((m, i) => {
        const y = 48 + i * rowH;
        g.fillStyle = m.color; g.beginPath(); g.arc(W + 24, y - 4, Math.min(9, rowH / 2 - 1), 0, 7); g.fill();
        g.fillStyle = '#fff'; g.font = '700 ' + Math.min(11, fs) + 'px sans-serif'; g.textAlign = 'center'; g.fillText(String(m.n), W + 24, y);
        g.textAlign = 'left'; g.fillStyle = '#1d2733'; g.font = fs + 'px sans-serif';
        let t = m.text; while (g.measureText(t).width > LW - 50 && t.length > 4) t = t.slice(0, -2);
        if (t !== m.text) t = t.slice(0, -1) + '…';
        g.fillText(t, W + 40, y);
      });
      if (v.categories !== false) {  // cable-category colour key (harness domains of parts.yaml)
        const cats = [['#c0392b', 'Battery and BAT bus (25 / 10 / 6 mm², busbars)'], ['#e67e22', 'SAFE bus and SAFE 24 V'], ['#f1c40f', 'Regulated 24 V (always on)'],
                      ['#27ae60', '5 V and 3.3 V'], ['#2980b9', 'Signal: CAN, USB, SPI, sensor lines, safety loops']];
        let y0 = H - 18 - cats.length * 18;
        g.fillStyle = '#1d2733'; g.font = '600 13px sans-serif'; g.fillText('Cable categories', W + 14, y0 - 8);
        cats.forEach((c, i) => { g.fillStyle = c[0]; g.fillRect(W + 16, y0 + 12 + i * 18 - 10, 22, 8); g.fillStyle = '#1d2733'; g.font = '12px sans-serif'; g.fillText(c[1], W + 46, y0 + 12 + i * 18 - 2); });
      }
      renderer.dispose();
      return cv.toDataURL('image/png');
    }, v);
    fs.writeFileSync(path.join(OUT, v.name + '.png'), Buffer.from(url.split(',')[1], 'base64'));
    console.log('wrote', v.name);
  }
  console.log('errors', errs.length, errs.slice(0, 3));
  await b.close();
})();
