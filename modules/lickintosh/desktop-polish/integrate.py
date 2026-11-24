"""Desktop input, overlay menus and stable widget material/placement."""
from pathlib import Path
import sys
root=Path(sys.argv[1]); here=Path(__file__).parent

def write(name,text):
 p=root/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(text)
def edit(name,old,new,count=1):
 s=(root/name).read_text()
 if s.count(old)!=count: raise ValueError(f'{name}: expected {count} anchors for {old[:70]!r}, found {s.count(old)}')
 write(name,s.replace(old,new))

# z only orders items inside a surface. Desktop is Bottom, Dock is Top:
# the menu needs its own Overlay surface, retaining its Item API for mapToItem.
name='ui/widgets/WidgetContextMenu.qml';s=(root/name).read_text()
s=s.replace('import QtQuick\n','import QtQuick\nimport Quickshell\nimport Quickshell.Wayland\nimport qs.components.glass\n',1)
s=s.replace('    function openAt(px, py, list) {','''    readonly property var host: QsWindow.window
    function openAt(px, py, list) {
        const point = root.host ? root.mapToItem(root.host.contentItem, px, py) : Qt.point(px,py)
        const a=root.host?.anchors, m=root.host?.margins
        const ox=a ? (a.left ? m.left : a.right ? overlay.screen.width-root.host.width-m.right : (overlay.screen.width-root.host.width)/2) : 0
        const oy=a ? (a.top ? m.top : a.bottom ? overlay.screen.height-root.host.height-m.bottom : (overlay.screen.height-root.host.height)/2) : 0
        px=point.x+ox;py=point.y+oy''')
s=s.replace('root.width - panel.width','overlay.screen.width - panel.width').replace('root.height - root.heightOf','overlay.screen.height - root.heightOf')
s=s.replace('    component MenuPanel: Rectangle {','    component MenuPanel: Item {')
s=s.replace('''        radius: 12
        color: Qt.rgba(0.16, 0.16, 0.18, 0.97)
        border.width: 1
        border.color: Qt.rgba(1, 1, 1, 0.12)''','''        BoxGlass {
            anchors.fill:parent;radius:12
            visible:WidgetState.desktopMenuMaterial==='glass'
            color:Theme.isLight ? '#b8f5f5f7':'#b8202025'
        }
        Rectangle {
            anchors.fill:parent;radius:12
            visible:WidgetState.desktopMenuMaterial!=='glass'
            color:WidgetState.desktopMenuMaterial==='transparent' ? 'transparent':(Theme.isLight ? '#f3f3f6':'#252529')
            border.width:1;border.color:Theme.isLight ? '#22000000':'#24ffffff'
        }''')
# Keep submenu geometry inside the overlay, including the second monitor.
s=s.replace('> root.width ?', '> overlay.width ?').replace('root.height - subPanel.height','overlay.height - subPanel.height')
s=s.replace('color: "#ffffff"','color: Theme.textPrimary').replace(': "#ffffff")',': Theme.textPrimary)')
start=s.index('    MouseArea {\n        anchors.fill: parent\n        acceptedButtons: Qt.AllButtons')
s=s[:start]+'''    PanelWindow {
        id:overlay
        screen:root.host?.screen || Quickshell.screens[0]
        visible:root.visible
        anchors {left:true;right:true;top:true;bottom:true}
        color:'transparent';exclusionMode:ExclusionMode.Ignore
        WlrLayershell.layer:WlrLayer.Overlay
        WlrLayershell.namespace:'quickintosh:desktop-menu'
        WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive
        GlassBackdrop{element:'menus';gateEnabled:false}
        Shortcut{sequence:'Escape';onActivated:root.close()}
'''+s[start:]
s=s[:-2]+'    }\n}\n'
write(name,s)

