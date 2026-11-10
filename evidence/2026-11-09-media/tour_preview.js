#!/usr/bin/env node
// SPDX-License-Identifier: MIT
// Preview of the exploded-view tour before the final renders (9 Nov 2026): one low-resolution frame per tour keyframe,
// taken 0.5 s after the keyframe, from the same deterministic render mode as scripts/render_tour.js.
// Usage: node evidence/2026-11-09-media/tour_preview.js <base url> <out dir> [w h]
const { chromium } = require('playwright');
const fs = require('fs');
const path = require('path');

(async () => {
  const [base, out, w = '640', h = '360'] = process.argv.slice(2);
  fs.mkdirSync(out, { recursive: true });
  const browser = await chromium.launch({ args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] });
  const page = await browser.newPage({ viewport: { width: +w, height: +h }, deviceScaleFactor: 1 });
  const errs = [];
  page.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
  page.on('pageerror', e => errs.push(e.message));
  await page.goto(`${base}exploded.html?render=1&frame=0&w=${w}&h=${h}`, { waitUntil: 'load' });
  await page.waitForFunction(() => window.__frameReady === true, null, { timeout: 120000 });
  const info = await page.evaluate(() => window.__tour);
  const keys = JSON.parse(fs.readFileSync(path.join(__dirname, '../../docs/assets/roadmap/model/exploded.json'), 'utf8')).tour.keys;
  const list = [];
  for (const k of keys) {
    const n = Math.min(info.frames - 1, Math.round((k.t + 0.5) * info.fps));
    const url = await page.evaluate(i => window.__renderFrame(i), n);
    const f = path.join(out, `${String(n).padStart(5, '0')}.png`);
    fs.writeFileSync(f, Buffer.from(url.slice(url.indexOf(',') + 1), 'base64'));
    list.push({ t: k.t, frame: n, file: path.basename(f), caption: k.caption || '' });
  }
  fs.writeFileSync(path.join(out, 'preview.json'), JSON.stringify({ fps: info.fps, frames: info.frames, list }, null, 1));
  await browser.close();
  if (errs.length) { console.error('console errors:', errs); process.exit(1); }
  console.log(`preview: ${list.length} frames of ${info.frames}`);
})();
