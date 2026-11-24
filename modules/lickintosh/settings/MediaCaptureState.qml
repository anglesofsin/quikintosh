pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import "capture-classifier.js" as Capture
Singleton {
 id:root
 property var cameraApps:[]
 property var micApps:[]
 property var screenApps:[]
 property var audioApps:[]
 property var detected:[]
 readonly property var visibleDetails:PrivacyPreferences.enabled ? detected.filter(entry=>PrivacyPreferences.allowed(entry)):[]
 readonly property bool cameraActive:visibleDetails.some(entry=>entry.kind==='camera')
 readonly property bool micActive:visibleDetails.some(entry=>entry.kind==='mic')
 readonly property bool screenActive:visibleDetails.some(entry=>entry.kind==='screen')
 readonly property bool audioActive:visibleDetails.some(entry=>entry.kind==='audio')
 readonly property var entries:PrivacyPreferences.kinds.map(kind=>({kind:kind,label:PrivacyPreferences.titles[kind],apps:Array.from(new Set(visibleDetails.filter(e=>e.kind===kind).map(e=>e.app))),color:PrivacyPreferences.category(kind).color,priority:PrivacyPreferences.category(kind).priority})).filter(entry=>entry.apps.length>0).sort((a,b)=>a.priority-b.priority)
 readonly property bool active:entries.length>0
 readonly property bool islandActive:active && PrivacyPreferences.island
 readonly property bool controlCenterActive:active && PrivacyPreferences.controlCenter
 readonly property color indicatorColor:entries.length ? entries[0].color:'#ff9f0a'
 readonly property string summary:entries.map(entry=>entry.label+' · '+entry.apps.join(', ')).join('   •   ')
 function _parse(text){
  let data=[];try{data=JSON.parse(text)}catch(error){}
  const result=Capture.classify(data)
  detected=result.details;cameraApps=result.camera;micApps=result.mic;screenApps=result.screen;audioApps=result.audio
 }
 Process{id:dump;command:['pw-dump'];stdout:StdioCollector{onStreamFinished:root._parse(text)} onExited:code=>{if(code!==0)root._parse('[]')}}
 Timer{interval:1000;running:true;repeat:true;triggeredOnStart:true;onTriggered:if(!dump.running)dump.running=true}
}
