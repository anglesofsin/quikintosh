"""Responsive desktop controls and the Tahoe widget editing workflow."""
from pathlib import Path
import sys

root = Path(sys.argv[1])
python = sys.argv[2]
here = Path(__file__).parent


def edit(name, before, after, count=1):
    path = root / name
    text = path.read_text()
    if text.count(before) != count:
        raise ValueError(f'Experience anchor {name}: {before[:75]} ({text.count(before)})')
    path.write_text(text.replace(before, after))


for src, dst in [('WallpaperLibrary.qml', 'services/WallpaperLibrary.qml'),
                 ('WallpaperPage.qml', 'ui/settings/pages/WallpaperPage.qml'),
                 ('WidgetGallery.qml', 'ui/widgets/WidgetGallery.qml'),
                 ('WidgetSettings.qml', 'ui/widgets/WidgetSettings.qml'),
                 ('wallpapers.py', 'tools/wallpaper-library.py')]:
    (root / dst).write_text((here / src).read_text().replace('@PYTHON@', python))
for name in ['TahoeButton', 'TahoeField', 'TahoeCombo']:
    (root/'components'/f'{name}.qml').write_text((here/f'{name}.qml').read_text())
    p=root/'components/qmldir'
    p.write_text(p.read_text()+f'\n{name} {name}.qml\n')
for name in ['ui/settings/pages/WallpaperPage.qml','ui/widgets/WidgetGallery.qml','ui/widgets/WidgetSettings.qml']:
    p=root/name
    text=p.read_text().replace('Button{','TahoeButton{').replace('ComboBox{','TahoeCombo{').replace('TextField{','TahoeField{')
    if 'import qs.components\n' not in text:text='import qs.components\n'+text
    p.write_text(text)
p = root / 'services/qmldir'
p.write_text(p.read_text() + '\nsingleton WallpaperLibrary WallpaperLibrary.qml\n')
p = root / 'ui/widgets/qmldir'
if p.exists():
    p.write_text(p.read_text() + '\nWidgetSettings WidgetSettings.qml\n')
# Other wallpaper entrypoints share the same single-process inventory/cache.
(root / 'tools/wallpaper-thumbs/spotlight-list.sh').write_text(
    '#!/usr/bin/env bash\nexec ' + python + ' "$(dirname "$0")/../wallpaper-library.py" "$@"\n')

# Floating settings windows are an application of their own, never a new
# generic Quickshell app in the Dock. Recognize older windows during upgrades.
p = root / 'settings.qml'
p.write_text('//@ pragma AppId org.lickintosh.Settings\n' + p.read_text())
edit('services/SettingsLauncher.qml', ', "--no-duplicate", "--daemonize"', ', "--no-duplicate"')
edit('ui/dock/Dock.qml', '        var clsLow = cls.toLowerCase()', '''        var clsLow = cls.toLowerCase()
        if (clsLow === "org.lickintosh.settings" ||
            (clsLow.indexOf("org.quickshell") === 0 &&
             ["Settings", "Réglages", "Ajustes", "Configurações"].indexOf(c.title || ititle) !== -1)) return "settings-app"''')
edit('ui/dock/Dock.qml', 'dockRoot.activeAppId=String(d.initialClass || d.class || "").toLowerCase()',
     'dockRoot.activeAppId=dockRoot.resolveAppId({cls:d.class,initialClass:d.initialClass,title:d.title,initialTitle:d.initialTitle}).toLowerCase()')
edit('ui/topbar/menubar/activewindows/ActiveWindow.qml', '    function formatName(winClass, winTitle) {',
     '    function formatName(winClass, winTitle) {\n        if(String(winClass).toLowerCase()==="org.lickintosh.settings")return I18n.tr("Réglages")')

# Reserve the widest badge slot instead of relaying out every tray icon when
# unread counts change (0 -> 1, 9 -> 10, 99 -> 99+).
edit('ui/topbar/statusarea/StatusArea.qml',
     'implicitWidth:  _clock.implicitWidth + (_badge.visible ? _badge.width + 4 : 0)',
     'implicitWidth: _clock.implicitWidth + (ShellConfig.options.topbar.clockBadgeVisible ? 34 : 0)')
