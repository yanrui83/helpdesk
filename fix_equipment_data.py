import frappe, os
os.chdir("/home/frappe/frappe-bench")
frappe.init(site="helpdesk.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

# Update EQ-0004 to customer 2311
doc = frappe.get_doc("HD Equipment", "EQ-0004")
print(f"Before: {doc.equipment_name}, customer={doc.customer}")
doc.customer = "2311"
doc.equipment_name = "IWT Moldrup 2311"
doc.save(ignore_permissions=True)
frappe.db.commit()
print(f"After: {doc.equipment_name}, customer={doc.customer}")

frappe.destroy()
print("Done!")
