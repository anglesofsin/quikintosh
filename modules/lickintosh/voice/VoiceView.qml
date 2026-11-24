import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import qs.rosa.services
Item {
    id: view
    property bool expanded: false
    property bool bubble: false
    property var person: VoiceCalls.speaker
    readonly property int avatarSize:IslandConfig.s("voiceAvatarSize")
    implicitWidth: expanded ? 500 : bubble ? 24 : 106
    implicitHeight: expanded ? 68 : 24
    property real wantH: implicitHeight
    TapHandler{enabled:view.expanded && VoiceCalls.incoming;onTapped:VoiceCalls.dismissIncoming()}
    VoiceAvatar {
        visible:!view.expanded
        width:view.bubble ? parent.width-4 : 20; height:width
        anchors.left:parent.left; anchors.leftMargin:view.bubble ? 2 : 0; anchors.verticalCenter:parent.verticalCenter
        name:view.person ? view.person.name : VoiceCalls.title
        image:view.person ? view.person.avatar : VoiceCalls.image
        speaking:!!view.person && view.person.speaking && !view.person.muted; indicator:false
    }
    Text {
        visible:!view.expanded && !view.bubble && IslandConfig.s("voiceClock")
        anchors.centerIn:parent; text:Qt.formatDateTime(clock.date,"HH:mm"); color:"white"; font.bold:true; font.pixelSize:12
    }
    Text { visible:!view.expanded && !view.bubble; anchors.right:parent.right; anchors.rightMargin:4; anchors.verticalCenter:parent.verticalCenter; text:VoiceCalls.selfDeaf ? "󰟎" : VoiceCalls.selfMuted ? "󰍭" : "󰏲"; color:VoiceCalls.selfDeaf || VoiceCalls.selfMuted ? "#ed4245" : "#23a55a"; font.pixelSize:16 }
    SystemClock { id:clock; precision:SystemClock.Minutes }
    ColumnLayout {
        visible:view.expanded; anchors.fill:parent; spacing:10
        RowLayout {
            Layout.fillWidth:true; Layout.fillHeight:true; spacing:12
            VoiceAvatar {
                Layout.preferredWidth:view.avatarSize+8; Layout.preferredHeight:view.avatarSize+8
                image:VoiceCalls.image; name:VoiceCalls.title; indicator:false; speaking:VoiceCalls.speakingCount>0
            }
            ColumnLayout {
                Layout.fillWidth:true; spacing:4
                Text { Layout.fillWidth:true; text:VoiceCalls.title; textFormat:Text.PlainText; elide:Text.ElideRight; color:"white"; font.pixelSize:17; font.bold:true }
                Text { Layout.fillWidth:true; text:(IslandConfig.s("voiceGuild") && VoiceCalls.call && VoiceCalls.call.guild ? VoiceCalls.call.guild+" · " : "")+(VoiceCalls.incoming ? "Incoming call":"In call")+(!VoiceCalls.incoming && IslandConfig.s("voiceDuration") ? " · "+VoiceCalls.duration : ""); textFormat:Text.PlainText; elide:Text.ElideRight; color:"#b9bcc9"; font.pixelSize:12 }
            }
            Repeater {
                model:IslandConfig.s("voiceControls") && VoiceCalls.active && (VoiceCalls.incoming ? VoiceCalls.incomingControls:VoiceCalls.controlsAvailable) ? (VoiceCalls.incoming ? ["reject","accept"]:["mute","deaf","disconnect"]) : []
                delegate: ToolButton {
                    required property string modelData
                    enabled:VoiceCalls.incoming ? VoiceCalls.incomingControls:VoiceCalls.controlsAvailable
                    readonly property bool selected:modelData==="mute" ? VoiceCalls.selfMuted : modelData==="deaf" ? VoiceCalls.selfDeaf : true
                    Layout.preferredWidth:40; Layout.preferredHeight:40
                    text:modelData==="accept" ? "󰏲" : modelData==="reject" ? "󰏲" : modelData==="mute" ? (selected ? "󰍭" : "󰍬") : modelData==="deaf" ? (selected ? "󰟎" : "󰋋") : "󰏲"
                    font.pixelSize:21
                    contentItem:Item {
                        Image {
                            anchors.centerIn:parent;width:20;height:20
                            source:Quickshell.shellDir+'/assets/icons/notch/'+(parent.parent.modelData==='mute' ? (parent.parent.selected ? 'mic-off.svg':'mic.svg') : parent.parent.modelData==='deaf' ? 'headphones.svg':'call-handset.svg')
                            sourceSize:Qt.size(40,40);fillMode:Image.PreserveAspectFit;smooth:true
                            rotation:['disconnect','reject'].includes(parent.parent.modelData) ? 135:0
                        }
                        Rectangle {
                            anchors.centerIn:parent;width:24;height:2;radius:1;rotation:45;color:'white'
                            visible:parent.parent.modelData==='deaf' && parent.parent.selected
                        }
                    }
                    background:Rectangle { radius:width/2; color:parent.modelData==="accept" ? "#23a55a" : ["reject","disconnect"].includes(parent.modelData) ? "#ed4245" : parent.selected ? "#5865f2" : "#393b46"; opacity:parent.hovered ? 1 : 0.9 }
                    Accessible.name:modelData==="accept" ? "Answer call" : modelData==="reject" ? "Decline call" : modelData==="mute" ? "Toggle microphone" : modelData==="deaf" ? "Toggle deafen" : "Leave call"
                    onClicked:VoiceCalls.control(modelData)
                }
            }
        }
    }
}
