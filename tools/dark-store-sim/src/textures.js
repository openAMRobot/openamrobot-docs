import * as THREE from 'three';

let seed = 11;
export const rand = () => (seed = (seed * 16807) % 2147483647) / 2147483647;

export function canvasTex(w, h, draw, opts = {}) {
  const c = document.createElement('canvas'); c.width = w; c.height = h;
  draw(c.getContext('2d'), w, h);
  const t = new THREE.CanvasTexture(c);
  t.colorSpace = opts.linear ? THREE.NoColorSpace : THREE.SRGBColorSpace;
  t.anisotropy = 8;
  if (opts.repeat) { t.wrapS = t.wrapT = THREE.RepeatWrapping; t.repeat.set(opts.repeat[0], opts.repeat[1]); }
  return t;
}

function noise(x, w, h, base, amp, n, rmin, rmax, alpha) {
  for (let i = 0; i < n; i++) {
    const v = base + (rand() - 0.5) * amp;
    x.fillStyle = `rgba(${v},${v},${v},${alpha})`;
    const r = rmin + rand() * (rmax - rmin);
    x.beginPath(); x.arc(rand() * w, rand() * h, r, 0, Math.PI * 2); x.fill();
  }
}

// Polished, slightly worn concrete (sealed) floor
export function concreteTextures() {
  const draw = (x, w, h, rough) => {
    x.fillStyle = rough ? '#8a8a8a' : '#9a9b98'; x.fillRect(0, 0, w, h);
    noise(x, w, h, rough ? 140 : 150, 60, 900, 20, 90, 0.05);
    noise(x, w, h, rough ? 120 : 130, 80, 6000, 0.6, 2.4, 0.25);
    for (let i = 0; i < 40; i++) {           // faint trowel marks / scuffs
      x.strokeStyle = `rgba(${rough ? 200 : 70},${rough ? 200 : 70},${rough ? 200 : 70},0.05)`;
      x.lineWidth = 1 + rand() * 4; x.beginPath();
      const cx = rand() * w, cy = rand() * h, r = 40 + rand() * 160;
      x.arc(cx, cy, r, rand() * 6, rand() * 6); x.stroke();
    }
    // saw cut joints every 2 m (texture spans 2 m)
    x.strokeStyle = rough ? 'rgba(255,255,255,0.6)' : 'rgba(60,60,60,0.55)'; x.lineWidth = 3;
    x.beginPath(); x.moveTo(0, 1); x.lineTo(w, 1); x.moveTo(1, 0); x.lineTo(1, h); x.stroke();
  };
  seed = 3;
  const map = canvasTex(1024, 1024, (x, w, h) => draw(x, w, h, false), { repeat: [1, 1] });
  seed = 3;
  const rough = canvasTex(1024, 1024, (x, w, h) => draw(x, w, h, true), { repeat: [1, 1], linear: true });
  return { map, rough };
}

export function barcode(x, x0, y0, w, h) {
  x.fillStyle = '#fff'; x.fillRect(x0, y0, w, h); x.fillStyle = '#111';
  let px = x0 + w * 0.06; const m = Math.max(1, w / 110);
  while (px < x0 + w * 0.92) { const bw = m * (1 + Math.floor(rand() * 3)); x.fillRect(px, y0 + h * 0.08, bw, h * 0.7); px += bw + m * (1 + Math.floor(rand() * 2.5)); }
  x.font = `${Math.round(h * 0.17)}px monospace`; x.textAlign = 'center';
  x.fillText('4 006381 ' + String(Math.floor(rand() * 900000 + 100000)), x0 + w / 2, y0 + h * 0.97);
}

function wave(x, w, y, amp, col, phase = 0) {
  x.fillStyle = col; x.beginPath(); x.moveTo(0, y);
  for (let i = 0; i <= 40; i++) x.lineTo(w * i / 40, y + Math.sin(i / 40 * Math.PI * 2 + phase) * amp);
  x.lineTo(w, 9999); x.lineTo(0, 9999); x.closePath(); x.fill();
}

