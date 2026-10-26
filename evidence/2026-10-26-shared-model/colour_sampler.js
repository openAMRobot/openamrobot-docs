// In-page colour sampler (injected by colour.js). Renders the beauty frame, then a part-ID pass and a
// view-space normal pass of the same camera; keeps pixels of the target parts whose 5 x 5 neighbourhood is
// the same part (no edges), whose face points to the key light (n . L > 0.35) and to the camera
// (view-space n.z > 0.3; o.lightDir overrides the key light direction); returns the median sRGB of the beauty frame per target.
window.__sampleColours = function (o) {
  const T = window.THREE, r = o.renderer, s = o.scene, cam = o.camera, gl = r.getContext();
  const W = gl.drawingBufferWidth, H = gl.drawingBufferHeight;
  const read = () => { const px = new Uint8Array(W * H * 4); gl.readPixels(0, 0, W, H, gl.RGBA, gl.UNSIGNED_BYTE, px); return px; };
  o.renderBeauty();
  const beauty = read();
  const partOf = x => { while (x && !(x.userData && x.userData.id)) x = x.parent; return x ? x.userData.id : null; };
  const inRoot = x => { while (x) { if (x === o.root) return true; x = x.parent; } return false; };
  const ids = Object.keys(o.targets), idx = {};
  ids.forEach((k, i) => o.targets[k].forEach(p => { idx[p] = i + 1; }));
  const saved = [], black = new T.MeshBasicMaterial({color: 0}), hidden = [];
  const save = {bg: s.background, fog: s.fog, tm: r.toneMapping, cs: r.outputColorSpace, ov: s.overrideMaterial};
  s.traverse(x => {
    if (x.isMesh) saved.push([x, x.material]);
    else if ((x.isLine || x.isPoints || x.isSprite) && x.visible) { hidden.push(x); x.visible = false; }
  });
  s.background = new T.Color(0); s.fog = null; s.overrideMaterial = null;
  r.toneMapping = T.NoToneMapping; r.outputColorSpace = T.LinearSRGBColorSpace;
  const idMats = {}, nrm = new T.MeshNormalMaterial();
  const pass = kind => {
    saved.forEach(([x]) => {
      const k = inRoot(x) ? idx[partOf(x)] : 0;
      if (!k) { x.material = black; return; }
      if (kind === 'id') {
        if (!idMats[k]) { idMats[k] = new T.MeshBasicMaterial(); idMats[k].color.setRGB(k / 255, 0, 0, T.LinearSRGBColorSpace); }
        x.material = idMats[k];
      } else x.material = nrm;
    });
    r.setRenderTarget(null); r.render(s, cam);
    return read();
  };
  const id = pass('id'), nv = pass('normal');
  saved.forEach(([x, m]) => { x.material = m; }); hidden.forEach(x => { x.visible = true; });
  s.background = save.bg; s.fog = save.fog; s.overrideMaterial = save.ov; r.toneMapping = save.tm; r.outputColorSpace = save.cs;
  const Ld = o.lightDir ? new T.Vector3().fromArray(o.lightDir).normalize() : new T.Vector3().subVectors(o.light.position, o.light.target.position).normalize();
  const rot = new T.Matrix3().setFromMatrix4(cam.matrixWorld), n = new T.Vector3();
  const out = {};
  ids.forEach((name, i) => {
    const k = i + 1, R = [], G = [], B = [];
    for (let y = 2; y < H - 2; y++) for (let x = 2; x < W - 2; x++) {
      const p = (y * W + x) * 4;
      if (id[p] !== k) continue;
      let ok = true;
      for (let dy = -2; dy <= 2 && ok; dy++) for (let dx = -2; dx <= 2; dx++) if (id[((y + dy) * W + x + dx) * 4] !== k) { ok = false; break; }
      if (!ok) continue;
      n.set(nv[p] / 127.5 - 1, nv[p + 1] / 127.5 - 1, nv[p + 2] / 127.5 - 1);
      if (n.z < .3) continue;
      n.applyMatrix3(rot).normalize();
      if (n.dot(Ld) < .35) continue;
      R.push(beauty[p]); G.push(beauty[p + 1]); B.push(beauty[p + 2]);
    }
    const med = a => { if (!a.length) return null; a.sort((u, v) => u - v); return a[a.length >> 1]; };
    out[name] = {n: R.length, rgb: [med(R), med(G), med(B)]};
  });
  o.renderBeauty();
  return out;
};
