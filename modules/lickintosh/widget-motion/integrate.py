from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
def save(name,s):
 p=root/name;p.chmod(p.stat().st_mode|0o200);p.write_text(s)
(root/'ui/widgets/types/PersonalClock.qml').write_text((here/'PersonalClock.qml').read_text());p=root/'ui/widgets/types/qmldir';save('ui/widgets/types/qmldir',p.read_text()+'\nPersonalClock PersonalClock.qml\n')
p=root/'services/WidgetRegistry.qml';save('services/WidgetRegistry.qml',p.read_text().replace('readonly property var types: [','''readonly property var types: [
        {type:'personalclock',title:'Personal Clock',file:'PersonalClock',sizes:['s','m','l'],icon:'notch/clock.svg',tint:'#0a84ff'},''',1))
p=root/'ui/widgets/WidgetSettings.qml';s=p.read_text();anchor='     RowLayout{visible:root.entry.type===\'image\'';i=s.index(anchor)
s=s[:i]+'''     ColumnLayout{visible:root.entry.type==='personalclock';Layout.fillWidth:true;spacing:12
      TahoeCombo{Layout.fillWidth:true;model:LockClockStyle.styles.map(style=>style.name);currentIndex:root.entry.clockStyle || 0;onActivated:index=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockStyle:index,clockFont:''})}
      TahoeField{Layout.fillWidth:true;text:root.entry.clockFont || '';placeholderText:'Custom font family (optional)';onEditingFinished:WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockFont:text.trim()})}
      ConfigSlider{text:'Font size';from:24;to:160;decimals:0;value:root.entry.clockSize || 76;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockSize:Math.round(value)})}
      ConfigSlider{text:'Weight';from:0;to:1;decimals:2;value:root.entry.clockWeight ?? .6;onMoved:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockWeight:value})}
      ConfigSwitch{text:'Show date';checked:root.entry.clockDate!==false;onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockDate:value})}
      ConfigSwitch{text:'Show seconds';checked:!!root.entry.clockSeconds;onToggled:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockSeconds:value})}
      ColorSetting{label:'Clock color';value:root.entry.clockColor || Theme.textPrimary;onPicked:value=>WidgetState.configure(WidgetState.editingZone,WidgetState.editingId,{clockColor:String(value)})}
     }
'''+s[i:];s='import qs.ui.settings.widgets\n'+s;save('ui/widgets/WidgetSettings.qml',s)
p=root/'ui/desktop/DesktopLayer.qml';s=p.read_text();s=s.replace('slot.dragging = false\n                            slot.dragDX = 0\n                            slot.dragDY = 0\n                            WidgetState.moveWidget(slot.modelData.id, nx, ny)','WidgetState.moveWidget(slot.modelData.id, nx, ny)\n                            slot.dragDX = 0\n                            slot.dragDY = 0\n                            slot.dragging = false')
# Cache the complete widget texture while dragging, avoiding repeated shader
# composition for the same widget on each pointer move.
s=s.replace('                    WidgetView {\n                        widgetData: slot.spec\n                    }','''                    WidgetView {
                        id:liveWidget
                        widgetData: slot.spec
                    }
                    ShaderEffectSource{
                        anchors.fill:parent;sourceItem:liveWidget
                        live:false;hideSource:slot.dragging;visible:slot.dragging
                        onVisibleChanged:if(visible)scheduleUpdate()
                    }''');save('ui/desktop/DesktopLayer.qml',s)
