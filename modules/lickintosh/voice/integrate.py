"""Add voice metadata to the existing island and native settings catalog."""
from pathlib import Path
import json,sys
root=Path(sys.argv[1]); source=Path(__file__).parent; base=root/'rosa'
def edit(name,old,new):
 p=base/name; s=p.read_text()
 if s.count(old)!=1: raise ValueError(f'Voice anchor {name}: {old[:70]}')
 p.write_text(s.replace(old,new,1))
for name,target in [('VoiceCalls.qml','services/VoiceCalls.qml'),('VoiceView.qml','overlays/VoiceView.qml'),('VoiceAvatar.qml','overlays/VoiceAvatar.qml'),('bridge.py','voice-bridge.py'),('avatar_cache.py','avatar_cache.py')]:
 s=(source/name).read_text().replace('@VOICE_PYTHON@',sys.argv[2]); (base/target).write_text(s)
for directory,entry in [('services','singleton VoiceCalls VoiceCalls.qml'),('overlays','VoiceView VoiceView.qml\nVoiceAvatar VoiceAvatar.qml')]:
 p=base/directory/'qmldir';p.write_text(p.read_text()+'\n'+entry+'\n')
options={
 'voiceIncoming':('bool',True,'Expand incoming calls'),
 'voiceLayout':('pick','auto','Call presentation'),
 'voiceBackground':('bool',True,'Minimize beside music or video'),
 'voiceClock':('bool',True,'Keep the clock in the center'),
 'voiceJoin':('bool',True,'Expand when joining a call'),
 'voiceDuration':('bool',True,'Show call duration'),
 'voiceGuild':('bool',True,'Show server name'),
 'voiceControls':('bool',True,'Show microphone, deafen and leave buttons'),
 'voiceCardWidth':('int',520,'Expanded call width'),
 'voiceEnabled':('bool',True,'Detect ongoing voice calls'),
 'voiceCanary':('bool',True,'Discord Canary'), 'voicePtb':('bool',True,'Discord PTB'),
 'voiceStable':('bool',True,'Discord Stable'), 'voiceEquibop':('bool',True,'Equibop'),
 'voiceGeneric':('bool',True,'Detect other communication apps (PipeWire)'),
 'voiceClient':('pick','auto','Preferred client'),
 'voiceSelf':('bool',True,'Show me'), 'voiceOthers':('bool',True,'Show other participants'),
 'voiceAvatars':('bool',True,'Show profile pictures'), 'voiceAura':('bool',True,'Green ring while speaking'),
 'voicePulse':('bool',False,'Animate the speaking ring'), 'voiceNames':('bool',True,'Show participant and channel names'),
 'voicePrivacy':('bool',True,'Hide calls in Discord streamer mode'),
 'voiceMax':('int',5,'Maximum visible participants'), 'voiceAvatarSize':('int',36,'Expanded avatar size'),
}
spec=''
for key,(kind,default,label) in options.items():
 extras=', values: ["auto","focus","minimized"]' if key=='voiceLayout' else ', min: 340, max: 800' if key=='voiceCardWidth' else ', values: ["auto","canary","ptb","stable","equibop"]' if kind=='pick' else ', min: 1, max: 8' if key=='voiceMax' else ', min: 24, max: 56' if key=='voiceAvatarSize' else ''
 spec+=f'        {key}: {{type:"{kind}", def:{json.dumps(default)}{extras}}},\n'
