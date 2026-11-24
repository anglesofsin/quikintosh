pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import qs.services
import qs.components.glass
Singleton {
    id:root
    readonly property string wallpaperPath:GlassWallpaper.stillPath
    readonly property string colorMode:ShellConfig.options.topbar.foregroundMode
    readonly property string screenSpec:JSON.stringify(Quickshell.screens.map(s=>({name:s.name,width:s.width,height:s.height})))
    property var samples:({})
    property bool pending:false
    function colorFor(screen,side) {
        const mode=root.colorMode
        if(mode==='custom')return ShellConfig.options.topbar.foregroundColor
        if(mode==='dark')return '#17171a'
        if(mode==='light')return '#fafafa'
        const name=screen ? screen.name : (Quickshell.screens.length ? Quickshell.screens[0].name : '')
        const sample=root.samples[name]
        return sample ? sample[side || 'right'] : Theme.isLight ? '#17171a' : '#fafafa'
    }
    function logoColor(screen) {return ShellConfig.options.topbar.logoColorMode==='custom' ? ShellConfig.options.topbar.logoColor : root.colorFor(screen,'left')}
    function refresh() {if(root.colorMode!=='auto' || !root.wallpaperPath)return; if(probe.running)root.pending=true;else probe.running=true}
    onWallpaperPathChanged:debounce.restart()
    onScreenSpecChanged:debounce.restart()
    onColorModeChanged:debounce.restart()
    Component.onCompleted:debounce.restart()
    Timer { id:debounce;interval:180;onTriggered:root.refresh() }
    Process {
        id:probe
        command:['python3',Quickshell.shellDir+'/tools/bar-sample.py',root.wallpaperPath,root.screenSpec]
        stdout:StdioCollector { onStreamFinished:{try {const result=JSON.parse(text);if(result.path===root.wallpaperPath && Object.keys(result.screens).length)root.samples=result.screens} catch(_){} } }
        onExited:if(root.pending){root.pending=false;debounce.restart()}
    }
}
