// node render.js <base url> <out dir> <jobs.json>
// jobs: [{name, k:{frame,az,el,zoom,r,lift,hide}, w, h, bg:[r,g,b] | "cutout"}]
const { chromium } = require('playwright');
const fs = require('fs');
const [base, out, jobsFile] = process.argv.slice(2);
const jobs = JSON.parse(fs.readFileSync(jobsFile, 'utf8'));
const GL = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
(async () => {
  const b = await chromium.launch({ args: GL, executablePath: '/usr/bin/google-chrome' });
  fs.mkdirSync(out, { recursive: true });
  const bySize = {};
  jobs.forEach(j => { (bySize[j.w + 'x' + j.h] = bySize[j.w + 'x' + j.h] || []).push(j); });
  for (const sz of Object.keys(bySize)) {
    const [W, H] = sz.split('x').map(Number);
    const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    p.setDefaultTimeout(1800000);
    p.on('pageerror', e => console.log('pageerror', String(e)));
    await p.goto(`${base}exploded.html?render=1&frame=0&w=${W}&h=${H}`, { waitUntil: 'load' });
    await p.waitForFunction(() => window.__frameReady === true);
    await p.evaluate(() => {
      const g = window.__model.root.parent.userData.grid;
      g.material.colorWrite = false; g.material.depthWrite = false;
    });
    for (const j of bySize[sz]) {
      const shots = j.bg === 'cutout' ? [[0, 0, 0], [255, 255, 255]] : [j.bg];
      for (let i = 0; i < shots.length; i++) {
        const url = await p.evaluate(([k, c, cut]) => {
          const scene = window.__model.root.parent;
          scene.background.setRGB(c[0] / 255, c[1] / 255, c[2] / 255, 'srgb');
          (scene.userData.ground || []).forEach(g => { g.material.colorWrite = !cut; });
          window.__renderKey(Object.assign({ labels: [], caption: null }, k));
          return document.querySelector('#stage canvas').toDataURL('image/png');
        }, [j.k, shots[i], j.bg === 'cutout']);
        const suffix = j.bg === 'cutout' ? (i ? '_white' : '_black') : '';
        fs.writeFileSync(`${out}/${j.name}${suffix}.png`, Buffer.from(url.split(',')[1], 'base64'));
        console.log('wrote', j.name + suffix);
      }
    }
    await p.close();
  }
  await b.close();
})();
