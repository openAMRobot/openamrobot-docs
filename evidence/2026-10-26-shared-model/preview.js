// Preview pictures, 1920 x 1080, page UI hidden, full look unless noted. Exploded-view pictures come from the
// page's render mode (exploded.html?render=1, window.__renderKey with a pose written like a tour keyframe);
// robot-page pictures from robot.html?look=full with everything but the 3D canvas hidden.
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
  ['05_exploded_explode_robot', {frame: 'robot', r: 1, az: -40, el: 18}],
  ['06_exploded_open_base_labels', {frame: 'base', b: 1, az: -40, el: 26, labels: BASE_LABELS, names: true}],
];
const save = (f, url) => fs.writeFileSync(f, Buffer.from(url.split(',')[1], 'base64'));
(async () => {
  const [port, out, which] = process.argv.slice(2);
  const b = await chromium.launch({args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist']});
  if (!which || which === 'exploded' || which === 'light') {
    const p = await b.newPage({viewport: {width: 1920, height: 1080}}); p.setDefaultTimeout(600000);
    const light = which === 'light';
    await p.goto(`http://localhost:${port}/exploded.html?render=1&w=1920&h=1080&frame=0${light ? '&look=light' : ''}`);
    await p.waitForFunction(() => window.__renderKey);
    for (const [name, k] of light ? [['09_light_look_assembled_front_three_quarter', SHOTS[0][1]]] : SHOTS)
      save(`${out}/${name}.png`, await p.evaluate(k => window.__renderKey(k), k));
    await p.close();
  }
  if (!which || which === 'robot') {
    for (const [name, view] of [['07_robot_page_side_dark_store', 'side'], ['08_robot_page_overview_dark_store', 'over']]) {
      const p = await b.newPage({viewport: {width: 1920, height: 1080}}); p.setDefaultTimeout(900000);
      await p.goto(`http://localhost:${port}/robot.html?look=full`, {waitUntil: 'domcontentloaded'});
      await p.waitForFunction(() => window.__sim && window.__sim.robot);
      await p.addStyleTag({content: '#stage{position:fixed!important;left:0;top:0;width:1920px!important;height:1080px!important;z-index:9999;margin:0}#stage>:not(canvas){display:none!important}body{overflow:hidden}'});
      await p.evaluate(v => { const t = document.getElementById('b-tiles'); if (window.__sim.S.tiles) t.click();
        document.querySelector(`[data-view="${v}"]`).click(); }, view);
      await p.waitForTimeout(150000);
      await p.evaluate(() => window.__sim.render());
      await p.locator('#stage canvas').first().screenshot({path: `${out}/${name}.png`});
      await p.close();
    }
  }
  await b.close();
})();
