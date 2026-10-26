// exploded.html render mode: frame N as PNG (the page's own deterministic render path)
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [port, w, h, outPrefix, ...frames] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const p = await b.newPage({viewport: {width: +w, height: +h}});
  const msgs = [];
  p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(m.text()); });
  p.on('pageerror', e => msgs.push('pageerror: ' + e.message));
  await p.goto(`http://localhost:${port}/exploded.html?render=1&w=${w}&h=${h}&frame=0`, {timeout: 120000});
  await p.waitForFunction(() => window.__renderFrame, null, {timeout: 120000});
  for (const f of frames) {
    const url = await p.evaluate(n => window.__renderFrame(n), +f);
    fs.writeFileSync(`${outPrefix}_${f}.png`, Buffer.from(url.split(',')[1], 'base64'));
  }
  console.log(JSON.stringify(msgs));
  await b.close();
})();
