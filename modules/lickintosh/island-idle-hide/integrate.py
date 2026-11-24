"""Optional idle hiding, using a single timer and compositor-friendly transforms."""
from pathlib import Path
import sys

root=Path(sys.argv[1]);here=Path(__file__).parent

def edit(name, before, after):
    p=root/name;s=p.read_text()
    if s.count(before)!=1:
        raise ValueError(f'Idle hiding anchor changed: {name}: {before[:60]}')
    p.write_text(s.replace(before,after,1))

(root/'rosa/overlays/IdleVisibility.qml').write_text((here/'IdleVisibility.qml').read_text())
p=root/'rosa/overlays/qmldir'
p.write_text(p.read_text()+'\nIdleVisibility IdleVisibility.qml\n')
edit('rosa/services/IslandConfig.qml','        enabled:     { type: "bool", def: true },','''        enabled:     { type: "bool", def: true },
        idleAutoHide: { type:"bool", def:false },
        idleHideSeconds: { type:"int", def:15, min:0, max:3600 },''')
edit('ui/settings/pages/RosaPage.qml','''    ContentSection {
        title: "Voice integration"''','''    ContentSection {
        title: "Automatic hiding"
        ConfigSwitch {
            text:"Automatically hide when inactive"
            checked:Rosa.IslandConfig.s("idleAutoHide")
            onToggled:value=>Rosa.IslandConfig.setStyle("idleAutoHide",value)
        }
        RowLayout {
            Layout.fillWidth:true;spacing:14
            enabled:Rosa.IslandConfig.s("idleAutoHide")
            CFText{Layout.fillWidth:true;text:"Inactivity delay (seconds)";font.pixelSize:13;color:Theme.textPrimary}
            TahoeField {
                Layout.preferredWidth:100
                text:String(Rosa.IslandConfig.s("idleHideSeconds"))
                validator:IntValidator{bottom:0;top:3600}
                selectByMouse:true
                onEditingFinished:if(acceptableInput)Rosa.IslandConfig.setStyle("idleHideSeconds",Number(text))
            }
        }
    }
    ContentSection {
        title: "Voice integration"''')
edit('rosa/overlays/IslandWindow.qml','    readonly property bool wanted:','''    readonly property bool idleEligible:
        (win.hub.kind === "clock" || win.hub.kind === "")
        && !win.hub.miniMedia && win.hub.leftKind === ""
        && !win.hub.pinned && !win.hub.demoWide && !win.seeking
        && !comet.on && !suck.on
        && !win.pointerIn && !win.hovering && !win.wide
        && !(IslandConfig.s("privacy") && Privacy.active)
    readonly property bool suppressIdleClock:
        IslandConfig.s("idleAutoHide") && IslandConfig.s("idleHideSeconds") === 0
        && win.idleEligible
    IdleVisibility {
        id:idleVisibility
        autoHide:IslandConfig.s("idleAutoHide")
        idle:win.idleEligible && !IslandBus.locked
        delayMs:IslandConfig.s("idleHideSeconds")*1000
        animate:!SettingsPreferences.accessibility.reduceMotion
    }
    readonly property bool wanted:''')
edit('rosa/overlays/IslandWindow.qml','''        win.hub.kind !== "" || win.hub.miniMedia || win.hub.leftKind !== ""
        || win.seeking''','''        win.hub.kind !== "" || win.hub.miniMedia || win.hub.leftKind !== ""
        || win.seeking || comet.on || suck.on''')
# Native services are already exposed to the hub, but this window uses a
# separate import namespace to avoid conflicting Rosa singleton names.
edit('rosa/overlays/IslandWindow.qml','import qs.rosa.services\n','import qs.rosa.services\nimport qs.services as NativeSettings\n')
p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text().replace('animate:!SettingsPreferences.accessibility.reduceMotion','animate:!NativeSettings.SettingsPreferences.accessibility.reduceMotion');p.write_text(s)
edit('rosa/overlays/IslandWindow.qml','visible: !IslandBus.locked && IslandConfig.s("enabled")','visible: !IslandBus.locked && IslandConfig.s("enabled") && !idleVisibility.fullyHidden')
edit('rosa/overlays/IslandWindow.qml','        opacity: birth.value\n        scale:','        opacity: birth.value * Math.min(1,idleVisibility.progress*4)\n        scale:')
edit('rosa/overlays/IslandWindow.qml','''        transform: [
            Scale {''','''        transform: [
            Scale {
                origin.x:stage.head+surface.width/2
                origin.y:stage.height/2
                xScale:idleVisibility.progress
                yScale:0.85+0.15*idleVisibility.progress
            },
            Scale {''')
edit('rosa/overlays/IslandWindow.qml','''                    scale: win.wide || win.seeking ? 0.92 : 1
                    visible: opacity > 0.01''','''                    scale: win.wide || win.seeking ? 0.92 : 1
                    visible: opacity > 0.01 && !win.suppressIdleClock''')

# Flying arrivals are emitted before the hub's main activity changes. They must
# be allowed to start while auto-hidden, so their active flag can wake the layer.
p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
before='if (!win.lead || !win.visible || !win.atTop || win.blocked)'
after='if (!win.lead || (!win.visible && !IslandConfig.s("idleAutoHide")) || !win.atTop || win.blocked)'
if s.count(before)!=2:raise ValueError('Island arrival visibility guards changed')
p.write_text(s.replace(before,after))

# Missing focused-monitor metadata is transient during workspace/lock updates.
# Keep a valid output rather than hiding every island window in that gap.
p=root/'rosa/services/Focus.qml';s=p.read_text().replace('if (!m)\n            return null;', 'if (!m)\n            return Quickshell.screens[0] || null;');s=s.replace('        return null;','        return Quickshell.screens[0] || null;');p.write_text(s)
p=root/'rosa/services/IslandConfig.qml';s=p.read_text().replace('hideFull:    { type: "bool", def: false }','hideFull:    { type: "bool", def: true }');p.write_text(s)

p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text()
anchor='    readonly property bool blocked: {'
s=s.replace(anchor,'''    property var fallbackMonitors:[]
    Process {
        id:monitorFallback
        command:["hyprctl","-j","--batch","monitors;clients"]
        stdout:StdioCollector{onStreamFinished:{try{const sections=JSON.parse("["+text.trim().replace(/]\\s*\\[/,"] , [")+"]");const monitors=sections[0],clients=sections[1];win.fallbackMonitors=monitors.map(m=>({name:m.name,fullscreen:clients.some(c=>c.monitor===m.id && c.fullscreen===2 && (c.workspace.id===m.activeWorkspace.id || c.workspace.id===m.specialWorkspace.id))}))}catch(e){}}}
    }
    Timer {
        interval:1000;running:IslandConfig.s("hideFull") && !IslandBus.locked
        repeat:true;triggeredOnStart:true
        onTriggered:if(!monitorFallback.running)monitorFallback.running=true
    }
'''+anchor)
s=s.replace("""        const mon = Hyprland.monitorFor(win.modelData);
        const ws = mon ? mon.activeWorkspace : null;""","""        const mon = Hyprland.monitorFor(win.modelData);
        if(!mon){
            const fallback=win.fallbackMonitors.find(m=>m.name===win.modelData.name)
            return !!(fallback && fallback.fullscreen)
        }
        const ws = mon ? mon.activeWorkspace : null;""")
p.write_text(s)
