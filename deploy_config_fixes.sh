#!/bin/bash
set -e
BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
DESK="$APP/desk/src"
API="$APP/helpdesk/api"

echo "=== Deploy: Config save + Import JSON + Auto-redirect ==="

# 1. Patch 3D viewer (postMessage on save + Import JSON button)
echo "1. Patching 3D viewer..."
sed -i 's/\r$//' /workspace/patch_viewer_config.py
python3 /workspace/patch_viewer_config.py

# 2. Deploy updated EquipmentDetail.vue (postMessage listener + server save)
echo "2. Deploying EquipmentDetail.vue..."
cp /workspace/EquipmentDetail.vue "$DESK/pages/equipment/EquipmentDetail.vue"

# 3. Deploy updated EquipmentList.vue (auto-redirect)
echo "3. Deploying EquipmentList.vue..."
cp /workspace/EquipmentList.vue "$DESK/pages/equipment/EquipmentList.vue"

# 4. Deploy updated equipment.py (ensure save_equipment_config is up to date)
echo "4. Deploying equipment.py..."
cp /workspace/equipment.py "$API/equipment.py"

# 5. Rebuild frontend
echo "5. Building frontend..."
cd "$BENCH"
bench build --app helpdesk 2>&1 | tail -6

echo ""
echo "=== Done! Hard-refresh browser (Ctrl+Shift+R) ==="
echo "✓ Save Config in editor now syncs to server + customer view"
echo "✓ Import JSON button added to editor panel"
echo "✓ Customer with 1 equipment skips list, opens 3D viewer directly"
