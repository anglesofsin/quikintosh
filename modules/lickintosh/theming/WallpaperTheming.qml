import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Scope {
 id:root
 property bool enabled:false
 readonly property string wallpaper:ShellConfig.options.wallpaper.path
 readonly property string mode:Theme.isLight ? 'light' : 'dark'
 readonly property bool wallpaperGtk:ShellConfig.options.appearance.wallpaperGtk
 readonly property bool wallpaperFileIcons:ShellConfig.options.appearance.wallpaperFileIcons || WidgetState.widgetStyle==='tinted'
 onWallpaperGtkChanged:delay.restart()
 onWallpaperFileIconsChanged:delay.restart()
 // Palette output can also change through other Matugen integrations. Follow
 // the published palette, not just the wallpaper setting that initiated it.
 property bool profilePending:false
 FileView{path:Quickshell.env('HOME')+'/.local/state/lickintosh/theming/palette.json';watchChanges:true;onFileChanged:profileDelay.restart();onLoaded:profileDelay.restart()}
 Timer{id:profileDelay;interval:140;onTriggered:{if(!root.enabled)return;if(profile.running){root.profilePending=true;return}profile.command=['lickintosh-desktop-profile','mode',root.mode];profile.running=true}}
 Process{id:profile;onExited:{if(root.profilePending){root.profilePending=false;profileDelay.restart()}}}
 property bool pending:false
 onWallpaperChanged:delay.restart()
 onModeChanged:delay.restart()
 onEnabledChanged:if(enabled)delay.restart()
 Component.onCompleted:if(enabled)delay.restart()
 Timer {id:delay;interval:350;onTriggered:{if(!root.enabled || !root.wallpaper)return;if(worker.running){root.pending=true;return}worker.command=['@PYTHON@',Quickshell.shellDir+'/theming/apply.py','@LEGACY@',root.wallpaper,root.mode];worker.running=true}}
 Process {id:worker;onExited:(code,status)=>{if(code)console.warn('Wallpaper application themes failed: see ~/.local/state/lickintosh/theming/apply.log');if(root.pending){root.pending=false;delay.restart()}}}
}
