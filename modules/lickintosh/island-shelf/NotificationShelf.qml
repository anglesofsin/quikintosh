import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell
import qs.services
import qs.ui.topbar.statusarea.notifcenter
Item {
 id:root;property var notices:[]
 function plain(text){return String(text || '').replace(/<br\s*\/?\s*>/gi,'\n').replace(/<[^>]*>/g,'')}
 ColumnLayout{anchors.fill:parent;spacing:12
  RowLayout{Layout.fillWidth:true
   ShelfIcon{size:18;icon:'notch/bell.svg'}
   Text{Layout.fillWidth:true;text:qsTr('Notifications');font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold;color:'white'}
   ShelfButton{flat:true;icon:NotifService.dndEnabled ? 'notch/moon.svg':'notch/bell.svg';selected:NotifService.dndEnabled;accessibleLabel:qsTr('Do Not Disturb');onClicked:NotifService.dndEnabled=!NotifService.dndEnabled}
  }
  ListView{id:list;Layout.fillWidth:true;Layout.fillHeight:true;spacing:12;clip:true;model:root.notices;boundsBehavior:Flickable.StopAtBounds
   delegate:Rectangle {
    id:card;required property var modelData
    property string sent:''
    property bool replyHeld:false
    readonly property bool canReply:!!modelData?.hasInlineReply
    width:list.width;height:content.implicitHeight+28;radius:22;color:root.notices.length===1 ? 'transparent':ShelfStyle.surface
    function send(){const text=field.text.trim();if(!canReply || !text)return;modelData.sendInlineReply(text);sent=text;field.text=''}
    Component.onDestruction:if(replyHeld)ShelfState.interaction(false)
    ColumnLayout{id:content;anchors.left:parent.left;anchors.right:parent.right;anchors.top:parent.top;anchors.margins:14;spacing:10
     RowLayout{Layout.fillWidth:true;spacing:12
      Item{Layout.preferredWidth:44;Layout.preferredHeight:44
       Rectangle{anchors.fill:parent;radius:22;color:'#636366';Text{anchors.centerIn:parent;text:String(card.modelData.summary || card.modelData.appName || 'N').slice(0,2).toUpperCase();font.family:ShelfStyle.textFamily;font.pixelSize:17;color:'white'}}
       NotifIcon{anchors.fill:parent;icon:card.modelData.appIcon || '';appName:card.modelData.appName || '';size:44;visible:!!resolvedSource}
      }
      ColumnLayout{Layout.fillWidth:true;spacing:3
       Text{Layout.fillWidth:true;text:card.modelData.summary || card.modelData.appName || qsTr('Notification');color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:16;font.weight:Font.DemiBold;elide:Text.ElideRight;textFormat:Text.PlainText}
       Text{visible:!!card.sent;Layout.fillWidth:true;text:qsTr('You: %1').arg(card.sent);color:'#0a84ff';font.family:ShelfStyle.textFamily;font.pixelSize:13;wrapMode:Text.WordWrap;textFormat:Text.PlainText}
      }
      Text{text:qsTr('now');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
      ShelfButton{flat:true;implicitWidth:24;implicitHeight:24;icon:'notch/x.svg';accessibleLabel:qsTr('Dismiss');onClicked:NotifService.removeFromCenter(card.modelData)}
     }
     Image{visible:!card.sent && !!card.modelData.image;Layout.leftMargin:56;Layout.fillWidth:true;Layout.preferredHeight:visible ? 145:0;source:card.modelData.image || '';fillMode:Image.PreserveAspectFit;sourceSize:Qt.size(600,300);asynchronous:true}
     Text{Layout.leftMargin:56;Layout.fillWidth:true;visible:!card.sent && !!text;text:root.plain(card.modelData.body);font.family:ShelfStyle.textFamily;font.pixelSize:14;color:'#d1d1d6';wrapMode:Text.WordWrap;maximumLineCount:5;elide:Text.ElideRight;textFormat:Text.PlainText}
     RowLayout{visible:card.canReply && !card.sent;Layout.leftMargin:56;Layout.fillWidth:true;spacing:8
      TextField{id:field;objectName:'notification-reply';Layout.fillWidth:true;implicitHeight:38;leftPadding:14;rightPadding:14;placeholderText:card.modelData.inlineReplyPlaceholder || qsTr('Reply');placeholderTextColor:ShelfStyle.secondary;color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:14;selectByMouse:true
       background:Rectangle{radius:19;color:'#24ffffff';border.width:field.activeFocus ? 1:0;border.color:'#0a84ff'}
       onActiveFocusChanged:{if(card.replyHeld!==activeFocus){card.replyHeld=activeFocus;ShelfState.interaction(activeFocus)}}
       onAccepted:card.send()
      }
      ShelfButton{implicitWidth:38;implicitHeight:38;icon:'notch/send.svg';iconSize:21;selected:true;accessibleLabel:qsTr('Send reply');enabled:field.text.trim().length>0;onClicked:card.send()}
     }
     Flow{visible:!card.sent;Layout.leftMargin:56;Layout.fillWidth:true;spacing:6
      Repeater{model:Array.from(card.modelData.actions || []).filter(a=>a.identifier!=='inline-reply' && a.identifier!=='default')
       delegate:ShelfButton{required property var modelData;text:modelData.text || qsTr('Open');onClicked:modelData.invoke()}
      }
     }
    }
   }
   Text{anchors.centerIn:parent;visible:list.count===0;text:qsTr('No notifications');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:14}
  }
 }
}
