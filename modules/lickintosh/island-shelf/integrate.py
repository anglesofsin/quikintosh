"""Extend the existing island; reuse its visibility, activity and privacy owners."""
import json,shutil,sys
from pathlib import Path
root=Path(sys.argv[1]);source=Path(sys.argv[3]) if len(sys.argv)>3 else Path(__file__).parent
shutil.copytree(source,root/'island-shelf',ignore=shutil.ignore_patterns('test_*','__pycache__','integrate.py'))
(root/'island-shelf').chmod(0o755)
for p in (root/'island-shelf').rglob('*'):p.chmod(0o755 if p.is_dir() else 0o644)
p=root/'island-shelf/ShelfState.qml';(root/'services/ShelfState.qml').write_text(p.read_text().replace('@PYTHON@',sys.argv[2]));p.unlink()
p=root/'services/qmldir';p.write_text(p.read_text()+'\nsingleton ShelfState ShelfState.qml\n')
(root/'island-shelf/qmldir').write_text('singleton ShelfStyle ShelfStyle.qml\n'+'\n'.join(name+' '+name+'.qml' for name in ['ShelfMedia','ShelfFocus','ShelfNotes','ShelfPlayback','ShelfForecast','ShelfStats','ShelfCamera','ShelfIcon','ShelfButton','ShelfCalendar','ShelfWeather','ShelfHome','FileTray','ClipboardShelf','LyricsShelf','AudioShelf','WidgetLibrary','ActivitiesShelf','FloatingMusic','ShelfChoice','ShelfSlider','StayAwakeShelf','NotificationShelf','FloatingTray','ShelfAppearance'])+'\n')
base=root/'rosa'
p=base/'services/IslandConfig.qml';s=p.read_text();spec={
 'interactionPreset':dict(type='pick',def_='droppy',values=['droppy','classic','custom']),
 'floatingPlayerSize':dict(type='pick',def_='player',values=['mini','player','expanded']),
 'surfaceMode':dict(type='pick',def_='island',values=['island','notch']),
 'externalSurfaceMode':dict(type='pick',def_='island',values=['island','notch']),
 'shelfMaterial':dict(type='pick',def_='dynamic',values=['black','glass','dynamic']),
 'shelfWidgetCards':dict(type='bool',def_=False),
 'shelfExpandedTabs':dict(type='bool',def_=False),
 'shelfAnimationMs':dict(type='int',def_=220,min=0,max=600),
 'shelfAdaptiveWidth':dict(type='bool',def_=True),
 'shelfWidth':dict(type='int',def_=1140,min=600,max=1400),
 'shelfHeight':dict(type='int',def_=216,min=200,max=520),
 'shelfOpenOnHover':dict(type='bool',def_=True),
 'shelfHoverDelay':dict(type='int',def_=250,min=100,max=2000),
 'shelfCollapseDelay':dict(type='int',def_=350,min=100,max=2000),
 'shelfLyricsBlank':dict(type='bool',def_=True),
}
for i,key in enumerate(['media','calendar','weather','none'],1):
 spec['shelfSlot'+str(i)]=dict(type='pick',def_=key,values=['none','media','calendar','weather','focus','notes','performance','files','clipboard','audio','awake','storage','camera','notifications'])
 spec['shelfWeight'+str(i)]=dict(type='int',def_=1,min=1,max=3)
lines=[]
for key,value in spec.items():
 value['def']=value.pop('def_');lines.append(key+': '+json.dumps(value)+',')
