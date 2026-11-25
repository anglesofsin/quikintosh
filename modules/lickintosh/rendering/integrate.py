"""Native frame pacing, quality policy and coherent animation controls."""
from pathlib import Path
import re,sys
root=Path(sys.argv[1]);here=Path(__file__).parent

def write(name,text):
 p=root/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(text)
def edit(name,old,new):
 text=(root/name).read_text();assert old in text,(name,old[:60]);write(name,text.replace(old,new))
write('services/RenderingState.qml',(here/'RenderingState.qml').read_text())
write('ui/settings/pages/RenderingSettings.qml',(here/'RenderingSettings.qml').read_text())
for folder,entry in [('services','singleton RenderingState RenderingState.qml'),('ui/settings/pages','RenderingSettings RenderingSettings.qml')]:
 p=folder+'/qmldir';write(p,(root/p).read_text()+'\n'+entry+'\n')
edit('services/ShellConfig.qml','            property JsonObject glass: JsonObject {','''            property JsonObject performance:JsonObject{
                property int maximumFps:0
                property int glassFps:0
                property int geometryFps:0
                property real textureScale:.5
                property real blurScale:.5
                property real motionScale:1
                property bool glassEnabled:true
                property bool blurEnabled:true
                property bool shadows:true
                property bool ambientAnimations:true
                property bool prewarm:true
                property bool measureFrames:false
                property bool cacheWidgetDrag:false
                property string renderer:"auto"
            }
            property JsonObject glass: JsonObject {''')
# Commit multi-option changes once, avoiding partial self-reloads and duplicate I/O.
edit('services/ShellConfig.qml','    FileView {','    Timer{id:configurationSave;interval:0;onTriggered:configFileView.writeAdapter()}\n    FileView {')
edit('services/ShellConfig.qml','onAdapterUpdated: writeAdapter()','onAdapterUpdated: configurationSave.restart()')
edit('shell.qml','    id: appRoot','    id: appRoot\n    property var renderPolicy:RenderingState')
edit('settings.qml',' id:window',' id:window\n property var renderPolicy:RenderingState')
edit('ui/settings/pages/AppearanceControls.qml',' CornerSettings{}',' RenderingSettings{}\n CornerSettings{}')
edit('services/Theme.qml','readonly property bool plainSurfaces: root.compositorBlur || root.gameMode','readonly property bool plainSurfaces: root.compositorBlur || root.gameMode || !RenderingState.glassEnabled')
edit('services/ShellMotion.qml',' : root.speed',' : root.speed * RenderingState.motionScale')
edit('services/ShellMotion.qml','    function spatial(factor) {','    function duration(ms){return Math.max(0,Math.round(ms*root.motionScale))}\n    function spatial(factor) {')
p='components/glass/LiquidGlassBackdrop.qml';s=(root/p).read_text().replace('property real blurDownscale: 0.5','property real blurDownscale: RenderingState.blurScale')
s=s.replace('readonly property Item blurSource: blurFinal','readonly property Item blurSource: RenderingState.blurEnabled ? blurFinal:fb')
s=s.replace('        if(ready)retained=true','        if(ready)retained=true\n        if(ready)Qt.callLater(function(){RenderingState.register(root.Window.window,root.element)})',1)
# Blur intermediates remain allocated but do not rerender when blur is disabled.
s=s.replace('id: blurIntermediate\n        visible: false\n        live: root.ready','id: blurIntermediate\n        visible: false\n        live: root.ready && RenderingState.blurEnabled',1)
s=s.replace('id: blurFinal\n        visible: false\n        live: root.ready','id: blurFinal\n        visible: false\n        live: root.ready && RenderingState.blurEnabled',1);write(p,s)
p='components/glass/GlassTracker.qml';s='import qs.services\n'+(root/p).read_text();s=s.replace('property real backdropScale: 0.5','property real backdropScale: RenderingState.textureScale')
a=s.index('    Timer {\n        interval: root.precisionUsers>0 ? 16');s=s[:a]+'''    property double lastNativeInventory:0
    property double lastGeometryFrame:0
    FrameAnimation{
        running:root.captureUsers>0 && (root.precisionUsers>0 || root.fast)
        onTriggered:{
            const now=Date.now(),fps=RenderingState.geometryFps
            if(fps>0 && now-root.lastGeometryFrame<1000/fps-.5)return
            root.lastGeometryFrame=now
            const signature=root.signature();if(signature!==root.lastSignature){root.lastSignature=signature;root.markActive()}
            RenderingState.updateGeometry()
            if(!RenderingState.geometryAvailable || now-root.lastNativeInventory>250){root.lastNativeInventory=now;root.refreshWindows()}
        }
    }
    Timer{
        interval:root.captureIdleInterval
        running:(root.captureUsers>0 || root.inventoryUsers>0) && !(root.captureUsers>0 && (root.precisionUsers>0 || root.fast))
        repeat:true
        onTriggered:{const signature=root.signature();if(signature!==root.lastSignature){root.lastSignature=signature;root.markActive()}if(root.captureUsers>0)root.refreshWindows();else root.captureSnapshot()}
    }
}
''';write(p,s)
p='components/glass/GlassWindows.qml';s=(root/p).read_text()
s=s.replace('    property bool capturing:true','''    property bool capturing:true
    property double lastCaptureFrame:0
    FrameAnimation{
        running:root.capturing && RenderingState.glassFps>0
        onTriggered:{
            const now=Date.now();if(now-root.lastCaptureFrame<1000/RenderingState.glassFps-.5)return
            root.lastCaptureFrame=now
            for(let i=0;i<windowsRepeater.count;i++){const view=windowsRepeater.itemAt(i);if(view && view.shown && !view.sourceClosed)view.captureFrame()}
        }
    }''',1)
