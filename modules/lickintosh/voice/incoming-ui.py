from pathlib import Path
import sys
base=Path(sys.argv[1])/'rosa'
def edit(name,old,new):
 p=base/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError('Incoming UI anchor '+name+': '+str(s.count(old)))
 p.write_text(s.replace(old,new,1))
edit('overlays/IslandWindow.qml','    readonly property bool wide:\n','    readonly property bool wide:\n        !(VoiceCalls.incoming && !VoiceCalls.showIncoming) &&\n')
edit('overlays/IslandWindow.qml','|| win.hub.voicePeek || win.replying','|| win.hub.voicePeek || VoiceCalls.showIncoming || win.replying')
edit('overlays/IslandWindow.qml','                onTapped: {\n                    if (win.hub.kind === "call"', '                onTapped: {\n                    if(VoiceCalls.incoming){VoiceCalls.dismissIncoming();win.hub.voicePeek=false;win.forced=false;win.hub.pinned=false;win.hushed=true;return}\n                    if (win.hub.kind === "call"')