name='services/WidgetState.qml'
edit(name,'    property var galleryDrag:null','''    property var galleryDrag:null
    property alias desktopMenuMaterial:widgetsAdapter.desktopMenuMaterial
    property alias widgetMaterial:widgetsAdapter.widgetMaterial
    property alias allowCtrlFreePlacement:widgetsAdapter.allowCtrlFreePlacement
    property alias avoidDesktopIcons:widgetsAdapter.avoidDesktopIcons''')
edit(name,'            property string widgetStyle:"auto"','''            property string desktopMenuMaterial:"glass"
            property string widgetMaterial:"glass"
            property bool allowCtrlFreePlacement:true
            property bool avoidDesktopIcons:true
            property string widgetStyle:"auto"''')
edit(name,'        var wide = root.cell * 2 + root.gap','''        const extended={portrait:{w:153,h:320},banner:{w:487,h:153},wide:{w:487,h:320},tall:{w:320,h:487},square:{w:487,h:487}}
        if(extended[size])return extended[size]
        var wide = root.cell * 2 + root.gap''')
edit(name,'    function collides(list, skipId, x, y, w, h) {','''    function collides(list, skipId, x, y, w, h) {
        if(root.avoidDesktopIcons && typeof DesktopFiles!=="undefined") {
            const icons=DesktopFiles.layout || []
            for(const icon of icons){
                const ix=icon.x-root.desktopOffsetX, iy=icon.y-root.desktopOffsetY
                if(x<ix+icon.w && x+w>ix && y<iy+icon.h && y+h>iy)return true
            }
        }''')
edit(name,'    function moveWidget(id, x, y) {','    function moveWidget(id, x, y, free) {')
edit(name,'        var nx = Math.round(x / root.step) * root.step\n        var ny = Math.round(y / root.step) * root.step','''        free=!!free && root.allowCtrlFreePlacement
        var nx = free ? x : Math.round(x / root.step) * root.step
        var ny = free ? y : Math.round(y / root.step) * root.step''')
edit(name,'        if (root.collides(list, id, nx, ny, d.w, d.h)) {','        if (!free && root.collides(list, id, nx, ny, d.w, d.h)) {')
edit(name,'{ x: nx, y: ny })','{ x: nx, y: ny, freePosition:free })')

for name in ['ui/widgets/WidgetView.qml','ui/widgets/WidgetSnapshot.qml']:
 s=(root/name).read_text()
 s=s.replace('readonly property string style:', 'readonly property string requestedStyle:')
 anchor='    readonly property bool muted:'
 i=s.index(anchor)
 s=s[:i]+'''    readonly property string style:root.requestedStyle==='auto' ? 'color':root.requestedStyle
    readonly property string material:root.widgetData.material || (['glass','clear','transparent'].includes(root.style) ? (root.style==='transparent' ? 'transparent':'glass'):WidgetState.widgetMaterial)
'''+s[i:]
 s=s.replace('readonly property bool muted:','readonly property bool muted:root.widgetData.type!=="image" && root.style!=="color" && root.widgetData.dimWithDesktop===true && ')
 s=s.replace('visible: palette.glass','visible:root.material==="glass"').replace('visible: !palette.glass && root.style!=="transparent"','visible:root.material==="solid"')
 s=s.replace('visible:root.style!=="transparent"','visible:root.material!=="transparent"').replace('palette.glass ?','root.material==="glass" ?')
 # Dimming must never desaturate the captured desktop or user photos.
 s=s.replace('saturation: -1','saturation: 0').replace('saturation:-1','saturation:0')
 write(name,s)

