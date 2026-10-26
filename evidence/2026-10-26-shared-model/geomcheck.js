// Geometry identity: mesh dump and silhouettes, before (port A) and after (port B).
// exploded: geomtest.html (built as exploded.html does); robot: robot.html in page (window.__sim.robot.g).
const { chromium } = require('playwright');
const fs = require('fs');
const S = __dirname;
const helpers = fs.readFileSync(S + '/geomtest.html', 'utf8').split('</script>')[4].replace(/^[\s\S]*?(function hashArr)/, '$1');
const DIRS = {front: [1.0, -0.82, 0.62], rear: [-1.0, 0.82, 0.62]};
async function grab(b, url, robotPage) {
  const p = await b.newPage({viewport: {width: 1280, height: 900}});
  const errs = [];
  p.on('pageerror', e => errs.push(e.message));
  await p.goto(url, {timeout: 180000, waitUntil: 'domcontentloaded'});
  if (robotPage) {
    await p.waitForFunction(() => window.__sim && window.__sim.robot, null, {timeout: 180000});
    await p.addScriptTag({content: helpers});
    await p.evaluate(() => {
      const g = window.__sim.robot.g; window.__root = g;
      window.__sim.renderer.setAnimationLoop(null);
      g.userData.save = [g.position.clone(), g.rotation.clone()]; g.position.set(0, 0, 0); g.rotation.set(0, 0, 0); g.updateMatrixWorld(true);
      window.__dump = () => dumpMeshes(g); window.__sil = d => silhouette(window.__sim.THREE, g, d);
    });
  } else await p.waitForFunction(() => window.__dump, null, {timeout: 60000});
  const dump = await p.evaluate(() => window.__dump());
  const sil = {};
  for (const k in DIRS) sil[k] = await p.evaluate(d => window.__sil(d), DIRS[k]);
  await p.close();
  return {dump, sil, errs};
}
(async () => {
  const [pa, pb, page, out] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const robotPage = page === 'robot.html';
  const A = await grab(b, `http://localhost:${pa}/${page}`, robotPage), B = await grab(b, `http://localhost:${pb}/${page}`, robotPage);
  await b.close();
  const key = m => m.pos + '|' + m.n + '|' + m.idx;
  // match meshes by geometry hash and nearest world matrix
  const pool = B.dump.slice(), pairs = [], unmatchedA = [];
  for (const m of A.dump) {
    let best = -1, bd = 1e9;
    pool.forEach((q, i) => { if (key(q) !== key(m)) return; const d = Math.max(...m.mw.map((v, j) => Math.abs(v - q.mw[j]))); if (d < bd) { bd = d; best = i; } });
    if (best < 0 || bd > 1e-6) unmatchedA.push(m); else { pairs.push([m, pool[best], bd]); pool.splice(best, 1); }
  }
  const maxd = Math.max(0, ...pairs.map(p => p[2]));
  const mat = pairs.filter(([a, c]) => a.color !== c.color || a.roughness !== c.roughness || a.metalness !== c.metalness || a.opacity !== c.opacity || a.transparent !== c.transparent || a.type !== c.type)
    .map(([a, c]) => ({part: a.part, before: [a.type, a.color, a.roughness, a.metalness, a.opacity], after: [c.type, c.color, +c.roughness.toFixed(4), c.metalness, c.opacity]}));
  const opacityChanged = pairs.filter(([a, c]) => a.opacity !== c.opacity || a.transparent !== c.transparent || a.visible !== c.visible).length;
  const res = {page, meshesBefore: A.dump.length, meshesAfter: B.dump.length, matched: pairs.length, unmatchedBefore: unmatchedA.map(m => m.part), unmatchedAfter: pool.map(m => m.part),
    maxMatrixDiff: maxd, opacityOrVisibilityChanged: opacityChanged, uvAdded: pairs.filter(([a, c]) => !a.uv && c.uv).length, materialChanges: mat.length, errs: [A.errs, B.errs], sil: {}};
  for (const k in DIRS) {
    const ma = A.sil[k].mask, mb = B.sil[k].mask; let diff = 0;
    for (let i = 0; i < ma.length; i++) if (ma[i] !== mb[i]) diff++;
    res.sil[k] = {litBefore: A.sil[k].lit, litAfter: B.sil[k].lit, differing: diff};
    fs.writeFileSync(`${out}_${k}_before.png`, Buffer.from(A.sil[k].png.split(',')[1], 'base64'));
    fs.writeFileSync(`${out}_${k}_after.png`, Buffer.from(B.sil[k].png.split(',')[1], 'base64'));
  }
  fs.writeFileSync(`${out}_materials.json`, JSON.stringify(mat, null, 1));
  console.log(JSON.stringify(res, null, 1));
})();
