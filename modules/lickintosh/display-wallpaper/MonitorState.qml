pragma Singleton
import QtQuick
import Quickshell
import Quickshell.Io
import Quickshell.Hyprland
Singleton{
 id:root
 property var monitors:[]
 property var drafts:[]
 property var profiles:({})
 property var pending:null
 property bool loading:false
 property bool dirty:false
 property string error:''
 property int secondsLeft:0
 readonly property int activeCount:drafts.filter(s=>!s.disabled).length
 function spec(m){return {output:m.name,mode:m.width ? m.width+'x'+m.height+'@'+Number(m.refreshRate || 60).toFixed(3):'preferred',position:(m.x || 0)+'x'+(m.y || 0),scale:m.scale || 1,transform:m.transform || 0,disabled:!!m.disabled,mirror:m.mirrorOf && m.mirrorOf!=='none' ? m.mirrorOf:'',vrr:m.vrr ? 1:0,bitdepth:(m.currentFormat || '').includes('2101010') ? 10:8,cm:m.colorManagementPreset || 'auto'}}
 function send(data){if(loading)return;loading=true;error='';worker.write(JSON.stringify(data)+'\n')}
 function refresh(){send({action:'refresh'})}
 function reset(){drafts=monitors.map(spec);dirty=false}
 function update(output,patch){drafts=drafts.map(s=>s.output===output ? Object.assign({},s,patch):s);dirty=true}
 function apply(){send({action:'preview',specs:drafts})}
 function confirm(){if(pending)send({action:'confirm',token:pending.token})}
 function revert(){if(pending)send({action:'revert',token:pending.token})}
 function saveProfile(name){send({action:'save-profile',name:name,specs:drafts})}
 function deleteProfile(name){send({action:'delete-profile',name:name})}
 function loadProfile(name){if(profiles[name]){drafts=JSON.parse(JSON.stringify(profiles[name]));dirty=true}}
 function dimensions(s){const m=String(s.mode || "preferred").match(/^(\d+)x(\d+)/),raw=monitors.find(m=>m.name===s.output);let w=m ? Number(m[1]):(raw?.width || 1920),h=m ? Number(m[2]):(raw?.height || 1080);if(s.transform%2){const swap=w;w=h;h=swap}return {w:w/s.scale,h:h/s.scale}}
 function position(s){const m=String(s.position || "0x0").match(/^(-?\d+)x(-?\d+)$/);return {x:m ? Number(m[1]):0,y:m ? Number(m[2]):0}}
 function beside(output,other,direction){const a=drafts.find(s=>s.output===output),b=drafts.find(s=>s.output===other);if(!a || !b)return;const p=position(b),ad=dimensions(a),bd=dimensions(b);update(output,{position:Math.round(p.x+(direction==='right' ? bd.w:direction==='left' ? -ad.w:0))+'x'+Math.round(p.y+(direction==='below' ? bd.h:direction==='above' ? -ad.h:0))})}
 Process{
  id:worker;running:true;command:['@PYTHON@',Quickshell.shellDir+'/tools/display-manager.py']
  stdout:SplitParser{onRead:line=>{try{const e=JSON.parse(line);if(e.ready){root.send({action:'restore'});return}root.loading=false;if(!e.ok){root.error=e.error;return}if(e.monitors)root.monitors=e.monitors;if(e.profiles)root.profiles=e.profiles;root.pending=e.pending || null;if(e.monitors && !root.pending)root.reset();tick.triggered()}catch(err){root.loading=false;root.error=String(err)}}}
  onExited:code=>{root.loading=false;if(code!==0)root.error='Display service stopped'}
 }
 Timer{id:tick;interval:500;running:root.pending!==null;repeat:true;onTriggered:{if(!root.pending)return;root.secondsLeft=Math.max(0,Math.ceil(root.pending.deadline-Date.now()/1000));if(root.secondsLeft===0 && !root.loading)root.refresh()}}
 Timer{id:hotplug;interval:700;onTriggered:if(!root.dirty && !root.pending)root.refresh()}
 Connections{target:Hyprland;function onRawEvent(event){if(event.name==='configreloaded' && !root.dirty && !root.pending && !root.loading){root.send({action:'restore'});return}if(['monitoradded','monitorremoved','monitoraddedv2'].includes(event.name))hotplug.restart()}}
}
