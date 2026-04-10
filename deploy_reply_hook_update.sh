#!/bin/bash
set -e
cp /workspace/admin_notifications.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/admin_notifications.py
cd /home/frappe/frappe-bench
bench --site helpdesk.localhost clear-cache
echo "Reply hook update deployed."