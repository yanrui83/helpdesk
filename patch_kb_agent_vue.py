#!/usr/bin/env python3
"""
Patch KnowledgeBaseAgent.vue:
1. Add defaultFilters to exclude Trash articles from main list
2. Replace deleteCategory with delete_category_safe API
3. Add Trash to status map
"""

FILE = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue"

with open(FILE, "r") as f:
    content = f.read()

changes = 0

# ──────────────────────────────────────────────────────────
# 1. Add defaultFilters to exclude Trash articles
# ──────────────────────────────────────────────────────────
OLD_OPTIONS = '''    doctype: "HD Article",
    selectable: true,
    view: {'''

NEW_OPTIONS = '''    doctype: "HD Article",
    selectable: true,
    defaultFilters: { status: ["!=", "Trash"] },
    view: {'''

if 'defaultFilters' not in content:
    if OLD_OPTIONS in content:
        content = content.replace(OLD_OPTIONS, NEW_OPTIONS)
        changes += 1
        print("1. Added defaultFilters to exclude Trash articles")
    else:
        print("1. WARNING: Could not find options block to patch")
else:
    print("1. defaultFilters already present")


# ──────────────────────────────────────────────────────────
# 2. Replace category delete with safe delete API
# ──────────────────────────────────────────────────────────

# Add the deleteCategorySafe resource after trashArticlesRes
OLD_TRASH_RES = '''const trashArticlesRes = createResource({
  url: "helpdesk.api.kb_custom.trash_articles",
});'''

NEW_TRASH_RES = '''const trashArticlesRes = createResource({
  url: "helpdesk.api.kb_custom.trash_articles",
});

const deleteCategorySafe = createResource({
  url: "helpdesk.api.kb_custom.delete_category_safe",
});'''

if 'deleteCategorySafe' not in content:
    if OLD_TRASH_RES in content:
        content = content.replace(OLD_TRASH_RES, NEW_TRASH_RES)
        changes += 1
        print("2a. Added deleteCategorySafe resource")
    else:
        print("2a. WARNING: Could not find trashArticlesRes block")
else:
    print("2a. deleteCategorySafe already present")

# Replace the handler to use safe delete
OLD_CAT_DELETE = '''          deleteCategory.submit(
            {
              doctype: "HD Article Category",
              name: groupedRow.group.value,
            },
            {
              onSuccess: () => {
                toast.success(__("Category deleted"));
                listViewRef.value.reload();
              },
            }
          );
          close();'''

NEW_CAT_DELETE = '''          deleteCategorySafe.submit(
            { category: groupedRow.group.value },
            {
              onSuccess: (r) => {
                toast.success(r?.message || __("Category deleted"));
                listViewRef.value.reload();
              },
              onError: (err) => {
                toast.error(err?.messages?.[0] || err.message);
              },
            }
          );
          close();'''

if 'deleteCategorySafe.submit' not in content:
    if OLD_CAT_DELETE in content:
        content = content.replace(OLD_CAT_DELETE, NEW_CAT_DELETE)
        changes += 1
        print("2b. Replaced category delete with safe delete")
    else:
        # Try alternate formatting
        print("2b. WARNING: Could not find exact delete block — checking alternate...")
        # Try with different close pattern
        OLD_ALT = '''          deleteCategory.submit(
            {
              doctype: "HD Article Category",
              name: groupedRow.group.value,
            },'''
        if OLD_ALT in content:
            # Find the full block and replace
            idx = content.index(OLD_ALT)
            # Find the matching close(); after this block
            end_marker = "close();"
            search_region = content[idx:idx+500]
            end_idx = search_region.index(end_marker) + len(end_marker)
            old_block = content[idx:idx+end_idx]
            new_block = '''          deleteCategorySafe.submit(
            { category: groupedRow.group.value },
            {
              onSuccess: (r) => {
                toast.success(r?.message || __("Category deleted"));
                listViewRef.value.reload();
              },
              onError: (err) => {
                toast.error(err?.messages?.[0] || err.message);
              },
            }
          );
          close();'''
            content = content.replace(old_block, new_block)
            changes += 1
            print("2b. Replaced category delete (alternate format)")
        else:
            print("2b. FAILED: Could not find delete block at all")
else:
    print("2b. deleteCategorySafe already in use")


# ──────────────────────────────────────────────────────────
# 3. Add Trash to statusMap
# ──────────────────────────────────────────────────────────
OLD_STATUS = '''  Archived: {
    label: __("Archived"),
    theme: "gray",
  },
};'''

NEW_STATUS = '''  Archived: {
    label: __("Archived"),
    theme: "gray",
  },
  Trash: {
    label: __("Trash"),
    theme: "red",
  },
};'''

if '"Trash"' not in content.split('statusMap')[1] if 'statusMap' in content else True:
    if OLD_STATUS in content:
        content = content.replace(OLD_STATUS, NEW_STATUS)
        changes += 1
        print("3. Added Trash to statusMap")
    else:
        print("3. WARNING: Could not find statusMap block to patch")
else:
    print("3. Trash already in statusMap")


# ──────────────────────────────────────────────────────────
# Write result
# ──────────────────────────────────────────────────────────
if changes > 0:
    with open(FILE, "w") as f:
        f.write(content)
    print(f"\nKnowledgeBaseAgent.vue: Applied {changes} patch(es)")
else:
    print("\nKnowledgeBaseAgent.vue: No changes needed")
