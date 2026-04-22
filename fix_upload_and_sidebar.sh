#!/bin/bash
set -e
BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
DESK="$APP/desk/src"
EQ_DIR="$APP/helpdesk/helpdesk/doctype/hd_equipment"
API="$APP/helpdesk/api"

echo "=== Fix: Sidebar optimistic + Upload field ==="

# 1. Fix sidebar (optimistic hasEquipment)
echo "1. Fixing sidebar optimistic rendering..."
sed -i 's/\r$//' /workspace/fix_sidebar_optimistic.py
python3 /workspace/fix_sidebar_optimistic.py

# 2. Deploy updated hd_equipment.json (is_private:0 + description)
echo "2. Deploying updated hd_equipment.json..."
cp /workspace/hd_equipment.json "$EQ_DIR/hd_equipment.json"

# 3. Deploy updated hd_equipment.py (auto-public file hook)
echo "3. Deploying hd_equipment.py controller..."
cp /workspace/hd_equipment.py "$EQ_DIR/hd_equipment.py"

# 4. Increase max file upload size (for large GLB files)
echo "4. Setting max file upload size to 1GB..."
cd "$BENCH"
bench --site helpdesk.localhost set-config max_file_size 1073741824

# 5. Run migration to update doctype field
echo "5. Running migration..."
bench --site helpdesk.localhost migrate --skip-failing 2>&1 | tail -5

# 6. Rebuild frontend
echo "6. Building frontend..."
bench build --app helpdesk 2>&1 | tail -5

# 7. Clear cache
echo "7. Clearing cache..."
bench --site helpdesk.localhost clear-cache

echo ""
echo "=== Done! Hard-refresh browser (Ctrl+Shift+R) ==="
echo "Spare Part tab: now shows immediately for portal users"
echo "Upload: Clear existing file, then drag-drop or click to upload new GLB"