name='ui/desktop/DesktopLayer.qml'
edit(name,'z: slot.dragging ? 100 : 0','z: slot.dragging ? 500 : 20')
# Separate pointer handlers use Qt's acceptedModifiers filtering, so Control
# is evaluated by Qt at grab time instead of reading nonexistent point fields.
edit(name,'WidgetState.moveWidget(slot.modelData.id, nx, ny)','WidgetState.moveWidget(slot.modelData.id, nx, ny, slot.freePlacement)')
edit(name,'                    property bool dragging: false','                    property bool dragging: false\n                    property bool freePlacement:false')
s=(root/name).read_text()
a=s.index('                    DragHandler {',s.index('id:liveWidget'))
b=s.index('\n                    MouseArea {',a)
handler=s[a:b]
normal=handler.replace('target: null','target: null\n                        acceptedModifiers:Qt.NoModifier').replace('slot.dragging = true','slot.freePlacement=false\n                                slot.dragging = true')
free=handler.replace('target: null','target: null\n                        acceptedModifiers:Qt.ControlModifier').replace('slot.dragging = true','slot.freePlacement=true\n                                slot.dragging = true')
s=s[:a]+normal+'\n'+free+s[b:]
# Widgets swallow clicks on their background while child controls still work.
a=s.index('                    WidgetView {\n                        id:liveWidget')
s=s[:a]+"                    MouseArea{anchors.fill:parent;z:-1;acceptedButtons:Qt.LeftButton}\n"+s[a:]
write(name,s)

# Gallery previously estimated a panel's global origin using screen height.
# This is incorrect with scale/overlays. mapToGlobal maps the grabbed pointer
# outside the panel too; subtract screen and desktop stage origins once.
name='ui/widgets/WidgetGallery.qml'
edit(name,'const gx=point.x,gy=win.screen.height-win.height+point.y','''const global=addMouse.mapToGlobal(event.x,event.y)
                const gx=global.x-win.screen.x,gy=global.y-win.screen.y''')
edit(name,'d.x-shape.w/2,d.y-shape.h/2,d.theme','d.x-shape.w/2-WidgetState.desktopOffsetX,d.y-shape.h/2-WidgetState.desktopOffsetY,d.theme')
# Explicitly retain the pointer grab across the compositor surface boundary.
edit(name,'hoverEnabled:true;preventStealing:true;cursorShape:Qt.PointingHandCursor','hoverEnabled:true;preventStealing:true;cursorShape:Qt.PointingHandCursor;drag.threshold:0')

# Image formats keep their own content and don't inherit a tinted icon filter.
name='ui/widgets/types/ImageWidget.qml'
s=(root/name).read_text().replace('radius:22','radius:root.widgetData?.shape===\'circle\' ? Math.min(width,height)/2:root.widgetData?.shape===\'rectangle\' ? 0:(root.widgetData?.cornerRadius ?? 22)')
s=s.replace('fillMode:Image.PreserveAspectCrop','fillMode:root.widgetData?.imageFit===\'fit\' ? Image.PreserveAspectFit:root.widgetData?.imageFit===\'stretch\' ? Image.Stretch:Image.PreserveAspectCrop')
s=s.replace('fillMode:AnimatedImage.PreserveAspectCrop','fillMode:root.widgetData?.imageFit===\'fit\' ? Image.PreserveAspectFit:root.widgetData?.imageFit===\'stretch\' ? Image.Stretch:Image.PreserveAspectCrop')
write(name,s)
name='services/WidgetRegistry.qml';s=(root/name).read_text()
# Match registry record regardless of its formatting.
import re
s,n=re.subn(r"(type\s*:\s*['\"]image['\"][^\n]*?sizes\s*:\s*)\[[^\]]*\]",r"\1['s','m','l','portrait','banner','wide','tall','square']",s)
if n!=1:raise ValueError('image size registry anchor')
write(name,s)

for src,dst in [('DesktopMenuLayer.qml','ui/desktop/DesktopMenuLayer.qml')]:write(dst,(here/src).read_text())
write('ui/desktop/qmldir',(root/'ui/desktop/qmldir').read_text()+'\nDesktopMenuLayer DesktopMenuLayer.qml\n')
name='shell.qml'
s=(root/name).read_text()
# Keep a lightweight context surface on secondary displays and during Game Mode.
pos=s.index('    FullscreenPrivacy') if '    FullscreenPrivacy' in s else s.rfind('}')
s=s[:pos]+'''    LazyLoader{active:appRoot.interfaceShown;DesktopMenuLayer{}}
'''+s[pos:];write(name,s)

