"""Embed the pinned Rosa island in Lickintosh; never run Rosa's desktop installer."""
from pathlib import Path
import sys,re,os
root=Path(sys.argv[1]); rosa=root/'rosa'; islandd=sys.argv[2]
def edit(name,old,new):
 p=root/name;s=p.read_text()
 if s.count(old)!=1:raise ValueError(f'Expected one integration anchor in {name}: {old[:70]}')
 p.write_text(s.replace(old,new,1))
# Namespace the original upstream modules, assets and persistent state.
for p in rosa.rglob('*.qml'):
 s=p.read_text()
 s=re.sub(r'import "root:/([^"]+)"',lambda m:'import "'+os.path.relpath(rosa/m[1],p.parent)+'"',s)
 s=s.replace('Quickshell.shellPath("','Quickshell.shellPath("rosa/')
 s=s.replace('"root:/', '"root:/rosa/')
 s=s.replace('Quickshell.env("HOME") + "/.config/hypr/scripts/', 'Quickshell.shellDir + "/rosa/helpers/')
 s=s.replace('Quickshell.shellDir + "/assets/', 'Quickshell.shellDir + "/rosa/assets/')
 s=s.replace('Quickshell.env("HOME") + "/.local/bin/islandd"', '"'+islandd+'"')
 s=re.sub(r'Quickshell.statePath\(([^()]+)\)',r'(Quickshell.env("HOME") + "/.config/lickintosh/rosa/" + \1)',s)
 p.write_text(s)