edit('services/IslandConfig.qml','        enabled:     { type: "bool", def: true },', '        enabled:     { type: "bool", def: true },\n'+spec)
edit('services/IslandConfig.qml','    readonly property var groups: [','    readonly property var groups: [\n        {key:"voice", names:'+json.dumps(list(options))+'},')
p=base/'lang/en.json'; lang=json.loads(p.read_text()); lang['isle.sec.voice']='Voice calls';lang.update({'isle.v.focus':'Keep call in the main island','isle.v.minimized':'Always use the left bubble'});lang.update({'isle.o.'+k:v[2] for k,v in options.items()});lang.update({'isle.v.'+k:v for k,v in {'auto':'Canary → PTB → Stable → Equibop','canary':'Discord Canary','ptb':'Discord PTB','stable':'Discord Stable','equibop':'Equibop'}.items()});p.write_text(json.dumps(lang,ensure_ascii=False,indent=2))
p=root/'RosaIntegration.qml';s=p.read_text();s=s.replace('    signal settingsOpening()', '''    Binding { target:RosaServices.VoiceCalls; property:"enabled"; value:root.enabled && !root.locked && RosaServices.IslandConfig.s("enabled") && RosaServices.IslandConfig.s("voiceEnabled") }
    signal settingsOpening()''');s=s.replace('knobs:Object.keys', 'voiceActive:RosaServices.VoiceCalls.active,voiceClient:RosaServices.VoiceCalls.call ? RosaServices.VoiceCalls.call.client : "",voiceParticipants:RosaServices.VoiceCalls.participants.length,voiceSpeaking:RosaServices.VoiceCalls.speakingCount,voiceControls:RosaServices.VoiceCalls.controlsAvailable,voiceImage:!!RosaServices.VoiceCalls.image,voiceError:RosaServices.VoiceCalls.error,knobs:Object.keys');p.write_text(s)
# Preserve alarms, incoming calls and transient notifications; resume ongoing call afterwards.
edit('overlays/Island.qml','        if (IslandConfig.on("call") && root.callState === "live")','        if (VoiceCalls.active && (!root.voiceSide || root.voicePeek)) return "voice";\n        if (root.voiceSide && Media.has && Media.playing && IslandConfig.on("media") && IslandConfig.s("voiceLayout") !== "minimized") return "media";\n        if (root.voiceSide && IslandConfig.s("voiceClock")) return "clock";\n        if (IslandConfig.on("call") && root.callState === "live")')
edit('overlays/IslandWindow.qml','        if (win.hub.kind === "timer" || win.hub.kind === "record"','        if (win.hub.kind === "voice") return "voice";\n        if (win.hub.kind === "timer" || win.hub.kind === "record"')
edit('overlays/IslandWindow.qml','              : win.wideKind === "media" ? IslandConfig.s("mediaHeight")','              : win.wideKind === "voice" ? Math.max(88, body.want + 20)\n              : win.wideKind === "media" ? IslandConfig.s("mediaHeight")')
edit('overlays/IslandBody.qml','            case "call":   return callCard;','            case "voice":  return voiceCard;\n            case "call":   return callCard;')
edit('overlays/IslandBody.qml','    Component { id: mediaCard;', '    Component { id:voiceCard; VoiceView { expanded:true } }\n    Component { id: mediaCard;')
# Compact content uses the same pill/surface and hover/click expansion as every island source.
edit('overlays/IslandPill.qml','    implicitWidth: pill.coreW + pill.sideRoom * 2 + 24','    implicitWidth: pill.kind === "voice" ? voice.implicitWidth + 12 : pill.coreW + pill.sideRoom * 2 + 24\n    VoiceView { id:voice; anchors.centerIn:parent; visible:pill.kind === "voice"; width:implicitWidth; height:implicitHeight }')
edit('overlays/IslandPill.qml','            id: middle','            id: middle\n            visible:pill.kind !== \"voice\"')
# Existing content is hidden only while showing real call metadata.
p=base/'overlays/IslandPill.qml';s=p.read_text().replace('readonly property bool hideClock: pill.flashing || pill.crabOn','readonly property bool hideClock: pill.kind === "voice" || pill.flashing || pill.crabOn');p.write_text(s)

edit('overlays/IslandWindow.qml','miniMedia: win.hub.miniMedia && !stage.minimalOn','miniMedia: win.hub.miniMedia && !stage.minimalOn && win.hub.kind !== "voice" && !(win.hub.voiceSide && IslandConfig.s("voiceLayout") === "minimized")')

edit('overlays/Island.qml','    property bool mediaBig: false','''    property bool voicePeek: false
    property int voicePeekMs: 900
    readonly property bool voiceSide: VoiceCalls.active && (IslandConfig.s("voiceLayout") === "minimized"
        || (IslandConfig.s("voiceLayout") === "auto" && IslandConfig.s("voiceBackground") && Media.has && Media.playing))
    Timer { running:root.voicePeek && !root.hoverHold; interval:root.voicePeekMs; onTriggered:root.voicePeek=false }
    Connections {
        target:VoiceCalls
        function onCallKeyChanged() {
            root.voicePeek=VoiceCalls.active && IslandConfig.s("voiceJoin")
            root.voicePeekMs=4000
        }
    }
    property bool mediaBig: false''')
