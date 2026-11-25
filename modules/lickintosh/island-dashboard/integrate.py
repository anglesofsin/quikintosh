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
qml = qml.replace('    property bool forced:', '''    Timer {
        id: pointerLeave
        interval: 180
        onTriggered: {
            if (win.pointerIn || win.dashboardPointerInside) return;
            win.dashboardRequested = false;
            win.forced = false;
            win.hub.voicePeek = false;
        }
    }

    property bool forced:''', 1)
qml = qml.replace('onHoveredChanged: win.pointerIn = hovered', '''onHoveredChanged: {
                    win.pointerIn = hovered;
                    if (hovered) pointerLeave.stop();
                    else pointerLeave.restart();
                }''', 1)
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
qml = qml.replace('    mask: Region { item: stage }', '''    property bool dashboardPointerInside: false
    property bool dashboardRequested: false
    onDashboardRequestedChanged: if (dashboardRequested) dashboardClose.stop(); else dashboardClose.restart()
    Timer { id: dashboardClose; interval: 250 }
    Connections {
        target: win
        function onVisibleChanged() { if (!win.visible) win.dashboardRequested = false }
    }
    LazyLoader {
        active: win.visible && IslandConfig.s("dashboardEnabled") && (win.dashboardRequested || dashboardClose.running)
        IslandDashboard {
            output: win.modelData
            capsuleTop: stage.y + surface.y
            capsuleWidth: surface.width
            capsuleHeight: surface.height
            expanded: win.dashboardRequested
            onPointerChanged: inside => {
                win.dashboardPointerInside = inside;
                if (inside) pointerLeave.stop(); else pointerLeave.restart();
            }
            Component.onDestruction: win.dashboardPointerInside = false
            onDismissed: win.dashboardRequested = false
        }
    }

    mask: Region { item: stage }''', 1)
anchor = 'opacity: birth.value * Math.min(1,idleVisibility.progress*4)'
assert qml.count(anchor) == 1
qml = qml.replace(anchor, anchor + ' * (win.dashboardRequested || dashboardClose.running ? 0 : 1)')
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


# A failed screencopy must not leave a visible Dock waiting on a readiness
# signal forever. Its background can recover after the surface is mapped.
path = root / 'tahoedock/TahoeDockSurface.qml'
text = path.read_text()
text = text.replace('readonly property bool displayShown:dock.shown && (Theme.plainSurfaces || glassPresented)',
                    'readonly property bool displayShown:dock.shown')
text = text.replace('visible:Theme.plainSurfaces || root.glassPresented',
                    'visible:dockGlassPresence.present')
path.write_text(text)

path = root / 'rosa/overlays/IslandWindow.qml'
text = path.read_text()
text = text.replace('privacy.restOffset+privacy.restWidth/2+7',
                    'privacy.restOffset+Math.max(privacy.restWidth,surface.width)/2+9')
path.write_text(text)

# Pin typography to the packaged SF faces instead of the host's fallback.
directory = root / 'ui/topbar/notch/dashboard'
for path in directory.glob('*.qml'):
    text = path.read_text()
    text = text.replace('font.family: "Sans Serif"', 'font.family: "SF Pro Text"')
    path.write_text(text)
