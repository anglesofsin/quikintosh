from pathlib import Path
import sys
root=Path(sys.argv[1]);here=Path(__file__).parent
for p in root.rglob('*'):
 if not p.is_symlink():p.chmod(p.stat().st_mode|0o200)
for name in ['ScreenEdges','CornerTrigger','HotCorners','CornerSettings','HotCornersSettings','QuickNote','MenuBarBackground']:
 (root/'components'/f'{name}.qml').write_text((here/f'{name}.qml').read_text())
 p=root/'components/qmldir';p.write_text(p.read_text()+f'\n{name} {name}.qml\n')
p=root/'services/ShellConfig.qml';s=p.read_text();anchor='            property JsonObject lockscreen: JsonObject {';assert s.count(anchor)==1
s=s.replace(anchor,'''            property JsonObject edges:JsonObject{
                property bool roundedCorners:false
                property int cornerRadius:18
                property bool hideCornersFullscreen:true
                property bool roundMenuBackground:false
                property int menuCornerRadius:12
                property bool hotCorners:false
                property bool hideHotCornersFullscreen:true
                property int hotCornerDelay:200
                property string topLeftAction:"none"
                property string topRightAction:"none"
                property string bottomLeftAction:"none"
                property string bottomRightAction:"none"
                property int topLeftModifiers:0
                property int topRightModifiers:0
                property int bottomLeftModifiers:0
                property int bottomRightModifiers:0
            }
'''+anchor);p.write_text(s)
# Export a normal Qt property with an explicit change event. The alias to the
# session-lock object was observed false over IPC while consumers remained true.
p=root/'ui/lockscreen/LockScreen.qml';s=p.read_text();old='    readonly property alias locked: lock.locked';assert old in s;s=s.replace(old,'''    property bool _sessionLocked:false
    readonly property bool locked:_sessionLocked''');s=s.replace('        onLockedChanged: {\n            if (locked)', '        onLockedChanged: {\n            root._sessionLocked=lock.locked\n            if (locked)');p.write_text(s)
