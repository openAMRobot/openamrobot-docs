// Both pages with their defaults at 375 and 1280 px: console errors and warnings, failed requests, horizontal
// scroll, and the robot.html defaults (view preset, Frames, Labels, High quality, look). Page screenshot after 25 s.
const { chromium } = require('playwright');
(async () => {
  const port = process.argv[2], b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const res = {};
  for (const page of ['robot.html', 'exploded.html']) for (const w of [1280, 375]) {
    const p = await b.newPage({viewport: {width: w, height: w > 400 ? 800 : 812}}); p.setDefaultTimeout(600000);
    const msgs = [];
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(m.type() + ': ' + m.text()); });
    p.on('pageerror', e => msgs.push('pageerror: ' + e.message)); p.on('requestfailed', r => msgs.push('requestfailed: ' + r.url()));
    await p.goto(`http://localhost:${port}/${page}`, {waitUntil: 'domcontentloaded'});
    await p.waitForTimeout(25000);
    const st = await p.evaluate(() => {
      const on = id => { const e = document.getElementById(id); return e ? e.classList.contains('on') || e.getAttribute('aria-pressed') === 'true' : null; };
      return {view: [...document.querySelectorAll('[data-view].on')].map(e => e.dataset.view), frames: on('b-frames'), labels: on('b-labels'),
        hq: window.__sim ? window.__sim.S.hq : on('b-hq'), light: window.OAMR_LOOK.isLight(), scrollWidth: document.documentElement.scrollWidth};
    });
    await p.screenshot({path: `${process.argv[3] || '.'}/${page.replace('.html', '')}_${w}_defaults.png`, timeout: 600000});
    res[page + '@' + w] = Object.assign(st, {msgs});
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1)); await b.close();
})();
