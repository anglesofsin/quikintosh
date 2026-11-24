import QtQuick
import qs.components.glass

// Every surface samples the same frozen capture and shared blur texture.
Rectangle {
    id: root
    property Item backdrop: null
    radius: 16
    color: "transparent"
    border.width: 1
    border.color: "#50ffffff"
    TahoeGlass {
        anchors.fill: parent
        z: -1
        backdrop: root.backdrop
        cornerRadius: root.radius
        autoDarken: true
    }
    Rectangle {
        anchors.fill: parent
        z: -1
        radius: root.radius
        color: "#280b101a"
        border.width: 1
        border.color: "#18ffffff"
    }
}
