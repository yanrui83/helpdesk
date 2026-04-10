#!/bin/bash
set -e

APP_API_DIR="/home/frappe/frappe-bench/apps/helpdesk/helpdesk/api"
HOOKS_FILE="/home/frappe/frappe-bench/apps/helpdesk/helpdesk/hooks.py"

cp /workspace/admin_notifications.py "$APP_API_DIR/admin_notifications.py"

if ! grep -q "notify_admin_new_ticket" "$HOOKS_FILE"; then
cat >> "$HOOKS_FILE" <<'EOF'

try:
    doc_events
except NameError:
    doc_events = {}

doc_events.setdefault("HD Ticket", {}).update({
    "after_insert": "helpdesk.api.admin_notifications.notify_admin_new_ticket",
})

doc_events.setdefault("Communication", {}).update({
    "after_insert": "helpdesk.api.admin_notifications.notify_admin_agent_reply",
})
EOF
fi

cd /home/frappe/frappe-bench
bench --site helpdesk.localhost clear-cache
bench --site helpdesk.localhost migrate

echo "Realtime admin notification hooks deployed."
