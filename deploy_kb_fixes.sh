#!/bin/bash
set -e

echo "================================================"
echo "  KB Bug Fixes Deployment"
echo "  1. Sub-category hierarchy labels"
echo "  2. Trash filter (hide Trash from main list)"
echo "  3. Safe category deletion"
echo "================================================"

cd /workspace

# ── 1. Copy patch scripts into container ──
echo ""
echo "[1/5] Copying patch scripts..."
cp patch_doc_hierarchy.py /home/frappe/frappe-bench/
cp patch_kb_safe_delete.py /home/frappe/frappe-bench/
cp patch_kb_agent_vue.py /home/frappe/frappe-bench/

# ── 2. Run backend patches ──
echo ""
echo "[2/5] Patching doc.py (hierarchy labels)..."
cd /home/frappe/frappe-bench
python patch_doc_hierarchy.py

echo ""
echo "[3/5] Patching kb_custom.py (safe delete)..."
python patch_kb_safe_delete.py

# ── 3. Run frontend patch ──
echo ""
echo "[4/5] Patching KnowledgeBaseAgent.vue (filters, safe delete, statusMap)..."
python patch_kb_agent_vue.py

# ── 4. Build frontend ──
echo ""
echo "[5/5] Building frontend..."
cd /home/frappe/frappe-bench
bench build --app helpdesk 2>&1 | tail -5

# Clean up patch scripts
rm -f patch_doc_hierarchy.py patch_kb_safe_delete.py patch_kb_agent_vue.py

echo ""
echo "================================================"
echo "  Deployment complete!"
echo "================================================"
