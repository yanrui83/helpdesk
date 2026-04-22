"""
Patch EquipmentDetail.vue to:
1. Add cache-busting version ?_v=4 to viewer URL (fixes Import button not showing)
2. Use separate loadedConfig ref to prevent iframe reload on save
3. Set loadedConfig when equipment data loads
4. Update loadedConfig on toggleEditor (so fresh config loads when switching modes)
"""

path = '/home/frappe/frappe-bench/apps/helpdesk/desk/src/pages/equipment/EquipmentDetail.vue'
with open(path, 'r') as f:
    content = f.read()

patches = [
    # 1. Add loadedConfig ref and VIEWER_VER constant after existing refs
    (
        'const configSaving = ref(false);\nconst configSaved = ref(false);\n\nconst isAgent',
        'const configSaving = ref(false);\nconst configSaved = ref(false);\nconst loadedConfig = ref(""); // Separate ref — only changes on load or editor toggle\nconst VIEWER_VER = "4"; // Bump to bust browser cache when viewer HTML changes\n\nconst isAgent'
    ),
    # 2. Fix viewerUrl: use loadedConfig + add _v param
    (
        '  if (isEditor.value) params.set("mode", "editor");\n  if (equipmentData.value.config) {\n    params.set("config", encodeURIComponent(equipmentData.value.config));\n  }\n  return `${base}?${params.toString()}`;',
        '  if (isEditor.value) params.set("mode", "editor");\n  if (loadedConfig.value) {\n    params.set("config", encodeURIComponent(loadedConfig.value));\n  }\n  params.set("_v", VIEWER_VER);\n  return `${base}?${params.toString()}`;'
    ),
    # 3. Fix toggleEditor: snapshot latest config before switching mode
    (
        'function toggleEditor() {\n  isEditor.value = !isEditor.value;\n}',
        'function toggleEditor() {\n  // Snapshot latest persisted config so iframe reloads with fresh data\n  loadedConfig.value = equipmentData.value.config || "";\n  isEditor.value = !isEditor.value;\n}'
    ),
    # 4. Fix handleViewerMessage: keep equipmentData update but don't touch loadedConfig
    (
        '  // Update local data so reloads use the latest config\n  equipmentData.value.config = newConfig;\n  // Persist to server',
        '  // Update equipmentData (used on next toggle) but NOT loadedConfig\n  // loadedConfig staying stable prevents the iframe from reloading mid-editing\n  equipmentData.value.config = newConfig;\n  // Persist to server'
    ),
    # 5. Set loadedConfig when equipment data loads
    (
        '  onSuccess(data) {\n    equipmentData.value = data;\n    loading.value = false;\n  },',
        '  onSuccess(data) {\n    equipmentData.value = data;\n    loadedConfig.value = data.config || ""; // Prime the iframe URL with fresh config\n    loading.value = false;\n  },'
    ),
]

applied = 0
for old, new in patches:
    if old in content:
        content = content.replace(old, new, 1)
        applied += 1
    else:
        print(f"MISS: could not find:\n{old[:80]}")

with open(path, 'w') as f:
    f.write(content)

print(f"Applied {applied}/{len(patches)} patches to EquipmentDetail.vue")

# Verify
checks = ['loadedConfig', 'VIEWER_VER = "4"', '_v", VIEWER_VER', 'Prime the iframe']
for c in checks:
    status = 'OK' if c in content else 'MISSING'
    print(f"  {status}: {c}")
