from pathlib import Path
import sys
r=Path(sys.argv[1]);here=Path(__file__).parent

def edit(name,old,new,count=1):
 p=r/name;s=p.read_text()
 if s.count(old)!=count:raise ValueError(f'Finder menu anchor {name}: {old[:60]} ({s.count(old)})')
 p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new))
base='ui/topbar/menubar/globalmenu/'
(r/base/'data/FinderMenus.qml').write_text((here/'FinderMenus.qml').read_text())
p=r/base/'data/qmldir';p.write_text(p.read_text()+'\nsingleton FinderMenus FinderMenus.qml\n')
edit('services/DesktopFiles.qml','import QtQuick\n','import QtQuick\nimport Quickshell.Hyprland\n')
edit('services/DesktopFiles.qml','    property var selection: []','''    property bool desktopFocused:false
    Connections{target:Hyprland;function onActiveToplevelChanged(){root.desktopFocused=!Hyprland.activeToplevel}function onRawEvent(event){if((event.name==="activewindow" || event.name==="activewindowv2") && String(event.data || "").replace(/,/g,"").trim())root.desktopFocused=false}}
    property var selection: []''')
edit('ui/desktop/DesktopLayer.qml','stage.forceActiveFocus()','{DesktopFiles.desktopFocused=true;stage.forceActiveFocus()}',2)
edit('ui/desktop/DesktopMenuLayer.qml','onPressed:mouse=>menu.openAt(mouse.x,mouse.y,DesktopFiles.desktopMenu())','onPressed:mouse=>{DesktopFiles.desktopFocused=true;menu.openAt(mouse.x,mouse.y,DesktopFiles.desktopMenu())}')
edit(base+'GlobalMenuService.qml','import QtQuick\n','import QtQuick\nimport qs.services\n')
edit(base+'GlobalMenuService.qml','readonly property bool hasWindow: root.currentToplevel !== null','''readonly property bool desktopMode:DesktopFiles.desktopFocused || root.currentToplevel===null
    readonly property bool hasWindow: true''')
edit(base+'GlobalMenuService.qml','root.classify(root.appId)','root.desktopMode ? "filemanager":root.classify(root.appId)')
edit(base+'GlobalMenuService.qml','case "filemanager": return FileManager.menus','case "filemanager": return FinderMenus.menus')
edit(base+'PopupMenu.qml','import QtQuick\n','import QtQuick\nimport qs.ui.topbar.menubar.globalmenu.data\n')
edit(base+'PopupMenu.qml','    function trigger(modelData) {','''    function trigger(modelData) {
        if(modelData.finderAction){root.subIndex=-1;root.closeRequested();FinderMenus.execute(modelData.finderAction);return}
        if(modelData.command){root.subIndex=-1;root.closeRequested();Quickshell.execDetached(modelData.command);return}
        if(GlobalMenuService.desktopMode && modelData.desktopAction){root.subIndex=-1;root.closeRequested();FinderMenus.execute(modelData.desktopAction);return}''')
name='ui/topbar/menubar/activewindows/ActiveWindow.qml'
edit(name,'import QtQuick\n','import QtQuick\nimport qs.ui.topbar.menubar.globalmenu\nimport qs.ui.topbar.menubar.globalmenu.data\n')
edit(name,'property string appName: formatName(currentAppId, currentTitle)','''property string appName:GlobalMenuService.desktopMode ? "Finder":formatName(currentAppId, currentTitle)
    property bool appMenuOpen:false
    function closeMenus(){appMenuOpen=false}
    onAppMenuOpenChanged:if(!appMenuOpen)MenuCoordinator.release(activeWindowText)
    Connections{target:GlobalMenuService;function onAppIdChanged(){activeWindowText.appMenuOpen=false}}
    MouseArea{
        anchors.fill:parent;enabled:GlobalMenuService.category==='filemanager'
        cursorShape:Qt.PointingHandCursor
        onClicked:{if(activeWindowText.appMenuOpen)activeWindowText.appMenuOpen=false;else{MenuCoordinator.claim(activeWindowText);const p=activeWindowText.mapToItem(null,0,activeWindowText.height);appMenu.xPos=p.x;appMenu.yPos=36;appMenu.items=FinderMenus.applicationMenu;activeWindowText.appMenuOpen=true}}
    }
    PopupMenu{id:appMenu;opened:activeWindowText.appMenuOpen;onCloseRequested:activeWindowText.appMenuOpen=false}''')
# Hyprland can retain the last toplevel after entering an empty workspace.
# The visible workspaces, not that stale pointer, decide desktop menu ownership.
p=r/base/'DesktopFocus.js';p.write_text((here/'DesktopFocus.js').read_text())
p=r/base/'GlobalMenuService.qml';s=p.read_text().replace('import qs.services','import qs.services\nimport qs.components.glass\nimport "DesktopFocus.js" as DesktopFocus',1)
s=s.replace('    readonly property bool desktopMode:DesktopFiles.desktopFocused || root.currentToplevel===null','''    property int workspaceHint:0
    readonly property var focusedMonitor:GlassTracker.monitorSnapshots.find(m=>m.name===Hyprland.focusedMonitor?.name) || null
    readonly property bool currentWindowVisible:DesktopFocus.windowVisible(root.currentToplevel ? root.currentToplevel.lastIpcObject || {}:null,root.focusedMonitor,root.workspaceHint)
    onCurrentWindowVisibleChanged:DesktopFiles.desktopFocused=!currentWindowVisible
    readonly property bool desktopMode:DesktopFiles.desktopFocused || !root.currentWindowVisible''',1)
s=s.replace('        function onRawEvent(event) {','''        function onRawEvent(event) {
            if(event.name==='workspacev2'){root.workspaceHint=parseInt(String(event.data).split(',')[0]) || 0;GlassTracker.refreshMonitorSnapshot()}
            else if(event.name==='focusedmon'){root.workspaceHint=0;GlassTracker.refreshMonitorSnapshot()}
            else if(event.name==='activespecial' || event.name==='activespecialv2'){root.workspaceHint=0;GlassTracker.refreshMonitorSnapshot();Hyprland.refreshToplevels()}''',1)
s=s.replace('    Component.onCompleted: Hyprland.refreshToplevels()','''    Component.onCompleted:{GlassTracker.inventoryUsers++;GlassTracker.refreshMonitorSnapshot();Hyprland.refreshToplevels()}
    Component.onDestruction:GlassTracker.inventoryUsers=Math.max(0,GlassTracker.inventoryUsers-1)''',1);p.write_text(s)
p=r/'ui/desktop/DesktopLayer.qml';s=p.read_text().replace('            id: stage','            id: stage\n            Connections{target:DesktopFiles;function onDesktopFocusedChanged(){if(DesktopFiles.desktopFocused)stage.forceActiveFocus()}}',1);p.write_text(s)
