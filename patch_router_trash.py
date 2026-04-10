#!/usr/bin/env python3
"""Patch the router to add KBTrash route."""

ROUTER = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/router/index.ts"

with open(ROUTER, "r") as f:
    content = f.read()

if "KBTrash" in content:
    print("KBTrash route already exists")
else:
    trash_route = """  {
    path: "/kb/trash",
    name: "KBTrash",
    component: () => import("@/pages/knowledge-base/KBTrash.vue"),
  },"""

    # Insert after the NewArticle route block
    marker = 'name: "NewArticle"'
    idx = content.index(marker)
    # Find the closing }, of this route
    close_idx = content.index("},", idx) + 2

    content = content[:close_idx] + "\n" + trash_route + content[close_idx:]

    with open(ROUTER, "w") as f:
        f.write(content)
    print("KBTrash route added to router")
