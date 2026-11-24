from pathlib import Path
import sys
root=Path(sys.argv[1])
def edit(name,old,new,count=1):
 p=root/name;s=p.read_text();assert old in s,(name,old);p.write_text(s.replace(old,new,count))
edit('shell.qml','  HyprPersist {}','  // Hyprland rules are managed by the NixOS configuration.')
edit('shell.qml','  id: root','  id: root\n'+Path(sys.argv[2]).read_text())
edit('config/Directories.qml','/.config/aureli','/.config/eqsh')
edit('ui/components/lockscreen/LockContext.qml','configDirectory: "pam"','configDirectory: "/etc/pam.d"')
edit('ui/components/lockscreen/LockContext.qml','config: "password.conf"','config: "eqsh-lock"')
edit('config/Default.qml','root.homeDirectory+"/.local/share/equora/eqsh/config/sigrid_system_prompt.txt"','Quickshell.shellDir + "/config/sigrid_system_prompt.txt"')
edit('config/mixins.js','"eqdesktop.settings": {','"eqdesktop.settings": {\n        page: [],')
edit('config/mixins.js','"eqdesktop.spotlight": {','"eqdesktop.spotlight": {\n        section: [],')
edit('config/mixins.js','"eqdesktop.menubar": {','"eqdesktop.menubar": {\n        session: [],')
edit('config/mixins.js','        isLoaded: []','        isLoaded: [],\n        isLocked: []')
edit('Ipc.qml','runMixin("eqdesktop.notch", "activateInstance")','runMixin("eqdesktop.notch", "activeInstance")')
edit('modules/spotlight/Spotlight.qml','    Component.onCompleted: {','    Component.onCompleted: {\n        Ipc.mixin("eqdesktop.spotlight", "section", (name) => root.clickAction(name));')
edit('modules/settings/Settings.qml','                        id: contentView','                        id: contentView\n                        Component.onCompleted: Ipc.mixin("eqdesktop.settings", "page", (index) => contentView.currentIndex = index)')
edit('ui/components/dock/Dock.qml','    visible: true','    visible: Config.dock.enable')
# Add the session handler next to the menu so its identifier is in scope.
edit('ui/components/panel/StatusBar.qml','            id: lBAppMenuDrop','            id: lBAppMenuDrop\n            Component.onCompleted: Ipc.mixin("eqdesktop.menubar", "session", () => lBAppMenuDrop.opened = !lBAppMenuDrop.opened)')
# Remove the blanket OpenGL/Vulkan override; let Qt select the compatible backend.
edit('shell.qml','//@ pragma Env QSG_RHI_BACKEND=vulkan','// Render backend follows the current Qt/driver configuration.')

edit('config/mixins.js', '"eqdesktop.controlCenter": {', '"eqdesktop.controlCenter": {\n        toggle: [],')
edit('ui/components/panel/ControlCenter.qml', '    Component.onCompleted: {', '    Component.onCompleted: {\n      Ipc.mixin("eqdesktop.controlCenter", "toggle", () => panelWindow.opened = !panelWindow.opened)')

edit('ui/components/screenshot/Screenshot.qml', '"Desktop/"', '(Quickshell.env("HOME") + "/Pictures/Screenshots/")', -1)
edit('ui/components/screenshot/Screenshot.qml', '"Documents/"', '(Quickshell.env("HOME") + "/Documents/")', -1)

edit('ui/components/panel/CCBluetooth.qml', 'property var enabled: adapter.enabled', 'property var enabled: adapter ? adapter.enabled : false')
edit('ui/components/screenshot/Screenshot.qml', 'property var outputMon: (CompositorService.isHyprland ? Hyprland.focusedMonitor : NiriService.outputs[NiriService.currentOutput])', 'property var outputMon: CompositorService.getFocusedScreen()')
edit('Ipc.qml', 'return returnLastMixin("eqdesktop.lock", "isLocked")', 'return Runtime.locked')
