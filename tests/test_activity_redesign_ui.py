"""New event surfaces rendered on a private Wayland display, never the host."""
from pathlib import Path
import json,os,signal,subprocess,tempfile,time,unittest
from test_island_compact_ui import REQUIRED

@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Private compositor required')
class ActivityRedesignUI(unittest.TestCase):
 def test_surfaces(self):
  runtime=Path(os.environ[REQUIRED[2]]).resolve();self.assertFalse(runtime.is_relative_to('/run/user'))
  out=Path(os.environ['QUICKINTOSH_REVIEW_DIR'])/'new';out.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='qi-event-review-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for e in source.iterdir():
    if e.name!='shell.qml':(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   (root/'shell.qml').write_text('''import QtQuick
import QtQuick.Controls.Basic
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtTest
import "island-shelf"
import qs.rosa.services
ShellRoot{
 PanelWindow{id:win;anchors{top:true;left:true;right:true}implicitHeight:settingsReview.active ? 780:500;color:'#100cc4';exclusionMode:ExclusionMode.Ignore
  property var fixture:({kind:'timer',title:'Timer',label:'20:00',value:'20:00',color:'#ff9f0a',icon:'clock'})
  property int actions:0
  property string lastReply:''
  function named(item,name){if(item.objectName===name)return item;for(const child of item.children || []){const match=named(child,name);if(match)return match}return null}
  ActivityData{id:policyData;kind:'task';context:({progress:1,status:'failed'})}
  TestCase{id:pointer;when:false}
  ActivitySurface{id:compact;objectName:'compact';x:400;y:70;activity:win.fixture;width:compact.preferredCompactWidth;height:26;onActivate:win.actions++}
  ActivitySurface{id:expanded;x:620;y:55;activity:win.fixture;presentation:'expanded';width:320;height:implicitHeight;onAction:(name,value)=>{win.actions++;if(name==='reply')win.lastReply=value}}
  ActivitySurface{id:left;x:360;y:70;activity:win.fixture;presentation:'satellite';width:26;height:26}
  ActivitySurface{id:right;x:980;y:70;activity:win.fixture;presentation:'satellite';width:26;height:26}
  Loader{id:brokenReview;x:1245;y:70;active:false;sourceComponent:Component{ShelfIcon{icon:'notch/vpn.svg';size:24}}}
  Loader{id:settingsReview;x:620;y:20;width:620;height:720;active:false;sourceComponent:Component{Rectangle{color:'#1c1c1e';radius:20;Flickable{anchors.fill:parent;anchors.margins:18;clip:true;contentHeight:form.implicitHeight;ScrollBar.vertical:ScrollBar{}IconSettings{id:form;width:parent.width}}}}}
  IpcHandler{target:'eventsQA';function policySet(key:string,value:string):void{ActivityIconPolicy.set(key,JSON.parse(value))}function policyState():string{return JSON.stringify(Object.assign({},ActivityIconPolicy.spec.defaults,ActivityIconPolicy.preferences))}function policyResolve(event:string,mode:string):string{return JSON.stringify(ActivityIconPolicy.resolve(JSON.parse(event),mode))}function policyAdapterState():string{return JSON.stringify(policyData.value)}function policyBroken():void{brokenReview.active=true;Qt.callLater(()=>win.named(brokenReview.item,'generated-icon-image').source='file:///nonexistent-quickintosh-icon-test.png')}function policyBrokenState():string{if(!brokenReview.item)return '{}';return JSON.stringify({fallback:win.named(brokenReview.item,'generated-icon-fallback').visible,source:String(win.named(brokenReview.item,'generated-icon-fallback').source)})}function policyVisual():string{return JSON.stringify(compact.iconView)}function policySettings():void{settingsReview.active=true}function policyCustomize():void{const button=win.named(settingsReview.item,'icon-policy-customize');pointer.mouseClick(button,button.width/2,button.height/2,Qt.LeftButton)}function policyChoose(kind:string,icon:string):void{const control=win.named(settingsReview.item,'icon-event-'+kind);control.activated(ActivityIconPolicy.spec.icons.indexOf(icon)+1)}function policyReset():void{const button=win.named(settingsReview.item,'icon-policy-reset');pointer.mouseClick(button,button.width/2,button.height/2,Qt.LeftButton)}function fixture(value:string):void{win.fixture=JSON.parse(value)}function state():string{return JSON.stringify({width:compact.width,height:compact.height,actions:win.actions,lastReply:win.lastReply,compactLabel:compact.compactLabel,expandedMeterY:win.named(expanded,'activity-meter').mapToItem(expanded,0,2).y,expandedIconY:win.named(expanded,'activity-meter-icon').mapToItem(expanded,0,win.named(expanded,'activity-meter-icon').height/2).y,expandedValueY:win.named(expanded,'activity-value').mapToItem(expanded,0,win.named(expanded,'activity-value').height/2).y,meterY:win.named(compact,'activity-meter').mapToItem(compact,0,2).y,iconY:win.named(compact,'activity-meter-icon').mapToItem(compact,0,win.named(compact,'activity-meter-icon').height/2).y,valueY:win.named(compact,'activity-value').mapToItem(compact,0,win.named(compact,'activity-value').height/2).y,recordDotX:win.named(expanded,'activity-record-dot').mapToItem(expanded,0,0).x,subtitleX:win.named(expanded,'activity-subtitle').mapToItem(expanded,0,0).x})}function vpnReview(on:bool):void{Vpn.up=on}function vpnState():string{return JSON.stringify({value:Vpn.up ? Vpn.activityElapsed:'Off'})}function reply():void{const open=win.named(expanded,'activity-reply-open');pointer.mouseClick(open,open.width/2,open.height/2,Qt.LeftButton);win.named(expanded,'activity-reply-input').text='Count me in!';const send=win.named(expanded,'activity-reply-send');pointer.mouseClick(send,send.width/2,send.height/2,Qt.LeftButton)}function click():void{pointer.mouseClick(compact,compact.width/2,compact.height/2,Qt.LeftButton)}}
 }
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent');env.pop('DISPLAY',None)
   qs=os.environ[REQUIRED[1]]
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   def ipc(*args):
    self.assertIsNone(p.poll(),(root/'log').read_text());r=subprocess.run([qs,'-p',tmp,'ipc','call','eventsQA',*args],env=env,capture_output=True,text=True,timeout=15)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
   try:
    for attempt in range(150):
     try:json.loads(ipc('state'));break
     except (RuntimeError,ValueError,subprocess.TimeoutExpired):time.sleep(.1)
    subprocess.run(['hyprctl','dismissnotify','-1'],env=env,capture_output=True,timeout=5)
    if os.environ.get('QUICKINTOSH_ICON_POLICY_REVIEW')=='1':
     def wait_policy(key,value):
      for attempt in range(100):
       if json.loads(ipc('policyState')).get(key)==value:return
       time.sleep(.05)
      self.fail(ipc('policyState'))
     self.assertTrue(json.loads(ipc('policyState'))['iconPolicySmart'])
     self.assertEqual(json.loads(ipc('policyAdapterState'))['status'],'failed');self.assertEqual(json.loads(ipc('policyAdapterState'))['value'],'Failed')
     event=dict(kind='task',icon='terminal',status='failed',title='Build failed',color='#a78bfa')
     ipc('fixture',json.dumps(event))
     self.assertEqual(json.loads(ipc('policyResolve',json.dumps(event),'compact'))['icon'],'x')
     ipc('policySet','iconPolicyOverrides',json.dumps({'task':'cloud'}));wait_policy('iconPolicyOverrides',{'task':'cloud'})
     self.assertEqual(json.loads(ipc('policyResolve',json.dumps(event),'compact'))['icon'],'x')
     ipc('policySet','iconPolicyStatusOverrides',json.dumps({'failed':'bell'}));wait_policy('iconPolicyStatusOverrides',{'failed':'bell'});self.assertEqual(json.loads(ipc('policyResolve',json.dumps(event),'compact'))['icon'],'bell')
     ipc('policySet','iconPolicyStatusOverrides','{}');wait_policy('iconPolicyStatusOverrides',{})
     ipc('policySet','iconPolicyStatus','false');wait_policy('iconPolicyStatus',False)
     self.assertEqual(json.loads(ipc('policyResolve',json.dumps(event),'compact'))['icon'],'cloud')
     self.assertEqual(json.loads(ipc('policyVisual'))['icon'],'cloud')
     ipc('policySet','iconPolicyColors','false');wait_policy('iconPolicyColors',False)
     self.assertEqual(json.loads(ipc('policyVisual'))['color'],'#f5f5f7')
     self.assertEqual(json.loads(ipc('policyResolve',json.dumps(event),'compact'))['color'],'#f5f5f7')
     ipc('policySet','iconPolicyCompactSize','20');wait_policy('iconPolicyCompactSize',20)
     ipc('fixture',json.dumps(event));time.sleep(.3)
     subprocess.run(['grim','-l','1',str(out/'icon-policy-custom.png')],env=env,check=True,timeout=15)
     ipc('policySettings');time.sleep(.5)
     subprocess.run(['grim','-l','1',str(out/'icon-policy-settings.png')],env=env,check=True,timeout=15)
     ipc('policyCustomize');time.sleep(.1);ipc('policyChoose','bt','smartphone');wait_policy('iconPolicyOverrides',{'task':'cloud','bt':'smartphone'})
     ipc('policyCustomize')
     ipc('policyReset');wait_policy('iconPolicyStatus',True);wait_policy('iconPolicyColors',True);wait_policy('iconPolicyCompactSize',16);wait_policy('iconPolicyOverrides',{})
     time.sleep(.2)
     subprocess.run(['grim','-l','1',str(out/'icon-policy-defaults.png')],env=env,check=True,timeout=15)
     text=(root/'log').read_text()
     for issue in ['ReferenceError:','TypeError:','Cannot assign','Failed to load configuration']:self.assertNotIn(issue,text)
     ipc('policyBroken')
     for attempt in range(100):
      fallback=json.loads(ipc('policyBrokenState'))
      if fallback.get('fallback'):break
      time.sleep(.05)
     self.assertTrue(fallback.get('fallback'));self.assertTrue(fallback['source'].endswith('/notch/shield.svg'))
     print('ICON_POLICY_NATIVE_PRIORITY_PERSISTENCE_SETTINGS_RESET_AND_IMAGE_FALLBACK_OK');return
    fixtures=[
     dict(kind='power',title='Charging',label='Charging',value='80%',color='#30d158'),
     dict(kind='power',title='Full Battery',label='Full Battery',value='100%',complete=True,subtitle='Your computer is fully charged.',color='#30d158'),
     dict(kind='low',title='Low Battery',label='Low Battery',value='9%',color='#ff453a'),
     dict(kind='timer',title='Timer',label='20:00',value='20:00',color='#ff9f0a',icon='clock',action='pause'),
     dict(kind='alarm',title='Alarm',label='7:00',icon='bell',color='#ff9f0a'),
     dict(kind='vpn',title='Connected',label='Studio VPN',subtitle='Studio VPN',value='01:05',icon='vpn',color='#ff9f0a'),
     dict(kind='record',title='1:05',label='1:05',subtitle='Screen Recording',action='stop',color='#ff453a'),
     dict(kind='notif',title='Jamie Chen',label='Jamie Chen',subtitle='Launch plan · The final cut is in the shared folder. Ship it!',initials='JC'),
     dict(kind='osd',title='Volume',meter=True,icon='volume-2',fraction=.6,value='60',color='#30d158'),
     dict(kind='osd',title='Muted',meter=True,icon='volume-x',fraction=.64,value='64',color='#ff453a'),
     dict(kind='osd',title='Brightness',meter=True,icon='sun',fraction=.64,value='64',color='#ffffff'),
     dict(kind='bt',title='Headphones',label='Connected',subtitle='Connected',value='80%',icon='headphones',color='#30d158'),
     dict(kind='net',title='Connected',label='Connected',subtitle='Ethernet',icon='wifi',color='#30d158'),
     dict(kind='focus',title='Focus',label='Off',icon='moon'),
     dict(kind='download',title='Download',label='64%',subtitle='Download in progress',icon='download',value='64%'),
     dict(kind='cmd',title='swift build',label='swift build',icon='terminal',value='64%'),
     dict(kind='done',title='Completed',label='Completed',icon='check',color='#30d158'),
     dict(kind='fail',title='Failed',label='Failed',icon='x',color='#ff453a'),
     dict(kind='clip',title='Clipboard',label='Copied',subtitle='Text copied to clipboard',icon='clipboard'),
     dict(kind='print',title='Printing',label='2 jobs',subtitle='Canon Printer',icon='file-text'),
     dict(kind='peri',title='Mouse',label='80%',subtitle='Connected',icon='battery',value='80%'),
     dict(kind='keys',title='Keyboard',label='EN',icon='command'),
     dict(kind='desk',title='Workspace',label='Desktop 2',icon='laptop'),
     dict(kind='route',title='Audio output',label='Headphones',icon='headphones'),
     dict(kind='remind',title='Reminder',label='Meeting',subtitle='Design sync in 5 minutes',icon='bell'),
     dict(kind='weather',title='Rain',label='Rain soon',subtitle='Rain in 20 minutes',icon='cloud'),
    ]
    fixtures += [dict(kind='net',title='Connected',label='A network name that is much longer than the compact width',subtitle='An extremely long network name to verify truncation without geometry changes',icon='wifi'),dict(kind='peri',title='Unknown battery',label='Connected',subtitle='No charge reported',icon='battery')]
    fixtures += [dict(kind='notif',title='Alex Morgan',label='Alex Morgan',subtitle='Look at this sunset! Dinner at seven?',initials='AM',image='file:///tmp/qi-review-notification.png'),dict(kind='share',title='Transfer',label='Transfer',value='80%',icon='link',color='#30d158'),dict(kind='cloud',title='Completed',label='Completed',icon='cloud',color='#a78bfa')]
    fixtures += [dict(kind='osd',title=title,meter=True,icon=icon,fraction=value,value=str(round(value*100)),color=color) for title,icon,value,color in [('Microphone','mic',.5,'#30d158'),('Microphone muted','mic-off',.5,'#ff453a'),('Keyboard backlight','sun',.5,'#ffffff'),('Volume zero','volume-2',0,'#30d158'),('Volume full','volume-2',1,'#30d158'),('Volume amplified','volume-2',2,'#30d158')]]
    for index,item in enumerate(fixtures):
     ipc('fixture',json.dumps(item));time.sleep(.15)
     state=json.loads(ipc('state'));self.assertEqual(state['height'],26);self.assertGreaterEqual(state['width'],118);self.assertLessEqual(state['width'],700)
     if item.get('meter'):
      self.assertEqual(state['width'],118);self.assertAlmostEqual(state['meterY'],state['iconY'],delta=.5);self.assertAlmostEqual(state['meterY'],state['valueY'],delta=.5);self.assertAlmostEqual(state['expandedMeterY'],state['expandedIconY'],delta=.5);self.assertAlmostEqual(state['expandedMeterY'],state['expandedValueY'],delta=.5)
     if item['kind']=='record':self.assertAlmostEqual(state['recordDotX'],state['subtitleX'],delta=.5)
     if item.get('label')==item.get('value'):self.assertEqual(state['compactLabel'],'')
     subprocess.run(['grim','-l','1',str(out/(f'{index:02}-{item["kind"]}.png'))],env=env,check=True,timeout=15)
    ipc('vpnReview','true');time.sleep(1.15);self.assertRegex(json.loads(ipc('vpnState'))['value'],r'^0:0[1-9]$');ipc('vpnReview','false');self.assertEqual(json.loads(ipc('vpnState'))['value'],'Off')
    ipc('click');self.assertEqual(json.loads(ipc('state'))['actions'],1)
    ipc('fixture',json.dumps(dict(kind='notif',title='Jamie Chen',label='Jamie Chen',subtitle='Can you join?',initials='JC',canReply=True)));time.sleep(.1);ipc('reply');self.assertEqual(json.loads(ipc('state'))['lastReply'],'Count me in!')
    subprocess.run(['grim','-l','1',str(out/'notification-replied.png')],env=env,check=True,timeout=15)
    text=(root/'log').read_text()
    for issue in ['ReferenceError:','TypeError:','Cannot assign','Failed to load configuration']:self.assertNotIn(issue,text)
    (out/'fixtures.json').write_text(json.dumps(fixtures,indent=2));print(f'{len(fixtures)}_EVENTS_COMPACT_EXPANDED_BOTH_METER_CENTERLINES_NATIVE_CLICK_OK')
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    (out/'qml.log').write_text((root/'log').read_text())
if __name__=='__main__':unittest.main()
