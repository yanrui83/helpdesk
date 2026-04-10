#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()

# Fix category names with trailing whitespace/newlines
cats = frappe.get_all('HD Article Category', fields=['name','category_name','parent_category'])
for c in cats:
    clean = c.category_name.strip()
    if clean != c.category_name:
        print(f'Fixing category name: [{repr(c.category_name)}] -> [{clean}]')
        frappe.db.set_value('HD Article Category', c.name, 'category_name', clean, update_modified=False)

frappe.db.commit()

# Refresh
cats = frappe.get_all('HD Article Category', fields=['name','category_name','parent_category'])
print('Categories after fix:')
for c in cats:
    print(f'  {c.name}: [{c.category_name}] parent={c.parent_category}')

# Create HMI if not exists
hmi = [c for c in cats if c.category_name.strip() == 'HMI']
auto = [c for c in cats if c.category_name.strip() == 'Automation']

if not hmi and auto:
    print()
    print('Creating HMI sub-category under Automation...')
    cat = frappe.new_doc('HD Article Category')
    cat.category_name = 'HMI'
    cat.parent_category = auto[0].name
    cat.insert(ignore_permissions=True)
    
    art = frappe.new_doc('HD Article')
    art.title = 'HMI Overview'
    art.category = cat.name
    art.status = 'Published'
    art.content = '<p>Overview of HMI systems and interfaces.</p>'
    art.insert(ignore_permissions=True)
    
    frappe.db.commit()
    print(f'Created HMI: {cat.name} under Automation ({auto[0].name})')
elif hmi:
    print(f'HMI already exists: {hmi[0].name}')

# Show final state
print()
cats = frappe.get_all('HD Article Category', fields=['name','category_name','parent_category'])
print('Final categories:')
for c in cats:
    p = ''
    if c.parent_category:
        p = frappe.db.get_value('HD Article Category', c.parent_category, 'category_name') or ''
    label = (p + ' > ' + c.category_name) if p else c.category_name
    print(f'  {label}')

frappe.destroy()
"
