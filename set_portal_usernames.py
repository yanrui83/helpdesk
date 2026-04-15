import frappe

def run():
    """Set username for portal users that don't have one yet.
    Uses the local part of the email (before @) as username, but only if unique."""
    portal_users = frappe.get_all(
        "User",
        filters={"user_type": "Website User", "enabled": 1},
        fields=["name", "username", "email"],
    )
    for u in portal_users:
        if u.username:
            print(f"  {u.name}: username already set = '{u.username}'")
            continue
        # Derive username from the part before the @ (e.g. "2311" from "2311@moldrup.com")
        candidate = u.name.split("@")[0]
        # Make sure it's unique
        if frappe.db.exists("User", {"username": candidate}):
            print(f"  {u.name}: '{candidate}' already taken, skipping — set manually")
            continue
        user_doc = frappe.get_doc("User", u.name)
        user_doc.username = candidate
        user_doc.save(ignore_permissions=True)
        print(f"  {u.name}: username set to '{candidate}'")
    frappe.db.commit()
    print("Done.")
