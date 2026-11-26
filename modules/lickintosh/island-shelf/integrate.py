"""Extend the existing island; reuse its visibility, activity and privacy owners."""
import json,shutil,sys
from pathlib import Path
root=Path(sys.argv[1]);source=Path(sys.argv[3]) if len(sys.argv)>3 else Path(__file__).parent
shutil.copytree(source,root/'island-shelf',ignore=shutil.ignore_patterns('test_*','__pycache__','integrate.py'))
(root/'island-shelf').chmod(0o755)
for p in (root/'island-shelf').rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
p=root/'island-shelf/ShelfState.qml';(root/'services/ShelfState.qml').write_text(p.read_text().replace('@PYTHON@',sys.argv[2]));p.unlink()
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton ShelfState ShelfState.qml\n')
(root/'island-shelf/qmldir').write_text('\n'.join(name+' '+name+'.qml' for name in ['ShelfButton','ShelfHome','FileTray','ClipboardShelf','LyricsShelf','AudioShelf','WidgetLibrary','ActivitiesShelf','FloatingMusic','ShelfChoice','ShelfSlider','StayAwakeShelf','NotificationShelf','FloatingTray'])+'\n')
base=root/'rosa'
p=base/'services/IslandConfig.qml';s=p.read_text();spec={
 'floatingPlayerSize':dict(type='pick',def_='player',values=['mini','player','expanded']),
 'surfaceMode':dict(type='pick',def_='island',values=['island','notch']),
 'externalSurfaceMode':dict(type='pick',def_='island',values=['island','notch']),
 'shelfMaterial':dict(type='pick',def_='black',values=['black','glass','dynamic']),
 'shelfExpandedTabs':dict(type='bool',def_=False),
 'shelfAnimationMs':dict(type='int',def_=220,min=0,max=600),
 'shelfWidth':dict(type='int',def_=1000,min=600,max=1400),
 'shelfHeight':dict(type='int',def_=310,min=240,max=520),
 'shelfOpenOnHover':dict(type='bool',def_=False),
 'shelfHoverDelay':dict(type='int',def_=350,min=100,max=2000),
 'shelfCollapseDelay':dict(type='int',def_=350,min=100,max=2000),
 'shelfLyricsBlank':dict(type='bool',def_=True),
}
for i,key in enumerate(['media','calendar','weather','none'],1):
 spec['shelfSlot'+str(i)]=dict(type='pick',def_=key,values=['none','media','calendar','weather','focus','notes','performance','files'])
 spec['shelfWeight'+str(i)]=dict(type='int',def_=1,min=1,max=3)
lines=[]
for key,value in spec.items():
 value['def']=value.pop('def_');lines.append(key+': '+json.dumps(value)+',')
