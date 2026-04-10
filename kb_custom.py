"""
Custom Knowledge Base API — Recycle Bin, Sub-categories, Category Access Control.
Extends helpdesk KB with:
  1) Soft-delete (Trash) for articles with configurable retention
  2) Sub-category (parent_category) support
  3) Per-customer category visibility
"""

import frappe
from frappe import _
from frappe.utils import now_datetime, add_days, getdate, get_user_info_for_avatar
from bs4 import BeautifulSoup


# ═══════════════════════════════════════════════════════════════
# 1. RECYCLE BIN — Soft Delete / Restore / Purge
# ═══════════════════════════════════════════════════════════════

@frappe.whitelist()
def trash_articles(articles):
    """Move articles to trash (soft delete). Expects list of article names."""
    if isinstance(articles, str):
        import json
        articles = json.loads(articles)

    frappe.has_permission("HD Article", "write", throw=True)

    for name in articles:
        doc = frappe.get_doc("HD Article", name)
        doc.status = "Trash"
        doc.trashed_on = now_datetime()
        doc.flags.ignore_validate = True
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    return {"message": f"{len(articles)} article(s) moved to trash"}


@frappe.whitelist()
def restore_articles(articles):
    """Restore trashed articles back to Draft status."""
    if isinstance(articles, str):
        import json
        articles = json.loads(articles)

    frappe.has_permission("HD Article", "write", throw=True)

    for name in articles:
        doc = frappe.get_doc("HD Article", name)
        if doc.status != "Trash":
            continue
        doc.status = "Draft"
        doc.trashed_on = None
        doc.flags.ignore_validate = True
        doc.save(ignore_permissions=True)

    frappe.db.commit()
    return {"message": f"{len(articles)} article(s) restored"}


@frappe.whitelist()
def permanently_delete_articles(articles):
    """Permanently delete trashed articles. Cannot be undone."""
    if isinstance(articles, str):
        import json
        articles = json.loads(articles)

    frappe.has_permission("HD Article", "delete", throw=True)

    count = 0
    for name in articles:
        status = frappe.db.get_value("HD Article", name, "status")
        if status == "Trash":
            frappe.delete_doc("HD Article", name, force=True)
            count += 1

    frappe.db.commit()
    return {"message": f"{count} article(s) permanently deleted"}


@frappe.whitelist()
def get_trash(limit_page_length=50, limit_start=0):
    """Get all trashed articles."""
    articles = frappe.get_all(
        "HD Article",
        filters={"status": "Trash"},
        fields=["name", "title", "trashed_on", "author", "modified", "category"],
        order_by="trashed_on desc",
        limit_page_length=int(limit_page_length),
        limit_start=int(limit_start),
    )
    for a in articles:
        a["author_info"] = get_user_info_for_avatar(a["author"]) if a.get("author") else {}
        if a.get("category"):
            a["category_name"] = frappe.db.get_value(
                "HD Article Category", a["category"], "category_name"
            ) or "Unknown"
        else:
            a["category_name"] = "No Category"
        # Calculate days remaining before auto-purge
        retention = get_trash_retention_days()
        if a.get("trashed_on") and retention > 0:
            purge_date = add_days(a["trashed_on"], retention)
            days_left = (getdate(purge_date) - getdate(now_datetime())).days
            a["days_left"] = max(0, days_left)
        else:
            a["days_left"] = -1  # No auto-purge

    return articles


@frappe.whitelist()
def get_trash_retention_days():
    """Get configured retention days. Default 30."""
    return frappe.db.get_single_value("HD Settings", "trash_retention_days") or 30


@frappe.whitelist()
def set_trash_retention_days(days):
    """Set trash retention period."""
    frappe.has_permission("HD Settings", "write", throw=True)
    days = int(days)
    if days < 1:
        frappe.throw(_("Retention days must be at least 1"))
    frappe.db.set_single_value("HD Settings", "trash_retention_days", days)
    frappe.db.commit()
    return {"message": f"Trash retention set to {days} days"}


def auto_purge_trash():
    """Scheduled task: permanently delete articles past retention period.
    Called by scheduler (add to hooks.py daily events).
    """
    retention = get_trash_retention_days()
    if retention <= 0:
        return

    cutoff = add_days(now_datetime(), -retention)
    old_articles = frappe.get_all(
        "HD Article",
        filters={"status": "Trash", "trashed_on": ["<", cutoff]},
        pluck="name",
    )
    for name in old_articles:
        frappe.delete_doc("HD Article", name, force=True)

    if old_articles:
        frappe.db.commit()
        frappe.logger().info(f"Auto-purged {len(old_articles)} trashed articles")


