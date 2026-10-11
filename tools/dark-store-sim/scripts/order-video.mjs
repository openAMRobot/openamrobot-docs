// Renders the order run as video frames: node video.mjs <mode:preview|full> [startFrame]
import { chromium } from 'playwright-core';
import http from 'http'; import fs from 'fs';
const MODE = process.argv[2] || 'preview', START = +(process.argv[3] || 0);
const FPS = 25, SPEED = 8, INTRO = 2.6, OUTRO = 3.4, W = 1280, H = 720;
const OUT = MODE === 'full' ? 'out/vid/frames' : 'out/vid/preview';
fs.mkdirSync(OUT, { recursive: true });
const html = fs.readFileSync('out/web/index.html');
const srv = http.createServer((q, r) => { r.writeHead(200, { 'content-type': 'text/html' }); r.end(html); }).listen(8794);
const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium', headless: false, args: ['--headless=new', '--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
p.on('pageerror', e => console.log('ERR', e.message));
await p.route(u => !u.toString().startsWith('http://localhost'), r => r.abort());
await p.goto('http://localhost:8794/', { waitUntil: 'domcontentloaded', timeout: 300000 });
await p.waitForFunction(() => window.__sim, null, { timeout: 300000 });
await p.addStyleTag({ content: 'header.top,aside.panel,.hud,.legend,.play,.tiles{display:none!important} .app,.work{display:block!important;height:100vh!important;width:100vw!important} .stage{position:fixed!important;inset:0!important;width:100vw!important;height:100vh!important}' });
const T = await p.evaluate(({ W, H }) => {
  const s = window.__sim; s.S.tiles = false; document.getElementById('b-order').click(); s.S.playing = false;
  if (s.S.hq) document.getElementById('b-q').click();
  s.key.shadow.mapSize.set(2048, 2048); if (s.key.shadow.map) { s.key.shadow.map.dispose(); s.key.shadow.map = null; }
  s.scene.traverse(o => { if (o.isRectAreaLight) o.visible = false; if (o.isHemisphereLight) o.intensity = 1.1; });
  const fill = new s.key.constructor(0xfff4e6, 0.6); fill.position.set(-1, 2, 6); s.scene.add(fill);
  s.camera.fov = 45; s.camera.updateProjectionMatrix();
  const L = (a, b, u) => a.map((v, i) => v + (b[i] - v) * u), E = u => u * u * (3 - 2 * u);
  // shots: [t0, t1, kind, cam0, cam1, tgt0, tgt1]  rel = offsets from robot (world axes); abs = world
  const SH = [
    [0, 11, 'crane', [-3.1, -2.95, 2.75], [-1.45, -0.3, 2.3], [0.9, -0.7, 0.45], [0.3, 0, 0.72]],
    [11, 23.6, 'rel', [1.5, -0.25, 1.5], [1.25, -0.55, 1.35], [0, 0.3, 1.0], [0, 0.32, 0.95]],
    [23.6, 37, 'rel', [-1.6, 0, 1.55], [-1.25, 0.1, 1.45], [0.6, 0, 0.95], [0.6, 0, 0.95]],
    [37, 52, 'rel', [-0.9, -0.2, 2.5], [0.9, -0.2, 2.4], [0.1, 0.1, 0.7], [0.2, 0.1, 0.7]],
    [52, 67, 'rel', [1.4, 0.25, 0.95], [1.6, 0.1, 1.15], [0, -0.3, 0.9], [0, -0.3, 0.95]],
    [67, 93, 'follow'],
    [93, 118, 'rel', [1.5, -0.25, 1.5], [1.2, -0.1, 1.25], [0, 0.3, 0.9], [0, 0.3, 0.9]],
    [118, 152, 'rel', [1.5, 0.25, 1.7], [1.2, 0.3, 1.95], [0, -0.3, 1.1], [0, -0.3, 1.15]],
    [152, 168, 'follow'],
    [168, 215, 'rel', [1.4, -0.9, 1.8], [1.15, 0.45, 1.7], [-0.5, 0, 0.8], [-0.5, 0, 0.8]],
    [215, 1e9, 'lock', [2.2, -1.8, 2.2], [2.7, -1.3, 2.25], [-0.4, 0, 0.7], [-0.4, 0, 0.7]],
  ];
  let fc = null, lastShot = -1;
  function cam(t) {
    const i = SH.findIndex(x => t >= x[0] && t < x[1]), sh = SH[i], g = s.robot.g.position, R = [g.x, g.y, 0];
    const u = E(Math.min(1, (t - sh[0]) / Math.min(sh[1] - sh[0], 40))), add = (a, o) => [a[0] + o[0], a[1] + o[1], o[2]];
    if (sh[2] === 'follow') {
      const yaw = s.robot.pose.yaw || 0, c = Math.cos(yaw), n = Math.sin(yaw);
      const cp = [g.x - 1.65 * c + 0.25 * n, g.y - 1.65 * n - 0.25 * c, 1.95], tp = [g.x + 0.55 * c, g.y + 0.55 * n, 0.75];
      if (i !== lastShot || !fc) fc = { cp, tp }; else { fc.cp = L(fc.cp, cp, 0.12); fc.tp = L(fc.tp, tp, 0.12); }
      lastShot = i; return [fc.cp, fc.tp];
    }
    if (sh[2] === 'lock') { if (i !== lastShot || !fc) fc = { base: R.slice() }; lastShot = i; const c = add(fc.base, L(sh[3], sh[4], u)), tl = add(fc.base, sh[5]), tr = add(R, sh[5]); return [c, L(tl, tr, 0.5)]; }
    lastShot = i;
    if (sh[2] === 'crane') return [L(sh[3], add(R, sh[4]), u), L(sh[5], add(R, sh[6]), u)];
    return [add(R, L(sh[3], sh[4], u)), add(R, L(sh[5], sh[6], u))];
  }
  const notes = s.TL.notes, nItems = notes.filter(n => n.text.startsWith('Pick ')).length;
  const oc = document.createElement('canvas'); oc.width = W; oc.height = H; const ctx = oc.getContext('2d');
  const hold = document.createElement('canvas'); hold.width = W; hold.height = H;
  const F = (w, px, fam = 'Barlow') => `${w} ${px}px "${fam}", sans-serif`;
  function pill(x, y, text, font, bg, fg, pad = 12, hgt = 34) {
    ctx.font = font; const w = ctx.measureText(text).width + pad * 2; ctx.fillStyle = bg; ctx.beginPath(); ctx.roundRect(x, y, w, hgt, 8); ctx.fill();
    ctx.fillStyle = fg; ctx.textBaseline = 'middle'; ctx.fillText(text, x + pad, y + hgt / 2 + 1); return w;
  }
  function hud(t) {
    let ph = ''; for (const n of notes) if (n.t <= t + 1e-6) ph = n.text;
    const picked = notes.filter(n => n.t <= t && n.text.startsWith('Place in')).length, onTable = notes.filter(n => n.t <= t && n.text.startsWith('Unload')).length;
    let x = 28; x += pill(x, 26, 'OpenAMRobot 2.0', F(700, 19, 'Barlow Semi Condensed'), 'rgba(14,18,24,0.82)', '#fff') + 8;
    pill(x, 26, 'Dark-store order run', F(500, 17), 'rgba(255,255,255,0.86)', '#16202a');
    ctx.font = F(700, 20, 'Barlow Semi Condensed'); const bw = 62; ctx.fillStyle = '#f2c230'; ctx.beginPath(); ctx.roundRect(W - 28 - bw, 26, bw, 34, 8); ctx.fill();
    ctx.fillStyle = '#16202a'; ctx.textAlign = 'center'; ctx.fillText('8×', W - 28 - bw / 2, 44); ctx.textAlign = 'left';
    const mm = Math.floor(t / 60), ss = Math.floor(t % 60).toString().padStart(2, '0');
    ctx.font = F(500, 17, 'IBM Plex Mono'); const tw = ctx.measureText(`${mm}:${ss}`).width + 24;
    pill(W - 28 - bw - 8 - tw, 26, `${mm}:${ss}`, F(500, 17, 'IBM Plex Mono'), 'rgba(14,18,24,0.82)', '#fff');
    const g = ctx.createLinearGradient(0, H - 150, 0, H); g.addColorStop(0, 'rgba(10,14,20,0)'); g.addColorStop(1, 'rgba(10,14,20,0.72)'); ctx.fillStyle = g; ctx.fillRect(0, H - 150, W, 150);
    ctx.fillStyle = '#f2c230'; ctx.fillRect(28, H - 92, 5, 58);
    ctx.fillStyle = '#fff'; ctx.textBaseline = 'alphabetic'; ctx.font = F(600, 30, 'Barlow Semi Condensed'); ctx.fillText(ph, 46, H - 62);
    ctx.font = F(500, 17); ctx.fillStyle = 'rgba(255,255,255,0.85)';
    ctx.fillText(`Shoulder height ${Math.round(s.robot.sh * 1000)} mm · DOLD Hexalift V4 lift · 2 × OpenArm 2.0`, 46, H - 36);
    const lab = onTable ? `On the table  ${onTable} / ${nItems}` : `In the totes  ${picked} / ${nItems}`;
    ctx.font = F(600, 22, 'Barlow Semi Condensed'); const lw = ctx.measureText(lab).width; ctx.fillStyle = '#fff'; ctx.fillText(lab, W - 28 - lw, H - 62);
    const pw = 220, pr = (onTable ? onTable : picked) / nItems; ctx.fillStyle = 'rgba(255,255,255,0.25)'; ctx.fillRect(W - 28 - pw, H - 46, pw, 6);
    ctx.fillStyle = onTable ? '#3ecf8e' : '#f2c230'; ctx.fillRect(W - 28 - pw, H - 46, pw * pr, 6);
  }
  function card(a, lines) {
    ctx.fillStyle = `rgba(10,14,20,${0.62 * a})`; ctx.fillRect(0, 0, W, H); ctx.globalAlpha = a; ctx.textAlign = 'center'; ctx.textBaseline = 'alphabetic';
    for (const [txt, font, col, y] of lines) { ctx.font = font; ctx.fillStyle = col; ctx.fillText(txt, W / 2, y); }
    ctx.textAlign = 'left'; ctx.globalAlpha = 1;
  }
  const tot = s.TL.T, mins = (tot / 60).toFixed(1);
  window.__frame = (k, n) => {
    const t = k.t; if (k.render) { s.applyAt(Math.min(t, tot)); const [c, tg] = cam(Math.min(t, tot - 1e-3)); s.closeUp(...c, ...tg); s.render(); hold.getContext('2d').drawImage(s.renderer.domElement, 0, 0, W, H); }
    ctx.drawImage(hold, 0, 0);
    if (k.kind === 'intro') { const a = Math.min(1, k.u * 4, (1 - k.u) * 5); card(Math.max(0, a), [
      ['OpenAMRobot 2.0', F(700, 72, 'Barlow Semi Condensed'), '#fff', H / 2 - 18],
      ['picks an 8-item grocery order in a dark store', F(500, 30), 'rgba(255,255,255,0.92)', H / 2 + 30],
      ['DOLD Hexalift V4 lift · 2 × OpenArm 2.0 · open-source simulation', F(500, 19), '#f2c230', H / 2 + 76]]); }
    else if (k.kind === 'outro') { hud(tot); card(Math.min(1, k.u * 3), [
      ['Order ready for packing', F(700, 60, 'Barlow Semi Condensed'), '#fff', H / 2 - 30],
      [`${nItems} items · 2 aisles · ${mins} min dock to dock`, F(500, 30), 'rgba(255,255,255,0.92)', H / 2 + 18],
      ['Shown at 8× speed · try it at docs.openamrobot.ai', F(500, 21), '#f2c230', H / 2 + 64]]); }
    else hud(t);
    return oc.toDataURL('image/jpeg', 0.93);
  };
  return tot;
}, { W, H });
// frame list
const frames = [];
const nI = Math.round(INTRO * FPS), nR = Math.ceil(T / SPEED * FPS), nO = Math.round(OUTRO * FPS);
for (let i = 0; i < nI; i++) frames.push({ kind: 'intro', t: 0, u: i / nI, render: i === 0 });
for (let i = 0; i <= nR; i++) frames.push({ kind: 'run', t: Math.min(T, i * SPEED / FPS), render: true });
for (let i = 0; i < nO; i++) frames.push({ kind: 'outro', t: T, u: i / nO, render: false });
let list = frames.map((f, i) => ({ ...f, i }));
if (MODE === 'preview') { const ts = [0, 6, 15, 30, 44, 60, 80, 100, 135, 160, 190, 230, 249]; list = ts.map(t => ({ kind: 'run', t, render: true, i: t })); list.unshift({ kind: 'intro', t: 0, u: 0.5, render: true, i: 'intro' }); list.push({ kind: 'outro', t: T, u: 0.9, render: true, i: 'outro' }); }
console.log('frames', frames.length, 'sim', T.toFixed(1));
// follow-cam smoothing needs sequential history: when resuming, warm up from 3 s before
if (START > 0) for (const f of list.slice(Math.max(0, START - 75), START)) if (f.render) await p.evaluate(f => { const s = window.__sim; s.applyAt(f.t); }, f);
const t0 = Date.now();
for (const f of list.slice(START)) {
  const d = await p.evaluate(f => window.__frame(f), f);
  const name = typeof f.i === 'number' && MODE === 'full' ? String(f.i).padStart(5, '0') : String(f.i);
  fs.writeFileSync(`${OUT}/${name}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
  if (MODE !== 'full' || f.i % 25 === 0) console.log('frame', name, ((Date.now() - t0) / 1000).toFixed(0) + 's');
}
await b.close(); srv.close(); console.log('done');
