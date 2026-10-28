/* SPDX-License-Identifier: MIT
 * OpenAMRobot 2.0 shared robot model for the roadmap pages (robot.html, exploded.html).
 *
 * One scene graph, built from:
 *  - window.BASE_GLB (model/base_glb.js): the base GLB of openamr-platform-sw
 *    tools/cad/step_to_description_meshes.py, one node per CAD part or component envelope,
 *    glTF extras id, name, class, source, bom_row, provisional; base_link frame, metres;
 *  - window.OPENARM (model/openarm.js): OpenArm 2.0 meshes and kinematics from the official
 *    openarm_description URDF (upstream licence);
 *  - the upper-body primitives below (lift base plate, lift column, adapter plate, arm profile,
 *    head camera), dimensions from openamr-upperbody-hw docs/mechanical/upper_body_option_B.md;
 *  - model/finish.json: finish colours (RAL reference, sRGB approximation) keyed by part id, and the
 *    material class of each part (physically based roughness and metalness, small procedural
 *    textures generated below at load). Without it the model keeps its previous colours and values.
 *    No geometry depends on it.
 *
 * M.build is the one entry point of both pages (robot.html and exploded.html): it returns the robot
 * as one object (root group, part groups, lift and head pivots, arm rigs, materials). The pages only
 * position it and add their own features. THREE is the namespace of model/three-r160.min.js. Every
 * part group carries userData.id, the key of COMPONENTS and of model/exploded.json.
 * Robot frame: floor origin, x forward, y left, z up (base_link 0.098 m above the floor).
 */
