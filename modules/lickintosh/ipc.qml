    // Local Nix integration: no installer or compositor keybind replacement.
    property bool riceBarVisible: true
    IpcHandler {
        target: "rice"
        function status(): string { return "ready" }
        function state(): string {
            return JSON.stringify({ launcher: appRoot.spotlightOpened,
                controlCenter: appRoot.ccOpened, notifications: appRoot.notifCenterOpened,
                session: appRoot.appleMenuOpened, bar: appRoot.riceBarVisible,
                dock: ShellConfig.options.dockAppearance.enable,
                theme: ShellConfig.options.appearance.mode, widgets: WidgetState.galleryZone,
                dnd: NotifService.dndEnabled, ai: appRoot.aiOpened,
                gameMode: GameMode.enabled, keepAwake: KeepAwake.enabled,
                nightlight: NightShift.enabled, locked: lockScreen.locked })
        }
        function prepareStop(): void { if (GameMode.enabled) GameMode.disable() }
        function clipboard(): void { LauncherState.pendingAction = "clipboard"; LauncherState.requested() }
        function emoji(): void { LauncherState.pendingAction = "emoji"; LauncherState.requested() }
        function command(): void { LauncherState.pendingAction = "command"; LauncherState.requested() }
        function launchpad(): void { LauncherState.openApplications() }
        function spotlight(): void { LauncherState.pendingAction = "spotlight"; LauncherState.requested() }
        function launcher(): void { appRoot.spotlightOpened = !appRoot.spotlightOpened }
        function controlCenter(): void { appRoot.ccOpened = !appRoot.ccOpened }
        function notifications(): void { appRoot.notifCenterOpened = !appRoot.notifCenterOpened }
        function session(): void { appRoot.appleMenuOpened = !appRoot.appleMenuOpened }
        function bar(): void { appRoot.riceBarVisible = !appRoot.riceBarVisible }
        function dock(): void { ShellConfig.options.dockAppearance.enable = !ShellConfig.options.dockAppearance.enable }
        function settings(): void { SettingsLauncher.open("") }
        function wallpaper(): void { SettingsLauncher.open("WallpaperPage") }
        function theme(): void { ShellConfig.options.appearance.mode = Theme.isDark ? "light" : "dark" }
        function nightlight(): void { NightShift.toggle() }
        function widgetGallery(zone: string): void { WidgetState.galleryZone = ["desktop", "notifCenter"].includes(zone) ? zone : "" }
        function widgets(): void { WidgetState.galleryZone = WidgetState.galleryZone === "desktop" ? "" : "desktop" }
        function dnd(): void { NotifService.dndEnabled = !NotifService.dndEnabled }
        function ai(): void { appRoot.aiOpened = !appRoot.aiOpened }
        function gameMode(): void { GameMode.toggle() }
        function keepAwake(): void { KeepAwake.toggle() }
        function closePanels(): void {
            appRoot.spotlightOpened = false
            appRoot.ccOpened = false
            appRoot.notifCenterOpened = false
            appRoot.appleMenuOpened = false
            appRoot.aiOpened = false
            WidgetState.galleryZone = ""
        }
    }
