#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Render the guided tour of docs/assets/roadmap/exploded.html to an H.264 video, frame by frame,
// from the page's deterministic render mode (exploded.html?render=1&frame=N&w=W&h=H). Each frame
// comes from window.__renderFrame(n) as a PNG and is piped into ffmpeg; the tour, captions and
// labels are those of model/exploded.json, so the video and the page draw the same shared model.
//
// Usage (Playwright with Chromium and ffmpeg on PATH; serve docs/assets/roadmap first):
//   (cd docs/assets/roadmap && python3 -m http.server 8765) &
//   node scripts/render_tour.js 1920 1080 docs/assets/roadmap/media/openamrobot-2-tour-1080p.mp4
//   node scripts/render_tour.js 1080 1350 docs/assets/roadmap/media/openamrobot-2-tour-1080x1350.mp4
// Optional fourth argument: base URL (default http://localhost:8765/).
// Options: --crf Q (x264 quality, default 23; higher is smaller), --frames-dir DIR (write the PNG frames there and encode
//   from them, so that the video can be encoded again at another --crf without rendering), --resume 1 (with --frames-dir:
//   keep complete frames already there and render only the missing ones).
const { chromium } = require('playwright');
const { spawn } = require('child_process');
const fs = require('fs');
const path = require('path');

(async () => {
  const args = process.argv.slice(2), opt = {}, pos = [];
  for (let i = 0; i < args.length; i++) if (args[i].startsWith('--')) opt[args[i].slice(2)] = args[++i]; else pos.push(args[i]);
  const [w, h, out, base] = pos, crf = String(opt.crf || 23), dir = opt['frames-dir'];
  if (!w || !h || !out) { console.error('usage: render_tour.js <w> <h> <out.mp4> [base url]'); process.exit(2); }
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push(e.message));
  await page.goto(`${base || 'http://localhost:8765/'}exploded.html?render=1&frame=0&w=${w}&h=${h}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__frameReady === true, null, { timeout: 120000 });
  const info = await page.evaluate(() => window.__tour);
  const enc = ['-c:v', 'libx264', '-preset', 'veryfast', '-crf', crf, '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out];
  const ff = spawn('ffmpeg', ['-y', '-loglevel', 'error', '-f', 'image2pipe', '-framerate', String(info.fps), '-c:v', 'png', '-i', '-', ...enc],
    { stdio: ['pipe', 'inherit', 'inherit'] });
  const file = n => path.join(dir, `${String(n).padStart(5, '0')}.png`);
  const complete = f => { try { const d = fs.readFileSync(f); return d.length > 12 && d.subarray(d.length - 8, d.length - 4).toString() === 'IEND' ? d : null; } catch (e) { return null; } };
  if (dir) fs.mkdirSync(dir, { recursive: true });
  for (let n = 0; n < info.frames; n++) {
    let buf = dir && opt.resume !== undefined ? complete(file(n)) : null;
    if (!buf) {
      const url = await page.evaluate(k => window.__renderFrame(k), n);
      buf = Buffer.from(url.slice(url.indexOf(',') + 1), 'base64');
      if (dir) fs.writeFileSync(file(n), buf);
    }
    if (!ff.stdin.write(buf)) await new Promise(r => ff.stdin.once('drain', r));
    if (n % 150 === 0) console.error(`frame ${n} of ${info.frames}`);
  }
  ff.stdin.end();
  const code = await new Promise(r => ff.on('close', r));
  await browser.close();
  if (errs.length) { console.error('console errors:', errs); process.exit(1); }
  process.exit(code);
})();
