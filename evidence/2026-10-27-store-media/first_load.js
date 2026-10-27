// robot.html first load (Content-Length of every response until load plus 10 s, 1280 x 800, no scrolling), before and after;
// then the media section scrolled into view: thumbnails loaded. node first_load.js <after base> <before base>
const { chromium } = require('playwright');
(async () => {
  const [after, before] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const res = {};
  for (const [tag, base] of [['before', before], ['after', after]]) {
    const p = await b.newPage({viewport: {width: 1280, height: 800}}); p.setDefaultTimeout(600000);
    let bytes = 0; const media = [];
    p.on('response', r => { const n = +(r.headers()['content-length'] || 0); bytes += n; if (/media\//.test(r.url())) media.push(r.url().replace(base, '')); });
    await p.goto(base + 'robot.html', {waitUntil: 'load'});
    await p.waitForTimeout(10000);
    res[tag] = {bytes, media: media.slice()};
    if (tag === 'after') {
      await p.locator('#media').scrollIntoViewIfNeeded();
      await p.waitForFunction(() => [...document.querySelectorAll('#media img')].every(i => i.complete && i.naturalWidth > 0), null, {timeout: 120000}).catch(() => {});
      res.afterScroll = await p.evaluate(() => [...document.querySelectorAll('#media img')].map(i => ({src: !!i.getAttribute('src'), loaded: i.complete && i.naturalWidth > 0})));
      res.afterScrollMedia = media.slice();
    }
    await p.close();
  }
  res.growth = res.after.bytes - res.before.bytes;
  console.log(JSON.stringify(res, null, 1));
  await b.close();
})();