edit('rosa/services/Cava.qml','Quickshell.env("HOME") + "/.config/cava/config-bar"','Quickshell.shellDir + "/rosa/cava.conf"')
# The shell already owns idle, power policy, notification history and MPRIS selection.
edit('rosa/services/Prefs.qml','property bool idleEnabled: true','property bool idleEnabled: false')
edit('rosa/services/Prefs.qml','property bool sfxEnabled: true','property bool sfxEnabled: false')
edit('rosa/services/Prefs.qml','property bool weatherEnabled: true','property bool weatherEnabled: false')
edit('rosa/services/Prefs.qml','property string design: "native"','property string design: "apple"')
edit('rosa/services/Prefs.qml','property string fontDisplay: "Adwaita Sans"','property string fontDisplay: "SF Pro Display"')
# An idle clock provides a discoverable island even without playback or alerts.
edit('rosa/services/IslandConfig.qml','srcClock:    { type: "bool", def: false }','srcClock:    { type: "bool", def: true }')
edit('rosa/services/IslandConfig.qml','path: (Quickshell.env("HOME") + "/.config/lickintosh/rosa/" + "island.json")','path: Quickshell.env("HOME") + "/.config/lickintosh/rosa/island.json"\n        watchChanges: true\n        onFileChanged: reload()')
# Settings-only actions must not create a second island or register desktop shortcuts.
edit('rosa/overlays/IslandWindow.qml','visible: IslandConfig.s("enabled")','visible: !IslandBus.locked && IslandConfig.s("enabled")')
# Align the Rosa island with the original 32px Lickintosh menu bar.
edit('rosa/services/IslandConfig.qml','offsetY:     { type: "int", def: 6,','offsetY:     { type: "int", def: 3,')
edit('rosa/services/BarConfig.qml','barHeight:     { type: "int", def: 34,','barHeight:     { type: "int", def: 32,')
edit('rosa/services/IslandConfig.qml','pillHeight:  { type: "int", def: 28,','pillHeight:  { type: "int", def: 26,')
edit('rosa/services/IslandConfig.qml','barTakeover: { type: "bool", def: true }','barTakeover: { type: "bool", def: false }')
# The existing Lickintosh source is authoritative for media selection and playback.
p=rosa/'services/Media.qml';s=p.read_text().replace('import Quickshell.Services.Mpris','import qs.services as Native\nimport Quickshell.Services.Mpris',1)
s=s.replace('property var player: null','property var player: Native.MprisState.activePlayer',1)
a=s.index('    function pick() {');b=s.index('\n    function toggle()',a)
s=s[:a]+'''    function pick() { player = Qt.binding(function() { return Native.MprisState.activePlayer }) }
'''+s[b:];p.write_text(s)
# DND is one shared setting. Rosa must never write a competing global DND marker.
(rosa/'services/Dnd.qml').write_text('''pragma Singleton
import Quickshell
import qs.ui.topbar.statusarea.notifcenter as Native
Singleton {
 readonly property bool active: Native.NotifService.dndEnabled
 function toggle() { Native.NotifService.dndEnabled = !Native.NotifService.dndEnabled }
}
''')
# Reuse the existing privacy monitor, avoiding duplicate process scans and microphone probes.
(rosa/'services/Privacy.qml').write_text('''pragma Singleton
import Quickshell
import qs.services as Native
Singleton {
 property bool watching: false
 readonly property bool mic: Native.MediaCaptureState.micActive
 readonly property bool camera: Native.MediaCaptureState.cameraActive
}
''')
# Colours follow the native theme rather than changing desktop applications via matugen.
p=rosa/'design/Colors.qml';s=p.read_text().replace('import QtQuick','import qs.services as Native\nimport QtQuick',1)
a=s.index('    FileView {');b=s.index('\n    property color bg:',a)
s=s[:a]+'''    Binding { target: root; property: "srcAccent"; value: Native.Theme.accent }
'''+s[b:];p.write_text(s)
# No missing external sound files: use the installed freedesktop alert when available.
p=rosa/'services/Sfx.qml';s=p.read_text().replace('Quickshell.execDetached(["pw-play", "--volume=" + level.toFixed(3), path]);','Quickshell.execDetached(["canberra-gtk-play", "-i", "complete"]);');p.write_text(s)
# Add a reversible provider choice and a single entry to the original advanced controls.
edit('services/ShellConfig.qml','property bool notchVisible:', 'property string islandProvider: "rosa"\n                property bool notchVisible:')
edit('ui/topbar/TopBar.qml','readonly property bool notchEnabled: ShellConfig.options.topbar.notchVisible','readonly property bool notchEnabled: ShellConfig.options.topbar.notchVisible && ShellConfig.options.topbar.islandProvider !== "rosa"')
edit('ui/settings/pages/TopBarPage.qml','import QtQuick\n','import QtQuick\nimport QtQuick.Controls\nimport Quickshell\n')
edit('ui/settings/pages/TopBarPage.qml','    id: root','''    id: root
    ContentSection {
        title: "Dynamic Island"
        ConfigSwitch {
            text: "Use enhanced Dynamic Island"
            checked: ShellConfig.options.topbar.islandProvider === "rosa"
            onToggled: function(v) { ShellConfig.options.topbar.islandProvider = v ? "rosa" : "classic" }
        }
        Button {
            text: "Dynamic Island settings"
            onClicked: Quickshell.execDetached(["lickintosh", "ipc", "call", "rosa", "settings"])
        }
        Button {
            text: "Preview island animations"
            onClicked: Quickshell.execDetached(["lickintosh", "ipc", "call", "island", "play", "media"])
        }
    }
''')
# Install the bridge from the local Nix integration, keeping all shell policy centralized.
import shutil
shutil.copyfile(Path(sys.argv[3]),root/'RosaIntegration.qml')
edit('shell.qml','    id: appRoot','''    id: appRoot
    RosaIntegration {
        id: rosaIsland
        enabled: appRoot.interfaceShown && appRoot.riceBarVisible && ShellConfig.options.topbar.notchVisible
                 && ShellConfig.options.topbar.islandProvider === "rosa"
        locked: lockScreen.locked
        onSettingsOpening: { appRoot.ccOpened = false; appRoot.notifCenterOpened = false; appRoot.spotlightOpened = false; NotchState.close() }
    }
''')
# Feed Rosa from the existing notification daemon; keep native notification center/history intact.
edit('ui/topbar/statusarea/notifcenter/NotifService.qml','    function pushPopup(notification) {\n        _centerModel.append({ notifObj: notification })\n        root.rebuild()','''    function pushPopup(notification) {
        _centerModel.append({ notifObj: notification })
        root.rebuild()
        if (ShellConfig.options.topbar.islandProvider === "rosa" && ShellConfig.options.topbar.notchVisible) {
            // The island consumes popup presentation, not notification tracking/history.
            if (!root.dndEnabled) RosaNotifications.receive(notification)
            if (RosaNotifications.consumePopups) return
        }
''')
p=root/'ui/topbar/statusarea/notifcenter/NotifService.qml';s=p.read_text();s=s.replace('import QtQuick', 'import qs.rosa.services as Rosa\nimport QtQuick', 1)
# Alias imported service to avoid ambiguity with native I18n/Theme names.
s=s.replace('RosaNotifications.receive(notification)','Rosa.LickNotifications.receive(notification)').replace('RosaNotifications.consumePopups','Rosa.LickNotifications.consumePopups');p.write_text(s)
(rosa/'services/LickNotifications.qml').write_text('''pragma Singleton
import Quickshell
import QtQuick
import "."
Singleton {
 readonly property bool consumePopups: IslandConfig.s("enabled") && IslandConfig.on("notif") && IslandConfig.s("eatPopups")
 function receive(n) { if (!IslandConfig.s("enabled") || !IslandConfig.on("notif")) return; NotifHistory.live=n; NotifHistory.add(n) }
}
''')
p=rosa/'services/qmldir';p.write_text(p.read_text()+'\nsingleton LickNotifications LickNotifications.qml\n')
(rosa/'services/Dnd.qml').write_text('''pragma Singleton
import Quickshell
import qs.ui.topbar.statusarea.notifcenter as Native
Singleton {
 readonly property bool active: Native.NotifService.dndEnabled
 function toggle() { Native.NotifService.dndEnabled = !Native.NotifService.dndEnabled }
 function sync() {}
}
''')
# Mirror the native timer as a virtual item while preserving Rosa's multiple timers.
p=rosa/'services/Timers.qml';s=p.read_text().replace('import QtQuick','import qs.services as Native\nimport QtQuick',1)
s=s.replace('root.items','root.localItems').replace('property var items: []','''property var localItems: []
    readonly property var nativeTimer: Native.TimerState.totalMs > 0 ? ({
        id: "lickintosh", label: "Lickintosh timer", total: Native.TimerState.totalMs / 1000,
        endsAt: Native.TimerState.endsAtMs, left: Native.TimerState.remainingMs / 1000,
        running: Native.TimerState.running, ringing: Native.TimerState.firing, muted: false
    }) : null
    readonly property var items: root.nativeTimer ? root.localItems.concat([root.nativeTimer]) : root.localItems''',1)
