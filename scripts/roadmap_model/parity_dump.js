// Dump the roadmap model as the pages build it, for scripts/roadmap_model/parity.py (convergence phase 1).
// For each configuration (bp000 L1000 / L1175 / L1350, bp050 L1000; head pitch 30 deg; arms at all joints 0 and
// grip 0, the zero pose of the combined URDF): per part id and per part group, the world bounding box and the
// world quaternion of the group; per arm, the world matrix of every link frame (base, links 1 to 7, fingers).
//   node scripts/roadmap_model/parity_dump.js [base URL, default http://localhost:8765/] [out json]
// Serve docs/assets/roadmap first: (cd docs/assets/roadmap && python3 -m http.server 8765)
const { chromium } = require('playwright');
const fs = require('fs');
const BASE = process.argv[2] || 'http://localhost:8765/', OUT = process.argv[3] || 'parity_dump.json';
const CONFIGS = [['bp000', 'L1000', 0], ['bp000', 'L1175', .175], ['bp000', 'L1350', .35], ['bp050', 'L1000', 0]];
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  const p = await b.newPage();
  const errs = [];
  p.on('pageerror', e => errs.push(String(e)));
  await p.goto(BASE + 'exploded.html?render=1', {waitUntil: 'load'});
  await p.waitForTimeout(3000);
  const out = await p.evaluate((CONFIGS) => {
    const T = window.THREE, M = window.OAMR_MODEL, D = M.DIMS, res = {};
    CONFIGS.forEach(([bp, stop, tr]) => {
      const R = M.build(T, {headPitch: 30, bp: bp});
      R.mov.position.z += tr;
      const sh = D.STOPS.L1000 + tr;
      ['left', 'right'].forEach(s => M.poseArm(T, R.arms[s], s, [0, 0, 0, 0, 0, 0, 0], 0, sh, D.BP[bp]));
      R.root.updateMatrixWorld(true);
      const parts = {};
      for (const id in R.parts) {
        parts[id] = R.parts[id].map(g => {
          const box = new T.Box3().setFromObject(g), q = new T.Quaternion(), v = new T.Vector3(), sc = new T.Vector3();
          g.matrixWorld.decompose(v, q, sc);
          return box.isEmpty() ? null : {min: box.min.toArray(), max: box.max.toArray(), q: q.toArray()};
        });
      }
      const arms = {};
      ['left', 'right'].forEach(s => {
        const rig = R.arms[s];
        const m = g => g.matrixWorld.elements.slice();
        arms[s] = {base: m(rig.gBase), links: rig.gLinks.map(m), fingers: rig.fingers.map(f => m(f.g))};
      });
      res[bp + ' ' + stop] = {parts, arms};
    });
    return res;
  }, CONFIGS);
  fs.writeFileSync(OUT, JSON.stringify({configs: out, errors: errs}));
  console.log('configs', Object.keys(out).length, 'errors', errs.length);
  await b.close();
})();
