import QtQuick
import Quickshell
import Quickshell.Wayland
import Quickshell.Io
import qs.services
Scope {
 id:root
 property var full:({})
 Process{id:query;command:['hyprctl','-j','--batch','monitors;clients'];stdout:StdioCollector{onStreamFinished:{try{
  const parts=JSON.parse('['+text.trim().replace(/]\s*\[/,'] , [')+']');const map={}
  for(const m of parts[0])map[m.name]=parts[1].some(c=>c.monitor===m.id && c.fullscreen===2 && (c.workspace.id===m.activeWorkspace.id || c.workspace.id===m.specialWorkspace.id))
  if(JSON.stringify(map)!==JSON.stringify(root.full))root.full=map
 }catch(e){}}}}
 Timer{interval:750;running:MediaCaptureState.islandActive;repeat:true;triggeredOnStart:true;onTriggered:if(!query.running)query.running=true}
 Variants{model:Quickshell.screens;delegate:PanelWindow{
  required property var modelData
  screen:modelData;visible:MediaCaptureState.islandActive && !!root.full[modelData.name]
  anchors{top:true;right:true}implicitWidth:18;implicitHeight:18;color:'transparent'
  exclusionMode:ExclusionMode.Ignore;WlrLayershell.layer:WlrLayer.Overlay;WlrLayershell.namespace:'lickintosh-fullscreen-privacy';mask:Region{}
  Rectangle{anchors.centerIn:parent;width:5;height:5;radius:2.5;color:MediaCaptureState.indicatorColor}
 }}
}
