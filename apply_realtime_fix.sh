#!/bin/bash
set -e

cp /workspace/admin_notifications.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/admin_notifications.py

cd /home/frappe/frappe-bench
bench --site helpdesk.localhost clear-cache

# Disable queued Notification rules to avoid duplicate/delayed emails
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python - <<'PY'
import frappe

frappe.init(site='helpdesk.localhost')
frappe.connect()
frappe.set_user('Administrator')

for name in ['HD New Ticket Email to Admin', 'HD Agent Reply Email to Admin']:
    if frappe.db.exists('Notification', name):
        n = frappe.get_doc('Notification', name)
        n.enabled = 0
        n.save(ignore_permissions=True)
        print('Disabled Notification:', name)

frappe.db.commit()
frappe.destroy()
PY

echo "Realtime immediate-send fix applied."
