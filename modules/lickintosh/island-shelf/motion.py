"""Coordinate the island's surfaces by actual geometry, not close timeouts."""
from pathlib import Path


def integrate(root):
    root=Path(root)
    p=root/'rosa/overlays/IslandDashboard.qml';s=p.read_text()
    # Keep one Wayland buffer size: tabs morph inside it instead of remapping it.
    a=s.index('    implicitWidth:');b=s.index('\n',a)
    s=s[:a]+'    implicitWidth: Math.min(output.width-32,Math.max(1000,IslandConfig.s("shelfWidth")))'+s[b:]
    a=s.index('    implicitHeight:');b=s.index('\n',a)
    s=s[:a]+'    implicitHeight: Math.min(output.height,592)'+s[b:]
    s=s.replace('    property bool expanded: false','''    property bool expanded: false
    property bool geometryExpanded:false
    readonly property real targetWidth:Math.min(width,page===0 && IslandConfig.s("shelfAdaptiveWidth") ? Math.min(IslandConfig.s("shelfWidth"),Math.max(380,[1,2,3,4].filter(i=>IslandConfig.s("shelfSlot"+i)!=="none").length*380)):pageWidth)
    readonly property bool geometryReady:Math.abs(body.width-targetWidth)<1 && Math.abs(body.height-bodyHeight)<1
    readonly property bool collapsed:!expanded && !geometryExpanded && Math.abs(body.width-Math.min(width,capsuleWidth))<1 && Math.abs(body.height-capsuleHeight)<1
    signal collapseFinished()
    onCollapsedChanged:if(collapsed)collapseFinished()
    onExpandedChanged:{
        if(expanded){closeGeometry.stop();geometryExpanded=true}
        else {pageOut.stop();pageIn.stop();pageContent.opacity=1;closeGeometry.restart()}
    }
    Timer{id:closeGeometry;interval:SettingsPreferences.accessibility.reduceMotion ? 0:80;onTriggered:panel.geometryExpanded=false}''',1)
    a=s.index('    function selectPage(index)');b=s.index('    property var selectedHour:',a)
    s=s[:a]+'''    function selectPage(index) {
        if(index<0 || index>13)return;
        pendingPage=index;
        if(page===index && !pageOut.running)return;
        if(!expanded){pageOut.stop();pageIn.stop();page=index;pageContent.opacity=1;return}
        if(pageOut.running)return;
        pageIn.stop();pageOut.start();
    }
    NumberAnimation {
        id:pageOut;target:pageContent;property:"opacity";to:0
        duration:SettingsPreferences.accessibility.reduceMotion ? 0:65;easing.type:Easing.OutCubic
        onFinished:{panel.page=panel.pendingPage;pageIn.start()}
    }
    NumberAnimation {
        id:pageIn;target:pageContent;property:"opacity";to:1
        duration:SettingsPreferences.accessibility.reduceMotion ? 0:130;easing.type:Easing.OutCubic
    }
'''+s[b:]
    s=s.replace('width: panel.expandedBody ? parent.width : Math.min(parent.width, panel.capsuleWidth)','width: panel.geometryExpanded ? panel.targetWidth : Math.min(parent.width, panel.capsuleWidth)')
    s=s.replace('height: panel.expandedBody ? panel.bodyHeight : panel.capsuleHeight','height: panel.geometryExpanded ? panel.bodyHeight : panel.capsuleHeight')
    s=s.replace('opacity: panel.expandedBody && body.height > 160 ? 1 : 0','opacity: panel.expandedBody && panel.geometryReady ? 1 : 0')
    s=s.replace('duration: SettingsPreferences.accessibility.reduceMotion ? 0:IslandConfig.s("shelfAnimationMs") } }\n            spacing:', 'duration: SettingsPreferences.accessibility.reduceMotion ? 0:80 } }\n            enabled:panel.expandedBody && panel.geometryReady\n            spacing:',1)
    p.write_text(s)
    p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
    s=s.replace('else dashboardClose.restart()','else if(!win.visible)dashboardCover=false',1)
    s=s.replace('if(!IslandConfig.s("dashboardEnabled"))win.dashboardRequested=false','if(!IslandConfig.s("dashboardEnabled")){win.dashboardRequested=false;win.dashboardCover=false}',1)
    s=s.replace('dashboardClose.stop()','')
    a=s.index('    Timer { id: dashboardClose;');b=s.index('\n',a)
    s=s[:a]+s[b:]
    s=s.replace('            onDismissed: win.dashboardRequested = false','            onDismissed: win.dashboardRequested = false\n            onCollapseFinished:if(!win.dashboardRequested)win.dashboardCover=false',1)
    s=s.replace('win.bigMotion ? 0.5 : Motion.isleOpenResponse','win.bigMotion ? 0.32 : Motion.isleOpenResponse',1)
    s=s.replace('closeMs: win.bigMotion ? 420 : Motion.isleCloseMs','closeMs: win.bigMotion ? 240 : Motion.isleCloseMs',1)
    s=s.replace('response: win.bigMotion ? 0.56 : Motion.isleWidthResponse','response: win.bigMotion ? 0.32 : Motion.isleWidthResponse',1)
    s=s.replace('response: win.bigMotion ? 0.56 : 0.44','response: win.bigMotion ? 0.32 : 0.28',1)
    s=s.replace('                        if (!win.bigMotion)\n                            return 1;\n                        const k = Math.max(0, Math.min(1, (morph.value - 0.3) / 0.55));', '                        const k = Math.max(0, Math.min(1, (morph.value - 0.6) / 0.3));',1)
    # Shared-element flight must relinquish both endpoints on an interrupted handoff.
    s=s.replace('                        hero.veil(false);\n                        hero.mode = "";', '                        hero.veil(false);\n                        hero.src=null;hero.dst=null;heroRun.settle(0);\n                        hero.mode = "";',1)
    s=s.replace('                    function recall() {','                    function recall() {\n                        if(win.dashboardCover || !win.presentationWanted){hero.release();return}',1)
    s=s.replace('if (!IslandConfig.s("hero") || !win.lead)','if (!IslandConfig.s("hero") || !win.lead || win.dashboardCover || !win.opened)',1)
    s=s.replace('                    property string mode: ""','''                    Connections{target:win;function onDashboardCoverChanged(){if(win.dashboardCover)hero.release()}function onPresentationWantedChanged(){if(!win.presentationWanted)hero.release()}}
                    property string mode: ""''',1)
    p.write_text(s)


if __name__=='__main__':
    import sys
    integrate(sys.argv[1])
