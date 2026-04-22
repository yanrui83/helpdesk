#!/bin/bash
set -e

BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
EQ_DIR="$APP/helpdesk/helpdesk/doctype/hd_equipment"
EQ_PAGE_DIR="$APP/desk/src/pages/equipment"

echo "=== Deploying Equipment 3D Viewer feature ==="

# Step 1: Create HD Equipment doctype directory and files
if [ ! -d "$EQ_DIR" ]; then
    mkdir -p "$EQ_DIR"
    echo "Created HD Equipment doctype directory"
fi

cp /workspace/hd_equipment.json "$EQ_DIR/hd_equipment.json"
cp /workspace/hd_equipment.py "$EQ_DIR/hd_equipment.py"
touch "$EQ_DIR/__init__.py"
echo "DocType files copied"

# Step 2: Copy Equipment API
cp /workspace/equipment.py "$APP/helpdesk/api/equipment.py"
echo "equipment.py API copied"

# Step 3: Copy Vue components
cp /workspace/Equipment3DViewer.vue "$APP/desk/src/components/Equipment3DViewer.vue"
echo "Equipment3DViewer.vue component copied"

# Step 4: Create equipment pages directory and copy page components
mkdir -p "$EQ_PAGE_DIR"
cp /workspace/EquipmentList.vue "$EQ_PAGE_DIR/EquipmentList.vue"
cp /workspace/EquipmentDetail.vue "$EQ_PAGE_DIR/EquipmentDetail.vue"
echo "Equipment page components copied"

# Step 5: Copy updated router with equipment routes
cp /workspace/router_index.ts "$APP/desk/src/router/index.ts"
echo "router_index.ts updated with equipment routes"

# Step 6: Migrate to register new doctype
cd "$BENCH"
bench --site helpdesk.localhost migrate 2>&1 | tail -5
echo "Migration done"

# Step 7: Rebuild frontend
cd "$BENCH" && bench build --app helpdesk 2>&1 | tail -5
bench --site helpdesk.localhost clear-cache
echo "Frontend rebuilt"

echo "=== Equipment 3D Viewer feature deployed ==="
