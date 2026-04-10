#!/bin/bash
python - <<'PY'
import json
path = '/home/frappe/frappe-bench/sites/helpdesk.localhost/site_config.json'
with open(path, 'r', encoding='utf-8') as f:
    data = json.load(f)

data['mute_emails'] = 0

with open(path, 'w', encoding='utf-8') as f:
    json.dump(data, f, indent=1)
    f.write('\n')

print('mute_emails set to 0 in site_config.json')
PY
