"""Local performance fixes; keep the original shell's features and glass rendering."""
from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new,count=1):
 p=root/name;s=p.read_text()
 if old not in s:raise ValueError(f'Missing optimization anchor in {name}: {old[:70]}')
 p.write_text(s.replace(old,new,count))

spot='ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
# Keep the popup's compiled scene, unmap its window while closed, and warm it asynchronously.
edit(spot,'    property bool _spotlightLoaded: false','''    property bool _spotlightLoaded: false
    Timer { interval: 1800; running: true; onTriggered: root._spotlightLoaded = true }
    property double lastMetadataRefresh: 0
    Timer {
        id: metadataRefresh
        interval: 180
        onTriggered: {
            if (!root.opened || Date.now() - root.lastMetadataRefresh < 10000) return
            root.lastMetadataRefresh = Date.now()
            RecentFiles.refresh()
            root.refreshClipHistory()
            root.refreshUserActions()
            if (root.wallpaperList.length === 0) root.refreshWallpaperList()
        }
    }''')
edit(spot,'''            RecentFiles.refresh()
            root.refreshClipHistory()
            root.refreshUserActions()
            root.refreshWallpaperList()''','''            metadataRefresh.restart()''')
edit(spot,'        active: root._spotlightLoaded','        active: root._spotlightLoaded\n        asynchronous: !root.opened')
edit(spot,'                id: win','                id: win\n                visible: root.opened || hideAnim.running')
edit(spot,'                    root._spotlightLoaded = false','                    // Retain the compiled popup; visible=false unmaps the window.')
# First creation can happen in the background. Do not focus or animate a hidden window.
edit(spot,'''                    showAnim.start()
                    searchField.forceActiveFocus()''','''                    if (root.opened) {
                        showAnim.start()
                        searchField.forceActiveFocus()
                    }''')
edit(spot,'                    showAnim.start()\n                }\n\n                function refreshClipboard','                    showAnim.start()\n                    searchField.forceActiveFocus()\n                }\n\n                function refreshClipboard')
edit(spot,'duration: ShellMotion.enter();','duration: Math.min(160, ShellMotion.enter());')
edit(spot,'duration: ShellMotion.exit(1.5);','duration: Math.min(120, ShellMotion.exit(1.5));')
edit(spot,'duration: ShellMotion.split(1.5);','duration: Math.min(180, ShellMotion.split(1.5));')
edit(spot,'                GlassBackdrop { element: "spotlight" }','                GlassBackdrop { element: "spotlight"; gateTimeout: 120 }')
# Exclude directories before descending, rather than walking every excluded subtree.
a=(root/spot).read_text();start=a.index('    readonly property string findExcludes: {');end=a.index('    readonly property string fileIndexCache:',start)
a=a[:start]+'''    readonly property string findExcludes: {
        var parts = ["-name '.*'"]
        var excludes = ShellConfig.options.spotlight.indexing.excludePaths
        for (var i = 0; i < excludes.length; i++) {
            var safe = String(excludes[i]).replace(/'/g, "")
            if (safe.length > 0) parts.push("-name '" + safe + "'")
        }
        return "\\\\( " + parts.join(" -o ") + " \\\\) -prune -o"
    }
'''+a[end:];(root/spot).write_text(a)
# Cache app sorting/category lookup across launches, search edits and popup creation.
edit(spot,'    function wrapApp(entry, cat) {','''    readonly property var alphabeticalApps: DesktopEntries.applications.values.slice().sort(function(a, b) { return a.name.localeCompare(b.name) })
    readonly property var cachedAppItems: {
        var sorted = root.sortAppsByUsage(root.alphabeticalApps)
        var out = []
        for (var i = 0; i < sorted.length; i++) out.push(root.wrapApp(sorted[i], root.categoryForApp(sorted[i])))
        return out
    }

    function wrapApp(entry, cat) {''')
