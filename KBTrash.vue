<template>
  <div class="flex flex-col">
    <LayoutHeader>
      <template #left-header>
        <Breadcrumbs :items="breadcrumbs" class="-ml-0.5" />
      </template>
      <template #right-header>
        <div class="flex items-center gap-2">
          <Badge
            v-if="retentionDays.data"
            :label="`Auto-delete after ${retentionDays.data} days`"
            variant="subtle"
            theme="orange"
          />
          <Button
            v-if="trashArticles.data?.length"
            variant="subtle"
            theme="red"
            :label="__('Empty Trash')"
            @click="confirmEmptyTrash"
          >
            <template #prefix>
              <LucideTrash2 class="h-4 w-4" />
            </template>
          </Button>
          <Button
            variant="subtle"
            :label="__('Settings')"
            @click="showSettings = true"
          >
            <template #prefix>
              <LucideSettings class="h-4 w-4" />
            </template>
          </Button>
        </div>
      </template>
    </LayoutHeader>

    <!-- Trash Settings Dialog -->
    <Dialog v-model="showSettings" :options="{ title: __('Trash Settings') }">
      <template #body-content>
        <div class="flex flex-col gap-3">
          <FormControl
            type="number"
            :label="__('Auto-delete articles after (days)')"
            v-model="retentionInput"
            :min="1"
            :max="365"
          />
          <p class="text-xs text-gray-500">
            Articles in trash will be automatically deleted after this many days.
          </p>
        </div>
      </template>
      <template #actions>
        <Button variant="solid" :label="__('Save')" @click="saveRetention" />
      </template>
    </Dialog>

    <!-- Empty state -->
    <div v-if="!trashArticles.data?.length && !trashArticles.loading" class="flex flex-col items-center justify-center py-20">
      <LucideTrash2 class="h-12 w-12 text-gray-300 mb-4" />
      <p class="text-lg text-gray-600">{{ __('Trash is empty') }}</p>
      <p class="text-sm text-gray-400">{{ __('Deleted articles will appear here') }}</p>
    </div>

    <!-- Loading state -->
    <div v-else-if="trashArticles.loading" class="flex items-center justify-center py-20">
      <LoadingIndicator class="h-6 w-6" />
    </div>

    <!-- Trash list -->
    <div v-else class="px-5 py-3">
      <!-- Selection bar -->
      <div
        v-if="selectedArticles.size > 0"
        class="flex items-center gap-3 px-4 py-2 bg-blue-50 rounded-lg mb-3"
      >
        <span class="text-sm text-blue-700 font-medium">
          {{ selectedArticles.size }} selected
        </span>
        <Button size="sm" variant="subtle" :label="__('Restore')" @click="handleRestore">
          <template #prefix>
            <LucideRotateCcw class="h-3.5 w-3.5" />
          </template>
        </Button>
        <Button size="sm" variant="subtle" theme="red" :label="__('Delete Permanently')" @click="handlePermanentDelete">
          <template #prefix>
            <LucideTrash2 class="h-3.5 w-3.5" />
          </template>
        </Button>
        <Button size="sm" variant="ghost" :label="__('Clear selection')" @click="selectedArticles.clear()" />
      </div>

      <!-- Table -->
      <div class="border rounded-lg overflow-hidden">
        <table class="w-full text-sm">
          <thead class="bg-gray-50 border-b">
            <tr>
              <th class="px-4 py-2.5 text-left w-8">
                <input
                  type="checkbox"
                  :checked="allSelected"
                  @change="toggleSelectAll"
                  class="rounded border-gray-300"
                />
              </th>
              <th class="px-4 py-2.5 text-left font-medium text-gray-600">{{ __('Title') }}</th>
              <th class="px-4 py-2.5 text-left font-medium text-gray-600">{{ __('Category') }}</th>
              <th class="px-4 py-2.5 text-left font-medium text-gray-600">{{ __('Deleted On') }}</th>
              <th class="px-4 py-2.5 text-left font-medium text-gray-600">{{ __('Days Left') }}</th>
              <th class="px-4 py-2.5 text-right font-medium text-gray-600">{{ __('Actions') }}</th>
            </tr>
          </thead>
          <tbody>
            <tr
              v-for="article in trashArticles.data"
              :key="article.name"
              class="border-b last:border-0 hover:bg-gray-50"
            >
              <td class="px-4 py-2.5">
                <input
                  type="checkbox"
                  :checked="selectedArticles.has(article.name)"
                  @change="toggleSelect(article.name)"
                  class="rounded border-gray-300"
                />
              </td>
              <td class="px-4 py-2.5">
                <span class="font-medium text-gray-900">{{ article.title }}</span>
              </td>
              <td class="px-4 py-2.5 text-gray-600">
                {{ article.category_name }}
              </td>
              <td class="px-4 py-2.5 text-gray-600">
                {{ formatDate(article.trashed_on) }}
              </td>
              <td class="px-4 py-2.5">
                <Badge
                  v-if="article.days_left >= 0"
                  :label="article.days_left + ' days'"
                  :variant="'subtle'"
                  :theme="article.days_left <= 3 ? 'red' : article.days_left <= 7 ? 'orange' : 'gray'"
                />
                <span v-else class="text-gray-400">—</span>
              </td>
              <td class="px-4 py-2.5 text-right">
                <div class="flex items-center justify-end gap-1">
                  <Button
                    size="sm"
                    variant="ghost"
                    :label="__('Restore')"
                    @click="restoreSingle(article.name)"
                  >
                    <template #prefix>
                      <LucideRotateCcw class="h-3.5 w-3.5" />
                    </template>
                  </Button>
                  <Button
                    size="sm"
                    variant="ghost"
                    theme="red"
                    @click="deleteSingle(article.name)"
                  >
                    <template #prefix>
                      <LucideTrash2 class="h-3.5 w-3.5" />
                    </template>
                  </Button>
                </div>
              </td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed } from "vue";
