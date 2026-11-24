import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Scope {
 id:root
 property bool enabled:false
 readonly property string wallpaper:ShellConfig.options.wallpaper.path
 readonly property string mode:Theme.isLight ? 'light' : 'dark'
 property bool pending:false
 onWallpaperChanged:delay.restart()
 onModeChanged:delay.restart()
 onEnabledChanged:if(enabled)delay.restart()
 Component.onCompleted:if(enabled)delay.restart()
 Timer {id:delay;interval:350;onTriggered:{if(!root.enabled || !root.wallpaper)return;if(worker.running){root.pending=true;return}worker.command=['@PYTHON@',Quickshell.shellDir+'/theming/apply.py','@LEGACY@',root.wallpaper,root.mode];worker.running=true}}
 Process {id:worker;onExited:(code,status)=>{if(code)console.warn('Wallpaper application themes failed: see ~/.local/state/lickintosh/theming/apply.log');if(root.pending){root.pending=false;delay.restart()}}}
}
