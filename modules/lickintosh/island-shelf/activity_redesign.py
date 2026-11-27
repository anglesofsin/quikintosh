"""Install new event surfaces without changing protected call/media/CPU/privacy/shot views."""
from pathlib import Path
import json,ast,re

def write(path,text):
 if path.is_symlink():path.unlink()
 path.write_text(text)

def integrate(root):
 root=Path(root)
 spec=json.loads((root/'island-shelf/icon_policy.json').read_text())
 generated=ast.literal_eval(re.search(r'generated:\((\{.*?\})\)',(root/'island-shelf/ShelfIcon.qml').read_text(),re.S)[1])
 missing=[icon for icon in spec['icons'] if not ((root/'island-shelf/icons/ai'/(generated[icon]+'.png')).is_file() if icon in generated else (root/'assets/icons/notch'/(icon+'.svg')).is_file())]
 if missing:raise ValueError('Missing activity icon assets: '+', '.join(missing))
 policy=root/'island-shelf/ActivityIconPolicy.qml';policy.write_text(policy.read_text().replace('@ICON_SPEC@',json.dumps(spec)))
 p=root/'island-shelf/qmldir'
 p.write_text(p.read_text()+'\nActivitySurface ActivitySurface.qml\nActivityData ActivityData.qml\nsingleton ActivityIconPolicy ActivityIconPolicy.qml\nIconSettings IconSettings.qml\n')
 p=root/'rosa/overlays/Island.qml';s=p.read_text().replace('    id: root','''    id: root
    readonly property var shelfActivity:ShelfState.activities.length ? ShelfState.activities[0]:null
    property int activityTrayCount:ShelfState.items.length
    Connections{target:ShelfState;function onItemsChanged(){const count=ShelfState.items.length;if(count>root.activityTrayCount && !VoiceCalls.active)root.flash("tray","",String(count),-1,true);root.activityTrayCount=count}}
''',1);s=s.replace('        if (root.restingClock)','        if(root.shelfActivity)return root.shelfActivity.kind || \"task\";\n        if (root.restingClock)',1);write(p,s)
 p=root/'rosa/overlays/IslandPill.qml';s=p.read_text()
 s=s.replace('    id: pill','''    id: pill
    ActivityData{id:eventData;kind:pill.flashing ? pill.flashKind:pill.kind;label:pill.flashText;fraction:pill.flashFraction;demo:pill.activityDemo;context:pill.activityContext;notification:pill.activityNotification}
    property var activityDemo:({})
    property var activityContext:({})
    property var activityNotification:({})
    readonly property bool newEvent:eventData.supported
    readonly property color eventTint:eventData.value.color || "white"
    ActivitySurface{id:eventSurface;objectName:'activity-compact';interactive:false;anchors.centerIn:parent;activity:eventData.value;width:pill.width;height:pill.height;visible:pill.newEvent;onAction:(name,value)=>eventData.action(name)}
''',1)
 s=s.replace('implicitWidth: pill.kind === "voice" ?', 'implicitWidth: pill.newEvent ? eventSurface.preferredCompactWidth:pill.kind === "voice" ?',1)
 s=s.replace('visible:pill.persistentIndicator','visible:!pill.newEvent && pill.persistentIndicator',1)
 # The legacy painting root has properties before anchors in some source versions.
 a=s.index('    Item {',s.index('    onFlashKindChanged:'))
 s=s[:a]+s[a:].replace('    Item {','    Item {\n        visible:!pill.newEvent',1)
 write(p,s)
 p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
 s=s.replace('    readonly property string wideKind: {','    readonly property string wideKind: {\n        if(!["clock","voice","media","sys","shot","gta","jarvis",""].includes(win.hub.kind))return win.hub.kind;',1)
 s=s.replace('target: win.hub.kind === "voice" || pill.compactMedia ? pill.implicitWidth', 'target: pill.newEvent || win.hub.kind === "voice" || pill.compactMedia ? pill.implicitWidth',1)
 s=s.replace('readonly property bool droppyCompact:IslandConfig.s("interactionPreset")==="droppy" && !win.wide && !win.seeking','readonly property bool droppyCompact:(pill.newEvent || (IslandConfig.s("interactionPreset")==="droppy" && !win.wide)) && !win.seeking',1)
 s=s.replace('target: win.big ? IslandConfig.s("mediaBigHeight")','target: pill.newEvent ? (win.wideKind==="notif" ? Math.max(88,body.want+24):64):win.big ? IslandConfig.s("mediaBigHeight")',1)
 s=s.replace('target: win.wideKind === "shot" ? Math.max(500, IslandConfig.s("wideWidth"))','target: pill.newEvent ? 320:win.wideKind === "shot" ? Math.max(500, IslandConfig.s("wideWidth"))',1)
 s=s.replace('Math.min(IslandConfig.s("radius"), surface.height / 2)','pill.newEvent ? surface.height/2:Math.min(IslandConfig.s("radius"), surface.height / 2)',1)
 s=s.replace('            id: sparks','            id: sparks\n            visible:!pill.newEvent',1)
 s=s.replace('visible: IslandConfig.s("goo") && count > 0', 'visible: !pill.newEvent && IslandConfig.s("goo") && count > 0',1)
 s=s.replace('visible: !IslandConfig.s("goo") ||', 'visible: pill.newEvent || !IslandConfig.s("goo") ||')
 s=s.replace('            id: dropHost','            id: dropHost\n            visible:!pill.newEvent',1)
 s=s.replace('visible: IslandConfig.s("sheen")','visible: !pill.newEvent && IslandConfig.s("sheen")')
 s=s.replace('            IslandRim {','            IslandRim {\n                visible:!pill.newEvent',1)
 s=s.replace('readonly property bool want: IslandConfig.on("timer") && Timers.anyRunning','readonly property bool want: !pill.newEvent && IslandConfig.on("timer") && Timers.anyRunning',1)
 s=s.replace('running: Keyboard.caps && win.visible','running: !pill.newEvent && Keyboard.caps && win.visible',1)
 s=s.replace('opacity: lit * (0.35 + 0.45 * breath)','opacity: pill.newEvent ? 0:lit * (0.35 + 0.45 * breath)',1)
 s=s.replace('opacity: 0.16 * win.chimeGlow','opacity: pill.newEvent ? 0:0.16 * win.chimeGlow',1)
 s=s.replace('onPressedChanged: win.pressed = pressed\n                onTapped: {','onPressedChanged: win.pressed = pressed\n                onTapped: {\n                    if(win.hub.kind==="tray"){win.dashboardRequested=true;NativeSettings.ShelfState.reveal(6);return}',1)
 s=s.replace('                    id: pill','                    id: pill\n                    activityDemo:win.hub.demo\n                    activityContext:win.hub.shelfActivity || ({title:win.hub.kind===\"download\" ? win.hub.downloadPath:win.hub.taskLine,result:win.hub.kind===\"download\" ? win.hub.downloadPhase:win.hub.taskResult})\n                    activityNotification:({title:win.hub.notifSummary,body:win.hub.notifBody,image:win.hub.notifImage,icon:win.hub.notifIconUrl})',1)
 write(p,s)
 p=root/'rosa/overlays/IslandBody.qml';s=p.read_text().replace('import QtQuick\n','import QtQuick\nimport "../../island-shelf"\n',1)
 s=s.replace('    id: body','''    id: body
    ActivityData{id:eventData;kind:body.kind;label:body.kind==='notif' ? body.notifSummary:body.kind==='clip' ? body.clipText:body.headline;context:({title:body.cmd.line || '',result:body.cmd.ok===false ? 'bad':'ok'});fraction:body.fraction;demo:body.demo;notification:({title:body.notifSummary,body:body.notifBody,image:body.notifImage,icon:body.notifIcon,canReply:!!body.notifLive && body.notifLive.hasInlineReply})}
''',1)
 s=s.replace('        sourceComponent: {','        sourceComponent: {\n            if(eventData.supported)return newEventCard;',1)
 s=s.replace('    Component { id:voiceCard;', '''    Component{id:newEventCard;ActivitySurface{activity:eventData.value;presentation:'expanded';property real wantH:implicitHeight;onAction:(name,value)=>{if(name==='reply' && body.notifLive){body.notifLive.sendInlineReply(value);body.notifReply(false);body.notifDone()}else if(name==='editing')body.notifReply(value==='true');else eventData.action(name)};onActivate:{if(body.kind==='tray')eventData.action('open');if(body.kind==='notif' && body.notifLive){for(const action of body.notifLive.actions || [])if(action.identifier==='default'){action.invoke();body.notifDone();break}}}}}
    Component { id:voiceCard;''',1)
 write(p,s)

 p=root/'rosa/services/Vpn.qml';s=p.read_text().replace('    id: root','''    id: root
    property double activityConnectedAt:up ? Date.now():0
    property double activityNow:Date.now()
    onUpChanged:{activityConnectedAt=up ? Date.now():0;activityNow=Date.now()}
    readonly property int activitySeconds:up && activityConnectedAt>0 ? Math.max(0,Math.floor((activityNow-activityConnectedAt)/1000)):0
    readonly property string activityElapsed:Math.floor(activitySeconds/60)+":"+String(activitySeconds%60).padStart(2,"0")
    Timer{interval:1000;repeat:true;running:root.up;onTriggered:root.activityNow=Date.now()}
''',1);write(p,s)

 p=root/'rosa/overlays/IslandSlot.qml';s=p.read_text();write(root/'rosa/overlays/LegacyActivitySlot.qml',s)
 q=root/'rosa/overlays/qmldir';write(q,q.read_text()+'\nLegacyActivitySlot 1.0 LegacyActivitySlot.qml\n')
 write(p,'''import QtQuick
import "../../island-shelf"
Item{
 id:slot
 property string kind:''
 property color tint:'white'
 property real size:28
 property bool live:true
 property string taskGlyph:''
 property string result:''
 property string icon:''
 property real load:0
 width:size;height:size
 ActivityData{id:eventData;kind:slot.kind;label:slot.result==='ok' ? qsTr('Completed'):''}
 ActivitySurface{anchors.fill:parent;visible:slot.kind!=='sys';presentation:'satellite';activity:eventData.value}
 Loader{anchors.fill:parent;active:slot.kind==='sys';sourceComponent:Component{LegacyActivitySlot{kind:slot.kind;tint:slot.tint;size:slot.size;live:slot.live;load:slot.load}}}
}
''')
