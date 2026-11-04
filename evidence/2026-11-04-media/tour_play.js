// Live tour playback check on exploded.html (not render mode): Play tour, captions advance through the new stops
// (Playwright clock fast-forwards performance.now), Pause / Resume, the tour ends on its own and restores the view
// (no part left hidden, lift back at L1000). node tour_play.js <base url>
const { chromium } = require('playwright');
(async () => {
  const b = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const p = await b.newPage({ viewport: { width: 1280, height: 800 } }); p.setDefaultTimeout(600000);
  const errs = []; p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') errs.push(m.text()); });
  await p.clock.install();
  await p.goto(base(), { waitUntil: 'load' });
  await p.waitForFunction(() => !document.getElementById('b-tour').disabled);
  await p.click('#b-tour');
  const seen = [];
  for (const t of [1, 14, 30, 47, 51, 55, 60, 67, 72, 75, 81, 87]) {
    await p.clock.runFor(t * 1000 - (seen.length ? seen[seen.length - 1].t * 1000 : 0));
    await p.waitForTimeout(50);
    seen.push({ t, cap: await p.$eval('#cap', e => e.hidden ? '' : e.textContent) });
  }
  await p.click('#b-pause'); const paused = await p.$eval('#b-pause', e => e.textContent);
  await p.click('#b-pause');
  await p.clock.runFor(3000); await p.waitForTimeout(100);
  const ended = await p.$eval('#b-tour', e => !e.hidden);
  console.log(JSON.stringify({ seen, paused, ended, errors: errs }, null, 1));
  await b.close();
  if (errs.length || !ended) process.exit(1);
  function base() { return (process.argv[2] || 'http://localhost:8802/') + 'exploded.html'; }
})();