edit('ui/topbar/statusarea/StatusArea.qml', 'width:   Math.max(16, _badgeTxt.implicitWidth + 8)', 'width: 30')

# The fullscreen popup used to intercept pointer motion over the menu bar,
# making GlobalMenuBar.onEntered unreachable despite its switching logic.
edit('ui/topbar/menubar/globalmenu/PopupMenu.qml', '                id: panel', '''                id: panel
                mask: Region { x:0; y:32; width:panel.width; height:Math.max(0,panel.height-32) }''')
edit('ui/topbar/menubar/globalmenu/GlobalMenuBar.qml', '        root.openIndex = index',
     '        popup.subIndex = -1\n        root.openIndex = index')

# An apps grid must have its final geometry before the first visible frame:
# animating its height creates a new row model and icon loads on every frame.
spot = 'ui/topbar/statusarea/spotlight/SpotlightWindow.qml'
p=root/spot
s=p.read_text();a=s.index('    property var wallpaperList: []');b=s.index('    Timer {\n        interval: ShellConfig.options.spotlight.indexing.incrementalMinutes',a)
s=s[:a]+'''    readonly property var wallpaperList:WallpaperLibrary.personal.map(item=>({title:item.name,description:"Wallpaper",path:item.path,thumb:(WallpaperLibrary.thumbnails[item.path] || "").replace(/^file:\\/\\//,""),isWallpaper:true,isVideo:item.video}))
    function refreshWallpaperList(){WallpaperLibrary.refresh()}

'''+s[b:];p.write_text(s)
picker='ui/topbar/statusarea/spotlight/SpotlightWallpaperPicker.qml'
edit(picker, '        readonly property bool isCurrent:', '''        onIsNearChanged:if(isNear)WallpaperLibrary.request(modelData.path)
        Component.onCompleted:if(isNear)WallpaperLibrary.request(modelData.path)
        readonly property bool isCurrent:''')
edit(picker, '                source: "file://" + tile.modelData.path', '                source:WallpaperLibrary.thumbnails[tile.modelData.path] || ""\n                sourceSize:Qt.size(340,192)')
edit(picker, '                asynchronous: false', '                asynchronous: true')
edit(spot, 'Behavior on Layout.preferredHeight { NumberAnimation { duration: ShellMotion.spatial(0.8);',
     'Behavior on Layout.preferredHeight { enabled: root.opened && !win.gridMode; NumberAnimation { duration: ShellMotion.spatial(0.8);')
edit(spot, 'Behavior on width { NumberAnimation { duration: Math.min(180, ShellMotion.split(1.5));',
     'Behavior on width { enabled:root.opened && !win.gridMode; NumberAnimation { duration: Math.min(180, ShellMotion.split(1.5));')
edit(spot, '                property string selectedAction: ""', '                property string selectedAction: "applications"')
edit(spot, '    function applyPending() {', '''    Timer{id:appsWarmup;interval:250;onTriggered:{if(!root.opened && spotlightLoader.item)spotlightLoader.item.prepareApps()}}
    function applyPending() {''')
edit(spot, '                function doClose() {', '''                function prepareApps(){if(!root.opened)selectedAction="applications"}
                function doClose() {''')
edit(spot, '                    root.closeRequested()\n                    // Retain', '                    root.closeRequested()\n                    appsWarmup.restart()\n                    // Retain')
edit(spot, '''                    showAnim.start()
                    searchField.forceActiveFocus()
                    Qt.callLater''', '''                    root.applyPending()
                    showAnim.start()
                    searchField.forceActiveFocus()
                    Qt.callLater''')
