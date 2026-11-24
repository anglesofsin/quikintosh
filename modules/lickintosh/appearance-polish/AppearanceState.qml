pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
Singleton {
 id:root
 readonly property var options:ShellConfig.options.appearance
 property var palette:({})
 readonly property color wallpaperAccent:palette[Theme.isLight ? 'light':'dark']?.primary || '#0a84ff'
 readonly property color iconColor:options.iconTintMode==='auto' ? wallpaperAccent:options.iconTintColor
 readonly property bool tinted:options.iconStyle==='tinted'
 function syncAccent(){if(options.accentMode==='auto' && String(Theme.accent)!==String(wallpaperAccent))Theme.setAccent(String(wallpaperAccent))}
 Connections{target:root.options;function onAccentModeChanged(){root.syncAccent()}}
 onWallpaperAccentChanged:syncAccent()
 FileView{path:Quickshell.env('HOME')+'/.local/state/lickintosh/theming/palette.json';watchChanges:true;onFileChanged:reload();onLoaded:{try{root.palette=JSON.parse(text());root.syncAccent()}catch(error){}}}
}
