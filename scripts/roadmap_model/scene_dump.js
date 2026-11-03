// Dump the world bounding box of every part group of the shared roadmap model (as the pages build it) for
// the self-check of scripts/roadmap_model/analyse.py: the Python scene must equal the page scene.
//   node scripts/roadmap_model/scene_dump.js [base URL, default http://localhost:8765/] [out json]
// Serve docs/assets/roadmap first: (cd docs/assets/roadmap && python3 -m http.server 8765)
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = process.argv[2] || 'http://localhost:8765/', OUT = process.argv[3] || 'scene_dump.json';
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.goto(BASE + 'exploded.html?render=1', {waitUntil: 'load'});
  await p.waitForTimeout(3000);
  const out = await p.evaluate(() => {
    const T = window.THREE, M = window.OAMR_MODEL, R = M.build(T, {headPitch: 30});
    R.root.updateMatrixWorld(true);
    const res = {};
    for (const id in R.parts) {
      const box = new T.Box3();
      R.parts[id].forEach(g => box.expandByObject(g));
      if (!box.isEmpty()) res[id] = [box.min.toArray(), box.max.toArray()];
    }
    // arm link origins (home pose of the page, M.ARM_POSE) for the FK check
    const arms = {};
    ['left', 'right'].forEach(s => { arms[s] = R.arms[s].gLinks.map(g => { const v = new T.Vector3(); v.setFromMatrixPosition(g.matrixWorld); return v.toArray(); }); });
    return {parts: res, arms, pose: M.ARM_POSE};
  });
  out.errors = errs;
  fs.writeFileSync(OUT, JSON.stringify(out));
  console.log('parts', Object.keys(out.parts).length, 'errors', errs.length);
  await b.close();
})();
