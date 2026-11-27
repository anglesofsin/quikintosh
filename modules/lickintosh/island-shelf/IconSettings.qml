import QtQuick
import QtQuick.Controls.Basic
import QtQuick.Layouts
import qs.services
import qs.components
ColumnLayout {
 id:root;objectName:'activity-icon-settings';spacing:12
 property bool settingsPage:false
 property bool overridesExpanded:false
 readonly property var iconNames:({"watch":qsTr("Watch"),"bluetooth":qsTr("Bluetooth"),"bell":qsTr("Notification"),"clock":qsTr("Clock"),"video":qsTr("Video"),"headphones":qsTr("Headphones"),"smartphone":qsTr("Phone"),"laptop":qsTr("Computer"),"keyboard":qsTr("Keyboard"),"mouse":qsTr("Mouse"),"volume-2":qsTr("Speaker"),"volume-x":qsTr("Muted speaker"),"mic":qsTr("Microphone"),"mic-off":qsTr("Muted microphone"),"sun":qsTr("Brightness"),"wifi":qsTr("Wi-Fi"),"vpn":qsTr("VPN"),"file-text":qsTr("Document"),"clipboard":qsTr("Clipboard"),"command":qsTr("Keyboard shortcuts"),"moon":qsTr("Focus"),"terminal":qsTr("Terminal"),"download":qsTr("Download"),"check":qsTr("Checkmark"),"x":qsTr("Close"),"inbox":qsTr("File tray"),"cloud":qsTr("Cloud"),"link":qsTr("Connection"),"battery":qsTr("Battery outline"),"battery-status":qsTr("Battery filled"),"battery-charging":qsTr("Charging battery"),"pause":qsTr("Pause"),"play":qsTr("Play"),"camera":qsTr("Camera"),"music":qsTr("Music"),"grid":qsTr("Widgets")})
 readonly property var stateNames:({completed:qsTr('Completed'),failed:qsTr('Error'),paused:qsTr('Paused'),disconnected:qsTr('Disconnected')})
 readonly property var names:({osd:qsTr('Volume and brightness'),timer:qsTr('Timer'),alarm:qsTr('Alarm'),vpn:qsTr('VPN'),net:qsTr('Network'),bt:qsTr('Bluetooth'),peri:qsTr('Devices'),notif:qsTr('Notifications'),cmd:qsTr('Commands'),cmdfail:qsTr('Command errors'),task:qsTr('Tasks'),taskfail:qsTr('Task errors'),download:qsTr('Downloads'),share:qsTr('Sharing'),cloud:qsTr('Cloud'),tray:qsTr('Files'),done:qsTr('Completion'),fail:qsTr('Errors'),focus:qsTr('Focus'),route:qsTr('Audio output'),print:qsTr('Printing'),clip:qsTr('Clipboard'),keys:qsTr('Keyboard'),desk:qsTr('Workspace'),remind:qsTr('Reminders'),weather:qsTr('Weather'),launch:qsTr('Applications')})
 readonly property var p:ActivityIconPolicy.preferences
 readonly property color ink:settingsPage ? Theme.textPrimary:ShelfStyle.primary
 function option(key){return p[key]===undefined ? ActivityIconPolicy.spec.defaults[key]:p[key]}
 Text{text:qsTr('Activity icons');color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold}
 Rectangle{Layout.fillWidth:true;implicitHeight:rows.implicitHeight+16;radius:12;color:root.settingsPage ? Theme.card:ShelfStyle.surface
  ColumnLayout{id:rows;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:12;y:8;spacing:0
   Repeater{model:[{key:'iconPolicySmart',title:qsTr('Automatic contextual icons')},{key:'iconPolicyStatus',title:qsTr('Prioritize completion, pause and errors')},{key:'iconPolicyDevices',title:qsTr('Match the connected device type')},{key:'iconPolicyColors',title:qsTr('Use status colors')},{key:'iconPolicyAppBadges',title:qsTr('Show notification app badges')}]
    RowLayout{required property var modelData;Layout.fillWidth:true;Layout.preferredHeight:38
     Text{Layout.fillWidth:true;text:modelData.title;color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:13}
     Switch{id:toggle;Accessible.name:modelData.title;enabled:!['iconPolicyStatus','iconPolicyDevices'].includes(modelData.key) || root.option('iconPolicySmart');checked:root.option(modelData.key);onToggled:ActivityIconPolicy.set(modelData.key,checked);padding:0;implicitWidth:40;implicitHeight:24
      indicator:Rectangle{opacity:toggle.enabled ? 1:.45;width:40;height:24;radius:12;color:toggle.checked ? '#30d158':'#55555b';Rectangle{x:toggle.checked ? 18:2;y:2;width:20;height:20;radius:10;color:'white'}}
      contentItem:Item{}
     }
    }
   }
   Repeater{model:[{key:'iconPolicyCompactSize',title:qsTr('Compact size')},{key:'iconPolicyExpandedSize',title:qsTr('Expanded base size')},{key:'iconPolicyMeterSize',title:qsTr('Volume and brightness icon size')},{key:'iconPolicySatelliteSize',title:qsTr('Side indicator size')}]
    RowLayout{required property var modelData;Layout.fillWidth:true;Layout.preferredHeight:40
     Text{Layout.fillWidth:true;text:modelData.title;color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:13}
     ShelfSlider{id:slider;Accessible.name:modelData.title;manageHold:!root.settingsPage;Layout.preferredWidth:150;from:ActivityIconPolicy.spec.sizes[modelData.key][0];to:ActivityIconPolicy.spec.sizes[modelData.key][1];stepSize:1;value:root.option(modelData.key);onPressedChanged:if(!pressed)ActivityIconPolicy.set(modelData.key,value);onMoved:if(!pressed)ActivityIconPolicy.set(modelData.key,value)}
     Text{Layout.preferredWidth:36;text:Math.round(slider.value)+' px';color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:11}
    }
   }
  }
 }
 Text{text:qsTr('State icons');color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold}
 Rectangle{Layout.fillWidth:true;implicitHeight:states.implicitHeight+16;radius:12;color:root.settingsPage ? Theme.card:ShelfStyle.surface
  ColumnLayout{id:states;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:12;y:8;spacing:6
   Repeater{model:ActivityIconPolicy.spec.statuses
    RowLayout{required property string modelData;Layout.fillWidth:true
     Text{Layout.fillWidth:true;text:root.stateNames[modelData];color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:13}
     ShelfChoice{manageHold:!root.settingsPage;Layout.preferredWidth:180;model:[qsTr('Automatic')].concat(ActivityIconPolicy.spec.icons.map(key=>root.iconNames[key] || key));currentIndex:Math.max(0,ActivityIconPolicy.spec.icons.indexOf((root.p.iconPolicyStatusOverrides || {})[modelData])+1);onActivated:index=>ActivityIconPolicy.stateOverride(modelData,index ? ActivityIconPolicy.spec.icons[index-1]:'')}
    }
   }
  }
 }
 RowLayout{Layout.fillWidth:true
  Text{Layout.fillWidth:true;text:qsTr('Per-event overrides');color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:15;font.weight:Font.DemiBold}
  ShelfButton{objectName:'icon-policy-customize';text:root.overridesExpanded ? qsTr('Hide event icons'):qsTr('Customize events');onClicked:root.overridesExpanded=!root.overridesExpanded}
  ShelfButton{objectName:'icon-policy-reset';text:qsTr('Restore defaults');onClicked:ActivityIconPolicy.reset()}
 }
 Rectangle{visible:root.overridesExpanded;Layout.fillWidth:true;implicitHeight:overrides.implicitHeight+16;radius:12;color:root.settingsPage ? Theme.card:ShelfStyle.surface
  ColumnLayout{id:overrides;anchors.left:parent.left;anchors.right:parent.right;anchors.margins:12;y:8;spacing:6
   Repeater{model:root.overridesExpanded ? ActivityIconPolicy.spec.kinds.filter(key=>!['record','power','low'].includes(key)):[]
    RowLayout{required property string modelData;Layout.fillWidth:true
     ShelfIcon{size:16;icon:'notch/'+ActivityIconPolicy.resolve({kind:modelData,icon:(root.p.iconPolicyOverrides || {})[modelData] || ''},'compact').icon+'.svg'}
     Text{Layout.fillWidth:true;text:root.names[modelData] || modelData;color:root.ink;font.family:ShelfStyle.textFamily;font.pixelSize:13}
     ShelfChoice{objectName:'icon-event-'+modelData;manageHold:!root.settingsPage;Layout.preferredWidth:180;model:[qsTr('Automatic')].concat(ActivityIconPolicy.spec.icons.map(key=>root.iconNames[key] || key));currentIndex:Math.max(0,ActivityIconPolicy.spec.icons.indexOf((root.p.iconPolicyOverrides || {})[modelData])+1);onActivated:index=>ActivityIconPolicy.override(modelData,index ? ActivityIconPolicy.spec.icons[index-1]:'')}
    }
   }
  }
 }
}
