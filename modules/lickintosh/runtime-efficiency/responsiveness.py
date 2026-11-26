"""Retain prepared scenes and warm common panels before user interaction."""
write('components/glass/GlassPrewarm.qml',(here/'GlassPrewarm.qml').read_text())
p='components/glass/qmldir';s=(root/p).read_text();s+='\nsingleton GlassPrewarm GlassPrewarm.qml\n';write(p,s)
# Retain decoded desktop items; hiding is not a reason to destroy their models.
edit('components/glass/DesktopSnapshot.qml','model: root.shown ? DesktopFiles.layout:[]','model: DesktopFiles.layout')
edit('components/glass/DesktopSnapshot.qml','model:root.widgetsShown && WidgetState.showDesktopWidgets ? WidgetState.desktop:[]','model:WidgetState.showDesktopWidgets ? WidgetState.desktop:[]')
p='components/glass/LiquidGlassBackdrop.qml';s=(root/p).read_text()
s=s.replace('    property bool warm: false','    property bool retained:false\n    property bool warm: false',1)
s=s.replace('        warm = false\n        if (ready)','        if(ready)retained=true\n        if (ready)',1)
s=s.replace('active: root.ready && root.captureWindows','active: (root.ready || root.retained) && root.captureWindows',1)
s=s.replace('sourceComponent: GlassWindows {','sourceComponent: GlassWindows {\n                capturing:root.ready',1)
# Frozen textures survive unmapping; the next opening resumes the same graph.
s=s.replace('        if (r.x !== root.glassRegion.x', '        if(!any && !root.ready)return\n        if (r.x !== root.glassRegion.x',1)
s=s.replace('onTriggered: root.warm = true','onTriggered: {root.warm = true;fb.scheduleUpdate();blurIntermediate.scheduleUpdate();blurFinal.scheduleUpdate()}',1)
write(p,s)
p='components/glass/GlassWindows.qml';s=(root/p).read_text()
s=s.replace('    property int captureInterval: 400','    property bool capturing:true\n    property bool inventoryHeld:false\n    function syncInventory(){if(inventoryHeld===capturing)return;inventoryHeld=capturing;GlassTracker.captureUsers=Math.max(0,GlassTracker.captureUsers+(inventoryHeld ? 1:-1));if(inventoryHeld)root.requiredSnapshot=GlassTracker.captureSnapshot()}\n    onCapturingChanged:syncInventory()\n    property int captureInterval: 400',1)
s=s.replace('Component.onCompleted: {GlassTracker.captureUsers++;root.requiredSnapshot=GlassTracker.captureSnapshot()}','Component.onCompleted:syncInventory()').replace('Component.onDestruction: GlassTracker.captureUsers--','Component.onDestruction:if(inventoryHeld)GlassTracker.captureUsers--')
s=s.replace('wanted: view.shown && view.captureOpacity > 0','wanted: root.capturing && view.shown && view.captureOpacity > 0',1)
s=s.replace('property bool sourceClosed:false','property bool sourceClosed:false\n            property bool sourceRetained:false',1)
s=s.replace('onWindowSourceChanged:if(windowSource){sourceClosed=false;restartFailures=0}','onWindowSourceChanged:{sourceRetained=false;if(windowSource){sourceClosed=false;restartFailures=0}}',1)
s=s.replace('onHasContentChanged:if(hasContent)restartFailures=0','onHasContentChanged:if(hasContent){restartFailures=0;Qt.callLater(function(){if(view.hasContent && !view.sourceClosed)view.sourceRetained=true})}',1)
s=s.replace('captureSource: gate.armed && gate.wanted &&','captureSource: (gate.armed || view.sourceRetained) && view.shown && view.captureOpacity>0 &&',1)
s=s.replace('live: gate.wanted &&','live: root.capturing && gate.wanted &&',1)
s=s.replace('(gate.armed || view.sourceRetained) && view.shown && view.captureOpacity>0 &&','(gate.armed || view.sourceRetained) && view.onScreen && !GlassTracker.captureBlocked && view.captureOpacity>0 &&',1)
write(p,s)
p='components/glass/GlassBackdrop.qml';s=(root/p).read_text()
s=s.replace('    readonly property var win: QsWindow.window','    property var hostWindow:null\n    readonly property var win:hostWindow || QsWindow.window',1)
s=s.replace('captureWindows: root.ready && ShellConfig.options.glass.captureWindows','captureWindows: ShellConfig.options.glass.captureWindows',1)
s=s.replace('    property bool gateEnabled:', """    property bool preload:false
    property bool preloadReady:true
    onPreloadReadyChanged:if(preloadReady && preload)GlassPrewarm.enqueue(root)
    property bool materialPrepared:false
    property bool prewarming:false
    property bool presentationActive:root.win!==null && root.win.visible
    property bool warmupHeld:false
    function syncPresentation(){
        const active=root.preload && root.presentationActive
        if(active!==warmupHeld){warmupHeld=active;GlassPrewarm.activePanels=Math.max(0,GlassPrewarm.activePanels+(active ? 1:-1))}
        if(active && prewarming)GlassPrewarm.remove(root)
    }
    onPresentationActiveChanged:syncPresentation()
    // Keep the prepared QML/scene graph, not a mapped full-screen transparent surface.
    Binding{target:root.win;property:"visible";value:root.prewarming || root.presentationActive;when:root.preload && root.win!==null}
    property Item warmItem:null
    // Child visibility follows its parent; restoring an inherited false value
    // after warm-up would pin the panel content invisible.
    Binding{target:root.warmItem;property:"opacity";value:1;when:root.prewarming && root.warmItem!==null}
    function prepareMaterial(done){
        if(!warmItem || warmItem.width<=0 || warmItem.height<=0){done();return}
        if(!warmItem.grabToImage(result=>done()))done()
    }
    property rect preparationRegion:Qt.rect(0,0,screenSize.width,screenSize.height)
    captureRegion:!root.prewarming && root.presentationActive && glassRegion.width>0 && glassRegion.height>0 ? glassRegion:root.preparationRegion
    property bool gateEnabled:""",1)
