  IpcHandler {
    target: "rice"
    function status(): string { return "ready" }
    function state(): string {
      return JSON.stringify({launchpad: Runtime.launchpadOpen, spotlight: Runtime.spotlightOpen,
        settings: Runtime.settingsOpen, ai: Runtime.aiOpen, widgets: Runtime.widgetEditMode,
        screenshot: Runtime.showScrn, locked: Runtime.locked, dock: Config.dock.enable,
        bar: Config.bar.enable, dnd: NotificationDaemon.popupInhibited})
    }
    function launchpad(): void { Runtime.launchpadOpen = !Runtime.launchpadOpen }
    function spotlight(): void { Runtime.spotlightOpen = !Runtime.spotlightOpen }
    function clipboard(): void { Runtime.spotlightOpen = true; Ipc.runMixin("eqdesktop.spotlight", "section", "clipboard") }
    function command(): void { Runtime.spotlightOpen = true; Ipc.runMixin("eqdesktop.spotlight", "section", "actions") }
    function bar(): void { Config.bar.enable = !Config.bar.enable }
    function dock(): void { Config.dock.enable = !Config.dock.enable }
    function theme(): void { Config.general.darkMode = !Config.general.darkMode }
    function wallpaper(): void { Runtime.settingsOpen = true; Ipc.runMixin("eqdesktop.settings", "page", 10) }
    function controlCenter(): void { Ipc.runMixin("eqdesktop.controlCenter", "toggle") }
    function session(): void { Ipc.runMixin("eqdesktop.menubar", "session") }
  }
