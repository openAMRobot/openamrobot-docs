const { chromium } = require('playwright');
(async () => {
  const port = process.argv[2];
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const res = {};
  for (const [page, w] of [['exploded.html', 1280], ['exploded.html', 375], ['robot.html', 1280], ['robot.html', 375]]) {
    const p = await b.newPage({viewport: {width: w, height: 800}}); p.setDefaultTimeout(600000);
    const msgs = []; p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(m.text()); }); p.on('pageerror', e => msgs.push(e.message));
    await p.goto(`http://localhost:${port}/${page}`, {waitUntil: 'domcontentloaded'});
    await p.waitForFunction(() => window.OAMR_LOOK && window.OAMR_LOOK.lastProbeMs !== undefined, null, {timeout: 600000});
    const st = await p.evaluate(() => ({probeMs: +window.OAMR_LOOK.lastProbeMs.toFixed(1), light: window.OAMR_LOOK.isLight(),
      hq: (document.getElementById('b-hq') || document.getElementById('b-q')).outerHTML.slice(0, 60), hqOn: window.__sim ? window.__sim.S.hq : document.getElementById('b-hq').getAttribute('aria-pressed') === 'true', sw: document.documentElement.scrollWidth}));
    if (page === 'exploded.html' && w === 1280) {  // toggle back to full and to light again
      await p.click('#b-hq'); st.afterClick1 = await p.evaluate(() => [window.OAMR_LOOK.isLight(), document.getElementById('b-hq').getAttribute('aria-pressed')]);
    }
    if (page === 'robot.html' && w === 1280) {
      await p.click('#b-q'); st.afterClick1 = await p.evaluate(() => [window.OAMR_LOOK.isLight(), window.__sim.S.hq]);
    }
    await p.waitForTimeout(3000);
    res[page + '@' + w] = Object.assign(st, {msgs});
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1)); await b.close();
})();