a=s.index('    readonly property int running:');b=s.index('    function left(',a);s=s[:a]+s[a:b].replace('root.localItems','root.items')+s[b:]
s=s.replace('return root.localItems.find(', 'return root.items.find(')
for fn,body in {
 'pause':'Native.TimerState.pause()', 'resume':'Native.TimerState.resume()',
 'toggle':'if(Native.TimerState.firing) Native.TimerState.dismissFiring(); else if(Native.TimerState.running) Native.TimerState.pause(); else Native.TimerState.resume()',
 'cancel':'Native.TimerState.cancel()', 'dismiss':'Native.TimerState.dismissFiring()',
 'restart':'Native.TimerState.start(Native.TimerState.totalMs)'
}.items():
 anchor=f'    function {fn}(id) {{'
 s=s.replace(anchor,anchor+'\n        if (id === "lickintosh") { '+body+'; return }',1)
s=s.replace('    function nudge(id, seconds) {','    function nudge(id, seconds) {\n        if (id === "lickintosh") { Native.TimerState.start(Math.max(1000,Native.TimerState.remainingMs + seconds*1000)); return }',1)
s=s.replace('    function snooze(id, seconds) {','    function snooze(id, seconds) {\n        if (id === "lickintosh") { Native.TimerState.start(Math.max(1,seconds || Prefs.timerSnoozeSec)*1000); return }',1)
p.write_text(s)
# The native OSD remains the brightness data source; Rosa handles presentation.
edit('shell.qml','        locked: lockScreen.locked','        locked: lockScreen.locked\n        brightness: _osd.brtValue')
edit('shell.qml','blocked: appRoot.ccOpened','blocked: rosaIsland.osdActive || appRoot.ccOpened')
edit('ui/osd/BatteryOSD.qml','    function _trigger() {','''    function _trigger() {
        if (ShellConfig.options.topbar.islandProvider === "rosa" && ShellConfig.options.topbar.notchVisible) return
''')
edit('rosa/design/Fonts.qml','readonly property string glyph: "JetBrainsMono Nerd Font"','readonly property string glyph: "Symbols Nerd Font Mono"')
# Right click opens configuration except while a live call reserves that gesture.
edit('rosa/services/IslandBus.qml','    signal failed(string glyph, string text)','    signal settingsRequested()\n    signal failed(string glyph, string text)')
edit('rosa/overlays/IslandWindow.qml', '''                onTapped: win.hub.endCall()
            }''', '''                onTapped: win.hub.endCall()
            }
            TapHandler {
                acceptedButtons: Qt.RightButton
                enabled: !(win.hub.kind === "call" && win.hub.callState === "live")
                onTapped: IslandBus.settingsRequested()
            }''')