a=(root/spot).read_text();start=a.index('                property var appItems: {');end=a.index('                property var fileItems:',start)
a=a[:start]+'                readonly property var appItems: root.cachedAppItems\n'+a[end:];(root/spot).write_text(a)
edit(spot,'DesktopEntries.applications.values.slice().sort(function(a, b) { return a.name.localeCompare(b.name) })\n                            return allApps','root.alphabeticalApps\n                            return allApps')
# Virtualize rows: preserve categories, suggestions, files, thumbnails and click actions.
grid='ui/topbar/statusarea/spotlight/SpotlightCategoryGrid.qml';s=(root/grid).read_text()
start=s.index('                                delegate: Item {');brace=s.index('{',start);depth=1;end=brace+1
while depth:
 if s[end]=='{':depth+=1
 elif s[end]=='}':depth-=1
 end+=1
tile=s[brace+1:end-1]
tile=tile.replace('active: tile.modelData.isVideo === true','active: root.visible && tile.modelData.isVideo === true')
start=s.index('        Flickable {\n            id: scrollArea')
s=s[:start]+'''        ListView {
            id: scrollArea
            Layout.fillWidth: true
            Layout.fillHeight: true
            clip: true
            reuseItems: true
            cacheBuffer: 100
            boundsBehavior: Flickable.StopAtBounds
            model: root.rowModel
            delegate: Item {
                required property var modelData
                width: scrollArea.width
                height: modelData.title !== "" ? 28 : 100
                Text {
                    visible: parent.modelData.title !== ""
                    text: parent.modelData.title
                    color: Theme.ink(parent, false)
                    opacity: 0.55
                    font.family: root.fontFamilyMedium
                    font.pixelSize: 13
                    font.weight: Font.DemiBold
                    renderType: Text.NativeRendering
                }
                Row {
                    spacing: 10
                    Repeater {
                        model: parent.parent.modelData.items
                        delegate: Tile {}
                    }
                }
            }
        }
    }
}
'''
pos=s.index('    ColumnLayout {')
s=s[:pos]+'''    readonly property int columns: Math.max(1, Math.floor((root.width + 10) / 88))
    readonly property var rowModel: {
        var groups = root.sectioned
            ? [{title: I18n.tr("Suggestions"), items: root.filteredItems.slice(0, root.suggestionsCount)},
               {title: I18n.tr("Récents"), items: root.filteredItems.slice(root.suggestionsCount)}]
            : [{title: "", items: root.filteredItems}]
        var rows = []
        for (var g = 0; g < groups.length; g++) {
            if (groups[g].items.length === 0) continue
            if (groups[g].title !== "") rows.push({title: groups[g].title, items: []})
            for (var i = 0; i < groups[g].items.length; i += root.columns)
                rows.push({title: "", items: groups[g].items.slice(i, i + root.columns)})
        }
        return rows
    }

    component Tile: Item {'''+tile+'\n    }\n\n'+s[pos:];(root/grid).write_text(s)
# Resolve each themed icon once, shared across the dock, grids, widgets and search.
edit('services/IconResolver.qml','    function byName(name) {\n        return name ? root.retheme(Quickshell.iconPath(name, true)) : ""\n    }','''    property var iconCache: ({})
    Connections { target: Theme; function onIconThemeChanged() { root.iconCache = ({}) } }
    Connections { target: DesktopEntries.applications; function onValuesChanged() { root.iconCache = ({}) } }
    function byName(name) {
        if (!name) return ""
        var key = Theme.iconTheme + ":" + name
        if (root.iconCache[key] !== undefined) return root.iconCache[key]
        var value = root.retheme(Quickshell.iconPath(name, true))
        root.iconCache[key] = value
        return value
    }''')
