<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Create Sub-Category') }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ __('Parent Category') }}</label>
          <select
            v-model="parentCategory"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
          >
            <option value="">{{ __('Select parent category...') }}</option>
            <option v-for="cat in categories.data" :key="cat.name" :value="cat.name">
              {{ cat.category_name }}
            </option>
          </select>
        </div>
        <FormControl
          type="text"
          :label="__('Sub-Category Name')"
          v-model="title"
          :placeholder="__('Enter sub-category name...')"
        />
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Create')"
          :disabled="!title || !parentCategory"
          @click="handleCreate"
          :loading="createRes.loading"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, watch } from "vue";
import { Button, Dialog, FormControl, createResource, toast } from "frappe-ui";
import { __ } from "@/translation";
import { useRouter } from "vue-router";

const router = useRouter();
const show = defineModel<boolean>({ default: false });

const emit = defineEmits(["created"]);

const title = ref("");
const parentCategory = ref("");

const categories = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Article Category",
    fields: ["name", "category_name"],
    order_by: "category_name asc",
    limit_page_length: 0,
  },
  auto: true,
  cache: ["parentCategories"],
});

const createRes = createResource({
  url: "helpdesk.api.kb_custom.create_subcategory",
});

function handleCreate() {
  createRes.submit(
    { title: title.value, parent_category: parentCategory.value },
    {
      onSuccess(data: any) {
        toast.success(__("Sub-category created"));
        emit("created", data);
        show.value = false;
        router.push({
          name: "Article",
          params: { articleId: data.article },
          query: {
            category: data.category,
            title: title.value,
            isEdit: 1,
          },
        });
      },
      onError(e: any) {
        toast.error(e.messages?.[0] || e.message);
      },
    }
  );
}

watch(show, (val) => {
  if (val) {
    title.value = "";
    parentCategory.value = "";
    categories.reload();
  }
});
</script>
