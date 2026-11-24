import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import QtMultimedia
import Quickshell
import Quickshell.Wayland
import qs.services
Scope {
 Loader {
  active:CaptureState.cameraOpened
  sourceComponent:PanelWindow {
   id:win
   screen:Quickshell.screens[0]
   anchors {top:true;bottom:true;left:true;right:true}
   color:'transparent';exclusiveZone:-1;mask:Region {item:box}
   WlrLayershell.namespace:'lickintosh:pinned-capture';WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.keyboardFocus:WlrKeyboardFocus.None
   property bool flipped:true
   property int device:0
   MediaDevices {id:devices}
   Rectangle {
    id:box;x:Math.max(0,win.width-400);y:80;width:360;height:310;radius:14;color:'#242428';border.color:'#5b5b63';border.width:1
    Item {id:view;x:8;y:8;width:parent.width-16;height:240;clip:true
     VideoOutput {id:video;anchors.fill:parent;fillMode:VideoOutput.PreserveAspectFit;mirrored:win.flipped}
     CaptureSession {
      camera:Camera {id:camera;active:CaptureState.cameraOpened && devices.videoInputs.length>0;cameraDevice:devices.videoInputs[Math.min(win.device,devices.videoInputs.length-1)] || devices.defaultVideoInput;onErrorOccurred:(code,message)=>CaptureState.error(message)}
      videoOutput:video
      imageCapture:ImageCapture {id:photo;onImageSaved:(id,path)=>CaptureState.send({action:'pinFile',path:path});onErrorOccurred:(id,code,message)=>CaptureState.error(message)}
     }
     Text {visible:devices.videoInputs.length===0;anchors.centerIn:parent;text:'No camera available';color:'white';font.pixelSize:15}
    }
    MouseArea {anchors.fill:view;cursorShape:Qt.SizeAllCursor;property real dx:0;property real dy:0;onPressed:m=>{const p=mapToItem(win.contentItem,m.x,m.y);dx=p.x-box.x;dy=p.y-box.y};onPositionChanged:m=>{if(pressed){const p=mapToItem(win.contentItem,m.x,m.y);box.x=Math.max(0,Math.min(win.width-box.width,p.x-dx));box.y=Math.max(0,Math.min(win.height-box.height,p.y-dy))}}}
    Row {anchors.bottom:parent.bottom;anchors.bottomMargin:10;anchors.horizontalCenter:parent.horizontalCenter;spacing:6
     Button {text:'Flip';onClicked:win.flipped=!win.flipped}
     Button {text:'Camera';enabled:devices.videoInputs.length>1;onClicked:win.device=(win.device+1)%devices.videoInputs.length}
     Button {text:'Capture';enabled:devices.videoInputs.length>0;onClicked:photo.captureToFile(Quickshell.env('XDG_RUNTIME_DIR')+'/lickintosh-camera-'+Date.now()+'.png')}
     Button {text:'×';onClicked:CaptureState.cameraOpened=false}
    }
   }
  }
 }
}
