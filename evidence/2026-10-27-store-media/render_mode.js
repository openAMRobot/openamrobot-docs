// Offline render mode of the robot page (robot.html?render=1&frame=N&w=W&h=H&fps=F&speed=K&cam=C). One
// "Run order (8 items)" run; frame N shows sim time N / F x K. cam: auto (Follow, with short cuts to the Side
// view around each shelf grasp), follow, side, over, aisle, top, store, front (front three-quarter, low) or
// tote (above the totes). Everything a frame shows is a function of its sim time and camera. Video frames carry
// the playback speed in their corner caption; pictures (__renderAt) do not.
(function () {
  'use strict';
  var Q = new URLSearchParams(location.search);
  if (Q.get('render') !== '1') return;
  var num = function (k, d, lo, hi) { var v = parseFloat(Q.get(k)); return isFinite(v) ? Math.max(lo, Math.min(hi, v)) : d; };
  var W = Math.round(num('w', 1920, 64, 4096)), H = Math.round(num('h', 1080, 64, 4096)), FPS = num('fps', 30, 1, 120);
  var SPEED = num('speed', 10, .1, 100), CAM = Q.get('cam') || 'auto', CAPTION = Q.get('caption') !== '0';
  var CUT_BEFORE = .8, CUT_AFTER = .5;  // side-view cut around each grasp, in video seconds (about 1.3 s)
  var css = document.createElement('style');
  css.textContent = 'html,body{overflow:hidden!important;margin:0}#stage{position:fixed!important;left:0;top:0;width:' + W +
    'px!important;height:' + H + 'px!important;z-index:2147483000;margin:0!important;border:0!important;border-radius:0!important}' +
    '#stage>:not(canvas){display:none!important}';
  document.head.appendChild(css);
  var S, info, comp = document.createElement('canvas');
  function rotate(p, yaw, v) {
    var c = Math.cos(yaw), s = Math.sin(yaw);
    return [p.x + c * v[0] - s * v[1], p.y + s * v[0] + c * v[1], v[2]];
  }
  function inCut(t) {
    for (var i = 0; i < info.picks.length; i++) {
      var g = info.picks[i].t;
      if (t >= g - CUT_BEFORE * SPEED && t <= g + CUT_AFTER * SPEED) return info.picks[i];
    }
    return null;
  }
  function camera(cam, t) {
    var p = S.robot.pose, yaw = p.yaw || 0;
    if (cam === 'auto') cam = inCut(t) ? 'side' : 'follow';
    if (cam === 'front' || cam === 'tote') {
      var side = cam === 'tote' ? (info.sideAt(t) === 'right' ? -1 : 1) : 1;
      var pos = cam === 'front' ? rotate(p, yaw, [1.75, -1.25, .55]) : rotate(p, yaw, [-.75, side * 1.05, 1.6]);
      var tgt = cam === 'front' ? rotate(p, yaw, [.1, 0, .72]) : rotate(p, yaw, [.12, side * .2, .42]);
      S.closeUp(pos[0], pos[1], pos[2], tgt[0], tgt[1], tgt[2]);
    } else S.setView(cam);
  }
  // Corner caption, opaque box: "OpenAMRobot 2.0, simulation visualization" and, on video frames, the
  // playback speed (sim seconds per video second, the speed parameter of the render).
  function speedText() { return (Math.round(SPEED * 10) / 10) + 'x speed'; }
  function caption(x, U, h, withSpeed) {
    var text = 'OpenAMRobot 2.0, simulation visualization' + (withSpeed ? ', ' + speedText() : '');
    x.font = '600 ' + 13 * U + 'px "Barlow Semi Condensed", "Arial Narrow", sans-serif';
    var tw = x.measureText(text).width, bw = tw + 22 * U, bh = 26 * U, bx = 16 * U, by = h - bh - 16 * U, r = 6 * U;
    x.beginPath();
    x.moveTo(bx + r, by);
    x.arcTo(bx + bw, by, bx + bw, by + bh, r);
    x.arcTo(bx + bw, by + bh, bx, by + bh, r);
    x.arcTo(bx, by + bh, bx, by, r);
    x.arcTo(bx, by, bx + bw, by, r);
    x.closePath();
    x.fillStyle = 'rgb(21,46,69)';
    x.fill();
    x.fillStyle = '#fff';
    x.textBaseline = 'middle';
    x.textAlign = 'left';
    x.fillText(text, bx + 11 * U, by + bh / 2 + .5 * U);
  }
  function compose(fmt, withSpeed) {
    var src = S.renderer.domElement;
    comp.width = src.width;
    comp.height = src.height;
    var x = comp.getContext('2d'), U = Math.min(W, H) / 620 * (src.width / W);
    x.drawImage(src, 0, 0);
    if (CAPTION) caption(x, U, comp.height, withSpeed);
    return fmt === 'jpeg' ? comp.toDataURL('image/jpeg', .9) : comp.toDataURL('image/png');
  }
  // The caption of a video frame alone on a transparent canvas (PNG), for overlaying frames rendered
  // with an earlier caption.
  function captionOverlay() {
    var c = document.createElement('canvas'), src = S.renderer.domElement;
    c.width = src.width;
    c.height = src.height;
    caption(c.getContext('2d'), Math.min(W, H) / 620 * (src.width / W), c.height, true);
    return c.toDataURL('image/png');
  }
  function at(t, cam, fmt, withSpeed) {
    t = Math.max(0, Math.min(info.T, t));
    S.applyAt(t);
    camera(cam || CAM, t);
    S.render();
    return compose(fmt, withSpeed);
  }
  function setup() {
    S = window.__sim;
    if (S.S.tiles) document.getElementById('b-tiles').click();
    ['b-frames', 'b-labels'].forEach(function (id) {
      var e = document.getElementById(id);
      if (e && e.getAttribute('aria-pressed') === 'true') e.click();
    });
    S.startRun(S.order(), 'order');
    S.S.playing = false;
    var tl = S.TL, picks = [], places = [];
    tl.items.forEach(function (c) {
      picks.push({t: c.tGrasp, side: c.side});
      for (var i = 0; i < c.phases.length; i++) if (c.phases[i].kind === 'robot') { places.push({t: c.phases[i].t, side: c.side}); break; }
    });
    info = {fps: FPS, speed: SPEED, T: tl.T, frames: Math.floor(tl.T / SPEED * FPS) + 1, picks: picks, places: places, w: W, h: H, cam: CAM,
      sideAt: function (t) { var s = 'left'; picks.forEach(function (p) { if (p.t <= t) s = p.side; }); return s; }};
    window.__store = {fps: FPS, speed: SPEED, T: tl.T, frames: info.frames, picks: picks, places: places, w: W, h: H, cam: CAM};
    window.__renderFrame = function (n, fmt) { return at(n / FPS * SPEED, CAM, fmt, true); };
    window.__captionOverlay = captionOverlay;
    window.__renderAt = function (t, cam, fmt) { return at(t, cam, fmt); };
    window.__frameReady = true;
  }
  function wait() {
    var c = window.__sim && window.__sim.renderer.domElement;
    if (!c || c.width !== W || c.height !== H) { setTimeout(wait, 50); return; }
    var fonts = document.fonts ? document.fonts.load('600 20px "Barlow Semi Condensed"') : Promise.resolve();
    fonts.then(setup);
  }
  wait();
})();
