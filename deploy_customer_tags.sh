#!/bin/bash
set -e

BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
TAG_DIR="$APP/helpdesk/helpdesk/doctype/hd_customer_tag"

echo "=== Deploying Customer Tags feature ==="

# Step 1: Create HD Customer Tag doctype directory and files
if [ ! -d "$TAG_DIR" ]; then
    mkdir -p "$TAG_DIR"
    echo "Created HD Customer Tag doctype directory"
fi

cp /workspace/hd_customer_tag.json "$TAG_DIR/hd_customer_tag.json"
cp /workspace/hd_customer_tag.py "$TAG_DIR/hd_customer_tag.py"
touch "$TAG_DIR/__init__.py"
echo "Doctype files copied"

# Step 2: Patch HD Ticket to add customer_tag field
python3 /workspace/patch_hd_ticket_customer_tag.py

# Step 2b: Patch HD Ticket to add plant_modification fields
python3 /workspace/patch_hd_ticket_plant_mod.py

# Step 3: Migrate to register new doctype and field
cd "$BENCH"
bench --site helpdesk.localhost migrate 2>&1 | tail -5
echo "Migration done"

# Step 4: Setup ticket types, template fields, and workspace link
cp /workspace/setup_ticket_fields.py "$APP/helpdesk/api/setup_ticket_fields.py"
bench --site helpdesk.localhost execute helpdesk.api.setup_ticket_fields.run

# Step 4b: Patch template API to filter tags by logged-in user's customer
cp /workspace/hd_ticket_template_api.py "$APP/helpdesk/helpdesk/doctype/hd_ticket_template/api.py"
echo "Template API patched (customer tag filter)"

# Step 5: Copy custom TicketNew.vue and rebuild frontend
cp /workspace/TicketNew.vue "$APP/desk/src/pages/ticket/TicketNew.vue"
echo "TicketNew.vue copied"
cd "$BENCH"
bench build --app helpdesk 2>&1 | tail -5
echo "Frontend rebuilt"

echo "=== Customer Tags feature deployed ==="