edit('overlays/Island.qml','        if (root.mediaBig)','        if (VoiceCalls.active && root.voicePeek) return "voice";\n        if (root.mediaBig)')
edit('overlays/Island.qml','    readonly property string leftKind: {','    readonly property string leftKind: {\n        if (root.voiceSide) return "voice";')
edit('overlays/IslandWindow.qml','IslandConfig.s("leftSlot") && win.hub.leftKind !== ""','(IslandConfig.s("leftSlot") || win.hub.leftKind === "voice") && win.hub.leftKind !== ""')
edit('overlays/IslandWindow.qml','&& (win.hub.pinned || win.forced || win.hub.demoWide || win.replying','&& (win.hub.pinned || win.forced || win.hub.demoWide || win.hub.voicePeek || win.replying')
edit('overlays/IslandWindow.qml','        target: win.big ? IslandConfig.s("mediaBigWidth") : IslandConfig.s("wideWidth")','        target: win.wideKind === "voice" ? IslandConfig.s("voiceCardWidth") : win.big ? IslandConfig.s("mediaBigWidth") : IslandConfig.s("wideWidth")')
edit('overlays/IslandWindow.qml','                kind: win.hub.leftKind','                visible: win.hub.leftKind !== "voice"\n                kind: win.hub.leftKind')
edit('overlays/IslandWindow.qml','            readonly property color hue: {','''            VoiceView { z:1; anchors.fill:parent; bubble:true; visible:win.hub.leftKind === "voice" }
            HoverHandler {
                enabled:win.hub.leftKind === "voice"
                cursorShape:Qt.PointingHandCursor
                onHoveredChanged:if(hovered) {win.hub.voicePeekMs=900; win.hub.voicePeek=true}
            }
            TapHandler { enabled:win.hub.leftKind === "voice"; onTapped:{win.hub.voicePeekMs=4000;win.hub.voicePeek=true} }
            readonly property color hue: {''')

edit('overlays/IslandWindow.qml','        target: Math.max(IslandConfig.s("pillMin"), pill.implicitWidth + 26)','        target: win.hub.kind === "voice" ? pill.implicitWidth : Math.max(IslandConfig.s("pillMin"), pill.implicitWidth + 26)')

# The detached voice bubble is an independent surface, not a metaball. Avoid a
# shared SDF outline and competing tinted glows around the neighboring clock.
edit('overlays/IslandWindow.qml','visible: IslandConfig.s("goo") && count > 0','visible: IslandConfig.s("goo") && count > 0 && !win.hub.voiceSide')
p=base/'overlays/IslandWindow.qml';s=p.read_text().replace('visible: !IslandConfig.s("goo") || goo.count <= 0','visible: !IslandConfig.s("goo") || goo.count <= 0 || win.hub.voiceSide')
s=s.replace('visible: IslandConfig.s("glow") && aura.power > 0.005','visible: IslandConfig.s("glow") && aura.power > 0.005 && !win.hub.voiceSide')
s=s.replace('function onWidthChanged() { goo.applySync(); }','function onXChanged() { goo.requestSync(); }\n            function onYChanged() { goo.requestSync(); }\n            function onWidthChanged() { goo.requestSync(); }').replace('function onHeightChanged() { goo.applySync(); }','function onHeightChanged() { goo.requestSync(); }')
p.write_text(s)

# Privacy belongs to the window, outside the island's animated/scaled stage.
edit('overlays/IslandWindow.qml','            id: privacy','''            id: privacy
            parent:win.contentItem
            z:100
            readonly property real collapsedWidth:win.hub.kind === "voice" ? pill.implicitWidth : Math.max(IslandConfig.s("pillMin"),pill.implicitWidth+26)
            property real restWidth:collapsedWidth
            function syncRest() { if(!win.wide && !win.pointerIn && !win.hub.voicePeek) restWidth=collapsedWidth }
            onCollapsedWidthChanged:syncRest()
            Component.onCompleted:restWidth=collapsedWidth
            Connections { target:win; function onWideChanged(){privacy.syncRest()} function onHoveringChanged(){privacy.syncRest()} }
            readonly property real restOffset:IslandConfig.s("centerMode") === "group" ? ((stage.leftOn ? stage.gapPx+stage.dotSize : 0)-(stage.minimalOn ? stage.gapPx+stage.dotSize : 0))/2 : 0''')
