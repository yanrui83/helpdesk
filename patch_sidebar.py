#!/usr/bin/env python3
"""Patch Sidebar.vue to conditionally show 'Spare Part' tab based on equipment access."""

import sys

SIDEBAR_PATH = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/components/layouts/Sidebar.vue"

with open(SIDEBAR_PATH, "r") as f:
    content = f.read()

# --- Patch 1: Add hasEquipment ref after showCommandPalette ---
old1 = 'const showCommandPalette = ref(false);'
new1 = '''const showCommandPalette = ref(false);

const hasEquipment = ref(false);'''

if old1 not in content:
    print("ERROR: Could not find showCommandPalette ref")
    sys.exit(1)
if 'hasEquipment' in content:
    print("Already patched (hasEquipment found), skipping patch 1")
else:
    content = content.replace(old1, new1)
    print("Patch 1: Added hasEquipment ref")

# --- Patch 2: Add checkEquipment function before setUpOnboarding ---
old2 = 'function setUpOnboarding() {'
new2 = '''// Check if portal user has equipment (for conditional sidebar tab)
async function checkEquipment() {
  if (!isCustomerPortal.value) return;
  try {
    const result = await call("helpdesk.api.equipment.has_equipment");
    hasEquipment.value = !!result;
  } catch (e) {
    hasEquipment.value = false;
  }
}

function setUpOnboarding() {'''

if 'checkEquipment' in content:
    print("Already patched (checkEquipment found), skipping patch 2")
else:
    content = content.replace(old2, new2)
    print("Patch 2: Added checkEquipment function")

# --- Patch 3: Call checkEquipment() in onMounted ---
old3 = '''  setUpOnboarding();
  if (isCustomerPortal.value) return;'''
new3 = '''  setUpOnboarding();
  checkEquipment();
  if (isCustomerPortal.value) return;'''

if 'checkEquipment();' in content:
    print("Already patched (checkEquipment call found), skipping patch 3")
else:
    content = content.replace(old3, new3)
    print("Patch 3: Added checkEquipment() call in onMounted")

# --- Patch 4: Filter requiresEquipment items in allViews ---
old4 = '''  if (!isCallingEnabled.value) {
    items = items.filter((item) => item.label !== __("Call Logs"));
  }'''
new4 = '''  if (!isCallingEnabled.value) {
    items = items.filter((item) => item.label !== __("Call Logs"));
  }

  // Hide "Spare Part" tab for portal users without equipment
  if (isCustomerPortal.value) {
    items = items.filter((item) => !item.requiresEquipment || hasEquipment.value);
  }'''

if 'requiresEquipment' in content:
    print("Already patched (requiresEquipment filter found), skipping patch 4")
else:
    content = content.replace(old4, new4)
    print("Patch 4: Added requiresEquipment filter in allViews")

with open(SIDEBAR_PATH, "w") as f:
    f.write(content)

print("Sidebar.vue patched successfully!")
