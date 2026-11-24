import QtQuick
import QtQuick.Layouts
import QtQuick.Controls

CaptureGlass {
    id: root
    property string title: ""
    property string result: ""
    property var colors: []
    property int copiedIndex: -1
    property bool copiedAll: false
    readonly property bool isPalette: title === "Color palette"
    signal copyRequested(string value)
    signal dismissed()
    width: isPalette ? 488 : 440
    height: content.implicitHeight + 40
    radius: 22
    onResultChanged: { copiedIndex = -1; copiedAll = false }
    MouseArea { anchors.fill: parent }
    ColumnLayout {
        id: content
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 20 }
        spacing: 16
        Item {
            Layout.fillWidth: true; Layout.preferredHeight: 48
            Text { anchors.left: parent.left; anchors.top: parent.top; text: root.title; color: "white"; font.pixelSize: 20; font.weight: Font.DemiBold }
            Text {
                anchors.left: parent.left; anchors.bottom: parent.bottom; width: parent.width - 42
                text: root.isPalette ? "Click a color to copy its HEX value" : "Select the text or copy the result below"
                color: "#c7cbd5"; font.pixelSize: 12; elide: Text.ElideRight
            }
            Rectangle {
                anchors.right: parent.right; anchors.top: parent.top
                width: 30; height: 30; radius: 15
                color: closeHover.containsMouse ? "#40ffffff" : "#18ffffff"
                Text { anchors.centerIn: parent; text: "×"; color: "white"; font.pixelSize: 20 }
                MouseArea { id: closeHover; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.dismissed() }
            }
        }
        GridLayout {
            visible: root.isPalette
            Layout.fillWidth: true
            columns: 4; rowSpacing: 10; columnSpacing: 10
            Repeater {
                model: root.isPalette ? root.colors : []
                Rectangle {
                    required property string modelData
                    required property int index
                    Layout.fillWidth: true; Layout.preferredHeight: 96
                    radius: 12; color: swatchMouse.containsMouse ? "#30ffffff" : "#14000000"
                    border.width: root.copiedIndex === index ? 2 : 1
                    border.color: root.copiedIndex === index ? "#ff9a70" : "#24ffffff"
                    Rectangle { x: 7; y: 7; width: parent.width - 14; height: 56; radius: 8; color: parent.modelData }
                    Text {
                        anchors { horizontalCenter: parent.horizontalCenter; bottom: parent.bottom; bottomMargin: 12 }
                        text: root.copiedIndex === parent.index ? "Copied ✓" : parent.modelData
                        color: "white"; font.family: "monospace"; font.pixelSize: 12
                    }
                    MouseArea {
                        id: swatchMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor
                        onClicked: { root.copyRequested(parent.modelData); root.copiedIndex = parent.index }
                    }
                }
            }
        }
        ScrollView {
            visible: !root.isPalette
            Layout.fillWidth: true; Layout.preferredHeight: Math.min(180, textResult.implicitHeight + 12)
            TextArea {
                id: textResult; text: root.result; readOnly: true; selectByMouse: true
                color: "white"; font.pixelSize: 14; font.family: "monospace"
                textFormat: TextEdit.PlainText; wrapMode: TextEdit.Wrap
                background: Rectangle { color: "#22000000"; radius: 10 }
            }
        }
        Rectangle {
            Layout.fillWidth: true; Layout.preferredHeight: 40
            radius: 12; color: allMouse.containsMouse ? "#ff855a" : "#eeff6b35"
            Text {
                anchors.centerIn: parent
                text: root.copiedAll ? "Copied ✓" : root.isPalette ? "Copy entire palette" : "Copy result"
                color: "white"; font.pixelSize: 13; font.weight: Font.DemiBold
            }
            MouseArea { id: allMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: { root.copyRequested(root.result); root.copiedAll = true } }
        }
    }
}