# Pause background capture for retained but hidden panels.
edit('components/glass/GlassBackdrop.qml','    ready: !Theme.plainSurfaces','    ready: !Theme.plainSurfaces && (!root.win || root.win.visible)')
edit('components/glass/GlassBackdrop.qml','    captureWindows: ShellConfig.options.glass.captureWindows','    captureWindows: root.ready && ShellConfig.options.glass.captureWindows')
edit('components/glass/LiquidGlassBackdrop.qml','active: root.captureWindows','active: root.ready && root.captureWindows')
edit('components/glass/LiquidGlassBackdrop.qml','shown: root.showDesktopItems','shown: root.ready && root.showDesktopItems')
edit('components/glass/LiquidGlassBackdrop.qml','widgetsShown: root.showDesktopWidgets','widgetsShown: root.ready && root.showDesktopWidgets')
# Monitor/workspace snapshots are event-driven; keep window geometry capture responsive.
tracker='components/glass/GlassTracker.qml'
edit(tracker,'        if (!monitorQuery.running) monitorQuery.running = true\n        Hyprland.refreshMonitors()\n        Hyprland.refreshToplevels()','        Hyprland.refreshToplevels()')
edit(tracker,'    property int captureUsers: 0','''    function refreshMonitorSnapshot() {
        if (!monitorQuery.running) monitorQuery.running = true
        Hyprland.refreshMonitors()
    }
    property int captureUsers: 0
    onCaptureUsersChanged: {
        if (captureUsers > 0) { refreshMonitorSnapshot(); refreshWindows() }
    }''')
edit(tracker,'            var n = event.name','''            var n = event.name
            if (root.transitionEvents.indexOf(n) !== -1 || n === "focusedmon" || n.indexOf("monitor") === 0)
                root.refreshMonitorSnapshot()''')
edit(tracker,'    property int captureIdleInterval: 200','    property int captureIdleInterval: 500')
# CPU/memory process scans only while an energy view is visible.
edit('services/ShellConfig.qml','    property var previousSample: ({})','''    property var energyObservers: ({})
    readonly property bool energyVisible: Object.keys(root.energyObservers).length > 0
    function watchEnergy(id, active) {
        var next = Object.assign({}, root.energyObservers)
        if (active) next[id] = true
        else delete next[id]
        root.energyObservers = next
    }
    onEnergyVisibleChanged: {
        if (energyVisible) { root.previousTimestamp = 0; _sampleProc.running = true; energyFirstSample.restart() }
        else { energyFirstSample.stop(); _sampleProc.running = false }
    }
    Timer { id: energyFirstSample; interval: 1000; onTriggered: { if(root.energyVisible && !_sampleProc.running) _sampleProc.running = true } }
    property var previousSample: ({})''')
edit('services/ShellConfig.qml','        interval: 3000\n        running: true','        interval: 3000\n        running: root.energyVisible')
edit('services/ShellConfig.qml','        _sampleProc.running   = true','        // Process sampling is requested by visible energy views.')
for name,identity in [('ui/settings/pages/BatteryPage.qml','battery-settings'),('ui/topbar/statusarea/battery/BatteryPanel.qml','battery-panel')]:
 p=root/name;s=p.read_text()
 if 'import Quickshell\n' not in s:s=s.replace('import QtQuick\n','import QtQuick\nimport Quickshell\n',1)
 s=s.replace('    id: root','''    id: root
    readonly property bool energyActive: visible && (QsWindow.window ? QsWindow.window.visible : false)
    onEnergyActiveChanged: ShellConfig.watchEnergy("'''+identity+'''", energyActive)
    Component.onDestruction: ShellConfig.watchEnergy("'''+identity+'''", false)''',1)
 p.write_text(s)

