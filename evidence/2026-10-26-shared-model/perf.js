// Frame time, same machine, headless Chromium + SwiftShader, 1280 x 800, median of N synced renders.
// exploded.html: every WebGLRenderer.render call of the page timed (render + 1-pixel readPixels to wait for the GPU);
//   "pose" = tour frames (parts move, shadow map updated), "orbit" = the same frame rendered again (camera-only change).
// robot.html: window.__sim.render() (store scene, GTAO in high quality, camera tiles) + 1-pixel readPixels.
const { chromium } = require('playwright');
const N = 30, WARM = 5;
const med = a => { a = a.slice().sort((x, y) => x - y); return a[a.length >> 1]; };
(async () => {
  const [port] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  const out = {};
  let p = await b.newPage({viewport: {width: 1280, height: 800}});
  p.setDefaultTimeout(600000);
  await p.addInitScript(() => {
    let T;
    Object.defineProperty(window, 'THREE', {configurable: true, get() { return T; }, set(v) {
      const W = v.WebGLRenderer;
      v.WebGLRenderer = function (a) {  // r160 defines render per instance: wrap it
        const r = new W(a), o = r.render;
        r.render = function (s, c) {
          const t0 = performance.now(); o.call(r, s, c);
          const gl = r.getContext(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4));
          window.__last = [r, s, c]; (window.__rt = window.__rt || []).push(performance.now() - t0);
        };
        return r;
      };
      T = v;
    }});
  });
  await p.goto(`http://localhost:${port}/exploded.html?render=1&w=1280&h=800&frame=0`);
  await p.waitForFunction(() => window.__renderFrame);
  out.exploded_pose = await p.evaluate(([N, W]) => { const t = []; for (let i = 0; i < N + W; i++) { window.__rt = []; window.__renderFrame(60 + i * 20); if (i >= W) t.push(window.__rt.reduce((a, b) => a + b, 0)); } return t; }, [N, WARM]);
  out.exploded_orbit = await p.evaluate(([N, W]) => { const [r, s, c] = window.__last, t = []; for (let i = 0; i < N + W; i++) { window.__rt = []; r.render(s, c); if (i >= W) t.push(window.__rt[0]); } return t; }, [N, WARM]);
  await p.close();
  p = await b.newPage({viewport: {width: 1280, height: 800}});
  p.setDefaultTimeout(600000);
  await p.goto(`http://localhost:${port}/robot.html`, {waitUntil: 'domcontentloaded'});
  await p.waitForFunction(() => window.__sim && window.__sim.robot);
  await p.waitForTimeout(5000);
  out.robot = await p.evaluate(([N, W]) => {
    const r = window.__sim.renderer, gl = r.getContext(), t = [];
    for (let i = 0; i < N + W; i++) { const t0 = performance.now(); window.__sim.render(); gl.readPixels(0, 0, 1, 1, gl.RGBA, gl.UNSIGNED_BYTE, new Uint8Array(4)); if (i >= W) t.push(performance.now() - t0); }
    return t;
  }, [N, WARM]);
  await b.close();
  const res = {};
  for (const k in out) res[k] = +med(out[k]).toFixed(1);
  console.log(JSON.stringify(res));
})();
