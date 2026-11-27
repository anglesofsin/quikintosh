import QtQuick
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import qs.services
Item {
 id:root
 property bool requested:false
 MediaDevices{id:devices}
 ColumnLayout{anchors.centerIn:parent;width:parent.width;spacing:12;visible:!root.requested || devices.videoInputs.length===0
  ShelfIcon{Layout.alignment:Qt.AlignHCenter;size:32;icon:'notch/camera.svg'}
  Text{Layout.fillWidth:true;text:devices.videoInputs.length ? qsTr('Camera'):qsTr('No camera connected');horizontalAlignment:Text.AlignHCenter;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.title;font.weight:Font.DemiBold}
  Text{Layout.fillWidth:true;text:devices.videoInputs.length ? qsTr('Preview starts only when you choose to open it.'):qsTr('Connect a camera to see yourself here.');horizontalAlignment:Text.AlignHCenter;color:ShelfStyle.secondary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;wrapMode:Text.WordWrap}
  ShelfButton{Layout.alignment:Qt.AlignHCenter;visible:devices.videoInputs.length>0;text:qsTr('Open camera');onClicked:root.requested=true}
 }
 Loader{anchors.fill:parent;active:root.requested && devices.videoInputs.length>0
  sourceComponent:Component{Item{
   Camera{id:camera;cameraDevice:devices.defaultVideoInput;active:root.visible && !!QsWindow.window && QsWindow.window.visible}
   CaptureSession{camera:camera;videoOutput:preview}
   VideoOutput{id:preview;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit;mirrored:true}
   Text{anchors.centerIn:parent;width:parent.width-32;visible:camera.error!==Camera.NoError;text:camera.errorString;color:ShelfStyle.primary;font.family:ShelfStyle.textFamily;font.pixelSize:ShelfStyle.body;wrapMode:Text.WordWrap;horizontalAlignment:Text.AlignHCenter}
   ShelfButton{anchors.right:parent.right;anchors.bottom:parent.bottom;icon:'notch/camera-off.svg';accessibleLabel:qsTr('Stop camera');onClicked:root.requested=false}
  }}
 }
}
