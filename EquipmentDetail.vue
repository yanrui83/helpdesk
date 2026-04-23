<template>
  <div class="eq-detail-page">
    <!-- Header bar -->
    <div class="eq-detail-header">
      <button class="eq-back-btn" @click="$router.back()">
        <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2"><polyline points="15 18 9 12 15 6"/></svg>
        Back
      </button>
      <div v-if="!loading && !error" class="eq-header-info">
        <h2>{{ equipmentData.equipment_name }}</h2>
        <span class="eq-header-id">{{ equipmentData.name }}</span>
      </div>
      <div class="eq-header-actions">
        <span v-if="configSaving" class="eq-save-status saving">Saving...</span>
        <span v-else-if="configSaved" class="eq-save-status saved">✓ Saved to server</span>
        <button
          v-if="!loading && !error && isAgent"
          class="eq-btn"
          :class="isEditor ? 'eq-btn-warn' : 'eq-btn-secondary'"
          @click="toggleEditor"
        >
          {{ isEditor ? 'Exit Editor' : 'Editor Mode' }}
        </button>
        <a
          v-if="!loading && !error"
          :href="viewerFullUrl"
          target="_blank"
          class="eq-btn eq-btn-secondary"
        >Open in New Tab</a>
      </div>
    </div>

    <!-- Loading state -->
    <div v-if="loading" class="eq-detail-loading">
      <div class="eq-detail-spinner"></div>
      <span>Loading equipment...</span>
    </div>

    <!-- Error state -->
    <div v-else-if="error" class="eq-detail-error">
      <p>{{ error }}</p>
    </div>

    <!-- Embedded 3D viewer iframe -->
    <iframe
      v-else
      :src="viewerUrl"
      class="eq-viewer-frame"
      frameborder="0"
      allow="fullscreen"
      ref="viewerFrame"
    ></iframe>
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from "vue";
import { useRoute } from "vue-router";
import { createResource } from "frappe-ui";
import { useAuthStore } from "@/stores/auth";

const route = useRoute();
const authStore = useAuthStore();

const equipmentData = ref({});
const loading = ref(true);
const error = ref("");
const isEditor = ref(false);
const viewerFrame = ref(null);
const configSaving = ref(false);
const configSaved = ref(false);

const isAgent = computed(() => authStore.isAgent || authStore.hasDeskAccess);

const VIEWER_VER = "7";

const viewerUrl = computed(() => {
  if (!equipmentData.value.model_file) return "";
  const base = "/assets/helpdesk/3d-viewer/index.html";
  const params = new URLSearchParams();
  params.set("embedded", "1");
  params.set("model", equipmentData.value.model_file);
  params.set("equipment_id", String(route.params.equipmentId));
  if (isEditor.value) params.set("mode", "editor");
  if (equipmentData.value.config) {
    params.set("config", encodeURIComponent(equipmentData.value.config));
  }
  params.set("_v", VIEWER_VER);
  return `${base}?${params.toString()}`;
});

const viewerFullUrl = computed(() => {
  if (!equipmentData.value.model_file) return "#";
  const base = "/assets/helpdesk/3d-viewer/index.html";
  const params = new URLSearchParams();
  params.set("model", equipmentData.value.model_file);
  if (isEditor.value) params.set("mode", "editor");
  return `${base}?${params.toString()}`;
});

function toggleEditor() {
  isEditor.value = !isEditor.value;
}

// Listen for config-saved postMessage from iframe viewer
function handleViewerMessage(event) {
  if (!event.data || event.data.type !== "eq-config-saved") return;
  if (!isAgent.value) return;
  const newConfig = event.data.config;
  if (!newConfig) return;
  // Update local data so reloads use the latest config
  equipmentData.value.config = newConfig;
  // Persist to server
  configSaving.value = true;
  configSaved.value = false;
  saveConfigResource.submit({
    equipment_id: route.params.equipmentId,
    config: newConfig,
  });
}

const saveConfigResource = createResource({
  url: "helpdesk.api.equipment.save_equipment_config",
  onSuccess() {
    configSaving.value = false;
    configSaved.value = true;
    setTimeout(() => { configSaved.value = false; }, 3000);
  },
  onError(err) {
    configSaving.value = false;
    console.error("Failed to save config to server:", err);
  },
});

const equipmentResource = createResource({
  url: "helpdesk.api.equipment.get_equipment",
  params: { equipment_id: route.params.equipmentId },
  auto: true,
  onSuccess(data) {
    equipmentData.value = data;
    loading.value = false;
  },
  onError(err) {
    error.value = err?.message || "Failed to load equipment";
    loading.value = false;
  },
});

onMounted(() => {
  equipmentResource.fetch();
  window.addEventListener("message", handleViewerMessage);
});

onUnmounted(() => {
  window.removeEventListener("message", handleViewerMessage);
});
</script>

<style scoped>
.eq-detail-page {
  height: calc(100vh - 40px);
  display: flex;
  flex-direction: column;
  overflow: hidden;
}
.eq-detail-header {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 10px 16px;
  background: #fff;
  border-bottom: 1px solid #e5e7eb;
  flex-shrink: 0;
}
.eq-back-btn {
  display: flex;
  align-items: center;
  gap: 4px;
  background: none;
  border: 1px solid #e5e7eb;
  border-radius: 6px;
  padding: 6px 10px;
  font-size: 12px;
  color: #374151;
  cursor: pointer;
  font-weight: 500;
}
.eq-back-btn:hover { background: #f9fafb; }
.eq-header-info {
  flex: 1;
  min-width: 0;
  display: flex;
  align-items: center;
  gap: 10px;
}
.eq-header-info h2 {
  font-size: 15px;
  font-weight: 600;
  color: #1f2937;
  margin: 0;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}
.eq-header-id {
  font-size: 11px;
  color: #9ca3af;
  font-family: monospace;
}
.eq-header-actions {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-shrink: 0;
  margin-left: auto;
}
.eq-save-status {
  font-size: 12px;
  font-weight: 500;
  padding: 4px 10px;
  border-radius: 6px;
}
.eq-save-status.saving { color: #6b7280; background: #f3f4f6; }
.eq-save-status.saved { color: #059669; background: #d1fae5; }
.eq-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 6px 14px;
  border-radius: 6px;
  font-size: 12px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  border: 1px solid transparent;
  transition: all 0.15s;
}
.eq-btn-secondary {
  background: #fff;
  color: #374151;
  border-color: #d1d5db;
}
.eq-btn-secondary:hover { background: #f9fafb; }
.eq-btn-warn {
  background: #f97316;
  color: #fff;
  border-color: #f97316;
}
.eq-btn-warn:hover { background: #ea580c; }
.eq-viewer-frame {
  flex: 1;
  width: 100%;
  border: none;
}
.eq-detail-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  flex: 1;
  color: #6b7280;
  font-size: 13px;
}
.eq-detail-spinner {
  width: 24px;
  height: 24px;
  border: 2px solid #e5e7eb;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: eq-d-spin 0.8s linear infinite;
}
@keyframes eq-d-spin { to { transform: rotate(360deg); } }
.eq-detail-error {
  display: flex;
  align-items: center;
  justify-content: center;
  flex: 1;
  color: #6b7280;
  font-size: 13px;
}
</style>
