#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe
from frappe.utils import now_datetime

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

subject = f'Realtime Hook Ticket {now_datetime()}'
t = frappe.new_doc('HD Ticket')
t.subject = subject
t.raised_by = '2311@moldrup.com'
t.insert(ignore_permissions=True)
frappe.db.commit()
print('Created ticket:', t.name)

# Check latest queue rows for admin
rows = frappe.db.sql('''
    select eq.name, eq.status, eq.creation, eq.sender, eqr.recipient
    from `tabEmail Queue` eq
    join `tabEmail Queue Recipient` eqr on eqr.parent = eq.name
    where eqr.recipient=%s
    order by eq.creation desc
    limit 5
''', ('xu.yanrui1983@gmail.com',), as_dict=True)
print('Latest admin email rows:')
for r in rows:
    print(r)

frappe.destroy()
PY
