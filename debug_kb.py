import os
os.chdir("/home/frappe/frappe-bench/sites")
import frappe
frappe.init(site="helpdesk.localhost")
frappe.connect()

# Check categories and parent relationships
cats = frappe.get_all("HD Article Category", fields=["name","category_name","parent_category"])
print("=== CATEGORIES ===")
for c in cats:
    print(f"  {c.name}: {c.category_name} | parent={c.parent_category}")

# Check if trash articles exist
trash = frappe.get_all("HD Article", filters={"status":"Trash"}, fields=["name","title","status","trashed_on"])
print()
print("=== TRASHED ARTICLES ===")
for t in trash:
    print(f"  {t.name}: {t.title} status={t.status} trashed_on={t.trashed_on}")

# Check all articles and their statuses
print()
print("=== ALL ARTICLES ===")
articles = frappe.get_all("HD Article", fields=["name","title","status","category"], order_by="modified desc")
for a in articles:
    print(f"  {a.name}: {a.title} | status={a.status} | cat={a.category}")

# Check HD Article schema for trashed_on field
meta = frappe.get_meta("HD Article")
fields = [f.fieldname for f in meta.fields]
print()
print("=== HD Article fields ===")
print("  Has trashed_on:", "trashed_on" in fields)
print("  Status options:", [f.options for f in meta.fields if f.fieldname == "status"])

frappe.destroy()
