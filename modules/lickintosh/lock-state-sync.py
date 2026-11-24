"""Publish the native session-lock state after the Wayland notify settles.

Only mirrors state; never requests unlock and never consults logind hints to
override a native lock. A stale presentation flag must not disable the island,
glass capture, hot corners and wallpaper services after successful unlock.
"""
from pathlib import Path
import sys

root=Path(sys.argv[1])
p=root/'ui/lockscreen/LockScreen.qml'
s=p.read_text()
old='''        onLockedChanged: {
            root._sessionLocked=lock.locked
            if (locked) {
                if (root.capturePath !== "") {
                    captureTimer.restart()
                }
                root.lockRequested()
            } else {
                lockContext.reset()
                root.unlockRequested()
            }
        }'''
assert old in s, 'Session-lock mirror anchor changed'
s=s.replace(old, '        onLockedChanged: Qt.callLater(root.synchronizeLockState)', 1)
anchor='    signal lockRequested'
s=s.replace(anchor, '''    function synchronizeLockState() {
        const current = lock.locked
        if (root._sessionLocked === current) return
        root._sessionLocked = current
        if (current) {
            if (root.capturePath !== "") captureTimer.restart()
            root.lockRequested()
        } else {
            lockContext.reset()
            root.unlockRequested()
        }
    }
    Timer {
        interval: 750
        repeat: true
        running: true
        triggeredOnStart: true
        onTriggered: root.synchronizeLockState()
    }

'''+anchor,1)
s=s.replace('        value: lock.locked','        value: root.locked',1)
s=s.replace('        lock.locked = true\n','        lock.locked = true\n        Qt.callLater(root.synchronizeLockState)\n',1)
s=s.replace('            lock.locked = false\n','            lock.locked = false\n            Qt.callLater(root.synchronizeLockState)\n',1)
s=s.replace('        function isLocked(): bool {', '''        function state(): string {
            return JSON.stringify({nativeLocked:lock.locked,publishedLocked:root.locked,
                captureBlocked:GlassTracker.captureBlocked,pending:root.lockPending})
        }
        function isLocked(): bool {''',1)
p.write_text(s)

# A monitor object can exist without activeWorkspace metadata on this Hyprland
# API version. Use the queried workspace inventory in both missing-data cases.
p=root/'rosa/overlays/IslandWindow.qml'
s=p.read_text().replace('        if(!mon){','        if(!mon || !mon.activeWorkspace){',1)
p.write_text(s)