// --- product artwork (invented brands, illustration only) -------------------------------------------
export const ART = {
  milk: (v) => canvasTex(512, 1024, (x, w, h) => {
    const c = v === 1 ? '#c8312b' : '#1f5fae';
    x.fillStyle = '#fbfbf7'; x.fillRect(0, 0, w, h);
    wave(x, w, h * 0.62, 18, '#8fc45a', 0.3); wave(x, w, h * 0.68, 14, '#5e9e37', 1.6);
    x.fillStyle = c; x.fillRect(0, 0, w, h * 0.13);
    x.fillStyle = '#fff'; x.font = 'bold 62px Georgia, serif'; x.textAlign = 'center'; x.fillText('Kleewiese', w / 2, h * 0.095);
    x.fillStyle = c; x.font = 'bold 88px Helvetica, Arial'; x.fillText('Frische', w / 2, h * 0.27);
    x.fillText('Milch', w / 2, h * 0.36);
    x.font = 'bold 120px Helvetica, Arial'; x.fillText(v === 1 ? '1,5%' : '3,5%', w / 2, h * 0.5);
    x.fillStyle = '#fff'; x.font = 'bold 54px Helvetica'; x.fillText('1 L', w * 0.8, h * 0.93);
    // cow silhouette
    x.fillStyle = '#222'; x.beginPath(); x.ellipse(w * 0.36, h * 0.8, 70, 34, 0, 0, Math.PI * 2); x.fill();
    x.fillStyle = '#fff'; x.beginPath(); x.ellipse(w * 0.33, h * 0.79, 24, 14, 0.4, 0, Math.PI * 2); x.fill();
    x.fillStyle = '#222'; x.fillRect(w * 0.26, h * 0.81, 10, 40); x.fillRect(w * 0.44, h * 0.81, 10, 40);
    x.beginPath(); x.ellipse(w * 0.5, h * 0.775, 26, 18, -0.3, 0, Math.PI * 2); x.fill();
  }),
  milkSide: (v) => canvasTex(256, 1024, (x, w, h) => {
    x.fillStyle = '#fbfbf7'; x.fillRect(0, 0, w, h);
    x.fillStyle = v === 1 ? '#c8312b' : '#1f5fae'; x.fillRect(0, 0, w, h * 0.13);
    wave(x, w, h * 0.62, 10, '#8fc45a'); wave(x, w, h * 0.68, 8, '#5e9e37', 2);
    x.fillStyle = '#333'; x.font = '18px Helvetica'; for (let i = 0; i < 9; i++) x.fillRect(24, h * 0.2 + i * 26, w - 48 - rand() * 60, 6);
    barcode(x, 30, h * 0.47, w - 60, 90);
  }),
  juice: (v) => canvasTex(1024, 256, (x, w, h) => {      // wrap label, v 0 orange, 1 apple
    const c1 = v ? '#6bb33a' : '#f39a1d', c2 = v ? '#2f7d22' : '#e2561b';
    const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, c1); g.addColorStop(1, c2); x.fillStyle = g; x.fillRect(0, 0, w, h);
    for (let k = 0; k < 2; k++) {
      const cx = w * (0.25 + k * 0.5);
      x.fillStyle = '#fff'; x.font = 'italic bold 46px Georgia'; x.textAlign = 'center'; x.fillText('Sonnenhang', cx, h * 0.3);
      x.fillStyle = v ? '#d6262a' : '#ffb21f'; x.beginPath(); x.arc(cx - 120, h * 0.66, 42, 0, Math.PI * 2); x.fill();
      x.fillStyle = 'rgba(255,255,255,0.35)'; x.beginPath(); x.arc(cx - 132, h * 0.62, 12, 0, Math.PI * 2); x.fill();
      x.fillStyle = '#fff'; x.font = 'bold 40px Helvetica'; x.fillText(v ? 'Apfelsaft' : 'Orangensaft', cx + 40, h * 0.62);
      x.font = '26px Helvetica'; x.fillText('100% Saft · 1 L', cx + 40, h * 0.82);
    }
    barcode(x, w * 0.46, h * 0.18, 70, 150);
  }),
  beer: (v) => canvasTex(1024, 256, (x, w, h) => {
    x.fillStyle = v ? '#f2e6c6' : '#123b2a'; x.fillRect(0, 0, w, h);
    x.strokeStyle = v ? '#9a7a2d' : '#d7b85a'; x.lineWidth = 6; x.strokeRect(10, 10, w - 20, h - 20);
    for (let k = 0; k < 2; k++) {
      const cx = w * (0.25 + k * 0.5);
      x.fillStyle = v ? '#7a1f1f' : '#e8cf7a'; x.textAlign = 'center';
      x.font = 'bold 52px Georgia'; x.fillText(v ? 'Spreewelle' : 'Kiezbräu', cx, h * 0.42);
      x.font = '34px Georgia'; x.fillText(v ? 'Pilsener' : 'Helles', cx, h * 0.66);
      x.font = '22px Georgia'; x.fillText('0,5 L · 4,9% vol', cx, h * 0.85);
    }
  }),
  water: (v) => canvasTex(1024, 256, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, w, 0); g.addColorStop(0, '#e9f6fc'); g.addColorStop(0.5, '#ffffff'); g.addColorStop(1, '#e9f6fc');
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    for (let k = 0; k < 2; k++) {
      const cx = w * (0.25 + k * 0.5);
      x.fillStyle = '#2a6fb6'; x.beginPath(); x.moveTo(cx - 170, h * 0.75); x.lineTo(cx - 130, h * 0.25); x.lineTo(cx - 90, h * 0.75); x.fill();
      x.fillStyle = '#0d3d75'; x.font = 'bold 56px Helvetica'; x.textAlign = 'left'; x.fillText('Quellstein', cx - 70, h * 0.48);
      x.fillStyle = v ? '#2fa44a' : '#2a6fb6'; x.font = 'bold 34px Helvetica'; x.fillText(v ? 'Medium · 1,5 L' : 'Still · 1,5 L', cx - 70, h * 0.74);
    }
  }),
  can: (v) => canvasTex(512, 256, (x, w, h) => {
    x.fillStyle = v ? '#f2d21b' : '#b5121b'; x.fillRect(0, 0, w, h);
    x.fillStyle = '#fff'; x.font = 'italic bold 64px Helvetica'; x.textAlign = 'center';
    x.fillText('Fizzbo', w * 0.3, h * 0.55); x.fillText('Fizzbo', w * 0.8, h * 0.55);
    x.font = 'bold 28px Helvetica'; x.fillStyle = v ? '#3a3a3a' : '#fff';
    x.fillText(v ? 'LEMON' : 'COLA', w * 0.3, h * 0.78); x.fillText(v ? 'LEMON' : 'COLA', w * 0.8, h * 0.78);
  }),
  chips: (v) => canvasTex(512, 768, (x, w, h) => {
    const cols = [['#d62a1f', '#ffcc29'], ['#1f7fd6', '#fff3c4'], ['#2c8f3b', '#ffe08a']][v % 3];
    const g = x.createRadialGradient(w / 2, h * 0.55, 30, w / 2, h * 0.55, w * 0.8); g.addColorStop(0, cols[1]); g.addColorStop(0.45, cols[0]); g.addColorStop(1, cols[0]);
    x.fillStyle = g; x.fillRect(0, 0, w, h);
    x.fillStyle = '#fff'; x.font = 'bold 70px Helvetica'; x.textAlign = 'center'; x.fillText('Knusper&Co', w / 2, h * 0.2);
    x.fillStyle = '#e8b04a'; for (let i = 0; i < 7; i++) { x.beginPath(); x.ellipse(w * (0.25 + rand() * 0.5), h * (0.48 + rand() * 0.2), 52, 34, rand() * 3, 0, Math.PI * 2); x.fill(); }
    x.fillStyle = '#fff'; x.font = 'bold 54px Helvetica'; x.fillText(['Paprika', 'Meersalz', 'Sour Cream'][v % 3], w / 2, h * 0.84);
    x.font = '30px Helvetica'; x.fillText('150 g', w / 2, h * 0.92);
  }),
  pretzel: () => canvasTex(512, 1024, (x, w, h) => {
    x.fillStyle = '#123a73'; x.fillRect(0, 0, w, h);
    x.fillStyle = '#f6c343'; x.font = 'bold 76px Helvetica'; x.textAlign = 'center'; x.fillText('Brezlinos', w / 2, h * 0.16);
    x.strokeStyle = '#a86a2b'; x.lineWidth = 16;
    for (let i = 0; i < 9; i++) { x.beginPath(); x.moveTo(w * 0.2 + i * 34, h * 0.32); x.lineTo(w * 0.32 + i * 30, h * 0.72); x.stroke(); }
    x.fillStyle = '#fff'; x.font = 'bold 48px Helvetica'; x.fillText('Salzstangen', w / 2, h * 0.84); x.font = '32px Helvetica'; x.fillText('250 g', w / 2, h * 0.91);
  }),
  pack: (v) => canvasTex(512, 256, (x, w, h) => {      // shrink-film print band
    x.clearRect(0, 0, w, h); x.fillStyle = 'rgba(42,111,182,0.9)'; x.fillRect(0, h * 0.3, w, h * 0.4);
    x.fillStyle = '#fff'; x.font = 'bold 54px Helvetica'; x.textAlign = 'center'; x.fillText('Quellstein 6 × 1,5 L', w / 2, h * 0.58);
  }),
  crate: (v) => canvasTex(512, 384, (x, w, h) => {
    x.fillStyle = v ? '#1e4f2e' : '#5a2a14'; x.fillRect(0, 0, w, h);
    x.fillStyle = 'rgba(0,0,0,0.25)'; for (let i = 0; i < 6; i++) x.fillRect(0, h * (0.12 + i * 0.15), w, 6);
    x.fillStyle = '#e8cf7a'; x.font = 'bold 62px Georgia'; x.textAlign = 'center'; x.fillText(v ? 'Spreewelle' : 'Kiezbräu', w / 2, h * 0.56);
    x.fillStyle = '#111'; x.fillRect(w * 0.3, h * 0.08, w * 0.4, h * 0.12);   // handle hole
  }, {}),
};

