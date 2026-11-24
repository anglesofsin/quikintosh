import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
Item {
 id:root
 property var look:null
 property string size:'s'
 property string variant:''
 property string mode:'shortcuts'
 readonly property bool compact:width<190
 readonly property color foreground:look?.primary || Theme.textPrimary
 readonly property color secondary:look?.secondary || Theme.textSecondary
 readonly property color accent:Theme.accent
 readonly property string heading:mode==='display' ? 'Display':mode==='storage' ? 'Storage':mode==='system' ? 'Activity':mode==='microphone' ? 'Microphone':'Shortcuts'
 readonly property var metrics:mode==='storage' ? [{title:'Used',value:ResourcesState.storagePercent,detail:ResourcesState.storageUsedGb.toFixed(1)+' / '+ResourcesState.storageTotalGb.toFixed(1)+' GB'}]:[{title:'CPU',value:ResourcesState.cpuPercent,detail:''},{title:'Memory',value:ResourcesState.memoryPercent,detail:ResourcesState.memoryUsedGb.toFixed(1)+' GB'}]
 ColumnLayout {
  anchors.fill:parent;spacing:8
  Text{Layout.fillWidth:true;text:root.heading;color:root.secondary;font.family:'SF Pro Text';font.pixelSize:11;font.weight:Font.DemiBold;elide:Text.ElideRight}
  ColumnLayout {
   visible:root.mode==='microphone';Layout.fillWidth:true;Layout.fillHeight:true;spacing:8
   RowLayout {
    Layout.fillWidth:true;Layout.fillHeight:true;spacing:10
    Rectangle {
     Layout.preferredWidth:root.compact ? 40:56;Layout.preferredHeight:width;radius:width/2
     color:Qt.rgba(root.accent.r,root.accent.g,root.accent.b,ExtraControls.microphoneMuted ? .10:.22)
     CFVI{anchors.centerIn:parent;size:root.compact ? 22:29;icon:ExtraControls.microphoneMuted ? 'notch/mic-off.svg':'notch/mic.svg';color:ExtraControls.microphoneMuted ? root.secondary:root.accent}
    }
    ColumnLayout{Layout.fillWidth:true;spacing:3
     Text{Layout.fillWidth:true;text:!ExtraControls.available('extra_microphone') ? 'No Input':ExtraControls.microphoneMuted ? 'Muted':'On';color:root.foreground;font.family:'SF Pro Display';font.pixelSize:root.compact ? 18:28;font.weight:Font.DemiBold;elide:Text.ElideRight}
     Text{visible:!root.compact;Layout.fillWidth:true;text:!ExtraControls.available('extra_microphone') ? 'Connect a microphone':ExtraControls.microphoneMuted ? 'Microphone is muted':'Ready to speak';color:root.secondary;font.pixelSize:11;elide:Text.ElideRight}
    }
   }
   Rectangle {
    Layout.fillWidth:true;Layout.preferredHeight:30;radius:15
    color:microphoneMouse.containsMouse ? Qt.rgba(root.accent.r,root.accent.g,root.accent.b,.30):Qt.rgba(root.accent.r,root.accent.g,root.accent.b,.16)
    opacity:ExtraControls.available('extra_microphone') ? 1:.45
    Text{anchors.centerIn:parent;text:ExtraControls.microphoneMuted ? 'Unmute':'Mute';color:root.foreground;font.pixelSize:12;font.weight:Font.Medium}
    MouseArea{id:microphoneMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;enabled:ExtraControls.available('extra_microphone');onClicked:ExtraControls.run('extra_microphone')}
   }
  }
  GridLayout {
   visible:root.mode==='shortcuts';columns:2;Layout.fillWidth:true;Layout.fillHeight:true;rowSpacing:6;columnSpacing:6
   Repeater{
    model:[{id:'extra_clipboard',label:'Clipboard',icon:'notch/clipboard.svg'},{id:'extra_quicknote',label:'Quick Note',icon:'notch/book.svg'},{id:'extra_wallpaper',label:'Wallpaper',icon:'notch/image.svg'},{id:'extra_settings',label:'Settings',icon:'settings/general.svg'}]
    delegate:Rectangle{
     id:tile;required property var modelData
     Layout.fillWidth:true;Layout.fillHeight:true;Layout.minimumHeight:42;radius:12
     color:Qt.rgba(root.accent.r,root.accent.g,root.accent.b,shortcutMouse.pressed ? .30:shortcutMouse.containsMouse ? .22:.10)
     border.width:1;border.color:Qt.rgba(root.accent.r,root.accent.g,root.accent.b,.10)
     CFVI{size:root.compact ? 19:23;icon:tile.modelData.icon;color:root.accent;x:root.compact ? (parent.width-width)/2:11;y:root.compact ? 5:(parent.height-height)/2}
     Text{
      x:root.compact ? 2:43;y:root.compact ? 26:0;width:parent.width-x-(root.compact ? 2:6);height:root.compact ? parent.height-y:parent.height
      text:tile.modelData.label;color:root.foreground;font.family:'SF Pro Text';font.pixelSize:root.compact ? 9:11;font.weight:Font.Medium
      horizontalAlignment:root.compact ? Text.AlignHCenter:Text.AlignLeft;verticalAlignment:Text.AlignVCenter;wrapMode:Text.WordWrap
     }
     MouseArea{id:shortcutMouse;anchors.fill:parent;hoverEnabled:true;cursorShape:Qt.PointingHandCursor;onClicked:ExtraControls.run(tile.modelData.id)}
    }
   }
  }
  ColumnLayout {
   visible:root.mode==='storage' || root.mode==='system';Layout.fillWidth:true;Layout.fillHeight:true;spacing:10
   Repeater{model:root.metrics
    ColumnLayout{required property var modelData;Layout.fillWidth:true;spacing:5
     RowLayout{Layout.fillWidth:true;Text{text:modelData.title;color:root.secondary;font.pixelSize:11;Layout.fillWidth:true}Text{text:Math.round(modelData.value)+'%';color:root.foreground;font.pixelSize:root.compact ? 20:27;font.weight:Font.DemiBold}}
     Rectangle{Layout.fillWidth:true;implicitHeight:6;radius:3;color:Qt.rgba(root.accent.r,root.accent.g,root.accent.b,.12);Rectangle{width:parent.width*Math.max(0,Math.min(1,modelData.value/100));height:parent.height;radius:3;color:root.accent}}
     Text{visible:text.length>0;text:modelData.detail;color:root.secondary;font.pixelSize:10}
    }
   }
   Item{Layout.fillHeight:true}
   TahoeButton{visible:!root.compact;text:'Details';onClicked:SettingsLauncher.open(root.mode==='storage' ? 'storage':'activity')}
  }
  ColumnLayout{
   visible:root.mode==='display';Layout.fillWidth:true;Layout.fillHeight:true;spacing:6
   RowLayout{Layout.fillWidth:true;CFVI{icon:'sun-small.svg';size:28;color:root.accent}Text{text:BrightnessController.available ? Math.round(BrightnessController.value*100)+'%':'—';color:root.foreground;font.pixelSize:root.compact ? 25:34;font.weight:Font.DemiBold;Layout.fillWidth:true}}
   TahoeSlider{Layout.fillWidth:true;from:.01;to:1;value:BrightnessController.value;enabled:BrightnessController.available;onMoved:BrightnessController.set(value)}
   TahoeButton{Layout.fillWidth:true;text:NightShift.enabled ? 'Night Shift On':'Night Shift Off';onClicked:NightShift.toggle()}
  }
 }
}
