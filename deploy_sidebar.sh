#!/bin/bash
set -e

BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
DESK="$APP/desk/src"
API="$APP/helpdesk/api"

echo "=== Deploying Spare Part sidebar + Equipment shortcut ==="

# 1. Deploy updated layoutSettings.ts
echo "1. Deploying layoutSettings.ts..."
cp /workspace/layoutSettings.ts "$DESK/components/layouts/layoutSettings.ts"
echo "   layoutSettings.ts deployed."

# 2. Deploy updated equipment.py (has_equipment API)
echo "2. Deploying equipment.py..."
cp /workspace/equipment.py "$API/equipment.py"
echo "   equipment.py deployed."

# 3. Deploy updated EquipmentList.vue
echo "3. Deploying EquipmentList.vue..."
cp /workspace/EquipmentList.vue "$DESK/pages/equipment/EquipmentList.vue"
echo "   EquipmentList.vue deployed."

# 4. Patch Sidebar.vue
echo "4. Patching Sidebar.vue..."
python3 /workspace/patch_sidebar.py
echo "   Sidebar.vue patched."

# 5. Fix equipment data (EQ-0004 -> customer 2311)
echo "5. Fixing equipment data..."
cd "$BENCH"
./env/bin/python3 /workspace/fix_equipment_data.py
echo "   Equipment data fixed."

# 6. Rebuild frontend
echo "6. Building frontend..."
cd "$BENCH"
bench build --app helpdesk 2>&1 | tail -5
echo "   Frontend built."

echo ""
echo "=== Done! Hard-refresh your browser ==="
