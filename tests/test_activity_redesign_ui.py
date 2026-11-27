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
import Quickshell
import Quickshell.Io
import Quickshell.Wayland
import QtTest
import "island-shelf"
import qs.rosa.services
ShellRoot{
 PanelWindow{id:win;anchors{top:true;left:true;right:true}implicitHeight:500;color:'#100cc4';exclusionMode:ExclusionMode.Ignore
  property var fixture:({kind:'timer',title:'Timer',label:'20:00',value:'20:00',color:'#ff9f0a',icon:'clock'})
  property int actions:0
  property string lastReply:''
  function named(item,name){if(item.objectName===name)return item;for(const child of item.children || []){const match=named(child,name);if(match)return match}return null}
  TestCase{id:pointer;when:false}
  ActivitySurface{id:compact;objectName:'compact';x:400;y:70;activity:win.fixture;width:compact.preferredCompactWidth;height:26;onActivate:win.actions++}
  ActivitySurface{id:expanded;x:620;y:55;activity:win.fixture;presentation:'expanded';width:320;height:implicitHeight;onAction:(name,value)=>{win.actions++;if(name==='reply')win.lastReply=value}}
  ActivitySurface{id:left;x:360;y:70;activity:win.fixture;presentation:'satellite';width:26;height:26}
  ActivitySurface{id:right;x:980;y:70;activity:win.fixture;presentation:'satellite';width:26;height:26}
  IpcHandler{target:'eventsQA';function fixture(value:string):void{win.fixture=JSON.parse(value)}function state():string{return JSON.stringify({width:compact.width,height:compact.height,actions:win.actions,lastReply:win.lastReply})}function vpnReview(on:bool):void{Vpn.up=on}function vpnState():string{return JSON.stringify({value:Vpn.up ? Vpn.activityElapsed:'Off'})}function reply():void{const open=win.named(expanded,'activity-reply-open');pointer.mouseClick(open,open.width/2,open.height/2,Qt.LeftButton);win.named(expanded,'activity-reply-input').text='Count me in!';const send=win.named(expanded,'activity-reply-send');pointer.mouseClick(send,send.width/2,send.height/2,Qt.LeftButton)}function click():void{pointer.mouseClick(compact,compact.width/2,compact.height/2,Qt.LeftButton)}}
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
    for index,item in enumerate(fixtures):
     ipc('fixture',json.dumps(item));time.sleep(.15)
     state=json.loads(ipc('state'));self.assertEqual(state['height'],26);self.assertGreaterEqual(state['width'],118);self.assertLessEqual(state['width'],180)
     if item['kind'] not in ['power','low']:self.assertEqual(state['width'],118)
     subprocess.run(['grim','-l','1',str(out/(f'{index:02}-{item["kind"]}.png'))],env=env,check=True,timeout=15)
    ipc('vpnReview','true');time.sleep(1.15);self.assertRegex(json.loads(ipc('vpnState'))['value'],r'^0:0[1-9]$');ipc('vpnReview','false');self.assertEqual(json.loads(ipc('vpnState'))['value'],'Off')
    ipc('click');self.assertEqual(json.loads(ipc('state'))['actions'],1)
    ipc('fixture',json.dumps(dict(kind='notif',title='Jamie Chen',label='Jamie Chen',subtitle='Can you join?',initials='JC',canReply=True)));time.sleep(.1);ipc('reply');self.assertEqual(json.loads(ipc('state'))['lastReply'],'Count me in!')
    subprocess.run(['grim','-l','1',str(out/'notification-replied.png')],env=env,check=True,timeout=15)
    text=(root/'log').read_text()
    for issue in ['ReferenceError:','TypeError:','Cannot assign','Failed to load configuration']:self.assertNotIn(issue,text)
    (out/'fixtures.json').write_text(json.dumps(fixtures,indent=2));print('31_EVENTS_COMPACT_EXPANDED_LEFT_RIGHT_FIXED_118x26_NATIVE_CLICK_OK')
   finally:
    if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
    (out/'qml.log').write_text((root/'log').read_text())
if __name__=='__main__':unittest.main()
