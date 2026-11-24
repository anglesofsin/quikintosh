import QtQuick

CaptureGlass {
    id: root
    signal selected(string action)
    width: 288
    height: groupsColumn.implicitHeight + 24
    radius: 18
    MouseArea { anchors.fill: parent }
    Column {
        id: groupsColumn
        anchors { left: parent.left; right: parent.right; top: parent.top; margins: 12 }
        spacing: 10
        Repeater {
            model: [
                {title: "EXTRACT", items: [{label: "Copy text with OCR", action: "ocr"}, {label: "Read QR / barcode", action: "qr"}, {label: "Create color palette", action: "palette"}, {label: "Search with Google Lens…", action: "lens"}]},
                {title: "ANNOTATE", items: [{label: "Highlighter", action: "highlight"}, {label: "Blur sensitive content", action: "blur"}]},
                {title: "TOOLS", items: [{label: "Pick a color", action: "color"}, {label: "Measure pixels", action: "measure"}]},
                {title: "RECORD", items: [{label: "Record selection as video", action: "record"}, {label: "Record selection as GIF", action: "gif"}, {label: "Camera mirror", action: "camera"}]}
            ]
            Column {
                required property var modelData
                width: groupsColumn.width
                spacing: 3
                Text { x: 10; text: parent.modelData.title; color: "#abb2c2"; font.pixelSize: 10; font.weight: Font.DemiBold; font.letterSpacing: 1 }
                Repeater {
                    model: parent.modelData.items
                    Rectangle {
                        required property var modelData
                        width: groupsColumn.width; height: 31; radius: 9
                        color: entryMouse.containsMouse ? "#32ffffff" : "transparent"
                        Text { x: 10; anchors.verticalCenter: parent.verticalCenter; text: parent.modelData.label; color: "white"; font.pixelSize: 13 }
                        MouseArea { id: entryMouse; anchors.fill: parent; hoverEnabled: true; cursorShape: Qt.PointingHandCursor; onClicked: root.selected(parent.modelData.action) }
                    }
                }
            }
        }
    }
}
