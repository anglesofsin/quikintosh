import QtQuick
import QtQuick.Layouts
import Quickshell
import qs.services
import qs.components.glass
BoxGlass{
 id:root
 readonly property var entry:MediaCaptureState.entries[0] || null
 implicitHeight:22;radius:11
 RowLayout{anchors.centerIn:parent;spacing:6
  Rectangle{Layout.preferredWidth:5;Layout.preferredHeight:5;radius:2.5;color:MediaCaptureState.indicatorColor;Layout.alignment:Qt.AlignVCenter}
  Text{text:root.entry ? I18n.tr(root.entry.label):'';color:Theme.textPrimary;font.pixelSize:12;verticalAlignment:Text.AlignVCenter}
 }
 MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:SettingsLauncher.open('privacy')}
}
