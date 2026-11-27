import QtQuick
import QtQuick.Layouts
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import qs.services
import qs.settingsapp
import qs.ui.settings.widgets
import qs.components
ContentPage {
 id:root
 property string historyRange:'24h'
 property var devices:[]
 readonly property var mainBattery:devices.find(d=>d.kind==='laptop' && d.connected!==false) || null
 readonly property var history:historyRange==='24h' ? BatteryHistoryState.last24h:BatteryHistoryState.last10days
 readonly property var usage:historyRange==='24h' ? BatteryHistoryState.screenUsage24h:BatteryHistoryState.screenUsage10days
 readonly property bool watching:visible && !!QsWindow.window && QsWindow.window.visible
 onWatchingChanged:{ShellConfig.watchEnergy('battery-settings',watching);if(watching && !inventory.running)inventory.running=true}
 Component.onDestruction:ShellConfig.watchEnergy('battery-settings',false)
 Timer{interval:30000;repeat:true;running:root.watching;onTriggered:if(!inventory.running)inventory.running=true}
 Process{id:inventory;command:[ShelfState.pythonExecutable,Quickshell.shellPath('island-shelf/battery_backend.py')];stdout:StdioCollector{onStreamFinished:{try{root.devices=JSON.parse(text).devices.filter(d=>d.connected!==false && d.name)}catch(_){root.devices=[]}}}}
 ContentSection{
  RowLayout{Layout.fillWidth:true;Layout.topMargin:12;Layout.bottomMargin:12;spacing:20
   Rectangle{Layout.preferredWidth:68;Layout.preferredHeight:68;radius:16;color:'#173f28'
    CFVI{anchors.centerIn:parent;icon:'notch/battery.svg';size:42;color:'#32d74b'}
   }
   ColumnLayout{Layout.fillWidth:true;spacing:6
    Text{text:root.mainBattery ? I18n.tr('Battery'):I18n.tr('Power');color:Theme.textPrimary;font.family:'SF Pro Display';font.pixelSize:24;font.weight:Font.DemiBold}
    Text{Layout.fillWidth:true;text:root.mainBattery ? (root.mainBattery.charging ? I18n.tr('Charging'):I18n.tr('On Battery')):I18n.tr('Connected to Power Adapter');color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:13;wrapMode:Text.WordWrap}
   }
   Text{visible:!!root.mainBattery;text:root.mainBattery ? root.mainBattery.percent+'%':'';font.family:'SF Pro Display';font.pixelSize:36;font.weight:Font.Medium;color:Theme.textPrimary}
  }
 }
 ContentSection{title:I18n.tr('Energy')
  SettingsRow{label:I18n.tr('Low Power Mode');description:I18n.tr('Reduce energy use to extend battery life.');kind:'choice';choices:[I18n.tr('Never'),I18n.tr('Always'),I18n.tr('Only on Battery'),I18n.tr('Only on Power Adapter')];selection:Math.max(0,['never','always','only-battery','only-ac'].indexOf(BatteryHealthState.lowPowerRule));onPicked:index=>BatteryHealthState.setLowPowerRule(['never','always','only-battery','only-ac'][index])}
  SettingsRow{visible:BatteryHealthState.energyFullDesign>0;label:I18n.tr('Battery Health');value:BatteryHealthState.healthLabel+' · '+BatteryHealthState.healthPercent+'%';separator:false}
  SettingsRow{visible:BatteryHealthState.chargeLimitSupported;label:I18n.tr('Charge Limit');kind:'slider';minimum:50;maximum:100;number:BatteryHealthState.chargeLimitValue;value:BatteryHealthState.chargeLimitValue+'%';step:1;onCommitted:value=>BatteryHealthState.setChargeLimit(value)}
 }
 ContentSection{title:I18n.tr('Usage History');visible:!!root.mainBattery || root.history.length>0
  RowLayout{Layout.fillWidth:true;Layout.topMargin:8;Layout.bottomMargin:12
   Text{Layout.fillWidth:true;text:I18n.tr('Battery Level');font.family:'SF Pro Text';font.pixelSize:14;font.weight:Font.DemiBold;color:Theme.textPrimary}
   TahoeCombo{model:[I18n.tr('Last 24 Hours'),I18n.tr('Last 10 Days')];currentIndex:root.historyRange==='24h' ? 0:1;onActivated:index=>root.historyRange=index===0 ? '24h':'10d'}
  }
  Item{Layout.fillWidth:true;implicitHeight:152
   Column{anchors.fill:parent;spacing:36;Repeater{model:4;Rectangle{width:parent.width;height:1;color:Theme.isLight ? '#10000000':'#18ffffff'}}}
   Row{anchors.fill:parent;anchors.bottomMargin:20;spacing:3;visible:root.history.length>1
    Repeater{model:root.history.slice(-72);Rectangle{required property var modelData;width:Math.max(2,(parent.width-3*(parent.children.length-1))/Math.max(1,parent.children.length));height:Math.max(2,Math.min(100,modelData.percent)/100*(parent.height));anchors.bottom:parent.bottom;radius:2;color:'#32d74b'}}
   }
   Text{anchors.centerIn:parent;visible:root.history.length<=1;text:I18n.tr('Battery history will appear as data is collected.');width:parent.width-40;wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignHCenter;color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:13}
  }
  RowLayout{Layout.fillWidth:true;Layout.bottomMargin:8
   Text{text:root.history.length ? Qt.formatDateTime(new Date(root.history[0].timestamp*1000),root.historyRange==='24h' ? 'hh:mm':'ddd d'):'';color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:11}
   Item{Layout.fillWidth:true}
   Text{text:root.history.length ? Qt.formatDateTime(new Date(root.history[root.history.length-1].timestamp*1000),root.historyRange==='24h' ? 'hh:mm':'ddd d'):'';color:Theme.textSecondary;font.family:'SF Pro Text';font.pixelSize:11}
  }
 }
 ContentSection{title:I18n.tr('Screen Activity');visible:root.usage.length>0
  Row{Layout.fillWidth:true;Layout.preferredHeight:100;height:100;spacing:4
   Repeater{model:root.usage.slice(-24);Rectangle{required property var modelData;width:Math.max(3,(parent.width-4*(parent.children.length-1))/Math.max(1,parent.children.length));height:Math.max(2,Math.min(60,Number(modelData.minutesOn))/60*90);anchors.bottom:parent.bottom;radius:3;color:Theme.accent}}
  }
 }
 ContentSection{title:I18n.tr('Connected Devices');visible:root.devices.some(d=>d.kind!=='laptop')
  Repeater{model:root.devices.filter(d=>d.kind!=='laptop');SettingsRow{required property var modelData;label:modelData.name;description:modelData.charging ? I18n.tr('Charging'):modelData.source;value:modelData.percent+'%'}}
 }
 ContentSection{title:I18n.tr('Energy Usage')
  Repeater{model:ShellConfig.topConsumers.slice(0,8);SettingsRow{required property var modelData;label:modelData.name;value:'CPU '+Number(modelData.cpu || 0).toFixed(1)+'% · '+ShellConfig.formatMemory(modelData.rssMb)}}
  SettingsRow{visible:!ShellConfig.topConsumers.length;label:ShellConfig.hasCollectedOnce ? I18n.tr('No significant energy usage'):I18n.tr('Collecting energy usage…');separator:false}
 }
}