s=s.replace('live: root.capturing && gate.wanted &&','live: RenderingState.glassFps===0 && root.capturing && gate.wanted &&',1)
s=s.replace('        ScreencopyView {\n            id: view',"""        Item {
            id:viewport
            required property var modelData
            readonly property var rendered:RenderingState.geometry[root.addressOf(modelData.address)] || null
            readonly property var clipBox:rendered && rendered.clipActive!==false ? (rendered.clip || null):null
            x:clipBox ? (clipBox[0]-root.monitorX)*root.coordinateScale:0
            y:clipBox ? (clipBox[1]-root.monitorY)*root.coordinateScale:0
            width:clipBox ? clipBox[2]*root.coordinateScale:root.monitorObject ? root.monitorObject.width/(root.monitorObject.scale || 1)*root.coordinateScale:0
            height:clipBox ? clipBox[3]*root.coordinateScale:root.monitorObject ? root.monitorObject.height/(root.monitorObject.scale || 1)*root.coordinateScale:0
            clip:true
            z:view.z
            opacity:Math.max(0,Math.min(1,rendered?.opacity ?? 1))
            readonly property alias ipc:view.ipc
            readonly property alias hasContent:view.hasContent
            readonly property alias pending:view.pending
            readonly property alias shown:view.shown
            readonly property alias sourceClosed:view.sourceClosed
            onOpacityChanged:root.recount()
            function captureFrame(){view.captureFrame()}
        ScreencopyView {
            id: view""",1)
