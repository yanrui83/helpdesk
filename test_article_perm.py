import os
os.chdir("/home/frappe/frappe-bench/sites")
import frappe
frappe.init(site="helpdesk.localhost")
frappe.connect()

# List website users
users = frappe.get_all("User", filters={"user_type": "Website User", "enabled": 1}, fields=["name", "full_name"], limit=5)
print("Website users:")
for u in users:
    roles = frappe.get_roles(u.name)
    print(f"  {u.name} ({u.full_name}) roles={roles}")

# Test get_article as a website user
if users:
    test_user = users[0].name
    print(f"\nTesting get_article as '{test_user}'...")
    frappe.set_user(test_user)
    try:
        from helpdesk.api.knowledge_base import get_article
        result = get_article("2v913g4pkd")
        print(f"  SUCCESS: got article '{result.get('title')}'")
    except Exception as e:
        print(f"  ERROR: {type(e).__name__}: {e}")
    
    # Also test has_permission directly
    print(f"\nDirect permission check:")
    has_perm = frappe.has_permission("HD Article", "read", doc="2v913g4pkd")
    print(f"  has_permission('HD Article', 'read') = {has_perm}")

frappe.destroy()