# Prepare the cached apps view while unmapped, rather than resetting and
# rebuilding it in the opening animation.
edit(spot, '                    selectedAction   = ""\n                    currentIdx', '                    // Preserve the prepared grid while the window is unmapped.\n                    currentIdx')
edit(spot, '''                    root.applyPending()
                    showAnim.start()''', '''                    if (LauncherState.pendingAction === "") selectedAction = ""
                    root.applyPending()
                    showAnim.start()''')

# OSD feedback needs no anticipation delay, delayed content reveal or blur
# animation. Keep those flourishes for larger interactive event cards.
window = 'rosa/overlays/IslandWindow.qml'
edit(window, 'IslandConfig.s("anticipate") && !win.big && win.visible',
     'IslandConfig.s("anticipate") && win.hub.kind !== "osd" && !win.big && win.visible')
edit(window, 'response: win.bigMotion ? 0.5 : Motion.isleOpenResponse',
     'response: win.hub.kind === "osd" ? 0.18 : win.bigMotion ? 0.5 : Motion.isleOpenResponse')
edit(window, 'response: pillWidth.target > pillWidth.value\n            ? 0.30 : Motion.isleWidthResponse',
     'response: win.hub.kind === "osd" ? 0.16 : pillWidth.target > pillWidth.value\n            ? 0.30 : Motion.isleWidthResponse')
body = 'rosa/overlays/IslandBody.qml'
edit(body, '        active: body.alive\n        asynchronous: true',
     '        active: body.alive || body.kind === "osd"\n        asynchronous: body.kind !== "osd"')
edit(body, 'layer.enabled: card.haze > 0.004', 'layer.enabled: body.kind !== "osd" && card.haze > 0.004')
p = root / body
p.write_text(p.read_text().replace('body.wide ? Motion.isleRevealDelay : 0', 'body.wide && body.kind !== "osd" ? Motion.isleRevealDelay : 0')
             .replace('body.wide ? Motion.isleRevealMs : Motion.isleHideMs', 'body.kind === "osd" ? Motion.instant : body.wide ? Motion.isleRevealMs : Motion.isleHideMs'))

# The user may disable island OSD and use the native volume/brightness panel.
# Retain its compiled scene too; closing unmaps it and stops all glass streams.
native_osd='ui/osd/OSD.qml'
edit(native_osd,'    property bool blocked:        false','''    property bool blocked:        false
    Presence{id:osdPresence;wanted:root._visible;exitDuration:Math.min(140,ShellMotion.fade())}
    Timer{interval:1000;running:true;onTriggered:_panelLoader.active=true}''')
edit(native_osd,'        onTriggered: _panelLoader.active = false','        onTriggered: {} // Keep the compiled, unmapped scene ready for the next key.')
edit(native_osd,'        id: _panelLoader\n        active: false','        id: _panelLoader\n        active: false\n        asynchronous: !root._visible')
edit(native_osd,'            PanelWindow {','            PanelWindow {\n                visible:osdPresence.present')
edit(native_osd,'duration:    200','duration: Math.min(120,ShellMotion.fade())')
edit(native_osd,'duration:    220','duration: Math.min(120,ShellMotion.fade())')

# Desktop icons and widgets have separate persistent layout controls.
state = 'services/WidgetState.qml'
edit(state, '    property alias showHidden: widgetsAdapter.showHidden', '''    property alias showHidden: widgetsAdapter.showHidden
    property alias iconSize: widgetsAdapter.iconSize
    property alias iconSpacing: widgetsAdapter.iconSpacing
    property alias showDesktopWidgets: widgetsAdapter.showDesktopWidgets
    property alias widgetStyle: widgetsAdapter.widgetStyle
    property alias dimWidgets: widgetsAdapter.dimWidgets
    property alias widgetTint: widgetsAdapter.widgetTint
    property string editingId:""
    property string editingZone:"desktop"
    function editWidget(zone,id){root.editingZone=zone;root.editingId=id}''')
edit(state, '            property bool showHidden: false', '''            property bool showHidden: false
            property int iconSize:56
            property int iconSpacing:40
            property bool showDesktopWidgets:true
            property string widgetStyle:"auto"
            property string dimWidgets:"auto"
            property string widgetTint:"#5589c9"''')
