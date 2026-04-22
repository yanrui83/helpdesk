#!/bin/bash
BENCH=/home/frappe/frappe-bench
APP=$BENCH/apps/helpdesk
VIEWER_DIR=$APP/helpdesk/public/3d-viewer

echo "=== Deploying 3D Viewer static assets ==="

mkdir -p "$VIEWER_DIR"

# Copy viewer HTML
cp /workspace/3D_Sparepart.html "$VIEWER_DIR/index.html"
echo "  Viewer HTML copied"

# Copy GLB model files
cp /workspace/2311.glb "$VIEWER_DIR/2311.glb"
echo "  2311.glb copied"

if [ -f /workspace/2311_full.glb ]; then
    cp /workspace/2311_full.glb "$VIEWER_DIR/2311_full.glb"
    echo "  2311_full.glb copied"
fi

# Copy setup/config page
if [ -f /workspace/3D_Setup.html ]; then
    cp /workspace/3D_Setup.html "$VIEWER_DIR/setup.html"
    echo "  Setup page copied"
fi

# Re-link public assets so bench serves the new files
cd "$BENCH"
bench setup assets
bench --site helpdesk.localhost clear-cache

echo "=== 3D Viewer assets deployed ==="
echo "Access at: /assets/helpdesk/3d-viewer/index.html"
echo "GLB model: /assets/helpdesk/3d-viewer/2311.glb"
