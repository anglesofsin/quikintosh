import QtQuick
import "DockOcclusion.js" as Occlusion

QtObject {
    property var clients: []
    property var monitors: []
    property string monitorName: ""
    property rect dockRect: Qt.rect(0,0,0,0)
    property real shellScale: 1
    readonly property bool blocked: Occlusion.blocked(clients,monitors,monitorName,dockRect,shellScale)
}
