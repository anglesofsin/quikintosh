"""Real compact states and privacy/satellite collision checks, private display only."""
from pathlib import Path
import json, os, signal, subprocess, tempfile, time, unittest

REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built shell and private compositor required')
class CompactIslandUI(unittest.TestCase):
 def test_compact_activities_and_privacy_reservation(self):
  runtime=Path(os.environ[REQUIRED[2]]).resolve();self.assertFalse(runtime.is_relative_to('/run/user'))
  out=Path(os.environ['QUICKINTOSH_REVIEW_DIR'])/'expanded';out.mkdir(parents=True,exist_ok=True)
  with tempfile.TemporaryDirectory(prefix='qi-compact-qa-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for e in source.iterdir():
    if e.name!='shell.qml':(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   for rel in ['rosa','rosa/overlays']:
    p=root/rel;original=p.resolve();p.unlink();p.mkdir()
    for e in original.iterdir():(p/e.name).symlink_to(e,target_is_directory=e.is_dir())
   p=root/'rosa/overlays/Island.qml';s=p.read_text();p.unlink();s=s.replace('    id: root','    id: root\n    property var qaWindow:null\n    property string qaLeftKind:""',1).replace('        IslandWindow {','        IslandWindow {\n            Component.onCompleted:root.qaWindow=this',1);s=s.replace('    readonly property string leftKind: {','    readonly property string leftKind: {\n        if(root.qaLeftKind)return root.qaLeftKind;',1);p.write_text(s)
   p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text();p.unlink();s=s.replace('    id: win','''    id: win
    property bool qaRight:false
    property bool qaLeft:false
    readonly property var qaGeometry:({crab:pill.crabOn,tint:String(pill.newEvent ? pill.eventTint:pill.tint),windowWidth:win.width,stageX:stage.x,droppy:win.droppyCompact,visible:visible,pillWidth:surface.width,pillHeight:stage.pillH,privacyX:privacy.x,edge:privacy.visualRight.x,gap:privacy.x-privacy.visualRight.x,right:dot.visible,rightProgress:dotLife.value,leftProgress:slotLife.value,wide:wide,stageWidth:stage.width})''',1)

   a=s.index('        readonly property bool minimalOn:');b=s.index('        readonly property real swallowed:',a)
   s=s[:a]+'''        readonly property bool minimalOn:win.qaRight
        readonly property bool leftOn:win.qaLeft

'''+s[b:]
   a=s.index('            readonly property bool on:',s.index('            id: privacy'));b=s.index('            width: 5',a);s=s[:a]+'            readonly property bool on:true\n\n'+s[b:];p.write_text(s)
   p=root/'rosa/overlays/IslandPill.qml';text=p.read_text();p.unlink();p.write_text(text.replace('property bool userIdle: false','property bool userIdle: true',1))
   (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import qs.rosa.overlays
import qs.rosa.services
ShellRoot {
 Island{id:hub;demoKind:'clock'}
 Component.onCompleted:{IslandConfig.setStyle('autoWide',false);IslandConfig.setStyle('dashboardEnabled',false);IslandConfig.setStyle('idleHide',false)}
 IpcHandler{target:'compactQA'
  function state():string{return JSON.stringify(hub.qaWindow?.qaGeometry || {})}
  function activity(name:string):void{hub.showDemo(name);hub.demoWide=true;hub.pinned=false;hub.voicePeek=false}
  function sides(left:bool,right:bool):void{hub.qaWindow.qaLeft=left;hub.qaWindow.qaRight=right}
  function leftKind(name:string):void{hub.qaLeftKind=name;hub.qaWindow.qaLeft=true}
  function offset(value:int):void{IslandConfig.setStyle("offsetX",value)}
  function align(name:string):void{IslandConfig.setStyle('align',name)}
 }
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent');env.pop('DISPLAY',None)
   qs=os.environ[REQUIRED[1]]
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   subprocess.run(['hyprctl','dismissnotify','-1'],env=env,capture_output=True,timeout=5)
   def ipc(*args):
    assert p.poll() is None,(root/'log').read_text()
    r=subprocess.run([qs,'-p',tmp,'ipc','call','compactQA',*args],env=env,capture_output=True,text=True,timeout=30)
    if r.returncode:raise RuntimeError(r.stdout+r.stderr)
    return r.stdout
   def wait(pred,seconds=30):
    end=time.monotonic()+seconds;last={}
    while time.monotonic()<end:
     try:
      last=json.loads(ipc('state'))
      if pred(last):return last
     except (RuntimeError,ValueError,subprocess.TimeoutExpired):pass
     time.sleep(.08)
    raise AssertionError(str(last)+'\n'+(root/'log').read_text()[-4000:])
   try:
    wait(lambda s:s.get('visible'),90)
    states={}
    kinds=['media','osd','notif','timer','alarm','record','bt','btoff','peri','power','low','net','vpn','print','clip','clipimg','keys','desk','route','focus','cmd','cmdfail','task','taskfail','shot','fail','done','gta','rain','snow','stack','call','chat','urgent','photo']
    kinds=['timer','record','bt','power','low','net','vpn','print','cmd','notif']
    for kind in kinds:
     ipc('activity',kind);time.sleep(.65)
     states[kind]=wait(lambda s:s.get('visible') and s.get('wide') and s.get('gap',-1)>=7.9)
     self.assertLessEqual(states[kind]['stageWidth'],states[kind]['pillWidth']+104)
     self.assertFalse(states[kind]['crab'],'Legacy idle animation overlapped compact state')
     subprocess.run(['grim','-l','1',str(out/(kind+'.png'))],env=env,check=True,timeout=30)
    text=(root/'log').read_text()
    for error in ['ReferenceError:','TypeError:','Cannot assign','Failed to load configuration']:self.assertNotIn(error,text,text[-5000:])
    (out/'geometry.json').write_text(json.dumps(states,indent=2))
    print('EXPANDED_ACTIVITY_STATES_RENDER_OK')
   finally:
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=5)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
    shutil_log=root/'log'
    if shutil_log.exists():(out/'qml.log').write_text(shutil_log.read_text())

if __name__=='__main__':unittest.main()
