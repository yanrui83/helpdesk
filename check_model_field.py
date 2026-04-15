import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()
v = frappe.db.get_single_value('HD Settings', 'ai_assistant_model')
print(f'ai_assistant_model = [{v}]')
meta = frappe.get_meta('HD Settings')
field = meta.get_field('ai_assistant_model')
if field:
    print(f'Field exists: label={field.label}, fieldtype={field.fieldtype}, default={field.default}')
else:
    print('Field NOT found in meta!')
frappe.destroy()
