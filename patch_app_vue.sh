#!/bin/bash
# Patch App.vue to include AiChatPanel
APP_VUE="/home/frappe/frappe-bench/apps/helpdesk/desk/src/App.vue"

if ! grep -q "AiChatPanel" "$APP_VUE"; then
    # Add import line after the Dialogs import
    sed -i '/import { Dialogs } from/a import AiChatPanel from "@/components/AiChatPanel.vue";' "$APP_VUE"
    # Add component to template after <Dialogs />
    sed -i 's|<Dialogs />|<Dialogs />\n  <AiChatPanel />|' "$APP_VUE"
    echo "App.vue patched with AiChatPanel."
else
    echo "App.vue already patched."
fi

cat "$APP_VUE"
