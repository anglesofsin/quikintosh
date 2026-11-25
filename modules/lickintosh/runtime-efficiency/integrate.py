"""Keep idle UI work bounded while preserving live capture and animation cadence."""
from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent

def write(name,s):
 p=root/name
 if p.exists():p.chmod(p.stat().st_mode|0o200)
 p.write_text(s)
def edit(name,old,new):
 s=(root/name).read_text();assert old in s,(name,old[:70]);write(name,s.replace(old,new))

# Unchanged filesystem replies must not reconstruct every Dock tile.
p='tahoedock/TahoeDockSurface.qml'
edit(p,"else if(e.type==='preview'){const next=Object.assign({},root.folderPreviews);next[e.folder]=e.items;root.folderPreviews=next}","else if(e.type==='preview'){if(JSON.stringify(root.folderPreviews[e.folder] || [])!==JSON.stringify(e.items)){const next=Object.assign({},root.folderPreviews);next[e.folder]=e.items;root.folderPreviews=next}}")
edit(p,"else if(e.type==='trash'){root.trashCount=e.count;previewsDelay.restart();if(root.stackOpen && root.folder==='trash')stackRefresh.restart()}","else if(e.type==='trash'){if(root.trashCount!==e.count){root.trashCount=e.count;previewsDelay.restart();if(root.stackOpen && root.folder==='trash')stackRefresh.restart()}}\n    else if(e.type==='thumbnailRetry'){previewsDelay.restart();if(root.stackOpen)stackRefresh.restart()}")
edit(p,'Timer {interval:2500;running:root.options.showTrash;', 'Timer {interval:30000;running:root.options.showTrash;')
edit(p," property var identityClients:[]", " property var identityClients:[]\n property string identitySignature:''")
edit(p,"  send({action:'identities',clients:identityClients})", "  const signature=JSON.stringify(identityClients);if(signature===identitySignature)return;identitySignature=signature\n  send({action:'identities',clients:identityClients})")
edit('ui/dock/Dock.qml','        dockRoot.groupedClients = result','        if(JSON.stringify(dockRoot.groupedClients)!==JSON.stringify(result))dockRoot.groupedClients = result')
# Hidden, prewarmed panels keep their controls but not duplicate desktop images.
edit('components/glass/DesktopSnapshot.qml','model: DesktopFiles.layout','model: root.shown ? DesktopFiles.layout:[]')
# The status icon shares the existing network service instead of another
# nmcli monitor + shell/grep/cut subprocess chain per display.
p='ui/topbar/statusarea/wifi/Wifi.qml';s=(root/p).read_text();a=s.index('    property int networkStrength:');b=s.index('    property string networkIcon:',a)
s=s[:a]+'''    readonly property int networkStrength:NetworkManager.active?.signal || 0
    readonly property bool nmcliExists:true

'''+s[b:];write(p,s)
# Merge bursts of NetworkManager signals into a single refresh batch.
p='services/NetworkManager.qml';s=(root/p).read_text();a=s.index('        id: _monitor\n');b=s.index('        onExited:',a);old=s[a:b]
a1=old.index('                _getNetworks.running');b1=old.index('\n            }',a1);oldbody=old[a1:b1];s=s.replace(old,old.replace(oldbody,'                networkEventBatch.restart()'),1)
s=s.replace('    Timer {\n        id: _monitorRestartTimer', '    Timer{id:networkEventBatch;interval:180;onTriggered:{_getNetworks.running=true;_getKnown.running=true;_wifiStatus.running=true;_getEthernet.running=true}}\n\n    Timer {\n        id: _monitorRestartTimer',1);write(p,s)
# DDC transactions are slow hardware I/O. Shell hotkeys already update the
# watched value file immediately; external changes only need an idle fallback.
edit('services/BrightnessController.qml','Timer{interval:5000;running:true;', 'Timer{interval:30000;running:true;')
# Stable geometry inventory: live screencopy remains untouched. During movement
# retain the native fast path; stationary checks publish/refresh only changes.
p='components/glass/GlassTracker.qml';s=(root/p).read_text()
s=s.replace('    property int captureUsers: 0','    property int inventoryUsers:0\n    property int captureUsers: 0',1)
s=s.replace('    property var clientsSnapshot: []','''    property var clientsSnapshot: []
    property string clientsSignature:""
    property string latestGeometry:""
    property string nativeGeometry:""
    property bool nativePending:false
    property int nativeRefreshes:0
    property int clientQueries:0
    function geometrySignature(data){return JSON.stringify(data.map(c=>[c.address,c.pid,c.class,c.at,c.size,c.monitor,c.workspace?.id,c.workspace?.name,c.hidden,c.mapped,c.floating,c.pinned,c.fullscreen,c.focusHistoryID]))}
    function refreshNativeIfChanged(){
        if(!nativePending || !latestGeometry || nativeGeometry===latestGeometry)return
        nativePending=false;nativeGeometry=latestGeometry;nativeRefreshes++;Hyprland.refreshToplevels()
    }''',1)