// Shelf-edge price labels with location codes
export function priceStripTex(bayCode, items) {
  return canvasTex(2048, 64, (x, w, h) => {
    x.fillStyle = '#f4f4f2'; x.fillRect(0, 0, w, h);
    items.forEach((it, i) => {
      const x0 = 30 + i * (w / items.length);
      x.fillStyle = '#fff'; x.fillRect(x0, 4, 300, h - 8); x.strokeStyle = '#ccc'; x.strokeRect(x0, 4, 300, h - 8);
      x.fillStyle = '#e30613'; x.fillRect(x0, 4, 8, h - 8);
      x.fillStyle = '#111'; x.font = 'bold 22px Helvetica'; x.textAlign = 'left'; x.fillText(it.name, x0 + 16, 26);
      x.font = '14px monospace'; x.fillText(bayCode + '-' + String(i + 1).padStart(2, '0'), x0 + 16, 50);
      x.font = 'bold 30px Helvetica'; x.textAlign = 'right'; x.fillText(it.price, x0 + 292, 46);
      barcode(x, x0 + 120, 32, 70, 28);
    });
  });
}

export function signTex(lines, bg = '#1d2733', fg = '#ffffff', w = 1024, h = 256) {
  return canvasTex(w, h, (x) => {
    x.fillStyle = bg; x.fillRect(0, 0, w, h);
    x.fillStyle = fg; x.textAlign = 'center';
    x.font = `bold ${Math.round(h * 0.38)}px Helvetica, Arial`; x.fillText(lines[0], w / 2, h * 0.5);
    if (lines[1]) { x.font = `${Math.round(h * 0.2)}px Helvetica, Arial`; x.globalAlpha = 0.8; x.fillText(lines[1], w / 2, h * 0.82); x.globalAlpha = 1; }
  });
}

