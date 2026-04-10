#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe
from frappe.utils import now_datetime

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

print('=== Creating test ticket ===')
subject = f'Notification Test Ticket {now_datetime()}'

t = frappe.new_doc('HD Ticket')
t.subject = subject
# use existing customer owner
t.raised_by = '2311@moldrup.com'
t.insert(ignore_permissions=True)
frappe.db.commit()
print('Created ticket:', t.name, '| subject:', subject)

print('\n=== Recent Email Queue Entries ===')
rows = frappe.get_all('Email Queue', fields=['name','status','sender','creation'], order_by='creation desc', limit=10)
for r in rows:
    print(r)

print('\n=== Recent Email Queue Recipient Entries ===')
try:
    rq = frappe.get_all('Email Queue Recipient', fields=['parent','recipient','status','creation'], order_by='creation desc', limit=20)
    for r in rq:
        print(r)
except Exception as e:
    print('Email Queue Recipient read error:', e)

frappe.destroy()
PY
