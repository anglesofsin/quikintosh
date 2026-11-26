"""Apply final interaction policy after the upstream UI integration stages."""
import shutil

def interaction_edit(name, before, after):
    path=root/name
    text=path.read_text()
    assert text.count(before)==1,(name,before[:70],text.count(before))
    path.write_text(text.replace(before,after,1))

# Detecting an existing call after startup is state hydration, never a join.
# Incoming calls and explicit clicks retain their own presentation path.
interaction_edit('rosa/overlays/Island.qml',
    'root.voicePeek=VoiceCalls.active && IslandConfig.s("voiceJoin")',
    'root.voicePeek=false')
interaction_edit('rosa/overlays/IslandWindow.qml',
    '|| (win.hovering && IslandConfig.s("hoverWide")\n                && !win.hushed)',
    '|| false')

# Avoid exposing the upstream French source strings before catalogs arrive.
interaction_edit('services/I18n.qml','    property var catalog: ({})',
    '    property bool ready:false\n    onLangChanged:{root.ready=false;root.catalog=({})}\n    property var catalog: ({})')
interaction_edit('services/I18n.qml','root.catalog = JSON.parse(file.text())',
    'root.catalog = JSON.parse(file.text()); root.ready=true')
interaction_edit('services/I18n.qml','onLoadFailed: root.catalog = ({})',
    'onLoadFailed: {root.catalog=({});root.ready=true}')
spot='ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
interaction_edit(spot,'visible: root.currentWallpaper === "" && !GlassWallpaper.videoActive',
    'visible: ShellConfig.ready && I18n.ready && bgWin.source === "" && !GlassWallpaper.videoActive')
# Add the missing Portuguese sentence (French keys map through the EN catalog).
path=root/'assets/i18n/pt_BR.json'
import json
catalog=json.loads(path.read_text())
catalog["Choisis une image dans Réglages › Fond d'écran, ou ajoute-en dans"]='Escolha uma imagem em Ajustes › Papel de parede ou adicione imagens em'
path.write_text(json.dumps(catalog,ensure_ascii=False,indent=1)+'\n')

# Keep indexing and ranking off the GUI thread. The field itself never waits
# on the 50k+ path inventory or on rendering the result delegate tree.
(root/'ui/topbar/statusarea/spotlight/SearchWorker.js').write_text((root/'ui/topbar/statusarea/spotlight/Search.js').read_text()+'\n'+(source/'SearchWorker.js').read_text())
interaction_edit(spot,'import QtQuick\n','import QtQuick\nimport QtQml.WorkerScript\n')
interaction_edit(spot,'readonly property var searchableFileIndex:FileSearch.indexPaths(root.fileIndex)', '''property string fileQuery:""
    property int searchSerial:0
    property string completedQuery:""
    property var fileMatches:[]
    onFileIndexChanged:fileSearchWorker.sendMessage({type:"index",paths:root.fileIndex})
    function queueFileSearch(query){root.fileQuery=query;fileSearchDelay.restart()}
    Timer{id:fileSearchDelay;interval:25;onTriggered:{
        if(root.fileQuery.trim()===""){root.completedQuery="";root.fileMatches=[];root.searchSerial++;return}
        fileSearchWorker.sendMessage({type:"search",query:root.fileQuery,serial:++root.searchSerial})
    }}
    WorkerScript {
        id:fileSearchWorker
        source:"SearchWorker.js"
        onMessage:message=>{
            if(message.type==="indexed"){if(root.fileQuery)fileSearchDelay.restart();return}
            if(message.serial!==root.searchSerial || message.query!==root.fileQuery)return
            root.completedQuery=message.query;root.fileMatches=message.paths
            const win=spotlightLoader.item
            if(win && win.selectedAction==="files")win.refreshFiles(message.query)
        }
    }''')
interaction_edit(spot,'return FileSearch.search(root.searchableFileIndex,query,limit)',
    'return query===root.completedQuery ? root.fileMatches.slice(0,limit || 30):[]')
interaction_edit(spot,'                                    onTextChanged: {\n                                        var t = text',
    '                                    onTextChanged: {\n                                        root.queueFileSearch(text)\n                                        var t = text')
# Release focus at the beginning of closing; ensure mapping precedes item focus.
interaction_edit(spot,'                    showAnim.start()\n                    searchField.forceActiveFocus()',
    '                    searchField.forceActiveFocus()\n                    showAnim.start()')

# Invisible, retained backgrounds must not retain live foreign-toplevel streams.
# Every new stream is attached only to a currently live source.
path=root/'components/glass/GlassWindows.qml'
text=path.read_text()
text=text.replace('captureSource: (gate.armed || view.sourceRetained) && view.onScreen',
                  'captureSource: root.capturing && (gate.armed || view.sourceRetained) && view.onScreen')
text=text.replace('function captureFrame(){view.captureFrame()}',
                  'function captureFrame(){if(root.capturing && view.windowSource && !view.sourceClosed && !view.dying)view.captureFrame()}')