s=s.replace('        enabled:     {', '        '+('\n        '.join(lines))+'\n        enabled:     {',1)
s=s.replace('readonly property var groups: [','readonly property var groups: [\n        {key:"shelf",names:'+json.dumps(list(spec))+'},',1)
p.write_text(s)
labels={'interactionPreset':'Interaction preset','shelfAdaptiveWidth':'Fit width to Home widgets','shelfWidgetCards':'Widget cards','floatingPlayerSize':'Floating player size','surfaceMode':'Display shape','externalSurfaceMode':'External display shape','shelfMaterial':'Expanded shelf material','shelfExpandedTabs':'Show expanded navigation tabs','shelfAnimationMs':'Shelf animation duration (ms)','shelfWidth':'Expanded shelf width','shelfHeight':'Expanded shelf height','shelfOpenOnHover':'Open shelf on hover','shelfHoverDelay':'Hover delay (ms)','shelfCollapseDelay':'Collapse delay (ms)','shelfLyricsBlank':'Keep lyrics blank when unavailable'}
for i in range(1,5):labels['shelfSlot'+str(i)]=f'Shelf widget {i}';labels['shelfWeight'+str(i)]=f'Widget {i} width'
p=base/'lang/en.json';d=json.loads(p.read_text());d['isle.sec.shelf']='Shelf behavior and motion';d.update({'isle.o.'+k:v for k,v in labels.items()});d.update({'isle.v.'+x:x.title() for x in ['droppy','classic','custom','island','notch','calendar','notes','performance','files','none','black','glass','dynamic','weather','focus','media']});p.write_text(json.dumps(d,ensure_ascii=False,indent=2))
p=base/'overlays/IslandDashboard.qml';s=p.read_text().replace('import qs.services','import "../../island-shelf"\nimport qs.services',1)
s=s.replace('implicitWidth: Math.min(output.width - 32, 1120)','implicitWidth: Math.min(output.width - 32, panel.page===13 ? 380:panel.page===0 && IslandConfig.s("shelfAdaptiveWidth") ? Math.min(IslandConfig.s("shelfWidth"),Math.max(380,[1,2,3,4].filter(i=>IslandConfig.s("shelfSlot"+i)!=="none").length*380)):IslandConfig.s("shelfWidth"))')
s=s.replace('        Layout.maximumWidth: parent ? parent.width : implicitWidth','')
s=s.replace('ShellMotion.fade()', 'SettingsPreferences.accessibility.reduceMotion ? 0:IslandConfig.s("shelfAnimationMs")')
s=s.replace('property int page: 0', 'readonly property int pageWidth:({1:560,2:540,3:460,4:480,5:480,6:820,7:1000,8:1000,9:620,10:440,11:580,12:500,13:(panel.detailWidget==="calendar" ? 620:380)})[page] || IslandConfig.s("shelfWidth")\n    property int page: 0')
s=s.replace('panel.page===13 ? 380:panel.page===0','panel.page!==0 ? panel.pageWidth:panel.page===0')
s=s.replace('implicitHeight: 306' ,'implicitHeight: bodyHeight+72')
s=s.replace('readonly property int bodyHeight: 236','readonly property int bodyHeight: panel.page===8 ? Math.min(output.height-80,ShelfState.editing ? 440:310):({1:336,4:300,5:300,6:280,7:300,9:330,10:300,11:300,12:216})[panel.page] || IslandConfig.s("shelfHeight")')
s=s.replace('property real capsuleTop: 3', 'readonly property bool attachedNotch:(output.name===Quickshell.screens[0]?.name ? IslandConfig.s("surfaceMode"):IslandConfig.s("externalSurfaceMode"))==="notch"\n    property real capsuleTop: 3')
s=s.replace('        HoverHandler { id: dashboardHover;', '        Rectangle{visible:panel.attachedNotch;anchors.top:parent.top;width:parent.width;height:30;color:body.color}\n        HoverHandler { id: dashboardHover;')
s=s.replace('mask: Region { item: body; radius: 30 }', 'mask: Region { item: body; radius: panel.attachedNotch ? 0:52; Region { item: navigation; radius: 22 } }')
s=s.replace('            Rectangle{anchors.fill:parent;', '            Rectangle{anchors.fill:parent;')
s=s.replace('property int page: 0','property var hub:null\n    property string detailWidget:"calendar"\n    property int page: 0')
s=s.replace('    property int page: 0', '    property int page: 0\n    readonly property bool editorActive:page===8 && ShelfState.editing && expanded && visible\n    onEditorActiveChanged:ShelfState.setEditor(output.name,editorActive)\n    Component.onDestruction:ShelfState.setEditor(output.name,false)\n')
s=s.replace('running: panel.expanded && panel.entered', 'running: panel.expanded && panel.entered && !ShelfState.holdOpen')
s=s.replace('if (!monitor || !panel.expanded) return', 'if (!monitor || !panel.expanded || ShelfState.holdOpen) return')
s=s.replace('onActivated: panel.dismissed()', 'onActivated: {ShelfState.editing=false;panel.dismissed()}')

