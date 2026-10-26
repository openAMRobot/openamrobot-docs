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
 *    for pages that do not light a floor of their own (the robot page keeps its store lighting).
 * THREE is the namespace of model/three-r160.min.js.
 */
(function () {
  'use strict';
  var L = (window.OAMR_LOOK = {});

  L.EXPOSURE = 1.0;
  L.ENV_BLUR = .04;  // PMREM blur (sigma) of the room environment

  // Renderer settings of both pages. o.exposure: tone mapping exposure of the page (default EXPOSURE).
  L.apply = function (THREE, renderer, o) {
    o = o || {};
    renderer.outputColorSpace = THREE.SRGBColorSpace;
    renderer.toneMapping = THREE.ACESFilmicToneMapping;
    renderer.toneMappingExposure = o.exposure === undefined ? L.EXPOSURE : o.exposure;
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

  // Key light with soft shadows, from the front left, high, framing a robot-sized box (o.half metres).
  L.keyLight = function (THREE, o) {
    o = o || {};
    var h = o.half || 1.1, k = new THREE.DirectionalLight(0xffffff, o.intensity === undefined ? 1.6 : o.intensity);
    k.position.set(1.1, .9, 3.6);
    k.target.position.set(0, 0, .55);
    k.castShadow = true;
    k.shadow.mapSize.set(o.mapSize || 1024, o.mapSize || 1024);
    k.shadow.bias = -2e-4;
    k.shadow.normalBias = .01;
    Object.assign(k.shadow.camera, {left: -h, right: h, top: h, bottom: -h, near: .5, far: 7});
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
})();
