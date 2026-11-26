"""Flush final workspace visibility and invalidate the entire retained backdrop."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
p=root/'components/glass/GlassTracker.qml';s=p.read_text();old='        onTriggered: root.fast = false';assert old in s
s=s.replace(old,'''        onTriggered: {
            root.fast = false
            // The final animation frame can be the last damaged compositor
            // frame. Refresh settled visibility even if no more frames arrive.
            root.refreshMonitorSnapshot()
            if(root.captureUsers>0 || root.inventoryUsers>0)root.captureSnapshot()
            if(root.captureUsers>0){RenderingState.updateGeometry();Hyprland.refreshToplevels()}
        }''',1);p.write_text(s)
p=root/'components/glass/GlassWindows.qml';s=p.read_text();old='&& (root.preciseGeometry ? viewport.rendered!==null && viewport.rendered.visible:root.workspaceVisible(ipc, modelData.workspace))';assert old in s
s=s.replace(old,'''&& (root.preciseGeometry ? viewport.rendered!==null && viewport.rendered.visible:root.workspaceVisible(ipc, modelData.workspace))
                // Retained render telemetry may outlive its workspace animation.
                // Once settled, the live workspace is authoritative.
                && (GlassTracker.fast || root.workspaceVisible(ipc, modelData.workspace))''',1);p.write_text(s)
p=root/'components/glass/LiquidGlassBackdrop.qml';s=p.read_text();needle='    Timer {\n        id: regionTimer';assert needle in s
s=s.replace(needle,'''    // Clear the complete offscreen chain after a workspace settles. Partial
    // source damage must not retain a strip of an outgoing window.
    Connections {
        target: GlassTracker
        function onFastChanged() { if(!GlassTracker.fast && root.ready)settledUpdate.restart() }
        function onSnapshotSerialChanged() { if(!GlassTracker.fast && root.ready)settledUpdate.restart() }
    }
    Timer { id:settledUpdate;interval:0;onTriggered:{fb.scheduleUpdate();blurIntermediate.scheduleUpdate();blurFinal.scheduleUpdate()} }
''' +needle,1);p.write_text(s)
