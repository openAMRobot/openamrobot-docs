// Screenshots of the harness routes, tie points and the lift energy chain (evidence/2026-11-03-harness), same renderer as shots.js.
//   node scripts/roadmap_model/harness_shots.js [base URL, default http://localhost:8765/] [out dir] [name filter]
// Serve docs/assets/roadmap first: (cd docs/assets/roadmap && python3 -m http.server 8765)
const { chromium } = require('playwright');
const fs = require('fs'), path = require('path');
const BASE = process.argv[2] || 'http://localhost:8765/';
const OUT = process.argv[3] || path.join(__dirname, '..', '..', 'evidence', '2026-11-03-harness');
const ONLY = process.argv[4] || '';
const H = ['harness_bat', 'harness_safe', 'harness_r24', 'harness_lv', 'harness_sig', 'harness_fittings', 'wheel_guards'];
const LEFT = ['side_panel_left', 'hub_motor_wheel_left', 'battery_cells_left', 'battery_tray_left', 'support_front_left', 'support_rear_left', 'castor_front_left', 'castor_rear_left'];
const CHAIN = ['lift_energy_chain', 'harness_upper', 'dp_lift', 'lift_stop_sensors', 'flag_rod', 'adapter_plate'];
const SHOTS = [
  {name: 'base_top_harness', hideUpper: 2, hideParts: ['cover', 'cover_flange_front', 'cover_flange_rear'], k: {frame: 'base', az: -90, el: 89, zoom: 1.0, c: 1, names: true, labels: ['wheel_guards', 'harness_sig', 'harness_bat', 'harness_fittings'], caption: 'Base, top view, cover off: harness routes W01 to W07 coloured by domain, tie points (dark), over-wheel guards'}},
  {name: 'base_side_harness', hideUpper: 2, hideParts: LEFT.concat(['cover', 'cover_flange_front', 'cover_flange_rear']), k: {frame: 'base', az: 90, el: 6, zoom: 1.0, c: 1, names: true, labels: ['wheel_guards', 'harness_sig', 'harness_safe'], caption: 'Base from the left, left panel, wheel and tray hidden: side trunks on the floor, over the wheel guard, beside the trays'}},
  {name: 'base_3d_harness', hideUpper: 2, hideParts: ['cover', 'cover_flange_front', 'cover_flange_rear'], k: {frame: 'base', az: -50, el: 40, zoom: 1.0, c: 1, names: true, labels: ['wheel_guards', 'harness_fittings', 'harness_bat'], caption: 'Base, cover off: harness routes and tie points'}},
  {name: 'lift_chain_L1000', k: {frame: CHAIN, az: 215, el: 4, zoom: 0.78, names: true, labels: ['lift_energy_chain', 'dp_lift', 'harness_upper', 'flag_rod'], caption: 'Lift energy chain at L1000: fixed sleeve on the column -y face, chain behind the column, moving trunk under the adapter plate'}},
  {name: 'lift_chain_L1175', lift: 0.175, k: {frame: CHAIN, az: 215, el: 4, zoom: 0.78, names: true, labels: ['lift_energy_chain'], caption: 'Lift energy chain at L1175'}},
  {name: 'lift_chain_L1350', lift: 0.35, k: {frame: CHAIN, az: 215, el: 4, zoom: 0.78, names: true, labels: ['lift_energy_chain', 'flag_rod'], caption: 'Lift energy chain at L1350: fixed run short, loop risen by half the stroke, clear of the flag rod and the cover'}},
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
      const url = await p.evaluate(([k, hide, lift, hideParts]) => {
        // hide the lift assembly and the arms for views into the base (restored after the shot)
        const M = window.__model, saved = [];
        let mov = null;
        M.root.traverse(o => { if (o.name === 'lift_assembly' && !mov) mov = o.children[0]; });
        if (lift && mov) { mov.position.z += lift; window.OAMR_MODEL.setChain(window.THREE, lift); }
        (hideParts || []).forEach(id => (M.parts[id] || []).forEach(g => g.traverse(o => { if (o.isMesh && o.userData.base) { saved.push([o, o.userData.base.opacity]); o.userData.base.opacity = 0; } })));
        if (hide) {
          for (const id in M.parts) M.parts[id].forEach(g => {
            let up = id.startsWith('openarm') || (hide === 2 && id === 'lift_base_plate');
            for (let q = g; q && !up; q = q.parent) if (q.name === 'lift_assembly') up = true;
            if (up) g.traverse(o => { if (o.isMesh && o.userData.base) { saved.push([o, o.userData.base.opacity]); o.userData.base.opacity = 0; } });
          });
        }
        const u = window.__renderKey(k);
        saved.forEach(([o, op]) => { o.userData.base.opacity = op; });
        if (lift && mov) { mov.position.z -= lift; window.OAMR_MODEL.setChain(window.THREE, 0); }
        return u;
      }, [s.k, s.hideUpper === 2 ? 2 : !!s.hideUpper, s.lift || 0, s.hideParts || []]);
      fs.writeFileSync(path.join(OUT, s.name + '.png'), Buffer.from(url.split(',')[1], 'base64'));
      console.log('wrote', s.name);
    }
    await p.close();
  }
  console.log('errors', errs.length, errs.slice(0, 5));
  await b.close();
})();
