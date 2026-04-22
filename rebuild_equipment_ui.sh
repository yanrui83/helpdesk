#!/bin/bash
BENCH=/home/frappe/frappe-bench
APP=$BENCH/apps/helpdesk

echo "Copying updated EquipmentList.vue..."
cp /workspace/EquipmentList.vue "$APP/desk/src/pages/equipment/EquipmentList.vue"

echo "Rebuilding frontend..."
cd "$BENCH"
bench build --app helpdesk 2>&1 | tail -10
bench --site helpdesk.localhost clear-cache

echo "Done! Refresh the Equipment page."
