#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe
from frappe.utils import now_datetime

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

# Pick latest ticket
ticket = frappe.get_all('HD Ticket', fields=['name','subject'], order_by='creation desc', limit=1)
if not ticket:
    print('No ticket found for reply test')
    frappe.destroy()
    raise SystemExit(1)

ticket_name = str(ticket[0]['name'])
print('Using ticket:', ticket_name)

# Create a Sent communication (agent reply style)
comm = frappe.new_doc('Communication')
comm.communication_type = 'Communication'
comm.communication_medium = 'Email'
comm.sent_or_received = 'Sent'
comm.reference_doctype = 'HD Ticket'
comm.reference_name = ticket_name
comm.subject = f'Reply Notification Test {now_datetime()}'
comm.content = '<p>Testing agent reply notification.</p>'
comm.sender = 'xu.yanrui1983@gmail.com'
comm.recipients = '2311@moldrup.com'
comm.insert(ignore_permissions=True)
frappe.db.commit()
print('Created communication:', comm.name)

# Check latest admin mail entries
rows = frappe.db.sql('''
    select eq.name, eq.status, eq.creation, eq.sender, eqr.recipient
    from `tabEmail Queue` eq
    join `tabEmail Queue Recipient` eqr on eqr.parent = eq.name
    where eqr.recipient=%s
    order by eq.creation desc
    limit 5
''', ('xu.yanrui1983@gmail.com',), as_dict=True)

print('Latest admin queue rows:')
for r in rows:
    print(r)

frappe.destroy()
PY