text=text.replace('onRequestFrame: view.captureFrame()',
                  'onRequestFrame: if(root.capturing && view.windowSource && !view.sourceClosed && !view.dying)view.captureFrame()')
path.write_text(text)

# Keep the surface mapped until the horizontal dismissal has finished. Qt's
# property animation can also reverse mid-flight without resuming stale springs.
interaction_edit('rosa/overlays/IslandWindow.qml',
    '        id: fold\n        response: 0.5',
    '        id: fold\n        enabled: false\n        response: 0.5')
interaction_edit('rosa/overlays/IslandWindow.qml',
    '    readonly property bool idleEligible:',
    """    readonly property bool presentationWanted:win.mine && win.wanted && IslandConfig.s("enabled") && !win.blocked && !IslandBus.locked
    property real presentationProgress:presentationWanted ? 1:0
    onPresentationWantedChanged:{
        if(!presentationWanted){win.dashboardRequested=false;win.forced=false;win.hub.voicePeek=false}
        else {fold.land();birth.land()}
    }
    Behavior on presentationProgress {NumberAnimation {duration:NativeSettings.SettingsPreferences.accessibility.reduceMotion ? 0:160;easing.type:Easing.OutCubic}}
    readonly property bool idleEligible:""")
path=root/'rosa/overlays/IslandWindow.qml'
text=path.read_text().replace('visible: !win.blocked && !IslandBus.locked','visible: win.presentationProgress>0.001 && !IslandBus.locked',1)
text=text.replace('opacity: birth.value * Math.min(1,idleVisibility.progress*4)', 'opacity: win.presentationProgress * birth.value * Math.min(1,idleVisibility.progress*4)',1)
text=text.replace('xScale:idleVisibility.progress','xScale:idleVisibility.progress*win.presentationProgress',1)
text=text.replace('yScale:0.85+0.15*idleVisibility.progress','yScale:0.85+0.15*idleVisibility.progress*win.presentationProgress',1)
text=text.replace('target: win.blocked ? 1 : 0','target: 0',1)
# A blocked window must retain geometry for its shrinking surface.
text=text.replace('(win.blocked && fold.value < 0.96)','(win.presentationProgress>0.001)')
path.write_text(text)

# Unmapped/prepared panels must never paint an input cursor or a partial edge
# over fullscreen content. Preparation resumes after leaving fullscreen.
path=root/'components/glass/GlassBackdrop.qml'
text=path.read_text()
text=text.replace('property bool preloadReady:true','property bool preloadReady:!PrivacyPresentation.fullscreen(root.scr?.name || "")')
text=text.replace('(RenderingState.prewarm && root.retained)', '(RenderingState.prewarm && root.retained && root.preloadReady)')
path.write_text(text)
path=root/'ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
text=path.read_text().replace('                visible: true','                visible: root.opened || hideAnim.running',1)
text=text.replace('                                    focus:               true','                                    focus: root.opened && !win.closing',1)
# Rendering preparation is not a user input session: never display its caret.
text=text.replace('                                    onTextChanged: {','                                    cursorVisible: root.opened && !win.closing && activeFocus\n                                    onTextChanged: {',1)
path.write_text(text)

# Expanded modules replace the entire control-center presentation, including its
# auxiliary chrome. Both must follow the same transition as the grid tiles.
path=root/'ui/topbar/statusarea/controlcenter/ControlCenter.qml'
text=path.read_text()
condition='!(root.wifiOpened || root.wifiClosing || root.btOpened || root.btClosing || root.playerExpanded || root.playerClosing || root.themeOpened || root.themeClosing || root.timerOpened || root.timerClosing || root.alarmOpened || root.alarmClosing || root.stopwatchOpened || root.stopwatchClosing)'
text=text.replace('visible:MediaCaptureState.controlCenterActive;backdrop:ccBackdrop','visible:MediaCaptureState.controlCenterActive && '+condition+';backdrop:ccBackdrop')
text=text.replace('opacity: ControlCatalog.galleryOpen ? 0 : 1','opacity: ControlCatalog.galleryOpen || !('+condition+') ? 0 : 1')
text=text.replace('enabled: !ControlCatalog.galleryOpen','enabled: !ControlCatalog.galleryOpen && '+condition)
path.write_text(text)
exec(compile((Path(sys.argv[3])/'integrate.py').read_text(),str(Path(sys.argv[3])/'integrate.py'),'exec'))

# Native rendering can bypass refreshWindows(); inventory consumers still need
# the settled IPC snapshot after moves, closes and workspace changes.
path=root/'components/glass/GlassTracker.qml'
text=path.read_text().replace('''            if (root.captureUsers > 0)
                root.refreshWindows()''','''            if(root.inventoryUsers>0)root.captureSnapshot()
            if (root.captureUsers > 0)
                root.refreshWindows()''')
path.write_text(text)
