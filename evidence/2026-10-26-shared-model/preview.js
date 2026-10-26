// Preview pictures, 1920 x 1080, page UI hidden, full look unless noted. Exploded-view pictures come from the
// page's render mode (exploded.html?render=1, window.__renderKey with a pose written like a tour keyframe);
// robot-page pictures from robot.html?look=full with everything but the 3D canvas hidden, camera tiles,
// Frames and Labels switched off for the picture (page defaults unchanged). 05 is framed to fill 80 % of the height.
// node preview.js <port> <out dir> [exploded|robot|light]
const { chromium } = require('playwright');
const fs = require('fs');
const UPPER = ['lift_column', 'adapter_plate', 'arm_profile', 'slot_cover_strips', 'openarm', 'head_camera', 'head_camera_bracket'];
const BASE_LABELS = ['battery', 'motor_driver', 'compute', 'base_controller', 'imu', 'lidar', 'base_camera', 'ultrasonic', 'tof'];
const SHOTS = [
  ['01_assembled_front_three_quarter', {frame: 'robot', az: -40, el: 16, zoom: .82}],
  ['02_assembled_rear_three_quarter', {frame: 'robot', az: 140, el: 18, zoom: .82}],
  ['03_base_close_up_front_three_quarter', {frame: 'base', az: -35, el: 5, min_r: .3, zoom: .85}],
  ['04_upper_body_close_up', {frame: ['arm_profile', 'openarm', 'head_camera', 'head_camera_bracket', 'adapter_plate'], az: -28, el: 12, min_r: .25, zoom: .9}],
  ['05_exploded_explode_robot', {frame: 'robot', r: 1, az: -40, el: 18, fill: true}],
  ['06_exploded_open_base_labels', {frame: 'base', b: 1, az: -40, el: 26, labels: BASE_LABELS, names: true}],
];
// exploded robot fills FILL of the image height: render with and without the robot, take the rows that
// differ, scale the camera distance (zoom) and repeat.
const FILL = .8;
async function fitZoom(p, k) {
  let z = k.zoom || 1;
  for (let i = 0; i < 3; i++) {
    const f = await p.evaluate(async k => {
      const root = window.__last[1].getObjectByName('OpenAMRobot'), load = u => new Promise(r => { const im = new Image(); im.onload = () => r(im); im.src = u; });
      const a = await load(window.__renderKey(k)); root.visible = false; const b = await load(window.__renderKey(k)); root.visible = true;
      const c = document.createElement('canvas'); c.width = a.width; c.height = a.height; const x = c.getContext('2d');
      x.drawImage(a, 0, 0); const A = x.getImageData(0, 0, c.width, c.height).data; x.drawImage(b, 0, 0); const B = x.getImageData(0, 0, c.width, c.height).data;
      let top = -1, bot = -1;
      for (let y = 0; y < c.height; y++) { let d = 0; for (let i = y * c.width * 4; i < (y + 1) * c.width * 4; i += 4) d += Math.abs(A[i] - B[i]) > 12 ? 1 : 0; if (d > 2) { if (top < 0) top = y; bot = y; } }
      return (bot - top + 1) / c.height;
    }, Object.assign({}, k, {zoom: z}));
    console.log('fill', z.toFixed(3), f.toFixed(3));
    if (Math.abs(f - FILL) < .02) break;
    z = z * f / FILL;
  }
  return Object.assign({}, k, {zoom: z});
}
const save = (f, url) => fs.writeFileSync(f, Buffer.from(url.split(',')[1], 'base64'));
(async () => {
  const [port, out, which] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  if (!which || which === 'exploded' || which === 'light') {
    const p = await b.newPage({viewport: {width: 1920, height: 1080}}); p.setDefaultTimeout(600000);
    await p.addInitScript(() => { let T; Object.defineProperty(window, 'THREE', {configurable: true, get() { return T; }, set(v) {
      const W = v.WebGLRenderer; v.WebGLRenderer = function (a) { const r = new W(a), o = r.render; r.render = function (s, c) { window.__last = [r, s, c]; o.call(r, s, c); }; return r; }; T = v; }}); });
    const light = which === 'light';
    await p.goto(`http://localhost:${port}/exploded.html?render=1&w=1920&h=1080&frame=0${light ? '&look=light' : ''}`);
    await p.waitForFunction(() => window.__renderKey);
    for (let [name, k] of light ? [['09_light_look_assembled_front_three_quarter', SHOTS[0][1]]] : SHOTS) {
      if (k.fill) k = await fitZoom(p, k);
      save(`${out}/${name}.png`, await p.evaluate(k => window.__renderKey(k), k));
    }
    await p.close();
  }
  if (!which || which === 'robot') {
    for (const [name, view] of [['07_robot_page_side_dark_store', 'side'], ['08_robot_page_overview_dark_store', 'over']]) {
      const p = await b.newPage({viewport: {width: 1920, height: 1080}}); p.setDefaultTimeout(900000);
      await p.goto(`http://localhost:${port}/robot.html?look=full`, {waitUntil: 'domcontentloaded'});
      await p.waitForFunction(() => window.__sim && window.__sim.robot);
      await p.addStyleTag({content: '#stage{position:fixed!important;left:0;top:0;width:1920px!important;height:1080px!important;z-index:9999;margin:0}#stage>:not(canvas){display:none!important}body{overflow:hidden}'});
      await p.evaluate(v => { const t = document.getElementById('b-tiles'); if (window.__sim.S.tiles) t.click();
        ['b-frames', 'b-labels'].forEach(id => { const e = document.getElementById(id); if (e.getAttribute('aria-pressed') === 'true') e.click(); });  // these pictures only
        document.querySelector(`[data-view="${v}"]`).click(); }, view);
      await p.waitForTimeout(150000);
      await p.evaluate(() => window.__sim.render());
      await p.locator('#stage canvas').first().screenshot({path: `${out}/${name}.png`});
      await p.close();
    }
  }
  await b.close();
})();
