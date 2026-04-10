#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

print('=== Latest Email Queue Entries ===')
rows = frappe.get_all(
    'Email Queue',
    fields=['name','status','sender','creation','modified','priority'],
    order_by='creation desc',
    limit=5,
)
for r in rows:
    print(r)

if not rows:
    print('No queue entries to flush.')
    frappe.destroy()
    raise SystemExit(0)

name = rows[0]['name']
print('\nInspecting latest queue record:', name)
q = frappe.get_doc('Email Queue', name)
print('status before:', q.status)
print('error before:', (q.error or '')[:500])

# Attempt direct send
try:
    q.send()
    frappe.db.commit()
    q.reload()
    print('Direct q.send() success')
    print('status after direct send:', q.status)
except Exception as e:
    frappe.db.rollback()
    q.reload()
    print('Direct q.send() failed:', e)
    print('status after failure:', q.status)
    print('error after failure:', (q.error or '')[:1000])

# Attempt framework flush
print('\nRunning frappe.email.queue.flush() ...')
try:
    from frappe.email.queue import flush
    flush()
    frappe.db.commit()
    print('flush() executed')
except Exception as e:
    frappe.db.rollback()
    print('flush() failed:', e)

q.reload()
print('final status:', q.status)
print('final error:', (q.error or '')[:1000])

frappe.destroy()
PY
