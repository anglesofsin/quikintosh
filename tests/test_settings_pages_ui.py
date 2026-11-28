"""Load and capture every real Settings route in a private nested compositor."""
from pathlib import Path
import json,os,signal,subprocess,tempfile,time,unittest
from test_island_compact_ui import REQUIRED
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Private compositor required')
class SettingsPagesUI(unittest.TestCase):
 def test_every_page(self):
  runtime=Path(os.environ[REQUIRED[2]]).resolve();self.assertFalse(runtime.is_relative_to('/run/user'))
  phase=os.environ.get('QI_SETTINGS_PHASE','before');out=Path(os.environ.get('QI_SETTINGS_REVIEW_DIR','/home/pg/.local/state/quickintosh/reviews/settings-tahoe-audit'))/phase;out.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='qi-settings-audit-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for e in source.iterdir():
    if e.name not in ['shell.qml','settings.qml']:(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   text=(source/'settings.qml').read_text().replace('IpcHandler{\n  target:', '''IpcHandler{
  function controlsAudit():string{
   const page=loader.item,previous=SettingsPreferences.inputOverrides
   SettingsPreferences.inputOverrides=({'input:kb_layout':'fr','input:touchpad:natural_scroll':true,'input:sensitivity':0.25,'decoration:rounding':12})
   page.apply({action:'input-reset'},null)
   const result={unknownSelection:page.choice('Test',['First'],-1,'none').selection,reset:SettingsPreferences.inputOverrides}
   SettingsPreferences.inputOverrides=previous
   return JSON.stringify(result)
  }
  function focusAudit():string{
   const before=FocusState.profile.start
   loader.item.apply({action:'focus-edit',key:'start'},'28:90')
   const result={unchanged:FocusState.profile.start===before,error:SettingsState.error}
   SettingsState.error='';return JSON.stringify(result)
  }
  function findSettings(query:string):string{return JSON.stringify(SettingsCatalog.search(query).map(page=>page.id))}
  function advanced():void{function scan(item){if(item.hasOwnProperty('advanced')){try{item.advanced=true}catch(error){}}if(item.hasOwnProperty('advancedOptions'))item.advancedOptions=true;for(const child of item.children || [])scan(child)}if(loader.item)scan(loader.item)}
  function batteryDemo():void{loader.item.devices=[{id:'review-laptop',name:'Mac-style notebook',kind:'laptop',percent:81,charging:true,connected:true},{id:'review-phone',name:'Phone',kind:'phone',percent:64,charging:false,connected:true,source:'KDE Connect'}];BatteryHealthState.energyFullDesign=60;BatteryHealthState.energyFull=57;const now=Date.now()/1000;BatteryHistoryState.rawEntries=Array.from({length:48},(_,i)=>({timestamp:now-(47-i)*1800,percent:Math.round(47+i*.72),screenOn:i%3!==0}));}
  function geometry():string{function scan(item,result){if(item.visible && item.width>0 && item.height>0){if(item.text!==undefined && typeof item.text==='string' && item.text.length)result.push({text:item.text.slice(0,200),x:item.x,y:item.y,w:item.width,h:item.height,clipped:item.truncated===true})}for(const child of item.children || [])scan(child,result)}const rows=[];if(loader.item)scan(loader.item,rows);return JSON.stringify({width:window.width,height:window.height,rows:rows})}
  function scrollBottom():void{if(loader.item && loader.item.contentItem && loader.item.contentHeight)loader.item.contentItem.contentY=Math.max(0,loader.item.contentHeight-loader.item.height)}
  target:''',1)
   (root/'ReviewSettings.qml').write_text(text)
   (root/'qmldir').unlink(missing_ok=True);(root/'qmldir').write_text((source/'qmldir').read_text()+'\nReviewSettings ReviewSettings.qml\n')
   (root/'shell.qml').write_text('import QtQuick\nimport Quickshell\nShellRoot{ReviewSettings{}}\n')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent',LICKINTOSH_PAGE='general');env.pop('DISPLAY',None)
   qs=os.environ[REQUIRED[1]]
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   def ipc(*args):
    assert p.poll() is None,(root/'log').read_text()
    r=subprocess.run([qs,'-p',tmp,'ipc','call','settingsWindow',*args],env=env,capture_output=True,text=True,timeout=10)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
   try:
    for attempt in range(200):
     try:
      if json.loads(ipc('state')).get('pages'):break
     except (RuntimeError,ValueError,subprocess.TimeoutExpired):pass
     time.sleep(.1)
    ctl='/run/current-system/sw/bin/hyprctl'
    for attempt in range(100):
     clients=json.loads(subprocess.run([ctl,'-j','clients'],env=env,capture_output=True,text=True,timeout=5).stdout)
     own=next((client for client in clients if client.get('pid')==p.pid),None)
     if own:break
     time.sleep(.05)
    assert own,'Settings window not mapped'
    selector='address:'+own['address']
    command='hl.dispatch(hl.dsp.window.resize({x=1000,y=740,window='+json.dumps(selector)+'}))'
    result=subprocess.run([ctl,'eval',command],env=env,capture_output=True,text=True,timeout=5)
    assert result.returncode==0,result.stdout+result.stderr
    time.sleep(.2)
    subprocess.run(['hyprctl','dismissnotify','-1'],env=env,capture_output=True,timeout=5)
    report={};pages=json.loads((source/'settingsapp/catalog.json').read_text())
    for page in pages+[dict(id='glass',title='Liquid Glass')]:
     key=page['id'];ipc('navigate',key);time.sleep(.25)
     for attempt in range(30):
      state=json.loads(ipc('state'))
      if state['loaded'] or state['loadError']:break
      time.sleep(.1)
     time.sleep(.2);geo=json.loads(ipc('geometry'));report[key]=dict(page=page,state=state,geometry=geo)
     subprocess.run(['grim','-l','1',str(out/(key+'.png'))],env=env,check=True,timeout=15)
     if phase=='after':self.assertFalse(state['loadError'],key+'\n'+(root/'log').read_text()[-5000:]);self.assertTrue(state['loaded'],key)
     if key=='battery' and phase=='after':
      ipc('batteryDemo');time.sleep(.25);subprocess.run(['grim','-l','1',str(out/'battery-notebook.png')],env=env,check=True,timeout=15)
     if True:
      ipc('scrollBottom');time.sleep(.2);subprocess.run(['grim','-l','1',str(out/(key+'-bottom.png'))],env=env,check=True,timeout=15)
    if phase=='after':
     ipc('navigate','keyboard');time.sleep(.2);audit=json.loads(ipc('controlsAudit'))
     self.assertEqual(audit['unknownSelection'],-1)
     self.assertNotIn('input:kb_layout',audit['reset'])
     self.assertEqual(audit['reset']['input:touchpad:natural_scroll'],True)
     self.assertEqual(audit['reset']['input:sensitivity'],.25)
     self.assertEqual(audit['reset']['decoration:rounding'],12)
     ipc('navigate','focus');time.sleep(.2);focus=json.loads(ipc('focusAudit'));self.assertTrue(focus['unchanged']);self.assertTrue(focus['error'])
     self.assertIn('mouse',json.loads(ipc('findSettings','tracking speed')))
     for key in ['appearance','island']:
      ipc('navigate',key);time.sleep(.2);ipc('advanced');time.sleep(.2)
      subprocess.run(['grim','-l','1',str(out/(key+'-advanced.png'))],env=env,check=True,timeout=15)
      ipc('scrollBottom');time.sleep(.2);subprocess.run(['grim','-l','1',str(out/(key+'-advanced-bottom.png'))],env=env,check=True,timeout=15)
    text=(root/'log').read_text()
    if phase=='after':
     for issue in ['ReferenceError:','TypeError:','Cannot assign','Binding loop','recursive rearrange']:self.assertNotIn(issue,text,text[-7000:])
    (out/'report.json').write_text(json.dumps(report,indent=2));print('SETTINGS_ROUTES_REVIEWED',len(report),'LOAD_FAILURES',[k for k,v in report.items() if v['state']['loadError']])
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    (out/'qml.log').write_text((root/'log').read_text())
if __name__=='__main__':unittest.main()
