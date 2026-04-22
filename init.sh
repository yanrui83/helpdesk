#!/bin/bash

deploy_custom_files() {
    cp /workspace/customer.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/customer.py
    cp /workspace/admin_notifications.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/admin_notifications.py

    # Patch the SPA router to fix login redirect for customers
    cp /workspace/router_index.ts /home/frappe/frappe-bench/apps/helpdesk/desk/src/router/index.ts

    # Deploy login redirect failsafe JS (with version stamp)
    cp /workspace/login_redirect.js /home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/js/login_redirect.js
    APP_VERSION=$(cat /workspace/VERSION 2>/dev/null | tr -d '[:space:]' || echo "unknown")
    sed -i "s/__APP_VERSION__/$APP_VERSION/g" \
        /home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/js/login_redirect.js

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

    # Add realtime admin email hooks for new tickets and agent replies
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
        echo "Admin realtime notification hooks added."
    fi

    # Deploy updated layoutSettings (Equipment in agent sidebar, Spare Part in portal sidebar)
    cp /workspace/layoutSettings.ts /home/frappe/frappe-bench/apps/helpdesk/desk/src/components/layouts/layoutSettings.ts

    # Patch Sidebar.vue for conditional Spare Part tab
    sed -i 's/\r$//' /workspace/patch_sidebar.py
    python3 /workspace/patch_sidebar.py

    # Fix sidebar to use optimistic hasEquipment (show tab immediately, only hide if API says false)
    sed -i 's/\r$//' /workspace/fix_sidebar_optimistic.py
    python3 /workspace/fix_sidebar_optimistic.py

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

# ─── Site settings ───
configure_site_settings() {
    echo "Configuring site settings..."
    cd /home/frappe/frappe-bench
    # Enable username login in site_config (belt-and-suspenders)
    bench --site helpdesk.localhost set-config allow_login_using_user_name 1
    # Enable username login in System Settings (the source Frappe auth actually reads)
    cp /workspace/enable_username_login.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/enable_username_login.py
    bench --site helpdesk.localhost execute helpdesk.api.enable_username_login.run
    echo "  allow_login_using_user_name enabled in System Settings"
    # Auto-assign username (part before @) to any portal user that has none
    cp /workspace/set_portal_usernames.py /home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/set_portal_usernames.py 2>/dev/null || true
    bench --site helpdesk.localhost execute helpdesk.api.set_portal_usernames.run
}

if [ -d "/home/frappe/frappe-bench/apps/frappe" ]; then
    echo "Bench already exists, skipping init"
    cd frappe-bench
    configure_site_settings
    deploy_custom_files

    # Deploy AI Assistant API key setting (doctype + UI patches)
    sed -i 's/\r$//' /workspace/deploy_api_key_setting.sh
    bash /workspace/deploy_api_key_setting.sh

    # Deploy Customer Tags doctype + mandatory ticket fields
    sed -i 's/\r$//' /workspace/deploy_customer_tags.sh
    bash /workspace/deploy_customer_tags.sh

    # Deploy Equipment 3D Viewer
    sed -i 's/\r$//' /workspace/deploy_equipment.sh
    bash /workspace/deploy_equipment.sh

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

# Deploy AI Assistant API key setting (doctype + UI patches)
sed -i 's/\r$//' /workspace/deploy_api_key_setting.sh
bash /workspace/deploy_api_key_setting.sh

# Deploy Customer Tags doctype + mandatory ticket fields
sed -i 's/\r$//' /workspace/deploy_customer_tags.sh
bash /workspace/deploy_customer_tags.sh

# Deploy Equipment 3D Viewer
sed -i 's/\r$//' /workspace/deploy_equipment.sh
bash /workspace/deploy_equipment.sh

deploy_kb_features
configure_site_settings

bench start
