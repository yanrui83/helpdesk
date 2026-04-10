#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import time
import frappe
from frappe.utils import now_datetime

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

subject = f'Latency Test Ticket {now_datetime()}'
t = frappe.new_doc('HD Ticket')
t.subject = subject
t.raised_by = '2311@moldrup.com'
t.insert(ignore_permissions=True)
frappe.db.commit()
print('Created ticket:', t.name)

# Find queue row targeting admin created after ticket creation
for i in range(1, 7):
    rows = frappe.db.sql('''
        select eq.name, eq.status, eq.creation
        from `tabEmail Queue` eq
        join `tabEmail Queue Recipient` eqr on eqr.parent = eq.name
        where eqr.recipient=%s
        order by eq.creation desc
        limit 3
    ''', ('xu.yanrui1983@gmail.com',), as_dict=True)
    print(f'check {i*10}s:', rows)
    time.sleep(10)

frappe.destroy()
PY
