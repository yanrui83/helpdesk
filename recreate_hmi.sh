#!/bin/bash
cd /home/frappe/frappe-bench/sites
/home/frappe/frappe-bench/env/bin/python -c "
import frappe
frappe.init(site='helpdesk.localhost')
frappe.connect()

# Check all categories
cats = frappe.get_all('HD Article Category', fields=['name','category_name','parent_category'])
print('Current categories:', len(cats))
for c in cats:
    print(f'  {c.name}: {c.category_name} | parent={c.parent_category}')

# Check if HMI exists
hmi = [c for c in cats if c.category_name == 'HMI']
if not hmi:
    print()
    print('HMI category not found - creating it as sub-category of Automation...')
    automation = [c for c in cats if c.category_name == 'Automation']
    if automation:
        cat = frappe.new_doc('HD Article Category')
        cat.category_name = 'HMI'
        cat.parent_category = automation[0].name
        cat.insert(ignore_permissions=True)
        
        # Create default article
        art = frappe.new_doc('HD Article')
        art.title = 'HMI Overview'
        art.category = cat.name
        art.status = 'Published'
        art.content = '<p>Overview of HMI systems.</p>'
        art.insert(ignore_permissions=True)
        
        frappe.db.commit()
        print(f'Created HMI category: {cat.name} under {automation[0].name}')
        print(f'Created article: {art.name}')
    else:
        print('ERROR: Automation category not found')
else:
    print(f'HMI already exists: {hmi[0].name}')

# Show final state
print()
print('Final categories:')
cats = frappe.get_all('HD Article Category', fields=['name','category_name','parent_category'])
for c in cats:
    p = ''
    if c.parent_category:
        p = frappe.db.get_value('HD Article Category', c.parent_category, 'category_name') or ''
    label = (p + ' > ' + c.category_name) if p else c.category_name
    print(f'  {label}')

frappe.destroy()
"
