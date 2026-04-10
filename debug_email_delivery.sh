#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe
from frappe.utils import now_datetime

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

print('=== Email Account Check ===')
try:
    ea = frappe.get_doc('Email Account', 'xu.yanrui1983@gmail.com')
    print('enabled:', ea.enable_outgoing, 'default_outgoing:', ea.default_outgoing)
    print('smtp:', ea.smtp_server, ea.smtp_port, 'tls:', ea.use_tls)
except Exception as e:
    print('email account read error:', e)

print('\n=== Recent Email Queue (last 10) ===')
rows = frappe.get_all(
    'Email Queue',
    fields=['name', 'status', 'sender', 'creation', 'modified'],
    order_by='creation desc',
    limit=10,
)
if not rows:
    print('No Email Queue records found')
else:
    for r in rows:
        print(f"{r['creation']} | {r['name']} | {r['status']} | {r.get('sender')}")

print('\n=== Recent Error Log (email-related, last 20) ===')
errors = frappe.get_all(
    'Error Log',
    fields=['name', 'method', 'creation', 'error'],
    order_by='creation desc',
    limit=20,
)
found = 0
for e in errors:
    txt = (e.get('error') or '').lower()
    if 'smtp' in txt or 'email' in txt or 'mail' in txt:
        found += 1
        snippet = (e.get('error') or '').split('\n')[0][:220]
        print(f"{e['creation']} | {e['name']} | {snippet}")
if found == 0:
    print('No recent email-related error log entries found')

print('\n=== Sending Fresh Test Email (force now) ===')
subject = f"Helpdesk Live Test {now_datetime()}"
msg = '<p>This is a live delivery test from Frappe Helpdesk.</p><p>If you can read this, outgoing mail works.</p>'
try:
    frappe.sendmail(
        recipients=['xu.yanrui1983@gmail.com'],
        sender='xu.yanrui1983@gmail.com',
        subject=subject,
        message=msg,
        now=True,
    )
    print('sendmail() completed successfully')
except Exception as ex:
    print('sendmail error:', ex)

print('\n=== Post-send Queue Snapshot ===')
rows2 = frappe.get_all(
    'Email Queue',
    fields=['name', 'status', 'sender', 'creation', 'modified'],
    order_by='creation desc',
    limit=5,
)
for r in rows2:
    print(f"{r['creation']} | {r['name']} | {r['status']} | {r.get('sender')}")

frappe.destroy()
PY
