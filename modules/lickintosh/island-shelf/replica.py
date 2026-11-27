"""Reference layouts and explicit ownership for the expanded shelf."""
from pathlib import Path


def integrate(root):
    root=Path(root)
    p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
    s=s.replace('    readonly property bool wanted:\n','    readonly property bool wanted: win.dashboardRequested || win.dashboardCover || IslandConfig.s("reserveClockSpace") ||\n',1)
    s=s.replace('(win.hub.kind === "clock" || win.hub.kind === "")','!win.dashboardRequested && !win.dashboardCover && (win.hub.kind === "clock" || win.hub.kind === "")',1)
    s=s.replace('onCollapseFinished:if(!win.dashboardRequested)win.dashboardCover=false','onCollapseFinished:Qt.callLater(function(){if(!win.dashboardRequested)win.dashboardCover=false})',1)
    s=s.replace('onPressedChanged: win.pressed = pressed','acceptedButtons:Qt.LeftButton\n                onPressedChanged: win.pressed = pressed',1)
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