# Replace hundreds of per-process shell forks with one /proc reader.
(root/'tools/energy-usage/sample-processes.py').write_text(r'''import os
import re
from pathlib import Path
exclude = re.compile(r"^(ps|awk|bash|sh|sleep|grep|cut|nproc|readlink|basename|cat|sort|head|find|dirname|mktemp|sample-processes\.sh|find-app-icon\.sh)$")
rows = {}
for entry in os.scandir('/proc'):
    if not entry.name.isdigit(): continue
    p = Path(entry.path)
    try:
        comm = (p/'comm').read_text().strip()
        if exclude.fullmatch(comm): continue
        fields = (p/'stat').read_text().rpartition(') ')[2].split()
        ticks = int(fields[11]) + int(fields[12])
        try: name = os.path.basename(os.readlink(p/'exe'))
        except OSError: name = comm
        name = name.removeprefix('.').removesuffix('-wrapped').removesuffix('.wrapped') or 'unknown'
        if exclude.fullmatch(name): continue
        try:
            text = (p/'smaps_rollup').read_text()
            memory = {line.split(':',1)[0]:int(line.split()[1]) for line in text.splitlines() if line.startswith(('Pss:', 'SwapPss:'))}
            rss, swap = memory.get('Pss',0), memory.get('SwapPss',0)
        except OSError:
            text = (p/'status').read_text()
            memory = {line.split(':',1)[0]:int(line.split()[1]) for line in text.splitlines() if line.startswith(('VmRSS:', 'VmSwap:'))}
            rss, swap = memory.get('VmRSS',0), memory.get('VmSwap',0)
        values = rows.setdefault(name, [0,0,0])
        values[0] += ticks; values[1] += rss; values[2] += swap
    except (OSError, ValueError, IndexError): continue
for name, values in rows.items(): print(name+';'+ ';'.join(map(str, values)))
''')
edit('services/ShellConfig.qml', '["bash", Quickshell.shellDir + "/tools/energy-usage/sample-processes.sh"]', '["python3", Quickshell.shellDir + "/tools/energy-usage/sample-processes.py"]')
# Native compositor shortcuts avoid spawning the shell router and IPC client per keypress.
edit('services/LauncherState.qml', 'import Quickshell\n', 'import Quickshell\nimport Quickshell.Hyprland\n')
edit('services/LauncherState.qml', '    signal requested()', '''    signal requested()
    GlobalShortcut {
        appid: "lickintosh"
        name: "spotlight"
        description: "Open Spotlight"
        onPressed: { root.pendingAction = "spotlight"; root.requested() }
    }
    GlobalShortcut {
        appid: "lickintosh"
        name: "launchpad"
        description: "Open Launchpad"
        onPressed: root.openApplications()
    }''')

edit('services/ShellConfig.qml', '        onExited: function() {\n            var now = Date.now()', '        onExited: function() {\n            if (!root.energyVisible) { _sampleProc.pending = ({}); return }\n            var now = Date.now()')
edit('ui/topbar/statusarea/spotlight/SpotlightWindow.qml', '    property var fileIndex:  []', '    property var fileIndex:  []\n    readonly property var lowercaseFileIndex: root.fileIndex.map(function(path) { return path.toLowerCase() })')
edit('ui/topbar/statusarea/spotlight/SpotlightWindow.qml', 'root.fileIndex[i].toLowerCase().indexOf(q)', 'root.lowercaseFileIndex[i].indexOf(q)')
# Reuse Settings instead of accumulating one full service stack per opening.
edit('settings.qml', 'import Quickshell\n', 'import Quickshell\nimport Quickshell.Io\n')
edit('settings.qml', '    id: root', '''    id: root
    IpcHandler {
        target: "settingsWindow"
        function open(page: string): void {
            if (page) {
                for (var i = 0; i < root.flatItems.length; i++) {
                    if (root.flatItems[i].component === page) { root.currentIndex = i; break }
                }
            }
            root.visible = false
            Qt.callLater(function() { root.visible = true })
        }
    }''')
(root/'services/SettingsLauncher.qml').write_text('''pragma Singleton
import Quickshell
import Quickshell.Io
import QtQuick
Singleton {
    id: root
    property string requestedPage: ""
    function open(page) {
        if (activateProc.running) return
        root.requestedPage = page || ""
        activateProc.running = true
    }
    Process {
        id: activateProc
        command: ["quickshell", "-p", Quickshell.shellDir + "/settings.qml", "ipc", "call", "settingsWindow", "open", root.requestedPage]
        stdout: StdioCollector {}
        stderr: StdioCollector {}
        onExited: function(code) {
            if (code === 0) return
            var cmd = ["quickshell", "-p", Quickshell.shellDir + "/settings.qml", "--no-duplicate", "--daemonize"]
            if (root.requestedPage) cmd = ["env", "LICKINTOSH_PAGE=" + root.requestedPage].concat(cmd)
            Quickshell.execDetached(cmd)
        }
    }
}
''')
