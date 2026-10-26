// Page screenshots: robot.html presets and 375 px pages; console errors, warnings, failed requests, horizontal scroll.
const { chromium } = require('playwright');
(async () => {
  const [port, tag] = process.argv.slice(2), q = process.argv[5] ? '?' + process.argv[5] : '';  // e.g. look=full
  const b = await chromium.launch(Object.assign({}, {args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']}));
  const report = {};
  const run = async (page, w, h, fn) => {
    const p = await b.newPage({viewport: {width: w, height: h}});
    const msgs = [];
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(m.type() + ': ' + m.text()); });
    p.on('pageerror', e => msgs.push('pageerror: ' + e.message));
    p.on('requestfailed', r => msgs.push('requestfailed: ' + r.url()));
    p.setDefaultTimeout(300000);
    await p.goto(`http://localhost:${port}/${page}${q}`, {waitUntil: 'domcontentloaded'});
    await fn(p);
    const sw = await p.evaluate(() => [document.documentElement.scrollWidth, innerWidth]);
    report[page + '@' + w] = {msgs, scrollWidth: sw[0], viewport: sw[1]};
    await p.close();
  };
  const ready = p => p.waitForFunction(() => window.__sim && window.__sim.robot);
  await run('robot.html', 1280, 800, async p => {
    await ready(p);
    for (const v of ['over', 'side']) {
      await p.click(`[data-view="${v}"]`);
      await p.waitForTimeout(12000);
      await p.locator('#stage').screenshot({path: `robot_1280_${v === 'over' ? 'overview' : v}_${tag}.png`});
    }
  });
  if (process.argv[4] === 'presets') { console.log(JSON.stringify(report)); await b.close(); return; }
  await run('robot.html', 375, 812, async p => { await ready(p); await p.waitForTimeout(12000); await p.screenshot({path: `robot_375_${tag}.png`}); });
  await run('exploded.html', 1280, 800, async p => { await p.waitForTimeout(10000); await p.screenshot({path: `exploded_1280_page_${tag}.png`}); });
  await run('exploded.html', 375, 812, async p => { await p.waitForTimeout(10000); await p.screenshot({path: `exploded_375_${tag}.png`}); });
  console.log(JSON.stringify(report, null, 1));
  await b.close();
})();
