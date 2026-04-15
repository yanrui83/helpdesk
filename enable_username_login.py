import frappe

def run():
    frappe.db.set_single_value("System Settings", "allow_login_using_user_name", 1)
    frappe.db.commit()
    val = frappe.db.get_single_value("System Settings", "allow_login_using_user_name")
    print(f"System Settings.allow_login_using_user_name = {val}")

    # Also verify find_by_credentials will work by checking the field path
    from frappe.utils import cint
    login_with_username = cint(frappe.db.get_single_value("System Settings", "allow_login_using_user_name"))
    print(f"login_with_username (cint) = {login_with_username}")
    print("Username login is ENABLED" if login_with_username else "Username login is DISABLED")