# A native stopwatch is controllable from the same timer card.
p=rosa/'services/Timers.qml';s=p.read_text();s=s.replace('readonly property var items: root.nativeTimer ? root.localItems.concat([root.nativeTimer]) : root.localItems','''readonly property var nativeStopwatch: Native.StopwatchState.running || Native.StopwatchState.elapsedMs > 0 ? ({
        id: "stopwatch", label: "Stopwatch", total: 0, endsAt: 0,
        left: Native.StopwatchState.elapsedMs / 1000, running: Native.StopwatchState.running, ringing:false, muted:true
    }) : null
    readonly property var items: root.localItems.concat(root.nativeTimer ? [root.nativeTimer] : [], root.nativeStopwatch ? [root.nativeStopwatch] : [])''')
s=s.replace('    function left(t) {','    function left(t) {\n        if (t && t.id === "stopwatch") return Math.floor(Native.StopwatchState.elapsedMs / 1000)',1)
for fn,body in {'pause':'stop()','resume':'start()','toggle':'toggle()','cancel':'reset()','dismiss':'reset()','restart':'reset(); Native.StopwatchState.start()'}.items():
 s=s.replace(f'    function {fn}(id) {{',f'    function {fn}(id) {{\n        if (id === "stopwatch") {{ Native.StopwatchState.{body}; return }}',1)
p.write_text(s)
# Native recording shortcuts keep ownership of the recorder and its lifecycle.
(rosa/'services/Recorder.qml').write_text('''pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "."
Singleton {
 id:root
 property int pid:0
 property bool active:false
 property double startedAt:0
 property int elapsed:0
 property string file:""
 readonly property string monitor:Focus.screen ? Focus.screen.name : ""
 readonly property string clock:Math.floor(root.elapsed/60)+":"+String(root.elapsed%60).padStart(2,"0")
 FileView {
  path:(Quickshell.env("XDG_STATE_HOME") || Quickshell.env("HOME")+"/.local/state")+"/nixos-rice/wf-recorder.pid"
  watchChanges:true; printErrors:false
  onFileChanged:reload()
  onLoaded:{root.pid=parseInt(text().trim())||0;if(root.pid>0){root.startedAt=Date.now()/1000;check.running=true}}
  onLoadFailed:{root.pid=0;root.active=false}
 }
 Process {id:check;command:["kill","-0",String(root.pid)];onExited:code=>{root.active=code===0;if(!root.active)root.pid=0}}
 Timer {interval:1000;repeat:true;running:root.pid>0;onTriggered:{if(!check.running)check.running=true;root.elapsed=Math.max(0,Math.floor(Date.now()/1000-root.startedAt))}}
 function stop(){if(root.active)Quickshell.execDetached(["rice-shell","action","screen-record"])}
}
''')
# General preferences needed by island events are editable beside the provider choice.
edit('ui/settings/pages/TopBarPage.qml','import Quickshell\n','import Quickshell\nimport qs.rosa.services as Rosa\n')
edit('ui/settings/pages/TopBarPage.qml','        title: "Dynamic Island"','''        title: "Dynamic Island"
        ConfigSwitch {
            text: "Island sound effects"
            checked: Rosa.Prefs.sfxEnabled
            onToggled: function(v) { Rosa.Prefs.set("sfxEnabled",v) }
        }
        ConfigSwitch {
            text: "Weather alerts"
            checked: Rosa.Prefs.weatherEnabled
            onToggled: function(v) { Rosa.Prefs.set("weatherEnabled",v) }
        }
        TextField {
            placeholderText: "Weather location (city or city,country)"
            text: Rosa.Prefs.weatherPlace
            onEditingFinished: Rosa.Prefs.set("weatherPlace",text.trim())
        }
''')

