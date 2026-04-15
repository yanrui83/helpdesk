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
existing_key = [f for f in doc["fields"] if f.get("fieldname") == "ai_assistant_api_key"]
existing_model = [f for f in doc["fields"] if f.get("fieldname") == "ai_assistant_model"]

if existing_key and existing_model:
    print("AI fields already exist, skipping doctype patch")
    sys.exit(0)

new_fields = []

if not existing_key:
    # Add Tab Break + Section Break + API Key + Model fields (fresh install)
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
        },
        {
            "fieldname": "ai_assistant_model",
            "fieldtype": "Data",
            "label": "AI Model",
            "default": "gemini-2.5-flash",
            "description": "Gemini model name (e.g. gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash). Leave blank for default."
        }
    ]
elif not existing_model:
    # API key exists but model field is missing — add just the model field
    new_fields = [
        {
            "fieldname": "ai_assistant_model",
            "fieldtype": "Data",
            "label": "AI Model",
            "default": "gemini-2.5-flash",
            "description": "Gemini model name (e.g. gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash). Leave blank for default."
        }
    ]

if new_fields:
    doc["fields"].extend(new_fields)

    fo = doc["field_order"]
    for nf in new_fields:
        fn = nf["fieldname"]
        if fn not in fo:
            if "trash_retention_days" in fo:
                idx = fo.index("trash_retention_days")
                fo.insert(idx, fn)
            else:
                fo.append(fn)

    with open(path, "w") as f:
        json.dump(doc, f, indent=1, ensure_ascii=False)
    print("Doctype JSON patched successfully")
else:
    print("No new fields to add")
PYEOF

echo "=== Step 2: Patch General.vue ==="
GENERAL_VUE="$DESK/components/Settings/General/General.vue"

python3 << 'PYEOF'
path = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/components/Settings/General/General.vue"
with open(path) as f:
    content = f.read()

changed = False

