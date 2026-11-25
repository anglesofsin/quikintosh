import QtQuick
import QtQuick.Controls
import QtQuick.Layouts
import Quickshell
import Quickshell.Io
import qs.services
import qs.components
import qs.settingsapp
ScrollView{
 id:root
 property string pageId:'general'
 property string selectedApp:''
 property string selectedPermissionApp:''
 property string serverName:''
 property string serverAddress:''
 signal navigate(string page)
 readonly property var current:SettingsCatalog.page(pageId)
 readonly property var stateData:SettingsState.data
 readonly property var apps:stateData.apps?.apps || []
 readonly property var notificationApps:Array.from(new Set(SettingsPreferences.notifications.appNames.concat(apps.map(app=>app.name)))).sort((a,b)=>a.localeCompare(b))
 readonly property string notificationApp:selectedApp || notificationApps[0] || ''
 readonly property var sections:build()
 readonly property string helpText:sections.map(section=>section.footer).filter(Boolean).join('\n\n')
 clip:true;contentWidth:availableWidth;contentHeight:column.implicitHeight+40
 ScrollBar.horizontal.policy:ScrollBar.AlwaysOff
 function row(label,kind,extra){return Object.assign({id:label,label:label,kind:kind || 'info'},extra || {})}
 function card(title,rows,footer){return {id:title || pageId,title:title,rows:rows || [],footer:footer || ''}}
 function nav(id){const page=SettingsCatalog.page(id);return row(page.title,'navigate',{action:'navigate',target:id})}
 function info(label,value){return row(label,'info',{value:value===undefined || value===null || value==='' ? 'Not available':String(value)})}
 function toggle(label,checked,action,extra){return row(label,'switch',Object.assign({checked:!!checked,action:action},extra || {}))}
 function choice(label,choices,index,action,extra){return row(label,'choice',Object.assign({choices:choices,selection:Math.max(0,index),action:action},extra || {}))}
 function button(label,caption,action,extra){return row(label,'button',Object.assign({buttonText:caption,action:action},extra || {}))}
 function pref(label,group,key,kind,extra){const value=SettingsPreferences[group][key];return row(label,kind,Object.assign({action:'pref',group:group,key:key,checked:value,value:String(value),number:Number(value)},extra || {}))}
 function input(label,key,kind,extra){const value=SettingsPreferences.inputOverrides[key]===undefined ? stateData.input?.values?.[key]:SettingsPreferences.inputOverrides[key];return row(label,kind,Object.assign({action:'input',key:key,number:Number(value),checked:!!value,value:value===undefined ? '':String(value),available:value!==undefined},extra || {}))}
 function permissionSelection(){if(pageId!=='app-permissions')return;const id=selectedPermissionApp || stateData.privacy?.flatpaks?.[0]?.id;if(id && stateData.permissions?.app!==id)SettingsState.query('permissions',false,{app:id})}
 function refresh(){const name=current?.query;if(name)SettingsState.query(name);if(['account','about'].includes(pageId))SettingsState.query('system');if(pageId==='notifications')SettingsState.query('apps');if(pageId==='sound')SettingsState.query('audio');if(pageId==='games')SettingsState.query('main');if(pageId==='shortcuts')SettingsState.query('shortcuts');permissionSelection()}
 Component.onCompleted:refresh()
 onPageIdChanged:{selectedApp='';selectedPermissionApp='';Qt.callLater(root.refresh)}
 Connections{target:SettingsState;function onReadyChanged(){root.refresh()}function onDataChanged(){root.permissionSelection()}function onCompleted(name,result){if(['audio-volume','audio-mute','audio-default'].includes(name))SettingsState.query('audio',true);if(name==='default-app'){const next=Object.assign({},SettingsPreferences.defaultApps);next[result.mime]=result.app;SettingsPreferences.defaultApps=next;SettingsState.query('apps',true);}if(name==='login-toggle')SettingsState.query('login',true);if(name.startsWith('network-'))SettingsState.query('network',true);if(name==='printer-default')SettingsState.query('printers',true);if(name==='flatpak-permission'){const id=root.selectedPermissionApp || root.stateData.privacy?.flatpaks?.[0]?.id;if(id)SettingsState.query('permissions',true,{app:id})}if(name==='usage-clear')SettingsState.query('usage',true);if(name==='shortcut-save')SettingsState.query('shortcuts',true)}}
 Timer{interval:2000;repeat:true;running:root.pageId==='sound' && root.visible && !!QsWindow.window?.visible;onTriggered:SettingsState.query('audio',true)}
 function build(){
  const sys=stateData.system || {},cap=sys.capabilities || {},result=[]
  if(pageId==='general'){
   result.push(card('',SettingsCatalog.childPages('general').map(page=>nav(page.id))))
  }else if(pageId==='account'){
   result.push(card('Profile',[
    pref('Display Name','profile','displayName','field',{value:SettingsPreferences.profile.displayName || sys.fullName || '',description:'The name shown by Lickintosh.'}),
    pref('Account Picture','profile','avatar','field',{description:'Path to your profile picture.'}),info('User Name',sys.user),info('Home Folder',sys.home)
   ]))
   result.push(card('Sign-In & Security',[button('Login Password','Change Password…','password'),nav('users'),nav('passwords')],'Your local Linux account is used here. Apple Account and iCloud sign-in require macOS.'))
  }else if(pageId==='about'){
   result.push(card('Hardware',[info('Model',sys.model || sys.vendor),info('Processor',sys.cpu),info('Memory',SettingsState.bytes(sys.memory)),info('Architecture',sys.architecture)]))
   result.push(card('System',[info('Operating System',sys.os),info('Kernel',sys.kernel),info('Computer Name',sys.hostname),nav('updates'),nav('storage')]))
  }else if(pageId==='updates'){
   const checked=stateData['update-check'] || stateData.updates?.check || {}
   result.push(card('Software Update',[
    info('Installed Version',stateData.updates?.system || sys.os),
    info('Last Checked',checked.checkedAt || 'Not checked'),
    info('Available Updates',checked.changes ? String(checked.changes.length)+' updated inputs':'Check for updates to see available versions'),
    button('Check for Updates',stateData && SettingsState.loading['update-check'] ? 'Checking…':'Check Now','check-updates',{available:!SettingsState.loading['update-check']}),
    button('Install System Updates','Review Update…','upgrade',{available:!!checked.changes?.length})
   ],'System updates are managed by NixOS and apply to every desktop profile. Installation opens the existing authenticated update workflow.'))
   if(checked.changes?.length)result.push(card('Available',checked.changes.map(item=>info(item.input,String(item.after || '').slice(0,12)))))
  }else if(pageId==='storage'){
   const disk=stateData['storage-details'] || stateData.storage || {}
   result.push(card('Storage',[info('Used',SettingsState.bytes(disk.used)),info('Available',SettingsState.bytes(disk.free)),info('Capacity',SettingsState.bytes(disk.total)),button('Storage Categories',SettingsState.loading['storage-details'] ? 'Calculating…':'Calculate Sizes','storage-details',{available:!SettingsState.loading['storage-details']})]))
   if(disk.folders?.length)result.push(card('Documents & Files',disk.folders.map(item=>row(item.name,'navigate',{value:SettingsState.bytes(item.size),action:'folder',target:item.path})),'Select a category to open it in Finder.'))
  }else if(pageId==='defaults'){
   const labels={'x-scheme-handler/http':'Default web browser','x-scheme-handler/mailto':'Email','text/plain':'Text documents','application/pdf':'PDF documents','image/png':'PNG images','video/mp4':'MP4 videos','audio/mpeg':'MP3 audio'}
   result.push(card('Default Applications',Object.keys(labels).map(mime=>choice(labels[mime],apps.map(a=>a.name),apps.findIndex(a=>a.id===stateData.apps?.defaults?.[mime]),'default-app',{mime:mime,available:apps.length>0})), 'These application associations belong to the Lickintosh desktop profile.'))
  }else if(pageId==='login'){
   result.push(card('Open at Login',(stateData.login?.items || []).map(item=>toggle(item.name,item.enabled,'login-toggle',{target:item.id,description:item.description})), 'Choose which applications start when you sign in. The original login-item preferences are restored when leaving this rice.'))
   if(!stateData.login?.items?.length)result.push(card('Login Items',[info('Applications','No desktop autostart entries found')]))
  }else if(pageId==='datetime'){
   result.push(card('Date & Time',[info('Current Date',stateData.datetime?.date),info('Time Zone',stateData.datetime?.Timezone),info('Automatic Time',stateData.datetime?.NTP==='yes' ? 'On':'Off'),info('Clock Synchronization',stateData.datetime?.NTPSynchronized==='yes' ? 'Synchronized':'Not synchronized')],'The system clock is managed by NixOS. Display formatting is configured separately for this shell.'))
   result.push(card('Clock Display',[row('Date & Time Format','field',{value:ShellConfig.options.topbar.clockFormat,action:'clock-format',description:'Example: ddd d MMM HH:mm'}),nav('menubar')]))
  }else if(pageId==='language'){
   result.push(card('Preferred Language',[choice('Shell Language',['Automatic','English','Français','Español'],['auto','en','fr','es'].indexOf(ShellConfig.options.general.language),'language'),info('System Locale',stateData.datetime?.locale)],'The shell language is separate from the languages used by your applications.'))
  }else if(['network','vpn','sharing'].includes(pageId)){
   const network=stateData.network || {},profiles=network.profiles || [],vpn=profiles.filter(p=>['vpn','wireguard'].includes(p.type))
   if(pageId==='sharing')result.push(card('Sharing',[info('Computer Name',network.hostname),button('Network Folders','Open Finder…','folder',{target:'network:///'})],'Sharing services and the computer name are managed by your NixOS configuration.'))
   else if(pageId==='network')result.push(card('Network Services',(network.devices || []).filter(d=>d.type!=='loopback').map(d=>info(d.device,d.state+' · '+d.connection))))
   if(pageId!=='sharing')result.push(card(pageId==='vpn' ? 'VPN Configurations':'Saved Connections',(pageId==='vpn' ? vpn:profiles).map(p=>toggle(p.name,!!p.device && p.device!=='--','network-profile',{target:p.uuid,description:p.type})), 'Network connections are shared by this computer.'))
   if(pageId==='vpn' && !vpn.length)result.push(card('VPN',[info('Configurations','No VPN profile configured')]))
   result.push(card('Configuration',[button('Connections','Edit Connections…','network-editor',{available:cap.networkEditor})]))
  }else if(pageId==='sound'){
   const audio=stateData.audio || {},out=audio.output || {},source=audio.input || {},outputs=audio.outputs || [],inputs=audio.inputs || []
   result.push(card('Output',[
    choice('Select a device for sound output',outputs.map(n=>n.name),outputs.findIndex(n=>n.id===out.id),'audio-output',{available:outputs.length>0}),
    row('Output volume','slider',{number:out.volume || 0,value:Math.round((out.volume || 0)*100)+'%',minimum:0,maximum:1,step:.01,action:'audio-volume',target:'output',available:!!out.available}),
    toggle('Mute',out.muted,'audio-mute',{target:'output',available:!!out.available})
   ]))
   result.push(card('Input',[
    choice('Select a device for sound input',inputs.map(n=>n.name),inputs.findIndex(n=>n.id===source.id),'audio-input',{available:inputs.length>0}),
    row('Input volume','slider',{number:source.volume || 0,minimum:0,maximum:1,step:.01,action:'audio-volume',target:'input',available:!!source.available}),
    toggle('Mute microphone',source.muted,'audio-mute',{target:'input',available:!!source.available})
   ]))
  }else if(pageId==='notifications'){
   result.push(card('Notification Settings',[
    pref('Allow Notification Banners','notifications','banners','switch'),
    pref('Show Notifications on Lock Screen','notifications','showOnLock','switch'),
    choice('Show Previews',['Always','When Unlocked','Never'],['always','unlocked','never'].indexOf(SettingsPreferences.notifications.previews),'preview'),
    pref('Banner Duration','notifications','duration','slider',{minimum:2000,maximum:15000,step:1000,description:'Time before a notification banner disappears.'})
   ]))
   result.push(card('Application Notifications',[
    choice('Application',notificationApps,notificationApps.indexOf(notificationApp),'notification-app',{available:notificationApps.length>0}),
    toggle('Allow Notifications',SettingsPreferences.appRule(notificationApp).allowed!==false,'app-rule',{key:'allowed',available:!!notificationApp}),
    toggle('Show Banners',SettingsPreferences.appRule(notificationApp).banners!==false,'app-rule',{key:'banners',available:!!notificationApp})
   ]))
  }else if(pageId==='focus'){
   result.push(card('Do Not Disturb',[
    toggle('Do Not Disturb',ShellConfig.options.session.focus,'dnd'),
    choice('Turn Off',['Manually','In 1 Hour','This Evening'],SettingsPreferences.focus.endAt>0 ? 1:0,'focus-duration'),
    pref('Allow Critical Alerts','focus','allowCritical','switch')
   ]))
   result.push(card('Set a Schedule',[
    pref('Scheduled','focus','schedule','switch'),pref('From','focus','start','field',{description:'24-hour time, for example 22:00'}),pref('To','focus','end','field',{description:'Schedules can continue past midnight.'})
   ],'The schedule runs while Lickintosh is active.'))
   result.push(card('Repeat',['Sunday','Monday','Tuesday','Wednesday','Thursday','Friday','Saturday'].map((day,index)=>toggle(day,SettingsPreferences.focus.days.includes(index),'focus-day',{target:index}))))
  }else if(pageId==='accessibility'){
   result.push(card('Vision & Display',[
    pref('Reduce Motion','accessibility','reduceMotion','switch'),pref('Reduce Transparency','accessibility','reduceTransparency','switch'),
    pref('Increase Contrast','accessibility','increaseContrast','switch'),
    pref('Interface Size','accessibility','textScale','slider',{minimum:.85,maximum:1.5,step:.05,description:'Scale the Settings interface and its text.'}),
    nav('mouse'),nav('keyboard'),nav('displays')
   ],'These accessibility preferences apply to this shell.'))
  }else if(pageId==='activity'){
   result.push(card('App & Website Activity',[
    pref('App Activity','activity','enabled','switch',{description:'Count time spent in the foreground app while Lickintosh is active.'}),
    button('Activity History','Clear History…','usage-clear',{available:SettingsPreferences.activity.enabled || Object.keys(stateData.usage || {}).length>0})
   ],'Only application identifiers and durations are stored locally. Window titles and browsing history are not recorded.'))
   const today=Qt.formatDate(new Date(),'yyyy-MM-dd'),usage=stateData.usage?.[today] || {}
   result.push(card('Today',Object.keys(usage).sort((a,b)=>usage[b]-usage[a]).map(app=>info(app,Math.round(usage[app]/60)+' min'))))
   if(!Object.keys(usage).length)result.push(card('Activity',[info('Today',SettingsPreferences.activity.enabled ? 'No activity recorded yet':'App Activity is turned off')]))
  }else if(pageId==='users'){
   result.push(card('Users',(stateData.users?.users || []).map(user=>row(user.fullName || user.name,'info',{value:user.current ? 'Current User':user.name,description:user.name+' · '+user.home})), 'System accounts and administrator membership are managed by NixOS.'))
   result.push(card('Your Account',[nav('account'),button('Login Password','Change Password…','password')]))
  }else if(pageId==='privacy'){
   result.push(card('Privacy',[nav('app-permissions'),nav('passwords'),info('Camera Devices',(stateData.privacy?.cameras || []).join(', ') || 'No camera detected')]))
   result.push(card('Active Media Access',(stateData.privacy?.streams || []).map(stream=>info(stream.name,stream.media)), 'Audio and screen permissions are provided by PipeWire, portals and each application.'))
   result.push(card('Security',[nav('auto-lock'),nav('updates')]))
  }else if(pageId==='app-permissions'){
   const flatpaks=stateData.privacy?.flatpaks || [],id=selectedPermissionApp || flatpaks[0]?.id || '',permissions=stateData.permissions?.app===id ? stateData.permissions.context || {}:{}
   const shares=String(permissions.shared || '').split(';'),files=String(permissions.filesystems || '').split(';')
   result.push(card('Sandboxed Applications',[choice('Application',flatpaks.map(a=>a.name),flatpaks.findIndex(a=>a.id===id),'permission-app',{available:flatpaks.length>0})], 'User overrides are isolated to the Lickintosh rice and restored when leaving it.'))
   if(id)result.push(card('Access',[
    toggle('Network',!!stateData.permissions?.grants?.network,'permission',{permission:'network',target:id}),
    toggle('Home Folder',!!stateData.permissions?.grants?.home,'permission',{permission:'home',target:id}),
    toggle('Downloads Folder',!!stateData.permissions?.grants?.downloads,'permission',{permission:'downloads',target:id})
   ],'Restart the application after changing sandbox permissions.'))
   else result.push(card('Applications',[info('Flatpak','No sandboxed application is installed')]))
  }else if(pageId==='passwords'){
   result.push(card('Passwords & Keys',[button('Your Keyring','Open Passwords…','passwords',{available:cap.passwords}),button('Login Password','Change Password…','password')], 'Credentials remain in the system keyring. Lickintosh does not copy or display saved passwords.'))
  }else if(pageId==='accounts'){
   result.push(card('Connected Servers',Array.from(SettingsPreferences.servers).reduce((rows,server,index)=>rows.concat([row(server.name,'navigate',{action:'server-open',target:server.url,value:server.url}),button('Remove '+server.name,'Remove','server-remove',{target:index})]),[]), 'Connect to SFTP, SMB or WebDAV servers through Finder. Authentication is handled by the file manager.'))
   result.push(card('Add a Server',[
    row('Name','field',{value:serverName,action:'server-name'}),row('Server Address','field',{value:serverAddress,action:'server-address',description:'sftp://host, smb://host/share or davs://host/folder'}),
    button('Connect','Connect…','server-add',{available:!!serverAddress})
   ],'Apple Account, iCloud and Exchange sign-in depend on their respective account providers and are not emulated.'))
  }else if(pageId==='games'){
   result.push(card('Game Mode',[toggle('Game Mode',stateData.main?.gameMode,'game-mode'),button('Game Library','Open Steam','steam',{available:cap.steam})], 'Game Mode uses the shell’s existing performance controls.'))
  }else if(['keyboard','mouse','trackpad'].includes(pageId)){
   if(pageId==='keyboard'){
    const layout=SettingsPreferences.inputOverrides['input:kb_layout'] || stateData.input?.values?.['input:kb_layout'] || 'us'
    result.push(card('Keyboard',[
     input('Key Repeat Rate','input:repeat_rate','slider',{minimum:10,maximum:100,step:1}),
     input('Delay Until Repeat','input:repeat_delay','slider',{minimum:100,maximum:1000,step:25}),
     choice('Input Source',['English (US)','Português (Brasil)','Português','English (UK)','Deutsch','Français','Español'],['us','br','pt','gb','de','fr','es'].indexOf(layout),'input-layout'),
     input('Input Source Variant','input:kb_variant','field'),nav('shortcuts')
    ]))
   }else if(pageId==='mouse'){
    const accel=SettingsPreferences.inputOverrides['input:accel_profile'] || stateData.input?.values?.['input:accel_profile'] || 'flat'
    result.push(card('Point & Click',[
     input('Tracking Speed','input:sensitivity','slider',{minimum:-1,maximum:1,step:.05}),
     choice('Pointer Acceleration',['Off','Adaptive'],accel==='adaptive' ? 1:0,'input-accel'),
     input('Natural Scrolling','input:natural_scroll','switch'),input('Scrolling Speed','input:scroll_factor','slider',{minimum:.1,maximum:3,step:.1}),
     input('Hide Pointer After Inactivity','cursor:inactive_timeout','slider',{minimum:0,maximum:30,step:1})
    ]))
   }else{
    result.push(card('Trackpad',[
     input('Tap to Click','input:touchpad:tap-to-click','switch'),input('Natural Scrolling','input:touchpad:natural_scroll','switch'),
     input('Disable While Typing','input:touchpad:disable_while_typing','switch'),input('Two-Finger Secondary Click','input:touchpad:clickfinger_behavior','switch'),
     input('Scrolling Speed','input:touchpad:scroll_factor','slider',{minimum:.1,maximum:3,step:.1})
    ]))
   }
   result.push(card('Profile',[button('Restore Input Settings','Restore Original Settings','input-reset')],'Input overrides are active only in Lickintosh and are restored when switching to another rice.'))
  }else if(pageId==='shortcuts'){
   const shortcuts=stateData.shortcuts?.items || []
   result.push(card('Quickintosh',shortcuts.filter(item=>item.editable).map(item=>
    row(item.name,'field',{value:item.key,action:'shortcut-save',target:item.name}))
    .concat([button('Restore shortcuts','↶ Restore Defaults','shortcut-reset',{available:!!stateData.shortcuts?.customized})])))
   result.push(card('Hyprland',shortcuts.filter(item=>!item.editable).map(item=>info(item.name,item.key))))
  }else if(pageId==='printers'){
   result.push(card('Printers',(stateData.printers?.printers || []).map(printer=>button(printer.name,printer.name===stateData.printers.default ? 'Default':'Make Default','printer-default',{target:printer.name,description:printer.status,available:printer.name!==stateData.printers.default}))))
   if(!stateData.printers?.printers?.length)result.push(card('Printers',[info('Printers',stateData.printers?.available ? 'No printer has been added':'The printing service is not running')]))
   result.push(card('Print & Scan',[button('Manage Printers','Open Printing…','printing',{available:!!stateData.printers?.available}),button('Scan Documents','Open Scanner…','scanner',{available:cap.scanner})]))
   if(stateData.printers?.jobs?.length)result.push(card('Print Queue',stateData.printers.jobs.map((job,index)=>info('Job '+(index+1),job))))
  }else if(pageId==='backups'){
   result.push(card('Back Up Files',[button('File Backups','Set Up Backup…','backups',{available:cap.backups})], 'Use the backup manager to choose folders, an archive location and a backup schedule.'))
   result.push(card('System Generations',(stateData.updates?.generations || []).map(generation=>info(generation.name,generation.date)), 'NixOS generations restore system configuration. They are separate from backups of your personal files.'))
  }else if(pageId==='auto-lock'){
   result.push(card('Automatic Locking',[
    pref('Lock Automatically When Idle','session','autoLock','switch'),
    pref('Start After','session','lockAfter','slider',{minimum:60,maximum:3600,step:60,description:Math.round(SettingsPreferences.session.lockAfter/60)+' minutes'})
   ],'This timer applies while Lickintosh is running. Any independent system idle policy still applies.'))
  }else if(pageId==='appearance'){
   result.push(card('Appearance',[
    choice('Appearance',['Light','Dark','Automatic'],SettingsPreferences.profile.autoAppearance ? 2:Theme.isLight ? 0:1,'appearance'),
    choice('Liquid Glass',['Clear','Tinted'],Theme.glassValue('*','tintAlpha')>.45 ? 1:0,'glass-look'),
    row('Accent Color','field',{value:String(Theme.accent),action:'accent',description:'A hexadecimal color, for example #0a84ff.'}),
    choice('Icon & Widget Style',['Automatic','Full Color','Clear','Tinted'],['auto','color','clear','tinted'].indexOf(WidgetState.widgetStyle),'widget-style'),
    toggle('Tint Dock Icons',ShellConfig.options.dockAppearance.iconTint,'dock-tint'),nav('glass')
   ]))
  }
  return result
 }
 function apply(row,value){
  const name=row.action
  if(name==='navigate'){navigate(row.target);return}
  if(name==='pref'){
   if(['start','end'].includes(row.key) && !/^([01]\d|2[0-3]):[0-5]\d$/.test(value)){SettingsState.error='Enter a valid time in 24-hour format.';return}
   SettingsPreferences[row.group][row.key]=value;return
  }
  if(name==='shortcut-save'){SettingsState.change(name,{label:row.target,value:value});return}
  if(name==='shortcut-reset'){SettingsState.change('shortcut-save',{reset:true});return}
  if(name==='input'){SettingsPreferences.input(row.key,value);return}
  if(name==='input-reset'){SettingsPreferences.inputOverrides=({});return}
  if(name==='input-layout'){const next=Object.assign({},SettingsPreferences.inputOverrides);next['input:kb_layout']=['us','br','pt','gb','de','fr','es'][value];next['input:kb_variant']='';SettingsPreferences.inputOverrides=next;return}
  if(name==='input-accel'){SettingsPreferences.input('input:accel_profile',value===1 ? 'adaptive':'flat');return}
  if(name==='folder'){SettingsState.open(['lickintosh-finder',row.target]);return}
  if(name==='clock-format'){ShellConfig.options.topbar.clockFormat=value;return}
  if(name==='language'){ShellConfig.options.general.language=['auto','en','fr','es'][value];return}
  if(name==='notification-app'){selectedApp=notificationApps[value];return}
  if(name==='app-rule'){SettingsPreferences.rule(notificationApp,row.key,value);return}
  if(name==='preview'){SettingsPreferences.notifications.previews=['always','unlocked','never'][value];return}
  if(name==='focus-day'){const days=SettingsPreferences.focus.days.filter(day=>day!==row.target);if(value)days.push(row.target);SettingsPreferences.focus.days=days.sort();return}
  if(name==='dnd'){ShellConfig.options.session.focus=value;if(!value)SettingsPreferences.focus.endAt=0;return}
  if(name==='focus-duration'){const date=new Date();if(value===2)date.setHours(20,0,0,0);SettingsPreferences.focus.endAt=value===0 ? 0:value===1 ? Date.now()+3600000:Math.max(Date.now()+60000,date.getTime());return}
  if(name==='usage-clear'){confirmAction='usage-clear';confirmText='Clear the locally recorded app activity?';confirmation.open();return}
  if(name==='default-app'){const app=apps[value];if(app)SettingsState.change('default-app',{mime:row.mime,app:app.id});return}
  if(name==='storage-details'){SettingsState.query('storage-details',true);return}
  if(name==='check-updates'){SettingsState.query('update-check',true);return}
  if(name==='upgrade'){confirmAction='upgrade';confirmText='Review and install updates for this NixOS system? All desktop profiles use the resulting system configuration.';confirmation.open();return}
  if(name==='login-toggle'){SettingsState.change(name,{id:row.target,enabled:value});return}
  if(name==='network-profile'){SettingsState.change(value ? 'network-up':'network-down',{uuid:row.target});return}
  if(name==='audio-output' || name==='audio-input'){const list=name==='audio-output' ? stateData.audio.outputs:stateData.audio.inputs;SettingsState.change('audio-default',{id:list[value].id});return}
  if(name==='audio-volume' || name==='audio-mute'){SettingsState.change(name,{target:row.target,value:value});return}
  if(name==='permission-app'){selectedPermissionApp=stateData.privacy.flatpaks[value].id;SettingsState.query('permissions',true,{app:selectedPermissionApp});return}
  if(name==='permission'){SettingsState.change('flatpak-permission',{app:row.target,permission:row.permission,enabled:value});return}
  if(name==='printer-default'){SettingsState.change(name,{name:row.target});return}
  if(name==='server-name'){serverName=value;return}
  if(name==='server-address'){serverAddress=value;return}
  if(name==='server-remove'){SettingsPreferences.servers=SettingsPreferences.servers.filter((item,index)=>index!==row.target);return}
  if(name==='server-open'){SettingsState.change('open-server',{url:row.target});return}
  if(name==='server-add'){const authority=serverAddress.split('://')[1]?.split('/')[0] || '';if(authority.includes('@') && authority.split('@')[0].includes(':')){SettingsState.error='Enter a server address without a password.';return}if(!/^(sftp|smb|davs?|ftp):\/\/[^\s]+$/.test(serverAddress)){SettingsState.error='Enter a supported server address.';return}SettingsPreferences.servers=SettingsPreferences.servers.concat([{name:serverName || serverAddress,url:serverAddress}]);SettingsState.change('open-server',{url:serverAddress});return}
  if(name==='game-mode'){SettingsState.open(['lickintosh','ipc','call','rice','gameMode']);return}
  if(name==='appearance'){SettingsPreferences.profile.autoAppearance=value===2;if(value<2)Theme.setMode(value===0 ? 'light':'dark');return}
  if(name==='glass-look'){Theme.setGlassParam('*','tintAlpha',value===0 ? .12:.62);return}
  if(name==='accent'){if(/^#[0-9a-fA-F]{6}$/.test(value))Theme.setAccent(value);else SettingsState.error='Enter a valid hexadecimal color.';return}
  if(name==='widget-style'){WidgetState.widgetStyle=['auto','color','clear','tinted'][value];return}
  if(name==='dock-tint'){ShellConfig.options.dockAppearance.iconTint=value;return}
  const commands={password:['kitty','--title','Change Password','-e','passwd'],passwords:['seahorse'],backups:['pika-backup'],scanner:['simple-scan'],'network-editor':['nm-connection-editor'],steam:['steam']}
  if(commands[name]){SettingsState.open(commands[name]);return}
  if(name==='printing')Qt.openUrlExternally('http://localhost:631/printers/')
 }
 property string confirmAction:''
 property string confirmText:''
 Dialog{
  id:confirmation;parent:Overlay.overlay;anchors.centerIn:parent;width:420;height:Math.max(180,confirmLabel.implicitHeight+120);modal:true;focus:true;padding:22;header:null
  background:Rectangle{radius:18;color:Theme.isLight ? '#fafafa':'#292a30';border.width:1;border.color:Theme.panelRim}
  ColumnLayout{anchors.fill:parent;spacing:18
   Text{id:confirmLabel;Layout.fillWidth:true;text:root.confirmText;color:Theme.textPrimary;font.pixelSize:13;wrapMode:Text.WordWrap}
   RowLayout{Layout.alignment:Qt.AlignRight;TahoeButton{text:'Cancel';onClicked:confirmation.close()}TahoeButton{text:'Continue';highlighted:true;onClicked:{confirmation.close();if(root.confirmAction==='upgrade')SettingsState.open(['kitty','--title','Software Update','-e','nix','upgrade','--all']);else SettingsState.change('usage-clear',{})}}}
  }
 }
 ColumnLayout{
  id:column;width:root.availableWidth-48;x:24;y:12;spacing:22
  Loader{
   Layout.fillWidth:true;Layout.preferredHeight:active ? 142:0;active:root.pageId==='appearance';visible:active
   sourceComponent:RowLayout{
    spacing:16
    Repeater{model:['Light','Dark','Automatic'];delegate:ColumnLayout{
     required property string modelData;required property int index;Layout.fillWidth:true;spacing:9
     readonly property bool selected:SettingsPreferences.profile.autoAppearance ? index===2:index===(Theme.isLight ? 0:1)
     Rectangle{
      Layout.fillWidth:true;Layout.preferredHeight:96;radius:11;color:index===1 ? '#232428':'#e5e6ed';border.width:selected ? 3:1;border.color:selected ? Theme.accent:'#50696a72'
      Rectangle{x:12;y:12;width:parent.width-24;height:parent.height-24;radius:7;color:index===1 ? '#3d3d43':'#fafafa';border.width:1;border.color:'#30505050'
       Rectangle{anchors{left:parent.left;top:parent.top;bottom:parent.bottom}width:parent.width*.28;radius:7;color:index===1 ? '#55555d':'#d0d3df'}
       Text{anchors.centerIn:parent;text:'Aa';font.family:'SF Pro Display';font.pixelSize:23;color:index===1 ? 'white':'#30313b'}
       Rectangle{visible:index===2;anchors{right:parent.right;top:parent.top;bottom:parent.bottom}width:parent.width*.4;radius:7;color:'#34343c';Text{anchors.centerIn:parent;text:'Aa';font.pixelSize:19;color:'white'}}
      }
      MouseArea{anchors.fill:parent;cursorShape:Qt.PointingHandCursor;onClicked:root.apply({action:'appearance'},index)}
     }
     Text{Layout.alignment:Qt.AlignHCenter;text:modelData;color:Theme.textPrimary;font.pixelSize:12}
    }}
   }
  }
  Loader{
   Layout.fillWidth:true;Layout.preferredHeight:active ? 160:0;active:['account','about','storage'].includes(root.pageId);visible:active
   sourceComponent:Item{
    ColumnLayout{anchors.centerIn:parent;spacing:9
     ProfileAvatar{visible:root.pageId==='account';Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:72;Layout.preferredHeight:72;source:(SettingsPreferences.profile.avatar || root.stateData.system?.avatar) ? QuickLookState.urlFor(SettingsPreferences.profile.avatar || root.stateData.system.avatar):IconResolver.byName('avatar-default')}
     Image{visible:root.pageId!=='account';Layout.alignment:Qt.AlignHCenter;Layout.preferredWidth:72;Layout.preferredHeight:72;source:root.pageId==='account' && (SettingsPreferences.profile.avatar || root.stateData.system?.avatar) ? QuickLookState.urlFor(SettingsPreferences.profile.avatar || root.stateData.system.avatar):IconResolver.byName(root.pageId==='storage' ? 'drive-harddisk':root.pageId==='account' ? 'avatar-default':'computer');sourceSize:Qt.size(144,144);fillMode:Image.PreserveAspectFit;asynchronous:true}
     Text{Layout.alignment:Qt.AlignHCenter;text:root.pageId==='storage' ? SettingsState.bytes(root.stateData.storage?.total):root.pageId==='account' ? SettingsPreferences.profile.displayName || root.stateData.system?.fullName || 'Your Account':root.stateData.system?.hostname || 'This Computer';font.family:'SF Pro Display';font.pixelSize:22;font.weight:Font.DemiBold;color:Theme.textPrimary}
     Text{Layout.alignment:Qt.AlignHCenter;text:root.pageId==='storage' ? SettingsState.bytes(root.stateData.storage?.free)+' available':root.pageId==='account' ? 'Local Account':root.stateData.system?.os || '';font.pixelSize:12;color:Theme.textSecondary}
    }
   }
  }
  Repeater{
   model:ScriptModel{values:root.sections;objectProp:'id'}
   delegate:SettingsCard{
    id:section;required property var modelData;visible:modelData.rows.length>0;title:modelData.title;footer:modelData.footer
    Repeater{
     model:ScriptModel{values:section.modelData.rows;objectProp:'id'}
     delegate:SettingsRow{
      required property var modelData;required property int index
      label:modelData.label;description:modelData.description || '';kind:modelData.kind;value:modelData.value || '';checked:!!modelData.checked
      choices:modelData.choices || [];selection:modelData.selection || 0;number:modelData.number || 0;minimum:modelData.minimum || 0;maximum:modelData.maximum===undefined ? 1:modelData.maximum;step:modelData.step || .01
      buttonText:modelData.buttonText || 'Open…';available:modelData.available!==false;separator:index<section.modelData.rows.length-1
      onActivated:root.apply(modelData,null);onToggled:value=>root.apply(modelData,value);onPicked:index=>root.apply(modelData,index);onEdited:value=>root.apply(modelData,value);onCommitted:value=>root.apply(modelData,value)
     }
    }
   }
  }
  BusyIndicator{Layout.alignment:Qt.AlignHCenter;visible:!!SettingsState.loading[root.current?.query || ''];running:visible;implicitWidth:24;implicitHeight:24}
 }
}