# Spectrum capture is not a real application using the microphone.
edit('services/MediaCaptureState.qml', '            var appName = props["application.name"] || props["node.description"] || props["node.name"] || "Application"',
     '            var appName = props["application.name"] || props["node.description"] || props["node.name"] || "Application"\n            if (String(appName).toLowerCase().indexOf("cava") === 0) continue')
# Clipboard previews are opt-in, with the upstream secret filter and an event-driven watcher.
edit('rosa/services/IslandConfig.qml','srcClip:     { type: "bool", def: true }','srcClip:     { type: "bool", def: false }')
edit('rosa/overlays/IslandSources.qml','running: src.clipOn && !Islandd.alive','running: src.clipOn')
# Media selection is bound to native MPRIS; paused playback needs no polling.
edit('rosa/services/Media.qml','        running: true','        running: root.playing')
# Prevent configured tall cards from being clipped by a fixed layer-shell surface.
edit('rosa/overlays/IslandWindow.qml','    implicitHeight: 320','''    implicitHeight: Math.min(win.modelData.height, Math.max(320,
        IslandConfig.s("mediaBigHeight") + IslandConfig.s("offsetY") + 80,
        IslandConfig.s("wideHeight") + IslandConfig.s("offsetY") + 80))''')
# Include native ringing alarms in the original Rosa alarm card.
p=rosa/'services/Timers.qml';s=p.read_text().replace('id: "stopwatch", label: "Stopwatch", total: 0, endsAt: 0,','id: "stopwatch", label: "Stopwatch", total: 0, endsAt: Number.MAX_SAFE_INTEGER,')
s=s.replace('    readonly property var items: root.localItems.concat(root.nativeTimer ? [root.nativeTimer] : [], root.nativeStopwatch ? [root.nativeStopwatch] : [])','''    readonly property var nativeAlarm: Native.AlarmState.firingAlarmId !== "" ? ({
        id:"native-alarm",label:"Alarm",total:0,endsAt:0,left:0,running:false,ringing:true,muted:false
    }) : null
    readonly property var items: root.localItems.concat(root.nativeTimer ? [root.nativeTimer] : [], root.nativeStopwatch ? [root.nativeStopwatch] : [], root.nativeAlarm ? [root.nativeAlarm] : [])''')
for fn in ['dismiss','cancel']:
 s=s.replace(f'    function {fn}(id) {{',f'    function {fn}(id) {{\n        if(id === "native-alarm") {{ Native.AlarmState.dismissFiringAlarm(); return }}',1)
s=s.replace('    function dismissAll() {\n        for (const t of root.localItems.slice())','    function dismissAll() {\n        for (const t of root.items.slice())')
s=s.replace('    function snooze(id, seconds) {','    function snooze(id, seconds) {\n        if(id === "native-alarm") { Native.AlarmState.snoozeFiringAlarm(Math.max(1,Math.round((seconds||300)/60))); return }',1)
p.write_text(s)
# Respect the existing manually enabled game mode as well as fullscreen game detection.
p=rosa/'services/Stage.qml';s=p.read_text().replace('import QtQuick','import qs.services as Native\nimport QtQuick',1)
s=s.replace('root.gaming = game;', 'root.gaming = game || Native.GameMode.enabled;')
s=s.replace('    property bool gaming: false','    property bool gaming: false\n    Connections { target: Native.GameMode; function onEnabledChanged() { root.recompute() } }',1)
p.write_text(s)
# Fix upstream cross-parent anchors in optional expanded cards.
edit('rosa/overlays/cards/OsdCard.qml','anchors.right: osdValue.left','anchors.right: osdValueBox.left')
edit('rosa/overlays/cards/OsdCard.qml','''    Item {
        anchors.right: parent.right
        anchors.rightMargin: 8''','''    Item {
        id: osdValueBox
        anchors.right: parent.right
        anchors.rightMargin: 8''')
