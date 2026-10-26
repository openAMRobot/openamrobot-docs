// lift column faces (front +x, right side -y, left side +y) under satin variants, exploded frame 0 pose and rear pose
const { chromium } = require('playwright');
const fs = require('fs');
const sampler = fs.readFileSync(process.argv[3] + '/colour_sampler.js', 'utf8');
(async () => {
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: 1280, height: 720}}); p.setDefaultTimeout(600000);
  await p.addInitScript(() => { let T; Object.defineProperty(window, 'THREE', {configurable: true, get() { return T; }, set(v) {
    const W = v.WebGLRenderer; v.WebGLRenderer = function (a) { const r = new W(a), o = r.render; r.render = function (s, c) { window.__last = [r, s, c]; o.call(r, s, c); }; return r; }; T = v; }}); });
  await p.goto(`http://localhost:${process.argv[2]}/exploded.html?render=1&w=1280&h=720&frame=0`);
  await p.waitForFunction(() => window.__renderKey);
  await p.addScriptTag({content: sampler});
  const out = await p.evaluate(variants => {
    const [r, s] = window.__last, root = s.getObjectByName('OpenAMRobot'), res = [];
    const mats = []; root.traverse(o => { if (o.isMesh && o.material.userData.cls === 'satin_aluminium') mats.push(o.material); });
    for (const v of variants) {
      mats.forEach(m => { m.roughness = v.r; m.metalness = v.m; if (v.env !== undefined) m.envMapIntensity = v.env; });
      const row = {v};
      for (const [pose, faces] of [[{frame: 'robot', az: -40, el: 16, zoom: .82}, {front: [1, 0, 0], side: [0, -1, 0]}], [{frame: 'robot', az: 140, el: 18, zoom: .82}, {rear: [-1, 0, 0], left: [0, 1, 0]}]]) {
        window.__renderKey(pose); const c = window.__last[2];
        for (const f in faces) {
          const q = window.__sampleColours({renderer: r, scene: s, camera: c, root, light: null, lightDir: faces[f], targets: {col: ['lift_column']}, renderBeauty: () => r.render(s, c)});
          row[f] = q.col.rgb[1];
        }
      }
      res.push(row);
    }
    return res;
  }, JSON.parse(process.argv[4]));
  out.forEach(o => console.log(JSON.stringify(o)));
  await b.close();
})();
