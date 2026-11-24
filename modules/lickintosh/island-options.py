"""Make every island activity independently controllable and center the actual pill."""
from pathlib import Path
import sys,json
root=Path(sys.argv[1]);base=root/'rosa'
def edit(name,old,new):
 p=base/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Expected one options anchor in {name}: {old[:65]}')
 p.write_text(s.replace(old,new,1))
# Use one singleton import identity in the island, bridge and native settings app.
import re,os
for p in base.rglob('*.qml'):
    text=p.read_text()
    def service_import(match):
        path=Path(os.path.normpath(str(p.parent/match[1])))
        return 'import qs.rosa.services' if path==base/'services' else match[0]
    text=re.sub(r'import "([.][^\"]*)"',service_import,text)
    p.write_text(text)
options={
 'srcDownload':('bool','true','Show downloads'),
 'srcLaunch':('bool','true','Show application launches'),
 'srcRemind':('bool','true','Show reminders'),
 'srcCall':('bool','true','Show incoming calls'),
 'srcCaps':('bool','true','Show Caps Lock changes'),
 'srcWall':('bool','true','Show wallpaper changes'),
 'srcDone':('bool','true','Show task completion'),
 'srcFail':('bool','true','Show task failures'),
}
spec=''.join(f'        {k}: {{ type: "{t}", def: {d} }},\n' for k,(t,d,l) in options.items())
spec+='''        downloadStaleMinutes: { type: "int", def: 15, min: 1, max: 1440 },
        centerMode: { type: "pick", def: "pill", values: ["pill", "group"] },
'''
edit('services/IslandConfig.qml','        enabled:     { type: "bool", def: true },','        enabled:     { type: "bool", def: true },\n'+spec)
edit('services/IslandConfig.qml','"srcClock"]','"srcClock", '+', '.join('"'+k+'"' for k in options)+']')
edit('services/IslandConfig.qml','"where", "offsetX", "offsetY"]','"where", "offsetX", "offsetY", "centerMode"]')
edit('services/IslandConfig.qml','"eatPopups", "sfx"]','"eatPopups", "sfx", "downloadStaleMinutes"]')
edit('services/IslandConfig.qml','comet:       { type: "bool", def: true }','comet:       { type: "bool", def: false }')
edit('overlays/Island.qml','&& (IslandConfig.s("inBar") || IslandConfig.on("clock"))','&& IslandConfig.on("clock")')
edit('overlays/Island.qml','if (root.launch !== null)','if (IslandConfig.on("launch") && root.launch !== null)')
edit('overlays/Island.qml','if (root.downloadPhase !== "")','if (IslandConfig.on("download") && root.downloadPhase !== "")')
edit('overlays/Island.qml','if (Reminders.soon !== null && Reminders.ringing === null)','if (IslandConfig.on("remind") && Reminders.soon !== null && Reminders.ringing === null)')
edit('overlays/Island.qml','if (Reminders.ringing !== null && root.remindLanded)','if (IslandConfig.on("remind") && Reminders.ringing !== null && root.remindLanded)')
for state in ['ring','live']:
 edit('overlays/Island.qml',f'\n        if (root.callState === "{state}")',f'\n        if (IslandConfig.on("call") && root.callState === "{state}")')
edit('overlays/IslandSources.qml','if (src.isCall(e, live))','if (IslandConfig.on("call") && src.isCall(e, live))')
edit('overlays/Island.qml','if (!IslandConfig.s("enabled") || (!force && !IslandConfig.on(kind)))','''if (!IslandConfig.s("enabled") || (!IslandConfig.on(kind)
            && (!force || IslandConfig.spec["src" + kind.charAt(0).toUpperCase() + kind.slice(1)] !== undefined)))''')
edit('overlays/Island.qml','    property string flashKind: ""','''    Connections {
        target: IslandConfig
        function onStyleChanged() {
            if (root.flashKind && !IslandConfig.on(root.flashKind)) root.dismiss();
            if (!IslandConfig.on("call") && root.callState !== "") root.endCall();
        }
    }
    property string flashKind: ""''')
edit('overlays/IslandWindow.qml','IslandConfig.s("offsetX") + (stage.head - stage.tail) / 2','IslandConfig.s("offsetX") + (IslandConfig.s("centerMode") === "pill" ? (stage.tail - stage.head) / 2 : 0)')
edit('services/Islandd.qml','    readonly property bool alive: proc.running','''    readonly property int downloadStaleMinutes: IslandConfig.s("downloadStaleMinutes")
    onDownloadStaleMinutesChanged: { proc.running = false; restart.restart() }
    readonly property bool alive: proc.running''')
edit('services/Islandd.qml','command: [root.bin, "watch"]','command: ["env", "ROSA_DOWNLOAD_STALE_SECONDS=" + (root.downloadStaleMinutes * 60), root.bin, "watch"]')
p=base/'services/Islandd.qml';s=p.read_text().replace('import QtQuick','import qs.rosa.services\nimport QtQuick',1);p.write_text(s)
p=base/'lang/en.json';d=json.loads(p.read_text());d.update({'isle.o.'+k:l for k,(_,_,l) in options.items()})
d.update({'isle.o.srcClock':'Show the idle clock','isle.o.srcDesk':'Show workspace changes',
 'isle.o.comet':'Fly notifications from the right into the island','isle.o.leftSlot':'Show the left activity indicator',
 'isle.o.centerMode':'Center alignment','isle.v.pill':'Main island stays centered','isle.v.group':'Center the island and side indicators together',
 'isle.o.downloadStaleMinutes':'Ignore partial downloads unchanged for (minutes)'})
d.update({'isle.sec.src':'Activity visibility','isle.sec.place':'Position and alignment','isle.sec.paint':'Appearance and animations','isle.sec.act':'Interaction and notifications','isle.o.srcDesk':'Show workspace changes','isle.o.srcClock':'Show the clock when idle','isle.o.comet':'Animate notifications flying in from the side'})
p.write_text(json.dumps(d,ensure_ascii=False,indent=2))

# Ignore stale asynchronous reads while a local edit is waiting to be persisted.
edit('services/IslandConfig.qml','        onLoaded: {\n            const out = {};','        onLoaded: {\n            if (flush.running) return;\n            const out = {};')
for kind in ['done','fail']:
    edit('overlays/Island.qml',f'    function {kind}(glyph, text) {{',f'    function {kind}(glyph, text) {{\n        if (!IslandConfig.on("{kind}")) return;')

edit('overlays/Island.qml','    function wallStart(tone) {','    function wallStart(tone) {\n        if (!IslandConfig.on("wall")) return;')
edit('overlays/Island.qml','        function onLaunching(info) {','        function onLaunching(info) {\n            if (!IslandConfig.on("launch")) return;')
edit('overlays/Island.qml','        function onDue(r) {','        function onDue(r) {\n            if (!IslandConfig.on("remind")) return;')