# Preserve state and the window graph over lock/unlock; visibility still follows
# IslandBus.locked, so no island surface is displayed while the session is locked.
p=root/'RosaIntegration.qml';s=p.read_text().replace('active: root.enabled && !root.locked && RosaServices.IslandConfig.s("enabled")','active: root.enabled && RosaServices.IslandConfig.s("enabled")');p.write_text(s)
p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text();anchor='    readonly property bool wanted:';assert anchor in s;s=s.replace(anchor,'''    Connections{
        target:IslandBus
        function onLockedChanged(){
            win.pointerIn=false;win.hovering=false;win.forced=false
            if(!IslandBus.locked){idleVisibility.reset();birth.land()}
        }
    }
'''+anchor);p.write_text(s)
p=root/'components/AppearanceControls.qml'
# AppearanceControls lives beside the legacy page, after the appearance merge.
if not p.exists():p=root/'ui/settings/pages/AppearanceControls.qml'
s=p.read_text();s=s[:s.rfind('}')]+ '\n CornerSettings{}\n'+s[s.rfind('}'):];p.write_text(s)
p=root/'ui/settings/pages/DockPage.qml';s=p.read_text();s=s[:s.rfind('}')]+ '\n    HotCornersSettings{}\n'+s[s.rfind('}'):];p.write_text(s)
p=root/'ui/settings/pages/TopBarPage.qml';s=p.read_text();a=s.index('    ContentSection{title:"Menu bar background"');z=s.index('\n    }',a);s=s[:z]+'''
        ConfigSwitch{visible:ShellConfig.options.topbar.backgroundEnabled;text:"Round background corners";checked:ShellConfig.options.edges.roundMenuBackground;onToggled:value=>ShellConfig.options.edges.roundMenuBackground=value}
        ConfigSlider{visible:ShellConfig.options.topbar.backgroundEnabled && ShellConfig.options.edges.roundMenuBackground;text:"Corner radius";from:0;to:24;decimals:0;value:ShellConfig.options.edges.menuCornerRadius;onMoved:value=>ShellConfig.options.edges.menuCornerRadius=Math.round(value)}
'''+s[z:];p.write_text(s)
p=root/'services/ShellConfig.qml';s=p.read_text();s=s.replace('property bool backgroundEnabled:false','property bool backgroundEnabled:false\n                property bool blurEnabled:false');p.write_text(s)
p=root/'ui/settings/pages/TopBarPage.qml';s=p.read_text();a=s.index('    ContentSection{title:"Menu bar background"');z=s.index('\n    }',a)
s=s[:z]+"""
        ConfigSwitch{text:"Blur background";checked:ShellConfig.options.topbar.blurEnabled;onToggled:value=>{ShellConfig.options.topbar.blurEnabled=value;SettingsPreferences.input('native-glass:menubar:enabled',value);if(value && SettingsPreferences.inputOverrides['native-glass:menubar:preset']===undefined)SettingsPreferences.input('native-glass:menubar:preset','subtle')}}
        ConfigSlider{visible:ShellConfig.options.topbar.blurEnabled;text:"Blur strength";from:0;to:8;value:SettingsPreferences.inputOverrides['native-glass:menubar:blur_strength'] ?? 1;onMoved:value=>SettingsPreferences.input('native-glass:menubar:blur_strength',value)}
        ConfigSwitch{visible:ShellConfig.options.topbar.blurEnabled;text:"Liquid Glass refraction";checked:(SettingsPreferences.inputOverrides['native-glass:menubar:refraction_strength'] ?? 0)>0;onToggled:value=>SettingsPreferences.input('native-glass:menubar:refraction_strength',value ? 2:0)}
"""+s[z:]
s=s.replace('text:"Round background corners"','text:"Round outside corners"').replace('visible:ShellConfig.options.topbar.backgroundEnabled && ShellConfig.options.edges.roundMenuBackground','visible:(ShellConfig.options.topbar.backgroundEnabled || ShellConfig.options.topbar.blurEnabled) && ShellConfig.options.edges.roundMenuBackground').replace('visible:ShellConfig.options.topbar.backgroundEnabled;text:"Round outside corners"','visible:ShellConfig.options.topbar.backgroundEnabled || ShellConfig.options.topbar.blurEnabled;text:"Round outside corners"').replace('text:"Opacity";from:0.1','text:"Opacity";from:0')
p.write_text(s)
p=root/'shell.qml';s=p.read_text();s='import qs.components\n'+s
before="""            Rectangle {
                anchors.fill:_topBarItem
                visible:ShellConfig.options.topbar.backgroundEnabled
                color:ShellConfig.options.topbar.backgroundColor
                opacity:ShellConfig.options.topbar.backgroundOpacity
            }"""
assert s.count(before)==1
s=s.replace(before,"""            MenuBarBackground {
                anchors.fill:_topBarItem
                fullscreen:PrivacyPresentation.fullscreen(topBarWindow.screen.name)
            }""",1)
a=s.index('    RosaIntegration {');s=s[:a]+'''    ScreenEdges{enabled:appRoot.interfaceShown && !lockScreen.locked}
    QuickNote{id:quickNote}
    HotCorners{
        enabled:appRoot.interfaceShown && !lockScreen.locked
        onActionRequested:action=>{
            if(lockScreen.locked)return
            if(action==="controlCenter")appRoot.ccOpened=true
            else if(action==="notifications")appRoot.notifCenterOpened=true
            else if(action==="launchpad")LauncherState.openApplications()
            else if(action==="spotlight"){LauncherState.pendingAction="spotlight";LauncherState.requested()}
            else if(action==="clipboard"){LauncherState.pendingAction="clipboard";LauncherState.requested()}
            else if(action==="widgets")WidgetState.galleryZone="desktop"
            else if(action==="quickNote")quickNote.open()
            else if(action==="focus")NotifService.dndEnabled=!NotifService.dndEnabled
            else if(action==="lock")lockScreen.lock()
            else if(action==="sleep")Quickshell.execDetached(["hyprctl","dispatch","dpms","off"])
        }
    }
'''+s[a:];p.write_text(s)
