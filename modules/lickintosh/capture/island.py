"""One screenshot event: keep the incoming thumbnail animation and a clean card."""
from pathlib import Path
import shutil,json,sys
root=Path(sys.argv[1]);here=Path(__file__).parent

def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Screenshot island anchor {name}: {old[:75]} ({s.count(old)})')
 p.write_text(s.replace(old,new,1))

shutil.copyfile(here/'island/ShotCard.qml',root/'rosa/overlays/cards/ShotCard.qml')
edit('rosa/services/IslandBus.qml','    signal settingsRequested()', '    signal screenshotSaved(string path)\n    signal settingsRequested()')
edit('RosaIntegration.qml','        function onSysOpen()', '        function onScreenshotSaved(path){if(islandLoader.item)islandLoader.item.shot(path)}\n        function onSysOpen()')
edit('rosa/overlays/IslandSources.qml','import QtQuick\n','import QtQuick\nimport qs.services as NativeCapture\n')
edit('rosa/overlays/IslandSources.qml','        switch (f[0]) {','''        if (NativeCapture.CaptureState.busy || now < NativeCapture.CaptureState.quietClipboardUntil) return;
        switch (f[0]) {''')
edit('rosa/overlays/Island.qml','        root.shotPath = path;','''        if(root.shotPath === path && Date.now()-root.shotAt<5000)return true;
        root.shotPath = path;''')
edit('rosa/overlays/IslandWindow.qml','              : win.wideKind === "media" ? IslandConfig.s("mediaHeight")','              : win.wideKind === "shot" ? Math.max(100, body.want + 24)\n              : win.wideKind === "media" ? IslandConfig.s("mediaHeight")')
edit('rosa/overlays/IslandWindow.qml','target: win.wideKind === "voice" ? IslandConfig.s("voiceCardWidth") :','target: win.wideKind === "shot" ? Math.max(500, IslandConfig.s("wideWidth")) : win.wideKind === "voice" ? IslandConfig.s("voiceCardWidth") :')
p=root/'rosa/lang/en.json';data=json.loads(p.read_text());data.update({'isle.shot.title':'Screenshot','isle.shot.desktop':'Saved to Desktop · just now','isle.shot.saved':'Saved · just now'});p.write_text(json.dumps(data,ensure_ascii=False,indent=2))

# Screenshot dwell and auto-expansion have different timers upstream. Keep the
# card expanded until its event expires; never expose a filename in the pill.
edit('rosa/overlays/IslandWindow.qml','    property bool forced: false','    property bool forced: false\n    property string previousKind: ""')
edit('rosa/overlays/IslandWindow.qml','        function onKindChanged() {','''        function onKindChanged() {
            if(win.previousKind === "shot" && win.hub.kind !== "shot") {force.stop();win.forced=false;win.hushed=true;}
            win.previousKind=win.hub.kind;''')
edit('rosa/overlays/IslandWindow.qml','&& (win.hub.pinned || win.forced || win.hub.demoWide || win.hub.voicePeek || win.replying','&& ((win.hub.kind === "shot" && IslandConfig.s("autoWide")) || win.hub.pinned || win.forced || win.hub.demoWide || win.hub.voicePeek || win.replying')
edit('rosa/overlays/Island.qml','            root.flashKind = "";\n            root.stacked = 0;','''            if(root.flashKind === "shot") {root.flashText="";root.flashGlyph="";root.flashFraction=-1;}
            root.flashKind = "";
            root.stacked = 0;''')
edit('rosa/overlays/Island.qml','        flashLife.stop();\n        root.flashKind = "";','''        flashLife.stop();
        if(root.flashKind === "shot") {root.flashText="";root.flashGlyph="";root.flashFraction=-1;}
        root.flashKind = "";''')
edit('RosaIntegration.qml','knobs:Object.keys(RosaServices.IslandConfig.spec).length','expandedScreens:RosaServices.IslandBus.expandedScreens,knobs:Object.keys(RosaServices.IslandConfig.spec).length')
# Do not substitute a media/text card into the outgoing screenshot while the
# outer island is shrinking. Only the normal compact pill should be revealed.
edit('rosa/overlays/IslandBody.qml','    property string shotPath: ""','''    property string shotPath: ""
    property bool shotPresented:false
    onKindChanged:if(body.kind === "shot")body.shotPresented=true''')
edit('rosa/overlays/IslandBody.qml','        if (body.wide) {','''        if (body.wide) {
            if(body.kind !== "shot")body.shotPresented=false;''')
edit('rosa/overlays/IslandBody.qml','        visible: opacity > 0.01','        visible: opacity > 0.01 && !(body.shotPresented && !body.wide)')
