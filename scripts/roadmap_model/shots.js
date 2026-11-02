// Screenshots of the shared roadmap model for the visual review (evidence/2026-11-02-roadmap-update).
// Each shot renders one keyframe of the exploded view (render mode, window.__renderKey): frame = component ids to fit,
// az / el (deg), zoom, r (explode), b (open base), c (cutaway), labels; bay = front bay option A or B.
//   node scripts/roadmap_model/shots.js [base URL, default http://localhost:8765/] [out dir] [name filter]
// Serve docs/assets/roadmap first: (cd docs/assets/roadmap && python3 -m http.server 8765)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765/';
const OUT = process.argv[3] || path.join(__dirname, '..', '..', 'evidence', '2026-11-02-roadmap-update');
const ONLY = process.argv[4] || '';
const BAY = ['bay_plate', 'compute', 'bay_din', 'bay_ddr240', 'bay_rsd60', 'bay_rsd100', 'bay_fbc', 'bay_usbhub', 'tz_receiver', 'lidar_support', 'lidar'];
const BAYB = BAY.map(c => (['compute', 'base_controller', 'tz_receiver', 'lidar_support', 'lidar'].includes(c) ? c : c + '_optb'));
const SHOTS = [
  // front bay option A and B: top view, side section through the receiver, opened base
  {name: 'front_bay_A_top', hideUpper: 2, bay: 'A', k: {frame: BAY, az: -90, el: 89, zoom: 1.55, c: 1, labels: ['compute', 'bay_ddr240', 'bay_din', 'bay_rsd100', 'bay_fbc', 'bay_usbhub', 'tz_receiver'], caption: 'Front bay option A (proposed): top view, cover off'}},
  {name: 'front_bay_B_top', hideUpper: 2, bay: 'B', k: {frame: BAYB, az: -90, el: 89, zoom: 1.55, c: 1, labels: ['compute', 'bay_rsd100_optb', 'bay_fbc_optb', 'bay_usbhub_optb', 'tz_receiver'], caption: 'Front bay option B (28 Oct alternative): top view, cover off'}},
  {name: 'front_bay_A_side_section', hideUpper: true, bay: 'A', k: {frame: ['tz_receiver', 'bay_plate', 'compute', 'bay_ddr240', 'lidar'], az: -90, el: 0, zoom: 0.95, c: 1, labels: ['tz_receiver', 'tz_ferrite', 'bay_ddr240', 'compute', 'lidar'], caption: 'Front bay option A: side view through the receiver (cutaway)'}},
  {name: 'front_bay_B_side_section', hideUpper: true, bay: 'B', k: {frame: ['tz_receiver', 'bay_plate_optb', 'compute', 'bay_rsd100_optb', 'lidar'], az: -90, el: 0, zoom: 0.95, c: 1, labels: ['tz_receiver', 'tz_ferrite', 'compute', 'lidar'], caption: 'Front bay option B: side view through the receiver (cutaway)'}},
  {name: 'front_bay_A_opened', bay: 'A', k: {frame: 'base', az: -35, el: 32, zoom: 0.95, b: 1, labels: ['compute', 'bay_ddr240', 'bay_din', 'tz_receiver', 'battery_tray'], caption: 'Front bay option A: opened base'}},
  {name: 'front_bay_B_opened', bay: 'B', k: {frame: 'base', az: -35, el: 32, zoom: 0.95, b: 1, labels: ['compute', 'bay_rsd100_optb', 'tz_receiver', 'battery_tray'], caption: 'Front bay option B: opened base'}},
  // TZBOT receiver with cut-out, metal-free zone and floor transmitter
  {name: 'tzbot_receiver_below', bay: 'A', k: {frame: ['tz_receiver', 'tz_metal_free_zone', 'base_cutout', 'tz_transmitter'], az: -120, el: -25, zoom: 1.6, labels: ['tz_receiver', 'base_cutout', 'tz_transmitter'], caption: 'TZBOT WCM-500-24 receiver from below: base-sheet cut-out, floor transmitter (placeholder height)'}},
  {name: 'tzbot_receiver_zone', hideUpper: true, bay: 'A', k: {frame: ['tz_receiver', 'tz_metal_free_zone', 'lidar_support', 'electronics_bracket'], az: -60, el: 20, zoom: 1.4, c: 1, labels: ['tz_receiver', 'tz_metal_free_zone', 'lidar_support', 'electronics_bracket', 'tz_ferrite'], caption: 'Receiver, ferrite sheet and 20 mm metal-free zone; MMP.07 and MMP.04.00.00.002 inside the zone (to be shortened)'}},
  // second E-stop P1 to P4
  {name: 'estop_positions_rear', bay: 'A', k: {frame: ['lift_column', 'arm_profile', 'second_estop', 'estop_p1_ghost', 'estop_p3_ghost', 'estop_p4_ghost', 'head_camera'], az: 160, el: 12, zoom: 1.05, labels: ['second_estop', 'estop_p1_ghost', 'estop_p3_ghost', 'estop_p4_ghost'], caption: 'Second E-stop: P2 drawn (proposed), P1, P3 and P4 as ghosts'}},
  {name: 'estop_p2_closeup', bay: 'A', k: {frame: ['second_estop', 'rear_estop_housing', 'head_camera_bracket'], az: 200, el: 15, zoom: 2.6, labels: ['second_estop', 'rear_estop_housing'], caption: 'P2: arm-post rear face, 55 mm below the post top, facing rearward'}},
  // lift base plate on the arch with its bolts
  {name: 'lift_base_plate_arch', bay: 'A', k: {frame: ['lift_base_plate', 'centre_bracket'], az: -30, el: 38, zoom: 1.25, c: 1, labels: ['lift_base_plate', 'centre_bracket', 'lift_column'], caption: 'Lift base plate MEC-019 on the centre-frame arch, 4 x M8 into the arch rivet nuts'}},
  {name: 'lift_base_plate_side', bay: 'A', k: {frame: ['lift_base_plate', 'centre_bracket', 'lift_column'], az: -90, el: 5, zoom: 1.1, c: 1, labels: ['lift_base_plate', 'centre_bracket'], caption: 'Lift base plate: side view, column forward of the arch centre'}},
  // rear zone, harness, Getac portrait
  {name: 'rear_zone', hideUpper: true, bay: 'A', k: {frame: ['battery_tray', 'rear_plate', 'rz_f0', 'rz_k1k2', 'rz_pre', 'rz_kchg', 'rz_fchg', 'rz_brake', 'rz_disc', 'rz_sb50', 'rz_batcon'], az: -150, el: 40, zoom: 1.15, c: 1, labels: ['battery_tray', 'rz_f0', 'rz_k1k2', 'rz_disc', 'rz_pwr017'], caption: 'Rear zone around the battery tray (FB-A, FB-B and the BMS have no space: GI-001)'}},
  {name: 'harness_front', hideUpper: true, bay: 'A', k: {frame: ['harness_sig', 'harness_bat', 'lidar', 'tz_receiver'], az: -55, el: 25, zoom: 1.1, c: 1, labels: ['harness_sig', 'harness_bat', 'lidar'], caption: 'Harness: front trunk drops below the LiDAR scan plane behind the open sector'}},
  {name: 'getac_portrait', bay: 'A', k: {frame: ['getac_pocket', 'getac_second_position_ghost', 'head_light', 'head_camera'], az: -25, el: 8, zoom: 1.3, labels: ['getac_second_position_ghost', 'head_light', 'head_camera'], caption: 'Getac pocket: portrait second position with the eccentric pivot, clear of the light bar'}},
  {name: 'exploded_assembled', bay: 'A', k: {frame: 'robot', az: -40, el: 18, caption: 'OpenAMRobot 2.0, assembled. Shared roadmap model, visualization only'}},
  {name: 'exploded_opened_base', bay: 'A', k: {frame: 'base', az: -40, el: 30, b: 1, caption: 'Opened base (front bay option A)'}},
];
(async () => {
  const b = await chromium.launch({args: ['--use-gl=angle', '--use-angle=swiftshader', '--enable-unsafe-swiftshader']});
  fs.mkdirSync(OUT, {recursive: true});
  const errs = [];
  for (const bay of ['A', 'B']) {
    const list = SHOTS.filter(s => s.bay === bay && s.name.includes(ONLY));
    if (!list.length) continue;
    const p = await b.newPage({viewport: {width: 1280, height: 720}});
    p.setDefaultTimeout(600000);
    p.on('pageerror', e => errs.push(String(e)));
    p.on('console', m => { if (m.type() === 'error') errs.push(m.text()); });
    await p.goto(BASE + 'exploded.html?render=1&frame=0&w=1280&h=720' + (bay === 'B' ? '&bay=B' : ''), {waitUntil: 'load'});
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