import { Badge, Button, Breadcrumbs, Dialog, FormControl, LoadingIndicator, createResource, toast } from "frappe-ui";
import LayoutHeader from "@/components/LayoutHeader.vue";
import { globalStore } from "@/stores/globalStore";
import { __ } from "@/translation";
import LucideTrash2 from "~icons/lucide/trash-2";
import LucideRotateCcw from "~icons/lucide/rotate-ccw";
import LucideSettings from "~icons/lucide/settings";

const { $dialog } = globalStore();

const showSettings = ref(false);
const retentionInput = ref(30);
const selectedArticles = ref(new Set<string>());

const trashArticles = createResource({
  url: "helpdesk.api.kb_custom.get_trash",
  auto: true,
  cache: ["trashArticles"],
});

const retentionDays = createResource({
  url: "helpdesk.api.kb_custom.get_trash_retention_days",
  auto: true,
  cache: ["trashRetention"],
  onSuccess(data: number) {
    retentionInput.value = data;
  },
});

const restoreRes = createResource({
  url: "helpdesk.api.kb_custom.restore_articles",
});

const deleteRes = createResource({
  url: "helpdesk.api.kb_custom.permanently_delete_articles",
});

const emptyTrashRes = createResource({
  url: "helpdesk.api.kb_custom.empty_trash",
});

const saveRetentionRes = createResource({
  url: "helpdesk.api.kb_custom.set_trash_retention_days",
});

const allSelected = computed(() => {
  if (!trashArticles.data?.length) return false;
  return trashArticles.data.every((a: any) => selectedArticles.value.has(a.name));
});

function toggleSelectAll() {
  if (allSelected.value) {
    selectedArticles.value.clear();
  } else {
    trashArticles.data?.forEach((a: any) => selectedArticles.value.add(a.name));
  }
}

function toggleSelect(name: string) {
  if (selectedArticles.value.has(name)) {
    selectedArticles.value.delete(name);
  } else {
    selectedArticles.value.add(name);
  }
}

function formatDate(dt: string) {
  if (!dt) return "—";
  return new Date(dt).toLocaleDateString("en-US", {
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  });
}

function handleRestore() {
  const articles = Array.from(selectedArticles.value);
  restoreRes.submit({ articles }, {
    onSuccess() {
      toast.success(__(`${articles.length} article(s) restored`));
      selectedArticles.value.clear();
      trashArticles.reload();
    },
    onError(e: any) {
      toast.error(e.messages?.[0] || e.message);
    },
  });
}

function restoreSingle(name: string) {
  restoreRes.submit({ articles: [name] }, {
    onSuccess() {
      toast.success(__("Article restored"));
      trashArticles.reload();
    },
    onError(e: any) {
      toast.error(e.messages?.[0] || e.message);
    },
  });
}

function handlePermanentDelete() {
  const articles = Array.from(selectedArticles.value);
  $dialog({
    title: __("Permanently delete?"),
    message: __(`This will permanently delete ${articles.length} article(s). This cannot be undone.`),
    actions: [
      {
        label: __("Delete"),
        variant: "solid",
        theme: "red",
        onClick({ close }: any) {
          deleteRes.submit({ articles }, {
            onSuccess() {
              toast.success(__("Articles permanently deleted"));
              selectedArticles.value.clear();
              trashArticles.reload();
              close();
            },
            onError(e: any) {
              toast.error(e.messages?.[0] || e.message);
              close();
            },
          });
        },
      },
    ],
  });
}

function deleteSingle(name: string) {
  $dialog({
    title: __("Permanently delete?"),
    message: __("This article will be permanently deleted. This cannot be undone."),
    actions: [
      {
        label: __("Delete"),
        variant: "solid",
        theme: "red",
        onClick({ close }: any) {
          deleteRes.submit({ articles: [name] }, {
            onSuccess() {
              toast.success(__("Article permanently deleted"));
              trashArticles.reload();
              close();
            },
            onError(e: any) {
              toast.error(e.messages?.[0] || e.message);
              close();
            },
          });
        },
      },
    ],
  });
}

function confirmEmptyTrash() {
  $dialog({
    title: __("Empty trash?"),
    message: __("All trashed articles will be permanently deleted. This cannot be undone."),
    actions: [
      {
        label: __("Empty Trash"),
        variant: "solid",
        theme: "red",
        onClick({ close }: any) {
          emptyTrashRes.submit({}, {
            onSuccess() {
              toast.success(__("Trash emptied"));
              trashArticles.reload();
              close();
            },
            onError(e: any) {
              toast.error(e.messages?.[0] || e.message);
              close();
            },
          });
        },
      },
    ],
  });
}

function saveRetention() {
  saveRetentionRes.submit({ days: retentionInput.value }, {
    onSuccess() {
      toast.success(__("Retention period updated"));
      retentionDays.reload();
      showSettings.value = false;
    },
    onError(e: any) {
      toast.error(e.messages?.[0] || e.message);
    },
  });
}

const breadcrumbs = computed(() => [
  { label: __("Knowledge Base"), route: { name: "KnowledgeBase" } },
  { label: __("Trash") },
]);
</script>
