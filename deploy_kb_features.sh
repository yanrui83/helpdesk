#!/bin/bash
# deploy_kb_features.sh — Patches HD Article, HD Article Category, creates HD Category Access doctype,
# adds custom fields, deploys Vue components, and patches the agent KB page and router.
set -e

BENCH="/home/frappe/frappe-bench"
APP="$BENCH/apps/helpdesk"
SITE="helpdesk.localhost"

echo "=== Deploying KB Features ==="

# ─── 1. Copy backend API ───
echo "[1/8] Installing kb_custom.py API..."
cp /workspace/kb_custom.py "$APP/helpdesk/api/kb_custom.py"

# ─── 2. Add 'Trash' status + 'trashed_on' field to HD Article ───
echo "[2/8] Patching HD Article schema..."
cd "$BENCH"
./env/bin/python -c "
import os
os.chdir('$BENCH/sites')
import frappe
frappe.init(site='$SITE')
frappe.connect()

# Add 'Trash' to status options
meta = frappe.get_doc('DocType', 'HD Article')
for f in meta.fields:
    if f.fieldname == 'status':
        if 'Trash' not in (f.options or ''):
            f.options = (f.options or '') + '\nTrash'
            print('  Added Trash status option')

# Add trashed_on field if not exists
has_trashed = any(f.fieldname == 'trashed_on' for f in meta.fields)
if not has_trashed:
    meta.append('fields', {
        'fieldname': 'trashed_on',
        'fieldtype': 'Datetime',
        'label': 'Trashed On',
        'read_only': 1,
        'hidden': 1,
    })
    print('  Added trashed_on field')

meta.flags.ignore_links = True
meta.save(ignore_permissions=True)
frappe.db.commit()
print('  HD Article schema updated')
frappe.destroy()
"

# ─── 3. Add parent_category field to HD Article Category ───
echo "[3/8] Patching HD Article Category schema..."
./env/bin/python -c "
import os
os.chdir('$BENCH/sites')
import frappe
frappe.init(site='$SITE')
frappe.connect()

meta = frappe.get_doc('DocType', 'HD Article Category')
has_parent_cat = any(f.fieldname == 'parent_category' for f in meta.fields)
if not has_parent_cat:
    meta.append('fields', {
        'fieldname': 'parent_category',
        'fieldtype': 'Link',
        'label': 'Parent Category',
        'options': 'HD Article Category',
    })
    print('  Added parent_category field')

meta.flags.ignore_links = True
meta.save(ignore_permissions=True)
frappe.db.commit()
print('  HD Article Category schema updated')
frappe.destroy()
"

# ─── 4. Create HD Category Access doctype ───
echo "[4/8] Creating HD Category Access doctype..."
./env/bin/python -c "
import os
os.chdir('$BENCH/sites')
import frappe
frappe.init(site='$SITE')
frappe.connect()

if not frappe.db.exists('DocType', 'HD Category Access'):
    dt = frappe.new_doc('DocType')
    dt.name = 'HD Category Access'
    dt.module = 'Helpdesk'
    dt.custom = 1
    dt.autoname = 'hash'
    dt.engine = 'InnoDB'
    dt.append('fields', {
        'fieldname': 'category',
        'fieldtype': 'Link',
        'label': 'Category',
        'options': 'HD Article Category',
        'reqd': 1,
        'in_list_view': 1,
    })
    dt.append('fields', {
        'fieldname': 'user',
        'fieldtype': 'Link',
        'label': 'User',
        'options': 'User',
        'reqd': 1,
        'in_list_view': 1,
    })
    dt.append('fields', {
        'fieldname': 'user_name',
        'fieldtype': 'Data',
        'label': 'User Name',
        'read_only': 1,
        'in_list_view': 1,
    })
    dt.append('permissions', {
        'role': 'System Manager',
        'read': 1, 'write': 1, 'create': 1, 'delete': 1,
    })
    dt.append('permissions', {
        'role': 'Agent',
        'read': 1, 'write': 1, 'create': 1, 'delete': 1,
    })
    dt.flags.ignore_links = True
    dt.insert(ignore_permissions=True)
    frappe.db.commit()
    print('  HD Category Access doctype created')
else:
    print('  HD Category Access doctype already exists')

frappe.destroy()
"

# ─── 5. Add trash_retention_days to HD Settings ───
echo "[5/8] Adding trash_retention_days to HD Settings..."
./env/bin/python -c "
import os
os.chdir('$BENCH/sites')
import frappe
frappe.init(site='$SITE')
frappe.connect()

meta = frappe.get_doc('DocType', 'HD Settings')
has_retention = any(f.fieldname == 'trash_retention_days' for f in meta.fields)
if not has_retention:
    meta.append('fields', {
        'fieldname': 'trash_retention_days',
        'fieldtype': 'Int',
        'label': 'Trash Retention Days',
        'default': '30',
        'description': 'Number of days before trashed articles are permanently deleted',
    })
    meta.flags.ignore_links = True
    meta.save(ignore_permissions=True)
    frappe.db.commit()
    print('  Added trash_retention_days field')
