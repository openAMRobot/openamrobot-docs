import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs';
const html = fs.readFileSync('out/web/index.html');
const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8790);
const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium', headless: false, args: ['--headless=new','--use-gl=angle','--use-angle=swiftshader','--enable-unsafe-swiftshader','--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: 1920, height: 1080 }, deviceScaleFactor: 1 });
p.on('console', m => console.log('C', m.text())); p.on('pageerror', e => console.log('ERR', e.message));
await p.route(u => !u.toString().startsWith('http://localhost'), r => r.abort());
await p.goto('http://localhost:8790/', { waitUntil: 'domcontentloaded', timeout: 300000 });
await p.waitForFunction(() => window.__sim, null, { timeout: 300000 });
await p.addStyleTag({ content: 'header.top,aside.panel,.hud,.legend,.play,.tiles{display:none!important} .app,.work{display:block!important;height:100vh!important;width:100vw!important} .stage{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important}' });
await p.evaluate(() => { const s = window.__sim; s.S.tiles = false; document.getElementById('b-order').click(); s.S.playing = false; });
await p.waitForTimeout(1500);
const shots = JSON.parse(process.argv[2]);
for (const sh of shots) {
  await p.evaluate(sh => {
    const s = window.__sim; s.S.playing = false; s.applyAt(sh.t);
    const g = s.robot.g.position;
    const W = ([a, b, h]) => [g.x + a, g.y + b, h]; console.log('pose', g.x.toFixed(2), g.y.toFixed(2), (s.robot.pose.yaw||0).toFixed(2));
    if (sh.view) s.setView(sh.view);
    else if (sh.abs) s.closeUp(...sh.abs);
    else s.closeUp(...W(sh.cam), ...W(sh.tgt));
    if (sh.fov) { s.camera.fov = sh.fov; s.camera.updateProjectionMatrix(); }
    s.render();
  }, sh);
  await p.waitForTimeout(400);
  await p.evaluate(() => window.__sim.render());
  await p.screenshot({ path: `out/pics/${sh.name}.png`, timeout: 300000 });
  console.log('shot', sh.name);
}
await b.close(); srv.close();