s=s.replace("qsTr('Camera')]", "qsTr('Camera'),qsTr('Files'),qsTr('Clipboard'),qsTr('Widgets'),qsTr('Lyrics'),qsTr('Audio'),qsTr('Activities'),qsTr('Stay Awake')]")
s=s.replace('width: Math.max(1050,pageFrame.width)','width: pageFrame.width')
s=s.replace('scale: Math.min(1,pageFrame.width / width)','scale: 1')
s=s.replace('id: pageFrame','id: pageFrame;clip:true')
s=s.replace('[overview, forecast, performance, media, notifications, cameraFull]', '[overview, forecast, performance, media, notifications, cameraFull, tray, clipboard, library, lyrics, audioApps, activities, awake, widgetDetail]')
a=s.index('    Component {\n        id: overview');b=s.index('    Component { id: performance;',a)
s=s[:a]+'''    Component {id:overview;ShelfHome{onOpenPage:page=>panel.selectPage(page)}}
    Component {id:tray;FileTray{}}
    Component {id:clipboard;ClipboardShelf{}}
    Component {id:library;WidgetLibrary{onOpenPage:page=>panel.selectPage(page);onOpenWidget:key=>{panel.detailWidget=key;panel.selectPage(13)}}}\n    Component{id:widgetDetail;ShelfHome{slots:[panel.detailWidget];onOpenPage:page=>panel.selectPage(page)}}
    Component {id:lyrics;LyricsShelf{}}
    Component {id:audioApps;AudioShelf{}}
    Component {id:awake;StayAwakeShelf{}}
    Component {id:activities;ActivitiesShelf{hub:panel.hub;onOpenPage:page=>panel.selectPage(page)}}

'''+s[b:]
a=s.index('    Component {\n        id: notifications');b=s.index('    component ForecastCell:',a)
s=s[:a]+'    Component{id:notifications;NotificationShelf{notices:panel.notices}}\n\n'+s[b:]
a=s.index('    Component {\n        id: media');b=s.index('    Component{id:notifications;',a)
s=s[:a]+'    Component{id:media;ShelfMedia{}}\n\n'+s[b:]
a=s.index('    Component {\n        id: forecast');b=s.index('    Component {\n        id: cameraFull',a)
s=s[:a]+'    Component{id:forecast;ShelfForecast{}}\n\n'+s[b:]
a=s.index('    Component {\n        id: cameraFull');s=s[:a]+'    Component{id:cameraFull;ShelfCamera{}}\n}\n'
s=s.replace('Component { id: performance; PerformancePage {} }','Component{id:performance;ShelfStats{}}')
s=s.replace('color: "#ff000000"', 'color: IslandConfig.s("shelfMaterial")==="black" || !RenderingState.glassEnabled ? "#ff000000":IslandConfig.s("shelfMaterial")==="dynamic" ? "#04000000":"#18202024"')
s=s.replace('        HoverHandler { id: dashboardHover;', '        Rectangle{anchors.fill:parent;radius:52;visible:IslandConfig.s("shelfMaterial")==="dynamic" && RenderingState.glassEnabled;gradient:Gradient{GradientStop{position:0;color:"#ff000000"}GradientStop{position:.48;color:"#ee000000"}GradientStop{position:1;color:"#00000000"}}}\n        HoverHandler { id: dashboardHover;')
s=s.replace('radius: Math.min(30, height / 2)', 'radius: Math.min(52, height / 2)')
s=s.replace('border.color: "#32ffffff"','border.color: "#12ffffff"')
s=s.replace('                Layout.preferredHeight: tabs.implicitHeight', '                visible:IslandConfig.s("shelfExpandedTabs")\n                Layout.preferredHeight: visible ? tabs.implicitHeight:0')
s=s.replace('            anchors.margins: 18', '            anchors.margins: 22',1)
# The navigation belongs to the same window and input mask as the island. It
# follows the morph, so the gap never creates a second popup or focus owner.
pos=s.index('    Component {id:overview;')
s=s[:pos]+'''    Rectangle {
        id:navigation
        anchors.horizontalCenter:parent.horizontalCenter
        y:body.height+18
        implicitWidth:navigationRow.implicitWidth+12;implicitHeight:44
        radius:22;color:"#eb151517";border.width:1;border.color:"#26ffffff"
        opacity:panel.expandedBody && body.height>panel.bodyHeight-4 ? 1:0
        visible:opacity>0.001;enabled:panel.expandedBody
        Behavior on opacity{NumberAnimation{duration:SettingsPreferences.accessibility.reduceMotion ? 0:120}}
        HoverHandler{onHoveredChanged:panel.pointerChanged(hovered)}
        RowLayout{id:navigationRow;anchors.centerIn:parent;spacing:3
            ShelfButton{implicitWidth:44;implicitHeight:36;icon:"notch/home.svg";accessibleLabel:qsTr("Home");selected:panel.page===0;onClicked:panel.selectPage(0)}
            ShelfButton{implicitWidth:44;implicitHeight:36;icon:"notch/inbox.svg";accessibleLabel:qsTr("File tray");badge:ShelfState.items.length;selected:panel.page===6;onClicked:panel.selectPage(6)}
            ShelfButton{implicitWidth:44;implicitHeight:36;icon:"notch/grid.svg";accessibleLabel:qsTr("Widgets");selected:panel.page===8;onClicked:panel.selectPage(8)}
            ShelfButton{visible:ShelfState.editing && panel.page!==8;text:qsTr("Done");icon:"notch/check.svg";onClicked:ShelfState.editing=false}
        }
    }
'''+s[pos:]
s=s.replace('y > body.height)', 'y > body.height+66)')