# Overlay editor has a bounded card and cannot inherit a stale floating-window
# geometry from other Quickshell windows. Keep it alive through the exit frame.
name='ui/widgets/WidgetSettings.qml';s=(root/name).read_text()
s=s.replace('sourceComponent:FloatingWindow{','sourceComponent:PanelWindow{')
s=s.replace("id:win;visible:true;title:'Edit Widget';implicitWidth:460;implicitHeight:column.implicitHeight+40;color:'transparent'", """id:win;visible:true;color:'transparent'
   anchors{left:true;right:true;top:true;bottom:true}
   exclusionMode:ExclusionMode.Ignore
   WlrLayershell.layer:WlrLayer.Overlay
   WlrLayershell.namespace:'quickintosh:widget-editor'
   WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive
   mask:Region{item:card}
   property bool closing:false
   property bool removeAfterClose:false
   function finish(remove){if(closing)return;removeAfterClose=!!remove;closing=true;closeDelay.restart()}
   Timer{id:closeDelay;interval:160;onTriggered:{const zone=WidgetState.editingZone,id=WidgetState.editingId;WidgetState.editingId='';if(win.removeAfterClose)WidgetState.removeWidget(zone,id)}}
   GlassBackdrop{element:'menus';gateEnabled:false}
""")
# This pass runs before localization, so source strings are still untranslated.
s=s.replace("   onClosed:WidgetState.editingId=''",'')
s=s.replace("anchors.fill:parent;radius:22;color:Theme.isLight ? '#f3f3f6':'#252529'", """id:card;anchors.centerIn:parent;width:Math.min(580,win.width-40)
    height:Math.min(win.height-80,column.implicitHeight+40)
    radius:22;color:Theme.isLight ? '#b8f3f3f6':'#b8252529'
    opacity:win.closing ? 0:1;scale:win.closing ? .96:1
    Behavior on opacity{NumberAnimation{duration:150}}
    Behavior on scale{NumberAnimation{duration:150;easing.type:Easing.OutCubic}}""")
s=s.replace('    ColumnLayout{\n     id:column;anchors{left:parent.left;right:parent.right;top:parent.top;margins:20}spacing:14', '''    ScrollView{
     anchors.fill:parent;anchors.margins:20;clip:true
     contentWidth:availableWidth
     ColumnLayout{
     id:column;width:parent.width;spacing:18''')
s=s.replace("     RowLayout{Layout.alignment:Qt.AlignRight", "     RowLayout{Layout.fillWidth:true;Layout.alignment:Qt.AlignRight")
s=s.replace("onClicked:{WidgetState.removeWidget(WidgetState.editingZone,WidgetState.editingId);WidgetState.editingId=''}",'onClicked:win.finish(true)')
s=s.replace("onClicked:WidgetState.editingId=''",'onClicked:win.finish(false)')
s=s.replace("   Shortcut{sequence:'Escape';onActivated:WidgetState.editingId=''}", "   Shortcut{sequence:'Escape';onActivated:win.finish(false)}")
s=s.replace("    }\n   }\n   Shortcut", "    }\n    }\n   }\n   Shortcut",1)
anchor="     RowLayout{visible:root.entry.type==='image';Layout.fillWidth:true"
i=s.index(anchor)
s=s[:i]+'''     Item{
      visible:root.entry.type==='image';Layout.fillWidth:true;Layout.preferredHeight:visible ? 132:0
      Rectangle{anchors.fill:parent;radius:14;color:Theme.fillControl}
      Image{anchors.fill:parent;anchors.margins:8;source:root.entry.image ? 'file://'+root.entry.image.split('/').map(encodeURIComponent).join('/'):'';fillMode:Image.PreserveAspectFit;asynchronous:true;sourceSize:Qt.size(500,240)}
     }
     RowLayout{Layout.fillWidth:true
      Text{text:'Surface';color:Theme.textPrimary;Layout.fillWidth:true}
      TahoeCombo{model:['Follow Settings','Liquid Glass','Solid','Transparent'];currentIndex:Math.max(0,['auto','glass','solid','transparent'].indexOf(root.entry.material || 'auto'));onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{material:i===0 ? '':['auto','glass','solid','transparent'][i]})}
     }
     RowLayout{visible:root.entry.type==='image';Layout.fillWidth:true
      Text{text:'Image fit';color:Theme.textPrimary;Layout.fillWidth:true}
      TahoeCombo{model:['Fill','Fit','Stretch'];currentIndex:Math.max(0,['crop','fit','stretch'].indexOf(root.entry.imageFit || 'crop'));onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{imageFit:['crop','fit','stretch'][i]})}
     }
     RowLayout{visible:root.entry.type==='image';Layout.fillWidth:true
      Text{text:'Shape';color:Theme.textPrimary;Layout.fillWidth:true}
      TahoeCombo{model:['Rounded','Rectangle','Circle'];currentIndex:Math.max(0,['rounded','rectangle','circle'].indexOf(root.entry.shape || 'rounded'));onActivated:i=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{shape:['rounded','rectangle','circle'][i]})}
     }
'''+s[i:]
write(name,s)

