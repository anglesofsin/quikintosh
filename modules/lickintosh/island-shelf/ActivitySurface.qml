import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import QtQuick.Shapes
Item {
 id:root
 required property var activity
 property string presentation:'compact'
 property bool reducedMotion:false
 property bool replying:false
 property bool interactive:true
 readonly property bool expanded:presentation==='expanded'
 readonly property bool satellite:presentation==='satellite'
 readonly property color accent:activity.color || '#f5f5f7'
 readonly property bool meter:activity.meter===true
 readonly property bool richNotification:expanded && notification && !!activity.image
 readonly property bool notification:activity.kind==='notif'
 readonly property int compactHeight:26
 readonly property string compactLabel:(activity.label || activity.title || '')===(activity.value || '') ? '':activity.label || activity.title || ''
 TextMetrics{id:labelMeasure;font.family:ShelfStyle.textFamily;font.pixelSize:['power','low'].includes(root.activity.kind) ? 11:12;font.weight:Font.DemiBold;text:root.compactLabel}
 TextMetrics{id:valueMeasure;font.family:ShelfStyle.textFamily;font.pixelSize:12;font.weight:Font.Medium;text:root.activity.value || ''}
 readonly property real preferredCompactWidth:meter ? 118:Math.max(118,Math.ceil(labelMeasure.width+valueMeasure.width+20+(['power','low'].includes(activity.kind) ? 16:16)+(compactLabel ? 12:6)+(activity.value ? 6:0)))
 implicitWidth:satellite ? 28:expanded ? 320:preferredCompactWidth
 implicitHeight:expanded ? notification ? 64+(richNotification ? 128:0)+(replying ? 42:0):64:compactHeight
 signal activate()
 signal action(string name,string value)
 Accessible.role:Accessible.Button
 Accessible.name:activity.title || activity.kind || ''
 Rectangle{anchors.fill:parent;radius:root.richNotification ? 32:height/2;color:'black'}
 Shape{visible:root.satellite && ['timer','download','cmd','task','print'].includes(root.activity.kind);anchors.fill:parent;preferredRendererType:Shape.CurveRenderer
  ShapePath{fillColor:'transparent';strokeColor:root.accent;strokeWidth:2;capStyle:ShapePath.RoundCap
   PathAngleArc{centerX:root.width/2;centerY:root.height/2;radiusX:root.width/2-3;radiusY:root.height/2-3;startAngle:-90;sweepAngle:Math.max(.06,Math.min(1,root.activity.fraction || 0))*360}
  }
 }
 RowLayout{
  anchors.fill:parent;anchors.leftMargin:root.satellite ? 5:root.expanded ? 16:10;anchors.rightMargin:root.satellite ? 5:root.expanded ? 16:10;anchors.topMargin:root.richNotification ? 16:0;anchors.bottomMargin:root.replying ? 42:0;spacing:root.expanded ? 12:6
  Item{
   visible:!root.meter && !['power','low'].includes(root.activity.kind) && !(root.expanded && root.activity.kind==='record')
   Layout.alignment:root.richNotification ? Qt.AlignTop:Qt.AlignVCenter;Layout.preferredWidth:root.expanded && root.notification ? 40:root.expanded ? root.activity.kind==='vpn' ? 32:28:16;Layout.preferredHeight:width
   Rectangle{visible:root.notification;anchors.fill:parent;radius:width/2;color:'#77777b'}
   Text{visible:root.notification;anchors.centerIn:parent;text:root.activity.initials || '';color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:root.expanded ? 17:8}
   Rectangle{visible:root.expanded && root.notification;x:parent.width-10;y:parent.height-8;width:12;height:12;radius:3;color:'#0a84ff';Image{visible:!!root.activity.appIcon;anchors.fill:parent;source:root.activity.appIcon || '';sourceSize:Qt.size(24,24);fillMode:Image.PreserveAspectFit}ShelfIcon{visible:!root.activity.appIcon;anchors.centerIn:parent;size:8;icon:'notch/mail.svg';color:'white'}}
   ShelfIcon{visible:!root.notification && root.activity.kind!=='record';anchors.centerIn:parent;size:root.expanded ? root.activity.kind==='vpn' ? 32:28:16;icon:'notch/'+(root.activity.icon || 'bell')+'.svg';color:root.activity.kind==='vpn' ? 'white':root.accent}
   Rectangle{visible:root.activity.kind==='record';anchors.centerIn:parent;width:root.expanded ? 12:6;height:width;radius:width/2;color:'#ff453a';anchors.verticalCenterOffset:root.expanded ? -9:0}
  }
  ShelfIcon{objectName:'activity-meter-icon';visible:root.meter;Layout.preferredWidth:16;Layout.preferredHeight:16;icon:'notch/'+(root.activity.icon || 'volume-2')+'.svg';color:root.accent;Layout.alignment:Qt.AlignVCenter}
  ColumnLayout{
   Layout.alignment:root.richNotification ? Qt.AlignTop:Qt.AlignVCenter
   visible:!root.satellite && !root.meter;Layout.fillWidth:true;spacing:root.expanded ? 3:0
   RowLayout{Layout.fillWidth:true;spacing:6
    Rectangle{objectName:'activity-record-dot';visible:root.expanded && root.activity.kind==='record';Layout.preferredWidth:12;Layout.preferredHeight:12;radius:6;color:'#ff453a';Layout.alignment:Qt.AlignVCenter}
    Text{visible:!root.meter && (root.expanded || root.compactLabel!=='') && !(root.activity.kind==='timer' && !root.expanded);Layout.fillWidth:!(root.expanded && ['power','low'].includes(root.activity.kind));text:root.expanded ? root.activity.title || '':root.compactLabel;textFormat:Text.PlainText;elide:Text.ElideRight;color:root.activity.kind==='record' ? root.accent:'white';font.family:ShelfStyle.textFamily;font.pixelSize:root.expanded ? root.notification ? 14:['vpn','net','bt'].includes(root.activity.kind) ? 11:12:['power','low'].includes(root.activity.kind) ? 11:12;font.weight:root.expanded && ['vpn','net','bt'].includes(root.activity.kind) ? Font.Normal:Font.DemiBold;font.features:({tnum:1})}
    Text{visible:root.expanded && ['power','low'].includes(root.activity.kind);Layout.fillWidth:true;text:root.activity.value || '';color:root.accent;font.family:ShelfStyle.textFamily;font.pixelSize:12;font.weight:Font.DemiBold}
    Text{visible:root.expanded && root.notification;text:root.activity.time || qsTr('now');color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:11}
   }
   Image{visible:root.richNotification;Layout.fillWidth:true;Layout.preferredHeight:128;source:visible ? root.activity.image || '':'';sourceSize:Qt.size(320,256);fillMode:Image.PreserveAspectFit;asynchronous:true}
   Text{objectName:'activity-subtitle';visible:root.expanded && !!root.activity.subtitle;Layout.fillWidth:true;text:root.activity.subtitle || '';textFormat:Text.PlainText;wrapMode:Text.Wrap;maximumLineCount:2;elide:Text.ElideRight;color:root.notification || ['record','vpn','net','bt'].includes(root.activity.kind) ? 'white':ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:root.notification ? 12:['record','vpn','net','bt'].includes(root.activity.kind) ? 12:10;font.weight:['record','vpn','net','bt'].includes(root.activity.kind) ? Font.DemiBold:Font.Normal}

  }

  Rectangle{objectName:'activity-meter';visible:root.meter && !root.satellite;Layout.fillWidth:true;Layout.preferredHeight:4;Layout.alignment:Qt.AlignVCenter;radius:2;color:'#323234';Rectangle{width:parent.width*Math.max(0,Math.min(1,root.activity.fraction || 0));height:4;radius:2;color:root.accent}}
  Text{objectName:'activity-value';visible:!root.satellite && !!root.activity.value && !(root.expanded && ['power','low'].includes(root.activity.kind));text:root.activity.value || '';textFormat:Text.PlainText;color:root.accent;font.family:root.expanded ? ShelfStyle.displayFamily:ShelfStyle.textFamily;font.pixelSize:root.expanded && !root.notification ? 25:12;font.weight:Font.Medium;font.features:({tnum:1})}
  ShelfIcon{visible:['power','low'].includes(root.activity.kind);size:root.expanded ? 32:16;icon:'notch/battery-status.svg';color:root.accent.r>root.accent.g ? root.accent:'white'}
  ShelfIcon{visible:root.expanded && !!root.activity.complete;size:18;icon:'notch/check.svg';color:'white'}
  Rectangle{objectName:'activity-primary-action';visible:root.expanded && !!root.activity.action;Layout.preferredWidth:38;Layout.preferredHeight:38;radius:19;color:'transparent';border.color:'white';border.width:2
   Rectangle{visible:root.activity.action==='stop';anchors.centerIn:parent;width:16;height:16;radius:3;color:root.accent}
   ShelfIcon{visible:root.activity.action!=='stop';anchors.centerIn:parent;size:17;icon:'notch/'+(root.activity.action==='pause' ? 'pause':root.activity.action==='dismiss' ? 'x':'check')+'.svg';color:root.accent}
   MouseArea{anchors.fill:parent;onClicked:root.action(root.activity.action,'')}
  }
 }
 RowLayout{visible:root.expanded && root.notification && !!root.activity.canReply;anchors.left:parent.left;anchors.right:parent.right;anchors.bottom:parent.bottom;anchors.margins:12;spacing:8
  TextField{id:reply;objectName:'activity-reply-input';visible:root.replying;Layout.fillWidth:true;implicitHeight:30;placeholderText:qsTr('Reply');color:'white';font.family:ShelfStyle.textFamily;font.pixelSize:13;padding:8;background:Rectangle{radius:15;color:'#252528'}onAccepted:root.sendReply()}
  ShelfButton{objectName:'activity-reply-open';visible:!root.replying;text:qsTr('Reply');onClicked:{root.replying=true;root.action('editing','true');reply.forceActiveFocus()}}
  ShelfButton{objectName:'activity-reply-send';visible:root.replying;icon:'notch/send.svg';accessibleLabel:qsTr('Send reply');implicitWidth:30;implicitHeight:30;onClicked:root.sendReply()}
 }
 function sendReply(){const text=reply.text.trim();if(!text)return;root.action('reply',text);reply.text='';root.replying=false;root.action('editing','false')}
 MouseArea{anchors.fill:parent;enabled:root.interactive;z:-1;onClicked:root.activate()}
}