s=s.replace('    Shortcut { sequence:', '''    Connections{target:ShelfState;function onReveal(page){panel.selectPage(page)}}
    DropArea{anchors.fill:parent;keys:['text/uri-list'];onEntered:{panel.pointerChanged(true);panel.selectPage(6)}\n    onExited:panel.pointerChanged(false)\n    onDropped:drop=>{ShelfState.add(drop.urls);drop.acceptProposedAction()}}
    Shortcut { sequence:''',1)
p.write_text(s)
p=base/'overlays/IslandWindow.qml';s=p.read_text().replace('    readonly property bool inBar:', '''    readonly property bool attachedNotch:(win.modelData.name===Quickshell.screens[0]?.name ? IslandConfig.s("surfaceMode"):IslandConfig.s("externalSurfaceMode"))==="notch"
    readonly property bool inBar:''',1)
s=s.replace('active: win.visible && IslandConfig.s("dashboardEnabled") && (win.dashboardRequested || dashboardClose.running)', 'active: IslandConfig.s("dashboardEnabled") && !IslandBus.locked')
s=s.replace('            output: win.modelData','            output: win.modelData\n            hub:win.hub\n            visible:win.visible && (win.dashboardRequested || dashboardClose.running)',1)
s=s.replace('id: dashboardClose; interval: 250', 'id: dashboardClose; interval: NativeSettings.SettingsPreferences.accessibility.reduceMotion ? 1:IslandConfig.s("shelfAnimationMs")+50')
s=s.replace('if (win.pointerIn || win.dashboardPointerInside) return;', 'if (win.pointerIn || win.dashboardPointerInside || NativeSettings.ShelfState.holdOpen) return;')
s=s.replace('if(!presentationWanted){win.dashboardRequested=false;', 'if(!presentationWanted){NativeSettings.ShelfState.editing=false;win.dashboardRequested=false;')
s=s.replace('        interval: 180' ,'        interval: IslandConfig.s("shelfCollapseDelay")',1)
s=s.replace('readonly property int gap: win.inBar','readonly property int gap: win.attachedNotch ? 0 : win.inBar',1)
needle='''                color: Colors.alpha(win.bodyColor, IslandConfig.s("fill") / 100)'''
s=s.replace(needle,needle+'''\n                Rectangle{visible:win.attachedNotch;anchors.top:parent.top;width:parent.width;height:Math.min(parent.height/2,18);color:parent.color}''',1)
s=s.replace('                onTapped: {\n                    if (win.wide) {', '                onTapped: {\n                    if(IslandConfig.s("interactionPreset")==="droppy" && IslandConfig.s("dashboardEnabled")){\n                        win.dashboardRequested=!win.dashboardRequested;\n                        return;\n                    }\n                    if (win.wide) {',1)
s=s.replace('    property bool forced: false','''    Connections{target:IslandConfig;function onStyleChanged(){if(!IslandConfig.s("dashboardEnabled"))win.dashboardRequested=false}}
    Timer{id:shelfHover;interval:IslandConfig.s("shelfHoverDelay");onTriggered:if(IslandConfig.s("dashboardEnabled") && win.pointerIn && (IslandConfig.s("interactionPreset")==="droppy" || (IslandConfig.s("interactionPreset")==="custom" && IslandConfig.s("shelfOpenOnHover"))))win.dashboardRequested=true}
    onPointerInChanged:{if(win.pointerIn && (IslandConfig.s("interactionPreset")==="droppy" || (IslandConfig.s("interactionPreset")==="custom" && IslandConfig.s("shelfOpenOnHover"))))shelfHover.restart();else shelfHover.stop()}
    Connections{target:NativeSettings.ShelfState;function onHoldOpenChanged(){if(!NativeSettings.ShelfState.holdOpen && win.dashboardRequested)pointerLeave.restart()}\n    function onCloseRequested(){NativeSettings.ShelfState.editing=false;win.dashboardRequested=false}
    function onReveal(page){if(win.presentationWanted){win.dashboardRequested=true}}}
    DropArea{ x:stage.x; y:stage.y; width:stage.width;height:stage.height;keys:['text/uri-list'];onEntered:{pointerLeave.stop();win.dashboardRequested=true;NativeSettings.ShelfState.reveal(6)}\n    onDropped:drop=>{NativeSettings.ShelfState.add(drop.urls);drop.acceptProposedAction()}}
    property bool forced: false''',1)