s=s.replace('instantReveal: gateEnabled','instantReveal:true',1)
s=s.replace('ready: !Theme.plainSurfaces && root.win !== null && root.win.visible','ready: !Theme.plainSurfaces && root.win !== null && (root.preload ? (root.prewarming || root.presentationActive):root.win.visible)',1)
s=s.replace('        if (!ready) revealed = !gateEnabled','        if (!ready && !root.captureSettled) revealed = !gateEnabled',1)
s=s.replace('        // The first visible frame must go through the same capture gate.','        root.syncPresentation();if(root.preload)GlassPrewarm.enqueue(root)',1)
s=s.replace('value: root.revealed ? 1 : 0','value: (root.prewarming || (root.preload && !root.presentationActive)) ? 0 : (root.revealed ? 1 : 0)',1)
s=s.replace('when: root.gateEnabled && root.win !== null && root.win !== undefined','when: (root.gateEnabled || root.preload) && root.win !== null && root.win !== undefined',1)
s=s.replace('Component.onDestruction: GlassRegistry.unregister(root)','Component.onDestruction:{GlassPrewarm.remove(root);if(root.warmupHeld)GlassPrewarm.activePanels=Math.max(0,GlassPrewarm.activePanels-1);GlassRegistry.unregister(root)}',1)
write(p,s)
# The opening animation starts immediately, using the already prepared scene.
p='ui/topbar/statusarea/controlcenter/ControlCenter.qml';s=(root/p).read_text()
s=s.replace('    Loader {\n        active: root._ccLoaderActive', '    Loader {\n        id:controlPanelLoader\n        active: root._ccLoaderActive',1)
s=s.replace('GlassBackdrop { id: ccBackdrop; element: "cc" }','GlassBackdrop { id: ccBackdrop; element: "cc";gateEnabled:false;preload:true;preloadReady:controlPanelLoader.status===Loader.Ready;hostWindow:ccWindow;warmItem:ccContent;preparationRegion:Qt.rect(Math.max(0,screenSize.width-ccContent.width-10),0,ccContent.width+10,ccContent.height+100);presentationActive:root._ccLoaderActive }',1)
s=s.replace('root.opened && ccBackdrop.revealed ? 1 : 0','root.opened ? 1 : 0')
s=s.replace('                    Connections{target:ccBackdrop;function onRevealedChanged(){if(root.opened && ccBackdrop.revealed)ccContent.showProgress=1}}\n','')
write(p,s)
for p,old,new in [
 ('ui/topbar/statusarea/notifcenter/NotifCenter.qml','GlassBackdrop { element: "notifcenter"; gateEnabled:false }','GlassBackdrop { element: "notifcenter"; gateEnabled:false;preload:true;hostWindow:ncWin;warmItem:panel;preparationRegion:Qt.rect(screenSize.width-root.panelWidth-root.panelMarginR,root.topOffset,root.panelWidth,screenSize.height-root.topOffset);presentationActive:presence.present }'),
 ('ui/topbar/menubar/applemenu/AppleMenuWindow.qml','GlassBackdrop { element: "menus" }','GlassBackdrop { element: "menus";preload:true;hostWindow:panel;warmItem:appleMenu;preparationRegion:Qt.rect(12,36,appleMenu.width,appleMenu.height);presentationActive:presence.present }'),
 ('ui/topbar/statusarea/StatusSubMenuWindow.qml','GlassBackdrop { element: "menus" }','GlassBackdrop { element: "menus";preload:true;hostWindow:panel;warmItem:menuContainer;preparationRegion:Qt.rect(Math.min(Math.max(root.xPos-20,10),screenSize.width-330),36,320,Math.max(80,menuContainer.height));presentationActive:presence.present }'),
 ('ui/topbar/menubar/globalmenu/PopupMenu.qml','GlassBackdrop {id:menuBackdrop; element: "menus";gateEnabled:false}','GlassBackdrop {id:menuBackdrop; element: "menus";gateEnabled:false;preload:true;hostWindow:panel;warmItem:menuContainer;preparationRegion:Qt.rect(root.xPos,root.yPos,300,Math.max(480,menuContainer.height));presentationActive:presence.present }'),
 ('ui/topbar/statusarea/spotlight/SpotlightWindow.qml','element: "spotlight"\n                    ready: !Theme.plainSurfaces && (root.opened || hideAnim.running)','element: "spotlight"\n                    preload:true;hostWindow:win;warmItem:bgPanel;preparationRegion:Qt.rect((screenSize.width-bgPanel.width)/2,Math.max(0,bgPanel.y),bgPanel.width,Math.max(520,bgPanel.height));presentationActive:root.opened || hideAnim.running\n                    ready: !Theme.plainSurfaces && (root.opened || hideAnim.running || prewarming)'),
]:edit(p,old,new)
# Launchpad keeps its prepared app model even while Spotlight has no category.
p='ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=(root/p).read_text()
# Earlier warm-up is staggered, never created synchronously by a click.
s=s.replace('interval: 1800; running: true; onTriggered: root._spotlightLoaded = true','interval: 650; running: true; onTriggered: root._spotlightLoaded = true',1)
write(p,s)
# Clearing Spotlight's action used to switch the hidden applications grid to
# files, discarding all prepared delegates immediately before the next launch.
p='ui/topbar/statusarea/spotlight/SpotlightWindow.qml';s=(root/p).read_text()
s=s.replace('                property string selectedAction: "applications"','                property string selectedAction: "applications"\n                property string preparedGrid:"applications"\n                onSelectedActionChanged:if(selectedAction==="applications" || selectedAction==="files")preparedGrid=selectedAction',1)
a=s.index('                                SpotlightCategoryGrid {');b=s.index('                                SpotlightResults {',a)
s=s[:a]+s[a:b].replace('win.selectedAction === "applications"','win.preparedGrid === "applications"').replace('win.selectedAction === "files"','win.preparedGrid === "files"')+s[b:];write(p,s)

