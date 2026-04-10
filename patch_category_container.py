#!/usr/bin/env python3
"""Patch CategoryFolderContainer.vue to use access-controlled categories API."""

FILE = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/components/knowledge-base/CategoryFolderContainer.vue"

with open(FILE, "r") as f:
    content = f.read()

if "kb_custom" not in content:
    # Replace the import from knowledgeBase store with a local createResource
    old_script = '''<script setup lang="ts">
import { onMounted } from "vue";
import { categories } from "@/stores/knowledgeBase";
import CategoryFolder from "./CategoryFolder.vue";

onMounted(() => {
  categories.fetch();
});
</script>'''

    new_script = '''<script setup lang="ts">
import { onMounted } from "vue";
import { createResource } from "frappe-ui";
import CategoryFolder from "./CategoryFolder.vue";

const categories = createResource({
  url: "helpdesk.api.kb_custom.get_categories_filtered",
  cache: ["categoriesFiltered"],
});

onMounted(() => {
  categories.fetch();
});
</script>'''

    content = content.replace(old_script, new_script)

    with open(FILE, "w") as f:
        f.write(content)
    print("CategoryFolderContainer.vue patched for access control")
else:
    print("Already patched")
