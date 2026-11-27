import QtQuick
import Quickshell
import qs.rosa.services
import qs.services as Native
QtObject {
 id:root
 property string kind:''
 property string label:''
 property real fraction:-1
 property var demo:({})
 property var context:({})
 property var notification:({})
 readonly property bool supported:!!kind && !['clock','voice','media','sys','shot','gta','jarvis'].includes(kind)
 readonly property var value:{
  const title=label || ({clip:qsTr('Clipboard'),keys:qsTr('Keyboard'),desk:qsTr('Workspace'),route:qsTr('Audio output'),focus:qsTr('Focus'),print:qsTr('Printing'),remind:qsTr('Reminder'),weather:qsTr('Weather'),launch:qsTr('Opening application'),cmd:qsTr('Command'),peri:qsTr('Device')}[kind] || qsTr('Activity'));
  const d={kind:kind,title:title,label:title,color:'#f5f5f7',fraction:fraction,icon:({timer:'clock',alarm:'bell',record:'video',bt:'bluetooth',peri:'battery',net:'wifi',vpn:'vpn',print:'file-text',clip:'clipboard',keys:'command',desk:'laptop',route:'headphones',focus:'moon',cmd:'terminal',task:'terminal',download:'download',remind:'bell',weather:'cloud',done:'check',fail:'x'}[kind] || 'bell')};
  if(kind==='osd'){d.meter=true;d.icon=Feedback.channel==='source' ? Feedback.flat ? 'mic-off':'mic':['light','brightness'].includes(Feedback.channel) ? 'sun':Feedback.flat ? 'volume-x':'volume-2';d.fraction=fraction>=0 ? fraction:Feedback.value;d.value=String(Math.round(d.fraction*100));d.color=Feedback.flat ? '#ff453a':['light','brightness'].includes(Feedback.channel) ? '#ffffff':'#30d158';d.title=Feedback.label}
  else if(['power','low'].includes(kind)){const p=demo.power;const percent=p ? p.pct:Power.percent;d.title=percent>=100 ? qsTr('Full Battery'):p ? p.charging ? qsTr('Charging'):qsTr('Battery'):Power.charging ? qsTr('Charging'):qsTr('Battery');d.label=d.title;d.value=percent+'%';d.color=percent<=15 ? '#ff453a':'#30d158';d.complete=percent>=100;d.subtitle=percent>=100 ? qsTr('Your computer is fully charged.'):''}
  else if(kind==='timer'){const t=demo.timer;d.title=t ? t.label:Timers.soonest ? Timers.soonest.label || qsTr('Timer'):qsTr('Timer');d.label=t ? Timers.clock(t.left):Timers.soonest ? Timers.clock(Timers.left(Timers.soonest)):'0:00';d.value=d.label;d.color='#ff9f0a';d.action='pause';d.fraction=t ? t.progress:Timers.soonest ? Timers.progress(Timers.soonest):0}
  else if(kind==='alarm'){d.color='#ff9f0a';d.title=qsTr('Alarm');d.label=label || qsTr('Alarm');d.action='dismiss'}
  else if(kind==='record'){d.title=demo.record ? demo.record.clock:Recorder.clock;d.label=d.title;d.subtitle=qsTr('Screen Recording');d.color='#ff453a';d.action='stop'}
  else if(kind==='vpn'){d.title=Vpn.up ? qsTr('Connected'):qsTr('Disconnected');d.subtitle=label || Vpn.iface;d.label=d.subtitle;d.value=Vpn.up ? Vpn.activityElapsed:qsTr('Off');d.color='#ff9f0a'}
  else if(kind==='net'){d.title=Network.connected || Network.wired ? qsTr('Connected'):qsTr('Disconnected');d.subtitle=label || Network.ssid;d.label=d.title;d.color='#30d158'}
  else if(kind==='bt'){const device=Bt.primary;const on=demo.bt ? demo.bt.on:Bt.connectedCount>0;const charge=demo.bt ? demo.bt.battery:device && device.batteryAvailable ? device.battery:-1;d.title=demo.bt ? demo.bt.name:Bt.label(device) || label;d.label=d.title;d.subtitle=on ? qsTr('Connected'):qsTr('Disconnected');d.value=on && charge>=0 ? Math.round(charge*100)+'%':'';d.color=on ? '#30d158':'#a1a1a6'}
  else if(kind==='notif'){d.title=notification.title || '';d.label=d.title;d.subtitle=notification.body || '';d.initials=d.title.split(' ').map(x=>x[0] || '').join('').substring(0,2);d.time=qsTr('now');d.image=notification.image || '';d.appIcon=notification.icon ? notification.icon.startsWith('/') || notification.icon.startsWith('file:') || notification.icon.startsWith('image:') ? notification.icon:Quickshell.iconPath(notification.icon,true):'';d.canReply=notification.canReply===true}
  else if(['cmdfail','taskfail','fail'].includes(kind)){d.color='#ff453a';d.title=label || qsTr('Failed');d.label=d.title;d.icon='x'}
  else if(kind==='cmd'){d.title=context.title || label || qsTr('Command');d.label=d.title;d.subtitle=context.result==='bad' ? qsTr('Failed'):qsTr('Completed');d.icon=context.result==='bad' ? 'x':'terminal';d.color=context.result==='bad' ? '#ff453a':'#30d158'}
  else if(kind==='task'){d.title=context.title || label || qsTr('Task');d.label=d.title;d.value=context.progress!==undefined && context.progress!==null ? Math.round(context.progress*100)+'%':context.result==='ok' ? qsTr('Done'):context.result==='bad' ? qsTr('Failed'):'';d.color=context.result==='bad' ? '#ff453a':context.result==='ok' ? '#30d158':'#a78bfa';d.icon=context.result==='ok' ? 'check':context.result==='bad' ? 'x':'terminal'}
  else if(['share','cloud'].includes(kind)){d.title=context.title || label || qsTr('Transfer');d.label=d.title;d.subtitle=context.subtitle || '';d.value=context.progress!==undefined && context.progress!==null ? Math.round(context.progress*100)+'%':'';d.icon=kind==='cloud' ? 'cloud':'link';d.color=kind==='cloud' ? '#a78bfa':'#30d158';if(context.progress===1 && (!context.status || context.status==='completed'))d.icon='check'}
  else if(kind==='download'){d.title=qsTr('Download');d.label=context.result==='ok' ? qsTr('Completed'):qsTr('Downloading');d.subtitle=context.title || label;d.color='#30d158';d.icon=context.result==='ok' ? 'check':'download'}
  else if(kind==='tray'){d.title=qsTr('File tray');d.label='';d.value=String(Native.ShelfState.items.length);d.icon='inbox';d.color='#30d158'}
  else if(kind==='done'){d.title=label || qsTr('Completed');d.label=d.title;d.color='#30d158'}
  else if(kind==='focus'){d.title=label || qsTr('Off');d.label=d.title;d.icon='moon'}
  d.channel=kind==='osd' ? Feedback.channel:'';
  d.muted=kind==='osd' && Feedback.flat;
  d.deviceType=context.deviceType || (demo.bt && demo.bt.type ? demo.bt.type:'') || (kind==='bt' && Bt.primary ? Bt.primary.icon:'') || '';
  d.status=context.result==='bad' || ['fail','cmdfail','taskfail'].includes(kind) ? 'failed':context.result==='ok' || d.complete || (['task','download','share','cloud'].includes(kind) && context.progress===1) ? 'completed':kind==='vpn' && !Vpn.up || kind==='net' && !Network.connected && !Network.wired || kind==='bt' && (demo.bt ? !demo.bt.on:Bt.connectedCount<=0) ? 'disconnected':kind==='timer' && Timers.soonest && !Timers.soonest.running && !demo.timer ? 'paused':'active';
  if(['active','completed','failed','paused','disconnected'].includes(context.status))d.status=context.status;
  if(context.status==='active' && ['task','download','share','cloud'].includes(kind))d.icon=({task:'terminal',download:'download',share:'link',cloud:'cloud'})[kind];
  if(d.status==='failed' && ['task','download','share','cloud'].includes(kind))d.value=qsTr('Failed');
  return d;
 }
 function action(name){if(kind==='tray' && name==='open'){Native.ShelfState.reveal(6);return;}if(Object.keys(demo).length)return;if(kind==='alarm' && name==='dismiss')Timers.dismissAll();if(kind==='record' && name==='stop')Recorder.stop();if(kind==='timer' && Timers.soonest && name==='pause')Timers.toggle(Timers.soonest.id)}
}
