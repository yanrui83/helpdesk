<template>
  <div class="eq-list-page">
    <div class="eq-list-header">
      <div>
        <h1>{{ isPortal ? 'Spare Part' : 'Equipment' }}</h1>
        <p>{{ isPortal ? 'View 3D models and order spare parts' : 'View and manage 3D equipment models' }}</p>
      </div>
      <div v-if="!isPortal" class="eq-list-actions">
        <a
          href="/app/hd-equipment/new"
          target="_blank"
          class="eq-btn eq-btn-primary"
        >
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
            <line x1="12" y1="5" x2="12" y2="19"/><line x1="5" y1="12" x2="19" y2="12"/>
          </svg>
          New Equipment
        </a>
      </div>
    </div>
    <div v-if="loading" class="eq-list-loading">
      <div class="eq-list-spinner"></div>
      <span>Loading equipment...</span>
    </div>
    <div v-else-if="equipment.length === 0" class="eq-list-empty">
      <svg width="48" height="48" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="1.5">
        <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
        <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
        <line x1="12" y1="22.08" x2="12" y2="12"/>
      </svg>
      <h3>No Equipment Found</h3>
      <p v-if="isPortal">No 3D equipment models have been assigned to your account yet.</p>
      <p v-else>Create an equipment record to assign a 3D model to a customer.</p>
      <a
        v-if="!isPortal"
        href="/app/hd-equipment/new"
        target="_blank"
        class="eq-btn eq-btn-primary"
        style="margin-top: 16px; display: inline-flex;"
      >
        + New Equipment
      </a>
    </div>
    <div v-else class="eq-list-grid">
      <div
        v-for="eq in equipment"
        :key="eq.name"
        class="eq-list-card"
        @click="navigateToEquipment(eq.name)"
      >
        <div class="eq-card-icon">
          <svg width="32" height="32" viewBox="0 0 24 24" fill="none" stroke="#4f46e5" stroke-width="1.5">
            <path d="M21 16V8a2 2 0 0 0-1-1.73l-7-4a2 2 0 0 0-2 0l-7 4A2 2 0 0 0 3 8v8a2 2 0 0 0 1 1.73l7 4a2 2 0 0 0 2 0l7-4A2 2 0 0 0 21 16z"/>
            <polyline points="3.27 6.96 12 12.01 20.73 6.96"/>
            <line x1="12" y1="22.08" x2="12" y2="12"/>
          </svg>
        </div>
        <div class="eq-card-info">
          <h3>{{ eq.equipment_name }}</h3>
          <p class="eq-card-customer">{{ eq.customer_name }}</p>
          <p class="eq-card-id">{{ eq.name }}</p>
        </div>
        <div class="eq-card-arrow">
          <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="#9ca3af" stroke-width="2">
            <polyline points="9 18 15 12 9 6"/>
          </svg>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
import { ref, onMounted } from "vue";
import { useRouter } from "vue-router";
import { createResource } from "frappe-ui";

const props = defineProps({
  isPortal: { type: Boolean, default: false },
});

const router = useRouter();
const equipment = ref([]);
const loading = ref(true);

const equipmentResource = createResource({
  url: "helpdesk.api.equipment.get_equipment_list",
  auto: true,
  onSuccess(data) {
    equipment.value = data || [];
    loading.value = false;
    // Portal users with exactly 1 equipment go straight to the detail view
    if (props.isPortal && equipment.value.length === 1) {
      router.replace({ name: "CustomerEquipmentDetail", params: { equipmentId: equipment.value[0].name } });
    }
  },
  onError() {
    loading.value = false;
  },
});

function navigateToEquipment(id) {
  const routeName = props.isPortal ? "CustomerEquipmentDetail" : "EquipmentDetail";
  router.push({ name: routeName, params: { equipmentId: id } });
}

onMounted(() => {
  equipmentResource.fetch();
});
</script>

<style scoped>
.eq-list-page {
  max-width: 960px;
  margin: 0 auto;
  padding: 32px 24px;
}
.eq-list-header {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  margin-bottom: 24px;
  gap: 16px;
  flex-wrap: wrap;
}
.eq-list-header h1 {
  font-size: 20px;
  font-weight: 700;
  color: #1f2937;
  margin: 0 0 4px;
}
.eq-list-header p {
  font-size: 13px;
  color: #6b7280;
  margin: 0;
}
.eq-list-actions {
  display: flex;
  gap: 8px;
  flex-shrink: 0;
}
.eq-btn {
  display: flex;
  align-items: center;
  gap: 6px;
  padding: 8px 16px;
  border-radius: 8px;
  font-size: 13px;
  font-weight: 600;
  text-decoration: none;
  cursor: pointer;
  transition: all 0.15s;
  border: 1px solid transparent;
  white-space: nowrap;
}
.eq-btn-primary {
  background: #4f46e5;
  color: #fff;
  border-color: #4f46e5;
}
.eq-btn-primary:hover {
  background: #4338ca;
  border-color: #4338ca;
}
.eq-btn-secondary {
  background: #fff;
  color: #374151;
  border-color: #d1d5db;
}
.eq-btn-secondary:hover {
  background: #f9fafb;
  border-color: #9ca3af;
}
.eq-list-loading {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  padding: 60px 0;
  color: #6b7280;
  font-size: 13px;
}
.eq-list-spinner {
  width: 20px;
  height: 20px;
  border: 2px solid #e5e7eb;
  border-top-color: #4f46e5;
  border-radius: 50%;
  animation: eq-spin 0.8s linear infinite;
}
@keyframes eq-spin { to { transform: rotate(360deg); } }
.eq-list-empty {
  text-align: center;
  padding: 60px 20px;
  color: #6b7280;
}
.eq-list-empty h3 {
  font-size: 15px;
  font-weight: 600;
  color: #374151;
  margin: 16px 0 4px;
}
.eq-list-empty p {
  font-size: 13px;
  margin: 0;
}
.eq-list-grid {
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.eq-list-card {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 16px 20px;
  background: #fff;
  border: 1px solid #e5e7eb;
  border-radius: 12px;
  cursor: pointer;
  transition: all 0.15s;
  box-shadow: 0 1px 2px rgba(0,0,0,.05);
}
.eq-list-card:hover {
  border-color: #d1d5db;
  box-shadow: 0 4px 6px -1px rgba(0,0,0,.1);
  transform: translateY(-1px);
}
.eq-card-icon {
  width: 48px;
  height: 48px;
  border-radius: 10px;
  background: rgba(99,102,241,.08);
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
}
.eq-card-info {
  flex: 1;
  min-width: 0;
}
.eq-card-info h3 {
  font-size: 14px;
  font-weight: 600;
  color: #1f2937;
  margin: 0 0 2px;
}
.eq-card-customer {
  font-size: 12px;
  color: #6b7280;
  margin: 0 0 2px;
}
.eq-card-id {
  font-size: 11px;
  color: #9ca3af;
  font-family: 'JetBrains Mono', monospace;
  margin: 0;
}
.eq-card-arrow {
  flex-shrink: 0;
}
</style>
