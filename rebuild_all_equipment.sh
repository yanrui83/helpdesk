#!/bin/bash
BENCH=/home/frappe/frappe-bench
APP=$BENCH/apps/helpdesk
VIEWER_DIR=$APP/helpdesk/public/3d-viewer
EQ_PAGE_DIR=$APP/desk/src/pages/equipment

echo "=== Full Equipment Rebuild ==="

# 1. Update viewer HTML with URL param support
cp /workspace/3D_Sparepart.html "$VIEWER_DIR/index.html"
echo "  Viewer HTML updated"

# 2. Update equipment API
cp /workspace/equipment.py "$APP/helpdesk/api/equipment.py"
echo "  API updated"

# 3. Update Vue components
cp /workspace/EquipmentList.vue "$EQ_PAGE_DIR/EquipmentList.vue"
cp /workspace/EquipmentDetail.vue "$EQ_PAGE_DIR/EquipmentDetail.vue"
echo "  Vue pages updated"

# 4. Build frontend
cd "$BENCH"
bench build --app helpdesk 2>&1 | tail -5
bench --site helpdesk.localhost clear-cache
echo "  Frontend rebuilt"

# 5. Create a test equipment record
cd "$BENCH"
python3 -c "
import frappe
frappe.init('helpdesk.localhost')
frappe.connect()

# Get first active customer
customers = frappe.get_all('HD Customer', filters={'disabled': 0}, limit=5, pluck='name')
if not customers:
    print('No customers found - creating test customer')
    cust = frappe.get_doc({'doctype': 'HD Customer', 'customer_name': 'Test Customer'})
    cust.insert(ignore_permissions=True)
    customer_id = cust.name
else:
    customer_id = customers[0]
    print(f'Using customer: {customer_id}')

# Check if equipment already exists
existing = frappe.get_all('HD Equipment', filters={'equipment_name': 'Equipment 2311'}, limit=1)
if existing:
    print(f'Equipment already exists: {existing[0].name}')
else:
    eq = frappe.get_doc({
        'doctype': 'HD Equipment',
        'equipment_name': 'Equipment 2311',
        'customer': customer_id,
        'model_file': '/assets/helpdesk/3d-viewer/2311.glb',
        'is_active': 1,
        'config': ''
    })
    eq.insert(ignore_permissions=True)
    print(f'Created equipment: {eq.name}')

frappe.db.commit()
frappe.destroy()
"

echo "=== Done ==="
