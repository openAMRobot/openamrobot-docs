// Page checks for this change. node page_checks.js <after base> <before base> <out dir>
// 1. both pages at 375 and 1280 px with their defaults: console errors and warnings, failed requests, horizontal
//    scroll, robot.html defaults (view preset, Frames, Labels, High quality);
// 2. first load of robot.html: bytes of every response until load plus 10 s, no scrolling, before and after;
// 3. robot.html Overview preset and a close view of the base, before and after (?look=full);
// 4. the realtime "Record order video" button starts a recording and stops it again.
const { chromium } = require('playwright');
const fs = require('fs');
(async () => {
  const [after, before, out] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const res = {pages: {}, firstLoad: {}, record: null};
  const page = async (w, h) => { const p = await b.newPage({viewport: {width: w, height: h}, deviceScaleFactor: 1}); p.setDefaultTimeout(900000); return p; };
  for (const name of ['robot.html', 'exploded.html']) for (const w of [1280, 375]) {
    const p = await page(w, w > 400 ? 800 : 812), msgs = [];
    p.on('console', m => { if (m.type() === 'error' || m.type() === 'warning') msgs.push(m.type() + ': ' + m.text()); });
    p.on('pageerror', e => msgs.push('pageerror: ' + e.message)); p.on('requestfailed', r => msgs.push('requestfailed: ' + r.url()));
    await p.goto(after + name, {waitUntil: 'load'});
    await p.waitForTimeout(20000);
    res.pages[name + '@' + w] = Object.assign(await p.evaluate(() => {
      const on = id => { const e = document.getElementById(id); return e ? e.classList.contains('on') || e.getAttribute('aria-pressed') === 'true' : null; };
      return {view: [...document.querySelectorAll('[data-view].on')].map(e => e.dataset.view), frames: on('b-frames'), labels: on('b-labels'),
        hq: window.__sim ? window.__sim.S.hq : null, scrollWidth: document.documentElement.scrollWidth, innerWidth: innerWidth};
    }), {msgs});
    if (name === 'robot.html') await p.locator('#media').screenshot({path: `${out}/robot_${w}_media_section.png`});
    await p.close();
  }
  for (const [tag, base] of [['before', before], ['after', after]]) {
    const p = await page(1280, 800); let bytes = 0; const files = {};
    p.on('response', async r => { try { const n = (await r.body()).length; bytes += n; files[r.url().replace(base, '')] = n; } catch (e) {} });
    await p.goto(base + 'robot.html', {waitUntil: 'load'});
    await p.waitForTimeout(10000);
    res.firstLoad[tag] = {bytes, media: Object.keys(files).filter(f => /media\//.test(f))};
    await p.close();
  }
  for (const [tag, base] of [['before', before], ['after', after]]) {
    const p = await page(1280, 800);
    await p.goto(base + 'robot.html?look=full#nomtx', {waitUntil: 'domcontentloaded'});
    await p.waitForFunction(() => window.__sim && window.__sim.robot);
    await p.evaluate(() => { if (window.__sim.S.tiles) document.getElementById('b-tiles').click(); document.querySelector('[data-view="over"]').click(); });
    await p.waitForTimeout(15000);
    await p.locator('#stage').screenshot({path: `${out}/robot_overview_${tag}.png`});
    await p.evaluate(() => { const g = window.__sim.robot.g.position; window.__sim.closeUp(g.x - 1.1, g.y - .75, .75, g.x - .05, g.y, .3); });
    await p.waitForTimeout(15000);
    await p.locator('#stage').screenshot({path: `${out}/robot_base_close_${tag}.png`});
    await p.close();
  }
  {
    const p = await page(1280, 800);
    await p.goto(after + 'robot.html', {waitUntil: 'domcontentloaded'});
    await p.waitForFunction(() => window.__sim && window.__sim.robot);
    await p.click('#b-rec'); await p.waitForTimeout(3000);
    const started = await p.evaluate(() => [document.getElementById('b-rec').textContent, document.getElementById('rec-msg').textContent]);
    await p.click('#b-rec'); await p.waitForTimeout(4000);
    const stopped = await p.evaluate(() => [document.getElementById('b-rec').textContent, document.getElementById('rec-msg').textContent]);
    res.record = {started, stopped};
    await p.close();
  }
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
