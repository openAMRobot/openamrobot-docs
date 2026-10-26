const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: 1280, height: 720}}); p.setDefaultTimeout(600000);
  await p.addInitScript(() => { let T; Object.defineProperty(window, 'THREE', {configurable: true, get() { return T; }, set(v) {
    const W = v.WebGLRenderer; v.WebGLRenderer = function (a) { const r = new W(a), o = r.render; r.render = function (s, c) { window.__last = [r, s, c]; o.call(r, s, c); }; return r; }; T = v; }}); });
  await p.goto(`http://localhost:${process.argv[2]}/exploded.html?render=1&w=1280&h=720&frame=0`);
  await p.waitForFunction(() => window.__renderKey);
  const info = await p.evaluate(() => { const s = window.__last[1], out = []; s.traverse(o => { if (o.isMesh && o.name === 'cover') { const m = o.material; out.push({type: m.type, rough: m.roughness, metal: m.metalness, env: m.envMapIntensity, nscale: m.normalScale && m.normalScale.x, rmap: !!m.roughnessMap}); } }); return out; });
  console.log(JSON.stringify(info));
  const key = {frame: 'base', az: 140, el: 18, min_r: .3, zoom: .9};
  const variants = {spec05: .5, spec03: .3, spec02: .2};
  for (const v in variants) {
    const url = await p.evaluate(([v, key]) => {
      const s = window.__last[1];
      if (!window.__orig) { window.__orig = []; s.traverse(o => { if (o.isMesh && /^cover/.test(o.name)) window.__orig.push([o, o.material.clone()]); }); }
      window.__orig.forEach(([o, m0]) => { o.material = o.userData.cur || (o.userData.cur = o.material); o.material.copy(m0); o.material.needsUpdate = true; });
      const fns = {}; window.__spec = {spec05: .5, spec03: .3, spec02: .2}[v];
      window.__orig.forEach(([o]) => { if (fns[v]) fns[v](o.material); else { const m0 = o.material, T = window.THREE; o.userData.phys = o.userData.phys && o.userData.phys.specularIntensity === window.__spec ? o.userData.phys : null; if (!o.userData.phys) o.userData.phys = new T.MeshPhysicalMaterial({color: m0.color, roughness: .62, metalness: 0, normalMap: m0.normalMap, normalScale: new T.Vector2(.06, .06), envMapIntensity: m0.envMapIntensity, specularIntensity: +(window.__spec || .5)}); o.material = o.userData.phys; } });
      return window.__renderKey(key);
    }, [v, key]);
    fs.writeFileSync(`${process.argv[3]}_${v}.png`, Buffer.from(url.split(',')[1], 'base64'));
  }
  await b.close();
})();