# The newly inserted viewport is the delegate; the child receives its model.
a=s.index('        ScreencopyView {\n            id: view');b=s.index('            readonly property var ipc:',a)
s=s[:a]+s[a:b].replace('required property var modelData','property var modelData:viewport.modelData')+s[b:]
s=s.replace('readonly property var ipc: root.normalizedIpc(modelData.lastIpcObject)','readonly property var ipc: root.normalizedIpc(viewport.rendered ? Object.assign({},modelData.lastIpcObject,{at:viewport.rendered.at,size:viewport.rendered.size}):modelData.lastIpcObject)',1)
s=s.replace('&& root.workspaceVisible(ipc, modelData.workspace)','&& (viewport.rendered ? viewport.rendered.visible:root.workspaceVisible(ipc, modelData.workspace))',1)
s=s.replace('x: ipc && ipc.at ? ipc.at[0] - root.monitorX : 0','x: ipc && ipc.at ? ipc.at[0] - root.monitorX - viewport.x:0',1)
s=s.replace('y: ipc && ipc.at ? ipc.at[1] - root.monitorY : 0','y: ipc && ipc.at ? ipc.at[1] - root.monitorY - viewport.y:0',1)
last=s.rfind('    }\n}');assert last>0;s=s[:last]+'        }\n'+s[last:]
write(p,s)
p='components/glass/GlassPrewarm.qml';s=(root/p).read_text().replace('if(!item || !item.preload','if(!RenderingState.prewarm || !item || !item.preload',1)
s=s.replace(' Connections{target:GlassTracker;', ' Connections{target:RenderingState;function onPrewarmChanged(){if(RenderingState.prewarm)root.requestAll();else{root.queue=[];root.finish()}}}\n Connections{target:GlassTracker;',1);write(p,s)
edit('components/glass/GlassBackdrop.qml','(root.prewarming || root.retained)','(root.prewarming || (RenderingState.prewarm && root.retained))')
edit('ui/desktop/DesktopLayer.qml','interactionPaused:slot.dragging','interactionPaused:slot.dragging && RenderingState.options.cacheWidgetDrag')
edit('ui/desktop/DesktopLayer.qml','live:false;hideSource:slot.dragging;visible:slot.dragging','live:false;hideSource:slot.dragging && RenderingState.options.cacheWidgetDrag;visible:slot.dragging && RenderingState.options.cacheWidgetDrag')
for name in ['PersonalClock.qml','CreativeText.qml']:
 p='ui/widgets/types/'+name;s=(root/p).read_text().replace("glassReady:effect==='glass' &&", "glassReady:!Theme.plainSurfaces && effect==='glass' &&");write(p,s)
# Scale finite literal transitions as well as the shared motion functions.
# Infinite animations keep their duration; pausing them avoids zero-time loops.
def add_import(text):
 if 'import qs.services as RenderPolicy' in text:return text
 pos=text.find('import ');assert pos>=0
 return text[:pos]+'import qs.services as RenderPolicy\n'+text[pos:]
for p in root.rglob('*.qml'):
 if p.is_symlink():continue
 s=p.read_text();original=s
 s=re.sub(r'shadowEnabled:\s*([^;\n}]+)',lambda m:'shadowEnabled:RenderPolicy.RenderingState.shadows && ('+m[1].strip()+')',s)
 if 'Animation.Infinite' not in s:
  s=re.sub(r'((?:NumberAnimation|PropertyAnimation|ColorAnimation|RotationAnimator|ScaleAnimator|OpacityAnimator|XAnimator|YAnimator)\s*(?:on\s+\w+\s*)?\{[^{}]*?\bduration:)\s*(\d+)(?![\d.])',lambda m:m[1]+'RenderPolicy.ShellMotion.duration('+m[2]+')',s)
 # Find animation blocks with a direct infinite-loop property, not their parent.
 inserts=[]
 for match in re.finditer(r'\b(?:NumberAnimation|PropertyAnimation|RotationAnimator|SequentialAnimation|ParallelAnimation)\s*(?:on\s+\w+\s*)?\{',s):
  start=match.end();depth=1;quote='';escaped=False;flat=[];end=start
  for end in range(start,len(s)):
   ch=s[end]
   if quote:
    if escaped:escaped=False
    elif ch=='\\':escaped=True
    elif ch==quote:quote=''
    if depth==1:flat.append(' ')
    continue
   if ch in "'\"":quote=ch;continue
   if ch=='{':depth+=1
   elif ch=='}':
    depth-=1
    if depth==0:break
   if depth==1:flat.append(ch)
  top=''.join(flat)
  if re.search(r'\bloops\s*:\s*Animation\.Infinite',top) and not re.search(r'\bpaused\s*:',top):inserts.append(start)
 for pos in reversed(inserts):s=s[:pos]+'\n paused:running && !RenderPolicy.RenderingState.ambientAnimations\n'+s[pos:]
 if s!=original:write(str(p.relative_to(root)),add_import(s))