name='ui/settings/pages/DockPage.qml';s=(root/name).read_text()
a='        title:"Widgets"'
# Widget controls are kept in Desktop & Dock, independent of icon appearance.
i=s.index(a)+len(a)
s=s[:i]+'''
        RowLayout{Layout.fillWidth:true
            Text{text:'Default widget surface';color:Theme.textPrimary;Layout.fillWidth:true}
            TahoeCombo{model:['Liquid Glass','Solid','Transparent'];currentIndex:Math.max(0,['glass','solid','transparent'].indexOf(WidgetState.widgetMaterial));onActivated:i=>WidgetState.widgetMaterial=['glass','solid','transparent'][i]}
        }
        RowLayout{Layout.fillWidth:true
            Text{text:'Desktop context menu';color:Theme.textPrimary;Layout.fillWidth:true}
            TahoeCombo{model:['Liquid Glass','Solid','Transparent'];currentIndex:Math.max(0,['glass','solid','transparent'].indexOf(WidgetState.desktopMenuMaterial));onActivated:i=>WidgetState.desktopMenuMaterial=['glass','solid','transparent'][i]}
        }
        ConfigSwitch{text:'Free widget placement with Control';checked:WidgetState.allowCtrlFreePlacement;onToggled:v=>WidgetState.allowCtrlFreePlacement=v}
        ConfigSwitch{text:'Keep widgets clear of desktop icons';checked:WidgetState.avoidDesktopIcons;onToggled:v=>WidgetState.avoidDesktopIcons=v}
'''+s[i:];write(name,s)
# Human-readable sizes in both the editor and gallery.
edit('services/WidgetRegistry.qml','readonly property var sizeLabels: ({','readonly property var sizeLabels: ({portrait:"Portrait",banner:"Banner",wide:"Wide",tall:"Tall",square:"Extra Large",')

# Immediate privacy handoff is event driven. The fullscreen fallback keeps its
# existing polling only as a safety net for monitors without an island.
write('services/PrivacyPresentation.qml',(here/'PrivacyPresentation.qml').read_text())
write('services/qmldir',(root/'services/qmldir').read_text()+'\nsingleton PrivacyPresentation PrivacyPresentation.qml\n')
name='rosa/overlays/IslandWindow.qml'
edit(name,'    readonly property bool inBar:', '''    readonly property bool privacyHandoff:win.mine && !IslandBus.locked &&
        (!IslandConfig.s("enabled") || win.blocked || !win.wanted || idleVisibility.hideRequested)
    function syncPrivacyHandoff(){NativeSettings.PrivacyPresentation.setCorner(win.modelData.name,win.privacyCornerRequested)}
    readonly property bool privacyCornerRequested:win.privacyHandoff && IslandConfig.s("privacy") && Privacy.active
    onPrivacyCornerRequestedChanged:syncPrivacyHandoff()
    readonly property bool inBar:''')
