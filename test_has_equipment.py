import frappe, os
os.chdir("/home/frappe/frappe-bench")
frappe.init(site="helpdesk.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()
frappe.set_user("2311@moldrup.com")

from helpdesk.api.equipment import has_equipment, _is_agent, _get_customer_for_user
print("is_agent:", _is_agent())
print("customer:", _get_customer_for_user())
result = has_equipment()
print("has_equipment result:", result, type(result))

frappe.destroy()
