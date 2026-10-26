const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: 1280, height: 800}}); p.setDefaultTimeout(600000);
  await p.addInitScript(() => { let T; Object.defineProperty(window, 'THREE', {configurable: true, get() { return T; }, set(v) {
    const W = v.WebGLRenderer; v.WebGLRenderer = function (a) { const r = new W(a), o = r.render; r.render = function (s, c) { window.__last = [r, s, c]; o.call(r, s, c); }; return r; }; T = v; }}); });
  await p.goto(`http://localhost:${process.argv[2]}/exploded.html?render=1&w=1280&h=800&frame=0`);
  await p.waitForFunction(() => window.__renderFrame);
  await p.evaluate(() => window.__renderFrame(0));
  const res = await p.evaluate(() => {
    const [r, s, c] = window.__last, gl = r.getContext();
    const time = () => { for (let i = 0; i < 3; i++) r.render(s, c); const t = []; for (let i = 0; i < 12; i++) { const t0 = performance.now(); r.render(s, c); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); t.push(performance.now() - t0); } t.sort((a, b) => a - b); return +t[6].toFixed(0); };
    const recompile = () => s.traverse(o => { if (o.material) o.material.needsUpdate = true; });
    const out = {all: time()};
    r.shadowMap.type = 1; recompile(); r.shadowMap.needsUpdate = true; out.pcf = time();
    const rcv = []; s.traverse(o => { if (o.isMesh && o.receiveShadow && !(o.material && o.material.isShadowMaterial)) { rcv.push(o); o.receiveShadow = false; o.material.needsUpdate = true; } });
    out.pcfNoRobotReceive = time();
    r.shadowMap.enabled = false; recompile(); out.noShadow = time();
    const env = s.environment; s.environment = null; recompile(); out.noShadowNoEnv = time();
    s.traverse(o => { if (o.isMesh && (o.material.normalMap || o.material.roughnessMap || o.material.clearcoat)) { o.material.normalMap = o.material.roughnessMap = null; if (o.material.clearcoat) o.material.clearcoat = 0; o.material.needsUpdate = true; } });
    out.bare = time();
    return out;
  });
  console.log(JSON.stringify(res)); await b.close();
})();
