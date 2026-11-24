"""Responsive utility widgets, native dialog handoff and persistent free sizing."""
from pathlib import Path
import sys
r=Path(sys.argv[1]);here=Path(__file__).parent

def edit(name,old,new,count=1):
 p=r/name;s=p.read_text()
 if s.count(old)!=count:raise ValueError(f'Widget UI anchor {name}: {old[:65]} ({s.count(old)})')
 p.chmod(p.stat().st_mode|0o200);p.write_text(s.replace(old,new))

for source,target in [('PersonalClock.qml','ui/widgets/types/PersonalClock.qml'),('WidgetResizeHandles.qml','ui/widgets/WidgetResizeHandles.qml')]:
 p=r/target
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text((here/source).read_text())
p=r/'ui/widgets/qmldir';p.write_text(p.read_text()+'\nWidgetResizeHandles WidgetResizeHandles.qml\n')
name='services/WidgetState.qml'
edit(name,'    property var galleryDrag:null','    property var galleryDrag:null\n    property string resizingId:""')
edit(name,'    function sizeOf(size) {','''    function sizeOf(size) {
        if(typeof size==='object' && size){
            const preset=root.sizeOf(size.size)
            return {w:size.customWidth>0 ? size.customWidth:preset.w,h:size.customHeight>0 ? size.customHeight:preset.h}
        }''')
edit(name,'var d = root.sizeOf(o.size)','var d = root.sizeOf(o)')
edit(name,'var d = root.sizeOf(list[i].size)','var d = root.sizeOf(list[i])')
edit(name,'root.nearestFree(list, id, list[i].size, nx, ny)','root.nearestFree(list, id, list[i], nx, ny)')
edit(name,'Object.assign({}, list[i], { size: size })','Object.assign({}, list[i], { size: size, customWidth:0, customHeight:0 })')
edit(name,'    function resizeWidget(zone, id, size) {','''    function resizeWidgetTo(id,width,height,free){
        const list=root.listOf('desktop'),i=root.indexOfId(list,id)
        if(i<0)return false
        const entry=list[i]
        const w=Math.round(Math.max(100,Math.min(root.areaWidth-entry.x,width)))
        const h=Math.round(Math.max(72,Math.min(root.areaHeight-entry.y,height)))
        const overlap=(free && root.allowCtrlFreePlacement) || !!entry.freePosition
        if(!overlap && root.collides(list,id,entry.x,entry.y,w,h))return false
        list[i]=Object.assign({},entry,{customWidth:w,customHeight:h,freePosition:overlap})
        root.setList('desktop',list);return true
    }
    function resizeWidget(zone, id, size) {''')
edit(name,'        if (widget) entries.push({label:"Edit Widget…",action:"configure"})','''        if (widget) entries.push({label:"Edit Widget…",action:"configure"})
        if(widget && zone==='desktop' && ['personalclock','image','notes','shortcuts','microphone','display','storageinfo','systeminfo'].includes(widget.type))entries.push({label:'Resize Widget',action:'resize'})''')
edit(name,'if (action === "configure") root.editWidget(zone,id)','if(action==="resize")root.resizingId=id\n        else if (action === "configure") root.editWidget(zone,id)')
for name in ['ui/widgets/WidgetView.qml','ui/widgets/WidgetSnapshot.qml']:
 edit(name,'WidgetState.sizeOf(root.widgetData.size)','WidgetState.sizeOf(root.widgetData)')
name='ui/desktop/DesktopLayer.qml'
edit(name,'WidgetState.sizeOf(slot.spec.size)','WidgetState.sizeOf(slot.spec)')
edit(name,'                    property bool dragging: false','''                    property bool resizing:false
                    property real resizeWidth:0
                    property real resizeHeight:0
                    property bool dragging: false''')
edit(name,'z: slot.dragging ? 500 : 20','z:slot.dragging || slot.resizing ? 500:20')
edit(name,'width: slot.dims.w','width:slot.resizing ? slot.resizeWidth:slot.dims.w')
edit(name,'height: slot.dims.h','height:slot.resizing ? slot.resizeHeight:slot.dims.h')
edit(name,'id:liveWidget\n                        widgetData: slot.spec','id:liveWidget\n                        width:slot.width;height:slot.height\n                        widgetData: slot.spec')
edit(name,'                    DragHandler {\n                        target: null','                    DragHandler {\n                        enabled:!slot.resizing\n                        target: null',2)
edit(name,'                    ShaderEffectSource{\n                        anchors.fill:parent;sourceItem:liveWidget','''                    WidgetResizeHandles{
                        anchors.fill:parent;slot:parent;stage:parent.parent
                        visible:['personalclock','image','notes','shortcuts','microphone','display','storageinfo','systeminfo'].includes(slot.spec.type) && (WidgetState.galleryZone==='desktop' || WidgetState.resizingId===slot.spec.id || active)
                    }
                    ShaderEffectSource{
                        anchors.fill:parent;sourceItem:liveWidget''')
