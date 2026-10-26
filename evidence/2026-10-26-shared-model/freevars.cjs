// Free (unresolved) identifiers of a script, as JSON; used by split_robot_bundle.py.
// Needs espree and eslint-scope (npm install espree@10 eslint-scope@8; NODE_PATH to their node_modules).
const espree = require('espree'), escope = require('eslint-scope'), fs = require('fs');
const src = fs.readFileSync(process.argv[2], 'utf8');
const ast = espree.parse(src, {ecmaVersion: 2022, sourceType: 'script', range: true});
const sm = escope.analyze(ast, {ecmaVersion: 2022, sourceType: 'script'});
const decl = new Set(sm.globalScope.variables.map(v => v.name)), free = new Set();
for (const r of sm.globalScope.through) if (!decl.has(r.identifier.name)) free.add(r.identifier.name);
console.log(JSON.stringify([...free].sort()));
