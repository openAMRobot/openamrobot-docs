// Tour posters and the no-WebGL image of exploded.html from its render mode (full look):
// posters: frame 780 (26 s, opened base) composited with labels and caption, 1920 x 1080 and 1080 x 1350;
// static: the raw 3D canvas of frame 0 at 960 x 720 (no labels, no caption). Palette reduction is done after.
// node exploded_stills.js <base url> <out dir>
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [base, out] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  for (const [w, h, name, frame, raw] of [[1920, 1080, 'openamrobot-2-tour-1080p-poster.png', 780, false], [1080, 1350, 'openamrobot-2-tour-1080x1350-poster.png', 780, false], [960, 720, 'exploded-static.png', 0, true]]) {
    const p = await b.newPage({viewport: {width: w, height: h}, deviceScaleFactor: 1}); p.setDefaultTimeout(900000);
    await p.goto(`${base}exploded.html?render=1&frame=0&w=${w}&h=${h}`, {waitUntil: 'load'});
    await p.waitForFunction(() => window.__frameReady === true);
    const url = await p.evaluate(([n, raw]) => {
      const c = window.__renderFrame(n);
      return raw ? document.querySelector('#stage canvas').toDataURL('image/png') : c;  // same task as the render
    }, [frame, raw]);
    fs.writeFileSync(`${out}/${name}`, Buffer.from(url.split(',')[1], 'base64'));
    await p.close();
  }
  await b.close();
})();
