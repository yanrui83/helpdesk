import os
os.chdir("/home/frappe/frappe-bench/sites")
import frappe
frappe.init(site="helpdesk.localhost")
frappe.connect()
articles = frappe.get_all("HD Article", fields=["name","title","status","content"], limit=10)
for a in articles:
    print("=== ARTICLE ===")
    print("Name:", a.name)
    print("Title:", a.title)
    print("Status:", a.status)
    content = (a.content or "")[:500]
    print("Content (first 500 chars):", repr(content))
    print()
frappe.destroy()
