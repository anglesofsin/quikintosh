import Quickshell
import Quickshell.Widgets
import QtQuick
import "../../design"
import qs.rosa.services

Item {
    id: root
    property color tint: Colors.accent
    property string path: ""
    readonly property Item hero: thumb
    readonly property real wantH: 72
    readonly property string url: path ? "file://" + path : ""
    readonly property string folder: path.slice(0, path.lastIndexOf("/"))
    signal dismissed()
    ClippingRectangle {
        id: thumb
        anchors.left: parent.left; anchors.verticalCenter: parent.verticalCenter
        width: 112; height: 68; radius: 12
        color: "#20202a"; border.width: 1; border.color: "#50ffffff"
        Image {
            anchors.fill: parent; source: root.url
            sourceSize: Qt.size(224, 136); fillMode: Image.PreserveAspectCrop
            asynchronous: true; cache: true; smooth: true; mipmap: true
        }
        MouseArea {
            anchors.fill: parent; cursorShape: Qt.PointingHandCursor
            onClicked: { Quickshell.execDetached(["xdg-open", root.path]); root.dismissed() }
        }
    }
    Column {
        anchors.left: thumb.right; anchors.leftMargin: 18
        anchors.right: folderButton.left; anchors.rightMargin: 18
        anchors.verticalCenter: parent.verticalCenter; spacing: 6
        Text {
            width: parent.width; text: I18n.t("isle.shot.title")
            font.family: Fonts.display; font.pixelSize: 18; font.weight: Font.DemiBold
            color: Colors.fg; elide: Text.ElideRight
        }
        Text {
            width: parent.width
            text: root.folder.endsWith("/Desktop") ? I18n.t("isle.shot.desktop") : I18n.t("isle.shot.saved")
            font.family: Fonts.display; font.pixelSize: 12; color: Colors.alpha(Colors.fg, .7)
            elide: Text.ElideRight
        }
    }
    Rectangle {
        id: folderButton
        anchors.right: parent.right; anchors.verticalCenter: parent.verticalCenter
        width: 46; height: 46; radius: 23
        color: folderMouse.containsMouse ? "#48ffffff" : "#22ffffff"
        Text { anchors.centerIn: parent; text: "󰉋"; font.family: Fonts.glyph; font.pixelSize: 23; color: Colors.fg }
        MouseArea {
            id: folderMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
            onClicked: {
                Quickshell.execDetached(["lickintosh-finder", root.folder])
                root.dismissed()
            }
        }
        Accessible.name: "Show screenshot in folder"
    }
}