export function logoTex() {
  return canvasTex(1024, 128, (x, w, h) => {
    x.clearRect(0, 0, w, h);
    x.fillStyle = '#1b2a3a'; x.font = '600 76px Helvetica, Arial'; x.textAlign = 'left'; x.textBaseline = 'middle';
    x.fillText('Open', 20, h / 2); const a = x.measureText('Open').width;
    x.fillStyle = '#0f8f86'; x.fillText('AMRobot', 20 + a, h / 2); const b = x.measureText('AMRobot').width;
    x.fillStyle = '#8a96a3'; x.font = '500 40px Helvetica'; x.fillText('2.0', 40 + a + b, h / 2 + 8);
  });
}

export function perforatedTex(color = '#3a3f45', hole = '#15181b') {
  return canvasTex(64, 512, (x, w, h) => {
    x.fillStyle = color; x.fillRect(0, 0, w, h);
    x.fillStyle = hole; for (let y = 8; y < h; y += 25) x.fillRect(w * 0.38, y, w * 0.24, 12);
  }, { repeat: [1, 8] });
}

export function pegboardTex() {
  return canvasTex(256, 256, (x, w, h) => {
    x.fillStyle = '#e7e8e6'; x.fillRect(0, 0, w, h);
    x.fillStyle = '#b9bbb8'; for (let i = 0; i < 8; i++) for (let j = 0; j < 8; j++) { x.beginPath(); x.arc(16 + i * 32, 16 + j * 32, 4, 0, Math.PI * 2); x.fill(); }
  }, { repeat: [12, 8] });
}

