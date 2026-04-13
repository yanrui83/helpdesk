#!/bin/bash
set -e

BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
DESK="$APP/desk/src"
SETTINGS_DIR="$APP/helpdesk/helpdesk/doctype/hd_settings"

echo "=== Step 1: Patch HD Settings doctype JSON ==="
python3 << 'PYEOF'
import json, sys

path = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/helpdesk/doctype/hd_settings/hd_settings.json"
with open(path) as f:
    doc = json.load(f)

# Check if already added
existing = [f for f in doc["fields"] if f.get("fieldname") == "ai_assistant_api_key"]
if existing:
    print("ai_assistant_api_key field already exists, skipping doctype patch")
    sys.exit(0)

# Add new fields: a Tab Break for "Integrations", a Section Break for "AI Assistant", and the Password field
new_fields = [
    {
        "fieldname": "integrations_tab",
        "fieldtype": "Tab Break",
        "label": "Integrations"
    },
    {
        "fieldname": "ai_assistant_section",
        "fieldtype": "Section Break",
        "label": "AI Assistant"
    },
    {
        "fieldname": "ai_assistant_api_key",
        "fieldtype": "Password",
        "label": "AI Assistant API Key",
        "description": "API key used by the AI assistant integration. This value is stored encrypted."
    }
]

# Add fields to the fields array
doc["fields"].extend(new_fields)

# Add to field_order (before trash_retention_days for logical ordering)
fo = doc["field_order"]
# Insert before the last item (trash_retention_days) or at the end
if "trash_retention_days" in fo:
    idx = fo.index("trash_retention_days")
    for i, nf in enumerate(new_fields):
        fo.insert(idx + i, nf["fieldname"])
else:
    for nf in new_fields:
        fo.append(nf["fieldname"])

with open(path, "w") as f:
    json.dump(doc, f, indent=1, ensure_ascii=False)

print("Doctype JSON patched successfully")
PYEOF

echo "=== Step 2: Patch General.vue ==="
GENERAL_VUE="$DESK/components/Settings/General/General.vue"

# Add aiAssistantApiKey to the settingsData ref (initial state)
python3 << 'PYEOF'
path = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/components/Settings/General/General.vue"
with open(path) as f:
    content = f.read()

if "aiAssistantApiKey" in content:
    print("General.vue already patched, skipping")
else:
    import re

    # 1. Add field to settingsData ref initial object
    content = content.replace(
        'outsideWorkingHoursBannerMessage: "",\n});',
        'outsideWorkingHoursBannerMessage: "",\n  aiAssistantApiKey: "",\n});'
    )

    # 2. Add to saveSettingsResource fieldname mapping
    content = content.replace(
        """outside_working_hours_message:
          settingsData.value.outsideWorkingHoursBannerMessage,""",
        """outside_working_hours_message:
          settingsData.value.outsideWorkingHoursBannerMessage,
        ai_assistant_api_key: settingsData.value.aiAssistantApiKey,"""
    )

    # 3. Add to transformData function
    content = content.replace(
        'outsideWorkingHoursBannerMessage: data.outside_working_hours_message || "",\n  };',
        'outsideWorkingHoursBannerMessage: data.outside_working_hours_message || "",\n    aiAssistantApiKey: data.ai_assistant_api_key || "",\n  };'
    )

    # 4. Add the AI Assistant Settings section in the template (before the User signup section)
    # We add it between WorkflowKnowledgebaseSettings and User signup
    ai_section = """<hr class="my-8" />
        <div>
          <div class="text-base font-semibold text-gray-900">
            {{ __("AI Assistant") }}
          </div>
          <div class="mt-4">
            <div class="flex flex-col gap-1 mb-2">
              <span class="text-base font-medium text-ink-gray-8">{{
                __("API Key")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __(
                  "Enter your AI assistant API key. This value is stored encrypted on the server."
                )
              }}</span>
            </div>
            <div class="flex items-center gap-2 max-w-md">
              <FormControl
                :type="showApiKey ? 'text' : 'password'"
                v-model="settingsData.aiAssistantApiKey"
                :placeholder="__('Enter API key')"
                class="flex-1"
              />
              <Button
                :icon="showApiKey ? EyeOffIcon : EyeIcon"
                variant="ghost"
                @click="showApiKey = !showApiKey"
              />
            </div>
          </div>
        </div>"""

    # Insert before the User signup <hr>+<div> block
    content = content.replace(
        """<hr class="my-8" />
        <div>
          <div class="text-base font-semibold text-gray-900">
            {{ __("User signup") }}""",
        ai_section + """
        <hr class="my-8" />
        <div>
          <div class="text-base font-semibold text-gray-900">
            {{ __("User signup") }}"""
    )

    # 5. Add imports for FormControl, Eye icons, and the showApiKey ref
    # Add FormControl to the frappe-ui import
    if "FormControl" not in content:
        content = content.replace(
            "from \"frappe-ui\";",
            'FormControl,\n} from "frappe-ui";'
        )
        # Make sure we don't double the closing brace - fix the import line
        content = content.replace(
            "} from \"frappe-ui\";\nFormControl,\n} from \"frappe-ui\";",
            "FormControl,\n} from \"frappe-ui\";"
        )

    # Add eye icon imports and showApiKey ref
    # Add after the existing icon/component imports
    content = content.replace(
        'import { HDSettings, HDSettingsSymbol } from "@/types";',
        '''import { HDSettings, HDSettingsSymbol } from "@/types";
import EyeIcon from "~icons/lucide/eye";
import EyeOffIcon from "~icons/lucide/eye-off";'''
    )

    # Add showApiKey ref
    content = content.replace(
        'const isDirty = ref(false);',
        'const isDirty = ref(false);\nconst showApiKey = ref(false);'
    )

    with open(path, "w") as f:
        f.write(content)
    print("General.vue patched successfully")
PYEOF

echo "=== Step 3: Patch types.ts ==="
python3 << 'PYEOF'
path = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/types.ts"
with open(path) as f:
    content = f.read()

if "aiAssistantApiKey" in content:
    print("types.ts already patched, skipping")
else:
    content = content.replace(
        "outsideWorkingHoursBannerMessage: string;\n}",
        "outsideWorkingHoursBannerMessage: string;\n  aiAssistantApiKey: string;\n}"
    )
    with open(path, "w") as f:
        f.write(content)
    print("types.ts patched successfully")
PYEOF

echo "=== Step 4: Migrate and rebuild ==="
cd "$BENCH"
bench --site helpdesk.localhost migrate 2>&1 | tail -5
echo "Migration done."

cd "$DESK/.."
yarn build 2>&1 | tail -5
echo "Frontend build done."

echo "=== All patches applied successfully ==="