s=s.replace('onStreamFinished:{try {root.clientsSnapshot=JSON.parse(text)} catch(_){};root.clientsUpdated=Date.now();root.snapshotSerial++}', '''onStreamFinished:{
                try{
                    const data=JSON.parse(text),signature=JSON.stringify(data)
                    if(signature!==root.clientsSignature){root.clientsSignature=signature;root.clientsSnapshot=data}
                    root.latestGeometry=root.geometrySignature(data);root.refreshNativeIfChanged()
                }catch(_){}
                root.clientQueries++;root.clientsUpdated=Date.now();root.snapshotSerial++
            }''',1)
s=s.replace('try { root.monitorSnapshots = JSON.parse(this.text) }','try { const data=JSON.parse(this.text);if(JSON.stringify(data)!==JSON.stringify(root.monitorSnapshots))root.monitorSnapshots=data }',1)
s=s.replace('    function refreshWindows() {\n        Hyprland.refreshToplevels()\n    }','''    function refreshWindows() {
        if(root.precisionUsers>0 || root.fast){root.nativeGeometry="";root.nativeRefreshes++;Hyprland.refreshToplevels();return}
        root.nativePending=true;root.captureSnapshot();if(!clientsQuery.running)root.refreshNativeIfChanged()
    }''',1)
s=s.replace('running: root.captureUsers > 0','running: root.captureUsers > 0 || root.inventoryUsers>0',1)
s=s.replace('            root.refreshWindows()\n        }\n    }\n}', '            if(root.captureUsers>0)root.refreshWindows();else root.captureSnapshot()\n        }\n    }\n}',1)
s=s.replace('    property bool fast: false','    onInventoryUsersChanged:if(inventoryUsers>0){root.refreshMonitorSnapshot();root.captureSnapshot()}\n    property bool fast: false',1)
s=s.replace('    property string clientsSignature:', '''    IpcHandler{target:"performance";function status():string{return JSON.stringify({captureUsers:root.captureUsers,inventoryUsers:root.inventoryUsers,precisionUsers:root.precisionUsers,nativeRefreshes:root.nativeRefreshes,clientQueries:root.clientQueries,fast:root.fast})}}
    property string clientsSignature:''',1)
