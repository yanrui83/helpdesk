import frappe, os
os.chdir("/home/frappe/frappe-bench")
frappe.init(site="helpdesk.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

eq = frappe.get_all("HD Equipment", fields=["name","equipment_name","customer","model_file","is_active"])
print("Equipment:", eq)

cust = frappe.get_all("HD Customer", fields=["name","customer_name"])
print("Customers:", cust)

contacts = frappe.get_all("Contact", fields=["name","user","email_id"], limit=10)
print("Contacts:", contacts)

frappe.destroy()
