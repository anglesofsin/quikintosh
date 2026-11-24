import QtQuick
Item {
 id:root
 property bool autoHide:false
 property bool idle:false
 property int delayMs:15000
 property bool animate:true
 property bool ready:false
 property bool expired:false
 readonly property bool hideRequested:autoHide && idle && (delayMs===0 || expired)
 readonly property bool fullyHidden:hideRequested && progress<0.001
 property real progress:hideRequested ? 0:1
 Behavior on progress{NumberAnimation{duration:root.animate ? 240:0;easing.type:Easing.InOutCubic}}
 function reset(){
  if(!ready)return
  deadline.stop();expired=false
  if(autoHide && idle && delayMs>0)deadline.restart()
 }
 onAutoHideChanged:reset()
 onIdleChanged:reset()
 onDelayMsChanged:reset()
 Component.onCompleted:{ready=true;reset()}
 Timer{id:deadline;interval:Math.max(1,root.delayMs);onTriggered:root.expired=true}
}
