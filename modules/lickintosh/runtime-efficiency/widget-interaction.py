"""Keep widget gestures local, retain snapshot delegates and batch live edits."""
p='components/glass/DesktopSnapshot.qml';s=(root/p).read_text();s='import Quickshell\n'+s
s=s.replace('    property bool widgetsShown: true','    property bool widgetsShown: true\n    property bool widgetsPrepared:false\n    onWidgetsShownChanged:if(widgetsShown)widgetsPrepared=true\n    Component.onCompleted:if(widgetsShown)widgetsPrepared=true',1)
s=s.replace('model:WidgetState.showDesktopWidgets ? WidgetState.desktop:[]','model:ScriptModel{values:root.widgetsPrepared && WidgetState.showDesktopWidgets ? WidgetState.desktop:[];objectProp:"id"}',1)
s=s.replace('model: DesktopFiles.layout','model:ScriptModel{values:DesktopFiles.layout;objectProp:"path"}',1);write(p,s)
# Snapshot previews must never sample a texture owned by another QQuickWindow.
p='ui/widgets/types/PersonalClock.qml';s=(root/p).read_text()
s=s.replace('  const shared=WidgetState.desktopBackdrop','  if(root.isSnapshot)return null\n  const shared=WidgetState.desktopBackdrop',1)
s=s.replace('if(shared && (!QsWindow.window?.screen || shared.monitorName===QsWindow.window.screen.name))return shared','if(shared && shared.win===QsWindow.window)return shared',1)
s=s.replace(' property bool isSnapshot:false',' property bool isSnapshot:false\n property bool interactionPaused:false',1)
# Measure the fixed-format envelope at a reference size, not for every pixel
# of resize. Keep custom spacing in the final fit rather than in FontMetrics.
s=s.replace('readonly property real reservedTextWidth:{','readonly property var measuredTime:{',1)
s=s.replace("let widest='0',digitWidth=0,result=1","let widest='0',digitWidth=0,result=1,columns=1",1)
s=s.replace("for(const line of value.replace(/[0-9]/g,widest).split('\\n'))result=Math.max(result,measure.advanceWidth(line),measure.boundingRect(line).width)","for(const line of value.replace(/[0-9]/g,widest).split('\\n')){result=Math.max(result,measure.advanceWidth(line),measure.boundingRect(line).width);columns=Math.max(columns,line.length)}",1)
s=s.replace('  return result\n }','  return {width:result,columns:columns}\n }\n readonly property real reservedTextWidth:root.measuredTime.width',1)
s=s.replace('readonly property real fittedSize:Math.min(basePixelSize,basePixelSize*Math.max(1,width-40)/reservedTextWidth)','readonly property real fittedSize:Math.min(basePixelSize,100*Math.max(1,width-40-(root.widgetData?.clockSpacing ?? root.style.spacing)*(root.measuredTime.columns-1))/reservedTextWidth)',1)
s=s.replace('pixelSize:root.basePixelSize,weight:','pixelSize:100,weight:',1)
s=s.replace('letterSpacing:root.widgetData?.clockSpacing ?? root.style.spacing,features:{tnum:1}})}','letterSpacing:0,features:{tnum:1}})}',1)
s=s.replace('live:true;visible:false','live:root.visible && !root.interactionPaused && (root.glassReady || root.effect===\'gradient\');visible:false',1)
s=s.replace('Connections{target:glyphGlass.Window.window;ignoreUnknownSignals:true;','Connections{target:glyphGlass.Window.window;enabled:root.visible && !root.isSnapshot && !root.interactionPaused;ignoreUnknownSignals:true;',1)
s=s.replace('    Component.onCompleted:syncOrigin()','    Component.onCompleted:syncOrigin()',1)
write(p,s)
# The drag image is frozen already. Do not keep remapping the hidden original
# glass quads or clock refraction while only that cached image is presented.
p='components/glass/TahoeGlass.qml';s=(root/p).read_text().replace('    property Item backdrop: null','    property Item backdrop: null\n    property bool trackingPaused:false\n    onTrackingPausedChanged:if(!trackingPaused){updatePosition();invalidate()}',1)
s=s.replace('enabled:root.visible &&','enabled:!root.trackingPaused && root.visible &&');write(p,s)
p='components/glass/BoxGlass.qml';s=(root/p).read_text().replace('    id: box','    id: box\n    property bool trackingPaused:false',1).replace('        sourceComponent: TahoeGlass {','        sourceComponent: TahoeGlass {\n            trackingPaused:box.trackingPaused',1);write(p,s)
p='ui/widgets/WidgetView.qml';s=(root/p).read_text().replace('    property bool desktopWidget:false','    property bool desktopWidget:false\n    property bool interactionPaused:false',1)
s=s.replace('    BoxGlass {','    BoxGlass {\n        trackingPaused:root.interactionPaused',1)
s=s.replace('        onLoaded: {','        onLoaded: {\n            if(loader.item.interactionPaused!==undefined)loader.item.interactionPaused=Qt.binding(function(){return root.interactionPaused})',1);write(p,s)
p='ui/desktop/DesktopLayer.qml';s=(root/p).read_text().replace('                        id:liveWidget','                        id:liveWidget\n                        interactionPaused:slot.dragging',1)
s=s.replace('slot.dragDX = centroid.scenePosition.x - centroid.scenePressPosition.x','slot.dragDX = Math.max(-slot.width,Math.min(stage.width,slot.spec.x+centroid.scenePosition.x-centroid.scenePressPosition.x))-slot.spec.x')
s=s.replace('slot.dragDY = centroid.scenePosition.y - centroid.scenePressPosition.y','slot.dragDY = Math.max(-slot.height,Math.min(stage.height,slot.spec.y+centroid.scenePosition.y-centroid.scenePressPosition.y))-slot.spec.y')
s=s.replace('enabled: stage.settled && !slot.dragging','enabled: stage.settled && !slot.dragging && !slot.resizing')
write(p,s)
# A slider may emit hundreds of pointer events. Publish one merged patch per
# frame and retain the existing file-write debounce. Structural actions flush
# pending edits before reading their list so no pending change can be lost.
p='services/WidgetState.qml';s=(root/p).read_text()
s=s.replace('    property var galleryDrag:null','''    property var pendingConfiguration:({})
    Timer{id:configurationFrame;interval:16;onTriggered:root.flushConfiguration()}
    function flushConfiguration(){
        const patches=root.pendingConfiguration,keys=Object.keys(patches)
        if(!keys.length)return
        root.pendingConfiguration={}
        for(const zone of ['desktop','notifCenter']){
            const list=(zone==='desktop' ? root.desktop:root.notifCenter).slice();let changed=false
            for(const key of keys){const patch=patches[key];if(patch.zone!==zone)continue
                const index=root.indexOfId(list,patch.id);if(index<0)continue
                const previous=list[index],next=Object.assign({},previous,patch.changes)
                if(Object.keys(patch.changes).some(field=>JSON.stringify(previous[field])!==JSON.stringify(next[field]))){list[index]=next;changed=true}
            }
            if(changed)root.setList(zone,list)
        }
    }
    onEditingIdChanged:root.flushConfiguration()
    onEditingZoneChanged:root.flushConfiguration()
    property var galleryDrag:null''',1)
