import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()

print('=== Test 1: Category Hierarchy ===')
cats = frappe.get_all('HD Article Category', fields=['name', 'category_name', 'parent_category'])
for c in cats:
    parent_name = ''
    if c.get('parent_category'):
        parent_name = frappe.db.get_value('HD Article Category', c['parent_category'], 'category_name')
    label = (parent_name + ' > ' + c['category_name']) if parent_name else c['category_name']
    print(f'  {c["name"]}: {label}')

print()
print('=== Test 2: delete_category_safe exists ===')
from helpdesk.api import kb_custom
print(f'  has delete_category_safe: {hasattr(kb_custom, "delete_category_safe")}')

print()
print('=== Test 3: doc.py has raw_options ===')
with open('/home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/doc.py') as f:
    doc_content = f.read()
print(f'  has raw_options: {"raw_options" in doc_content}')
print(f'  has parent_category check: {"parent_category" in doc_content}')

print()
print('=== Test 4: Articles by status ===')
for status in ['Published', 'Draft', 'Archived', 'Trash']:
    count = frappe.db.count('HD Article', {'status': status})
    print(f'  {status}: {count}')

frappe.destroy()
