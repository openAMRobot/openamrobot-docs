// Colour samples of the lit side panel, cover and arm profile against finish.json, for a list of look
// parameter sets. node colour.js <port> exploded|robot '<json list of {exposure, key, envDielectric, envMetal}>'
// exploded: exploded.html render mode, frame 0 (assembled), 1280 x 720; robot: robot.html?look=full, Side
// preset (or the preset named by the 4th argument), 1280 x 800, camera tiles off. An empty set measures the page as it is.
const { chromium } = require('playwright');
const fs = require('fs');
const sampler = fs.readFileSync(__dirname + '/colour_sampler.js', 'utf8');
const TARGETS = {side_panel: ['side_panel_left', 'side_panel_right'], cover: ['cover'], arm_profile: ['arm_profile']};
const REF = {side_panel: '#CBD0CC', cover: '#383E42', arm_profile: '#383E42'};
const hex = h => [1, 3, 5].map(i => parseInt(h.slice(i, i + 2), 16));
const luma = c => .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
(async () => {
  const [port, page, sets, preset] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: 1280, height: 800}});
  p.setDefaultTimeout(600000);
  await p.addInitScript(() => { let T; Object.defineProperty(window, 'THREE', {configurable: true, get() { return T; }, set(v) {
    const W = v.WebGLRenderer; v.WebGLRenderer = function (a) { const r = new W(a), o = r.render; r.render = function (s, c) { window.__last = [r, s, c]; o.call(r, s, c); }; return r; }; T = v; }}); });
  if (page === 'exploded') {
    await p.goto(`http://localhost:${port}/exploded.html?render=1&w=1280&h=720&frame=0`);
    await p.waitForFunction(() => window.__renderFrame);
    await p.evaluate(() => window.__renderFrame(0));
  } else {
    await p.goto(`http://localhost:${port}/robot.html?look=full`, {waitUntil: 'domcontentloaded'});
    await p.waitForFunction(() => window.__sim && window.__sim.robot);
    await p.evaluate(() => { const t = document.getElementById('b-tiles'); if (window.__sim.S.tiles) t.click(); });
    await p.click(`[data-view="${preset || 'side'}"]`);
    await p.waitForTimeout(8000);
  }
  await p.addScriptTag({content: sampler});
  const res = await p.evaluate(([page, sets, TARGETS]) => {
    const T = window.THREE, out = [];
    let o;
    if (page === 'exploded') {
      const [r, s, c] = window.__last, root = s.getObjectByName('OpenAMRobot');
      let key = null; s.traverse(x => { if (x.isDirectionalLight && (!key || x.intensity > key.intensity)) key = x; });  // the key light
      o = {renderer: r, scene: s, camera: c, root, light: key, lightDir: [2, -2, 1.85], targets: TARGETS, renderBeauty: () => r.render(s, c)};
    } else {
      const S = window.__sim;
      o = {renderer: S.renderer, scene: S.scene, camera: S.camera, root: S.robot.g, light: S.key, targets: TARGETS, renderBeauty: () => S.render()};
    }
    for (const p of sets) {
      if (p.exposure !== undefined) o.renderer.toneMappingExposure = p.exposure;
      if (p.key !== undefined && page === 'exploded') o.light.intensity = p.key;
      if (p.envDielectric !== undefined) window.OAMR_LOOK.robotEnv(o.root, p);
      out.push({params: p, samples: window.__sampleColours(o)});
    }
    return out;
  }, [page, JSON.parse(sets || '[{}]'), TARGETS]);
  await b.close();
  for (const r of res) {
    const row = {params: r.params};
    let worst = 0;
    for (const k in REF) {
      const s = r.samples[k], ref = hex(REF[k]);
      if (!s.rgb[0] && s.rgb[0] !== 0) { row[k] = 'no pixels'; worst = 9; continue; }
      const dl = luma(s.rgb) / luma(ref) - 1, dc = Math.max(...s.rgb.map((v, i) => Math.abs(v / ref[i] - 1)));
      worst = Math.max(worst, Math.abs(dl));
      row[k] = {n: s.n, rgb: s.rgb, ref: REF[k], luma: +(100 * dl).toFixed(1), maxChannel: +(100 * dc).toFixed(1)};
    }
    row.worstLuma = +(100 * worst).toFixed(1);
    console.log(JSON.stringify(row));
  }
})();
