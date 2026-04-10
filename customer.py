import frappe
from frappe.utils.password import update_password

from helpdesk.utils import agent_only


@frappe.whitelist()
@agent_only
def add_customer(email: str, first_name: str, password: str, last_name: str = ""):
    """Manually create a customer user with a given password. No email is sent."""

    if not email or not first_name or not password:
        frappe.throw("Email, first name, and password are required.")

    if len(password) < 8:
        frappe.throw("Password must be at least 8 characters.")

    if frappe.db.exists("User", email):
        frappe.throw(f"User {email} already exists.")

    user = frappe.get_doc({
        "doctype": "User",
        "email": email,
        "first_name": first_name,
        "last_name": last_name,
        "send_welcome_email": 0,
        "user_type": "Website User",
        "enabled": 1,
        "roles": [{"role": "Customer"}],
    }).insert(ignore_permissions=True)

    update_password(user=user.name, pwd=password)

    contact = frappe.get_doc({
        "doctype": "Contact",
        "first_name": first_name,
        "last_name": last_name,
        "email_id": email,
        "email_ids": [{"email_id": email, "is_primary": 1}],
        "user": user.name,
    }).insert(ignore_permissions=True)

    frappe.db.commit()

    return {
        "user": user.name,
        "contact": contact.name,
        "message": f"Customer {first_name} ({email}) created successfully.",
    }
