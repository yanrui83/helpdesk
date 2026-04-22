#!/bin/bash
BENCH=/home/frappe/frappe-bench
APP=$BENCH/apps/helpdesk
EQ_DIR=$APP/helpdesk/helpdesk/doctype/hd_equipment
EQ_PAGE_DIR=$APP/desk/src/pages/equipment

echo "Step 1: Create doctype directory"
mkdir -p "$EQ_DIR"
cp /workspace/hd_equipment.json "$EQ_DIR/hd_equipment.json"
cp /workspace/hd_equipment.py "$EQ_DIR/hd_equipment.py"
touch "$EQ_DIR/__init__.py"
echo "  DocType files copied to $EQ_DIR"

echo "Step 2: Copy equipment API"
cp /workspace/equipment.py "$APP/helpdesk/api/equipment.py"
echo "  equipment.py copied"

echo "Step 3: Copy Vue components"
cp /workspace/Equipment3DViewer.vue "$APP/desk/src/components/Equipment3DViewer.vue"
echo "  Equipment3DViewer.vue copied"

echo "Step 4: Copy page components"
mkdir -p "$EQ_PAGE_DIR"
cp /workspace/EquipmentList.vue "$EQ_PAGE_DIR/EquipmentList.vue"
cp /workspace/EquipmentDetail.vue "$EQ_PAGE_DIR/EquipmentDetail.vue"
echo "  Page components copied"

echo "Step 5: Copy router"
cp /workspace/router_index.ts "$APP/desk/src/router/index.ts"
echo "  Router updated"

echo "Step 6: Run migrate to register HD Equipment DocType"
cd "$BENCH"
bench --site helpdesk.localhost migrate
echo "  Migration done"

echo "Step 7: Rebuild frontend"
bench build --app helpdesk
bench --site helpdesk.localhost clear-cache
echo "  Frontend rebuilt"

echo "=== Equipment deployment complete ==="
