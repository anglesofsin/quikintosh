.pragma library
// Pure and deterministic: no timers, name guessing, filesystem or service calls.
function resolve(spec, preferences, event, presentation) {
 const p=Object.assign({},spec.defaults,preferences || {}),e=event || {};
 for(const key in spec.defaults)if(typeof spec.defaults[key]==='boolean' && typeof p[key]!=='boolean')p[key]=spec.defaults[key];
 if(!p.iconPolicyOverrides || typeof p.iconPolicyOverrides!=='object' || Array.isArray(p.iconPolicyOverrides))p.iconPolicyOverrides={};
 const valid=name=>spec.icons.indexOf(name)>=0;
 const base={osd:'volume-2',power:'battery-status',low:'battery-status',timer:'clock',alarm:'bell',record:'video',vpn:'vpn',net:'wifi',bt:'bluetooth',peri:'battery',notif:'bell',cmd:'terminal',cmdfail:'x',task:'terminal',taskfail:'x',download:'download',share:'link',cloud:'cloud',tray:'inbox',done:'check',fail:'x',focus:'moon',route:'headphones',print:'file-text',clip:'clipboard',keys:'command',desk:'laptop',remind:'bell',weather:'cloud',launch:'grid'};
 let icon=valid(e.icon) ? e.icon:base[e.kind] || 'bell', color=/^#[0-9a-f]{6}([0-9a-f]{2})?$/i.test(String(e.color || '')) ? String(e.color):'#f5f5f7';
 const protectedKind=['record','power','low'].indexOf(e.kind)>=0;
 if(e.kind==='power' || e.kind==='low')icon='battery-status';
 if(p.iconPolicySmart){
  if(p.iconPolicyDevices && ['bt','peri','route'].indexOf(e.kind)>=0){
   const types={'audio-headset':'headphones','audio-headphones':'headphones','input-keyboard':'command',headset:'headphones',headphones:'headphones',phone:'smartphone',smartphone:'smartphone',computer:'laptop',laptop:'laptop',keyboard:'command',watch:'watch',speaker:'volume-2'};
   icon=types[e.deviceType] || (e.kind==='bt' && e.deviceType ? 'bluetooth':icon);
  }
  if(e.kind==='osd'){
   const channel=e.channel || '';
   if(channel==='source')icon=e.muted ? 'mic-off':'mic';
   else if(['light','brightness','keyboard'].indexOf(channel)>=0)icon='sun';
   else if(channel==='sink')icon=e.muted || e.fraction===0 ? 'volume-x':'volume-2';
  }
 }
 const override=(p.iconPolicyOverrides || {})[e.kind];
 if(valid(override) && !protectedKind)icon=override;
 // Status wins over optional event overrides unless the user turns it off.
 if(p.iconPolicySmart && p.iconPolicyStatus && !protectedKind){
  if(e.status==='failed')icon='x';
  else if(e.status==='completed' && ['task','download','share','cloud','cmd','launch','done'].indexOf(e.kind)>=0)icon='check';
  else if(e.status==='paused' && e.kind==='timer')icon='pause';
 }
 if(p.iconPolicySmart && p.iconPolicyStatus && !protectedKind && p.iconPolicyStatusOverrides && valid(p.iconPolicyStatusOverrides[e.status]))icon=p.iconPolicyStatusOverrides[e.status];
 if(p.iconPolicySmart && p.iconPolicyColors){
  if(e.status==='failed')color='#ff453a';
  else if(e.status==='disconnected')color='#a1a1a6';
 }
 const monochrome=!p.iconPolicyColors && !protectedKind;
 if(monochrome)color='#f5f5f7';
 const key=e.meter && presentation!=='satellite' ? 'iconPolicyMeterSize':presentation==='expanded' ? 'iconPolicyExpandedSize':presentation==='satellite' ? 'iconPolicySatelliteSize':'iconPolicyCompactSize';
 const bounds=spec.sizes[key];let size=p[key];if(typeof size!=='number' || !isFinite(size))size=spec.defaults[key];size=Math.max(bounds[0],Math.min(bounds[1],size));
 if(presentation==='satellite' && ['timer','download','cmd','task','print'].indexOf(e.kind)>=0)size=Math.min(16,size);
 if(presentation==='expanded' && e.kind==='vpn')size=Math.min(32,size+4);
 return {icon:valid(icon) ? icon:'bell',color:color,size:size,monochrome:monochrome,appBadges:p.iconPolicyAppBadges!==false};
}
