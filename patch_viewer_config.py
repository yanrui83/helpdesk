#!/usr/bin/env python3
"""
Patch the 3D viewer to:
1. Send config back to parent via postMessage when agent clicks Save Config
2. Add Import JSON button to the editor footer
"""
import sys

VIEWER_PATH = "/home/frappe/frappe-bench/apps/helpdesk/helpdesk/public/3d-viewer/index.html"

with open(VIEWER_PATH, "r") as f:
    content = f.read()

changed = False

# ── Patch 1: Make editorSave() notify parent via postMessage ──────────────────
OLD_SAVE = "function editorSave(){saveConfig();buildTree();buildHotspotElements();if(editorCompId&&hotspotEls[editorCompId])hotspotEls[editorCompId].classList.add('editor-sel');toast('Configuration saved!')}"
NEW_SAVE = (
    "function editorSave(){"
    "saveConfig();"
    "buildTree();"
    "buildHotspotElements();"
    "if(editorCompId&&hotspotEls[editorCompId])hotspotEls[editorCompId].classList.add('editor-sel');"
    # Notify parent iframe so EquipmentDetail.vue can persist the config
    "if(window.parent&&window.parent!==window){window.parent.postMessage({type:'eq-config-saved',config:JSON.stringify(CONFIG)},'*');}"
    "toast('Configuration saved to server!');}"
)

if OLD_SAVE in content:
    content = content.replace(OLD_SAVE, NEW_SAVE)
    print("Patch 1: editorSave now sends postMessage to parent")
    changed = True
elif "eq-config-saved" in content:
    print("Patch 1: Already patched, skipping")
else:
    print("ERROR: Could not find editorSave function to patch")
    sys.exit(1)

# ── Patch 2: Add Import JSON button + function ────────────────────────────────
OLD_FOOTER = (
    "h+='<div class=\"ed-footer\">"
    "<button class=\"ed-btn green\" onclick=\"editorSave()\" style=\"flex:1\">Save Config</button>"
    "<button class=\"ed-btn secondary\" onclick=\"editorExport()\">Export JSON</button>"
    "</div>';"
)
NEW_FOOTER = (
    "h+='<div class=\"ed-footer\">"
    "<button class=\"ed-btn green\" onclick=\"editorSave()\" style=\"flex:1\">Save Config</button>"
    "<button class=\"ed-btn secondary\" onclick=\"editorExport()\">Export JSON</button>"
    "<button class=\"ed-btn secondary\" onclick=\"editorImportClick()\">Import JSON</button>"
    "</div>';"
    # Hidden file input for import
    "h+='<input type=\"file\" id=\"eq-import-input\" accept=\".json\" style=\"display:none\">';"
)

if OLD_FOOTER in content:
    content = content.replace(OLD_FOOTER, NEW_FOOTER)
    print("Patch 2: Import JSON button added to editor footer")
    changed = True
elif "editorImportClick" in content:
    print("Patch 2: Already patched, skipping")
else:
    print("ERROR: Could not find editor footer HTML to patch")
    sys.exit(1)

# ── Patch 3: Add editorImport functions after editorExport ───────────────────
OLD_AFTER_EXPORT = (
    "function editorExport(){"
    "var blob=new Blob([JSON.stringify(CONFIG,null,2)],{type:'application/json'});"
    "var a=document.createElement('a');"
    "a.href=URL.createObjectURL(blob);"
    "a.download=(CONFIG.projectName||'config')+'.json';"
    "a.click();"
    "URL.revokeObjectURL(a.href);"
    "toast('Config exported')}"
)
NEW_AFTER_EXPORT = (
    "function editorExport(){"
    "var blob=new Blob([JSON.stringify(CONFIG,null,2)],{type:'application/json'});"
    "var a=document.createElement('a');"
    "a.href=URL.createObjectURL(blob);"
    "a.download=(CONFIG.projectName||'config')+'.json';"
    "a.click();"
    "URL.revokeObjectURL(a.href);"
    "toast('Config exported')}"
    # Attach event listener once for the file input
    "function editorImportClick(){"
    "var inp=document.getElementById('eq-import-input');"
    "if(!inp)return;"
    # Reset so same file can be re-imported
    "inp.value='';"
    "inp.onchange=function(e){"
    "var f=e.target.files[0];if(!f)return;"
    "var r=new FileReader();"
    "r.onload=function(ev){"
    "try{"
    "var parsed=JSON.parse(ev.target.result);"
    "if(!parsed||!parsed.components){toast('Invalid config file');return;}"
    "CONFIG=parsed;"
    "saveConfig();"
    "buildHotspotElements();"
    "buildTree();"
    "renderEditorPanel();"
    "if(window.parent&&window.parent!==window){window.parent.postMessage({type:'eq-config-saved',config:JSON.stringify(CONFIG)},'*');}"
    "toast('Config imported and saved!');"
    "}catch(err){toast('Error reading file: '+err.message);}"
    "};"
    "r.readAsText(f);"
    "};"
    "inp.click();}"
)

if OLD_AFTER_EXPORT in content:
    content = content.replace(OLD_AFTER_EXPORT, NEW_AFTER_EXPORT)
    print("Patch 3: editorImportClick function added")
    changed = True
elif "editorImportClick" in content and "FileReader" in content:
    print("Patch 3: Already has import function, skipping")
else:
    print("ERROR: Could not find editorExport function for anchoring import function")
    sys.exit(1)

if changed:
    with open(VIEWER_PATH, "w") as f:
        f.write(content)
    print("3D viewer patched successfully!")
else:
    print("No changes needed.")
