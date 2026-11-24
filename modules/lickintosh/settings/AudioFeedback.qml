pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
Singleton {
 id:root
 property bool panelOpen:false
 property bool nativeVisible:false
 readonly property bool suppressed:panelOpen || settle.running
 onPanelOpenChanged:settle.restart()
 function manual(){settle.restart()}
 Timer{id:settle;interval:450}
 IpcHandler {
  target:'audioFeedback'
  function manual():void{root.manual()}
  function state():string{return JSON.stringify({panelOpen:root.panelOpen,suppressed:root.suppressed,nativeVisible:root.nativeVisible})}
 }
}
