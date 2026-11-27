"""Explicit island clicks and an optional reserved central clock slot."""
from pathlib import Path
import json


def integrate(root):
    root=Path(root)
    p=root/'rosa/services/IslandConfig.qml'
    s=p.read_text().replace('readonly property var spec: ({','readonly property var spec: ({\n        reserveClockSpace:{type:"bool",def:true},',1)
    s=s.replace('{key:"shelf",names:[','{key:"shelf",names:["reserveClockSpace",',1)
    p.write_text(s)
    for lang,label in [('en','Keep central clock space when empty'),('pt','Manter espaço central do relógio quando vazio')]:
        p=root/f'rosa/lang/{lang}.json'
        if p.exists():
            data=json.loads(p.read_text());data['isle.o.reserveClockSpace']=label;p.write_text(json.dumps(data,ensure_ascii=False,indent=2))
    p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
    s=s.replace('''                    if(IslandConfig.s("interactionPreset")==="droppy" && IslandConfig.s("dashboardEnabled")){
                        win.dashboardRequested=!win.dashboardRequested;
                        return;
                    }
''','')
    s=s.replace('if (win.pointerIn || win.dashboardPointerInside || NativeSettings.ShelfState.holdOpen) return;', 'if (win.dashboardRequested || win.pointerIn || win.dashboardPointerInside || NativeSettings.ShelfState.holdOpen) return;')
    a=s.index('    Timer{id:shelfHover;');b=s.index('    Connections{target:NativeSettings.ShelfState;',a)
    s=s[:a]+s[b:]
    p.write_text(s)
    p=root/'rosa/overlays/IslandDashboard.qml';s=p.read_text()
    s=s.replace('running: panel.expanded && panel.entered && !ShelfState.holdOpen','running: false')
    s=s.replace("    Shortcut { sequence: 'Escape'; onActivated: {ShelfState.editing=false;panel.dismissed()} }",'')
    # The expanded surface replaces the capsule, so it owns the second right click.
    s=s.replace('id: body','id: body\n        TapHandler{acceptedButtons:Qt.RightButton;onTapped:panel.dismissed()}',1)
    p.write_text(s)
    p=root/'rosa/overlays/IslandPill.qml';s=p.read_text()
    s=s.replace('pill.hideClock ? 0:clockEm.width','pill.hideClock && !IslandConfig.s("reserveClockSpace") ? 0:clockEm.width')
    p.write_text(s)
    p=root/'rosa/overlays/VoiceView.qml';s=p.read_text()
    s=s.replace('IslandConfig.s("voiceClock") && IslandConfig.on("clock") ? 106 : 72','(IslandConfig.s("reserveClockSpace") || (IslandConfig.s("voiceClock") && IslandConfig.on("clock"))) ? 106 : 72')
    a=s.index('    ShelfIcon { visible:!view.expanded && !view.bubble; anchors.right:');b=s.index('\n',a)
    s=s[:a]+'    Text { visible:!view.expanded && !view.bubble; anchors.right:parent.right; anchors.rightMargin:4; anchors.verticalCenter:parent.verticalCenter; text:VoiceCalls.selfDeaf ? "󰟎" : VoiceCalls.selfMuted ? "󰍭" : "󰏲"; color:VoiceCalls.selfDeaf || VoiceCalls.selfMuted ? "#ed4245" : "#23a55a"; font.pixelSize:16 }'+s[b:]
    p.write_text(s)


if __name__=='__main__':
    import sys
    integrate(sys.argv[1])