@frappe.whitelist()
def empty_trash():
    """Permanently delete ALL trashed articles."""
    frappe.has_permission("HD Article", "delete", throw=True)

    articles = frappe.get_all(
        "HD Article", filters={"status": "Trash"}, pluck="name"
    )
    for name in articles:
        frappe.delete_doc("HD Article", name, force=True)

    frappe.db.commit()
    return {"message": f"{len(articles)} article(s) permanently deleted"}


# ═══════════════════════════════════════════════════════════════
# 2. SUB-CATEGORIES
# ═══════════════════════════════════════════════════════════════

@frappe.whitelist()
def create_subcategory(title, parent_category):
    """Create a sub-category under a parent category."""
    frappe.has_permission("HD Article Category", "create", throw=True)

    if not parent_category:
        frappe.throw(_("Parent category is required for sub-categories"))

    if not frappe.db.exists("HD Article Category", parent_category):
        frappe.throw(_("Parent category does not exist"))

    category = frappe.new_doc("HD Article Category")
    category.category_name = title
    category.parent_category = parent_category
    category.insert()

    # Create a default article in the new sub-category
    article = frappe.new_doc("HD Article")
    article.title = "New Article"
    article.category = category.name
    article.insert()

    return {"category": category.name, "article": article.name}


@frappe.whitelist(allow_guest=True)
def get_categories_tree():
    """Get categories in a tree structure with sub-categories nested."""
    user = frappe.session.user

    categories = frappe.get_all(
        "HD Article Category",
        fields=["name", "category_name", "description", "icon", "parent_category"],
        order_by="category_name asc",
    )

    # Count published articles per category
    for c in categories:
        c["article_count"] = frappe.db.count(
            "HD Article",
            filters={"category": c["name"], "status": "Published"},
        )

    # Apply access control for non-agents
    from helpdesk.utils import is_agent
    if not is_agent():
        categories = _filter_categories_by_access(categories, user)

    # Build tree: separate root and children
    cat_map = {c["name"]: {**c, "children": []} for c in categories}
    roots = []

    for c in categories:
        parent = c.get("parent_category")
        if parent and parent in cat_map:
            cat_map[parent]["children"].append(cat_map[c["name"]])
        else:
            roots.append(cat_map[c["name"]])

    # Sort: most articles first, filter empty top-levels only for customers
    if not is_agent():
        roots = _filter_empty_tree(roots)

    roots.sort(key=lambda x: x["article_count"], reverse=True)
    return roots


def _filter_empty_tree(nodes):
    """Recursively remove nodes with no articles (and no children with articles)."""
    result = []
    for node in nodes:
        node["children"] = _filter_empty_tree(node.get("children", []))
        total = node["article_count"] + sum(c["article_count"] for c in node["children"])
        if total > 0:
            result.append(node)
    return result


@frappe.whitelist(allow_guest=True)
def get_category_with_children(category):
    """Get a category and its direct sub-categories."""
    cat = frappe.get_doc("HD Article Category", category).as_dict()
    children = frappe.get_all(
        "HD Article Category",
        filters={"parent_category": category},
        fields=["name", "category_name", "description", "icon"],
    )
    for c in children:
        c["article_count"] = frappe.db.count(
            "HD Article",
            filters={"category": c["name"], "status": "Published"},
        )
    cat["children"] = children
    cat["article_count"] = frappe.db.count(
        "HD Article",
        filters={"category": category, "status": "Published"},
    )
    return cat


# ═══════════════════════════════════════════════════════════════
# 3. CATEGORY ACCESS CONTROL
# ═══════════════════════════════════════════════════════════════

@frappe.whitelist()
def get_category_access(category):
    """Get list of customers who have access to a category."""
    frappe.has_permission("HD Article Category", "read", throw=True)

    access_list = frappe.get_all(
        "HD Category Access",
        filters={"category": category},
        fields=["name", "user", "user_name"],
    )
    return access_list