p=rosa/'panels/SysRings.qml';s=p.read_text();a=s.index('                        Text {\n                            anchors.baseline: wNow.baseline');s=s[:a]+s[a:].replace('anchors.baseline: wNow.baseline','anchors.verticalCenter: parent.verticalCenter',1);p.write_text(s)
# Optional git-activity calendar data should be silent when the user has no producer.
p=rosa/'panels/Calendar.qml';s=p.read_text().replace('path: Quickshell.env("HOME") + "/.cache/git-activity.json"','printErrors: false\n        path: Quickshell.env("HOME") + "/.cache/git-activity.json"');p.write_text(s)
# Validate advanced settings at the model boundary, including direct IPC calls.
edit('rosa/services/IslandConfig.qml','''    function setStyle(name, value) {
        const next = {};''','''    function setStyle(name, value) {
        const sp = root.spec[name];
        if (!sp) return;
        if (sp.type === "bool") value = value === true;
        else if (sp.type === "int") {
            value = Number(value);
            if (!isFinite(value)) return;
            value = Math.max(sp.min, Math.min(sp.max, Math.round(value)));
        } else if (sp.type === "pick" && sp.values.indexOf(value) < 0) return;
        const next = {};''')
# All advanced controls live in the existing settings application.
shutil.copyfile(Path(sys.argv[4]),root/'ui/settings/pages/RosaPage.qml')
edit('settings.qml','{ name: "Top Bar",','{ name: "Dynamic Island", icon: "settings/notch.svg", component: "RosaPage", implemented: true },\n                { name: "Top Bar",')
edit('settings.qml','case "TopBarPage":    return _topbarComp','case "RosaPage": return _rosaComp\n                                case "TopBarPage":    return _topbarComp')
edit('settings.qml','    Component { id: _topbarComp; TopBarPage {} }','    Component { id: _rosaComp; RosaPage {} }\n    Component { id: _topbarComp; TopBarPage {} }')
# Fill missing upstream English labels; avoid exposing internal option names.
import json
p=rosa/'lang/en.json';table=json.loads(p.read_text())
for name,label in {'srcTask':'Task progress','srcSys':'System load and temperature','srcShot':'Screenshots','srcWeather':'Weather alerts'}.items():
 table['isle.o.'+name]=label
for name in re.findall(r'^        (\w+):\s+\{ type:',(rosa/'services/IslandConfig.qml').read_text(),re.M):
 table.setdefault('isle.o.'+name,re.sub(r'(?<=[a-z])(?=[A-Z])',' ',name).capitalize())
p.write_text(json.dumps(table,ensure_ascii=False,indent=2))
# Notify only on completed screenshot files, with no periodic directory scan.
(rosa/'watch-screenshots.py').write_text('''import ctypes,os,struct,json,signal
from pathlib import Path
folder=Path.home()/"Pictures/Screenshots"
folder.mkdir(parents=True,exist_ok=True)
libc=ctypes.CDLL(None,use_errno=True)
libc.prctl(1,signal.SIGTERM,0,0,0)
if os.getppid()==1:raise SystemExit(0)
fd=libc.inotify_init1(os.O_CLOEXEC)
if fd<0:raise OSError(ctypes.get_errno(),"inotify")
if libc.inotify_add_watch(fd,os.fsencode(folder),0x8|0x80)<0:raise OSError(ctypes.get_errno(),"watch")
while True:
 data=os.read(fd,65536);offset=0
 while offset+16<=len(data):
  wd,mask,cookie,length=struct.unpack_from("iIII",data,offset)
  name=os.fsdecode(data[offset+16:offset+16+length].split(bytes([0]),1)[0]);offset+=16+length
  if not name or name.startswith("."):continue
  path=folder/name
  if path.suffix.lower() in (".png",".jpg",".jpeg",".webp") and path.is_file():print(json.dumps(str(path)),flush=True)
''')
# Native alert fallback remains available when Rosa is disabled in its own settings.
p=root/'ui/osd/BatteryOSD.qml';s=p.read_text().replace('import QtQuick','import qs.rosa.services as Rosa\nimport QtQuick',1)
s=s.replace('if (ShellConfig.options.topbar.islandProvider === "rosa" && ShellConfig.options.topbar.notchVisible) return','if (ShellConfig.options.topbar.islandProvider === "rosa" && ShellConfig.options.topbar.notchVisible && Rosa.IslandConfig.s("enabled") && Rosa.IslandConfig.on("power")) return');p.write_text(s)
# Honour Rosa's bar-takeover option without hiding or replacing native bar controls.
edit('rosa/services/IslandBus.qml','    property bool locked: false','''    property bool locked: false
    property var expandedScreens: ({})
    function setExpanded(screen, on) {
        const next=Object.assign({},expandedScreens);
        if(on) next[screen]=true; else delete next[screen];
        expandedScreens=next;
    }''')
