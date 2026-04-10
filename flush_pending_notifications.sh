#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

print('=== Pending before flush ===')
before = frappe.get_all('Email Queue', fields=['name','status','creation'], filters={'status':'Not Sent'}, order_by='creation desc', limit=20)
for r in before:
    print(r)

print('\nRunning flush() ...')
from frappe.email.queue import flush
flush()
frappe.db.commit()

print('\n=== Status after flush ===')
after = frappe.get_all('Email Queue', fields=['name','status','creation'], order_by='creation desc', limit=20)
for r in after:
    print(r)

print('\n=== Recipient statuses ===')
rq = frappe.get_all('Email Queue Recipient', fields=['parent','recipient','status','creation'], order_by='creation desc', limit=20)
for r in rq:
    print(r)

frappe.destroy()
PY