@frappe.whitelist()
def set_category_access(category, users):
    """Set which customers can see a category.
    If users is empty, the category is public (visible to all).
    If users is provided, only those customers can see the category.

    Args:
        category: HD Article Category name
        users: JSON list of user emails, or empty list for public
    """
    if isinstance(users, str):
        import json
        users = json.loads(users)

    frappe.has_permission("HD Article Category", "write", throw=True)

    if not frappe.db.exists("HD Article Category", category):
        frappe.throw(_("Category does not exist"))

    # Remove existing access entries
    existing = frappe.get_all(
        "HD Category Access",
        filters={"category": category},
        pluck="name",
    )
    for entry in existing:
        frappe.delete_doc("HD Category Access", entry, force=True)

    # Add new entries
    for user_email in users:
        if not user_email or not isinstance(user_email, str):
            continue
        user_email = user_email.strip()
        if not frappe.db.exists("User", user_email):
            continue

        user_name = frappe.db.get_value("User", user_email, "full_name") or user_email
        doc = frappe.new_doc("HD Category Access")
        doc.category = category
        doc.user = user_email
        doc.user_name = user_name
        doc.insert(ignore_permissions=True)

    frappe.db.commit()

    if users:
        return {"message": f"Access restricted to {len(users)} user(s)"}
    else:
        return {"message": "Category is now public (visible to all)"}


@frappe.whitelist()
def get_all_customers():
    """Get list of all customers (non-agent users) for access control UI."""
    frappe.has_permission("HD Article Category", "read", throw=True)

    users = frappe.get_all(
        "User",
        filters={
            "enabled": 1,
            "user_type": "Website User",
            "name": ["not in", ["Guest", "Administrator"]],
        },
        fields=["name", "full_name", "email"],
        order_by="full_name asc",
    )
    return users


def _filter_categories_by_access(categories, user):
    """Filter categories based on access control rules.
    - If a category has NO access entries, it's public (visible to all).
    - If a category HAS access entries, only listed users can see it.
    """
    if user == "Administrator" or user == "Guest":
        return categories

    # Get all restricted categories and which users have access
    restricted = frappe.get_all(
        "HD Category Access",
        fields=["category", "user"],
    )

    if not restricted:
        return categories  # No restrictions anywhere

    # Build map: category -> set of allowed users
    access_map = {}
    for r in restricted:
        access_map.setdefault(r["category"], set()).add(r["user"])

    # Filter: keep public categories + categories the user has access to
    filtered = []
    for cat in categories:
        allowed_users = access_map.get(cat["name"])
        if allowed_users is None:
            # No restrictions = public
            filtered.append(cat)
        elif user in allowed_users:
            filtered.append(cat)
        # else: restricted and user not in list -> skip

    return filtered


# Override for customer-facing category listing with access control
@frappe.whitelist(allow_guest=True)
def get_categories_filtered():
    """Get categories filtered by access control for current user.
    Replacement for the default get_categories endpoint for customer portal.
    """
    user = frappe.session.user
    from helpdesk.utils import is_agent

    categories = frappe.get_all(
        "HD Article Category",
        fields=["name", "category_name", "modified", "parent_category", "description", "icon"],
    )

    for c in categories:
        c["article_count"] = frappe.db.count(
            "HD Article",
            filters={"category": c["name"], "status": "Published"},
        )

    # Apply access control for customers
    if not is_agent():
        categories = _filter_categories_by_access(categories, user)

    # Filter out empty categories for customers
    if not is_agent():
        categories = [c for c in categories if c["article_count"] > 0]

    categories.sort(key=lambda c: c["article_count"], reverse=True)
    return categories


# ═══════════════════════════════════════════════════════════════
# OVERRIDE: get_category_articles with access control
# ═══════════════════════════════════════════════════════════════

@frappe.whitelist(allow_guest=True)
def get_category_articles_filtered(category):
    """Get articles for a category, respecting access control."""
    user = frappe.session.user
    from helpdesk.utils import is_agent

    # Check access for customers
    if not is_agent():
        restricted = frappe.get_all(
            "HD Category Access",
            filters={"category": category},
            pluck="user",
        )
        if restricted and user not in restricted:
            frappe.throw(_("You don't have access to this category"), frappe.PermissionError)

    articles = frappe.get_all(
        "HD Article",
        filters={"category": category, "status": "Published"},
        fields=["name", "title", "published_on", "modified", "author", "content"],
    )
    for article in articles:
        article["author"] = get_user_info_for_avatar(article["author"])
        soup = BeautifulSoup(article["content"], "html.parser")
        article["content"] = str(soup.text)[:100]

    return articles