edit(state, '        var entries = []\n        if (widget)', '''        var entries = []
        if (widget) entries.push({label:"Edit Widget…",action:"configure"})
        if (widget)''')
edit(state, '        if (action === "edit") root.openGallery(zone)',
     '        if (action === "configure") root.editWidget(zone,id)\n        else if (action === "edit") root.openGallery(zone)')
edit(state, 'theme: theme || "glass"', 'theme: theme || "auto"', count=2)
edit(state, '    property string galleryTheme: "glass"', '    property string galleryTheme: "auto"')
edit(state, '        root.galleryTheme = "glass"', '        root.galleryTheme = "auto"')
edit(state, '    function setImage(zone, id, path) {', '''    function configure(zone,id,changes){
        const list=root.listOf(zone),i=root.indexOfId(list,id)
        if(i<0)return
        list[i]=Object.assign({},list[i],changes);root.setList(zone,list)
    }
    function setImage(zone, id, path) {''')
p=root/state
s=p.read_text();a=s.index('            if (resolved.type === "image") {');b=s.index('            var sizes =',a)
s=s[:a]+'''            if (resolved.type === "image")entries.push({label:"Choose Photo…",action:"configure"})
'''+s[b:];p.write_text(s)
desktop = 'ui/desktop/DesktopLayer.qml'
edit(desktop, 'readonly property real iconW: 96', 'readonly property real iconW: WidgetState.iconSize+WidgetState.iconSpacing')
edit(desktop, 'readonly property real iconH: 100', 'readonly property real iconH: WidgetState.iconSize+WidgetState.iconSpacing+4')
edit(desktop, '            property var iconCells: ({})', '''            onIconWChanged: Qt.callLater(stage.relayout)
            onIconHChanged: Qt.callLater(stage.relayout)
            property var iconCells: ({})''')
edit(desktop, '                    id: slot', '''                    id: slot
                    visible:WidgetState.showDesktopWidgets || WidgetState.galleryZone==="desktop"''')
edit('ui/desktop/DesktopIcon.qml', '        width: 56\n        height: 56', '        width: WidgetState.iconSize\n        height: width')
edit('ui/desktop/DesktopIcon.qml', '        sourceSize: Qt.size(112, 112)', '        sourceSize: Qt.size(width*2,height*2)')
edit('services/DesktopFiles.qml', '{ label: "Change Wallpaper…", action: "wallpaper" },',
     '{ label: "Change Wallpaper…", action: "wallpaper" },\n            { label: "Desktop View Options…", action: "desktop-options" },')
edit('services/DesktopFiles.qml', '    function handle(action, target) {',
     '    function handle(action, target) {\n        if(action==="desktop-options"){SettingsLauncher.open("DockPage");return}')
p = root / 'ui/settings/pages/DockPage.qml'
s = p.read_text();s = s.replace('    id: root', '    id: root\n' + (here / 'DesktopSettings.qml.inc').read_text().replace('Button{','TahoeButton{').replace('ComboBox{','TahoeCombo{').replace('TextField{','TahoeField{'), 1)
s='import Quickshell\n'+s
p.write_text(s)

# Automatic/clear/tinted looks use one palette and one dimming policy. Existing
# explicit Glass/Light/Dark widgets retain their individual overrides.
edit('ui/widgets/WidgetView.qml', 'import QtQuick\n', 'import QtQuick\nimport Quickshell.Hyprland\nimport QtQuick.Effects\n')
edit('ui/widgets/WidgetView.qml', '    width: root.dims.w', '''    readonly property string style:(root.widgetData.theme || "auto")==="auto" ? WidgetState.widgetStyle:(root.widgetData.theme || "auto")
    readonly property bool muted:root.widgetData.id!=="preview" && WidgetState.galleryZone==="" && (WidgetState.dimWidgets==="always" || (WidgetState.dimWidgets==="auto" && !!Hyprland.activeToplevel))
    readonly property color tint:WidgetState.widgetTint
    layer.enabled:root.muted
    layer.effect:MultiEffect{saturation:-1}
    opacity:root.muted ? 0.78:1
    Behavior on opacity{NumberAnimation{duration:ShellMotion.fade()}}
    width: root.dims.w''')
