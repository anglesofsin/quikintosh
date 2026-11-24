import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import qs.services
import qs.components
Item{
 id:root
 property var look:null
 property string size:'s'
 property string variant:''
 property string mode:'shortcuts'
 readonly property color foreground:look?.light ? '#202124':'#f6f6f8'
 readonly property color secondary:look?.light ? '#64646b':'#babac4'
 readonly property var metrics:mode==='storage' ? [{title:'Used',value:ResourcesState.storagePercent,detail:ResourcesState.storageUsedGb.toFixed(1)+' / '+ResourcesState.storageTotalGb.toFixed(1)+' GB'}]:[{title:'CPU',value:ResourcesState.cpuPercent,detail:''},{title:'Memory',value:ResourcesState.memoryPercent,detail:ResourcesState.memoryUsedGb.toFixed(1)+' GB'}]
 ColumnLayout{
  anchors.fill:parent;spacing:8
  Text{Layout.fillWidth:true;text:root.mode==='display' ? 'Display':root.mode==='storage' ? 'Storage':root.mode==='system' ? 'Activity':root.mode==='microphone' ? 'Microphone':'Shortcuts';color:root.foreground;font.family:'SF Pro Text';font.pixelSize:13;font.weight:Font.DemiBold}
  ColumnLayout{visible:root.mode==='storage' || root.mode==='system';Layout.fillWidth:true;Layout.fillHeight:true;spacing:8
   Repeater{model:root.metrics
    ColumnLayout{required property var modelData;Layout.fillWidth:true;spacing:4
     RowLayout{Layout.fillWidth:true;Text{text:modelData.title;color:root.secondary;font.pixelSize:11;Layout.fillWidth:true}Text{text:Math.round(modelData.value)+'%';color:root.foreground;font.pixelSize:root.size==='s' ? 18:25;font.weight:Font.DemiBold}}
     Rectangle{Layout.fillWidth:true;implicitHeight:5;radius:3;color:root.look?.light ? '#20000000':'#25ffffff';Rectangle{width:parent.width*Math.max(0,Math.min(1,modelData.value/100));height:parent.height;radius:3;color:Theme.accent}}
     Text{visible:text.length>0;text:modelData.detail;color:root.secondary;font.pixelSize:10}
    }
   }
   Item{Layout.fillHeight:true}
   TahoeButton{visible:root.size!=='s';text:'Details';onClicked:SettingsLauncher.open(root.mode==='storage' ? 'storage':'activity')}
  }
  ColumnLayout{visible:root.mode==='display';Layout.fillWidth:true;Layout.fillHeight:true
   Text{text:BrightnessController.available ? Math.round(BrightnessController.value*100)+'%':'Unavailable';color:root.foreground;font.pixelSize:32;font.weight:Font.DemiBold}
   TahoeSlider{Layout.fillWidth:true;from:.01;to:1;value:BrightnessController.value;enabled:BrightnessController.available;onMoved:BrightnessController.set(value)}
   TahoeButton{text:NightShift.enabled ? 'Night Shift On':'Night Shift Off';onClicked:NightShift.toggle()}
  }
  ColumnLayout{visible:root.mode==='microphone';Layout.fillWidth:true;Layout.fillHeight:true
   Text{Layout.fillWidth:true;wrapMode:Text.WordWrap;text:!ExtraControls.available('extra_microphone') ? 'No microphone':ExtraControls.microphoneMuted ? 'Muted':'On';color:root.foreground;font.pixelSize:24;font.weight:Font.DemiBold}
   TahoeButton{text:ExtraControls.microphoneMuted ? 'Unmute':'Mute';enabled:ExtraControls.available('extra_microphone');onClicked:ExtraControls.run('extra_microphone')}
   Item{Layout.fillHeight:true}
  }
  GridLayout{visible:root.mode==='shortcuts';columns:2;Layout.fillWidth:true;Layout.fillHeight:true;rowSpacing:6;columnSpacing:6
   Repeater{model:[{id:'extra_clipboard',label:'Clipboard'},{id:'extra_quicknote',label:'Quick Note'},{id:'extra_wallpaper',label:'Wallpaper'},{id:'extra_settings',label:'Settings'}]
    TahoeButton{required property var modelData;Layout.fillWidth:true;text:modelData.label;onClicked:ExtraControls.run(modelData.id)}
   }
  }
 }
}