s=s.replace('    function listOf(zone) {','    function listOf(zone) {\n        root.flushConfiguration()',1)
a=s.index('    function configure(zone,id,changes){');b=s.index('    function setImage(',a)
s=s[:a]+'''    function configure(zone,id,changes){
        zone=zone==='desktop' ? 'desktop':'notifCenter'
        if(!root.entryOf(zone,id))return
        const key=zone+':'+id,previous=root.pendingConfiguration[key]
        const merged=Object.assign({},previous?.changes || {},changes)
        root.pendingConfiguration[key]={zone:zone,id:id,changes:merged}
        if(!configurationFrame.running)configurationFrame.start()
    }
'''+s[b:];write(p,s)

# Commit the final dimensions before removing the local resize preview.
p='ui/widgets/WidgetResizeHandles.qml';s=(root/p).read_text()
s=s.replace('     root.cancel();if(WidgetState.resizingId===id)WidgetState.resizingId="";root.finished()\n     WidgetState.resizeWidgetTo(id,w,h,free)','     WidgetState.resizeWidgetTo(id,w,h,free)\n     root.cancel();if(WidgetState.resizingId===id)WidgetState.resizingId="";root.finished()',1);write(p,s)

p='ui/widgets/types/CreativeText.qml';s=(root/p).read_text()
s=s.replace('backdrop:{const shared=WidgetState.desktopBackdrop;if(shared && (!QsWindow.window?.screen || shared.monitorName===QsWindow.window.screen.name))return shared;return isSnapshot ? null:hostBackdrop}','backdrop:{if(root.isSnapshot)return null;const shared=WidgetState.desktopBackdrop;if(shared && shared.win===QsWindow.window)return shared;return hostBackdrop}',1)
s=s.replace('Connections{target:glyph.Window.window;ignoreUnknownSignals:true;', 'Connections{target:glyph.Window.window;enabled:root.visible && !root.isSnapshot;ignoreUnknownSignals:true;',1);write(p,s)
