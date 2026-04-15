import frappe
from frappe.utils.password import check_password

def run():
    users = frappe.get_all(
        "User",
        filters={"user_type": "Website User", "enabled": 1},
        fields=["name", "username"],
    )
    print("Checking password status for portal users...")
    for u in users:
        if u.name == "Guest":
            continue
        # Check __Auth table directly
        has_pwd = frappe.db.exists(
            "__Auth",
            {"doctype": "User", "name": u.name, "fieldname": "password"}
        )
        print(f"  {u.name} (username={u.username}): password={'SET' if has_pwd else 'NOT SET'}")
