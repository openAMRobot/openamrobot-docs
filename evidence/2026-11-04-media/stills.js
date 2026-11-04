// High-resolution stills of the roadmap model (docs/assets/roadmap/media/stills/): 2560 x 1440, full look.
// Robot stills 1 to 8: exploded.html render mode, one pose written like a tour keyframe (window.__renderKey: frame,
// az, el, zoom, r, b, c, lift, hide), then the raw 3D canvas (no labels, no corner caption, grid lines hidden; the
// shadow ground stays). Store stills 9 and 10: robot.html render mode (window.__renderAt, sim time and camera of the
// store pictures) with the corner caption off (&caption=0). The bottom caption line is burned in by stills_caption.py.
// node stills.js <base url> <out dir> [name filter]
const { chromium } = require('playwright');
const fs = require('fs');
const [base, out, only] = [process.argv[2], process.argv[3], process.argv[4] || ''];
const W = 2560, H = 1440;
const HID = ['cover', 'cover_flange', '@upper', 'lift_base_plate'];
const REAR = ['rear_plate', 'rz_f0', 'rz_k1k2', 'rz_fbb', 'rz_fba', 'rz_bms', 'rz_pwr017', 'rz_disc', 'tz_receiver'];
const SIDE = ['side_plates', 'bay_fbc', 'bay_usbpd', 'bay_pwr032', 'bay_usbhub', 'bay_usbcan', 'bay_lidar_uart', 'bay_plate', 'compute'];
const BODY = ['base_plate', 'cover', 'front_panel', 'rear_panel', 'side_panel', 'hub_motor_wheel', 'castor', 'lift_column', 'adapter_plate', 'arm_profile', 'openarm', 'head_camera', 'getac_tablet'];
const ROBOT = [
  ['01_robot_front_three_quarter_L1000', {frame: BODY, az: -38, el: 14, zoom: 1.0}],
  ['02_robot_rear_three_quarter_L1350', {frame: BODY, az: 148, el: 14, zoom: 1.0, lift: 0.35}],
  ['03_robot_side', {frame: BODY, az: -90, el: 4, zoom: 1.0}],
  ['04_base_cover_off_harness', {frame: 'base', az: -38, el: 52, zoom: 0.85, hide: HID}],
  ['05_rear_power_module', {frame: REAR, min_r: 0.18, az: 145, el: 40, zoom: 1.05, hide: HID}],
  ['06_front_bay_side_zones', {frame: SIDE, min_r: 0.18, az: -20, el: 52, zoom: 1.1, hide: HID}],
  ['07_lift_column_rear', {frame: ['lift_column', 'lift_energy_chain', 'flag_rod', 'flag_rod_guide', 'lift_stop_sensors'], az: 210, el: 10, zoom: 1.6, hide: ['openarm']}],
  ['08_exploded_view', {frame: 'robot', az: -42, el: 20, r: 1, zoom: 0.8}],
];
const STORE = [
  ['09_store_picking_from_shelf', 15.6, 'pick'],
  ['10_store_at_dock', 255.9, 'over'],
];
const GL = ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'];
(async () => {
  const b = await chromium.launch({ args: GL }), errs = [];
  fs.mkdirSync(out, { recursive: true });
  const page = async url => {
    const p = await b.newPage({ viewport: { width: W, height: H }, deviceScaleFactor: 1 });
    p.setDefaultTimeout(1800000);
    p.on('pageerror', e => errs.push(String(e))); p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(url, { waitUntil: 'load' });
    await p.waitForFunction(() => window.__frameReady === true);
    return p;
  };
  const robot = ROBOT.filter(s => s[0].includes(only)), store = STORE.filter(s => s[0].includes(only));
  if (robot.length) {
    const p = await page(`${base}exploded.html?render=1&frame=0&w=${W}&h=${H}`);
    await p.evaluate(() => {  // grid lines off for a clean background (the page sets visible on every pose)
      const g = window.__model.root.parent.userData.grid;
      Object.defineProperty(g, 'visible', { get: () => false, set: () => {} });
    });
    for (const [name, k] of robot) {
      const url = await p.evaluate(k => { window.__renderKey(Object.assign({labels: [], caption: null}, k)); return document.querySelector('#stage canvas').toDataURL('image/png'); }, k);
      fs.writeFileSync(`${out}/${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
      console.log('wrote', name);
    }
    await p.close();
  }
  for (const [name, t, cam] of store) {
    const p = await page(`${base}robot.html?render=1&w=${W}&h=${H}&fps=24&speed=7.5&cam=${cam}&caption=0#nomtx`);
    const url = await p.evaluate(([t, c]) => window.__renderAt(t, c, 'png'), [t, cam]);
    fs.writeFileSync(`${out}/${name}.png`, Buffer.from(url.split(',')[1], 'base64'));
    console.log('wrote', name);
    await p.close();
  }
  console.log('errors', errs.length, errs.slice(0, 5));
  await b.close();
  if (errs.length) process.exit(1);
})();