# Keep the compact surface covered until both morphs have reached their rest.
s=s.replace('    onDashboardRequestedChanged: if (dashboardRequested) dashboardClose.stop(); else dashboardClose.restart()', '    property bool dashboardCover:false\n    function collapseActivity(){force.stop();windupHold.stop();win.forced=false;win.hub.mediaBig=false;win.hub.voicePeek=false;win.hub.pinned=false;win.hushed=true;win.opened=false}\n    onDashboardRequestedChanged:{\n        if(dashboardRequested && !IslandConfig.s("dashboardEnabled")){dashboardRequested=false;return}\n        if(dashboardRequested){dashboardCover=true;collapseActivity();dashboardClose.stop()}\n        else dashboardClose.restart()\n    }\n')
s=s.replace('id: dashboardClose; interval: NativeSettings.SettingsPreferences.accessibility.reduceMotion ? 1:IslandConfig.s("shelfAnimationMs")+50', 'id: dashboardClose; interval: NativeSettings.SettingsPreferences.accessibility.reduceMotion ? 1:IslandConfig.s("shelfAnimationMs")+50;onTriggered:{if(Math.abs(morph.value)>.015){dashboardClose.restart();return}win.dashboardCover=false}')
s=s.replace('win.dashboardRequested || dashboardClose.running','win.dashboardCover')
s=s.replace('win.wideKind !== "" && !win.seeking','win.wideKind !== "" && !win.seeking && !win.dashboardCover')
s=s.replace('            win.dashboardRequested = false;\n            win.forced = false;\n            win.hub.voicePeek = false;', '            win.dashboardRequested=false;win.collapseActivity();')
s=s.replace('                    opacity: {\n                        if (!win.bigMotion)', '                    opacity: {\n                        if(!win.opened || win.dashboardCover)return 0;\n                        if (!win.bigMotion)',1)
p.write_text(s)
p=root/'shell.qml'
s=p.read_text();s='import "island-shelf"\n'+s
s=s.replace('    id: appRoot','    id: appRoot\n    FloatingMusic {}\n    FloatingTray {}',1)
p.write_text(s)

