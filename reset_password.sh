#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()

# Reset admin password
from frappe.utils.password import update_password
update_password('Administrator', 'Admin1234')
frappe.db.commit()
print('Admin password reset successfully to: Admin1234')

frappe.destroy()
"
