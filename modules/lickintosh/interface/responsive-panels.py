"""Retain compiled popups without mapping them or keeping captures active."""
from pathlib import Path
import sys

root = Path(sys.argv[1])

def edit(name, before, after, count=1):
    p = root / name
    text = p.read_text()
    if text.count(before) != count:
        raise ValueError(f'Responsive panel anchor {name}: {before[:70]} ({text.count(before)})')
    p.write_text(text.replace(before, after))

# Warm the QML object graphs while unmapped. A closed popup has neither an
# input region nor an active glass stream; opening still gates on fresh capture.
for name, delay in [
    ('ui/topbar/menubar/applemenu/AppleMenuWindow.qml', 1400),
    ('ui/topbar/statusarea/notifcenter/NotifCenter.qml', 2200),
    ('ui/topbar/statusarea/StatusSubMenuWindow.qml', 1800),
]:
    edit(name, '    property bool opened: false', f'''    property bool opened: false
    property bool warmed: false
    Timer {{ interval: {delay}; running: true; onTriggered: root.warmed = true }}''')
    p = root / name
    text = p.read_text().replace('active: presence.present', 'active: root.warmed || presence.present\n        asynchronous: !root.opened')
    text = text.replace('                id: panel\n', '                id: panel\n                visible: presence.present\n')
    text = text.replace('                id: ncWin\n', '                id: ncWin\n                visible: presence.present\n')
    if name.endswith('NotifCenter.qml'):
        text = text.replace('mask: WidgetState.galleryZone === "notifCenter" ? galleryMask : null', 'mask: !root.opened ? emptyMask : WidgetState.galleryZone === "notifCenter" ? galleryMask : null\n                Region { id: emptyMask }')
        text = text.replace('WlrKeyboardFocus.OnDemand', 'root.opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None')
        text = text.replace('duration: ShellMotion.enter()', 'duration: Math.min(180, ShellMotion.enter())')
    else:
        text = text.replace('duration: ShellMotion.fade()', 'duration: Math.min(120, ShellMotion.fade())')
    p.write_text(text)

cc = 'ui/topbar/statusarea/controlcenter/ControlCenter.qml'
edit(cc, '    property bool _ccLoaderActive: false', '''    property bool _ccLoaderActive: false
    property bool _ccWarmed: false
    Timer { interval: 2800; running: true; onTriggered: root._ccWarmed = true }''')
edit(cc, '        active: root._ccLoaderActive', '        active: root._ccLoaderActive || root._ccWarmed\n        asynchronous: !root.opened')
edit(cc, '                id: ccWindow', '                id: ccWindow\n                visible: root._ccLoaderActive')
edit(cc, 'Component.onCompleted: showProgress = 1', 'Component.onCompleted: showProgress = root.opened ? 1 : 0')
edit(cc, 'if (!root.opened) ccContent.showProgress = 0', 'ccContent.showProgress = root.opened ? 1 : 0')
edit(cc, 'readonly property int animationDur: ShellMotion.fade()', 'readonly property int animationDur: Math.min(140, ShellMotion.fade())')
edit(cc, 'mask: ControlCatalog.galleryOpen ? editMask : null', 'mask: !root.opened ? emptyMask : ControlCatalog.galleryOpen ? editMask : null\n                Region { id: emptyMask }')
edit(cc, 'WlrLayershell.keyboardFocus: WlrKeyboardFocus.OnDemand', 'WlrLayershell.keyboardFocus: root.opened ? WlrKeyboardFocus.OnDemand : WlrKeyboardFocus.None')
p = root / cc
p.write_text(p.read_text().replace('interval: ShellMotion.spatial(0.45)', 'interval: Math.min(60, ShellMotion.spatial(0.45))'))
edit('ui/topbar/menubar/applemenu/AppleMenu.qml', 'duration: ShellMotion.fade()', 'duration: Math.min(120, ShellMotion.fade())', count=3)

# Reuse a recent inventory for popup openings, but invalidate it on compositor
# changes. Concurrent glass instances share one query instead of queuing many.
tracker = 'components/glass/GlassTracker.qml'
edit(tracker, '    property bool snapshotAgain:false', '    property bool snapshotAgain:false\n    property double clientsUpdated:0')
edit(tracker, 'if(clientsQuery.running) {snapshotAgain=true;return snapshotSerial+2}', '''if (Date.now()-clientsUpdated < 120 && snapshotSerial > 0) return snapshotSerial
        if(clientsQuery.running) {snapshotAgain=true;return snapshotSerial+1}''')
edit(tracker, 'root.snapshotSerial++', 'root.clientsUpdated=Date.now();root.snapshotSerial++')
edit(tracker, '            var n = event.name', '''            var n = event.name
            if(root.geometryEvents.indexOf(n)!==-1 || n === "activewindow" || n === "activewindowv2")root.clientsUpdated=0''')

# A frozen screenshot is already the exact composed desktop. The capture editor
# shares this source among all TahoeGlass surfaces, with no screencopy streams.
backdrop = 'components/glass/LiquidGlassBackdrop.qml'
edit(backdrop, '    property bool captureWindows: true', '    property Item frozenSource: null\n    property bool captureWindows: true')
edit(backdrop, 'sourceItem: scene', 'sourceItem: root.frozenSource || scene')
edit(backdrop, 'hideSource: true', 'hideSource: root.frozenSource === null')
