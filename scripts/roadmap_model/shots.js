// Screenshots of the shared roadmap model for the visual review (evidence/2026-11-02-roadmap-update).
// Each shot renders one keyframe of the exploded view (render mode, window.__renderKey): frame = component ids to fit,
// az / el (deg), zoom, r (explode), b (open base), c (cutaway), labels.
//   node scripts/roadmap_model/shots.js [base URL, default http://localhost:8765/] [out dir] [name filter]
// Serve docs/assets/roadmap first: (cd docs/assets/roadmap && python3 -m http.server 8765)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765/';
const OUT = process.argv[3] || path.join(__dirname, '..', '..', 'evidence', '2026-11-02-roadmap-update');
const ONLY = process.argv[4] || '';
const BAY = ['bay_plate', 'compute', 'base_controller', 'bay_din', 'bay_ddr240', 'bay_rsd60', 'bay_rsd100', 'bay_fbc', 'bay_usbhub', 'lidar_support', 'lidar'];
const REAR = ['battery_cells', 'battery_tray', 'rear_plate', 'rz_f0', 'rz_k1k2', 'rz_pre', 'rz_kchg', 'rz_fchg', 'rz_fba', 'rz_pwr017', 'rz_disc', 'rz_sb50', 'tz_receiver'];
const SHOTS = [
  // front bay, one layout (A2)
  {name: 'front_bay_top', hideUpper: 2, k: {frame: BAY, az: -90, el: 89, zoom: 1.55, c: 1, labels: ['compute', 'bay_ddr240', 'bay_din', 'bay_rsd100', 'bay_fbc', 'bay_usbhub'], caption: 'Front bay, one layout (A2): top view, cover off'}},
  {name: 'front_bay_side_section', hideUpper: true, k: {frame: ['bay_plate', 'compute', 'bay_ddr240', 'lidar'], az: -90, el: 0, zoom: 0.95, c: 1, labels: ['bay_ddr240', 'compute', 'lidar', 'bay_rsd100'], caption: 'Front bay: side view (cutaway), plate on the base sheet, second tier'}},
  {name: 'front_bay_opened', k: {frame: 'base', az: -35, el: 32, zoom: 0.95, b: 1, labels: ['compute', 'bay_ddr240', 'bay_din', 'battery_cells', 'rear_plate'], caption: 'Opened base: front bay and rear section'}},
  // rear section (A1): receiver reserved at the rear panel, cells in the side pockets, power plate above
  {name: 'rear_section_top', hideUpper: 2, k: {frame: REAR, az: 90, el: 89, zoom: 1.4, c: 1, labels: ['battery_cells', 'tz_receiver', 'rz_fba', 'rz_f0', 'rz_k1k2', 'rz_disc'], caption: 'Rear section (A1): receiver reserved at the rear panel, 4 + 4 LF105 in the side pockets, power plate above'}},
  {name: 'rear_section_3d', hideUpper: true, k: {frame: REAR, az: 150, el: 35, zoom: 1.15, c: 1, labels: ['battery_cells', 'battery_tray', 'rear_plate', 'tz_metal_free_zone', 'battery_series_link'], caption: 'Rear section: trays, series link across the centre, power plate 122 mm above the floor'}},
  {name: 'tzbot_receiver_below', k: {frame: ['tz_receiver', 'tz_metal_free_zone', 'base_cutout', 'tof_rear'], az: 120, el: -25, zoom: 1.6, labels: ['tz_receiver', 'base_cutout', 'tz_metal_free_zone', 'tof_rear'], caption: 'TZBOT WCM-500-24 receiver reserved at the rear panel (release 3.0): from below, with the 20 mm margin'}},
  // second E-stop on the adapter plate (A5), Getac portrait and light (A3), ZED (A4)
  {name: 'estop_adapter_plate', k: {frame: ['second_estop', 'rear_estop_housing', 'adapter_plate', 'arm_profile'], az: 200, el: 30, zoom: 1.8, labels: ['second_estop', 'rear_estop_housing', 'adapter_plate'], caption: 'Second E-stop on the adapter plate behind the post, button up (A5)'}},
  {name: 'getac_portrait', k: {frame: ['getac_pocket', 'getac_tablet', 'head_light', 'head_camera'], az: -25, el: 8, zoom: 1.3, labels: ['getac_tablet', 'head_light', 'head_camera'], caption: 'Getac ZX80 portrait (A3), light bar 10 mm below, ZED lens 57 mm ahead of J1_A (A4)'}},
  {name: 'upper_body_side', k: {frame: ['arm_profile', 'getac_tablet', 'head_camera', 'second_estop', 'lift_column'], az: -90, el: 5, zoom: 1.05, labels: ['getac_tablet', 'head_camera', 'second_estop', 'head_light'], caption: 'Upper body, side view at L1000'}},
  {name: 'harness_front', hideUpper: true, k: {frame: ['harness_sig', 'harness_bat', 'lidar'], az: -55, el: 25, zoom: 1.1, c: 1, labels: ['harness_sig', 'harness_bat', 'lidar'], caption: 'Harness: front trunk below the LiDAR scan plane behind the open sector'}},
  {name: 'exploded_assembled', k: {frame: 'robot', az: -40, el: 18, caption: 'OpenAMRobot 2.0, assembled. Shared roadmap model, visualization only'}},
  {name: 'exploded_rear_view', k: {frame: 'robot', az: 150, el: 18, caption: 'OpenAMRobot 2.0 from the rear'}},
];
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  fs.mkdirSync(OUT, {recursive: true});
  const errs = [];
  for (const bay of ['one']) {
    const list = SHOTS.filter(s => s.name.includes(ONLY));
    if (!list.length) continue;
    const p = await b.newPage({viewport: {width: 1280, height: 720}});
    p.setDefaultTimeout(600000);
    p.on('pageerror', e => errs.push(String(e)));
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(BASE + 'exploded.html?render=1&frame=0&w=1280&h=720' , {waitUntil: 'load'});
    await p.waitForFunction(() => window.__frameReady === true);
    for (const s of list) {
      const url = await p.evaluate(([k, hide]) => {
        // hide the lift assembly and the arms for views into the base (restored after the shot)
        const M = window.__model, saved = [];
        if (hide) {
          for (const id in M.parts) M.parts[id].forEach(g => {
            let up = id.startsWith('openarm') || (hide === 2 && id === 'lift_base_plate');
            for (let q = g; q && !up; q = q.parent) if (q.name === 'lift_assembly') up = true;
            if (up) g.traverse(o => { if (o.isMesh && o.userData.base) { saved.push([o, o.userData.base.opacity]); o.userData.base.opacity = 0; } });
          });
        }
        const u = window.__renderKey(k);
        saved.forEach(([o, op]) => { o.userData.base.opacity = op; });
        return u;
      }, [s.k, s.hideUpper === 2 ? 2 : !!s.hideUpper]);
      fs.writeFileSync(path.join(OUT, s.name + '.png'), Buffer.from(url.split(',')[1], 'base64'));
      console.log('wrote', s.name);
    }
    await p.close();
  }
  console.log('errors', errs.length, errs.slice(0, 5));
  await b.close();
})();