# --- API Key field (existing logic) ---
if "aiAssistantApiKey" not in content:
    import re

    content = content.replace(
        'outsideWorkingHoursBannerMessage: "",\n});',
        'outsideWorkingHoursBannerMessage: "",\n  aiAssistantApiKey: "",\n  aiAssistantModel: "",\n});'
    )

    content = content.replace(
        """outside_working_hours_message:
          settingsData.value.outsideWorkingHoursBannerMessage,""",
        """outside_working_hours_message:
          settingsData.value.outsideWorkingHoursBannerMessage,
        ai_assistant_api_key: settingsData.value.aiAssistantApiKey,
        ai_assistant_model: settingsData.value.aiAssistantModel,"""
    )

    content = content.replace(
        'outsideWorkingHoursBannerMessage: data.outside_working_hours_message || "",\n  };',
        'outsideWorkingHoursBannerMessage: data.outside_working_hours_message || "",\n    aiAssistantApiKey: data.ai_assistant_api_key || "",\n    aiAssistantModel: data.ai_assistant_model || "",\n  };'
    )

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
          <div class="mt-4">
            <div class="flex flex-col gap-1 mb-2">
              <span class="text-base font-medium text-ink-gray-8">{{
                __("AI Model")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __(
                  "Gemini model name (e.g. gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash). Leave blank for default."
                )
              }}</span>
            </div>
            <div class="max-w-md">
              <FormControl
                type="text"
                v-model="settingsData.aiAssistantModel"
                :placeholder="__('gemini-2.5-flash')"
              />
            </div>
          </div>
        </div>"""

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

    if "FormControl" not in content:
        content = content.replace(
            "from \"frappe-ui\";",
            'FormControl,\n} from "frappe-ui";'
        )
        content = content.replace(
            "} from \"frappe-ui\";\nFormControl,\n} from \"frappe-ui\";",
            "FormControl,\n} from \"frappe-ui\";"
        )

    content = content.replace(
        'import { HDSettings, HDSettingsSymbol } from "@/types";',
        '''import { HDSettings, HDSettingsSymbol } from "@/types";
import EyeIcon from "~icons/lucide/eye";
import EyeOffIcon from "~icons/lucide/eye-off";'''
    )

    content = content.replace(
        'const isDirty = ref(false);',
        'const isDirty = ref(false);\nconst showApiKey = ref(false);'
    )

    changed = True

# --- Model field only (API key already existed, add model to existing patched file) ---
elif "aiAssistantModel" not in content:
    # Add to settingsData initial state
    content = content.replace(
        'aiAssistantApiKey: "",\n});',
        'aiAssistantApiKey: "",\n  aiAssistantModel: "",\n});'
    )

    # Add to save mapping
    content = content.replace(
        'ai_assistant_api_key: settingsData.value.aiAssistantApiKey,',
        'ai_assistant_api_key: settingsData.value.aiAssistantApiKey,\n        ai_assistant_model: settingsData.value.aiAssistantModel,'
    )

    # Add to transform
    content = content.replace(
        'aiAssistantApiKey: data.ai_assistant_api_key || "",\n  };',
        'aiAssistantApiKey: data.ai_assistant_api_key || "",\n    aiAssistantModel: data.ai_assistant_model || "",\n  };'
    )

    # Add model input below the API key div
    model_html = """
          <div class="mt-4">
            <div class="flex flex-col gap-1 mb-2">
              <span class="text-base font-medium text-ink-gray-8">{{
                __("AI Model")
              }}</span>
              <span class="text-p-sm text-ink-gray-6">{{
                __(
                  "Gemini model name (e.g. gemini-2.5-flash, gemini-2.5-pro, gemini-2.0-flash). Leave blank for default."
                )
              }}</span>
            </div>
            <div class="max-w-md">
              <FormControl
                type="text"
                v-model="settingsData.aiAssistantModel"
                :placeholder="__('gemini-2.5-flash')"
              />
            </div>
          </div>"""

    # Insert after the API key toggle button div
    content = content.replace(
        '''variant="ghost"
                @click="showApiKey = !showApiKey"
              />
            </div>
          </div>
        </div>''',
        '''variant="ghost"
                @click="showApiKey = !showApiKey"
              />
            </div>
          </div>''' + model_html + '''
        </div>'''
    )
    changed = True

if changed:
    with open(path, "w") as f:
        f.write(content)
    print("General.vue patched successfully")
else:
    print("General.vue already has all AI fields, skipping")
PYEOF

echo "=== Step 3: Patch types.ts ==="
python3 << 'PYEOF'
path = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/types.ts"
with open(path) as f:
    content = f.read()

changed = False

if "aiAssistantApiKey" not in content:
    content = content.replace(
        "outsideWorkingHoursBannerMessage: string;\n}",
        "outsideWorkingHoursBannerMessage: string;\n  aiAssistantApiKey: string;\n  aiAssistantModel: string;\n}"
    )
    changed = True
elif "aiAssistantModel" not in content:
    content = content.replace(
        "aiAssistantApiKey: string;\n}",
        "aiAssistantApiKey: string;\n  aiAssistantModel: string;\n}"
    )
    changed = True

if changed:
    with open(path, "w") as f:
        f.write(content)
    print("types.ts patched successfully")
else:
    print("types.ts already has all AI fields, skipping")
PYEOF

echo "=== Step 4: Copy AI backend and frontend files ==="
cp /workspace/ai_chat.py "$APP/helpdesk/api/ai_chat.py"
echo "ai_chat.py copied"

cp /workspace/AiChatPanel.vue "$APP/desk/src/components/AiChatPanel.vue"
echo "AiChatPanel.vue copied"

echo "=== Step 5: Migrate and rebuild ==="
cd "$BENCH"
bench --site helpdesk.localhost migrate 2>&1 | tail -5
echo "Migration done."

bench build --app helpdesk 2>&1 | tail -5
echo "Frontend build done."

echo "=== All AI patches applied successfully ==="
