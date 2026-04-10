#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

print('=== System Settings ===')
try:
    ss = frappe.get_single('System Settings')
    print('disable_email_alerts:', getattr(ss, 'disable_email_alerts', None))
except Exception as e:
    print('System Settings read error:', e)

print('\n=== Email Account Defaults ===')
try:
    rows = frappe.get_all('Email Account', fields=['name','email_id','enable_outgoing','default_outgoing','enable_incoming','default_incoming'])
    for r in rows:
        print(r)
except Exception as e:
    print('Email Account error:', e)

print('\n=== Existing Notification Docs ===')
try:
    notifs = frappe.get_all('Notification', fields=['name','document_type','enabled','channel','event','condition','recipients'], order_by='modified desc')
    if not notifs:
        print('No Notification docs found')
    for n in notifs:
        print('---')
        for k,v in n.items():
            print(f'{k}: {v}')
except Exception as e:
    print('Notification read error:', e)

print('\n=== Recent HD Ticket (last 5) ===')
try:
    tickets = frappe.get_all('HD Ticket', fields=['name','subject','creation','owner','status'], order_by='creation desc', limit=5)
    for t in tickets:
        print(t)
except Exception as e:
    print('HD Ticket read error:', e)

print('\n=== Recent Communication on HD Ticket (last 10) ===')
try:
    comm = frappe.get_all('Communication', fields=['name','creation','reference_doctype','reference_name','sent_or_received','communication_type','subject','sender','recipients'], filters={'reference_doctype':'HD Ticket'}, order_by='creation desc', limit=10)
    for c in comm:
        print(c)
except Exception as e:
    print('Communication read error:', e)

frappe.destroy()
PY
