"""Exercise the real compact/dashboard handoff on a private Wayland display."""
from pathlib import Path
import os,json,tempfile,subprocess,time,signal,unittest
REQUIRED=['QUICKINTOSH_TEST_SOURCE','QUICKINTOSH_TEST_QS','QUICKINTOSH_TEST_PRIVATE_RUNTIME','QUICKINTOSH_TEST_PRIVATE_WAYLAND','QUICKINTOSH_TEST_PRIVATE_HYPRLAND']
@unittest.skipUnless(all(os.environ.get(k) for k in REQUIRED),'Built shell and private compositor required')
class IslandMorphUI(unittest.TestCase):
 def test_repeated_compact_expanded_handoff(self):
  runtime=Path(os.environ[REQUIRED[2]]).resolve();self.assertFalse(runtime.is_relative_to('/run/user'))
  with tempfile.TemporaryDirectory(prefix='qi-island-morph-') as tmp:
   root=Path(tmp);source=Path(os.environ[REQUIRED[0]])
   for e in source.iterdir():
    if e.name!='shell.qml':(root/e.name).symlink_to(e,target_is_directory=e.is_dir())
   for relative in ['rosa','rosa/overlays']:
    p=root/relative;original=p.resolve();p.unlink();p.mkdir()
    for e in original.iterdir():(p/e.name).symlink_to(e,target_is_directory=e.is_dir())
   p=root/'rosa/overlays/Island.qml';s=p.read_text();p.unlink();s=s.replace('    id: root','    id: root\n    property var qaWindow:null',1).replace('        IslandWindow {','        IslandWindow {\n            Component.onCompleted:root.qaWindow=this',1);p.write_text(s)
   p=root/'rosa/overlays/IslandWindow.qml';s=p.read_text();p.unlink();s=s.replace('    id: win','    id: win\n    readonly property var qaGeometry:({cover:dashboardCover,requested:dashboardRequested,compactOpacity:stage.opacity,morph:morph.value,visible:visible})',1);p.write_text(s)
   (root/'shell.qml').write_text('''import QtQuick
import Quickshell
import Quickshell.Io
import qs.rosa.overlays
import qs.rosa.services
ShellRoot{
 Island{id:hub;demoKind:'clock'}
 IpcHandler{target:'morphQA';function state():string{return JSON.stringify(hub.qaWindow?.qaGeometry || {})}function expandIsland(on:bool):void{hub.qaWindow.dashboardRequested=on}function dashboardEnabled(on:bool):void{IslandConfig.setStyle("dashboardEnabled",on)}}
}''')
   env=dict(os.environ,HOME=tmp,XDG_CONFIG_HOME=tmp+'/.config',XDG_CACHE_HOME=tmp+'/.cache',XDG_STATE_HOME=tmp+'/.state',XDG_RUNTIME_DIR=str(runtime),WAYLAND_DISPLAY=os.environ[REQUIRED[3]],HYPRLAND_INSTANCE_SIGNATURE=os.environ[REQUIRED[4]],DBUS_SESSION_BUS_ADDRESS='unix:path=/nonexistent');env.pop('DISPLAY',None)
   qs=os.environ[REQUIRED[1]]
   with (root/'log').open('w') as log:p=subprocess.Popen([qs,'-p',tmp],env=env,stdout=log,stderr=log,start_new_session=True)
   try:
    def ipc(*args):
     self.assertIsNone(p.poll(),(root/'log').read_text())
     r=subprocess.run([qs,'-p',tmp,'ipc','call','morphQA',*args],env=env,capture_output=True,text=True,timeout=5)
     self.assertEqual(r.returncode,0,r.stdout+r.stderr);return r.stdout
    def wait(predicate):
     end=time.monotonic()+5;last={}
     while time.monotonic()<end:
      try:
       last=json.loads(ipc('state'))
       if predicate(last):return last
      except (ValueError,KeyError,AssertionError):
       if p.poll() is not None:raise
      time.sleep(.025)
     self.fail(str(last)+'\n'+(root/'log').read_text()[-3500:])
    wait(lambda s:s.get('visible') and s.get('compactOpacity',0)>.95)
    for _ in range(20):
     ipc('expandIsland','true');wait(lambda s:s.get('cover') and s.get('compactOpacity')==0)
     time.sleep(.08)
     ipc('expandIsland','false');wait(lambda s:not s.get('cover') and s.get('compactOpacity',0)>.95)
    ipc('dashboardEnabled','false');ipc('expandIsland','true')
    wait(lambda s:not s.get('cover') and not s.get('requested') and s.get('compactOpacity',0)>.95)
    ipc('dashboardEnabled','true')
    print('ISLAND_REAL_OWNER_20_MORPH_HANDOFFS_AND_DISABLED_DASHBOARD_OK')
   finally:
    if p.poll() is None:
     os.killpg(p.pid,signal.SIGTERM)
     try:p.wait(timeout=4)
     except subprocess.TimeoutExpired:os.killpg(p.pid,signal.SIGKILL);p.wait()
if __name__=='__main__':unittest.main()
