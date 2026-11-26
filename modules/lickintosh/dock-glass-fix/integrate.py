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
        }''',1);s=s.replace('    property bool fast: false','    property bool fast: false\n    property bool workspaceTextureTransition:false\n    Timer{id:workspaceTextureRelease;interval:900;onTriggered:root.workspaceTextureTransition=false}',1)
s=s.replace('root.transitionEpoch++','{root.workspaceTextureTransition=true;workspaceTextureRelease.restart();root.transitionEpoch++}',1)
p.write_text(s)
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

# Workspace screencopy can return a transitional black frame even while the
# compositor still reports valid rendered geometry. Keep the last complete
# per-window texture during that interval; continue moving/clipping it using
# frame-synchronized geometry. Resume the existing stream when settled.
p=root/'components/glass/GlassWindows.qml';s=p.read_text()
s=s.replace('property bool capturing:true','property bool capturing:true\n    readonly property bool workspaceTextureHold:root.capturing && GlassTracker.workspaceTextureTransition && root.preciseGeometry',1)
s=s.replace('if(root.capturing && view.windowSource && !view.sourceClosed && !view.dying)view.captureFrame()', 'if(root.capturing && !root.workspaceTextureHold && view.windowSource && !view.sourceClosed && !view.dying)view.captureFrame()')
s=s.replace('live: RenderingState.glassFps===0 && root.capturing && gate.wanted', 'live: RenderingState.glassFps===0 && root.capturing && !(root.workspaceTextureHold && view.hasContent) && gate.wanted',1)
s=s.replace('onStopped: { if (gate.wanted && !dying && !sourceClosed) view.restart() }','onStopped: { if (gate.wanted && !dying && !sourceClosed && !root.workspaceTextureHold) view.restart() }',1)
s=s.replace('    property int pending: 0', """    Connections {
        target:GlassTracker
        function onWorkspaceTextureTransitionChanged(){
            if(!GlassTracker.workspaceTextureTransition && root.capturing){
                for(let i=0;i<windowsRepeater.count;i++){
                    const item=windowsRepeater.itemAt(i)
                    if(item && item.shown && !item.sourceClosed)item.captureFrame()
                }
            }
        }
    }
    property int pending: 0""",1)
p.write_text(s)