(function () {
  'use strict';
  var M = (window.OAMR_MODEL = {});

  // Finish colours (model/finish.json, next to this file). Read synchronously because the pages build
  // the model right after this script; on any failure the finish is empty and nothing is recoloured.
  M.FINISH = (function () {
    try {
      var s = document.currentScript, url = (s && s.src ? s.src.replace(/[^/]*$/, '') : 'model/') + 'finish.json';
      var x = new XMLHttpRequest();
      x.open('GET', url, false);
      x.send(null);
      return x.status === 200 || (x.status === 0 && x.responseText) ? JSON.parse(x.responseText) : null;
    } catch (e) { return null; }
  })();
  // {color, roughness, metalness} of a part id, or null when finish.json does not name it.
  M.finishOf = function (id) {
    var f = M.FINISH, p = f && f.parts && f.parts[id], c = p && f.colours[p.ral], k = p && f.finishes[p.finish];
    return c && k ? {color: parseInt(c.srgb.slice(1), 16), roughness: k.roughness, metalness: k.metalness} : null;
  };
  // Material class of part id (primitive prim of a GLB node, or a named sub-part), or null.
  M.classOf = function (id, prim) {
    var c = M.FINISH && M.FINISH.class_of && M.FINISH.class_of[id];
    if (!c || typeof c === 'string') return c || null;
    return c[String(prim)] || c['*'] || null;
  };
  var classDef = function (cls) { return (cls && M.FINISH && M.FINISH.classes && M.FINISH.classes[cls]) || null; };

  // Procedural textures of the material classes: tileable, at most 256 x 256, generated once at load
  // from a fixed seed (the same pixels on every load), linear data (normal and roughness maps).
  var TEX = {}, BRUSH_MEAN = .9;
  function lattice(n, cells, seed) {  // tileable value noise, n x n samples, cells x cells lattice
    var g = [], out = new Float32Array(n * n), i, x, y;
    for (i = 0; i < cells * cells; i++) g.push((seed = seed * 16807 % 2147483647) / 2147483647);
    for (y = 0; y < n; y++) for (x = 0; x < n; x++) {
      var fx = x * cells / n, fy = y * cells / n, x0 = Math.floor(fx), y0 = Math.floor(fy), tx = fx - x0, ty = fy - y0;
      var x1 = (x0 + 1) % cells, y1 = (y0 + 1) % cells, a = g[y0 * cells + x0], b = g[y0 * cells + x1];
      var c = g[y1 * cells + x0], d = g[y1 * cells + x1];
      tx = tx * tx * (3 - 2 * tx);
      ty = ty * ty * (3 - 2 * ty);
      out[y * n + x] = a + (b - a) * tx + (c - a) * ty + (a - b - c + d) * tx * ty;
    }
    return out;
  }
  function dataTexture(THREE, px, n) {
    var t = new THREE.DataTexture(px, n, n, THREE.RGBAFormat);
    t.wrapS = t.wrapT = THREE.RepeatWrapping;
    t.magFilter = THREE.LinearFilter;
    t.minFilter = THREE.LinearMipmapLinearFilter;
    t.generateMipmaps = true;
    t.colorSpace = THREE.NoColorSpace;
    t.needsUpdate = true;
    return t;
  }
  function normalMap(THREE, h, n, k) {  // height field (tileable) to a tangent-space normal map
    var px = new Uint8Array(n * n * 4);
    for (var y = 0; y < n; y++) for (var x = 0; x < n; x++) {
      var dx = (h[y * n + (x + 1) % n] - h[y * n + (x + n - 1) % n]) * k;
      var dy = (h[(y + 1) % n * n + x] - h[(y + n - 1) % n * n + x]) * k, l = Math.sqrt(dx * dx + dy * dy + 1), i = (y * n + x) * 4;
      px[i] = Math.round((-dx / l * .5 + .5) * 255);
      px[i + 1] = Math.round((-dy / l * .5 + .5) * 255);
      px[i + 2] = Math.round((1 / l * .5 + .5) * 255);
      px[i + 3] = 255;
    }
    return dataTexture(THREE, px, n);
  }
  M.texture = function (THREE, name) {
    if (TEX[name]) return TEX[name];
    var n, h, i, a, b;
    if (name === 'orange_peel') {  // powder coat: two octaves of soft bumps, about 1.2 and 0.6 mm
      n = 256;
      a = lattice(n, 24, 7);
      b = lattice(n, 48, 11);
      h = new Float32Array(n * n);
      for (i = 0; i < h.length; i++) h[i] = .65 * a[i] + .35 * b[i];
      return (TEX[name] = normalMap(THREE, h, n, 6));
    }
    if (name === 'layer_lines') {  // print layers: 16 ridges per tile along v, a little noise
      n = 64;
      a = lattice(n, 8, 5);
      h = new Float32Array(n * n);
      for (i = 0; i < h.length; i++) h[i] = .5 + .5 * Math.cos(2 * Math.PI * 16 * Math.floor(i / n) / n) + .15 * a[i];
      return (TEX[name] = normalMap(THREE, h, n, 1.2));
    }
    if (name === 'brushed') {  // roughness map, streaks along v; values 0.8 to 1 (mean BRUSH_MEAN) scale the class roughness
      n = 256;
      a = lattice(n, 4, 3);
      var px = new Uint8Array(n * n * 4), col = [], s = 13;
      for (i = 0; i < n; i++) col.push((s = s * 16807 % 2147483647) / 2147483647);
      for (i = 0; i < n * n; i++) {
        var x = i % n, v = .8 + .2 * (.55 * col[x] + .25 * col[(x + 1) % n] + .2 * a[i]);
        px[i * 4] = px[i * 4 + 1] = px[i * 4 + 2] = Math.round(v * 255);
        px[i * 4 + 3] = 255;
      }
      return (TEX[name] = dataTexture(THREE, px, n));
    }
    return null;
  };

  // A material of class cls (finish.json classes) with colour hex, plus extra material parameters.
  // A class with clearcoat or specular gives a MeshPhysicalMaterial, else a MeshStandardMaterial. userData.tile
  // (metres per texture tile) tells M.prepare to give the meshes planar texture coordinates.
  M.classMaterial = function (THREE, cls, color, extra) {
    var c = classDef(cls) || {}, p = {color: c.srgb ? parseInt(c.srgb.slice(1), 16) : color, roughness: c.roughness, metalness: c.metalness};
    if (c.normal_map) {
      p.normalMap = M.texture(THREE, c.normal_map);
      p.normalScale = new THREE.Vector2(c.normal_scale, c.normal_scale);
    }
    if (c.roughness_map) {
      p.roughnessMap = M.texture(THREE, c.roughness_map);
      p.roughness = c.roughness / BRUSH_MEAN;  // the map averages BRUSH_MEAN, so the mean roughness is the class value
    }
    if (c.clearcoat !== undefined) {
      p.clearcoat = c.clearcoat;
      if (c.clearcoat_roughness !== undefined) p.clearcoatRoughness = c.clearcoat_roughness;
    }
    if (c.specular !== undefined) p.specularIntensity = c.specular;
    var phys = c.clearcoat !== undefined || c.specular !== undefined;
    var m = new (phys ? THREE.MeshPhysicalMaterial : THREE.MeshStandardMaterial)(Object.assign(p, extra || {}));
    m.userData.cls = cls;
    if (c.tile_m) m.userData.tile = c.tile_m;
    if (c.env_scale) m.userData.envScale = c.env_scale;  // environment intensity relative to the page value (look.js robotEnv)
    return m;
  };

  var finished = {};
  // A material for part id: the finish colour of finish.json if it names the part (with the values of
  // its material class, else of its finish), else the given material.
  function finishMat(THREE, id, fallback) {
    var f = M.finishOf(id), cls = M.classOf(id);
    if (!f) return fallback;
    return (finished[id] = finished[id] || (cls ? M.classMaterial(THREE, cls, f.color) : new THREE.MeshStandardMaterial(f)));
  }

  // Planar texture coordinates (metres / tile, projected along the dominant normal axis: u, v = y, z or
  // x, z on the sides, x, y on top) for meshes whose material has a texture tile. Positions, normals and
  // indices are unchanged; only the uv attribute is set. Runs once per geometry.
  M.prepare = function (THREE, obj) {
    obj.traverse(function (o) {
      var g = o.isMesh && o.geometry, t = o.isMesh && o.material && o.material.userData && o.material.userData.tile;
      if (!t || g.userData.uvTile === t || !g.attributes.normal) return;
      var p = g.attributes.position, nr = g.attributes.normal, uv = new Float32Array(p.count * 2);
      for (var i = 0; i < p.count; i++) {
        var ax = Math.abs(nr.getX(i)), ay = Math.abs(nr.getY(i)), az = Math.abs(nr.getZ(i));
        var u = ax >= ay && ax >= az ? p.getY(i) : p.getX(i), v = az > ax && az > ay ? p.getY(i) : p.getZ(i);
        uv[i * 2] = u / t;
        uv[i * 2 + 1] = v / t;
      }
      g.setAttribute('uv', new THREE.BufferAttribute(uv, 2));
      g.userData.uvTile = t;
    });
  };

  // Design values used by the geometry and by the robot page simulation (P-03 rev19.7, register).
  M.DIMS = {X0: -.39, X1: .39, HW: .291, DECK: .294, COVER: .296, BELLY: .052, WHEEL_R: .1, WHEEL_Y: .2,
    CASTER: [[.27505, .215], [.27505, -.215], [-.27495, .215], [-.27495, -.215]], PLATE_T: .01, PLATE_TOP: .304,
    BP: {bp000: .06, bp050: .11},
    COL: {L: .24, W: .06, RETRACTED: .53, STROKE: .35, HEAD: .012, MASS: 11.7, PUSH: 800, PULL: 400, SPEED: .018,
      M_LONG_STAT: 1200, M_LONG_DYN: 500, M_LAT_STAT: 450, M_LAT_DYN: 225},
    MOUNT_ABOVE_COL: .166, MOUNT_X: .18, PROFILE: {X: .12, Y: .06, L: .34, ADAPTER: .01}, MOUNT_Y: .031,
    STOPS: {L1000: 1, L1175: 1.175, L1350: 1.35}, BASE_LINK_Z: .098, GEMINI: {x: .387, z: .046}, LIDAR_X: .33,
    LIDAR_Z: .22205, IMU: {x: .0544, z: .121, yaw: -90}, TOF_X: .39, US_XF: .39, US_XR: -.39, NEAR_Z: .0914,
    US_Y: .13, ZED_ABOVE_SH: .223, ZED_X: .202};

  // Arm pose of the assembled view (joint angles, rad); the right arm mirrors the left.
  var mirror = function (q) { return [-q[0], -q[1], -q[2], q[3], -q[4], -q[5], -q[6]]; };
  M.ARM_POSE = {left: [.25, -.12, 0, 1.9, 0, -.78, 0], right: mirror([.25, -.12, 0, 1.9, 0, -.78, 0])};
  M.ARM_GRIP = .6;

  var HW = 'https://github.com/openAMRobot/openamr-platform-hw/';
  var SW = 'https://github.com/openAMRobot/openamr-platform-sw/';
  var UB = 'https://github.com/openAMRobot/openamr-upperbody-hw/';
  M.LINKS = {PROVENANCE: SW + 'blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml',
    OPTION_B: UB + 'blob/main/docs/mechanical/upper_body_option_B.md', HW: HW, SW: SW, UB: UB};

  // Component registry: one entry per numbered item of the component list. geometry: cad (CAD-derived
  // mesh), envelope (simplified component volume), primitive (drawn from decided dimensions) or none
  // (not drawn). nodes: GLB node ids; parts: upper-body part ids. Parsed by scripts/check_roadmap.py.
  M.COMPONENTS = /*COMPONENTS-JSON*/[
{"id":"base_plate","name":"Base plate (deck)","qty":1,"geometry":"cad","bom":"MEC-001","purpose":"Steel deck that carries the drive, castors, electronics and battery.","source":"CAD v0.2 part MMP.02.00.00.001 (openamr-platform-hw full-assembly STEP, placement corrected in the converter)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.02.00.00.001%20Base.STEP","nodes":["base_plate"]},
{"id":"front_panel","name":"Front panel (Rev B)","qty":1,"geometry":"cad","bom":"MEC-001","purpose":"Front closure with the camera slot and the front sensor holes.","source":"CAD v0.2 part MMP.00.00.00.001","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.00.00.00.001%20Front%20panel.STEP","nodes":["front_panel"]},
{"id":"rear_panel","name":"Rear panel (Rev B)","qty":1,"geometry":"cad","bom":"MEC-001","purpose":"Rear closure with the rear sensor holes.","source":"CAD v0.2 part MMP.00.00.00.002","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.00.00.00.002%20Back%20panel.STEP","nodes":["rear_panel"]},
{"id":"side_panel","name":"Side panel","qty":2,"geometry":"cad","bom":"MEC-001","purpose":"Left and right closures of the base.","source":"CAD v0.2 part MMP.00.00.00.003","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.00.00.00.003%20Side%20panel.STEP","nodes":["side_panel_left","side_panel_right"]},
{"id":"support","name":"Corner support","qty":4,"geometry":"cad","bom":"MEC-001","purpose":"Corner posts between the deck and the cover.","source":"CAD v0.2 part MMP.05.00.00.001 (two mirrored variants)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.05.00.00.001%20Support.STEP","nodes":["support_front_left","support_front_right","support_rear_left","support_rear_right"]},
{"id":"centre_bracket","name":"Centre bracket","qty":1,"geometry":"cad","bom":"MEC-001","purpose":"Cross member between the deck and the cover.","source":"CAD v0.2 part MMP.04.00.00.001","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.04.00.00.001%20Center%20bracket.STEP","nodes":["centre_bracket"]},
{"id":"hub_motor_wheel","name":"Hub motor wheel with brake","qty":2,"geometry":"envelope","bom":"DRV-001","purpose":"ZLTECH ZLLG80ASM250-L-B drive wheels, brake side inboard; track 0.400 m is a placeholder.","source":"PROVENANCE.yaml components.hub_motor_wheel (revolved profile from the ZLLG80ASM250-L-B2 STEP)","link":"https://github.com/openAMRobot/openamr-platform-hw/tree/main/datasheets/ZLTech/wheel_ZLLG80ASM250","nodes":["hub_motor_wheel_left","hub_motor_wheel_right"]},
{"id":"castor","name":"Swivel castor","qty":4,"geometry":"envelope","bom":"MEC-002","purpose":"LPA-VSTH 35K castors at the four corners of the deck.","source":"PROVENANCE.yaml components.castor","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["castor_front_left","castor_front_right","castor_rear_left","castor_rear_right"]},
{"id":"motor_driver","name":"Motor driver","qty":1,"geometry":"envelope","bom":"DRV-002","purpose":"ZLAC8015D V4.2 dual-channel driver for the two hub motors (CAN1).","source":"PROVENANCE.yaml components.motor_driver (as in the CAD)","link":"https://github.com/openAMRobot/openamr-platform-hw/tree/main/datasheets/ZLTech/drivers","nodes":["motor_driver"]},
{"id":"driver_mount","name":"Motor driver mount","qty":1,"geometry":"cad","bom":"","purpose":"Holds the motor driver on the deck.","source":"CAD v0.2 instance driver_mount v2 (production file MMP.02.00.00.002)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.02.00.00.002%20Motor%20driver%20mount.STEP","nodes":["driver_mount"]},
{"id":"battery","name":"Battery cell-group envelope","qty":1,"geometry":"envelope","provisional":true,"label":"Cell-group envelope, provisional (not the complete battery assembly)","bom":"PWR-001, PWR-028","purpose":"Eight EVE LF105 cells upright in one row across the robot (8S1P LiFePO4), on the rear deck with the front face 2 mm behind the centre bracket. Not the complete battery assembly: the BMS, power distribution board, pack fuse, terminals and wiring are not drawn and are never on top of the cells; they go in the BMS and power distribution zone behind it.","source":"PROVENANCE.yaml components.battery: cell-group envelope 314 (y) x 140 (x) x 210 (z) mm (cell layout plus 5 mm per outer face), position computed by the openamr-platform-sw converter (project-lead decision of 25 Oct 2026)","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["battery"]},
{"id":"safety_relay_set","name":"Safety relay, contactors, main fuse and disconnect","qty":1,"geometry":"none","bom":"SAF-002, SAF-003, PWR-003, PWR-004","purpose":"Hardwired safety chain and main power protection.","source":"PROVENANCE.yaml components.safety_relay_set (not modelled)","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml"},
{"id":"estop","name":"Base E-stop","qty":1,"geometry":"envelope","placeholder":true,"label":"Placeholder from datasheet dimensions (Schneider STEP not yet read)","bom":"SAF-001","purpose":"One of the two E-stop buttons of the robot, in the front-panel hole of the release 001 E-stop on the robot left (+y).","source":"PROVENANCE.yaml components.estop: placeholder geometry centred on the release 001 button hole axis at x 390.0, y +130.0, z 44.5 mm in base_link (P-03 rev20.0 item 24; openamr-platform-sw PR #100 at 1939b82)","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["estop"]},
{"id":"reset_button","name":"RESET button","qty":1,"geometry":"envelope","placeholder":true,"label":"Placeholder from datasheet dimensions (Schneider STEP not yet read)","bom":"SAF-005","purpose":"The only RESET button of the safety chain, in the front-panel hole of the release 001 start button on the robot right (-y).","source":"PROVENANCE.yaml components.reset_button: placeholder geometry centred on the release 001 button hole axis at x 390.0, y -130.0, z 44.5 mm in base_link (P-03 rev20.0 items 20 and 24; openamr-platform-sw PR #100 at 1939b82)","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["reset_button"]},
{"id":"wireless_charging_receiver","name":"Wireless charging receiver","qty":1,"geometry":"none","bom":"WCH-002","purpose":"TZBOT WCM-500-24 receiver for normal charging.","source":"PROVENANCE.yaml components.wireless_charging_receiver (not modelled)","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml"},
{"id":"electronics_bracket","name":"Electronics bracket","qty":1,"geometry":"cad","bom":"","purpose":"Carries the compute module and the base controller above the deck.","source":"CAD v0.2 instance electronics_bracket v19 (production file MMP.04.00.00.002)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.04.00.00.002%20Electronics%20bracket.STEP","nodes":["electronics_bracket"]},
{"id":"compute","name":"Compute (Jetson Orin NX on J401 carrier)","qty":1,"geometry":"envelope","bom":"CMP-001, CMP-002","purpose":"Runs the ROS 2 software of the robot.","source":"PROVENANCE.yaml components.compute (as in the CAD; heatsink kit not in the CAD)","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["compute"]},
{"id":"controller_plate","name":"Base controller mount plate","qty":1,"geometry":"cad","bom":"","purpose":"Holds the base controller board.","source":"CAD v0.2 instance stm32_click_mount_plate (production file MMP.04.00.00.003)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.04.00.00.003%20STM32%20Click%20mount%20plate.STEP","nodes":["controller_plate"]},
{"id":"base_controller","name":"Base controller","qty":1,"geometry":"envelope","bom":"CTL-001","purpose":"NUCLEO-H723ZG board for drive, sensors and IMU (Gate B).","source":"PROVENANCE.yaml components.base_controller (board outline only)","link":"https://github.com/openAMRobot/openamr-platform-hw/tree/main/datasheets/STMicroelectronics/STM32H723ZG","nodes":["base_controller"]},
{"id":"imu","name":"IMU","qty":1,"geometry":"envelope","bom":"IMU-001","purpose":"ICM-42688-P on a MIKROE-4237 click board.","source":"PROVENANCE.yaml components.imu","link":"https://github.com/openAMRobot/openamr-platform-hw/tree/main/datasheets/TDK/ICM-42688-P","nodes":["imu"]},
{"id":"lidar_support","name":"LiDAR support","qty":1,"geometry":"cad","bom":"MEC-008","purpose":"Bracket that carries the LiDAR above the deck.","source":"CAD v0.2 part MMP.07.00.00.001","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.07.00.00.001%20Lidar%20support.STEP","nodes":["lidar_support"]},
{"id":"lidar_spacer","name":"LiDAR spacer 17.5 mm","qty":1,"geometry":"cad","bom":"MEC-008","purpose":"Sets the scan plane at 222.05 mm above the floor.","source":"CAD v0.2 instance lidar_mount_spacer (production file MMP.07.00.00.002)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.07.00.00.002%20Lidar%20mount%20spacer.STEP","nodes":["lidar_spacer"]},
{"id":"lidar","name":"2D LiDAR","qty":1,"geometry":"envelope","bom":"NAV-001","purpose":"SLAMTEC RPLIDAR S3 for navigation.","source":"PROVENANCE.yaml components.lidar","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["lidar"]},
{"id":"camera_mount","name":"Base camera mount","qty":1,"geometry":"cad","bom":"MEC-009","purpose":"Printed mount behind the front-panel camera slot.","source":"CAD v0.2 part MMP.01.00.00.003","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.01.00.00.003%20Camera%20mount.STEP","nodes":["camera_mount"]},
{"id":"base_camera","name":"Base RGB-D camera","qty":1,"geometry":"envelope","bom":"CAM-001","purpose":"Orbbec Gemini 336L, 10 degrees up-tilt baseline.","source":"PROVENANCE.yaml components.base_camera","link":"https://github.com/openAMRobot/openamr-platform-sw/blob/main/ros2/src/openamrobot_description/meshes/PROVENANCE.yaml","nodes":["base_camera"]},
{"id":"ultrasonic_mount","name":"Ultrasonic mount","qty":4,"geometry":"cad","bom":"MEC-011","purpose":"Holds one ultrasonic sensor at each panel edge hole.","source":"CAD v0.2 instance ultrasonic_mount_ v1 (production file MMP.00.00.00.006)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.00.00.00.006%20Ultrasonic%20mount.STEP","nodes":["ultrasonic_mount_front_left","ultrasonic_mount_front_right","ultrasonic_mount_rear_left","ultrasonic_mount_rear_right"]},
{"id":"ultrasonic","name":"Ultrasonic sensor","qty":4,"geometry":"envelope","bom":"SNS-002","purpose":"MaxBotix MB7060 near-field sensors in the front and rear edge holes.","source":"PROVENANCE.yaml components.ultrasonic","link":"https://github.com/openAMRobot/openamr-platform-hw/tree/main/datasheets/MaxBotix/MB7060","nodes":["ultrasonic_front_left","ultrasonic_front_right","ultrasonic_rear_left","ultrasonic_rear_right"]},
{"id":"tof_mount","name":"ToF sensor mount","qty":2,"geometry":"cad","bom":"","purpose":"Holds one cliff sensor behind each panel centre hole.","source":"CAD v0.2 instance tf_luna_mount (production file MMP.00.00.00.005)","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.00.00.00.005%20TF-Luna%20mount.STEP","nodes":["tof_mount_front","tof_mount_rear"]},
{"id":"tof","name":"ToF cliff sensor","qty":2,"geometry":"envelope","bom":"SNS-001","purpose":"Benewake TF-Luna sensors in the front and rear centre holes.","source":"PROVENANCE.yaml components.tof (URDF frame on platform-sw main)","link":"https://github.com/openAMRobot/openamr-platform-hw/tree/main/datasheets/Benewake/TF-Luna","nodes":["tof_front","tof_rear"]},
{"id":"cover","name":"Cover","qty":1,"geometry":"cad","bom":"MEC-001","purpose":"Top cover of the base; the lift base plate stands on it.","source":"CAD v0.2 part MMP.01.00.00.001","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.01.00.00.001%20Cover.STEP","nodes":["cover"]},
{"id":"cover_flange","name":"Cover flange","qty":2,"geometry":"cad","bom":"MEC-001","purpose":"Front and rear sloped ends of the cover.","source":"CAD v0.2 part MMP.01.00.00.002","link":"https://github.com/openAMRobot/openamr-platform-hw/blob/main/mechanical/cad/production_files/MMP.01.00.00.002%20Cover%20flange.STEP","nodes":["cover_flange_front","cover_flange_rear"]},
{"id":"lift_base_plate","name":"Lift base plate","qty":1,"geometry":"primitive","bom":"MEC-019","purpose":"10 mm aluminium plate with two fore-aft positions (bp000 shown).","source":"openamr-upperbody-hw option B (P-03 rev19.0 items 16 to 19): top face 304 mm; outline drawn 300 x 100 mm, drawing pending","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["lift_base_plate"]},
{"id":"lift_column","name":"Lift column","qty":1,"geometry":"primitive","bom":"MEC-018","purpose":"DOLD Hexalift V4, 350 mm stroke, 530 mm retracted, 240 mm side fore-aft.","source":"openamr-upperbody-hw option B; lift column CAD not yet available, lateral width drawn 60 mm","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["lift_column"]},
{"id":"adapter_plate","name":"Adapter plate","qty":1,"geometry":"primitive","bom":"MEC-004","purpose":"10 mm plate on the column top that carries the arm profile.","source":"openamr-upperbody-hw option B; drawing pending","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["adapter_plate"]},
{"id":"arm_profile","name":"Arm profile HFS6-60120","qty":1,"geometry":"primitive","bom":"MEC-003","purpose":"MISUMI HFS6-60120, 340 mm, carries the two arm mounts (J1_A plate outline pending).","source":"openamr-upperbody-hw option B","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["arm_profile"]},
{"id":"slot_cover_strips","name":"Slot cover strips","qty":2,"geometry":"primitive","bom":"","purpose":"Two thin cosmetic strips in the front-most slot of each side face of the arm profile, above the arm mounts, about 85 mm long; colour from model/finish.json.","source":"Primitive drawn on the arm profile of option B; colour RAL 5018 (cyan reference) from model/finish.json","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["slot_cover_strips"]},
{"id":"openarm","name":"OpenArm 2.0 arm","qty":2,"geometry":"cad","bom":"ARM-001","purpose":"Two 7-axis arms with grippers, mounted 180 mm ahead of the column axis.","source":"OpenArm 2.0 meshes and kinematics from the upstream openarm_description URDF; mount point per option B","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["openarm_left","openarm_right"]},
{"id":"head_camera_bracket","name":"Head camera bracket","qty":1,"geometry":"primitive","bom":"ARM-011","purpose":"Pitch bracket on the profile top; supplier mount fit to be confirmed.","source":"openamr-upperbody-hw option B (camera body and bracket height pending supplier CAD)","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["head_camera_bracket"]},
{"id":"head_camera","name":"Head stereo camera","qty":1,"geometry":"primitive","bom":"ARM-003","purpose":"Stereolabs ZED Mini, lens 22 mm ahead of and 223 mm above the shoulder, 25 degrees down baseline.","source":"openamr-upperbody-hw option B","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md","parts":["head_camera"]},
{"id":"arm_kit_estop","name":"Arm kit E-stop","qty":1,"geometry":"none","bom":"ARM-008","purpose":"The second of the two E-stop buttons of the robot, supplied with the arm kit.","source":"BOM Issue 7.11 ARM-008; no position in the 2.0 documentation","link":"https://github.com/openAMRobot/openamr-upperbody-hw/blob/main/docs/mechanical/upper_body_option_B.md"}
]/*COMPONENTS-JSON-END*/;

  // The robot materials that are not per part (the GLB nodes get theirs in M.base). alu, aluDark and anod:
  // aluminium of the lift column, lift stage and head bracket (class of lift_column, satin); lens: ZED Mini lenses (sensor glass class);
  // arm: OpenArm 2.0 vertex colours as delivered, one material for both arms (no highlight tint). steel, slot,
  // black and the robot page fittings (skirt, red, yellow, cable, resetLit) keep their values.
  M.materials = function (THREE) {
    var S = THREE.MeshStandardMaterial, A = M.classOf('lift_column') || 'anodised_aluminium';
    return {skirt: new S({color: 2830391, roughness: .55}),
      black: new S({color: 1382428, roughness: .35, metalness: .2}),
      steel: new S({color: 4869973, roughness: .45, metalness: .7}), alu: M.classMaterial(THREE, A, 13225426),
      aluDark: M.classMaterial(THREE, A, 10133671), anod: M.classMaterial(THREE, A, 14146270),
      slot: new S({color: 2895926, roughness: .6, metalness: .3}),
      red: new S({color: 14164767, roughness: .35}), yellow: new S({color: 15909376, roughness: .45}),
      resetLit: new S({color: 2056145, emissive: 732282, emissiveIntensity: .6, roughness: .3}),
      lens: M.classMaterial(THREE, M.classOf('head_camera', 'lens') || 'sensor_glass', 329224),
      cable: new S({color: 1711135, roughness: .6}),
      arm: M.classMaterial(THREE, 'openarm_as_delivered', 16777215, {vertexColors: true, side: THREE.DoubleSide})};
  };

  function bytes(b64) {
    var s = atob(b64), n = s.length, u = new Uint8Array(n);
    for (var i = 0; i < n; i++) u[i] = s.charCodeAt(i);
    return u;
  }

  // Base GLB: a group "base_cad" in base_link (the caller sets z = BASE_LINK_Z) with one child group
  // per GLB node (name = id, userData = extras), one mesh per primitive. Provisional envelopes are
  // drawn at 35 % opacity; a primitive whose GLB material has alpha under 1 (the battery envelope
  // shell) is drawn at that alpha and marked userData.shell. Each primitive takes the material class
  // finish.json gives it (M.classOf(node id, primitive index)) and the finish colour of its node, if any.
  M.base = function (THREE, b64) {
    var t = bytes((b64 || window.BASE_GLB).replace(/\./g, ''));
    var jl = new DataView(t.buffer).getUint32(12, true);
    var doc = JSON.parse(new TextDecoder().decode(t.subarray(20, 20 + jl))), bin = 28 + jl;
    var root = new THREE.Group();
    root.name = 'base_cad';
    var slice = function (view) { return t.buffer.slice(bin + view.byteOffset, bin + view.byteOffset + view.byteLength); };
    doc.nodes.forEach(function (node) {
      if (node.mesh === undefined) return;
      var g = new THREE.Group(), ex = node.extras || {id: node.name};
      g.name = ex.id;
      g.userData = Object.assign({id: ex.id, part: true}, ex);
      doc.meshes[node.mesh].primitives.forEach(function (p, pi) {
        var pa = doc.accessors[p.attributes.POSITION], ia = doc.accessors[p.indices];
        var geo = new THREE.BufferGeometry();
        geo.setAttribute('position', new THREE.BufferAttribute(new Float32Array(slice(doc.bufferViews[pa.bufferView])), 3));
        var ib = slice(doc.bufferViews[ia.bufferView]);
        geo.setIndex(new THREE.BufferAttribute(ia.componentType === 5123 ? new Uint16Array(ib) : new Uint32Array(ib), 1));
        geo = geo.toNonIndexed();
        geo.computeVertexNormals();
        geo.computeBoundingSphere();
        var c = doc.materials[p.material].pbrMetallicRoughness.baseColorFactor;
        var hex = Math.round(c[0] * 255) << 16 | Math.round(c[1] * 255) << 8 | Math.round(c[2] * 255);
        var fin = M.finishOf(ex.id), cls = M.classOf(ex.id, pi), def = classDef(cls), mat;  // finish.json colour and class
        if (def && !def.keep) mat = M.classMaterial(THREE, cls, fin ? fin.color : hex);
        else {
          mat = new THREE.MeshStandardMaterial({color: hex, roughness: .6, metalness: .15});
          if (fin) { mat.color.setHex(fin.color); mat.roughness = fin.roughness; mat.metalness = fin.metalness; }
        }
        var shell = c[3] !== undefined && c[3] < 1;
        if (ex.provisional || shell) {
          mat.transparent = true;
          mat.opacity = shell ? Math.min(c[3], .35) : .35;
          mat.depthWrite = false;
        }
        var mesh = new THREE.Mesh(geo, mat);
        if (shell) mesh.userData.shell = true;
        mesh.name = ex.id;
        mesh.castShadow = !ex.provisional;
        mesh.receiveShadow = true;
        if (ex.provisional) mesh.renderOrder = 2;
        g.add(mesh);
      });
      root.add(g);
    });
    return root;
  };

  // OpenArm geometries keyed by mesh path (int16 positions with scale q, uint8 vertex colours).
  M.armGeometries = function (THREE) {
    var out = {}, src = window.OPENARM.meshes;
    for (var k in src) {
      var e = src[k], b = bytes(e.pos), p = new Int16Array(b.buffer), n = new Float32Array(p.length);
      for (var i = 0; i < p.length; i++) n[i] = p[i] * e.q;
      var g = new THREE.BufferGeometry();
      g.setAttribute('position', new THREE.BufferAttribute(n, 3));
      g.setAttribute('color', new THREE.BufferAttribute(bytes(e.col), 3, true));
      g.computeVertexNormals();
      g.computeBoundingSphere();
      out[k] = g;
    }
    return out;
  };

  function xyzrpy(THREE, s, e) {
    var m = new THREE.Matrix4();
    m.makeRotationFromEuler(new THREE.Euler(e[0], e[1], e[2], 'ZYX'));
    m.setPosition(s[0], s[1], s[2]);
    return m;
  }

  // One arm as a group "openarm_<side>" of link groups (matrix set by the caller, matrixAutoUpdate off):
  // gBase, gLinks (seven joints) and fingers[i].g, each holding its visual mesh at the URDF visual origin.
  M.armRig = function (THREE, side, geos, mats) {
    var a = window.OPENARM.arms[side], grp = new THREE.Group();
    grp.name = 'openarm_' + side;
    grp.userData = {id: 'openarm_' + side, part: true};
    var link = function (v) {
      var g = new THREE.Group();
      g.matrixAutoUpdate = false;
      if (v && geos[v.key]) {
        var mesh = new THREE.Mesh(geos[v.key], mats.arm);
        mesh.castShadow = mesh.receiveShadow = true;
        mesh.matrixAutoUpdate = false;
        mesh.matrix.copy(xyzrpy(THREE, v.xyz, v.rpy)).multiply(new THREE.Matrix4().makeScale(v.scale[0], v.scale[1], v.scale[2]));
        g.add(mesh);
      }
      grp.add(g);
      return g;
    };
    return {group: grp, gBase: link(a.base_visual), gLinks: a.joints.map(function (j) { return link(j.visual); }),
      fingers: a.fingers.map(function (f) { return {g: link(f.visual)}; })};
  };

  // Pose an arm rig at joint angles q and grip (0 closed to 1 open), in the robot frame (lift at shoulder
  // height sh, column axis at bpX); the same forward kinematics as the robot page simulation.
  M.poseArm = function (THREE, rig, side, q, grip, sh, bpX) {
    var D = M.DIMS, a = window.OPENARM.arms[side];
    q = q || M.ARM_POSE[side];
    grip = grip === undefined ? M.ARM_GRIP : grip;
    sh = sh === undefined ? D.STOPS.L1000 : sh;
    bpX = bpX === undefined ? D.BP.bp000 : bpX;
    var l = new THREE.Matrix4().makeTranslation(bpX, 0, sh).multiply(xyzrpy(THREE, [D.MOUNT_X, a.mount.xyz[1], 0], a.mount.rpy));
    rig.gBase.matrix.copy(l);
    var r = new THREE.Matrix4();
    a.joints.forEach(function (j, i) {
      l.multiply(xyzrpy(THREE, j.xyz, j.rpy));
      l.multiply(r.makeRotationAxis(new THREE.Vector3().fromArray(j.axis).normalize(), q[i]));
      rig.gLinks[i].matrix.copy(l);
    });
    a.fingers.forEach(function (f, i) {
      var lim = Math.abs(f.lo) > Math.abs(f.hi) ? f.lo : f.hi;
      rig.fingers[i].g.matrix.copy(l).multiply(xyzrpy(THREE, f.xyz, f.rpy))
        .multiply(new THREE.Matrix4().makeRotationAxis(new THREE.Vector3().fromArray(f.axis).normalize(), lim * grip));
    });
    rig.group.traverse(function (o) { o.matrixWorldNeedsUpdate = true; });
  };

  // Upper-body primitives, added to the caller's groups: fixed (on the lift base plate, x at the column
  // axis), moving (the lift stage, z offset = lift travel) and zed (head camera pivot on the lens line).
  // Returns {part id: [groups]}; a part may sit in more than one parent (the lift column).
  M.upperBody = function (THREE, parents, mats) {
    var D = M.DIMS, e = D.COL, t = D.PLATE_TOP, h = D.PROFILE, out = {};
    var part = function (parent, id) {
      var g = new THREE.Group();
      g.name = id;
      g.userData = {id: id, part: true};
      parent.add(g);
      (out[id] = out[id] || []).push(g);
      return g;
    };
    var box = function (g, x, y, z, m, px, py, pz, name) {
      var c = new THREE.Mesh(new THREE.BoxGeometry(x, y, z), m);
      c.position.set(px, py, pz);
      c.castShadow = c.receiveShadow = true;
      if (name) c.name = name;
      g.add(c);
      return c;
    };
    var rbox = function (g, x, y, z, r, m, px, py, pz) {
      var c = new THREE.Mesh(new THREE.RoundedBoxGeometry(x, y, z, 3, r), m);
      c.position.set(px, py, pz);
      c.castShadow = c.receiveShadow = true;
      g.add(c);
      return c;
    };
    var cyl = function (g, r, len, m, px, py, pz, axis, seg) {
      var c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), m);
      c.castShadow = true;
      if (axis === 'x') c.rotation.z = Math.PI / 2; else if (axis === 'z') c.rotation.x = Math.PI / 2;
      c.position.set(px, py, pz);
      g.add(c);
      return c;
    };
    var slots = function (g, x, y, len, z) {
      for (var s = -1; s <= 1; s += 2) {
        box(g, .008, .002, len - .01, mats.slot, -x / 4, s * (y / 2 + 2e-4), z);
        box(g, .008, .002, len - .01, mats.slot, x / 4, s * (y / 2 + 2e-4), z);
        box(g, .002, .008, len - .01, mats.slot, s * (x / 2 + 2e-4), 0, z);
      }
    };
    var fixed = parents.fixed, mov = parents.moving;
    box(part(fixed, 'lift_base_plate'), .3, .1, D.PLATE_T, finishMat(THREE, 'lift_base_plate', mats.alu), 0, 0, t - D.PLATE_T / 2, 'base_plate');
    var col = part(fixed, 'lift_column'), i = e.RETRACTED - e.HEAD - .012;
    rbox(col, e.L, e.W, i, .007, mats.anod, 0, 0, t + i / 2);
    slots(col, e.L, e.W, i, t + i / 2);
    box(col, e.L + .004, e.W + .004, .012, mats.aluDark, 0, 0, t + i - .006);
    var stage = part(mov, 'lift_column'), l = .44, c = t + e.RETRACTED;
    rbox(stage, e.L - .016, e.W - .012, l, .005, mats.alu, 0, 0, c - e.HEAD - l / 2);
    slots(stage, e.L - .016, e.W - .012, l, c - e.HEAD - l / 2);
    box(stage, .25, .072, e.HEAD, mats.aluDark, 0, 0, c - e.HEAD / 2, 'head_plate');
    for (var s = -1; s <= 1; s += 2) box(stage, .03, .012, .05, mats.aluDark, s * .11, 0, c + .025);
    var u = D.MOUNT_X, f = c + h.ADAPTER, d = -e.L / 2, p = u + h.X / 2;
    box(part(mov, 'adapter_plate'), p - d, .072, h.ADAPTER, finishMat(THREE, 'adapter_plate', mats.aluDark), (d + p) / 2, 0, c + h.ADAPTER / 2, 'adapter_plate');
    var prof = part(mov, 'arm_profile');
    rbox(prof, h.X, h.Y, h.L, .004, finishMat(THREE, 'arm_profile', mats.alu), u, 0, f + h.L / 2);
    for (s = -1; s <= 1; s += 2) {
      box(prof, .008, .002, h.L - .01, mats.slot, u - h.X / 4, s * (h.Y / 2 + 2e-4), f + h.L / 2);
      box(prof, .008, .002, h.L - .01, mats.slot, u + h.X / 4, s * (h.Y / 2 + 2e-4), f + h.L / 2);
      box(prof, .002, .008, h.L - .01, mats.slot, u + s * (h.X / 2 + 2e-4), 0, f + h.L / 2);
    }
    for (s = -1; s <= 1; s += 2) box(prof, .09, .001, .09, mats.steel, u, s * .0305, c + D.MOUNT_ABOVE_COL);
    // Slot cover strips (inside the arm-profile group): 85 mm in the front-most slot of each side face,
    // above the arm mounts, 247.5 to 332.5 mm above the column top, so that they stay more than 150 mm
    // from the chest E-stop the robot page draws on the profile front face.
    var strips = part(prof, 'slot_cover_strips'), sm = finishMat(THREE, 'slot_cover_strips', mats.slot);
    for (s = -1; s <= 1; s += 2) box(strips, .0085, .0026, .085, sm, u + h.X / 4, s * (h.Y / 2 + 5e-4), c + .29, 'slot_cover_strip');
    var m = c + D.MOUNT_ABOVE_COL + D.ZED_ABOVE_SH, y = f + h.L, br = part(mov, 'head_camera_bracket');
    box(br, .03, .03, .006, mats.alu, D.ZED_X - .03, 0, y + .003);
    box(br, .012, .03, m - y, mats.aluDark, D.ZED_X - .03, 0, (y + m) / 2);
    var zed = part(parents.zed, 'head_camera');
    box(zed, .0265, .1245, .0305, mats.black, -.013, 0, 0);
    cyl(zed, .0085, .003, mats.lens, 5e-4, -.0315, 0, 'x', 20);
    cyl(zed, .0085, .003, mats.lens, 5e-4, .0315, 0, 'x', 20);
    return out;
  };

  // ---------------------------------------------------------------- robot page fittings
  // Items the robot page draws on the robot that are not in the component registry (and so not in the
  // exploded view): base-plate hole marks, base and chest E-stop, RESET button, belly skirt, side and rear
  // decals, lift-column screw heads and label, lift cable, wrist cameras. No light strips: the robot carries
  // no status lights (the LED strips and the column foot light of earlier versions were removed).
  // Built only with M.build(THREE, {fittings: true}).
  function canvasTexture(THREE, w, h, draw) {
    var c = document.createElement('canvas');
    c.width = w;
    c.height = h;
    draw(c.getContext('2d'), w, h);
    var t = new THREE.CanvasTexture(c);
    t.colorSpace = THREE.SRGBColorSpace;
    t.anisotropy = 8;
    return t;
  }
  function decalTexture(THREE) {
    return canvasTexture(THREE, 1024, 128, function (s, w, h) {
      s.clearRect(0, 0, w, h);
      s.fillStyle = '#1b2a3a';
      s.font = '600 76px Helvetica, Arial';
      s.textAlign = 'left';
      s.textBaseline = 'middle';
      s.fillText('Open', 20, h / 2);
      var a = s.measureText('Open').width;
      s.fillStyle = '#0f8f86';
      s.fillText('AMRobot', 20 + a, h / 2);
      var b = s.measureText('AMRobot').width;
      s.fillStyle = '#8a96a3';
      s.font = '500 40px Helvetica';
      s.fillText('2.0', 40 + a + b, h / 2 + 8);
    });
  }
  function labelTexture(THREE, lines, bg, fg, w, h) {
    return canvasTexture(THREE, w, h, function (r) {
      r.fillStyle = bg;
      r.fillRect(0, 0, w, h);
      r.fillStyle = fg;
      r.textAlign = 'center';
      r.font = 'bold ' + Math.round(h * .38) + 'px Helvetica, Arial';
      r.fillText(lines[0], w / 2, h * .5);
      r.font = Math.round(h * .2) + 'px Helvetica, Arial';
      r.globalAlpha = .8;
      r.fillText(lines[1], w / 2, h * .82);
      r.globalAlpha = 1;
    });
  }
  function box(THREE, g, x, y, z, m, px, py, pz) {
    var c = new THREE.Mesh(new THREE.BoxGeometry(x, y, z), m);
    c.position.set(px, py, pz);
    c.castShadow = c.receiveShadow = true;
    g.add(c);
    return c;
  }
  function cyl(THREE, g, r, len, m, px, py, pz, axis, seg) {
    var c = new THREE.Mesh(new THREE.CylinderGeometry(r, r, len, seg), m);
    c.castShadow = true;
    if (axis === 'x') c.rotation.z = Math.PI / 2; else c.rotation.x = Math.PI / 2;
    c.position.set(px, py, pz);
    g.add(c);
    return c;
  }
  function plane(THREE, g, w, h, m, rx, ry, px, py, pz) {
    var c = new THREE.Mesh(new THREE.PlaneGeometry(w, h), m);
    c.rotation.set(rx, ry, 0);
    c.position.set(px, py, pz);
    g.add(c);
    return c;
  }
  function chassisFittings(THREE, g, mats) {
    var D = M.DIMS, hole = new THREE.CircleGeometry(.0045, 12), k, x, y, s;
    for (k in D.BP) for (x of [-.13, .13]) for (y of [-.035, .035]) {
      var h = new THREE.Mesh(hole, mats.black);
      h.position.set(D.BP[k] + x, y, D.DECK + 5e-4);
      g.add(h);
    }
    box(THREE, g, .006, .065, .065, mats.yellow, D.X1 + .003, -.2, .255);  // base E-stop on the front panel
    cyl(THREE, g, .012, .016, mats.black, D.X1 + .014, -.2, .255, 'x', 16);
    cyl(THREE, g, .02, .016, mats.red, D.X1 + .028, -.2, .255, 'x', 24);
    cyl(THREE, g, .015, .008, mats.black, D.X0 + .06, -.21, D.COVER + .004, 'z', 20);  // RESET on the rear deck
    cyl(THREE, g, .011, .008, mats.resetLit, D.X0 + .06, -.21, D.COVER + .012, 'z', 20);
    box(THREE, g, .2, .16, .012, mats.skirt, -.17, 0, D.BELLY - .012);
    var decal = new THREE.MeshStandardMaterial({map: decalTexture(THREE), transparent: true, roughness: .5});
    for (s of [-1, 1]) plane(THREE, g, .4, .05, decal, Math.PI / 2, s > 0 ? Math.PI : 0, -.08, s * (D.HW + .0015), .17);
    plane(THREE, g, .34, .043, decal, Math.PI / 2, -Math.PI / 2, D.X0 - .0015, -.05, .155);
  }
  // Lift cable from the arm profile down the column back to the plate, for the column top at z colTop.
  M.cableGeometry = function (THREE, colTop) {
    var e = colTop, t = M.DIMS.PLATE_TOP, D = M.DIMS, V = THREE.Vector3;
    return new THREE.TubeGeometry(new THREE.CatmullRomCurve3([new V(D.MOUNT_X - D.PROFILE.X / 2 - .012, .012, e + .06),
      new V(.03, .012, e + .03), new V(-.06, .012, e + .02), new V(-.125, .014, e - .06), new V(-.15, .016, (e + t) / 2 + .05),
      new V(-.15, .016, t + .1), new V(-.14, .016, t + .012)]), 48, .0055, 8, false);
  };
  function columnFittings(THREE, col, mov, mats) {
    var D = M.DIMS, e = D.COL, t = D.PLATE_TOP, x, y;
    for (x of [-.13, .13]) for (y of [-.035, .035]) cyl(THREE, col, .0065, .005, mats.steel, x, y, t + .0025, 'z', 6);
    plane(THREE, col, .11, .035, new THREE.MeshStandardMaterial({map: labelTexture(THREE, ['HEXALIFT V4', '800 N · 18 mm/s · 24 V'],
      '#e9ecef', '#1d2733', 512, 160), roughness: .5}), Math.PI / 2, 0, 0, -e.W / 2 - .0012, t + .12);
    var z = t + e.RETRACTED + D.MOUNT_ABOVE_COL - .115, f = D.MOUNT_X + D.PROFILE.X / 2;  // chest E-stop on the profile front
    box(THREE, mov, .036, .07, .07, mats.yellow, f + .018, 0, z);
    cyl(THREE, mov, .019, .02, mats.red, f + .046, 0, z, 'x', 24);
    var cable = new THREE.Mesh(new THREE.BufferGeometry(), mats.cable);
    cable.castShadow = true;
    col.add(cable);
    return {cable: cable};
  }
  function wristCameras(THREE, g, mats) {  // camera bodies; the robot page sets the group matrices
    var out = {};
    ['left', 'right'].forEach(function (s) {
      var o = new THREE.Group(), c = new THREE.Mesh(new THREE.BoxGeometry(.018, .018, .012), mats.black);
      o.matrixAutoUpdate = false;
      c.position.z = .006;
      o.add(c);
      g.add(o);
      out[s] = o;
    });
    return out;
  }

  // ---------------------------------------------------------------- the robot
  // The robot as one object, built the same way for both pages: root (group "OpenAMRobot", robot frame),
  // base (base_cad, GLB parts), col (lift assembly at the base-plate position bp), mov (lift stage; its
  // z is the lift travel), zed (head camera pivot, pitch headPitch degrees), arms (rigs posed at
  // ARM_POSE), parts ({part id: [groups]}), baseIds, mats. o.fittings adds the robot page fittings and
  // returns them as fit ({cable, wrist}).
  M.build = function (THREE, o) {
    o = o || {};
    var D = M.DIMS, mats = M.materials(THREE), R = {mats: mats, parts: {}, baseIds: {}, arms: {}};
    var add = function (id, g) { (R.parts[id] = R.parts[id] || []).push(g); };
    var root = R.root = new THREE.Group();
    root.name = 'OpenAMRobot';
    var base = R.base = M.base(THREE);
    base.position.z = D.BASE_LINK_Z;
    root.add(base);
    base.children.forEach(function (g) { R.baseIds[g.userData.id] = true; add(g.userData.id, g); });
    if (o.fittings) chassisFittings(THREE, root, mats);
    var col = R.col = new THREE.Group(), mov = R.mov = new THREE.Group(), zed = R.zed = new THREE.Group();
    col.name = 'lift_assembly';
    col.position.x = D.BP[o.bp || 'bp000'];
    root.add(col);
    col.add(mov);
    zed.position.set(D.ZED_X, 0, D.PLATE_TOP + D.COL.RETRACTED + D.MOUNT_ABOVE_COL + D.ZED_ABOVE_SH);
    zed.rotation.y = (o.headPitch === undefined ? 25 : o.headPitch) * Math.PI / 180;
    mov.add(zed);
    var ub = M.upperBody(THREE, {fixed: col, moving: mov, zed: zed}, mats);
    for (var id in ub) ub[id].forEach(function (g) { add(id, g); });
    if (o.fittings) R.fit = columnFittings(THREE, col, mov, mats);
    var geos = M.armGeometries(THREE);
    ['left', 'right'].forEach(function (s) {
      var rig = R.arms[s] = M.armRig(THREE, s, geos, mats);
      root.add(rig.group);
      add(rig.group.userData.id, rig.group);
      M.poseArm(THREE, rig, s);
    });
    if (o.fittings) R.fit.wrist = wristCameras(THREE, root, mats);
    M.prepare(THREE, root);
    return R;
  };
})();
