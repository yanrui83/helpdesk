#!/usr/bin/env python3
"""Fix Sidebar.vue to use optimistic hasEquipment (start true, only hide when API says false)."""

import sys

SIDEBAR_PATH = "/home/frappe/frappe-bench/apps/helpdesk/desk/src/components/layouts/Sidebar.vue"

with open(SIDEBAR_PATH, "r") as f:
    content = f.read()

changed = False

# Fix 1: Change ref(false) to ref(true) for hasEquipment (optimistic default)
old1 = 'const hasEquipment = ref(false);'
new1 = 'const hasEquipment = ref(true);'
if old1 in content:
    content = content.replace(old1, new1)
    print("Fix 1: hasEquipment changed to ref(true) (optimistic)")
    changed = True
elif 'const hasEquipment = ref(true);' in content:
    print("Fix 1: Already uses ref(true), skipping")
else:
    print("ERROR: Could not find hasEquipment ref declaration")
    sys.exit(1)

# Fix 2: Don't hide tab on API error (keep true)
old2 = '''async function checkEquipment() {
  if (!isCustomerPortal.value) return;
  try {
    const result = await call("helpdesk.api.equipment.has_equipment");
    hasEquipment.value = !!result;
  } catch (e) {
    hasEquipment.value = false;
  }
}'''
new2 = '''async function checkEquipment() {
  if (!isCustomerPortal.value) return;
  try {
    const result = await call("helpdesk.api.equipment.has_equipment");
    // Only hide tab if API explicitly returns false/falsy
    if (!result && result !== undefined && result !== null) {
      hasEquipment.value = false;
    } else {
      hasEquipment.value = !!result;
    }
  } catch (e) {
    // Keep tab visible on API error (safe default)
  }
}'''
if old2 in content:
    content = content.replace(old2, new2)
    print("Fix 2: checkEquipment updated to keep tab on error")
    changed = True
elif 'Keep tab visible on API error' in content:
    print("Fix 2: Already updated, skipping")
else:
    print("WARNING: checkEquipment function not found as expected, skipping fix 2")

if changed:
    with open(SIDEBAR_PATH, "w") as f:
        f.write(content)
    print("Sidebar.vue updated successfully!")
else:
    print("No changes needed.")
