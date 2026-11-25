from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
(root/'services/MenuCoordinator.qml').write_text((here/'MenuCoordinator.qml').read_text());p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton MenuCoordinator MenuCoordinator.qml\n')
p=root/'shell.qml';s=p.read_text().replace('onActionRequested:action=>{','onActionRequested:action=>{\n            MenuCoordinator.close()');a=s.index('    ScreenEdges{');s=s[:a]+'''    Connections{
        target:MenuCoordinator
        function onOpening(){
            appRoot.ccOpened=false;appRoot.notifCenterOpened=false;appRoot.appleMenuOpened=false
            appRoot.wifiOpened=false;appRoot.bluetoothOpened=false;appRoot.batteryOpened=false
            appRoot.volumeOpened=false;appRoot.spotlightOpened=false;appRoot.aiOpened=false;NotchState.close()
        }
    }
    onAnySubmenuOpenedChanged:if(appRoot.anySubmenuOpened)MenuCoordinator.close()
'''+s[a:];p.write_text(s)
p=root/'ui/topbar/menubar/globalmenu/GlobalMenuBar.qml';s=p.read_text().replace('    property int openIndex: -1','''    property int openIndex: -1
    function closeMenus(){root.openIndex=-1}
    onOpenIndexChanged:if(openIndex===-1)MenuCoordinator.release(root)
    Component.onDestruction:MenuCoordinator.release(root)''').replace('    function openMenu(index, x, items) {','    function openMenu(index, x, items) {\n        MenuCoordinator.claim(root)').replace('    function openOverflow(x) {','    function openOverflow(x) {\n        MenuCoordinator.claim(root)');p.write_text(s)
p=root/'ui/topbar/menubar/globalmenu/PopupMenu.qml';s=p.read_text().replace('        active: presence.present','        active: true',1).replace('                id: panel\n','                id: panel\n                visible:presence.present\n',1).replace('width:panel.width; height:Math.max(0,panel.height-32)','width:root.opened ? panel.width:0; height:root.opened ? Math.max(0,panel.height-32):0').replace('duration: ShellMotion.fade()','duration: Math.min(90,ShellMotion.fade())')
s=s.replace('                GlassBackdrop { element: "menus" }','                GlassBackdrop {id:menuBackdrop; element: "menus";gateEnabled:false}')
# Keep glass registered while painting a stable, themed surface until the first
# captured frame is ready. Menus accept input immediately without wallpaper flash.
s=s.replace('                    ColumnLayout {\n                        id: itemsColumn','''                    Rectangle{anchors.fill:parent;radius:parent.radius;color:Theme.isLight ? '#e9e9ed':'#242428';visible:!menuBackdrop.captureSettled}
                    ColumnLayout {
                        z:1
                        id: itemsColumn''',1);p.write_text(s)
p=root/'components/glass/GlassWindows.qml';s=p.read_text();a=s.index('    function workspaceVisible(');z=s.index('    function windowLayer(',a)
s=s[:a]+'''    function workspaceVisible(ipc, workspace) {
        if(!ipc || !root.monitorObject)return false
        if(ipc.pinned===true)return true
        const id=workspace?.id ?? ipc.workspace?.id
        // QObject workspace state changes before the last IPC geometry snapshot.
        // Read both live monitor state and the snapshot used for positioning.
        for(const monitor of GlassTracker.monitorSnapshots){
            if(monitor.id!==ipc.monitor && monitor.id!==root.monitorObject.id)continue
            const live=Hyprland.monitors.values.find(item=>item.name===monitor.name)
            const regular=live?.activeWorkspace?.id ?? monitor.activeWorkspace?.id
            const special=monitor.specialWorkspace
            const target=ipc.workspace
            const specialName=special?.address || special?.name
            if((id!==undefined && id===regular)
                || (special?.id && id===special.id)
                || (specialName && specialName===(target?.address || target?.name)))return true
        }
        return false
    }

'''+s[z:]
# Metadata can be temporarily absent on a newly mapped client. The foreign
# toplevel's current workspace provides visibility until the snapshot catches up.
s=s.replace('root.workspaceVisible(c,null)','root.workspaceVisible(c,null)')
p.write_text(s)
# Refresh workspace/geometry inventory after unlocking, before revealing glass.
p=root/'components/glass/GlassTracker.qml';s=p.read_text().replace('''        if (!sessionLocked)
            unlockSettle.restart()''','''        if (!sessionLocked){
            root.clientsUpdated=0;root.captureSnapshot();root.refreshMonitorSnapshot();root.refreshWindows()
            unlockSettle.restart()
        }''');p.write_text(s)