s=s.replace('        enabled:     {', '        '+('\n        '.join(lines))+'\n        enabled:     {',1)
s=s.replace('readonly property var groups: [','readonly property var groups: [\n        {key:"shelf",names:'+json.dumps(list(spec))+'},',1)
p.write_text(s)
labels={'floatingPlayerSize':'Floating player size','surfaceMode':'Display shape','externalSurfaceMode':'External display shape','shelfMaterial':'Expanded shelf material','shelfExpandedTabs':'Show expanded navigation tabs','shelfAnimationMs':'Shelf animation duration (ms)','shelfWidth':'Expanded shelf width','shelfHeight':'Expanded shelf height','shelfOpenOnHover':'Open shelf on hover','shelfHoverDelay':'Hover delay (ms)','shelfCollapseDelay':'Collapse delay (ms)','shelfLyricsBlank':'Keep lyrics blank when unavailable'}
for i in range(1,5):labels['shelfSlot'+str(i)]=f'Shelf widget {i}';labels['shelfWeight'+str(i)]=f'Widget {i} width'
p=base/'lang/en.json';d=json.loads(p.read_text());d['isle.sec.shelf']='Shelf and display style';d.update({'isle.o.'+k:v for k,v in labels.items()});d.update({'isle.v.'+x:x.title() for x in ['island','notch','calendar','notes','performance','files','none','black','glass','dynamic','weather','focus','media']});p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
p=base/'overlays/IslandDashboard.qml';s=p.read_text().replace('import qs.services','import "../../island-shelf"\nimport qs.services',1)
s=s.replace('implicitWidth: Math.min(output.width - 32, 1120)','implicitWidth: Math.min(output.width - 32, IslandConfig.s("shelfWidth"))')
s=s.replace('        Layout.maximumWidth: parent ? parent.width : implicitWidth','')
s=s.replace('ShellMotion.fade()', 'SettingsPreferences.accessibility.reduceMotion ? 0:IslandConfig.s("shelfAnimationMs")')
s=s.replace('implicitHeight: 306','implicitHeight: IslandConfig.s("shelfHeight")+20')
s=s.replace('readonly property int bodyHeight: 236','readonly property int bodyHeight: IslandConfig.s("shelfHeight")')
s=s.replace('property real capsuleTop: 3', 'readonly property bool attachedNotch:(output.name===Quickshell.screens[0]?.name ? IslandConfig.s("surfaceMode"):IslandConfig.s("externalSurfaceMode"))==="notch"\n    property real capsuleTop: 3')
s=s.replace('        HoverHandler { id: dashboardHover;', '        Rectangle{visible:panel.attachedNotch;anchors.top:parent.top;width:parent.width;height:30;color:body.color}\n        HoverHandler { id: dashboardHover;')
s=s.replace('mask: Region { item: body; radius: 30 }', 'mask: Region { item: body; radius: panel.attachedNotch ? 0:30 }')
s=s.replace('            Rectangle{anchors.fill:parent;', '            Rectangle{anchors.fill:parent;')
s=s.replace('property int page: 0','property var hub:null\n    property int page: 0')
s=s.replace("qsTr('Camera')]", "qsTr('Camera'),qsTr('Files'),qsTr('Clipboard'),qsTr('Widgets'),qsTr('Lyrics'),qsTr('Audio'),qsTr('Activities'),qsTr('Stay Awake')]")
s=s.replace('width: Math.max(1050,pageFrame.width)','width: panel.page===0 || panel.page>=6 ? pageFrame.width:Math.max(1050,pageFrame.width)')
s=s.replace('[overview, forecast, performance, media, notifications, cameraFull]', '[overview, forecast, performance, media, notifications, cameraFull, tray, clipboard, library, lyrics, audioApps, activities, awake]')
a=s.index('    Component {\n        id: overview');b=s.index('    Component { id: performance;',a)
s=s[:a]+'''    Component {id:overview;ShelfHome{onOpenPage:page=>panel.selectPage(page)}}
    Component {id:tray;FileTray{}}
    Component {id:clipboard;ClipboardShelf{}}
    Component {id:library;WidgetLibrary{onOpenPage:page=>panel.selectPage(page)}}
    Component {id:lyrics;LyricsShelf{}}
    Component {id:audioApps;AudioShelf{}}
    Component {id:awake;StayAwakeShelf{}}
    Component {id:activities;ActivitiesShelf{hub:panel.hub;onOpenPage:page=>panel.selectPage(page)}}

'''+s[b:]
a=s.index('    Component {\n        id: notifications');b=s.index('    component ForecastCell:',a)
s=s[:a]+'    Component{id:notifications;NotificationShelf{notices:panel.notices}}\n\n'+s[b:]
s=s.replace('color: "#ff000000"', 'color: IslandConfig.s("shelfMaterial")==="black" || !RenderingState.glassEnabled ? "#ff000000":"#45202024"')
s=s.replace('        HoverHandler { id: dashboardHover;', '        Rectangle{anchors.fill:parent;radius:30;visible:IslandConfig.s("shelfMaterial")==="dynamic" && RenderingState.glassEnabled;gradient:Gradient{GradientStop{position:0;color:"#ff000000"}GradientStop{position:.48;color:"#a0000000"}GradientStop{position:1;color:"#10000000"}}}\n        HoverHandler { id: dashboardHover;')
s=s.replace('                Layout.preferredHeight: tabs.implicitHeight', '                visible:IslandConfig.s("shelfExpandedTabs")\n                Layout.preferredHeight: visible ? tabs.implicitHeight:0')
s=s.replace('            anchors.margins: 18', '            anchors.margins: 18\n            anchors.bottomMargin:54',1)
# Navigation is kept inside the animated silhouette, avoiding a separate popup.
pos=s.index('    Component {id:overview;')
body_end=s.rfind('    }',0,pos)
s=s[:body_end]+'''        RowLayout {
            anchors.bottom:parent.bottom;anchors.bottomMargin:12;anchors.horizontalCenter:parent.horizontalCenter;spacing:5
            ShelfButton{visible:ShelfState.editing;text:qsTr("Done");onClicked:ShelfState.editing=false}
            ShelfButton{text:qsTr("Home");icon:"notch/home.svg";selected:panel.page===0;onClicked:panel.selectPage(0)}
            ShelfButton{text:qsTr("Files")+(ShelfState.items.length ? " · "+ShelfState.items.length:"");icon:"notch/inbox.svg";selected:panel.page===6;onClicked:panel.selectPage(6)}
            ShelfButton{text:qsTr("Widgets");icon:"notch/grid.svg";selected:panel.page===8;onClicked:panel.selectPage(8)}
            ShelfButton{text:qsTr("Media");icon:"notch/music.svg";selected:panel.page===3;onClicked:panel.selectPage(3)}
        }
'''+s[body_end:]
s=s.replace('    Shortcut { sequence:', '''    Connections{target:ShelfState;function onReveal(page){panel.selectPage(page)}}
    DropArea{anchors.fill:parent;keys:['text/uri-list'];onEntered:{panel.pointerChanged(true);panel.selectPage(6)}\n    onExited:panel.pointerChanged(false)\n    onDropped:drop=>{ShelfState.add(drop.urls);drop.acceptProposedAction()}}
    Shortcut { sequence:''',1)
