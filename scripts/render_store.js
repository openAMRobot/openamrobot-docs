#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Render one "Run order (8 items)" run of the grocery store on docs/assets/roadmap/robot.html to an H.264 video,
// frame by frame, from the page's deterministic render mode (robot.html?render=1&frame=N&w=W&h=H&fps=F&speed=K&cam=C).
// Frame N shows sim time N / F x K; the camera, robot, items and lighting of a frame depend on that time only, so the
// frame range can be split across parallel browser workers and the PNG frames are the same however it is split.
// The frames are written to a folder, then encoded with ffmpeg (libx264, yuv420p, no audio).
//
// Usage (Playwright with Chromium and ffmpeg on PATH; serve docs/assets/roadmap first):
//   (cd docs/assets/roadmap && python3 -m http.server 8765) &
//   node scripts/render_store.js 1920 1080 docs/assets/roadmap/media/openamrobot-2-store-1080p.mp4 --fps 30 --speed 6.4 --workers 2
// Options: --fps F (default 30), --speed K (sim seconds per video second, default 6.4), --cam C (default auto),
//   --workers N (default 1), --frames A:B (render frames A to B-1 only, no video), --frames-dir DIR (keep the PNG
//   frames there), --resume 1 (keep complete frames already in --frames-dir and render only the missing ones), --base URL (default http://localhost:8765/), --hashes FILE (write the sha256 of every frame).
//   --recaption 1: lay the page's current corner caption (window.__captionOverlay, opaque box) over every frame
//   while encoding, for frames rendered before a caption change.
//   --still T --cam C --out FILE.png|jpg: one picture at sim time T instead of a video.
const { chromium } = require('playwright');
const { spawnSync } = require('child_process');
const crypto = require('crypto');
const fs = require('fs');
const os = require('os');
const path = require('path');

const args = process.argv.slice(2), opt = {}, pos = [];
for (let i = 0; i < args.length; i++) if (args[i].startsWith('--')) opt[args[i].slice(2)] = args[++i]; else pos.push(args[i]);
const [w, h, out] = pos;
if (!w || !h || (!out && !opt.frames && !opt.still)) {
  console.error('usage: render_store.js <w> <h> <out.mp4> [--fps F] [--speed K] [--cam C] [--workers N] [--frames A:B] [--frames-dir DIR] [--base URL] [--hashes FILE]');
  console.error('       render_store.js <w> <h> --still T --cam C --out FILE');
  process.exit(2);
}
const fps = +(opt.fps || 30), speed = +(opt.speed || 6.4), cam = opt.cam || 'auto', base = opt.base || 'http://localhost:8765/';
const url = `${base}robot.html?render=1&w=${w}&h=${h}&fps=${fps}&speed=${speed}&cam=${cam}#nomtx`;

async function open(browser) {
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  page.setDefaultTimeout(1800000);
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push(e.message));
  await page.goto(url, { waitUntil: 'domcontentloaded' });
  await page.waitForFunction(() => window.__frameReady === true);
  return { page, errs };
}
const launch = () => chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
const png = u => Buffer.from(u.slice(u.indexOf(',') + 1), 'base64');

(async () => {
  if (opt.still !== undefined) {
    const browser = await launch(), { page, errs } = await open(browser);
    const fmt = /\.jpe?g$/i.test(opt.out) ? 'jpeg' : 'png';
    fs.writeFileSync(opt.out, png(await page.evaluate(([t, c, f]) => window.__renderAt(t, c, f), [+opt.still, cam, fmt])));
    await browser.close();
    if (errs.length) { console.error('console errors:', errs); process.exit(1); }
    return;
  }
  const probe = await launch(), first = await open(probe);
  const info = await first.page.evaluate(() => window.__store);
  const overlay = opt.recaption !== undefined ? png(await first.page.evaluate(() => window.__captionOverlay())) : null;
  await probe.close();
  let [a, b] = opt.frames ? opt.frames.split(':').map(Number) : [0, info.frames];
  b = Math.min(b, info.frames);
  const dir = opt['frames-dir'] || fs.mkdtempSync(path.join(os.tmpdir(), 'store-frames-'));
  fs.mkdirSync(dir, { recursive: true });
  const n = Math.max(1, +(opt.workers || 1)), per = Math.ceil((b - a) / n), t0 = Date.now(), errors = [];
  const frameFile = f => path.join(dir, `${String(f).padStart(5, '0')}.png`);
  const complete = file => { try { const d = fs.readFileSync(file); return d.length > 12 && d.subarray(d.length - 8, d.length - 4).toString() === 'IEND'; } catch (e) { return false; } };
  console.error(`run ${info.T.toFixed(1)} s sim, speed ${speed}, ${fps} fps: frames ${a} to ${b - 1} of ${info.frames}, ${n} worker(s)`);
  await Promise.all(Array.from({ length: n }, async (_, k) => {
    const lo = a + k * per, hi = Math.min(b, lo + per);
    if (lo >= hi) return;
    const todo = [];
    for (let f = lo; f < hi; f++) if (!(opt.resume !== undefined && complete(frameFile(f)))) todo.push(f);
    if (!todo.length) return;
    const browser = await launch(), { page, errs } = await open(browser);
    for (const f of todo) {
      const tmp = frameFile(f) + '.part';  // written whole, then renamed: a frame on disk is always complete
      fs.writeFileSync(tmp, png(await page.evaluate(i => window.__renderFrame(i), f)));
      fs.renameSync(tmp, frameFile(f));
      if (f % 30 === 0) console.error(`worker ${k}: frame ${f} (${((Date.now() - t0) / 1000).toFixed(0)} s)`);
    }
    errors.push(...errs);
    await browser.close();
  }));
  console.error(`frames ${a} to ${b - 1} done in ${((Date.now() - t0) / 1000).toFixed(0)} s`);
  if (opt.hashes) {
    const lines = [];
    for (let f = a; f < b; f++) lines.push(crypto.createHash('sha256').update(fs.readFileSync(path.join(dir, `${String(f).padStart(5, '0')}.png`))).digest('hex') + `  ${String(f).padStart(5, '0')}.png`);
    fs.writeFileSync(opt.hashes, lines.join('\n') + '\n');
  }
  if (errors.length) { console.error('console errors:', errors); process.exit(1); }
  if (opt.frames) return;
  const input = ['-framerate', String(fps), '-start_number', '0', '-i', path.join(dir, '%05d.png')];
  if (overlay) {  // the page's current corner caption over every frame (frames rendered with an earlier caption)
    fs.writeFileSync(path.join(dir, 'caption.png'), overlay);
    input.push('-i', path.join(dir, 'caption.png'), '-filter_complex', '[0:v][1:v]overlay=0:0:format=rgb');
  }
  const r = spawnSync('ffmpeg', ['-y', '-loglevel', 'error', ...input,
    '-c:v', 'libx264', '-preset', 'veryfast', '-crf', '23', '-pix_fmt', 'yuv420p', '-movflags', '+faststart', '-an', out], { stdio: 'inherit' });
  if (!opt['frames-dir']) fs.rmSync(dir, { recursive: true, force: true });
  process.exit(r.status);
})();