edit('overlays/IslandWindow.qml','            x: stage.width + 7\n            anchors.verticalCenter: surface.verticalCenter','''            x:IslandConfig.s("align") === "left" ? 23+IslandConfig.s("offsetX")+privacy.restWidth
                : IslandConfig.s("align") === "right" ? win.width-9+IslandConfig.s("offsetX")
                : win.width/2+IslandConfig.s("offsetX")+privacy.restOffset+privacy.restWidth/2+7
            y:win.atTop ? stage.gap+stage.pillH/2-height/2 : win.height-stage.gap-stage.pillH/2-height/2''')

# Keep the detached call avatar identical to its 20 px focused counterpart.
edit('overlays/IslandWindow.qml','        readonly property int dotSize: stage.pillH','        readonly property int dotSize: stage.pillH\n        readonly property int headSize:win.hub.leftKind === "voice" ? 24 : stage.dotSize\n        readonly property int headGap:win.hub.leftKind === "voice" ? Math.min(6,stage.gapPx) : stage.gapPx')
edit('overlays/IslandWindow.qml','            stage.headDetach * (stage.gapPx + stage.dotSize)','            stage.headDetach * (stage.headGap + stage.headSize)')
p=base/'overlays/IslandWindow.qml';s=p.read_text();start=s.index('            id: task');end=s.index('            id: privacy',start)
part=s[start:end].replace('width: stage.dotSize','width: stage.headSize').replace('height: stage.dotSize','height: stage.headSize').replace('stage.head - stage.headDetach * (stage.gapPx + stage.dotSize)','stage.head - stage.headDetach * (stage.headGap + stage.headSize)').replace('task.wobP >= 1 ? 0','task.wobP >= 1 || win.hub.leftKind === "voice" ? 0')
s=s[:start]+part+s[end:];s=s.replace('(stage.leftOn ? stage.gapPx+stage.dotSize : 0)','(stage.leftOn ? stage.headGap+stage.headSize : 0)');p.write_text(s)

# Do not draw the fixed privacy light over expanded content or its closing animation.
edit('overlays/IslandWindow.qml','            scale: privacy.on ? 1 : 0\n            visible: scale > 0.01','            scale: privacy.on ? 1 : 0\n            visible: scale > 0.01 && !win.wide && !win.seeking && Math.abs(morph.value) < 0.02 && Math.abs(seek.value) < 0.02')

# Keep the update repair worker outside the client and preserve its logs.
for name in ['guard.py','install-clients.py','main-hook.cjs','discord-bridge.js']:(base/name).write_text((source/name).read_text())
p=base/'services/VoiceCalls.qml';s=p.read_text();s=s.replace('    Process {\n        id: process','    Process{running:root.enabled;command:["'+sys.argv[2]+'",Quickshell.shellDir+"/rosa/guard.py"]}\n    Process {\n        id: process');p.write_text(s)

# Incoming metadata interrupts media until dismissed; hover cannot immediately reopen it.
edit('overlays/Island.qml','        if (VoiceCalls.active && (!root.voiceSide || root.voicePeek))', '        if (VoiceCalls.showIncoming) return "voice";\n        if (VoiceCalls.incoming && !VoiceCalls.showIncoming) return Media.has && Media.playing ? "media":"clock";\n        if (VoiceCalls.active && (!root.voiceSide || root.voicePeek))')

p=root/'ui/topbar/statusarea/notifcenter/NotifService.qml';s=p.read_text();anchor='        _centerModel.append({ notifObj: notification })';assert s.count(anchor)==1;s=s.replace(anchor,'        if(!root.dndEnabled)Rosa.VoiceCalls.receiveNotification(notification)\n'+anchor,1);p.write_text(s)