write(p,s)
# Fullscreen privacy consumes the shared inventory, not a parallel polling loop.
# The component is installed under ui/overlays by the feedback stage.
paths=list(root.rglob('FullscreenPrivacy.qml'));assert len(paths)==1,paths
p=str(paths[0].relative_to(root))
write(p,'''import QtQuick
import Quickshell
import Quickshell.Wayland
import qs.services
import qs.components.glass
Scope{
 id:root
 readonly property bool watching:MediaCaptureState.islandActive
 property bool held:false
 function sync(){if(watching===held)return;held=watching;GlassTracker.inventoryUsers=Math.max(0,GlassTracker.inventoryUsers+(held ? 1:-1))}
 onWatchingChanged:sync()
 Component.onCompleted:sync()
 Component.onDestruction:if(held)GlassTracker.inventoryUsers=Math.max(0,GlassTracker.inventoryUsers-1)
 readonly property var full:{const map={};for(const m of GlassTracker.monitorSnapshots)map[m.name]=GlassTracker.clientsSnapshot.some(c=>c.monitor===m.id && c.fullscreen===2 && (c.workspace?.id===m.activeWorkspace?.id || c.workspace?.id===m.specialWorkspace?.id));return map}
 Variants{model:Quickshell.screens;delegate:PanelWindow{
  required property var modelData
  screen:modelData;visible:MediaCaptureState.islandActive && !!root.full[modelData.name]
  anchors{top:true;right:true}implicitWidth:18;implicitHeight:18;color:'transparent'
  exclusionMode:ExclusionMode.Ignore;WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.namespace:'lickintosh-fullscreen-privacy';mask:Region{}
  Rectangle{anchors.centerIn:parent;width:5;height:5;radius:2.5;color:MediaCaptureState.indicatorColor}
 }}
}
''')
edit('rosa/overlays/IslandWindow.qml','running:IslandConfig.s("hideFull") && !IslandBus.locked','running:IslandConfig.s("hideFull") && !IslandBus.locked && !Hyprland.monitorFor(win.modelData)')
# Performance graphs are sampled only for real visible consumers, not snapshots
# or every tile in the hidden widget gallery.
edit('services/ResourcesState.qml','    id: root','''    id: root
    property int watchers:0
    function watch(active){watchers=Math.max(0,watchers+(active ? 1:-1))}''')
edit('services/ResourcesState.qml','running: !GameMode.enabled','running: root.watchers>0 && !GameMode.enabled')
for name,condition in [('ui/widgets/types/UtilityWidget.qml',"['storage','system'].includes(root.mode)"),('ui/widgets/types/BatteryWidget.qml','true'),('ui/topbar/notch/dashboard/PerformancePage.qml','true')]:
 s=(root/name).read_text();extra=''
 if 'property bool isSnapshot:' not in s:extra='    property bool isSnapshot:false\n'
 block='''
    QtObject{
        id:resourceWatch
        readonly property bool active:root.visible && !!root.Window.window?.visible && !root.isSnapshot && CONDITION
        property bool held:false
        function sync(){if(active===held)return;held=active;ResourcesState.watch(held)}
        onActiveChanged:sync()
        Component.onCompleted:sync()
        Component.onDestruction:if(held)ResourcesState.watch(false)
    }
'''.replace('CONDITION',condition)
 s=s.replace('    id: root','    id: root\n'+extra+block,1) if '    id: root' in s else s.replace(' id:root',' id:root\n'+extra+block,1)
 if name.endswith('UtilityWidget.qml'):s=s.replace("readonly property var metrics:mode==='storage'", "readonly property var metrics:!['storage','system'].includes(mode) ? []:mode==='storage'")
 if name.endswith('BatteryWidget.qml'):s=s.replace('root.size === "l"','root.size === "l" && root.visible && !!root.Window.window?.visible && !root.isSnapshot')
 write(name,s)
# Share one MPRIS position clock. Hidden/snapshot media tiles must not hold it.
p='ui/widgets/types/MediaWidget.qml';s=(root/p).read_text();s=s.replace('    Component.onCompleted: MprisState.watchPosition(true)','''    property bool isSnapshot:false
    readonly property bool needsPosition:visible && !!root.Window.window?.visible && !isSnapshot
    property bool positionHeld:false
    function syncPosition(){if(needsPosition===positionHeld)return;positionHeld=needsPosition;MprisState.watchPosition(positionHeld)}
    onNeedsPositionChanged:syncPosition()
    Component.onCompleted:syncPosition()''').replace('        MprisState.watchPosition(false)','        if(root.positionHeld)MprisState.watchPosition(false)');write(p,s)
