import QtQuick
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import qs.services
Item {
 id:root
 property bool requested:false
 ColumnLayout {
  anchors.centerIn:parent;width:parent.width;spacing:12;visible:!root.requested
  ShelfIcon{Layout.alignment:Qt.AlignHCenter;size:32;icon:'notch/camera.svg'}
  Text{Layout.fillWidth:true;text:qsTr('Camera preview');horizontalAlignment:Text.AlignHCenter;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.title;font.weight:Font.DemiBold}
  Text{Layout.fillWidth:true;text:qsTr('Preview starts only when you choose to open it.');horizontalAlignment:Text.AlignHCenter;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;wrapMode:Text.WordWrap}
  ShelfButton{Layout.alignment:Qt.AlignHCenter;text:qsTr('Open camera');onClicked:root.requested=true}
 }
 Loader {
  anchors.fill:parent;active:root.requested;asynchronous:true
  sourceComponent:Component{Item{
   MediaDevices{id:devices}
   Camera{id:camera;cameraDevice:devices.defaultVideoInput;active:root.visible && !!QsWindow.window && QsWindow.window.visible && devices.videoInputs.length>0}
   CaptureSession{camera:camera;videoOutput:preview}
   VideoOutput{id:preview;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit;mirrored:true;visible:devices.videoInputs.length>0}
   Text{anchors.centerIn:parent;width:parent.width-32;text:devices.videoInputs.length===0 ? qsTr('No camera connected'):camera.errorString;visible:devices.videoInputs.length===0 || camera.error!==Camera.NoError;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignHCenter}
   ShelfButton{anchors.right:parent.right;anchors.bottom:parent.bottom;icon:'notch/camera-off.svg';accessibleLabel:qsTr('Stop camera');onClicked:root.requested=false}
  }}
 }
}
