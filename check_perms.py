import frappe
import json

def run():
    # 1. Show current HD Customer Tag permissions
    meta = frappe.get_meta("HD Customer Tag")
    print("=== HD Customer Tag permissions ===")
    for p in meta.permissions:
        print(f"  role={p.role}, read={p.read}, write={p.write}, create={p.create}")

    # 2. Show roles of current portal users (non-system users)
    print("\n=== Portal user roles ===")
    portal_users = frappe.get_all(
        "User",
        filters={"user_type": "Website User", "enabled": 1},
        fields=["name"],
        limit=5,
    )
    for u in portal_users:
        roles = frappe.get_roles(u.name)
        print(f"  {u.name}: {roles}")

    # 3. Show HD Ticket Type permissions for reference
    print("\n=== HD Ticket Type permissions (reference) ===")
    hd_ticket_type_meta = frappe.get_meta("HD Ticket Type")
    for p in hd_ticket_type_meta.permissions:
        print(f"  role={p.role}, read={p.read}")
