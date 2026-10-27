/* SPDX-License-Identifier: MIT
 * OpenAMRobot 2.0 roadmap pages: the shared look of the robot (robot.html, exploded.html).
 *
 * Renderer settings, one environment map and the shadow set-up used by both pages, so that the robot
 * of model/model.js renders with the same tone mapping, colour output and image-based light on each:
 *  - ACES filmic tone mapping, sRGB output; physically based light units (three.js r160 default,
 *    legacy lights off);
 *  - environment: three.js RoomEnvironment (model/three-r160.min.js, same r160 release, MIT) through
 *    PMREMGenerator, built in code at load; nothing is downloaded;
 *  - shadows: PCF soft shadow maps; a key light with soft shadows and a contact shadow under the base
 *    for pages that do not light a floor of their own (the robot page keeps its store lighting);
 *  - calibration (CAL): exposure, key light and environment intensity per page, set so that the lit
 *    faces of the side panel, the cover and the arm profile read within about 10 % of their
 *    finish.json sRGB values (evidence/2026-10-26-shared-model, colour samples);
 *  - light look: a fallback for slow devices (first 30 frames over 33 ms on average) or when the page's
 *    High quality toggle is off: environment on the metal and glass classes only, the other robot
 *    materials without image-based light, no robot shadow map, the contact shadow kept.
 * THREE is the namespace of model/three-r160.min.js.
 */