# Visual shape/material controls precede the advanced schema rows in Settings.
p=root/'ui/settings/pages/RosaPage.qml';s=p.read_text().replace('import QtQuick','import "../../../island-shelf"\nimport QtQuick',1)
s=s.replace('    property bool weatherLocationRevealed:false','    property bool weatherLocationRevealed:false\n    ContentSection{ShelfAppearance{Layout.fillWidth:true;settingsPage:true}}',1)
s=s.replace('model: group.modelData.names.filter(name=>name!=="eatPopups")', 'model: group.modelData.names.filter(name=>name!=="eatPopups" && !["surfaceMode","externalSurfaceMode","shelfMaterial","shelfWidth","shelfHeight","shelfSlot1","shelfSlot2","shelfSlot3","shelfSlot4","shelfWeight1","shelfWeight2","shelfWeight3","shelfWeight4"].includes(name))')
s=s.replace('    ContentSection {\n        title: I18n.tr("Dashboard")', '    ContentSection {\n        title: I18n.tr("Dashboard")\n        TahoeButton{text:I18n.tr("Customize shelf…");onClicked:Quickshell.execDetached(["quickintosh","ipc","call","shelf","open","8"])}',1)
p.write_text(s)

# Shelf graphs use the shared graph's explicit transparent surface option.
sparkline = root / "ui/topbar/notch/dashboard/Sparkline.qml"
if sparkline.exists():
    text = sparkline.read_text().replace("property color lineColor: Theme.accent", "property color lineColor: Theme.accent\n    property color backgroundColor: \"#141414\"")
    sparkline.write_text(text.replace('color: "#141414"', 'color: root.backgroundColor'))

# Apply compact presentation after the existing ownership/interaction patches.
import runpy
runpy.run_path(str(source / 'compact.py'))['integrate'](root)

# Expanded activity player shares the same capability-aware media presentation.
p=root/'rosa/overlays/cards/MediaCard.qml'
p.write_text('''import QtQuick
import "../../../island-shelf"
Item {
 id:root
 property color tint:"white"
 property var demo:({})
 property bool big:false
 readonly property Item hero:player.hero
 ShelfMedia{id:player;anchors.fill:parent;demo:root.demo}
}
''')

runpy.run_path(str(source / 'interaction.py'))['integrate'](root)
runpy.run_path(str(source / 'motion.py'))['integrate'](root)
runpy.run_path(str(source / 'tab_response.py'))['integrate'](root)
runpy.run_path(str(source / 'replica.py'))['integrate'](root)
