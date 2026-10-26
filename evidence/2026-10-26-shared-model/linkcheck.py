# Offline check of local links in the built site: every href/src that is not external must resolve to a file.
import os, re, sys, urllib.parse
root = sys.argv[1]; bad = []; n = 0
for d, _, fs in os.walk(root):
    for f in fs:
        if not f.endswith('.html'): continue
        p = os.path.join(d, f); h = open(p, encoding='utf-8', errors='replace').read()
        h = re.sub(r'<script\b[^>]*>(?!\s*</script>).*?</script>', '', h, flags=re.S)  # inline scripts are not links
        for u in re.findall(r'(?:href|src)="([^"]+)"', h):
            if re.match(r'^(?:[a-z]+:|#|//)', u, re.I): continue
            n += 1
            t = urllib.parse.unquote(u.split('#')[0].split('?')[0])
            if not t: continue
            q = os.path.normpath(os.path.join(root, t.lstrip('/')) if t.startswith('/') else os.path.join(d, t))
            if os.path.isdir(q): q = os.path.join(q, 'index.html')
            if not os.path.exists(q): bad.append((os.path.relpath(p, root), u))
print('links checked', n, 'missing', len(bad)); [print(' ', *b) for b in bad[:30]]