# The native file chooser is a regular application window. An Overlay editor
# must temporarily yield both its stacking layer and exclusive keyboard grab.
name='ui/widgets/WidgetSettings.qml'
edit(name,"WlrLayershell.layer:WlrLayer.Overlay","WlrLayershell.layer:picker.visible ? WlrLayer.Bottom:WlrLayer.Overlay")
edit(name,'WlrLayershell.keyboardFocus:WlrKeyboardFocus.Exclusive','WlrLayershell.keyboardFocus:picker.visible ? WlrKeyboardFocus.None:WlrKeyboardFocus.Exclusive')
edit(name,'mask:Region{item:card}','mask:Region{item:picker.visible ? null:win.contentItem}')
edit(name,"FileDialog{id:picker;","FileDialog{id:picker;modality:Qt.WindowModal;currentFolder:'file://'+Quickshell.env('HOME')+'/Pictures';")
# This full input region also keeps in-process color dialogs, popup controls and
# their outside-card portions clickable. The chooser receives no intercepted input.
name='ui/widgets/WidgetGallery.qml'
edit(name,"id:win;anchors{left:true;right:true;top:true;bottom:true}","id:win;visible:WidgetState.editingId==='';anchors{left:true;right:true;top:true;bottom:true}")

name='ui/widgets/WidgetSettings.qml'
s=(r/name).read_text();a="     ColumnLayout{visible:root.entry.type==='personalclock';Layout.fillWidth:true;spacing:12";i=s.index(a);z=s.index("     Item{\n      visible:root.entry.type==='image'",i)
s=s[:i]+(here/'ClockControls.inc').read_text()+s[z:]
p=r/name;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
# Photos and the personal clock get the wider presets as well as mouse resizing.
p=r/'services/WidgetRegistry.qml';s=p.read_text();s=s.replace("file:'PersonalClock',sizes:['s','m','l']","file:'PersonalClock',sizes:['s','m','l','wide','banner','tall','square']");p.write_text(s)

# Keep completion controls visible even with an extensive clock editor.
name='ui/widgets/WidgetSettings.qml'
p=r/name;s=p.read_text();a=s.index('     RowLayout{Layout.fillWidth:true;Layout.alignment:Qt.AlignRight')
z=s.index('\n     }',a)+len('\n     }')
buttons=s[a:z]
s=s[:a]+s[z:]
footer=buttons.replace('     RowLayout{Layout.fillWidth:true;Layout.alignment:Qt.AlignRight','''     RowLayout{anchors{left:parent.left;right:parent.right;bottom:parent.bottom;margins:20}spacing:10
      Item{Layout.fillWidth:true}''')
anchor='    }\n    }\n   }\n   Shortcut'
if s.count(anchor)!=1:raise ValueError('Widget footer anchor')
s=s.replace(anchor,'    }\n    }\n'+footer+'\n   }\n   Shortcut')
s=s.replace('height:Math.min(win.height-80,column.implicitHeight+40)','height:Math.min(win.height-80,column.implicitHeight+96)')
s=s.replace('anchors.fill:parent;anchors.margins:20;clip:true','anchors.fill:parent;anchors.margins:20;anchors.bottomMargin:76;clip:true')
s=s.replace("Shortcut{sequence:'Escape';onActivated:win.finish(false)}","Shortcut{sequence:'Escape';enabled:!picker.visible;onActivated:win.finish(false)}")
p.write_text(s)

