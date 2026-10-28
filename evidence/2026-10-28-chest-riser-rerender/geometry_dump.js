// node geodump.js <out.json>: mesh inventory of robot.html (render mode scene at t=0) and of a fresh OAMR_MODEL.build on exploded.html
const { chromium } = require('playwright'); const fs = require('fs');
const GL = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
const dump = `(() => { const THREE = window.__sim ? window.__sim.THREE : window.THREE; const out = [];
  const walk = (root, tag) => { root.updateMatrixWorld(true); root.traverse(o => { if (!o.isMesh) return;
    const path = []; for (let p = o; p && p !== root; p = p.parent) path.unshift(p.name || p.type);
    const b = new THREE.Box3().setFromObject(o); const g = o.geometry; const pos = g.attributes.position;
    let h = 0; for (let i = 0; i < pos.array.length; i += 7) h = (h * 31 + Math.round(pos.array[i] * 1e5)) | 0;
    const m = o.material || {}; out.push({tag, path: path.join('/'), verts: pos.count, hash: h, visible: o.visible,
      bbox: [b.min.toArray(), b.max.toArray()].map(v => v.map(x => Math.round(x * 1e4) / 1e4)),
      color: m.color ? m.color.getHexString() : null, rough: m.roughness, metal: m.metalness, emissive: m.emissive ? m.emissive.getHexString() : null}); }); };
  if (window.__sim) walk(window.__sim.robot.g, 'robot'); else walk(window.OAMR_MODEL.build(THREE, {}).root, 'exploded_build');
  return out; })()`;
(async () => {
  const out = {}; const b = await chromium.launch({ args: GL });
  for (const [k, url] of [['robot', 'http://localhost:8765/robot.html?render=1&w=640&h=360&fps=24&speed=4&cam=front#nomtx'], ['exploded', 'http://localhost:8765/exploded.html']]) {
    const p = await b.newPage({ viewport: { width: 640, height: 360 } }); p.setDefaultTimeout(900000);
    const errs = []; p.on('pageerror', e => errs.push(e.message)); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'domcontentloaded' });
    if (k === 'robot') { await p.waitForFunction(() => window.__frameReady === true); await p.evaluate(() => window.__renderAt(0, 'front', 'png')); }
    else await p.waitForFunction(() => !!window.OAMR_MODEL && !!window.THREE && document.querySelector('canvas'));
    out[k] = await p.evaluate(dump); out[k + '_errs'] = errs; await p.close();
  }
  await b.close(); fs.writeFileSync(process.argv[2], JSON.stringify(out)); console.log(Object.keys(out).map(k => k + ':' + out[k].length).join(' '));
})();