(function () {
  'use strict';
  var L = (window.OAMR_LOOK = {});

  L.ENV_BLUR = .04;  // PMREM blur (sigma) of the room environment
  // Per page: tone mapping exposure, key light intensity (exploded view; the robot page keeps its store
  // lights), environment intensity of the robot materials (dielectric and metal classes).
  L.CAL = {
    exploded: {exposure: 1.2, key: 2.8, rim: 2, envDielectric: .14, envMetal: 1.3},
    robot: {exposure: 1.05, envDielectric: .16, envMetal: 1.3}  // exposure as before: the store look is unchanged
  };
  L.METAL_CLASSES = ['anodised_aluminium', 'satin_aluminium', 'heatsink', 'sensor_glass'];  // keep the environment in the light look
  L.FRAME_BUDGET_MS = 33;
  L.PROBE_FRAMES = 30;

  // Renderer settings of both pages. o.exposure: tone mapping exposure of the page.
  L.apply = function (THREE, renderer, o) {
    o = o || {};
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = o.exposure === undefined ? 1 : o.exposure;
    renderer.shadowMap.enabled = true;
    renderer.shadowMap.type = THREE.PCFSoftShadowMap;
  };

  // The one environment map: RoomEnvironment prefiltered by PMREM (for scene.environment).
  L.environment = function (THREE, renderer) {
    var pmrem = new THREE.PMREMGenerator(renderer), room = new THREE.RoomEnvironment(renderer);
    var tex = pmrem.fromScene(room, L.ENV_BLUR).texture;
    room.traverse(function (o) { if (o.isMesh) { o.geometry.dispose(); o.material.dispose(); } });
    pmrem.dispose();
    return tex;
  };

  var isMetal = function (m) { return L.METAL_CLASSES.indexOf(m.userData && m.userData.cls) >= 0; };
  // Environment intensity of the robot materials (cal: {envDielectric, envMetal}; times the class env_scale).
  L.robotEnv = function (root, cal) {
    root.traverse(function (o) {
      var m = o.isMesh && o.material;
      if (m && m.isMeshStandardMaterial) m.envMapIntensity = (isMetal(m) ? cal.envMetal : cal.envDielectric) * (m.userData.envScale || 1);
    });
  };

  // Key light with soft shadows, from the camera side (front right, above), at about the same angle to the
  // front, right side and top faces, framing a robot-sized box (o.half metres).
  L.keyLight = function (THREE, o) {
    o = o || {};
    var h = o.half || 1.1, k = new THREE.DirectionalLight(0xffffff, o.intensity === undefined ? 1.6 : o.intensity);
    k.position.set(2.0, -2.0, 2.4);
    k.target.position.set(0, 0, .55);
    k.castShadow = true;
    k.shadow.mapSize.set(o.mapSize || 1024, o.mapSize || 1024);
    k.shadow.bias = -2e-4;
    k.shadow.normalBias = .01;
    Object.assign(k.shadow.camera, {left: -h, right: h, top: h, bottom: -h, near: .5, far: 8});
    return k;
  };

  // Ground that shows only the shadows cast on it (transparent elsewhere), size metres square.
  L.shadowCatcher = function (THREE, size, opacity) {
    var g = new THREE.Mesh(new THREE.PlaneGeometry(size, size), new THREE.ShadowMaterial({opacity: opacity === undefined ? .22 : opacity}));
    g.receiveShadow = true;
    g.position.z = 5e-4;
    return g;
  };

  // Contact shadow under the base: a soft dark ellipse on the floor, w x d metres, centred at x.
  L.contactShadow = function (THREE, w, d, x) {
    var n = 128, c = document.createElement('canvas');
    c.width = c.height = n;
    var s = c.getContext('2d'), gr = s.createRadialGradient(n / 2, n / 2, 0, n / 2, n / 2, n / 2);
    gr.addColorStop(0, 'rgba(0,0,0,0.55)');
    gr.addColorStop(.55, 'rgba(0,0,0,0.38)');
    gr.addColorStop(1, 'rgba(0,0,0,0)');
    s.fillStyle = gr;
    s.fillRect(0, 0, n, n);
    var t = new THREE.CanvasTexture(c);
    var m = new THREE.Mesh(new THREE.PlaneGeometry(w, d), new THREE.MeshBasicMaterial({map: t, transparent: true, depthWrite: false, toneMapped: false}));
    m.position.set(x || 0, 0, 3e-4);
    m.renderOrder = -1;
    return m;
  };

  // Weak fill light from the rear left, so that the faces turned away from the key light (rear and left
  // side panels) keep their light grey. A hemisphere light oriented to the rear left (sky white, ground
  // black): diffuse only, so it adds no specular glint on the glossier parts at grazing angles. Pages that
  // light their own scene (the robot page store) do not add it.
  L.rimLight = function (THREE, intensity) {
    var r = new THREE.HemisphereLight(0xffffff, 0x000000, intensity === undefined ? 1 : intensity);
    r.position.set(-2.2, 2.0, .45);
    r.name = 'look_rim';
    return r;
  };

  // Hemisphere light that stands in for the environment on the non-metal materials in the light look.
  L.fillLight = function (THREE) { return new THREE.HemisphereLight(0xffffff, 0x8a9590, 1.4); };

  // ---------------------------------------------------------------- light look
  var twins = new WeakMap(), lightOn = false;
  function twinOf(THREE, m) {  // a Lambert material (no image-based light) with the look of m
    var t = twins.get(m);
    if (t) return t;
    t = new THREE.MeshLambertMaterial({color: m.color, map: m.map, vertexColors: m.vertexColors, side: m.side,
      transparent: m.transparent, opacity: m.opacity, depthWrite: m.depthWrite,
      emissive: m.emissive, emissiveIntensity: m.emissiveIntensity});
    t.userData = Object.assign({}, m.userData, {twinOf: true});
    twins.set(m, t);
    twins.set(t, m);
    return t;
  }
  // Switch the robot under root to the light look (on) or back to the full look. o.contact: add a
  // contact shadow under the base while the light look is on (pages that light their own floor).
  L.lightLook = function (THREE, root, on, o) {
    o = o || {};
    lightOn = !!on;
    root.traverse(function (x) {
      if (!x.isMesh || x.userData.lookContact) return;
      var m = x.material;
      if (on) {
        if (x.userData.shadow === undefined) x.userData.shadow = [x.castShadow, x.receiveShadow];
        x.castShadow = x.receiveShadow = false;
        if (m.isMeshStandardMaterial && !isMetal(m)) x.material = twinOf(THREE, m);
      } else {
        if (x.userData.shadow) { x.castShadow = x.userData.shadow[0]; x.receiveShadow = x.userData.shadow[1]; }
        if (m.userData && m.userData.twinOf) x.material = twins.get(m);
      }
      x.material.needsUpdate = true;
    });
    if (o.contact) {
      var c = root.userData.lookContact;
      if (!c && on) {
        c = root.userData.lookContact = L.contactShadow(THREE, .95, .78, 0);
        c.userData.lookContact = true;
        root.add(c);
      }
      if (c) c.visible = !!on;
    }
  };
  L.isLight = function () { return lightOn; };
  // The material to show for m in the current look (pages that swap materials themselves).
  L.pick = function (m) { return lightOn && m && m.isMeshStandardMaterial && !isMetal(m) ? twins.get(m) || m : m; };

  // Look forced by the URL (?look=full or ?look=light, or render mode: full), else null.
  // The offline render mode (?render=1, videos and pictures) is always the full look unless ?look= says
  // otherwise, and never runs the frame-time probe.
  L.forced = function () {
    var q = new URLSearchParams(location.search), v = q.get('look');
    if (v === 'full' || v === 'light') return v;
    return q.get('render') === '1' ? 'full' : null;
  };

  // Frame-time probe: the page renders every frame while probing() is true and calls frame(timestamp)
  // after each render; after PROBE_FRAMES frames done(average interval in ms) is called once.
  var probe = null;
  L.startProbe = function (done) { probe = {t: [], done: done}; };
  L.probing = function () { return !!probe; };
  L.frame = function (ts) {
    if (!probe) return;
    probe.t.push(ts);
    if (probe.t.length > L.PROBE_FRAMES) {
      var p = probe, avg = (p.t[p.t.length - 1] - p.t[0]) / (p.t.length - 1);
      probe = null;
      L.lastProbeMs = avg;
      p.done(avg);
    }
  };
})();
