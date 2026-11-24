import QtQuick
import QtQuick.Effects
import qs.rosa.services
Item {
    id: root
    property string image: ""
    property string name: ""
    property bool speaking: false
    property bool indicator: false
    Rectangle {
        anchors.fill:parent; radius:width/2; color:"#5865f2"
        Text { anchors.centerIn:parent; text:root.name.slice(0,1).toUpperCase(); color:"white"; font.pixelSize:parent.width*0.46; textFormat:Text.PlainText }
        Image {
            anchors.fill:parent; source:IslandConfig.s("voiceAvatars") ? root.image : ""
            sourceSize.width:80; sourceSize.height:80; asynchronous:true; cache:true
            layer.enabled:source!==""; layer.effect:MultiEffect { maskEnabled:true; maskSource:mask }
        }
        Rectangle { id:mask; anchors.fill:parent; radius:width/2; visible:false; layer.enabled:true }
    }
    Rectangle {
        id:ring
        anchors.fill:parent; anchors.margins:-2; radius:width/2; color:"transparent"
        SequentialAnimation on opacity {
            running:root.speaking && root.visible && IslandConfig.s("voicePulse")
            loops:Animation.Infinite
            NumberAnimation { to:0.55; duration:650 }
            NumberAnimation { to:1; duration:650 }
            onRunningChanged:if(!running) ring.opacity=1
        }
        border.width:root.speaking && IslandConfig.s("voiceAura") ? 2 : 0; border.color:"#23a55a"
    }
    Rectangle {
        visible:root.indicator; width:Math.max(6,root.width*0.24); height:width; radius:width/2
        anchors.right:parent.right; anchors.bottom:parent.bottom
        color:root.speaking ? "#23a55a" : "#747f8d"; border.width:1; border.color:"#14151c"
    }
}