p='rosa/services/Media.qml';s=(root/p).read_text();a=s.index('    Timer {\n        interval: 1000');b=s.index('    Component.onCompleted:',a)
s=s[:a]+'''    property bool positionHeld:false
    readonly property bool needsPosition:root.playing && root.hasPosition
    function syncPosition(){if(positionHeld===needsPosition)return;positionHeld=needsPosition;Native.MprisState.watchPosition(positionHeld)}
    onNeedsPositionChanged:syncPosition()
    Component.onDestruction:if(positionHeld)Native.MprisState.watchPosition(false)

'''+s[b:];s=s.replace('Component.onCompleted: pick()','Component.onCompleted:{pick();syncPosition()}');write(p,s)
# Keep one metadata monitor, merge PipeWire deltas off the UI thread, and send
# heartbeats without reparsing the full graph. The privacy classifier is intact.
write('tools/pipewire-watch.py',(here/'pipewire_watch.py').read_text())
p='services/MediaCaptureState.qml';s=(root/p).read_text().replace('data=JSON.parse(text)','data=Array.isArray(text) ? text:JSON.parse(text)');a=s.index(' Process{id:dump;');s=s[:a]+''' Process{
  id:monitor;running:true;command:['PYTHON',Quickshell.shellDir+'/tools/pipewire-watch.py']
  stdout:SplitParser{onRead:line=>{try{
   const event=JSON.parse(line)
   if(event.type==='state')root._parse(event.data)
   else if(event.type==='heartbeat')AudioActivity.fresh()
   else if(event.type==='unavailable'){root._parse('[]');AudioActivity.checked=false}
  }catch(error){console.warn('PipeWire metadata:',error)}}}
  onExited:{root._parse('[]');AudioActivity.checked=false;retry.restart()}
 }
 Timer{id:retry;interval:2000;onTriggered:monitor.running=true}
}
'''.replace("'PYTHON'",repr(sys.executable));write(p,s)
p='services/AudioActivity.qml';s=(root/p).read_text().replace(' function observe(data){',' function fresh(){checked=true;stale.restart()}\n function observe(data){').replace('apps=next','if(JSON.stringify(next)!==JSON.stringify(apps))apps=next');write(p,s)
# Hidden prewarmed windows must not run per-frame mapToItem work. Visible
# surfaces retain frame-accurate coordinates during every transform animation.
for name in ['components/glass/TahoeGlass.qml','components/glass/LiquidGlass.qml']:
 edit(name,'        ignoreUnknownSignals: true','        ignoreUnknownSignals: true\n        enabled:root.visible && !!root.backdrop && root.backdrop.ready && !!root.Window.window?.visible')
for name in ['components/glass/TahoeGlass.qml','components/glass/LiquidGlass.qml']:
 edit(name,'    onVisibleChanged: invalidate()','    onVisibleChanged:{if(visible)updatePosition();invalidate()}')
# Present the first CC frame only after its backdrop is ready, and start its
# opening animation then, rather than showing an untextured intermediate card.
p='ui/topbar/statusarea/controlcenter/ControlCenter.qml'
edit(p,'GlassBackdrop { id: ccBackdrop; element: "cc"; gateEnabled:false }','GlassBackdrop { id: ccBackdrop; element: "cc" }')
edit(p,'showProgress = root.opened ? 1 : 0','showProgress = root.opened && ccBackdrop.revealed ? 1 : 0')
edit(p,'                    property real showProgress: 0','''                    Connections{target:ccBackdrop;function onRevealedChanged(){if(root.opened && ccBackdrop.revealed)ccContent.showProgress=1}}
                    property real showProgress: 0''')
edit(p,'        if (opened) {\n            _ccCloseTimer.stop()','        if (opened) {\n            BrightnessController.refresh()\n            _ccCloseTimer.stop()')
# Keep capture through the Dock's exit animation; warm the next scene before
# sliding the Dock in. No plain-material -> glass fade and no hidden capture loop.
p='tahoedock/TahoeDockSurface.qml';s=(root/p).read_text();s='import qs.components\n'+s
s=s.replace(' property bool revealed:false',''' Presence{id:dockGlassPresence;wanted:dock.shown;exitDuration:160}
 property bool glassPresented:false
 property int glassFrames:0
 readonly property bool displayShown:dock.shown && (Theme.plainSurfaces || glassPresented)
 Connections{target:dockGlassPresence;function onPresentChanged(){if(!dockGlassPresence.present){root.glassPresented=false;root.glassFrames=0}}}
 FrameAnimation{running:dock.shown && !Theme.plainSurfaces && dockGlass.captureSettled && !root.glassPresented;onTriggered:if(++root.glassFrames>=2)root.glassPresented=true}
 property bool revealed:false''',1)
