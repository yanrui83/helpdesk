import frappe, os
os.chdir("/home/frappe/frappe-bench")
frappe.init("helpdesk.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

customers = frappe.get_all("HD Customer", limit=5, pluck="name")
if not customers:
    cust = frappe.get_doc({"doctype": "HD Customer", "customer_name": "Test Customer"})
    cust.insert(ignore_permissions=True)
    customer_id = cust.name
    print("Created customer:", customer_id)
else:
    customer_id = customers[0]
    print("Using customer:", customer_id)

existing = frappe.get_all("HD Equipment", filters={"equipment_name": "Equipment 2311"}, limit=1)
if existing:
    print("Equipment exists:", existing[0].name)
else:
    eq = frappe.get_doc({
        "doctype": "HD Equipment",
        "equipment_name": "Equipment 2311",
        "customer": customer_id,
        "model_file": "/assets/helpdesk/3d-viewer/2311.glb",
        "is_active": 1,
        "config": "",
    })
    eq.insert(ignore_permissions=True)
    print("Created equipment:", eq.name)

frappe.db.commit()
frappe.destroy()
