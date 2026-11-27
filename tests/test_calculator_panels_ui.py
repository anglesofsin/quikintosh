"""Verify real CC launch routing and complete menu fades on a private compositor."""
from pathlib import Path
import os,subprocess,time,json,signal,shutil,tempfile,unittest
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built source and private compositor required')
class CalculatorAndMenus(unittest.TestCase):
 def test_cc_launch_and_menu_lifetime(self):
  self.assertNotEqual(Path(os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME']).resolve(),Path(os.environ.get('XDG_RUNTIME_DIR','/run/user/1000')).resolve())
  temporary=tempfile.TemporaryDirectory(prefix='qi-menu-controls-');self.addCleanup(temporary.cleanup);home=Path(temporary.name)
  src=Path(os.environ['QUICKINTOSH_TEST_SOURCE']);app=home/'ccprobe';shutil.copytree(src,app,symlinks=True)
  app.chmod(app.stat().st_mode|0o700)
  for p in app.rglob('*'):
   if not p.is_symlink():p.chmod(p.stat().st_mode|0o200)
  for rel in ['ui/topbar/menubar/applemenu/AppleMenuWindow.qml','ui/topbar/statusarea/StatusSubMenuWindow.qml']:
   p=app/rel;s=p.read_text().replace('    property bool opened: false','    property int testMiddle:0\n    property bool testClipped:false\n    property var testPanel:null\n    function testStatus(){const surface=testPanel?.contentItem.children.find(c=>c.objectName===\'testSurface\');return {middle:testMiddle,clipped:testClipped,visible:!!testPanel?.visible,opacity:surface?.opacity ?? -1,scale:surface?.scale ?? -1}}\n    property bool opened: false',1)
   s=s.replace('Component.onCompleted: panel.entered = true','Component.onCompleted: {panel.entered=true;root.testPanel=panel}',1).replace('id: appleMenu','id: appleMenu;objectName:"testSurface";onOpacityChanged:if(root.closingAnimation && opacity>0 && opacity<1){root.testMiddle++;if(!panel.visible)root.testClipped=true}',1).replace('id: menuContainer','id: menuContainer;objectName:"testSurface";onOpacityChanged:if(root.closingAnimation && opacity>0 && opacity<1){root.testMiddle++;if(!panel.visible)root.testClipped=true}',1);p.write_text(s)
  (app/'shell.qml').write_text('''import QtQuick
  import Quickshell
  import Quickshell.Io
  import qs.services
  import qs.ui.topbar.menubar.applemenu
  import qs.ui.topbar.statusarea
  import qs.ui.topbar.statusarea.volume
  import qs.ui.topbar.statusarea.controlcenter
  ShellRoot{
   property bool closed:false
   ControlCenter{id:cc;onClosing:closed=true}
   AppleMenuWindow{id:apple}
   StatusSubMenuWindow{id:volume;contentComponent:Component{VolumePanel{}}}
   IpcHandler{target:'ccPolish'
   function launch():void{cc.openCalculator()}
   function toggle(on:bool):void{apple.opened=on;volume.opened=on}
   function status():string{return JSON.stringify({motion:ShellMotion.duration(160),game:GameMode.enabled,closed:closed,apple:apple.testStatus(),volume:volume.testStatus()})}
   }
  }''')
  binpath=app/'bin';binpath.mkdir();launcher=binpath/'quickintosh-calculator';launcher.write_text('#!/bin/sh\nprintf launched > "$HOME/calculator-launched"\n');launcher.chmod(0o755)
  env=dict(os.environ,QSG_RENDER_LOOP="basic",HOME=str(home),XDG_CONFIG_HOME=str(home/'.config'),XDG_STATE_HOME=str(home/'.state'),XDG_CACHE_HOME=str(home/'.cache'),PATH=str(binpath)+':'+os.environ['PATH'],XDG_RUNTIME_DIR=os.environ['QUICKINTOSH_TEST_PRIVATE_RUNTIME'],WAYLAND_DISPLAY=os.environ['QUICKINTOSH_TEST_PRIVATE_WAYLAND'],HYPRLAND_INSTANCE_SIGNATURE=os.environ['QUICKINTOSH_TEST_PRIVATE_HYPRLAND'])
  qs=os.environ['QUICKINTOSH_TEST_QS'];log=app/'log'
  with log.open('w') as f:p=subprocess.Popen([qs,'-p',str(app)],env=env,stdout=f,stderr=f,start_new_session=True)
  def call(*args):return subprocess.check_output([qs,'-p',str(app),'ipc','call','ccPolish',*args],env=env,text=True,stderr=subprocess.DEVNULL,timeout=10)
  try:
   for _ in range(200):
    if p.poll() is not None:raise RuntimeError(log.read_text())
    if 'Configuration Loaded' not in log.read_text():time.sleep(.1);continue
    try:json.loads(call('status'));break
    except subprocess.CalledProcessError:pass
    time.sleep(.1)
   call('launch');time.sleep(.4);assert json.loads(call('status'))['closed'];assert (home/'calculator-launched').exists()
   for _ in range(5):
    call('toggle','true')
    deadline=time.monotonic()+4
    while True:
     opened=json.loads(call('status'))
     if all(opened[m]['opacity']==1 and opened[m]['visible'] for m in ['apple','volume']):break
     assert time.monotonic()<deadline,opened;time.sleep(.03)
    call('toggle','false');deadline=time.monotonic()+4
    while True:
     closed=json.loads(call('status'))
     if all(not closed[m]['visible'] for m in ['apple','volume']):break
     assert time.monotonic()<deadline,closed;time.sleep(.025)
    for menu in ['apple','volume']:assert closed[menu]['middle']>0 and closed[menu]['scale']==1 and not closed[menu]['clipped'],closed
   print('CC_LAUNCH_AND_CONTINUOUS_MENU_FADE_OK',flush=True)
  finally:
   print(log.read_text()[-6000:],flush=True)
   if p.poll() is None:os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=5)
  text=log.read_text();print(text[-6000:],flush=True)
  for error in ['Failed to load configuration','ReferenceError','TypeError']:assert error not in text,error

if __name__=='__main__':unittest.main()