s=s.replace('ready:!Theme.plainSurfaces && dock.shown;', 'instantReveal:true;ready:!Theme.plainSurfaces && dockGlassPresence.present;',1)
s=s.replace("monitorName:dock.screen.name;element:'dock';captureWindows:","captureRegion:Qt.rect(root.origin.x+plate.x,root.origin.y+plate.y,plate.width,plate.height)\n   monitorName:dock.screen.name;element:'dock';captureWindows:",1)
s=s.replace('   id:plate\n','   id:plate\n   visible:Theme.plainSurfaces || root.glassPresented\n',1)
s=s.replace('x:!dock.shown && root.vertical','x:!root.displayShown && root.vertical').replace('y:!dock.shown && !root.vertical','y:!root.displayShown && !root.vertical')
s=s.replace('automatic:options.hoverToReveal,visible:dock.shown,','automatic:options.hoverToReveal,visible:dock.shown,presented:root.displayShown,glassReady:dockGlass.captureSettled,')
write(p,s)
# The old image-choice dropdown no longer has consumers; media/folder pickers
# use their own demand-driven library. Do not recursively scan wallpapers twice.
p='services/WidgetState.qml';s=(root/p).read_text();a=s.index('    function refreshImages() {');b=s.index('    function resizeWidgetTo(',a)
s=s[:a]+s[b:];s=s.replace('    property var imageChoices: []\n\n','');write(p,s)
# Clipboard listings reuse hashes of unchanged files and read short text previews
# directly, instead of a shell/ls/cksum/cut/tr subprocess chain for every entry.
write('tools/clipboard-history.py',(here/'clipboard_history.py').read_text())
p='ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=(root/p).read_text();a=s.index('    function refreshClipHistory() {');b=s.index('    Process {\n        id: clipListProc',a)
s=s[:a]+'''    function refreshClipHistory(){
        clipListProc.command=['PYTHON',Quickshell.shellDir+'/tools/clipboard-history.py',root.clipDir,String(ShellConfig.options.spotlight.clipboard.maxEntries)]
        clipListProc.running=true
    }

'''.replace("'PYTHON'",repr(sys.executable))+s[b:];write(p,s)
# A closed Wayland toplevel must never be used to restart a screencopy stream.
# Repeated compositor refusals back off instead of creating an 80 ms retry loop.
p='components/glass/GlassWindows.qml';s=(root/p).read_text()
s=s.replace('            property bool restarting: false','''            property bool sourceClosed:false
            property int restartFailures:0
            readonly property var windowSource:modelData.wayland
            onWindowSourceChanged:if(windowSource){sourceClosed=false;restartFailures=0}
            Connections{
                target:view.windowSource
                ignoreUnknownSignals:true
                function onClosed(){view.sourceClosed=true;restartTimer.stop();view.restarting=false}
            }
            onHasContentChanged:if(hasContent)restartFailures=0
            property bool restarting: false''',1)
s=s.replace('            function restart() {\n                restarting = true\n                restartTimer.start()','''            function restart() {
                if(sourceClosed || !shown || restarting)return
                restartFailures++
                restarting = true
                restartTimer.restart()''',1)
s=s.replace('id: restartTimer\n                interval: 80','id: restartTimer\n                interval:Math.min(4000,80*Math.pow(2,Math.min(6,Math.max(0,view.restartFailures-1))))',1)
s=s.replace('&& !restarting && !dying ? modelData.wayland','&& !restarting && !dying && !sourceClosed ? modelData.wayland',1).replace('live: gate.wanted && !restarting && !dying','live: gate.wanted && !restarting && !dying && !sourceClosed',1).replace('if (gate.wanted && !dying) view.restart()','if (gate.wanted && !dying && !sourceClosed) view.restart()',1)
write(p,s)