edit('rosa/overlays/IslandWindow.qml','    onWideChanged: {','    onWideChanged: {\n        IslandBus.setExpanded(win.modelData.name,win.visible && win.wide)')
edit('rosa/overlays/IslandWindow.qml','    Component.onDestruction: {','    Component.onDestruction: {\n        IslandBus.setExpanded(win.modelData.name,false)')
edit('rosa/overlays/IslandWindow.qml','    property bool opened: false','    onVisibleChanged: IslandBus.setExpanded(win.modelData.name,win.visible && win.wide)\n    property bool opened: false')
p=root/'ui/topbar/TopBar.qml';s=p.read_text().replace('import QtQuick\n','import QtQuick\nimport qs.rosa.services as Rosa\n',1)
s=s.replace('opacity: NotchState.expanded ? 0 : 1','opacity: NotchState.expanded || root.rosaTakeover ? 0 : 1').replace('enabled: !NotchState.expanded','enabled: !NotchState.expanded && !root.rosaTakeover')
s=s.replace('    readonly property alias notchExpandedPanel:', '''    readonly property bool rosaTakeover: ShellConfig.options.topbar.islandProvider === "rosa"
        && ShellConfig.options.topbar.notchVisible && Rosa.IslandConfig.s("enabled")
        && Rosa.IslandConfig.s("barTakeover") && root.hostWindow && root.hostWindow.screen
        && Rosa.IslandBus.expandedScreens[root.hostWindow.screen.name] === true
    readonly property alias notchExpandedPanel:''',1)
p.write_text(s)
# Use the user's configured desktop file handler instead of Rosa's optional Yazi setup.
edit('rosa/overlays/Island.qml','Quickshell.execDetached(["kitty", "--class", "yazi", "-e", "yazi", root.downloadPath]);','Quickshell.execDetached(["xdg-open", root.downloadPath]);')

# Capture helpers must exit with the owning shell, including forced shell stops.
edit('rosa/services/Cava.qml','command: ["cava", "-p", root.config]','command: ["setpriv", "--pdeathsig", "TERM", "cava", "-p", root.config]')
edit('rosa/services/MicLevel.qml','command: ["sh", "-c",','command: ["setpriv", "--pdeathsig", "TERM", "sh", "-c",')

# The dock has one authoritative visibility switch, in the existing Dock settings page.
# Do not expose the independent, unused Rosa desktop dock preferences.
p=root/'ui/settings/pages/TopBarPage.qml';s=p.read_text()
pattern=re.compile(r'        ConfigSwitch \{(?:(?!\n        \}).)*?ShellConfig\.options\.dockAppearance\.enable(?:(?!\n        \}).)*?\n        \}\n',re.S)
s=pattern.sub('',s);p.write_text(s)
# Island controls have a dedicated native settings page; remove their Top Bar duplicates.
p=root/'ui/settings/pages/TopBarPage.qml';s=p.read_text()
for marker in ['        title: "Dynamic Island"','        title: I18n.tr("Notch")']:
    at=s.find(marker)
    if at<0:raise ValueError('Missing duplicate Top Bar section: '+marker)
    start=s.rfind('    ContentSection {',0,at)
    begin=s.index('{',start);depth=1;end=begin+1
    while depth:
        if s[end]=='{':depth+=1
        elif s[end]=='}':depth-=1
        end+=1
    s=s[:start]+s[end:]
p.write_text(s)
