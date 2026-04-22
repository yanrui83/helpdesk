"""Fix ed-footer CSS and copy viewer to sites/assets."""
import subprocess

path = '/home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/3d-viewer/index.html'
with open(path) as f:
    c = f.read()

old = '.ed-footer{padding:12px 14px;border-top:1px solid var(--border);display:flex;gap:6px;flex-shrink:0}'
new = '.ed-footer{padding:12px 14px;border-top:1px solid var(--border);display:flex;gap:6px;flex-shrink:0;flex-wrap:wrap;overflow-x:auto}'
c2 = c.replace(old, new, 1)

if c2 == c:
    print('MISS: footer style not found, checking existing...')
    import re
    m = re.search(r'\.ed-footer\{[^}]+\}', c)
    if m:
        print('Found:', m.group()[:120])
else:
    with open(path, 'w') as f:
        f.write(c2)
    print('OK: ed-footer updated with flex-wrap:wrap')

# Also copy to sites/assets
import shutil, os
src = '/home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/3d-viewer/index.html'
dst = '/home/frappe/frappe-bench/sites/assets/helpdesk/3d-viewer/index.html'
os.makedirs(os.path.dirname(dst), exist_ok=True)
shutil.copy2(src, dst)
print(f'Copied viewer HTML to {dst}')
