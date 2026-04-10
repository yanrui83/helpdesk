#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()

cats = frappe.get_all('HD Article Category', fields=['name','category_name','parent_category'])
for c in cats:
    print(f'{c.name}: {c.category_name} | parent={c.parent_category}')

print()
print('Articles by status:')
for s in ['Published','Draft','Archived','Trash']:
    print(f'  {s}: {frappe.db.count(\"HD Article\", {\"status\": s})}')

print()
from helpdesk.api import kb_custom
print(f'delete_category_safe exists: {hasattr(kb_custom, \"delete_category_safe\")}')

with open('/home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/doc.py') as f:
    d = f.read()
print(f'doc.py has raw_options: {\"raw_options\" in d}')

frappe.destroy()
"