# Existing lifecycle handler remains intact; use a child object for teardown.
edit(name,'    readonly property bool privacyHandoff:', '''    QtObject{Component.onCompleted:win.syncPrivacyHandoff();Component.onDestruction:NativeSettings.PrivacyPresentation.setCorner(win.modelData.name,false)}
    readonly property bool privacyHandoff:''')
edit(name,'visible: scale > 0.01 && (NativeSettings.PrivacyPreferences.showExpanded','visible: !win.privacyHandoff && scale > 0.01 && (NativeSettings.PrivacyPreferences.showExpanded')
name='ui/FullscreenPrivacy.qml'
# Locate the file by its installed name (the feedback integrator owns this).
if not (root/name).exists():
 matches=list(root.rglob('FullscreenPrivacy.qml'))
 if len(matches)!=1:raise ValueError('FullscreenPrivacy location')
 name=str(matches[0].relative_to(root))
edit(name,'!!root.full[modelData.name]','(!IslandBus.locked && (PrivacyPresentation.corner[modelData.name] || !!root.full[modelData.name]))')
# IslandBus belongs to Rosa's service namespace.
edit(name,'import qs.services\n','import qs.services\nimport qs.rosa.services\n')

# Resizing a freely placed widget must not snap it back to the grid.
edit('services/WidgetState.qml','|| root.collides(list, id, next.x, next.y, d.w, d.h)) {','|| (!next.freePosition && root.collides(list, id, next.x, next.y, d.w, d.h))) {')
# Clear the gallery grab state when closed from Escape or another surface.
edit('services/WidgetState.qml','    function closeGallery() {','    function closeGallery() {\n        root.galleryDrag=null')

# Layer-shell windows do not publish a reliable global window position to Qt.
# Use a full-screen, input-masked gallery so pointer and desktop coordinates
# share the same origin, and retain the input region throughout a drag.
name='ui/widgets/WidgetGallery.qml'
edit(name,'id:win;anchors{left:true;right:true;bottom:true}','id:win;anchors{left:true;right:true;top:true;bottom:true}')
edit(name,"implicitHeight:Math.min(screen.height-60,580);color:'transparent';exclusiveZone:-1","color:'transparent';exclusiveZone:-1")
edit(name,'mask:Region{item:panel}','mask:Region{item:WidgetState.galleryDrag ? win.contentItem:panel}')
edit(name,'height:parent.height-24;radius:24','height:Math.min(parent.height-60,556);radius:24')
edit(name,'const global=addMouse.mapToGlobal(event.x,event.y)\n                const gx=global.x-win.screen.x,gy=global.y-win.screen.y','const gx=point.x,gy=point.y')
edit(name,'outside:point.y<panel.y','free:!!(event.modifiers & Qt.ControlModifier),outside:point.y<panel.y || point.x<panel.x || point.x>panel.x+panel.width || point.y>panel.y+panel.height')
edit(name,'d.y-shape.h/2-WidgetState.desktopOffsetY,d.theme','d.y-shape.h/2-WidgetState.desktopOffsetY,d.theme,d.free')
name='services/WidgetState.qml'
edit(name,'function snap(size, x, y) {','function snap(size, x, y, free) {')
edit(name,'        var list = root.listOf("desktop")\n        var d = root.sizeOf(size)','''        var list = root.listOf("desktop")
        var d = root.sizeOf(size)
        if(free && root.allowCtrlFreePlacement)return {x:Math.max(0,Math.min(x,root.areaWidth-d.w)),y:Math.max(0,Math.min(y,root.areaHeight-d.h))}''')
edit(name,'function addWidgetAt(zone, type, size, variant, x, y, theme) {','function addWidgetAt(zone, type, size, variant, x, y, theme, free) {')
edit(name,'var p = root.snap(size, x, y)','var p = root.snap(size, x, y, free)')
edit(name,'theme: theme || "auto", x: p.x, y: p.y','theme: theme || "auto", x: p.x, y: p.y, freePosition:!!free && root.allowCtrlFreePlacement')
