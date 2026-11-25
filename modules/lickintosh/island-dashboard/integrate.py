"""Install the dashboard and route island gestures on the assembled shell."""
from pathlib import Path
import shutil
import sys

root = Path(sys.argv[1])
source = Path(sys.argv[2])
overlays = root / 'rosa/overlays'
shutil.copyfile(source / 'IslandDashboard.qml', overlays / 'IslandDashboard.qml')
shutil.copytree(source / 'assets', overlays / 'assets', dirs_exist_ok=True)
module = overlays / 'qmldir'
module.write_text(module.read_text() + '\nIslandDashboard IslandDashboard.qml\n')

window = overlays / 'IslandWindow.qml'
qml = window.read_text()
start = qml.index('    onPointerInChanged: {')
end = qml.index('    property bool forced:', start)
qml = qml[:start] + qml[end:]
qml = qml.replace('''            HoverHandler {
                onHoveredChanged: win.pointerIn = hovered
            }

''', '', 1)
qml = qml.replace('''            HoverHandler {
                enabled:win.hub.leftKind === "voice"
                cursorShape:Qt.PointingHandCursor
                onHoveredChanged:if(hovered) {win.hub.voicePeekMs=900; win.hub.voicePeek=true}
            }
''', '')
start = qml.index('                    } else if (dy < 0 && !win.wide')
end = qml.index('\n                }', start)
qml = qml[:start] + '                    }' + qml[end:]
start = qml.index('                onTapped: {\n                    if(VoiceCalls.incoming)')
end = qml.index('            ClippingRectangle {', start)
qml = qml[:start] + '''                onTapped: {
                    if (win.wide) {
                        if (VoiceCalls.incoming) VoiceCalls.dismissIncoming();
                        win.hub.voicePeek = false;
                        win.hub.pinned = false;
                        win.forced = false;
                        win.hushed = true;
                        force.stop();
                    } else if (win.wideKind !== "") {
                        win.hushed = false;
                        win.forced = true;
                    }
                    win.bump();
                }
            }

            TapHandler {
                acceptedButtons: Qt.RightButton
                onTapped: win.dashboardRequested = !win.dashboardRequested
            }

''' + qml[end:]
# Keep the dashboard tied to the output where the gesture occurred.
qml = qml.replace('    mask: Region { item: stage }', '''    property bool dashboardRequested: false
    Connections {
        target: win
        function onVisibleChanged() { if (!win.visible) win.dashboardRequested = false }
    }
    LazyLoader {
        active: win.visible && win.dashboardRequested && IslandConfig.s("dashboardEnabled")
        IslandDashboard { output: win.modelData; onDismissed: win.dashboardRequested = false }
    }

    mask: Region { item: stage }''', 1)
window.write_text(qml)

config = root / 'rosa/services/IslandConfig.qml'
qml = config.read_text()
anchor = '        enabled:     { type: "bool", def: true },'
assert qml.count(anchor) == 1
qml = qml.replace('"hoverWide", "tapWide", "autoWide"', '"autoWide"', 1)
config.write_text(qml.replace(anchor, anchor + '''
        dashboardEnabled: { type: "bool", def: true },
        dashboardCamera: { type: "bool", def: false },
        dashboardWeatherArt: { type: "bool", def: true },
        dashboardWeatherLocation: { type: "bool", def: false },'''))

for name, before, after in [
    ('NotchDashboard.qml', '    spacing: 8', '    property Component profileModule\n    spacing: 8'),
    ('NotchDashboard.qml', 'DashboardPage {}', 'DashboardPage { profileModule: root.profileModule }'),
    ('dashboard/DashboardPage.qml', '    property string expandedKind', '    property Component profileModule\n    property string expandedKind'),
    ('dashboard/DashboardPage.qml', '        ProfilePhotoModule {}',
     '        Loader { Layout.preferredWidth: 100; Layout.fillHeight: true; sourceComponent: root.profileModule || defaultProfile }\n'
     '        Component { id: defaultProfile; ProfilePhotoModule {} }'),
]:
    path = root / 'ui/topbar/notch' / name
    text = path.read_text()
    assert before in text, name
    path.write_text(text.replace(before, after, 1))
