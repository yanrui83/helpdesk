#!/usr/bin/env python3
"""
Patch kb_custom.py: Add delete_category_safe function.
Safely deletes a category by moving articles to General and
un-parenting sub-categories before deletion.
"""

FILE = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/api/kb_custom.py"

with open(FILE, "r") as f:
    content = f.read()

ADDITION = '''

# ═══════════════════════════════════════════════════════════════
# SAFE CATEGORY DELETE (handles sub-categories properly)
# ═══════════════════════════════════════════════════════════════

@frappe.whitelist()
def delete_category_safe(category):
    """Safely delete a category:
    - Moves articles from this category to General
    - Moves sub-categories to root level (removes parent_category)
    - Then deletes the category
    """
    frappe.has_permission("HD Article Category", "delete", throw=True)

    cat_name = frappe.db.get_value("HD Article Category", category, "category_name")
    if not cat_name:
        frappe.throw(_("Category not found"))
    if cat_name == "General":
        frappe.throw(_("Cannot delete the General category"))

    general_category = frappe.db.get_value(
        "HD Article Category", {"category_name": "General"}, "name"
    )

    # 1. Move all articles from this category to General
    articles = frappe.get_all("HD Article", filters={"category": category}, pluck="name")
    for article_name in articles:
        frappe.db.set_value("HD Article", article_name, "category", general_category, update_modified=False)

    # 2. Move sub-categories to root level (remove parent)
    subcats = frappe.get_all(
        "HD Article Category",
        filters={"parent_category": category},
        pluck="name",
    )
    for subcat in subcats:
        frappe.db.set_value("HD Article Category", subcat, "parent_category", None, update_modified=False)

    # 3. Now safe to delete the category
    frappe.delete_doc("HD Article Category", category, force=True)
    frappe.db.commit()

    return {"message": f"Category \\"{cat_name}\\" deleted. {len(articles)} article(s) moved to General, {len(subcats)} sub-category(ies) moved to root."}
'''

if "delete_category_safe" in content:
    print("kb_custom.py: Already has delete_category_safe")
else:
    content += ADDITION
    with open(FILE, "w") as f:
        f.write(content)
    print("kb_custom.py: Added delete_category_safe function")
