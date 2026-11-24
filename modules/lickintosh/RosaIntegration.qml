import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.ui.topbar.statusarea.notifcenter as NativeNotifications
import qs.rosa.overlays as Rosa
import qs.rosa.panels as RosaPanels
import qs.rosa.services as RosaServices

Scope {
    id: root
    property bool enabled: false
    property bool locked: false
    property real brightness: -1
    readonly property bool osdActive: enabled && !locked && RosaServices.IslandConfig.s("enabled") && RosaServices.IslandConfig.on("osd")
    property bool feedbackReady: false
    Timer { interval: 1500; running: true; onTriggered: root.feedbackReady = true }
    onBrightnessChanged: {
        if (root.feedbackReady && root.osdActive && root.brightness >= 0)
            RosaServices.Feedback.flash("󰃞",root.brightness,true,"Brightness",false,"brightness")
    }
    signal settingsOpening()
    function openSettings() {
        if(root.locked) return
        closeAuxiliary()
        settingsOpening()
        SettingsLauncher.open("RosaPage")
    }
    onLockedChanged: { if (locked) closeAuxiliary() }
    Connections {
        target: RosaServices.IslandBus
        function onSettingsRequested() { root.openSettings() }
    }
    Binding { target: RosaServices.IslandBus; property: "locked"; value: root.locked }
    LazyLoader {
        id: islandLoader
        active: root.enabled && !root.locked && RosaServices.IslandConfig.s("enabled")
        Rosa.Island {}
    }
    function closeAuxiliary(except) {
        for (var loader of [systemPanel, processesPanel, calendarPanel, timerPanel])
            if (loader !== except) loader.active = false
    }
    function openPanel(name) {
        var loader = ({system:systemPanel,processes:processesPanel,calendar:calendarPanel,timers:timerPanel})[name]
        if (!loader || root.locked) return false
        closeAuxiliary(loader)
        settingsOpening()
        loader.active = true
        Qt.callLater(function(){if(loader.item) loader.item.shown = true})
        return true
    }
    LazyLoader { id:systemPanel; active:false; RosaPanels.SysRings { onShownChanged: { if(!shown) systemPanel.active=false } } }
    LazyLoader { id:processesPanel; active:false; RosaPanels.Procs { onShownChanged: { if(!shown) processesPanel.active=false } } }
    LazyLoader { id:calendarPanel; active:false; RosaPanels.Calendar { onShownChanged: { if(!shown) calendarPanel.active=false } } }
    LazyLoader { id:timerPanel; active:false; RosaPanels.TimerPanel { onShownChanged: { if(!shown) timerPanel.active=false } } }
    Connections {
        target: RosaServices.IslandBus
        function onSysOpen() { root.openPanel("system") }
        function onProcsOpen() { root.openPanel("processes") }
        function onCalendarAt(ms) { root.openPanel("calendar");Qt.callLater(function(){if(calendarPanel.item)calendarPanel.item.select(new Date(ms))}) }
    }
    Process {
        running: root.enabled && !root.locked && !!islandLoader.item && RosaServices.IslandConfig.on("shot")
        command: ["python3",Quickshell.shellDir+"/rosa/watch-screenshots.py"]
        stdout: SplitParser {
            onRead: line => {
                try { if(islandLoader.item) islandLoader.item.shot(JSON.parse(line)) }
                catch(error) { console.warn("Rosa screenshot event:",error) }
            }
        }
    }
    IpcHandler {
        target: "rosa"
        function settings(): void { root.openSettings() }
        function panel(name:string): string {return root.openPanel(name) ? "opened" : "unavailable"}
        function close(): void { root.closeAuxiliary(); if(islandLoader.item) { islandLoader.item.runDemo("stop"); islandLoader.item.mediaBig=false; islandLoader.item.dismiss() } }
        function status(): string {
            return JSON.stringify({enabled:root.enabled,loaded:!!islandLoader.item,locked:root.locked,
                inBar:RosaServices.IslandConfig.s("inBar"),offsetX:RosaServices.IslandConfig.s("offsetX"),pillHeight:RosaServices.IslandConfig.s("pillHeight"),settingsProvider:"lickintosh",leftActivity:islandLoader.item ? islandLoader.item.leftKind : "",downloads:islandLoader.item ? islandLoader.item.downloading : 0,kind:islandLoader.item ? islandLoader.item.kind : "",
                notifications:NativeNotifications.NotifService.trackedCount,popups:NativeNotifications.NotifService.popupModel.count,
                knobs:Object.keys(RosaServices.IslandConfig.spec).length})
        }
        function set(name:string, value:string): string {
            if (!islandLoader.item) return "island inactive"
            return islandLoader.item.knob(name,value)
        }
    }
}
