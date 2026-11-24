"""Damage/render-driven glass capture, without changing the glass shader or its scale."""
from pathlib import Path
import sys
root = Path(sys.argv[1])
def edit(name, old, new):
    p = root / name
    text = p.read_text()
    if text.count(old) != 1:
        raise ValueError(f'Expected one anchor in {name}: {old[:80]}')
    p.write_text(text.replace(old, new, 1))

gate = 'components/glass/CaptureGate.qml'
edit(gate, '    property bool armed: false', '    property bool armed: false\n    property bool streaming: false')
edit(gate, '''        if (wanted && (calm || !hasContent))
            armed = true''', '''        armed = wanted && (streaming || calm || !hasContent)''')
edit(gate, 'running: root.armed && root.wanted && root.calm && root.hasContent',
     'running: !root.streaming && root.armed && root.wanted && root.calm && root.hasContent')

windows = 'components/glass/GlassWindows.qml'
edit(windows, '                calm: !GlassTracker.fast && !GlassTracker.captureBlocked',
     '                streaming: true\n                calm: !GlassTracker.captureBlocked')
edit(windows, '            live: false', '''            // Quickshell requests the next frame when the current one is rendered.
            // Do not throttle video to the snapshot timer or suspend it during movement.
            live: gate.wanted && !restarting && !dying
            onStopped: { if (gate.wanted && !dying) view.restart() }''')
edit(windows, 'captureSource: gate.armed && !restarting && !dying ? modelData.wayland : null',
     'captureSource: gate.armed && gate.wanted && !restarting && !dying ? modelData.wayland : null')
# Clip to the monitor: a quad translated below the screen must not keep a stream alive.
edit(windows, '    property int pending: 0', '''    readonly property rect visibleRegion: Qt.rect(
        Math.max(0, region.x), Math.max(0, region.y),
        Math.max(0, Math.min(monitorObject ? monitorObject.width / (monitorObject.scale || 1) : 0, region.x + region.width) - Math.max(0, region.x)),
        Math.max(0, Math.min(monitorObject ? monitorObject.height / (monitorObject.scale || 1) : 0, region.y + region.height) - Math.max(0, region.y)))

    property int pending: 0''')
p = root / windows
s = p.read_text()
s = s.replace('root.region.', 'root.visibleRegion.')
p.write_text(s)

backdrop = 'components/glass/LiquidGlassBackdrop.qml'
edit(backdrop, '''        id: blurIntermediate
        visible: false''', '''        id: blurIntermediate
        visible: false
        live: root.ready''')
edit(backdrop, '''        id: blurFinal
        visible: false''', '''        id: blurFinal
        visible: false
        live: root.ready''')
edit('ui/dock/Dock.qml', '                    ready: !Theme.plainSurfaces', '''                    ready: !Theme.plainSurfaces && dockWin.visible
                        && dockMouseArea.anchors.topMargin < dockWin.height - dockRoot.hoverRegionH - 1''')

# QsWindow detaches from hidden windows; null must mean inactive, not ready.
edit('components/glass/GlassBackdrop.qml',
     'ready: !Theme.plainSurfaces && (!root.win || root.win.visible)',
     'ready: !Theme.plainSurfaces && root.win !== null && root.win.visible')
# A retained popup must reset its reveal gate on every unmap, not only at creation.
edit('components/glass/GlassBackdrop.qml', '''    onGlassReadyChanged: {
        if (glassReady)
            revealed = true
    }''', '''    property int revealFrames: 0
    onGlassReadyChanged: {
        revealFrames = 0
        if (!ready) revealed = !gateEnabled
    }
    FrameAnimation {
        running: root.gateEnabled && root.glassReady && !root.revealed
        onTriggered: {
            if (++root.revealFrames >= 2) root.revealed = true
        }
    }''')
edit('components/glass/GlassBackdrop.qml', '    property int gateTimeout: 400', '    property int gateTimeout: 1200')
edit('components/glass/GlassBackdrop.qml', 'running: root.gateEnabled && !root.revealed',
     'running: root.ready && root.gateEnabled && !root.revealed')
edit('ui/topbar/statusarea/spotlight/SpotlightWindow.qml', 'GlassBackdrop { element: "spotlight"; gateTimeout: 120 }',
     'GlassBackdrop { element: "spotlight" }')
edit(windows, 'if (!root.latched && root.graceDone && (root.pending === 0 || root.timedOut))',
     'if (!root.latched && root.monitorObject !== null && root.graceDone && (root.pending === 0 || root.timedOut))')
# Centralize exclusion so mouse clicks, IPC and keybinds all follow the same rule.
edit('shell.qml', '    property bool ccOpened:          false', '''    onCcOpenedChanged: { if (ccOpened) notifCenterOpened = false }
    onNotifCenterOpenedChanged: { if (notifCenterOpened) ccOpened = false }
    property bool ccOpened:          false''')
# Wait for capture readiness, not arbitrary warm-up delays. Delegates report pending frames.
edit(backdrop, '''        id: warmTimer
        interval: 50''', '''        id: warmTimer
        interval: 0''')
edit(windows, '''        id: graceTimer
        interval: 60''', '''        id: graceTimer
        interval: 0''')
edit(windows, '    property int pending: 0', '    onMonitorObjectChanged: root.recount()\n\n    property int pending: 0')
# Keep the launcher's rendering context warm; the closed surface has no input or capture.
spotlight = 'ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
edit(spotlight, '                visible: root.opened || hideAnim.running', '''                visible: true
                mask: Region { item: root.opened || hideAnim.running ? win.contentItem : null }''')
edit(spotlight, '                WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand',
     '                WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None')
edit(spotlight, 'GlassBackdrop { element: "spotlight" }', '''GlassBackdrop {
                    element: "spotlight"
                    ready: !Theme.plainSurfaces && (root.opened || hideAnim.running)
                }''')
# Shared services also run in Settings: only the shell may own desktop shortcuts.
launcher = root / 'services/LauncherState.qml'
s = launcher.read_text()
start = s.index('    GlobalShortcut {')
end = s.index('\n    function openApplications()', start)
shortcuts = s[start:end]
launcher.write_text(s[:start] + s[end:])
shortcuts = shortcuts.replace('root.pendingAction', 'LauncherState.pendingAction').replace('root.requested()', 'LauncherState.requested()').replace('root.openApplications()', 'LauncherState.openApplications()')
edit('shell.qml', '    id: appRoot', '    id: appRoot\n' + shortcuts)
