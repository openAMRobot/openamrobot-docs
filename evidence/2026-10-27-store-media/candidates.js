const { chromium } = require('playwright'); const fs = require('fs');
(async () => {
  const [w, h, list, out] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: +w, height: +h}, deviceScaleFactor: 1}); p.setDefaultTimeout(900000);
  await p.goto(`http://localhost:8802/robot.html?render=1&w=${w}&h=${h}&fps=24&speed=7.5#nomtx`, {waitUntil: 'domcontentloaded'});
  await p.waitForFunction(() => window.__frameReady === true);
  for (const [t, cam] of JSON.parse(list)) {
    const u = await p.evaluate(([t, c]) => window.__renderAt(t, c, 'jpeg'), [t, cam]);
    fs.writeFileSync(`${out}_${cam}_${t}.jpg`, Buffer.from(u.split(',')[1], 'base64'));
  }
  await b.close();
})();
