"""Convert compositor coordinates into Qt logical units for per-shell scaling."""
from pathlib import Path
import sys

root=Path(sys.argv[1])
p=root/'components/glass/LiquidGlassBackdrop.qml'
s=p.read_text().replace('readonly property real aa: GlassTracker.backdropScale', 'readonly property real aa: GlassTracker.backdropScale * Number(Quickshell.env("QT_SCALE_FACTOR") || 1)',1)
p.write_text(s)
p=root/'components/glass/GlassWindows.qml'
s=p.read_text().replace('    property string monitorName:', '''    readonly property real coordinateScale: 1 / Number(Quickshell.env("QT_SCALE_FACTOR") || 1)
    function normalizedIpc(client) {
        if (!client || coordinateScale === 1) return client
        const next = Object.assign({}, client)
        if (client.at) next.at = [root.monitorX+(client.at[0]-root.monitorX)*coordinateScale,
                                  root.monitorY+(client.at[1]-root.monitorY)*coordinateScale]
        if (client.size) next.size = [client.size[0]*coordinateScale,client.size[1]*coordinateScale]
        return next
    }
    property string monitorName:''',1)
s=s.replace('monitorObject.width / (monitorObject.scale || 1)', 'monitorObject.width / (monitorObject.scale || 1) * root.coordinateScale')
s=s.replace('monitorObject.height / (monitorObject.scale || 1)', 'monitorObject.height / (monitorObject.scale || 1) * root.coordinateScale')
s=s.replace('for(var c of clients) {', 'for(var entry of clients) {\n            var c=root.normalizedIpc(entry)')
s=s.replace('readonly property var ipc: modelData.lastIpcObject', 'readonly property var ipc: root.normalizedIpc(modelData.lastIpcObject)')
p.write_text(s)
p=root/'settingsapp/SettingsWindowGlass.qml'
s=p.read_text().replace('import QtQuick\n','import QtQuick\nimport Quickshell\n',1)
s=s.replace(' property bool precision:false', ' readonly property real coordinateScale:1/Number(Quickshell.env("QT_SCALE_FACTOR") || 1)\n property bool precision:false',1)
s=s.replace('Qt.point((own.at?.[0] || 0)-(monitor.x || 0),(own.at?.[1] || 0)-(monitor.y || 0))', 'Qt.point(((own.at?.[0] || 0)-(monitor.x || 0))*coordinateScale,((own.at?.[1] || 0)-(monitor.y || 0))*coordinateScale)')
p.write_text(s)
p=root/'services/QuickLookState.qml'
s=p.read_text().replace('  return {address:w.address,x:w.at[0]-m.x,y:w.at[1]-m.y,width:w.size ? w.size[0]:0,height:w.size ? w.size[1]:0,monitor:m.name}', '''  const factor=1/Number(Quickshell.env("QT_SCALE_FACTOR") || 1)
  return {address:w.address,x:(w.at[0]-m.x)*factor,y:(w.at[1]-m.y)*factor,width:w.size ? w.size[0]*factor:0,height:w.size ? w.size[1]*factor:0,monitor:m.name}''')
p.write_text(s)
p=root/'settings.qml'
s=p.read_text().replace('implicitWidth:1000;implicitHeight:740;minimumSize:Qt.size(820,560)', '''implicitWidth:Math.min(1000,(window.screen?.width || 1040)-40);implicitHeight:Math.min(740,(window.screen?.height || 780)-40);minimumSize:Qt.size(Math.max(320,Math.min(820,(window.screen?.width || 1040)-40)),Math.max(240,Math.min(560,(window.screen?.height || 780)-40)))''')
p.write_text(s)
p=root/'quicklook/QuickLookWindow.qml'
s=p.read_text().replace('implicitWidth:880;implicitHeight:650;', 'implicitWidth:Math.min(880,(window.screen?.width || 940)-60);implicitHeight:Math.min(650,(window.screen?.height || 710)-60);')
p.write_text(s)
