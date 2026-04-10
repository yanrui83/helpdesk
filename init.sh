#!/bin/bash

deploy_custom_files() {
    cp /workspace/customer.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/customer.py

    # Patch the SPA router to fix login redirect for customers
    cp /workspace/router_index.ts /home/frappe/frappe-bench/apps/helpdesk/desk/src/router/index.ts

    # Deploy login redirect failsafe JS
    cp /workspace/login_redirect.js /home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/js/login_redirect.js

    # Deploy AI chat backend API
    cp /workspace/ai_chat.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/ai_chat.py

    # Deploy AI chat Vue component
    cp /workspace/AiChatPanel.vue /home/frappe/frappe-bench/apps/helpdesk/desk/src/components/AiChatPanel.vue

    # Patch App.vue to include AiChatPanel if not already patched
    APP_VUE="/home/frappe/frappe-bench/apps/helpdesk/desk/src/App.vue"
    if ! grep -q "AiChatPanel" "$APP_VUE"; then
        # Add import
        sed -i '/import { Dialogs } from/a import AiChatPanel from "@/components/AiChatPanel.vue";' "$APP_VUE"
        # Add component to template after <Dialogs />
        sed -i 's|<Dialogs />|<Dialogs />\n  <AiChatPanel />|' "$APP_VUE"
        echo "App.vue patched with AiChatPanel."
    fi

    # Install google-genai Python package for AI chat
    cd /home/frappe/frappe-bench
    ./env/bin/pip install google-genai 2>/dev/null || true

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

    # Rebuild helpdesk frontend with patched router + AI chat
    cd /home/frappe/frappe-bench && bench build --app helpdesk

    echo "Custom files deployed and frontend rebuilt."
}

# ─── KB Features deployment ───
deploy_kb_features() {
    echo "Deploying KB features..."
    cd /home/frappe/frappe-bench

    # Copy KB custom API
    cp /workspace/kb_custom.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/kb_custom.py

    # Copy Vue components
    cp /workspace/KBTrash.vue /home/frappe/frappe-bench/apps/helpdesk/desk/src/pages/knowledge-base/KBTrash.vue
    cp /workspace/CategoryAccessModal.vue /home/frappe/frappe-bench/apps/helpdesk/desk/src/components/knowledge-base/CategoryAccessModal.vue
    cp /workspace/SubCategoryModal.vue /home/frappe/frappe-bench/apps/helpdesk/desk/src/components/knowledge-base/SubCategoryModal.vue

    # Run schema patches
    sed -i 's/\r$//' /workspace/deploy_kb_features.sh
    bash /workspace/deploy_kb_features.sh

    # Patch router for KBTrash route
    python3 /workspace/patch_router_trash.py

    # Patch delete to use trash
    python3 /workspace/patch_delete_to_trash.py

    # Fix any syntax issues
    python3 /workspace/fix_syntax.py 2>/dev/null || true

    # Patch customer portal for access control
    python3 /workspace/patch_category_container.py

    # Rebuild frontend
    cd /home/frappe/frappe-bench && bench build --app helpdesk
    bench --site helpdesk.localhost clear-cache

    echo "KB features deployed."
}

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    deploy_custom_files
    deploy_kb_features
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
deploy_kb_features

bench start
