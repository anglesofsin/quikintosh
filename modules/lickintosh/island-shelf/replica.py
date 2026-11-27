"""Reference layouts and explicit ownership for the expanded shelf."""
from pathlib import Path


def integrate(root):
    root=Path(root)
    p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
    s=s.replace('    readonly property bool wanted:\n','    readonly property bool wanted: win.dashboardRequested || win.dashboardCover || IslandConfig.s("reserveClockSpace") ||\n',1)
    s=s.replace('(win.hub.kind === "clock" || win.hub.kind === "")','!win.dashboardRequested && !win.dashboardCover && (win.hub.kind === "clock" || win.hub.kind === "")',1)
    s=s.replace('onCollapseFinished:if(!win.dashboardRequested)win.dashboardCover=false','onCollapseFinished:Qt.callLater(function(){if(!win.dashboardRequested)win.dashboardCover=false})',1)
    s=s.replace('onPressedChanged: win.pressed = pressed','acceptedButtons:Qt.LeftButton\n                onPressedChanged: win.pressed = pressed',1)
    start=s.index('            readonly property point visualRight:')
    end=s.index('            readonly property bool cam:',start)
    s=s[:start]+'            readonly property point visualRight: {\n                const edge=dot.visible && dot.opacity>0.01\n                    ? Math.max(surface.x+surface.width,dot.x+dot.width/2+dot.width/2*dot.scale*Math.max(1,dot.blobScaleX))\n                    : surface.x+surface.width;\n                const cx=stage.width/2,cy=stage.height/2;\n                const origin=stage.head+surface.width/2;\n                const progress=idleVisibility.progress*win.presentationProgress;\n                let px=origin+(edge-origin)*progress;\n                let py=cy+(stage.pillH/2-cy)*(0.85+0.15*progress);\n                px=cx+(px-cx)*(1+stage.jelly+Motion.isleSquashX*squash.value+0.016*magP.value);\n                py=cy+(py-cy)*(1-stage.jelly*Motion.isleJellyCross-Motion.isleSquashY*squash.value+0.03*magP.value);\n                px+=win.shakeX+drift.value*9+magX.value;\n                py+=magY.value;\n                return Qt.point(stage.x+cx+(px-cx)*stage.scale,stage.y+cy+(py-cy)*stage.scale);\n            }\n\n'+s[end:]
    p.write_text(s)
    p=root/'rosa/overlays/IslandDashboard.qml';s=p.read_text()
    s=s.replace('TapHandler{acceptedButtons:Qt.RightButton;onTapped:panel.dismissed()}','MouseArea{anchors.fill:parent;acceptedButtons:Qt.RightButton;onClicked:panel.dismissed()}')
    s=s.replace('panel.page===8 ?','panel.page===0 && ShelfState.editing ? IslandConfig.s("shelfHeight")+100:panel.page===8 ?',1)
    s=s.replace('return index===8 ?','return index===0 && ShelfState.editing ? IslandConfig.s("shelfHeight")+100:index===8 ?',1)
    # The visible catalogue is also available inline, preserving Home while editing.
    s=s.replace('Component{id:media;ShelfMedia{}}','Component{id:media;ShelfMedia{onOpenLyrics:panel.selectPage(9);onOpenSources:panel.selectPage(10)}}')
    s=s.replace('Component {id:overview;ShelfHome{onOpenPage:page=>panel.selectPage(page)}}','Component {id:overview;HomeEditor{onOpenPage:page=>panel.selectPage(page)}}')
    s=s.replace('Component{id:widgetDetail;ShelfHome{slots:[panel.detailWidget];onOpenPage:page=>panel.selectPage(page)}}','Component{id:widgetDetail;ShelfHome{slots:[panel.detailWidget];onOpenPage:page=>panel.selectPage(page)}}')
    s=s.replace('ShelfButton{implicitWidth:44;implicitHeight:36;icon:"notch/grid.svg";', 'ShelfButton{implicitWidth:44;implicitHeight:36;icon:"notch/grid.svg";')
    a='            ShelfButton{visible:ShelfState.editing && panel.page!==8;'
    s=s.replace(a,'            ShelfButton{implicitWidth:44;implicitHeight:36;icon:"notch/hard-drive.svg";accessibleLabel:qsTr("Storage");selected:panel.page===14;onClicked:panel.selectPage(14)}\n'+a,1)
    s=s.replace('index>13','index>14').replace('model:14','model:15')
    s=s.replace('    property var visitedPages:({0:true})',
        '    property var visitedPages:({0:true})\n    property int prewarmCursor:0\n    readonly property var prewarmPages:[2,5,11,13]\n    Timer{interval:250;running:panel.prewarmCursor<panel.prewarmPages.length;repeat:true;onTriggered:{const next=Object.assign({},panel.visitedPages);next[panel.prewarmPages[panel.prewarmCursor++]]=true;panel.visitedPages=next}}')
    s=s.replace('active:!!panel.visitedPages[index]','asynchronous:index!==0\n                            active:!!panel.visitedPages[index]')
    s=s.replace('awake,widgetDetail][index]','awake,widgetDetail,storage][index]')
    s=s.replace('    Component {id:tray;','    Component{id:storage;StorageShelf{}}\n    Component {id:tray;',1)
    s=s.replace('13:(panel.detailWidget===','14:540,13:(panel.detailWidget===')
    s=s.replace('13:(detailWidget===','14:540,13:(detailWidget===')
    s=s.replace('({1:336,4:300','({14:300,1:336,4:300')
    s=s.replace('6:820','6:720').replace('6:280','6:250').replace('4:300','4:460')
    # A menu on the capsule background, with actual settings and customization.
    s=s.replace('id: body\n','''id: body
        Menu{id:shelfMenu
            background:Rectangle{radius:14;color:'#ed242426';border.color:'#30ffffff'}
            MenuItem{text:qsTr('Customize Home');onTriggered:{panel.selectPage(0);ShelfState.editing=true}}
            MenuItem{text:qsTr('Audio sources');onTriggered:panel.selectPage(10)}
            MenuItem{text:qsTr('Open Control Center');onTriggered:Quickshell.execDetached(['quickintosh','ipc','call','rice','controlCenter'])}
            MenuItem{text:qsTr('Open Settings');onTriggered:SettingsLauncher.open('')}
        }
''',1)
    # Right click retains toggle behavior; context menu available explicitly via Home editor.
    p.write_text(s)
    qmldir=root/'island-shelf/qmldir'
    qmldir.write_text(qmldir.read_text()+'\nHomeEditor HomeEditor.qml\nTransformWindow TransformWindow.qml\nStorageShelf StorageShelf.qml\nShelfMenu ShelfMenu.qml\nShelfMenuItem ShelfMenuItem.qml\nShelfMenuSeparator ShelfMenuSeparator.qml\n')
    p=root/'shell.qml';s=p.read_text();s += '\n' if not s.endswith('\n') else ''
    # Add transformation window next to the existing floating tray/player.
    s=s.replace('    FloatingMusic {','    TransformWindow {}\n    FloatingMusic {',1)
    s=s.replace('    NotificationServer {','    NotificationServer {\n        inlineReplySupported:true',1)
    if 'TransformWindow {}' not in s:s=s.replace('FloatingMusic{','TransformWindow{}\n    FloatingMusic{',1)
    p.write_text(s)


if __name__=='__main__':
    import sys
    integrate(sys.argv[1])
