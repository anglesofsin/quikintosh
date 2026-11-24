"""Reveal glass only after a fresh window inventory and its first captured frames."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Glass readiness anchor {name}: {old[:65]} ({s.count(old)})')
 p.write_text(s.replace(old,new,1))
tracker='components/glass/GlassTracker.qml'
edit(tracker,'    property var monitorSnapshots: []','''    property var monitorSnapshots: []
    property var clientsSnapshot: []
    property int snapshotSerial:0
    property bool snapshotAgain:false
    function captureSnapshot() {
        if(clientsQuery.running) {snapshotAgain=true;return snapshotSerial+2}
        clientsQuery.running=true
        return snapshotSerial+1
    }
    Process {
        id:clientsQuery
        command:["hyprctl","clients","-j"]
        stdout:StdioCollector {
            onStreamFinished:{try {root.clientsSnapshot=JSON.parse(text)} catch(_){};root.snapshotSerial++}
        }
        onExited:if(root.snapshotAgain){root.snapshotAgain=false;Qt.callLater(function(){clientsQuery.running=true})}
    }''')
windows='components/glass/GlassWindows.qml'
edit(windows,'    property int pending: 0','''    property int requiredSnapshot:2147483647
    function addressOf(value) {return String(value || "").replace(/^0x/i,"").toLowerCase()}
    function expectedPending() {
        var clients=GlassTracker.clientsSnapshot
        for(var c of clients) {
            if(c.hidden || c.mapped === false || !root.workspaceVisible(c,null) || root.opacityFor(c["class"])<=0 || !c.at || !c.size) continue
            const x=c.at[0]-root.monitorX,y=c.at[1]-root.monitorY,r=root.visibleRegion
            if(x>=r.x+r.width || x+c.size[0]<=r.x || y>=r.y+r.height || y+c.size[1]<=r.y) continue
            var ready=false
            for(var i=0;i<windowsRepeater.count;i++) {
                var view=windowsRepeater.itemAt(i)
                if(view && view.ipc && addressOf(view.ipc.address)===addressOf(c.address) && view.hasContent && view.opacity>0.99) {ready=true;break}
            }
            if(!ready)return true
        }
        return false
    }
    property int pending: 0''')
# The snapshot includes windows that the asynchronous foreign-toplevel model has
# not attached yet. An initially empty model must not be mistaken for desktop-only.
edit(windows,'if (!root.latched && root.monitorObject !== null && root.graceDone && (root.pending === 0 || root.timedOut))','if (!root.latched && root.monitorObject !== null && root.visibleRegion.width>0 && root.visibleRegion.height>0 && GlassTracker.snapshotSerial>=root.requiredSnapshot && root.graceDone && ((!root.expectedPending() && root.pending === 0) || root.timedOut))')
edit(windows,'    Component.onCompleted: GlassTracker.captureUsers++','    Component.onCompleted: {GlassTracker.captureUsers++;root.requiredSnapshot=GlassTracker.captureSnapshot()}')
edit(windows,'        function onTransitionEpochChanged() {','        function onSnapshotSerialChanged(){root.recount()}\n        function onTransitionEpochChanged() {\n            root.requiredSnapshot=GlassTracker.captureSnapshot()')
p=root/windows;s=p.read_text().replace('        if (!ipc || !monitor) return false','''        if (!ipc || !monitor) return false
        if(ipc.monitor !== monitor.id) {
            var owner=GlassTracker.monitorSnapshots.find(m=>m.id===ipc.monitor)
            var workspaceId=ipc.workspace ? ipc.workspace.id : null
            if(owner && ((owner.activeWorkspace && owner.activeWorkspace.id===workspaceId)
                || (owner.specialWorkspace && owner.specialWorkspace.id!==0 && owner.specialWorkspace.id===workspaceId))) return true
        }''').replace('                && ipc.monitor === root.monitorObject.id\n','').replace('duration: ShellMotion.fade(0.5)','duration: 0')
p.write_text(s)
backdrop='components/glass/GlassBackdrop.qml'
edit(backdrop,'        if (glassReady)\n            revealed = true','        // The first visible frame must go through the same capture gate.')
edit(backdrop,'        onTriggered: root.revealed = true','        onTriggered: {if(root.captureSettled)root.revealed=true}')
edit(windows,'            onPendingChanged: root.recount()','            onPendingChanged: root.recount()\n            onOpacityChanged: root.recount()')
edit(windows,'    onMonitorObjectChanged: root.recount()','    onMonitorObjectChanged: root.recount()\n    onVisibleRegionChanged: root.recount()')
