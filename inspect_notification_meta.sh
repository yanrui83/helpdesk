#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

print('=== Notification Meta Fields ===')
meta = frappe.get_meta('Notification')
for f in meta.fields:
    print(f.fieldname, '|', f.fieldtype, '| reqd=', f.reqd, '| options=', f.options)

print('\n=== Notification child tables ===')
for f in meta.fields:
    if f.fieldtype == 'Table':
        print('table:', f.fieldname, '->', f.options)
        cmeta = frappe.get_meta(f.options)
        for cf in cmeta.fields:
            print('  ', cf.fieldname, '|', cf.fieldtype, '| reqd=', cf.reqd, '| options=', cf.options)

print('\n=== Existing Notifications (name, doc, enabled) ===')
rows = frappe.get_all('Notification', fields=['name','document_type','enabled','event','channel','condition'], order_by='modified desc')
if not rows:
    print('none')
for r in rows:
    print(r)

frappe.destroy()
PY
