import frappe
frappe.init(site="helpdesk.localhost")
frappe.connect()
print("site_url:", frappe.utils.get_url())
frappe.destroy()
