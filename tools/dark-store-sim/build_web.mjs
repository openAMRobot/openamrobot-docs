import fs from 'fs';
const fam = [['Barlow', 'barlow', [400, 500, 600]], ['Barlow Semi Condensed', 'barlow-semi-condensed', [500, 600, 700]], ['IBM Plex Mono', 'ibm-plex-mono', [400, 500]]];
let css = '';
for (const [name, pkg, ws] of fam) for (const w of ws) {
  const b = fs.readFileSync(`node_modules/@fontsource/${pkg}/files/${pkg}-latin-${w}-normal.woff2`).toString('base64');
  css += `@font-face{font-family:"${name}";font-style:normal;font-weight:${w};font-display:swap;src:url(data:font/woff2;base64,${b}) format("woff2");}\n`;
}
let body = fs.readFileSync('out/artifact.html', 'utf8');
body = body.replace(/<link rel="preconnect"[^>]*>\n?/, '').replace(/<link rel="stylesheet" href="https:\/\/fonts\.googleapis\.com[^>]*>\n?/, '');
body = body.replace('<style>', '<style>\n' + css);
const head = `<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<meta name="description" content="Interactive 3D simulation of the open-source OpenAMRobot 2.0 mobile manipulator picking a grocery order in a dark store: DOLD Hexalift V4 lift, two OpenArm 2.0 arms, reach and camera checks.">
<meta property="og:title" content="OpenAMRobot 2.0 dark-store pick simulation">
<meta property="og:description" content="Interactive 3D simulation: OpenAMRobot 2.0 picks an 8-item grocery order from two aisles and hands it over at the packing table.">
<style>body{margin:0}[hidden]{display:none!important}</style>
</head>
<body>
`;
fs.mkdirSync('out/web', { recursive: true });
fs.writeFileSync('out/web/index.html', head + body + '\n</body>\n</html>\n');
console.log('web', (fs.statSync('out/web/index.html').size / 1e6).toFixed(2), 'MB', 'google refs:', (body.match(/googleapis|gstatic/g) || []).length);
