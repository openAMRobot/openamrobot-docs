import { chromium } from 'playwright-core';
import fs from 'fs';
const W = 1280, H = 720, FPS = 25, F0 = +process.argv[2], N = +process.argv[3], OUT = process.argv[4];
const css = fs.readFileSync('out/web/index.html', 'utf8').match(/@font-face\{[^}]+\}/g).join('\n');
const b = await chromium.launch({ executablePath: process.env.CHROMIUM || '/opt/pw-browsers/chromium', headless: false, args: ['--headless=new'] });
const p = await b.newPage({ viewport: { width: W, height: H } });
await p.setContent(`<style>${css}</style><div style="font-family:'IBM Plex Mono';font-weight:500">x</div><div style="font-family:'IBM Plex Mono';font-weight:400">x</div><div style="font-family:'Barlow Semi Condensed';font-weight:700">x</div>`);
await p.evaluate(() => document.fonts.ready);
await p.evaluate(({ W, H }) => {
  const c = document.createElement('canvas'); c.width = W; c.height = H; const x = c.getContext('2d');
  const L = [
    { t: 'BUILD FAILED: warehouse integrity check', col: '#ff5f56', w: 500, x: true, at: 0.5, cps: 38 },
    { t: 'Known issue: bottle picking escalates into structural redesign.', col: '#d7dde4', w: 400, at: 2.1, cps: 34 },
    { t: 'PRs welcome. Join OpenAMRobot.', col: '#f2c230', w: 500, at: 4.6, cps: 26 },
    { t: 'github.com/openAMRobot · docs.openamrobot.ai', col: '#7fb4ff', w: 400, at: 5.9, cps: 48 },
  ];
  window.draw = T => {
    x.fillStyle = '#07090c'; x.fillRect(0, 0, W, H);
    const wx = 70, wy = 150, ww = W - 140, wh = 400, a = Math.min(1, T / 0.35);
    x.globalAlpha = a;
    x.fillStyle = '#11151b'; x.beginPath(); x.roundRect(wx, wy, ww, wh, 12); x.fill();
    x.strokeStyle = 'rgba(255,255,255,0.08)'; x.lineWidth = 1; x.stroke();
    x.fillStyle = '#1a1f27'; x.beginPath(); x.roundRect(wx, wy, ww, 40, [12, 12, 0, 0]); x.fill();
    ['#ff5f56', '#ffbd2e', '#27c93f'].forEach((cl, i) => { x.fillStyle = cl; x.beginPath(); x.arc(wx + 24 + i * 22, wy + 20, 6.5, 0, 7); x.fill(); });
    x.fillStyle = 'rgba(255,255,255,0.45)'; x.font = '400 15px "IBM Plex Mono"'; x.textAlign = 'center'; x.textBaseline = 'middle'; x.fillText('openamrobot · ci', wx + ww / 2, wy + 21); x.textAlign = 'left';
    const lx = wx + 40, ys = [wy + 100, wy + 170, wy + 250, wy + 300], fs = [27, 25, 30, 22];
    let cur = null;
    L.forEach((l, i) => {
      if (T < l.at) return;
      const n = Math.min(l.t.length, Math.floor((T - l.at) * l.cps)); const s = l.t.slice(0, n);
      let px = lx;
      if (l.x) { x.strokeStyle = l.col; x.lineWidth = 4; x.lineCap = 'round'; const cx = lx + 11, cy = ys[i] - 1, r = 9; x.beginPath(); x.moveTo(cx - r, cy - r); x.lineTo(cx + r, cy + r); x.moveTo(cx + r, cy - r); x.lineTo(cx - r, cy + r); x.stroke(); px = lx + 40; }
      x.font = `${l.w} ${fs[i]}px "IBM Plex Mono"`; x.fillStyle = l.col; x.textBaseline = 'middle'; x.fillText(s, px, ys[i]);
      cur = { x: px + x.measureText(s).width + 4, y: ys[i], h: fs[i] + 6, done: n >= l.t.length };
    });
    if (!cur) cur = { x: lx, y: wy + 100, h: 33, done: true };
    if (!cur.done || Math.floor(T * 2.2) % 2 === 0) { x.fillStyle = '#d7dde4'; x.fillRect(cur.x, cur.y - cur.h / 2, 13, cur.h); }
    x.globalAlpha = 1;
    return c.toDataURL('image/jpeg', 0.93);
  };
}, { W, H });
for (let i = 0; i < N; i++) {
  const d = await p.evaluate(T => window.draw(T), i / FPS);
  fs.writeFileSync(`${OUT}/${String(F0 + i).padStart(5, '0')}.jpg`, Buffer.from(d.split(',')[1], 'base64'));
}
await b.close(); console.log('ok');
