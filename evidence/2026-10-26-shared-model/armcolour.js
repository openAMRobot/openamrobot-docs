// Both OpenArm 2.0 arms on robot.html: median sRGB of the same link on the left and the right arm, per preset
// and look. node armcolour.js <port> <look full|light> <mode camera|up> [mirrored] <preset over|side> [<preset> ...]
// Each link group of the two rigs is tagged with an id for the sampler (test only); pixels of faces turned to
// the camera, edges eroded; camera tiles, Frames and Labels off. mode camera: faces toward the camera
// (n . view > 0.35); mode up: faces turned up (n . z > 0.35, same orientation on both arms, so the store
// lighting reaches them alike) and toward the camera. 'arm' pools all links of an arm.
const { chromium } = require('playwright');
const fs = require('fs');
const sampler = fs.readFileSync(__dirname + '/colour_sampler.js', 'utf8');
(async () => {
  const [port, look, mode, ...rest] = process.argv.slice(2);
  const mirrored = rest[0] === 'mirrored', presets = mirrored ? rest.slice(1) : rest;  // mirrored: both arms in the model's mirrored rest pose (ARM_POSE), test only
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const out = {};
  for (const preset of presets) {
    const p = await b.newPage({viewport: {width: 1280, height: 800}}); p.setDefaultTimeout(900000);
    await p.goto(`http://localhost:${port}/robot.html?look=${look}`, {waitUntil: 'domcontentloaded'});
    await p.waitForFunction(() => window.__sim && window.__sim.robot);
    await p.evaluate(v => {
      if (window.__sim.S.tiles) document.getElementById('b-tiles').click();
      ['b-frames', 'b-labels'].forEach(id => { const e = document.getElementById(id); if (e.getAttribute('aria-pressed') === 'true') e.click(); });
      document.querySelector(`[data-view="${v}"]`).click();
    }, preset);
    if (mirrored) await p.evaluate(() => { const R = window.__sim.robot, P = window.OAMR_MODEL.ARM_POSE;
      R.applyArm('left', P.left); R.applyArm('right', P.right); R.setGrip('left', .6); R.setGrip('right', .6); });
    await p.waitForTimeout(20000);
    await p.addScriptTag({content: sampler});
    out[preset] = await p.evaluate(mode => {
      const S = window.__sim, R = S.robot, T = window.THREE, targets = {};
      ['left', 'right'].forEach(side => {
        const a = R.arm[side];
        [a.gBase, ...a.gLinks].forEach((g, i) => { g.userData.id = side + '_link' + i; (targets[side + '_link' + i] = [side + '_link' + i]); });
      });
      const arms = {left_arm: [0, 1, 2, 3, 4, 5, 6, 7].map(i => 'left_link' + i), right_arm: [0, 1, 2, 3, 4, 5, 6, 7].map(i => 'right_link' + i)};
      const dir = S.camera.getWorldDirection(new T.Vector3()).negate(), mats = new Set(), uuids = {left: new Set(), right: new Set()};
      ['left', 'right'].forEach(side => { const a = R.arm[side]; [a.gBase, ...a.gLinks, ...a.fingers.map(f => f.g)].forEach(g => g.traverse(o => { if (o.isMesh) { mats.add(o.material); uuids[side].add(o.material.type + ' emissive ' + (o.material.emissive ? o.material.emissive.getHexString() : '-')); } })); });
      const ident = {distinctArmMaterials: mats.size, left: [...uuids.left], right: [...uuids.right]};
      const r = window.__sampleColours({renderer: S.renderer, scene: S.scene, camera: S.camera, root: R.g, light: null, lightDir: mode === 'up' ? [0, 0, 1] : dir.toArray(),
        targets, renderBeauty: () => S.render()});
      Object.assign(r, window.__sampleColours({renderer: S.renderer, scene: S.scene, camera: S.camera, root: R.g, light: null,
        lightDir: mode === 'up' ? [0, 0, 1] : dir.toArray(), targets: arms, renderBeauty: () => S.render()}));
      ['left', 'right'].forEach(side => { const a = R.arm[side]; [a.gBase, ...a.gLinks].forEach(g => { delete g.userData.id; }); });
      r.__ident = ident;
      return r;
    }, mode);
    await p.close();
  }
  await b.close();
  for (const preset in out) console.log(JSON.stringify({look, preset, materials: out[preset].__ident}));
  const luma = c => .2126 * c[0] + .7152 * c[1] + .0722 * c[2];
  for (const preset in out) {
    const r = out[preset];
    for (const i of [0, 1, 2, 3, 4, 5, 6, 7, 'arm']) {
      const L = r[i === 'arm' ? 'left_arm' : 'left_link' + i], Rr = r[i === 'arm' ? 'right_arm' : 'right_link' + i];
      if (!L || !Rr || L.n < 150 || Rr.n < 150) continue;
      const dl = luma(L.rgb) / luma(Rr.rgb) - 1, dc = Math.max(...L.rgb.map((v, k) => Math.abs(v / Rr.rgb[k] - 1)));
      // chromaticity: each channel over the luma of its own arm (the tint, independent of how bright the light is)
      const ch = Math.max(...L.rgb.map((v, k) => Math.abs((v / luma(L.rgb)) / (Rr.rgb[k] / luma(Rr.rgb)) - 1)));
      console.log(JSON.stringify({look, mode, pose: mirrored ? 'mirrored' : 'page', preset, link: i, left: L.rgb, nLeft: L.n, right: Rr.rgb, nRight: Rr.n, lumaDiff: +(100 * dl).toFixed(1), maxChannel: +(100 * dc).toFixed(1), chroma: +(100 * ch).toFixed(1)}));
    }
  }
})();
