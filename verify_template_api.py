import frappe
import json

def run():
    from helpdesk.helpdesk.doctype.hd_ticket_template.api import get_fields_meta
    fields = get_fields_meta("Default")
    for f in fields:
        print(f"  {f.fieldname}: type={f.fieldtype}, hide={f.hide_from_customer}, req={f.required}, depends_on={repr(f.depends_on)}, options={f.options}")
