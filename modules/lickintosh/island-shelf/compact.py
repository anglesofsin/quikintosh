"""Apply the shared compact/satellite presentation to the assembled island."""
from pathlib import Path
import re


def integrate(root):
    root = Path(root)
    window = root / 'rosa/overlays/IslandWindow.qml'
    text = window.read_text()
    start = text.index('        anchors.horizontalCenter:\n            IslandConfig.s("align")')
    end = text.index('\n', text.index('        anchors.rightMargin:',start))
    text = text[:start]+'''        // Conditional opposing anchors can temporarily stretch the stage and
        // discard its width binding when alignment changes. Keep one x owner.
        readonly property real desiredX:IslandConfig.s("align")==="left" ? 16+IslandConfig.s("offsetX")
            : IslandConfig.s("align")==="right" ? parent.width-width-16+IslandConfig.s("offsetX")
            : IslandConfig.s("offsetX")+(IslandConfig.s("centerMode")==="pill"
                ? parent.width/2-surface.width/2-stage.head : (parent.width-width)/2)
        x:Math.max(4,Math.min(parent.width-width-(privacy.on ? 22:4),stage.desiredX))
'''+text[end:]
    start = text.index('            readonly property real collapsedWidth:', text.index('            id: privacy'))
    end = text.index('            readonly property bool cam:', start)
    text = text[:start] + '''            // Track rendered bounds, not a cached central-pill width. Read the
            // animated inputs explicitly so mapToItem is evaluated every frame.
            readonly property point visualRight: {
                const motion = stage.x + stage.y + stage.width + stage.scale
                    + stage.jelly + squash.value + magP.value + magX.value
                    + magY.value + drift.value + win.shakeX
                    + idleVisibility.progress + win.presentationProgress;
                const surfaceEdge = surface.x + surface.width;
                const satelliteEdge = dot.visible && dot.opacity > 0.01
                    ? dot.x + dot.width / 2 + dot.width / 2
                        * dot.scale * Math.max(1, dot.blobScaleX) : surfaceEdge;
                return stage.mapToItem(win.contentItem,
                    Math.max(surfaceEdge, satelliteEdge), stage.pillH / 2);
            }

''' + text[end:]
    start = text.index('            x:IslandConfig.s("align")', text.index('            id: privacy'))
    end = text.index('            scale: privacy.on', start)
    text = text[:start] + '''            x:Math.min(win.width-width-4,Math.max(4,privacy.visualRight.x+8))
            y:privacy.visualRight.y-height/2
''' + text[end:]
    text = text.replace('    readonly property color bodyColor:', '    readonly property bool droppyCompact:IslandConfig.s("interactionPreset")==="droppy" && !win.wide && !win.seeking\n\n    readonly property color bodyColor:',1)
    text = text.replace('IslandConfig.s("black") ? Qt.rgba(0, 0, 0, 1) : Colors.bg', '(win.droppyCompact || IslandConfig.s("black")) ? Qt.rgba(0, 0, 0, 1) : Colors.bg',1)
    text = text.replace('IslandConfig.s("glow") && aura.power', '!win.droppyCompact && IslandConfig.s("glow") && aura.power')
    text = text.replace('stroke: IslandConfig.s("borderAlpha") > 0 || win.hearing || win.voicing ? 1.5 : 0', 'stroke: !win.droppyCompact && (IslandConfig.s("borderAlpha") > 0 || win.hearing || win.voicing) ? 1.5 : 0')
    text = text.replace('shadowColor: IslandConfig.s("tintShadow")', 'shadowColor: !win.droppyCompact && IslandConfig.s("tintShadow")')
    text = text.replace('strokeAlpha: win.edgeAlpha', 'strokeAlpha: win.droppyCompact ? 0 : win.edgeAlpha')
    text = text.replace('border.width: IslandConfig.s("borderAlpha") > 0 || win.hearing || win.voicing ? 1.5 : 0', 'border.width: !win.droppyCompact && (IslandConfig.s("borderAlpha") > 0 || win.hearing || win.voicing) ? 1.5 : 0')
    text = text.replace('border.width: IslandConfig.s("borderAlpha") > 0 ? 1 : 0', 'border.width: !win.droppyCompact && IslandConfig.s("borderAlpha") > 0 ? 1 : 0')
    # Restrained compact profile: no legacy coloured fill waves or flash halos.
    for name in ['ring','gloss','tide','tidePulse','liquid','glint','blot','shutter']:
        match=re.search(r'(?m)^( +)id: '+name+r'\s*$',text)
        if not match:continue
        indent=match[1];start=match.end();end=text.find('\n'+indent[:-4]+'}',start)
        if end<0:raise ValueError('Unclosed decoration '+name)
        block=text[start:end]
        visible=re.search(r'(?m)^'+indent+r'visible: ([^\n]+)',block)
        if visible:
            block=block[:visible.start()]+indent+'visible: !win.droppyCompact && ('+visible[1]+')'+block[visible.end():]
        else:block='\n'+indent+'visible: !win.droppyCompact'+block
        text=text[:start]+block+text[end:]
    window.write_text(text)
    pill = root / 'rosa/overlays/IslandPill.qml'
    text = pill.read_text().replace('import QtQuick\n', 'import QtQuick\nimport "../../island-shelf"\n', 1)
    text = text.replace('(pill.userIdle || IslandBus.crabDemo)', '(IslandBus.crabDemo || (IslandConfig.s("interactionPreset")!=="droppy" && pill.userIdle && (pill.kind==="" || pill.kind==="clock")))',1)
    # Proportional SF Pro with tabular digits: same baseline across every HUD.
    text = text.replace('font.family: Fonts.mono', 'font.family: "SF Pro Text"')
    text = text.replace('font.family: Fonts.display', 'font.family: "SF Pro Text"')
    before = '''                    Text {
                        anchors.centerIn: parent
                        visible: !pill.notifFlash && !pill.osdFlash && !pill.thumbFlash
                        text: pill.flashGlyph
                        color: pill.tint
                        font.family: Fonts.glyph
                        font.pixelSize: 14
                    }'''
    after = '''                    ShelfIcon {
                        anchors.centerIn: parent
                        visible: !pill.notifFlash && !pill.osdFlash && !pill.thumbFlash
                        icon: "notch/"+({timer:"clock",alarm:"bell",record:"video",bt:"bluetooth",btoff:"bluetooth",peri:"battery",power:"battery-charging",low:"battery",net:"wifi",vpn:"shield",print:"file-text",clip:"clipboard",keys:"command",desk:"monitor",route:"headphones",focus:"moon",cmd:"terminal",cmdfail:"alert-triangle",task:"check-circle",taskfail:"alert-triangle",shot:"camera",fail:"x",done:"check",gta:"target",rain:"cloud-rain",snow:"cloud-snow",call:"phone",launch:"external-link",download:"download",remind:"bell",sys:"cpu",weather:"cloud"}[pill.flashKind] || "bell")+".svg"
                        color:pill.tint
                        size:Math.min(16,pill.inner)
                    }'''
    if before not in text:
        raise ValueError('Compact event glyph anchor changed')
    text = text.replace(before, after, 1)
    text = text.replace('|| pill.flashing || pill.crabOn', '|| pill.flashing || pill.crabOn || pill.persistentIndicator',1)
    text = text.replace('Math.max(clockEm.width, pill.eventW)', 'Math.max(pill.hideClock ? 0 : clockEm.width, pill.eventW)')
    text = text.replace('                Text {\n                    anchors.centerIn:parent;visible:Media.art===""\n                    text:"\U000f0388";color:pill.mediaTint;font.family:Fonts.glyph\n                    font.pixelSize:Math.max(8,parent.width*.6)\n                }', '                ShelfIcon {\n                    anchors.centerIn:parent;visible:Media.art===""\n                    icon:"notch/music.svg";color:pill.mediaTint\n                    size:Math.max(8,parent.width*.6)\n                }')
    anchor = '    readonly property real coreW:'
    start = text.index(anchor)
    end = text.index('\n', start)
    text = text[:start] + """    readonly property bool persistentIndicator:!pill.flashing && !pill.miniMedia && pill.kind!=="voice" && ["timer","alarm","record","print","task","download","launch","media","shot","clip","fail","done"].includes(pill.kind)
    readonly property string persistentLabel: {
        if(pill.kind==="record" && Native.CaptureState.recording)return Native.CaptureState.recordTime;
        if(pill.kind!=="timer" || !Timers.soonest)return "";
        const seconds=Math.max(0,Math.ceil(Timers.left(Timers.soonest)));
        return Math.floor(seconds/60)+":"+String(seconds%60).padStart(2,"0");
    }
    TextMetrics{id:persistentEm;font.family:"SF Pro Text";font.pixelSize:13;font.weight:Font.DemiBold;text:pill.persistentLabel}
    readonly property real coreW:Math.max(pill.hideClock ? 0:clockEm.width,pill.eventW,pill.persistentIndicator ? pill.inner+(pill.persistentLabel ? 9+persistentEm.width:0):0)
""" + text[end:]
    text = text.replace('    SequentialAnimation {\n        id: pop', """    Row {
        anchors.centerIn:parent;spacing:9
        visible:pill.persistentIndicator
        ShelfIcon{anchors.verticalCenter:parent.verticalCenter;size:Math.min(16,pill.inner);color:pill.tint;icon:"notch/"+({timer:"clock",alarm:"bell",record:"video",print:"file-text",task:"check-circle",download:"download",launch:"external-link",media:"music",shot:"camera",clip:"clipboard",fail:"x",done:"check"}[pill.kind] || "bell")+".svg"}
        Text{visible:!!pill.persistentLabel;text:pill.persistentLabel;color:pill.tint;font.family:"SF Pro Text";font.pixelSize:13;font.weight:Font.DemiBold;font.features:({tnum:1})}
    }
    SequentialAnimation {
        id: pop""",1)
    pill.write_text(text)
    slot = root / 'rosa/overlays/IslandSlot.qml'
    text = slot.read_text().replace('import QtQuick\n', 'import QtQuick\nimport "../../island-shelf"\n',1)
    a = text.index('    Text {\n        id: mark')
    b = text.index('        SequentialAnimation on opacity', a)
    text = text[:a] + """    Item {
        id:mark
        anchors.centerIn:parent
        width:Math.max(10,Math.round(slot.size*.50));height:width
        visible:!slot.counting && slot.glyph!==""
        ShelfIcon{anchors.centerIn:parent;size:parent.width;color:slot.tint;icon:"notch/"+(slot.result==="ok" ? "check":slot.result==="bad" ? "x":({print:"file-text",timer:"clock",remind:"bell",task:"terminal",download:"download",launch:"external-link"}[slot.kind] || "circle"))+".svg"}

"""+text[b:]
    text = text.replace('family: Fonts.mono','family: "SF Pro Text"')
    slot.write_text(text)
    orb = root / 'rosa/overlays/IslandOrb.qml'
    text = orb.read_text().replace('import QtQuick\n', 'import QtQuick\nimport "../../island-shelf"\n',1)
    start = text.index('        Text {')
    end = text.index('\n        }', start)+len('\n        }')
    text = text[:start]+"""        ShelfIcon {
            anchors.centerIn:parent
            visible:Media.art===""
            icon:"notch/music.svg"
            color:orb.tint
            size:Math.max(8,parent.width*.7)
        }"""+text[end:]
    orb.write_text(text)

    voice = root / 'rosa/overlays/VoiceView.qml'
    text = voice.read_text().replace('import QtQuick\n', 'import QtQuick\nimport "../../island-shelf"\n',1)
    old = '    Text { visible:!view.expanded && !view.bubble; anchors.right:parent.right; anchors.rightMargin:4; anchors.verticalCenter:parent.verticalCenter; text:VoiceCalls.selfDeaf ? "󰟎" : VoiceCalls.selfMuted ? "󰍭" : "󰏲"; color:VoiceCalls.selfDeaf || VoiceCalls.selfMuted ? "#ed4245" : "#23a55a"; font.pixelSize:16 }'
    new = '    ShelfIcon { visible:!view.expanded && !view.bubble; anchors.right:parent.right; anchors.rightMargin:4; anchors.verticalCenter:parent.verticalCenter; icon:VoiceCalls.selfDeaf ? "notch/headphones.svg" : VoiceCalls.selfMuted ? "notch/mic-off.svg" : "notch/phone.svg"; color:VoiceCalls.selfDeaf || VoiceCalls.selfMuted ? "#ff453a" : "#30d158"; size:16 }'
    if old not in text:raise ValueError('Compact call glyph anchor changed')
    text = text.replace('implicitWidth: expanded ? 500 : bubble ? 24 : 106', 'implicitWidth: expanded ? 500 : bubble ? 24 : IslandConfig.s("voiceClock") && IslandConfig.on("clock") ? 106 : 72',1)
    text = text.replace(old,new,1).replace('font.bold:true; font.pixelSize:12','font.family:"SF Pro Text"; font.features:({tnum:1}); font.bold:true; font.pixelSize:12',1)
    voice.write_text(text)



if __name__ == '__main__':
    import sys
    integrate(sys.argv[1])
