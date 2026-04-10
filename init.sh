#!/bin/bash

deploy_custom_files() {
    cp /workspace/customer.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/customer.py

    # Patch the SPA router to fix login redirect for customers
    cp /workspace/router_index.ts /home/frappe/frappe-bench/apps/helpdesk/desk/src/router/index.ts

    # Deploy login redirect failsafe JS
    cp /workspace/login_redirect.js /home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/js/login_redirect.js

    # Add role_home_page to hooks if not already present
    HOOKS_FILE="/home/frappe/frappe-bench/apps/helpdesk/helpdesk/hooks.py"
    if ! grep -q "role_home_page" "$HOOKS_FILE"; then
        sed -i '/^website_route_rules = \[/,/^\]/!b;/^\]/a\
\
role_home_page = {\
    "Customer": "/helpdesk",\
}' "$HOOKS_FILE"
        echo "role_home_page hook added."
    fi

    # Add web_include_js for login redirect failsafe if not already present
    if ! grep -q "web_include_js" "$HOOKS_FILE"; then
        echo '' >> "$HOOKS_FILE"
        echo 'web_include_js = ["/assets/helpdesk/js/login_redirect.js"]' >> "$HOOKS_FILE"
        echo "web_include_js hook added."
    fi

    # Rebuild helpdesk frontend with patched router
    cd /home/frappe/frappe-bench && bench build --app helpdesk

    echo "Custom files deployed and frontend rebuilt."
}

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    deploy_custom_files
    bench start
else
    echo "Creating new bench..."
fi

bench init --skip-redis-config-generation frappe-bench --version version-15

cd frappe-bench

# Use containers instead of localhost
bench set-mariadb-host mariadb
bench set-redis-cache-host redis://redis:6379
bench set-redis-queue-host redis://redis:6379
bench set-redis-socketio-host redis://redis:6379

# Remove redis, watch from Procfile
sed -i '/redis/d' ./Procfile
sed -i '/watch/d' ./Procfile

bench get-app telephony
bench get-app helpdesk --branch main

bench new-site helpdesk.localhost \
--force \
--mariadb-root-password 123 \
--admin-password admin \
--no-mariadb-socket

bench --site helpdesk.localhost install-app telephony
bench --site helpdesk.localhost install-app helpdesk
bench --site helpdesk.localhost set-config developer_mode 1
bench --site helpdesk.localhost set-config mute_emails 1
bench --site helpdesk.localhost set-config server_script_enabled 1
bench --site helpdesk.localhost clear-cache
bench use helpdesk.localhost

# Set website home page to helpdesk portal
bench --site helpdesk.localhost execute frappe.db.set_single_value --args '["Website Settings", "home_page", "helpdesk"]'
bench --site helpdesk.localhost execute frappe.db.commit

deploy_custom_files

bench start