# A mapped transparent surface must not subscribe hidden controls to data clocks.
for p in ['ui/widgets/types/UtilityWidget.qml','ui/widgets/types/BatteryWidget.qml','ui/widgets/types/MediaWidget.qml','ui/topbar/notch/dashboard/PerformancePage.qml']:
 s=(root/p).read_text().replace('!!root.Window.window?.visible','(!!root.Window.window?.visible && root.Window.window.contentItem.opacity>0)')
 write(p,s)
# Compile one submenu level in advance; deeper menus are retained after first use.
# Keeping a child must never recursively instantiate an unbounded menu tree.
p='ui/topbar/menubar/globalmenu/PopupMenu.qml';s=(root/p).read_text()
s=s.replace('    property bool opened: false','    property bool opened: false\n    property int menuDepth:0\n    property bool subPrepared:false\n    Timer{interval:2600;running:true;onTriggered:if(root.menuDepth===0)root.subPrepared=true}',1)
s=s.replace('        if (root.subIndex !== -1 && root.items[root.subIndex]) {','        if (root.subIndex !== -1 && root.items[root.subIndex]) {\n            root.subPrepared=true',1)
s=s.replace('                root.subItems = []','                // Retain the last prepared submenu rows.',1)
s=s.replace('active: root.subKeep && presence.present','active: root.subPrepared\n        asynchronous:!root.opened',1)
s=s.replace('            item.opened = Qt.binding','            item.menuDepth=root.menuDepth+1\n            item.opened = Qt.binding',1)
write(p,s)

# Start retained UI construction early, in staggered asynchronous batches.
for p,old,new in [
 ('ui/topbar/menubar/applemenu/AppleMenuWindow.qml','interval: 1400; running: true','interval: 400; running: true'),
 ('ui/topbar/statusarea/StatusSubMenuWindow.qml','interval: 1800; running: true','interval: 800; running: true'),
 ('ui/topbar/statusarea/notifcenter/NotifCenter.qml','interval: 2200; running: true','interval: 1100; running: true'),
 ('ui/topbar/statusarea/controlcenter/ControlCenter.qml','interval: 2800; running: true','interval: 1400; running: true'),
]:edit(p,old,new)
