#!/usr/bin/env python3
"""Patch KnowledgeBaseAgent.vue to use trash (soft delete) instead of permanent delete."""

FILE = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/pages/knowledge-base/KnowledgeBaseAgent.vue"

with open(FILE, "r") as f:
    content = f.read()

# 1. Add trashArticles resource import
if "trash_articles" not in content:
    # Add a createResource for trashing
    trash_resource = """
const trashArticlesRes = createResource({
  url: "helpdesk.api.kb_custom.trash_articles",
});
"""
    # Insert after the generalCategory resource
    marker = "const generalCategory = createResource({"
    idx = content.index(marker)
    # Find the end of generalCategory block
    depth = 0
    i = content.index("{", idx)
    for j in range(i, len(content)):
        if content[j] == "{":
            depth += 1
        elif content[j] == "}":
            depth -= 1
            if depth == 0:
                # Find the closing );
                end = content.index(");", j) + 2
                content = content[:end] + "\n" + trash_resource + content[end:]
                break

    # 2. Replace handleDeleteArticles to use trash
    old_handler = '''function handleDeleteArticles() {
  deleteArticles.submit(
    {
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        listViewRef.value?.reload();
        listViewRef.value?.unselectAll();
        listSelections.value?.clear();
        toast.success(__("Articles deleted"));
      },
    }
  );
}'''

    new_handler = '''function handleDeleteArticles() {
  trashArticlesRes.submit(
    {
      articles: Array.from(listSelections.value),
    },
    {
      onSuccess: () => {
        listViewRef.value?.reload();
        listViewRef.value?.unselectAll();
        listSelections.value?.clear();
        toast.success(__("Articles moved to trash"));
      },
      onError: (error) => {
        const msg = error?.messages?.[0] || error.message;
        toast.error(msg);
      },
    }
  );
}'''

    content = content.replace(old_handler, new_handler)

    # 3. Update the delete confirmation dialog message
    content = content.replace(
        'message: __("Are you sure you want to delete these articles?")',
        'message: __("Articles will be moved to trash. You can restore them later.")'
    )
    content = content.replace(
        'title: __("Delete articles?")',
        'title: __("Move to trash?")'
    )

    with open(FILE, "w") as f:
        f.write(content)
    print("KnowledgeBaseAgent.vue patched to use trash for deletes")
else:
    print("Already patched for trash")