else:
    print('  trash_retention_days already exists')
frappe.destroy()
"

# ─── 6. Copy Vue components ───
echo "[6/8] Copying Vue components..."
cp /workspace/KBTrash.vue "$APP/desk/src/pages/knowledge-base/KBTrash.vue"
cp /workspace/CategoryAccessModal.vue "$APP/desk/src/components/knowledge-base/CategoryAccessModal.vue"
cp /workspace/SubCategoryModal.vue "$APP/desk/src/components/knowledge-base/SubCategoryModal.vue"

# ─── 7. Patch router to add Trash route ───
echo "[7/8] Patching router..."
ROUTER_FILE="$APP/desk/src/router.ts"
if ! grep -q "KBTrash" "$ROUTER_FILE"; then
    # Find the KnowledgeBase route block and add Trash route after it
    # We'll add it as a new agent route
    sed -i '/name: "KnowledgeBase"/,/component:/s|component:.*|&\n      },\n      {\n        path: "kb/trash",\n        name: "KBTrash",\n        component: () => import("@/pages/knowledge-base/KBTrash.vue"),|' "$ROUTER_FILE" 2>/dev/null || true

    # If sed didn't work cleanly, try a Python-based patch
    python3 -c "
import re

with open('$ROUTER_FILE', 'r') as f:
    content = f.read()

if 'KBTrash' not in content:
    # Find the agent children array and add the trash route
    trash_route = '''      {
        path: \"kb/trash\",
        name: \"KBTrash\",
        component: () => import(\"@/pages/knowledge-base/KBTrash.vue\"),
      },'''

    # Insert after the last KB-related route
    # Look for the Articles route  and insert after it
    pattern = r'(name:\s*\"Article\".*?},)'
    match = re.search(pattern, content, re.DOTALL)
    if match:
        insert_pos = match.end()
        content = content[:insert_pos] + '\n' + trash_route + content[insert_pos:]
        with open('$ROUTER_FILE', 'w') as f:
            f.write(content)
        print('  Router patched with KBTrash route')
    else:
        print('  WARNING: Could not find insertion point for KBTrash route')
else:
    print('  KBTrash route already exists')
" 2>/dev/null || echo "  Router patch via Python also failed, will try alternate method"
fi

# ─── 8. Patch KnowledgeBaseAgent.vue to add Trash, SubCategory, and Access Control buttons ───
echo "[8/8] Patching KnowledgeBaseAgent.vue..."
KB_AGENT="$APP/desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue"

# Check if already patched
if ! grep -q "SubCategoryModal" "$KB_AGENT"; then
    python3 -c "
import re

with open('$KB_AGENT', 'r') as f:
    content = f.read()

# 1. Add imports for new components
import_additions = '''import SubCategoryModal from \"@/components/knowledge-base/SubCategoryModal.vue\";
import CategoryAccessModal from \"@/components/knowledge-base/CategoryAccessModal.vue\";
import LucideTrash2 from \"~icons/lucide/trash-2\";
import LucideShield from \"~icons/lucide/shield\";
import LucideFolderPlus from \"~icons/lucide/folder-plus\";'''

# Insert after the last existing import
last_import = content.rfind('import ')
next_newline = content.index('\n', last_import)
content = content[:next_newline+1] + import_additions + '\n' + content[next_newline+1:]

# 2. Add component state variables
state_additions = '''
const showSubCategoryModal = ref(false);
const showAccessModal = ref(false);
'''
# Insert after const mergeModal
content = content.replace(
    'const mergeModal = ref(false);',
    'const mergeModal = ref(false);' + state_additions
)

# 3. Add new header options (Sub-Category, Access Control, Trash)
# Find the headerOptions array and add entries
new_options = '''  {
    label: __(\"Sub-Category\"),
    icon: \"folder-plus\",
    onClick: () => {
      showSubCategoryModal.value = true;
    },
  },
  {
    label: __(\"Access Control\"),
    icon: \"shield\",
    onClick: () => {
      showAccessModal.value = true;
    },
  },
  {
    label: __(\"Trash\"),
    icon: \"trash-2\",
    onClick: () => {
      router.push({ name: \"KBTrash\" });
    },
  },'''

# Insert before the closing ] of headerOptions
content = content.replace(
    '''    label: __(\"Article\"),''',
    new_options + '''
  {
    label: __(\"Article\"),'''
)

# 4. Add modal components to template
# Add before </div> (the closing of the root template div)
modal_template = '''    <SubCategoryModal v-model=\"showSubCategoryModal\" @created=\"() => listViewRef?.reload()\" />
    <CategoryAccessModal v-model=\"showAccessModal\" />'''

# Insert before the final </div></template>
content = content.replace(
    '  </div>\n</template>',
    modal_template + '\n  </div>\n</template>'
)

with open('$KB_AGENT', 'w') as f:
    f.write(content)
print('  KnowledgeBaseAgent.vue patched')
"
else
    echo "  KnowledgeBaseAgent.vue already patched"
fi

echo ""
echo "=== KB Features deployed. Run 'bench build --app helpdesk' to rebuild frontend. ==="
