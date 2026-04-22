import frappe, os
os.chdir("/home/frappe/frappe-bench")
frappe.init(site="helpdesk.localhost", sites_path="/home/frappe/frappe-bench/sites")
frappe.connect()

# Check contact/dynamic links for 2311
contact = frappe.db.get_value("Contact", {"user": "2311@moldrup.com"}, "name")
print("Contact for 2311@moldrup.com:", contact)
if contact:
    links = frappe.get_all("Dynamic Link", filters={"parent": contact, "parenttype": "Contact"}, fields=["link_doctype","link_name"])
    print("Dynamic links:", links)
else:
    print("No contact found!")

# Check all contacts
all_contacts = frappe.get_all("Contact", fields=["name","user","email_id"], limit=15)
print("\nAll contacts:")
for c in all_contacts:
    print(" ", c)

# Check equipment
eq = frappe.get_all("HD Equipment", fields=["name","equipment_name","customer","is_active"])
print("\nEquipment:", eq)

# Check what has_equipment would return for 2311 user
user = "2311@moldrup.com"
c2 = frappe.db.get_value("Contact", {"user": user}, "name")
print(f"\nhas_equipment check - contact for {user}:", c2)
if c2:
    dl = frappe.get_all("Dynamic Link", filters={"parent": c2, "parenttype": "Contact", "link_doctype": "HD Customer"}, fields=["link_name"], limit=1)
    print("HD Customer links:", dl)
    if dl:
        customer = dl[0]["link_name"]
        exists = frappe.db.exists("HD Equipment", {"customer": customer, "is_active": 1})
        print(f"Equipment exists for customer {customer}:", exists)

frappe.destroy()