p.write_text(s)
p=base/'overlays/IslandWindow.qml';s=p.read_text().replace('    readonly property bool inBar:', '''    readonly property bool attachedNotch:(win.modelData.name===Quickshell.screens[0]?.name ? IslandConfig.s("surfaceMode"):IslandConfig.s("externalSurfaceMode"))==="notch"
    readonly property bool inBar:''',1)
s=s.replace('active: win.visible && IslandConfig.s("dashboardEnabled") && (win.dashboardRequested || dashboardClose.running)', 'active: IslandConfig.s("dashboardEnabled") && !IslandBus.locked')
s=s.replace('            output: win.modelData','            output: win.modelData\n            hub:win.hub\n            visible:win.visible && (win.dashboardRequested || dashboardClose.running)',1)
s=s.replace('id: dashboardClose; interval: 250', 'id: dashboardClose; interval: NativeSettings.SettingsPreferences.accessibility.reduceMotion ? 1:IslandConfig.s("shelfAnimationMs")+50')
s=s.replace('        interval: 180','        interval: IslandConfig.s("shelfCollapseDelay")',1)
s=s.replace('readonly property int gap: win.inBar','readonly property int gap: win.attachedNotch ? 0 : win.inBar',1)
needle='''                color: Colors.alpha(win.bodyColor, IslandConfig.s("fill") / 100)'''
s=s.replace(needle,needle+'''\n                Rectangle{visible:win.attachedNotch;anchors.top:parent.top;width:parent.width;height:Math.min(parent.height/2,18);color:parent.color}''',1)
s=s.replace('    property bool forced: false','''    Timer{id:shelfHover;interval:IslandConfig.s("shelfHoverDelay");onTriggered:if(win.pointerIn && IslandConfig.s("shelfOpenOnHover"))win.dashboardRequested=true}
    onPointerInChanged:{if(win.pointerIn && IslandConfig.s("shelfOpenOnHover"))shelfHover.restart();else shelfHover.stop()}
    Connections{target:NativeSettings.ShelfState;function onCloseRequested(){win.dashboardRequested=false}
    function onReveal(page){if(win.presentationWanted){win.dashboardRequested=true}}}
    DropArea{ x:stage.x; y:stage.y; width:stage.width;height:stage.height;keys:['text/uri-list'];onEntered:{pointerLeave.stop();win.dashboardRequested=true;NativeSettings.ShelfState.reveal(6)}\n    onDropped:drop=>{NativeSettings.ShelfState.add(drop.urls);drop.acceptProposedAction()}}
    property bool forced: false''',1)
p.write_text(s)
p=root/'shell.qml'
s=p.read_text();s='import "island-shelf"\n'+s
s=s.replace('    id: appRoot','    id: appRoot\n    FloatingMusic {}\n    FloatingTray {}',1)
p.write_text(s)
