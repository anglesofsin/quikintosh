import QtQuick
import Quickshell
import QtQuick.Layouts
import qs.components
import qs.services
import qs.settingsapp
import qs.ui.settings.widgets
import qs.rosa.services as Rosa
ContentPage {
 id:root
 property bool revealed:false
 readonly property var host:QsWindow.window
 Connections{target:root.host;function onVisibleChanged(){if(!root.host.visible)root.revealed=false}}
 SettingsCard{title:'Location'
  RowLayout{Layout.fillWidth:true;implicitHeight:48
   Text{Layout.fillWidth:true;text:'Weather location';color:Theme.textPrimary;font.pixelSize:13}
   TahoeButton{text:root.revealed ? 'Hide location':'Edit location…';onClicked:root.revealed=!root.revealed}
  }
  TahoeField{visible:root.revealed;Layout.fillWidth:true;text:root.revealed ? Rosa.Prefs.weatherPlace:'';placeholderText:'City or city,country';onEditingFinished:if(root.revealed)Rosa.Prefs.set('weatherPlace',text.trim())}
 }
 SettingsCard{title:'Alerts'
  SettingsRow{label:'Weather alerts';kind:'switch';checked:Rosa.Prefs.weatherEnabled;separator:false;onToggled:value=>Rosa.Prefs.set('weatherEnabled',value)}
 }
}
