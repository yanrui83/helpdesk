#!/bin/bash
# Patch Sidebar.vue to conditionally show/hide "Spare Part" tab
# based on whether the customer has equipment

SIDEBAR="/home/frappe/frappe-bench/apps/helpdesk/desk/src/components/layouts/Sidebar.vue"

echo "Patching Sidebar.vue..."

# 1. Add import for call from frappe-ui (if not already present) - it's already imported via frappe-ui
# 2. Add hasEquipment ref and fetch logic
# 3. Modify allViews to filter out requiresEquipment items

# --- Step 1: Add hasEquipment ref after showCommandPalette ---
sed -i '/const showCommandPalette = ref(false);/a \
\
const hasEquipment = ref(false);\
' "$SIDEBAR"

# --- Step 2: Add equipment check in onMounted ---
# We need to add the check after the existing onMounted. Let's insert it as a new onMounted.
sed -i '/function setUpOnboarding/i \
// Check if portal user has equipment (for conditional sidebar tab)\
async function checkEquipment() {\
  if (!isCustomerPortal.value) return;\
  try {\
    const result = await call("helpdesk.api.equipment.has_equipment");\
    hasEquipment.value = !!result;\
  } catch (e) {\
    hasEquipment.value = false;\
  }\
}\
' "$SIDEBAR"

# --- Step 3: Add checkEquipment() call in the onMounted block ---
sed -i 's/setUpOnboarding();/setUpOnboarding();\n  checkEquipment();/' "$SIDEBAR"

# --- Step 4: Filter items in allViews computed ---
# Replace the line that assigns items from customer/agent options to also filter requiresEquipment
sed -i 's/if (!isCallingEnabled.value) {/if (!isCallingEnabled.value) {\n    items = items.filter((item) => item.label !== __("Call Logs"));\n  }\n\n  if (isCustomerPortal.value) {\n    items = items.filter((item) => !item.requiresEquipment || hasEquipment.value);\n  }\n\n  if (false) {/' "$SIDEBAR"

echo "Sidebar.vue patched."