p=root/'ui/widgets/WidgetGallery.qml';s=p.read_text();s=s.replace('Drag.active:drag.active;Drag.dragType:Drag.Automatic','Drag.dragType:Drag.None');a=s.index('              MouseArea{id:addMouse;');z=s.index('\n             }',a)
s=s[:a]+'''              MouseArea{
               id:addMouse;anchors.fill:parent;hoverEnabled:true;preventStealing:true;cursorShape:Qt.PointingHandCursor
               property real startX:0;property real startY:0;property bool dragged:false
               function updateDrag(event){
                const point=addMouse.mapToItem(win.contentItem,event.x,event.y)
                const gx=point.x,gy=win.screen.height-win.height+point.y
                WidgetState.galleryDrag={type:section.modelData.type,size:tile.modelData.size,variant:tile.modelData.variant || '',theme:WidgetState.galleryTheme,x:gx,y:gy,screen:win.screen.name,outside:point.y<panel.y}
               }
               onPressed:event=>{startX=event.x;startY=event.y;dragged=false}
               onPositionChanged:event=>{if(pressed && (dragged || Math.hypot(event.x-startX,event.y-startY)>12)){dragged=true;updateDrag(event)}}
               onReleased:event=>{
                if(dragged){updateDrag(event);const d=WidgetState.galleryDrag;if(d && d.outside){const shape=WidgetState.sizeOf(d.size);WidgetState.addWidgetAt('desktop',d.type,d.size,d.variant,d.x-shape.w/2,d.y-shape.h/2,d.theme)}}
                WidgetState.galleryDrag=null
               }
               onCanceled:WidgetState.galleryDrag=null
               onClicked:if(!dragged)WidgetState.addWidget(WidgetState.galleryZone,section.modelData.type,tile.modelData.size,tile.modelData.variant,WidgetState.galleryTheme)

              }
'''+s[z:];save('ui/widgets/WidgetGallery.qml',s)

# Pointer grab stays on the gallery surface throughout the drag. No native
# layer-shell DnD dependency, which differs between Sway and Hyprland.
p=root/'services/WidgetState.qml';save('services/WidgetState.qml',p.read_text().replace('id: root','id: root\n    property var galleryDrag:null',1))
p=root/'ui/desktop/DesktopLayer.qml';s=p.read_text();anchor='            DropArea {\n                anchors.fill: parent\n                keys: ["text/plain"]'
i=s.index(anchor);s=s[:i]+'''            Item{
                readonly property var dragSpec:WidgetState.galleryDrag
                visible:!!dragSpec && dragSpec.outside && dragSpec.screen===win.screen.name
                x:dragSpec ? WidgetState.snap(dragSpec.size,dragSpec.x-WidgetState.sizeOf(dragSpec.size).w/2,dragSpec.y-WidgetState.sizeOf(dragSpec.size).h/2).x:0
                y:dragSpec ? WidgetState.snap(dragSpec.size,dragSpec.x-WidgetState.sizeOf(dragSpec.size).w/2,dragSpec.y-WidgetState.sizeOf(dragSpec.size).h/2).y:0
                width:dragSpec ? WidgetState.sizeOf(dragSpec.size).w:0;height:dragSpec ? WidgetState.sizeOf(dragSpec.size).h:0
                opacity:.65;z:500
                WidgetView{visible:!!parent.dragSpec;widgetData:parent.dragSpec || ({type:'personalclock',size:'s',theme:'transparent'})}
            }
'''+s[i:];save('ui/desktop/DesktopLayer.qml',s)
# Transparent means neither glass nor a background/border, independently of
# light/dark text palette and of the widget's own content.
p=root/'ui/widgets/WidgetView.qml';s=p.read_text().replace('visible: !palette.glass','visible: !palette.glass && root.style!=="transparent"');save('ui/widgets/WidgetView.qml',s)
for name in ['ui/widgets/WidgetGallery.qml','ui/widgets/WidgetSettings.qml','ui/widgets/DesktopSettings.qml','ui/settings/pages/AppearanceControls.qml','settingsapp/SettingsContent.qml']:
 p=root/name
 if not p.exists():continue
 s=p.read_text()
 for old,new in [("'Clear','Tinted'","'Clear','Tinted','Transparent'"),("'clear','tinted'","'clear','tinted','transparent'"),("'Dark','Tinted'","'Dark','Tinted','Transparent'"),("'dark','tinted'","'dark','tinted','transparent'")]:s=s.replace(old,new)
 save(name,s)
p=root/'ui/widgets/WidgetSnapshot.qml';s=p.read_text().replace('    Rectangle {\n        anchors.fill: parent','    Rectangle {\n        visible:root.style!=="transparent"\n        anchors.fill: parent',1);save('ui/widgets/WidgetSnapshot.qml',s)
p=root/'services/WidgetState.qml';s=p.read_text().replace('                { label: I18n.tr("Glass"), action:', '                { label: I18n.tr("Transparent"), action: "theme:transparent", checkable: true, checked: current === "transparent" },\n                { label: I18n.tr("Glass"), action:',1);save('services/WidgetState.qml',s)
