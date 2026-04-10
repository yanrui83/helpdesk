<template>
  <Dialog
    v-model="show"
    :options="{ title: __('Category Access Control'), size: 'lg' }"
  >
    <template #body-content>
      <div class="flex flex-col gap-4">
        <!-- Category selector -->
        <div>
          <label class="block text-sm font-medium text-gray-700 mb-1">{{ __('Category') }}</label>
          <select
            v-model="selectedCategory"
            class="w-full border border-gray-300 rounded-md px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
            @change="loadAccess"
          >
            <option value="">{{ __('Select a category...') }}</option>
            <option v-for="cat in allCategories.data" :key="cat.name" :value="cat.name">
              {{ cat.category_name }}{{ cat.parent_category ? ' (sub)' : '' }}
            </option>
          </select>
        </div>

        <div v-if="selectedCategory" class="flex flex-col gap-3">
          <!-- Access mode -->
          <div class="flex items-center gap-3 p-3 bg-gray-50 rounded-lg">
            <div class="flex items-center gap-2">
              <input
                type="radio"
                id="public"
                value="public"
                v-model="accessMode"
                class="text-blue-600"
              />
              <label for="public" class="text-sm font-medium text-gray-700">
                {{ __('Public') }}
              </label>
            </div>
            <div class="flex items-center gap-2">
              <input
                type="radio"
                id="restricted"
                value="restricted"
                v-model="accessMode"
                class="text-blue-600"
              />
              <label for="restricted" class="text-sm font-medium text-gray-700">
                {{ __('Restricted') }}
              </label>
            </div>
            <span class="text-xs text-gray-500 ml-2">
              {{ accessMode === 'public'
                ? __('All customers can see this category')
                : __('Only selected customers can see this category')
              }}
            </span>
          </div>

          <!-- Customer selection (only for restricted mode) -->
          <div v-if="accessMode === 'restricted'" class="flex flex-col gap-2">
            <div class="flex items-center justify-between">
              <label class="text-sm font-medium text-gray-700">{{ __('Allowed Customers') }}</label>
              <span class="text-xs text-gray-500">{{ selectedUsers.length }} selected</span>
            </div>

            <!-- Search -->
            <FormControl
              type="text"
              :placeholder="__('Search customers...')"
              v-model="searchQuery"
              size="sm"
            />

            <!-- Customer list -->
            <div class="border rounded-lg max-h-60 overflow-y-auto">
              <div
                v-for="customer in filteredCustomers"
                :key="customer.name"
                class="flex items-center gap-3 px-3 py-2 hover:bg-gray-50 border-b last:border-0 cursor-pointer"
                @click="toggleUser(customer.name)"
              >
                <input
                  type="checkbox"
                  :checked="selectedUsers.includes(customer.name)"
                  class="rounded border-gray-300 text-blue-600"
                  @click.stop
                  @change="toggleUser(customer.name)"
                />
                <div class="flex flex-col">
                  <span class="text-sm font-medium text-gray-900">{{ customer.full_name || customer.name }}</span>
                  <span class="text-xs text-gray-500">{{ customer.email || customer.name }}</span>
                </div>
              </div>
              <div v-if="!filteredCustomers.length" class="px-3 py-4 text-center text-sm text-gray-400">
                {{ __('No customers found') }}
              </div>
            </div>
          </div>
        </div>
      </div>
    </template>
    <template #actions>
      <div class="flex gap-2">
        <Button variant="subtle" :label="__('Cancel')" @click="show = false" />
        <Button
          variant="solid"
          :label="__('Save Access')"
          :disabled="!selectedCategory"
          @click="saveAccess"
          :loading="saveRes.loading"
        />
      </div>
    </template>
  </Dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch } from "vue";
import { Button, Dialog, FormControl, createResource, toast } from "frappe-ui";
import { __ } from "@/translation";

const show = defineModel<boolean>({ default: false });

const selectedCategory = ref("");
const accessMode = ref<"public" | "restricted">("public");
const selectedUsers = ref<string[]>([]);
const searchQuery = ref("");

const allCategories = createResource({
  url: "frappe.client.get_list",
  params: {
    doctype: "HD Article Category",
    fields: ["name", "category_name", "parent_category"],
    order_by: "category_name asc",
    limit_page_length: 0,
  },
  auto: true,
  cache: ["allCategoriesAccess"],
});

const customers = createResource({
  url: "helpdesk.api.kb_custom.get_all_customers",
  auto: true,
  cache: ["allCustomers"],
});

const accessRes = createResource({
  url: "helpdesk.api.kb_custom.get_category_access",
});

const saveRes = createResource({
  url: "helpdesk.api.kb_custom.set_category_access",
});

const filteredCustomers = computed(() => {
  if (!customers.data) return [];
  const q = searchQuery.value.toLowerCase();
  if (!q) return customers.data;
  return customers.data.filter(
    (c: any) =>
      (c.full_name || "").toLowerCase().includes(q) ||
      (c.email || c.name || "").toLowerCase().includes(q)
  );
});

function loadAccess() {
  if (!selectedCategory.value) return;
  accessRes.submit({ category: selectedCategory.value }, {
    onSuccess(data: any) {
      if (data && data.length > 0) {
        accessMode.value = "restricted";
        selectedUsers.value = data.map((d: any) => d.user);
      } else {
        accessMode.value = "public";
        selectedUsers.value = [];
      }
    },
  });
}

function toggleUser(email: string) {
  const idx = selectedUsers.value.indexOf(email);
  if (idx >= 0) {
    selectedUsers.value.splice(idx, 1);
  } else {
    selectedUsers.value.push(email);
  }
}

function saveAccess() {
  const users = accessMode.value === "public" ? [] : selectedUsers.value;
  saveRes.submit(
    { category: selectedCategory.value, users: JSON.stringify(users) },
    {
      onSuccess() {
        toast.success(__("Access control updated"));
        show.value = false;
      },
      onError(e: any) {
        toast.error(e.messages?.[0] || e.message);
      },
    }
  );
}

watch(show, (val) => {
  if (val) {
    selectedCategory.value = "";
    accessMode.value = "public";
    selectedUsers.value = [];
    searchQuery.value = "";
    allCategories.reload();
    customers.reload();
  }
});
</script>