export function toteTex(color) {
  return canvasTex(256, 256, (x, w, h) => {
    x.fillStyle = color; x.fillRect(0, 0, w, h);
    x.fillStyle = 'rgba(0,0,0,0.12)'; for (let i = 0; i < 8; i++) x.fillRect(i * 32 + 12, 0, 6, h);
    x.fillStyle = 'rgba(255,255,255,0.06)'; x.fillRect(0, 0, w, 10);
  });
}

export function chillerDoorTex() {
  return canvasTex(256, 1024, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, 0, h); g.addColorStop(0, '#f5fbff'); g.addColorStop(1, '#d9e8f2'); x.fillStyle = g; x.fillRect(0, 0, w, h);
    const cols = ['#1f5fae', '#f39a1d', '#fbfbf7', '#c8312b', '#6bb33a', '#2a6fb6'];
    for (let s = 0; s < 6; s++) {
      const y = 80 + s * 160; x.fillStyle = '#b8c4cc'; x.fillRect(0, y + 120, w, 8);
      for (let i = 0; i < 10; i++) { x.fillStyle = cols[(s + i) % cols.length]; x.fillRect(8 + i * 25, y + 40 + rand() * 10, 20, 80 - rand() * 10); }
    }
  });
}

// generic printed artwork for the wider assortment (invented brands)
// o: {w,h, bg:[c1,c2], brand, name, sub, accent, ink, style:'band'|'burst'|'stripes'|'dots'|'photo', wrap:bool}
export function packArt(o) {
  const W = o.w || 512, H = o.h || 768;
  return canvasTex(W, H, (x, w, h) => {
    const g = x.createLinearGradient(0, 0, o.wrap ? w : 0, o.wrap ? 0 : h); g.addColorStop(0, o.bg[0]); g.addColorStop(1, o.bg[1] || o.bg[0]); x.fillStyle = g; x.fillRect(0, 0, w, h);
    const reps = o.wrap ? 2 : 1;
    for (let k = 0; k < reps; k++) {
      const cx = o.wrap ? w * (0.25 + k * 0.5) : w / 2, s = o.wrap ? h / 300 : w / 512;
      x.save(); x.translate(cx, 0);
      if (o.style === 'burst') { x.fillStyle = o.accent; x.beginPath(); for (let i = 0; i < 24; i++) { const a = i / 24 * Math.PI * 2, r = (i % 2 ? 70 : 105) * s; x.lineTo(Math.cos(a) * r, h * 0.55 + Math.sin(a) * r); } x.fill(); }
      if (o.style === 'band') { x.fillStyle = o.accent; x.fillRect(-w, h * 0.42, 2 * w, h * 0.2); }
      if (o.style === 'stripes') { x.fillStyle = o.accent; for (let i = -6; i < 6; i++) { x.beginPath(); x.moveTo(i * 60 * s, h); x.lineTo(i * 60 * s + 30 * s, h); x.lineTo(i * 60 * s + 140 * s, h * 0.45); x.lineTo(i * 60 * s + 110 * s, h * 0.45); x.fill(); } }
      if (o.style === 'dots') { for (let i = 0; i < 26; i++) { x.fillStyle = ['#e63946', '#f4a261', '#2a9d8f', '#e9c46a', '#8338ec'][i % 5]; x.beginPath(); x.ellipse((rand() - 0.5) * 300 * s, h * (0.45 + rand() * 0.3), 18 * s, 13 * s, rand() * 3, 0, Math.PI * 2); x.fill(); } }
      if (o.style === 'photo') { x.fillStyle = o.accent; x.beginPath(); x.ellipse(0, h * 0.58, 150 * s, 95 * s, 0, 0, Math.PI * 2); x.fill(); x.fillStyle = 'rgba(255,255,255,0.25)'; x.beginPath(); x.ellipse(-40 * s, h * 0.53, 45 * s, 22 * s, -0.4, 0, Math.PI * 2); x.fill(); }
      x.textAlign = 'center'; x.fillStyle = o.ink || '#fff';
      x.font = `italic bold ${Math.round(64 * s)}px Georgia, serif`; x.fillText(o.brand, 0, h * (o.wrap ? 0.3 : 0.17));
      x.font = `bold ${Math.round(50 * s)}px Helvetica, Arial`; x.fillText(o.name, 0, h * (o.wrap ? 0.88 : 0.84));
      if (o.sub) { x.font = `${Math.round(30 * s)}px Helvetica, Arial`; x.globalAlpha = 0.9; x.fillText(o.sub, 0, h * (o.wrap ? 0.97 : 0.92)); x.globalAlpha = 1; }
      x.restore();
    }
  });
}