# One-shot resize selection ends on outside focus/click, Escape or release.
name='ui/desktop/DesktopLayer.qml'
edit(name,'WlrLayershell.layer: WlrLayer.Bottom','WlrLayershell.layer:WidgetState.resizingId!=="" ? WlrLayer.Top:WlrLayer.Bottom')
edit(name,'        id: win','        id: win\n        Shortcut{sequence:"Escape";context:Qt.ApplicationShortcut;enabled:WidgetState.resizingId!=="";onActivated:WidgetState.resizingId=""}')
edit(name,'            focus: true','            focus: true\n            Connections{target:WidgetState;function onResizingIdChanged(){if(WidgetState.resizingId!=="")Qt.callLater(()=>stage.forceActiveFocus())}}')
edit(name,'QuickLookState.returnToDesktop ? WlrKeyboardFocus.Exclusive','QuickLookState.returnToDesktop || WidgetState.resizingId!=="" ? WlrKeyboardFocus.Exclusive')
edit(name,'{DesktopFiles.desktopFocused=true;stage.forceActiveFocus()}','{WidgetState.resizingId="";DesktopFiles.desktopFocused=true;stage.forceActiveFocus()}',2)
edit(name,'            Keys.onPressed: function(event) {','            Keys.onPressed: function(event) {\n                if(event.key===Qt.Key_Escape && WidgetState.resizingId!==""){WidgetState.resizingId="";event.accepted=true;return}')
name='services/WidgetState.qml'
edit(name,'    property string resizingId:""','    property string resizingId:""\n    Connections{target:DesktopFiles;function onDesktopFocusedChanged(){if(!DesktopFiles.desktopFocused)root.resizingId=""}}')
edit(name,'    function closeGallery() {','    function closeGallery() {\n        root.resizingId=""')

# Previews wrap vertically instead of being silently cropped by a horizontal
# flickable. Each preview fits both the viewport width and available height.
name='ui/widgets/WidgetGallery.qml'
edit(name,'''         Flickable{
          width:parent.width;height:previews.height+6;contentWidth:previews.width;clip:true;boundsBehavior:Flickable.StopAtBounds
          Row{
           id:previews;spacing:16''','''         Flow{
           id:previews;width:parent.width;spacing:18''')
edit(name,'readonly property var dims:WidgetState.sizeOf(modelData.size);spacing:8','readonly property var dims:WidgetState.sizeOf(modelData.size);readonly property real previewScale:Math.max(.1,Math.min(.66,(list.width-8)/dims.w,(list.height-36)/dims.h));spacing:8')
edit(name,'id:face;width:tile.dims.w*.78;height:tile.dims.h*.78','id:face;width:tile.dims.w*tile.previewScale;height:tile.dims.h*tile.previewScale')
edit(name,'WidgetView{transformOrigin:Item.TopLeft;scale:.78;','WidgetView{transformOrigin:Item.TopLeft;scale:tile.previewScale;')
edit(name,'''            }
           }
          }
         }
        }
        Text{anchors.centerIn:parent''','''            }
           }
         }
        }
        Text{anchors.centerIn:parent''')

# Share the desktop's wallpaper-only sampler. Backdrop snapshots must never
# recursively sample the very clock image they are producing.
edit('services/WidgetState.qml','    property string resizingId:""','    property var desktopBackdrop:null\n    property string resizingId:""')
edit('ui/desktop/DesktopLayer.qml','        GlassBackdrop {\n            captureWindows: false','        GlassBackdrop {\n            id:desktopWidgetBackdrop\n            Component.onCompleted:WidgetState.desktopBackdrop=desktopWidgetBackdrop\n            Component.onDestruction:if(WidgetState.desktopBackdrop===desktopWidgetBackdrop)WidgetState.desktopBackdrop=null\n            captureWindows: false')
edit('ui/widgets/WidgetSnapshot.qml','        onLoaded: {','        onLoaded: {\n            if(loader.item.isSnapshot!==undefined)loader.item.isSnapshot=true')
import shutil,subprocess,os
shader=r/'assets/shaders/liquidglass/WidgetGlyphGlass.frag'
shader.parent.mkdir(parents=True,exist_ok=True)
shutil.copyfile(here/'WidgetGlyphGlass.frag',shader)
qsb=os.environ.get('QUICKINTOSH_TEST_QSB','qsb')
subprocess.run([qsb,'--glsl','100 es,120,150,300 es,320 es,440','--hlsl','50','--msl','12','-o',str(shader)+'.qsb',str(shader)],check=True)

# A gallery offers clock compositions, not seven copies of one design.
edit('services/WidgetRegistry.qml','    function tilesOf(type) {',"    function tilesOf(type) {\n        if(type==='personalclock')return [\n            {size:'m',variant:'classic',label:'Classic'},\n            {size:'l',variant:'stacked',label:'Stacked'},\n            {size:'m',variant:'minimal',label:'Minimal'}\n        ]")
