import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components.glass
BoxGlass{
 id:root
 readonly property var entry:MediaCaptureState.entries[0] || null
 function appName(value){const match=DesktopEntries.heuristicLookup(value);if(match?.name)return match.name;const clean=String(value).replace(/^\./,'').replace(/-wrapped$/,'');return clean.charAt(0).toUpperCase()+clean.slice(1)}
 readonly property string apps:(entry?.apps || []).map(appName).join(', ')
 implicitHeight:48;radius:23
 Rectangle{anchors.fill:parent;radius:23;color:Theme.isLight ? '#52ffffff':'#52000000'}
 ColumnLayout{anchors.fill:parent;anchors.margins:7;spacing:2
  RowLayout{Layout.alignment:Qt.AlignHCenter;spacing:6
   Rectangle{Layout.preferredWidth:5;Layout.preferredHeight:5;radius:2.5;color:MediaCaptureState.indicatorColor;Layout.alignment:Qt.AlignVCenter}
   Text{text:root.entry ? I18n.tr(root.entry.label):'';color:Theme.textPrimary;font.pixelSize:12;font.weight:Font.DemiBold;verticalAlignment:Text.AlignVCenter}
  }
  Text{Layout.fillWidth:true;text:root.apps;color:Theme.textSecondary;font.pixelSize:11;horizontalAlignment:Text.AlignHCenter;elide:Text.ElideRight;textFormat:Text.PlainText}
 }
 MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:SettingsLauncher.open('privacy')}
}