edit('ui/widgets/WidgetView.qml', 'theme: root.widgetData.theme || "glass"', 'theme:root.style')
edit('ui/widgets/WidgetView.qml', '        color: palette.background', '        color:root.style==="tinted" ? Qt.tint(palette.background,Qt.rgba(root.tint.r,root.tint.g,root.tint.b,0.32)):palette.background')
edit('ui/widgets/WidgetPalette.qml', 'import QtQuick', 'import QtQuick\nimport qs.services')
edit('ui/widgets/WidgetPalette.qml', 'root.theme === "light"', '(root.theme === "light" || ((root.theme === "auto" || root.theme === "color" || root.theme === "tinted") && Theme.isLight))')
edit('ui/widgets/WidgetPalette.qml', 'root.theme === "dark"', '(root.theme === "dark" || ((root.theme === "auto" || root.theme === "color" || root.theme === "tinted") && !Theme.isLight))')
edit('ui/widgets/WidgetPalette.qml', 'root.theme !== "light" && root.theme !== "dark"', 'root.theme === "glass" || root.theme === "clear"')
# The backdrop's desktop replica must follow the same sizing, visibility and
# colors, otherwise glass would still show old icons or disabled widgets.
snapshot='components/glass/DesktopSnapshot.qml'
edit(snapshot,'            model: WidgetState.desktop','            model:root.widgetsShown && WidgetState.showDesktopWidgets ? WidgetState.desktop:[]')
edit(snapshot,'                width: 56\n                height: 56','                width:WidgetState.iconSize\n                height:width')
edit(snapshot,'                sourceSize: Qt.size(112, 112)','                sourceSize:Qt.size(width*2,height*2)')
snapshot='ui/widgets/WidgetSnapshot.qml'
edit(snapshot,'import QtQuick\n','import QtQuick\nimport QtQuick.Effects\nimport Quickshell.Hyprland\n')
edit(snapshot,'    width: root.dims.w', '''    readonly property string style:(root.widgetData.theme || "auto")==="auto" ? WidgetState.widgetStyle:(root.widgetData.theme || "auto")
    readonly property bool muted:WidgetState.galleryZone==="" && (WidgetState.dimWidgets==="always" || (WidgetState.dimWidgets==="auto" && !!Hyprland.activeToplevel))
    readonly property color tint:WidgetState.widgetTint
    layer.enabled:root.muted
    layer.effect:MultiEffect{saturation:-1}
    opacity:root.muted ? 0.78:1
    width: root.dims.w''')
edit(snapshot,'theme: root.widgetData.theme || "glass"','theme:root.style')
edit(snapshot,'color: palette.glass ? "#59101014" : palette.background','color:palette.glass ? "#59101014":root.style==="tinted" ? Qt.tint(palette.background,Qt.rgba(root.tint.r,root.tint.g,root.tint.b,0.32)):palette.background')
# Keep the edit-mode remove button above widget interactions.
edit(desktop, '''                    DragHandler {
                        target: null''', '''                    Rectangle{
                        visible:WidgetState.galleryZone==="desktop"
                        x:-7;y:-7;width:25;height:25;radius:13;color:"#e8d7d9de";border.width:1;border.color:"#60000000";z:200
                        Text{anchors.centerIn:parent;text:"−";font.pixelSize:21;color:"#25262b"}
                        MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:WidgetState.removeWidget("desktop",slot.spec.id)}
                    }
                    DragHandler {
                        target: null''')
# Other widget zones share the same configuration dialog.
edit('shell.qml', '    id: appRoot', '    id: appRoot\n    WidgetSettings{}') if 'import qs.ui.widgets' in (root/'shell.qml').read_text() else None
